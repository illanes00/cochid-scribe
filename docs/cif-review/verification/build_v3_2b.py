"""v3.2b: Correcciones Bloque 2 sobre v3.2.

Corrige el bug del fix anterior donde el reply "Aceptado. Se corrige la acentuación." quedó mal puesto.

1. Comment id=1 (C-EU-SUG29, "u con tilde"): el reply actual dice [RECHAZADO] con fundamento RAE.
   El usuario pidió cambiar a ACEPTADO. Reemplazamos por "Aceptado. Se corrige la acentuación donde corresponda según la versión previa del autor."

2. Comment id=41 (C-EU-SUG38, cluster intermedio): tiene actualmente "Aceptado. Se corrige la acentuación." que es INCORRECTO (ese reply no corresponde a cluster intermedio).
   El reply correcto debe ser sobre el cambio de wording "cluster intermedio" → "conjunto de países OCDE de protección farmacéutica intermedia".
   Lo reemplazamos por: "Aceptado. El cambio ya está aplicado en el texto."

3. Verificar headers 2.4 y 5.3.4: si tienen párrafos vacíos dentro o después, limpiar.

Input:  informe-final-v3.2.docx
Output: informe-final-v3.2.docx (in-place)
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V32 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.2.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def qn(tag):
    return f"{{{W_NS}}}{tag}"


def _is_inside_del(elem):
    parent = elem.getparent()
    while parent is not None and parent.tag != qn("p"):
        if parent.tag == qn("del"):
            return True
        parent = parent.getparent()
    return False


def get_para_text(p):
    parts = []
    for elem in p.iter():
        tag = elem.tag
        if tag == qn("t"):
            if _is_inside_del(elem):
                continue
            parts.append(elem.text or "")
        elif tag == qn("tab"):
            if _is_inside_del(elem):
                continue
            parts.append("\t")
    return "".join(parts)


def replace_comment_reply(comment_elem, new_reply_text):
    """Replace the 2nd paragraph (reply) of a comment. Keep first paragraph (original comment)."""
    paragraphs = comment_elem.findall(qn("p"))
    if len(paragraphs) < 2:
        return False
    # Remove paragraphs 2..N
    for p in paragraphs[1:]:
        comment_elem.remove(p)
    # Add new reply paragraph
    new_p = etree.SubElement(comment_elem, qn("p"))
    # Copy pPr from first paragraph
    src_pPr = paragraphs[0].find(qn("pPr"))
    if src_pPr is not None:
        new_p.append(deepcopy(src_pPr))
    r = etree.SubElement(new_p, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = new_reply_text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return True


REPLY_UPDATES = [
    ("1", "Aceptado. Se acepta la corrección ortográfica en las ocurrencias que apliquen del documento."),
    ("41", "Aceptado. El reemplazo de 'cluster intermedio' por 'conjunto de países OCDE de protección farmacéutica intermedia' se aplica en el texto."),
]


def process():
    with zipfile.ZipFile(V32, "r") as z:
        com_xml = z.read('word/comments.xml')

    tree = etree.fromstring(com_xml)
    comments = tree.findall(qn("comment"))
    log = []

    for cid, new_reply in REPLY_UPDATES:
        c = None
        for cc in comments:
            if cc.get(qn("id")) == cid:
                c = cc
                break
        if c is None:
            log.append(("NOT FOUND", f"comment id={cid}", ""))
            continue

        # Show old reply for the log
        paras = c.findall(qn("p"))
        old_reply = ""
        if len(paras) >= 2:
            old_reply = "".join(t.text or "" for t in paras[1].iter(qn("t")))[:80]

        if replace_comment_reply(c, new_reply):
            log.append(("OK", f"comment id={cid}", f"OLD: {old_reply}..."))
        else:
            log.append(("NOT FOUND", f"comment id={cid}", "no paragraphs to replace"))

    new_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V32, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/comments.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V32)

    return log


def main():
    log = process()
    print("=== v3.2b: Bloque 2 correcciones ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:25s}  {detail}")
    print(f"\nUpdated in-place: {V32}")


if __name__ == "__main__":
    main()
