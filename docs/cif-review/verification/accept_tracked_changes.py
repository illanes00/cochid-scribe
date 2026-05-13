"""Aceptación de tracked changes sobre un docx.

Toma un docx con tracked changes (`<w:ins>`, `<w:del>`, paragraph ins/del marks)
y produce una copia con todos los cambios aceptados: el `<w:del>` se elimina,
el `<w:ins>` se desenvuelve dejando el contenido.

Los comentarios se preservan (el razonamiento MI-NN sigue visible para el lector).

Uso:
    python3 accept_tracked_changes.py input.docx output.docx
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def qn(t):
    return f"{{{W_NS}}}{t}"


TRACKED_FILES = (
    "word/document.xml",
    "word/comments.xml",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/header1.xml",
    "word/header2.xml",
    "word/header3.xml",
    "word/footer1.xml",
    "word/footer2.xml",
    "word/footer3.xml",
)


def accept_in_tree(tree):
    """Accept tracked changes in-place on an lxml tree."""
    # 1. Remove all <w:del>...</w:del> completely (and their deleted content)
    for del_elem in list(tree.iter(qn("del"))):
        parent = del_elem.getparent()
        if parent is not None:
            parent.remove(del_elem)

    # Also remove standalone delText fragments left behind
    for del_text in list(tree.iter(qn("delText"))):
        parent = del_text.getparent()
        if parent is not None:
            parent.remove(del_text)

    # 2. Unwrap all <w:ins>: move children out, remove the ins wrapper.
    #    <w:ins> inside <w:rPr> or <w:pPr>/<w:rPr> marks inserted paragraph/run
    #    formatting — those we just delete (no content to preserve).
    for ins_elem in list(tree.iter(qn("ins"))):
        parent = ins_elem.getparent()
        if parent is None:
            continue
        # If parent is rPr, this is a formatting-mark insertion -> drop
        if parent.tag == qn("rPr"):
            parent.remove(ins_elem)
            continue
        # Otherwise unwrap: move ins children to parent in the same position
        idx = list(parent).index(ins_elem)
        children = list(ins_elem)
        for child in children:
            ins_elem.remove(child)
            parent.insert(idx, child)
            idx += 1
        parent.remove(ins_elem)

    # 3. Remove pPrChange / rPrChange / sectPrChange (formatting-change trackers)
    for change_tag in ("pPrChange", "rPrChange", "sectPrChange", "tblPrChange",
                       "tblGridChange", "trPrChange", "tcPrChange"):
        for el in list(tree.iter(qn(change_tag))):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)

    # 4. Convert <w:moveTo> to regular content (accept), drop <w:moveFrom>
    for move_from in list(tree.iter(qn("moveFrom"))):
        parent = move_from.getparent()
        if parent is not None:
            parent.remove(move_from)
    for move_to in list(tree.iter(qn("moveTo"))):
        parent = move_to.getparent()
        if parent is None:
            continue
        idx = list(parent).index(move_to)
        children = list(move_to)
        for child in children:
            move_to.remove(child)
            parent.insert(idx, child)
            idx += 1
        parent.remove(move_to)


def accept_docx(input_path: Path, output_path: Path):
    if output_path.exists():
        output_path.unlink()
    shutil.copy(input_path, output_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    counts = {}
    with zipfile.ZipFile(output_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                raw = zin.read(item)
                if item in TRACKED_FILES:
                    try:
                        tree = etree.fromstring(raw)
                    except etree.XMLSyntaxError:
                        zout.writestr(item, raw)
                        continue
                    before_ins = len(list(tree.iter(qn("ins"))))
                    before_del = len(list(tree.iter(qn("del"))))
                    accept_in_tree(tree)
                    after_ins = len(list(tree.iter(qn("ins"))))
                    after_del = len(list(tree.iter(qn("del"))))
                    counts[item] = (before_ins, before_del, after_ins, after_del)
                    new_xml = etree.tostring(
                        tree, xml_declaration=True, encoding="UTF-8", standalone=True
                    )
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, raw)

    shutil.move(tmp_path, output_path)

    print(f"Accepted: {input_path.name} -> {output_path.name}")
    print(f"Size: {output_path.stat().st_size:,} bytes\n")
    print(f"  {'file':30s}  ins before/after   del before/after")
    for name, (bi, bd, ai, ad) in counts.items():
        print(f"  {name:30s}  {bi:4d}/{ai:<4d}         {bd:4d}/{ad:<4d}")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])
    if not inp.exists():
        print(f"input no existe: {inp}")
        sys.exit(1)
    accept_docx(inp, out)


if __name__ == "__main__":
    main()
