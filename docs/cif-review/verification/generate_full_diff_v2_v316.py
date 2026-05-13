"""Generate a tracked-changes docx that shows ALL differences between v2 and v3.16-aceptada.

Strategy:
- Use v3.16-aceptada as the structural base (portada nueva, saltos, nueva bibliografía, comentarios MI-NN).
- For each paragraph, compare against v2 using difflib.SequenceMatcher.
- Mark differences as <w:ins> (new) / <w:del> (removed from v2) as tracked changes.
- Preserve comments.

Inputs:
- v2.docx (base leída por directores en abril)
- v3.16-aceptada.docx (texto final limpio)

Output:
- v3.16-full-tracked-vs-v2.docx (muestra TODOS los cambios vs v2)
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path

from lxml import etree

BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
V2 = BASE / "output/informe-final-v2.docx"
V316A = BASE / "output/informe-final-v3.16-aceptada.docx"
OUT = BASE / "output/informe-final-v3.16-full-tracked-vs-v2.docx"

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00-03:00"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_rev = [6000000]


def next_rev():
    _rev[0] += 1
    return str(_rev[0])


def qn(t):
    return f"{{{W_NS}}}{t}"


def extract_paragraphs_text(docx_path):
    """Return list of paragraph text strings, in body order."""
    with zipfile.ZipFile(docx_path) as z:
        doc_xml = z.read("word/document.xml")
    tree = etree.fromstring(doc_xml)
    body = tree.find(qn("body"))
    texts = []
    for p in body.findall(qn("p")):
        parts = []
        for t in p.iter(qn("t")):
            parts.append(t.text or "")
        for tab in p.iter(qn("tab")):
            parts.append("\t")
        texts.append("".join(parts))
    return texts


def normalize(s):
    return re.sub(r"\s+", " ", s or "").strip()


def make_delete_paragraph(text, reference_p):
    """Build a paragraph that appears as fully deleted (tracked del) containing text."""
    new_p = etree.Element(qn("p"))
    ref_pPr = reference_p.find(qn("pPr"))
    if ref_pPr is not None:
        pPr_copy = deepcopy(ref_pPr)
        new_p.append(pPr_copy)
    # Add paragraph-mark delete (w:pPr/w:rPr/w:del)
    pPr = new_p.find(qn("pPr"))
    if pPr is None:
        pPr = etree.SubElement(new_p, qn("pPr"))
    rPr = pPr.find(qn("rPr"))
    if rPr is None:
        rPr = etree.SubElement(pPr, qn("rPr"))
    del_mark = etree.SubElement(rPr, qn("del"))
    del_mark.set(qn("id"), next_rev())
    del_mark.set(qn("author"), AUTHOR)
    del_mark.set(qn("date"), DATE)
    # Add del wrapper with content
    del_elem = etree.SubElement(new_p, qn("del"))
    del_elem.set(qn("id"), next_rev())
    del_elem.set(qn("author"), AUTHOR)
    del_elem.set(qn("date"), DATE)
    r = etree.SubElement(del_elem, qn("r"))
    t = etree.SubElement(r, qn("delText"))
    t.text = text
    t.set(f"{{{XML_NS}}}space", "preserve")
    return new_p


def convert_paragraph_runs_to_ins(p):
    """Wrap existing runs of a paragraph in <w:ins>, and mark paragraph-mark as inserted."""
    pPr = p.find(qn("pPr"))
    # Mark paragraph-mark as inserted
    if pPr is not None:
        rPr = pPr.find(qn("rPr"))
        if rPr is None:
            rPr = etree.SubElement(pPr, qn("rPr"))
        ins_mark = etree.SubElement(rPr, qn("ins"))
        ins_mark.set(qn("id"), next_rev())
        ins_mark.set(qn("author"), AUTHOR)
        ins_mark.set(qn("date"), DATE)

    # Wrap existing runs in <w:ins>
    runs = [c for c in list(p) if c.tag == qn("r")]
    if not runs:
        return
    # Insert a single <w:ins> wrapping all runs in place
    first_r = runs[0]
    idx = list(p).index(first_r)
    ins_wrap = etree.Element(qn("ins"))
    ins_wrap.set(qn("id"), next_rev())
    ins_wrap.set(qn("author"), AUTHOR)
    ins_wrap.set(qn("date"), DATE)
    for r in runs:
        p.remove(r)
        ins_wrap.append(r)
    p.insert(idx, ins_wrap)


def wrap_paragraph_replace(p, old_text):
    """Mark current paragraph as ins + prepend a del element with the old text."""
    # Convert current runs to ins wrapper
    convert_paragraph_runs_to_ins(p)
    # Prepend a del wrapper with old text (inserted after pPr)
    pPr = p.find(qn("pPr"))
    insert_pos = 1 if pPr is not None else 0
    del_elem = etree.Element(qn("del"))
    del_elem.set(qn("id"), next_rev())
    del_elem.set(qn("author"), AUTHOR)
    del_elem.set(qn("date"), DATE)
    r = etree.SubElement(del_elem, qn("r"))
    t = etree.SubElement(r, qn("delText"))
    t.text = old_text
    t.set(f"{{{XML_NS}}}space", "preserve")
    p.insert(insert_pos, del_elem)


def process():
    if OUT.exists():
        OUT.unlink()
    shutil.copy(V316A, OUT)
    print(f"Base: {V316A.name} -> {OUT.name}")

    # Extract paragraph texts
    v2_texts = extract_paragraphs_text(V2)
    v316_texts = extract_paragraphs_text(V316A)
    print(f"v2: {len(v2_texts)} paragraphs")
    print(f"v3.16: {len(v316_texts)} paragraphs")

    # Normalize for matching but preserve originals
    v2_norm = [normalize(t) for t in v2_texts]
    v316_norm = [normalize(t) for t in v316_texts]

    sm = SequenceMatcher(None, v2_norm, v316_norm, autojunk=False)
    opcodes = sm.get_opcodes()
    print(f"Opcodes: {len(opcodes)}")
    stats = {"equal": 0, "replace": 0, "insert": 0, "delete": 0}
    for tag, _, _, _, _ in opcodes:
        stats[tag] = stats.get(tag, 0) + 1
    print(f"  equal: {stats.get('equal', 0)}, replace: {stats.get('replace', 0)}, "
          f"insert: {stats.get('insert', 0)}, delete: {stats.get('delete', 0)}")

    # Build per-paragraph edits for v3.16 paragraphs
    v316_edit = [None] * len(v316_texts)  # ("replace", old_text) | "insert" | None
    # deletes are paragraphs present in v2 only; we'll insert them as "fully deleted"
    # paragraphs right before the v316 paragraph at index j1 of each delete op.
    delete_inserts = {}  # v316_idx -> list of texts to insert (as deleted) before this paragraph

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        if tag == "replace":
            # v2[i1:i2] replaced by v316[j1:j2]
            # Simple 1-to-1 matching: first v316[j1] becomes replace(v2[i1]),
            # extra v316 are inserts, extra v2 are deletes before j1.
            overlap = min(i2 - i1, j2 - j1)
            for k in range(overlap):
                v316_edit[j1 + k] = ("replace", v2_texts[i1 + k])
            # Extra v316 paragraphs are inserts
            for k in range(overlap, j2 - j1):
                v316_edit[j1 + k] = ("insert",)
            # Extra v2 paragraphs are deletes, inserted before j1+overlap (i.e., right after last replace)
            if i2 - i1 > j2 - j1:
                pos = j1 + overlap
                extra_deletes = v2_texts[i1 + overlap : i2]
                delete_inserts.setdefault(pos, []).extend(extra_deletes)
        elif tag == "insert":
            for k in range(j1, j2):
                v316_edit[k] = ("insert",)
        elif tag == "delete":
            # v2[i1:i2] are deleted; in v316 the position is j1 (== j2)
            delete_inserts.setdefault(j1, []).extend(v2_texts[i1:i2])

    # Open v316 docx, modify, save
    with zipfile.ZipFile(OUT, "r") as z:
        doc_xml = z.read("word/document.xml")
    tree = etree.fromstring(doc_xml)
    body = tree.find(qn("body"))

    # Get paragraphs in body order (we must keep a reference list, as we'll insert into body)
    v316_paragraphs = body.findall(qn("p"))
    if len(v316_paragraphs) != len(v316_texts):
        print(f"WARNING: mismatch {len(v316_paragraphs)} vs {len(v316_texts)}")

    n_replace = 0
    n_insert = 0
    n_delete_paras = 0

    # Iterate in reverse so insertions don't shift indices we haven't processed yet
    for idx in range(len(v316_paragraphs) - 1, -1, -1):
        p = v316_paragraphs[idx]
        edit = v316_edit[idx]

        # First apply the edit for this paragraph
        if edit:
            if edit[0] == "replace":
                wrap_paragraph_replace(p, edit[1])
                n_replace += 1
            elif edit[0] == "insert":
                convert_paragraph_runs_to_ins(p)
                n_insert += 1

        # Then insert any deleted paragraphs BEFORE this paragraph
        if idx in delete_inserts:
            texts = delete_inserts[idx]
            parent = p.getparent()
            parent_idx = list(parent).index(p)
            # Insert each deleted paragraph in order before p
            for del_text in texts:
                new_p = make_delete_paragraph(del_text, p)
                parent.insert(parent_idx, new_p)
                parent_idx += 1
                n_delete_paras += 1

    # Also handle deletes that should go at the very end (idx == len(v316_paragraphs))
    end_idx = len(v316_paragraphs)
    if end_idx in delete_inserts:
        for del_text in delete_inserts[end_idx]:
            ref = v316_paragraphs[-1] if v316_paragraphs else None
            new_p = make_delete_paragraph(del_text, ref) if ref is not None else None
            if new_p is not None:
                body.append(new_p)
                n_delete_paras += 1

    print(f"\nApplied: {n_replace} replaces, {n_insert} inserts, {n_delete_paras} deleted paragraphs")

    # Write back
    new_doc = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name
    with zipfile.ZipFile(OUT, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc)
                else:
                    zout.writestr(item, zin.read(item))
    shutil.move(tmp_path, OUT)
    print(f"\nOutput: {OUT}")
    print(f"Size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    process()
