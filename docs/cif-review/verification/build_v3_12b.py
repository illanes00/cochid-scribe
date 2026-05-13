"""v3.12b: agregar MI-02 y MI-11 con anchors específicos sobre v3.12."""

from __future__ import annotations
import re, shutil, tempfile, zipfile
from copy import deepcopy
from pathlib import Path
from lxml import etree

V312 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.12.docx")
V312B = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.12b.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def qn(t): return f"{{{W_NS}}}{t}"


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
        if elem.tag == qn("t") and not _is_inside_del(elem):
            parts.append(elem.text or "")
        elif elem.tag == qn("tab") and not _is_inside_del(elem):
            parts.append("\t")
    return "".join(parts)


def make_comment_elem(cid, text):
    c = etree.Element(qn("comment"))
    c.set(qn("id"), cid)
    c.set(qn("author"), AUTHOR)
    c.set(qn("date"), DATE)
    c.set(qn("initials"), "MI")
    p = etree.SubElement(c, qn("p"))
    r = etree.SubElement(p, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return c


def anchor_comment_to_paragraph(p, cid):
    pPr = p.find(qn("pPr"))
    pos = 0 if pPr is None else 1
    cr_start = etree.Element(qn("commentRangeStart"))
    cr_start.set(qn("id"), cid)
    cr_end = etree.Element(qn("commentRangeEnd"))
    cr_end.set(qn("id"), cid)
    r_ref = etree.Element(qn("r"))
    rPr = etree.SubElement(r_ref, qn("rPr"))
    rStyle = etree.SubElement(rPr, qn("rStyle"))
    rStyle.set(qn("val"), "CommentReference")
    cref = etree.SubElement(r_ref, qn("commentReference"))
    cref.set(qn("id"), cid)
    p.insert(pos, cr_start)
    p.append(cr_end)
    p.append(r_ref)


ITEMS = [
    {
        "code": "MI-02",
        "target_para_idx": 225,  # "2.3. Financiamiento y ejecutores de gasto"
        "body": (
            "[MI-02] Estado dual: comprador directo + asegurador obligatorio. El Estado chileno "
            "opera simultáneamente como (i) comprador directo vía programas propios (Servicios de "
            "Salud, PNI, Ricarte Soto, DAC) y (ii) asegurador obligatorio que recauda cotizaciones "
            "7% para financiar FONASA. Esta distinción es metodológicamente relevante aunque el "
            "ejercicio presupuestario reporta el gasto agregado sin etiquetar la fuente. Responde "
            "a Carla Castillo (DOCX40)."
        ),
    },
    {
        "code": "MI-11",
        "target_para_idx": 678,  # "Lo gratis sigue gratis"
        "body": (
            "[MI-11] Principio 'lo gratis sigue gratis'. El BFAU no quita beneficios actuales (APS "
            "arsenal, GES tramo A/B). Agrega una capa focalizada por exposición al gasto, no "
            "homogeneiza canastas universalmente. Para afiliados ISAPRE: accede al subsidio BFAU "
            "cuando el gasto de bolsillo acumulado supera el tope, sin modificar su plan base. "
            "Responde a Carla Castillo (DOCX140)."
        ),
    },
]


def process():
    if V312B.exists():
        V312B.unlink()
    shutil.copy(V312, V312B)
    print(f"Copied: {V312.name} -> {V312B.name}")

    with zipfile.ZipFile(V312B, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))
    com_tree = etree.fromstring(com_xml)
    paragraphs = body.findall(qn("p"))

    # Max ID
    existing_ids = [int(c.get(qn("id"), "0")) for c in com_tree.findall(qn("comment"))]
    max_id = max(existing_ids) if existing_ids else 0
    next_id = max(max_id + 1, 1010)

    log = []
    for spec in ITEMS:
        idx = spec["target_para_idx"]
        if idx >= len(paragraphs):
            log.append(("OUT OF RANGE", spec["code"], ""))
            continue
        p = paragraphs[idx]
        text_preview = get_para_text(p)[:60]

        cid = str(next_id)
        next_id += 1

        comment_elem = make_comment_elem(cid, spec["body"])
        com_tree.append(comment_elem)

        anchor_comment_to_paragraph(p, cid)
        log.append(("OK", f"{spec['code']} (cid={cid}, para {idx})", text_preview))

    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V312B, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V312B)

    # Replace V312 with V312B in place
    shutil.move(V312B, V312)

    return log


def main():
    log = process()
    print("=== v3.12b MI-02 + MI-11 (in-place) ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:30s}  {detail}")


if __name__ == "__main__":
    main()
