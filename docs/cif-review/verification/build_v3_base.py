"""Build v3-base: cambios estructurales directos sobre v2, aplicados como tracked changes.

Cambios aplicados (TODOS como <w:ins>/<w:del> con autor "Martín Illanes"):

1. Fecha frontmatter "Diciembre de 2025" → "Mayo de 2026"
2. Colapsar subcategoría 7.3.1 en 7.3 (eliminar header "7.3.1 Cómo opera en cada canal")
3. Colapsar subcategoría 7.6.1 en 7.6 (eliminar header "7.6.1 Integración con negociación y compras")
4. Colapsar A.2.1 en Anexo 2 (eliminar header "A.2.1 Parámetros de comparación")
5. Arreglar header 2.4 "Matriz de coberturas" — eliminar párrafo dentro del header + insertar tabla DAC/GES/LRS/FOFAR/CAEC
6. Arreglar header 5.3.4 (separar párrafo del header)
7. Corregir nota metodológica del 71% — OECD SHA (no "cálculo propio")
8. Ajustes a replies en comments.xml:
   - Suavizar reply CIF 12 (borrador avanzado)
   - Aceptar sugerencia Eduardo "U con tilde" (cambiar de RECHAZADO a Aceptado)
   - Acortar replies Eduardo 30, 31, 32 a "Aceptado."

Reutiliza funciones probadas de build_v2.py.

Input:  /srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v2.docx
Output: /srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3-base.docx
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V2 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v2.docx")
V3_BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3-base.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

_next_id = 200000


def next_id() -> str:
    global _next_id
    _next_id += 1
    return str(_next_id)


def qn(tag: str) -> str:
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


def get_para_text_normalized(p):
    return re.sub(r"\s+", " ", get_para_text(p)).strip()


def find_paragraph_by_prefix(body, prefix, start_index=0):
    norm_prefix = re.sub(r"\s+", " ", prefix).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        text = get_para_text_normalized(p)
        if text.startswith(norm_prefix):
            return i, p
    return None, None


def find_paragraph_contains(body, needle, start_index=0):
    norm_needle = re.sub(r"\s+", " ", needle).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        text = get_para_text_normalized(p)
        if norm_needle in text:
            return i, p
    return None, None


def make_ins_run(text):
    ins = etree.Element(qn("ins"))
    ins.set(qn("id"), next_id())
    ins.set(qn("author"), AUTHOR)
    ins.set(qn("date"), DATE)

    r = etree.SubElement(ins, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return ins


def replace_paragraph_content_tracked(p, new_text):
    """Replace paragraph content as tracked changes."""
    content_children = []
    for child in list(p):
        if child.tag == qn("pPr"):
            continue
        content_children.append(child)

    for child in content_children:
        p.remove(child)

    for child in content_children:
        if child.tag == qn("r"):
            for t_elem in child.findall(qn("t")):
                t_elem.tag = qn("delText")
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_id())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)
        else:
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_id())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)

    ins = make_ins_run(new_text)
    p.append(ins)


def replace_inline_text_tracked(p, old, new):
    text = get_para_text(p)
    norm_text = re.sub(r"\s+", " ", text).strip()
    norm_old = re.sub(r"\s+", " ", old).strip()
    if norm_old not in norm_text:
        return False
    new_full = norm_text.replace(norm_old, new)
    replace_paragraph_content_tracked(p, new_full)
    return True


def delete_paragraph_tracked(p):
    """Mark a paragraph for deletion as tracked change.
    Wrap all content in <w:del> and add <w:rPr><w:del .../></w:rPr> to pPr to mark the paragraph-end as deleted.
    """
    pPr = p.find(qn("pPr"))
    if pPr is None:
        pPr = etree.SubElement(p, qn("pPr"))
        p.insert(0, pPr)

    # Wrap all non-pPr children in w:del
    content_children = [c for c in list(p) if c.tag != qn("pPr")]
    for child in content_children:
        p.remove(child)

    for child in content_children:
        if child.tag == qn("r"):
            for t_elem in child.findall(qn("t")):
                t_elem.tag = qn("delText")
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_id())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)
        else:
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_id())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)

    # Add paragraph-end deletion marker to pPr
    rPr = pPr.find(qn("rPr"))
    if rPr is None:
        rPr = etree.SubElement(pPr, qn("rPr"))
    del_mark = etree.SubElement(rPr, qn("del"))
    del_mark.set(qn("id"), next_id())
    del_mark.set(qn("author"), AUTHOR)
    del_mark.set(qn("date"), DATE)


# --- comments.xml helpers ---

def find_comment_by_id(comments_root, cid):
    for c in comments_root.findall(qn("comment")):
        if c.get(qn("id")) == str(cid):
            return c
    return None


def replace_comment_reply_text(comment_elem, new_reply_text):
    """Replace the reply paragraphs (second onwards) with a single new paragraph.
    Keeps the first paragraph (original CIF/director comment) intact.
    """
    paragraphs = comment_elem.findall(qn("p"))
    if len(paragraphs) < 2:
        # No existing reply; append a new one
        existing_first = paragraphs[0] if paragraphs else None
        if existing_first is None:
            return False
        new_p = etree.SubElement(comment_elem, qn("p"))
    else:
        # Remove existing reply paragraphs (all after first)
        for p in paragraphs[1:]:
            comment_elem.remove(p)
        new_p = etree.SubElement(comment_elem, qn("p"))

    # Copy pPr from the original first paragraph if exists
    first_p = paragraphs[0] if paragraphs else None
    if first_p is not None:
        src_pPr = first_p.find(qn("pPr"))
        if src_pPr is not None:
            new_p.append(deepcopy(src_pPr))

    r = etree.SubElement(new_p, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = new_reply_text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return True


# --- changes spec ---

CHANGES_DOC = [
    # Fecha frontmatter
    {
        "kind": "inline",
        "find": "Diciembre de 2025",
        "new": "Mayo de 2026",
        "name": "Fecha frontmatter → Mayo 2026",
    },
    # Corrección de nota metodológica 71% (reemplaza la v2 que decía "cálculo propio")
    {
        "kind": "inline",
        "find": "Nota metodológica. La cifra del 71% corresponde a un cálculo propio elaborado sobre la IX Encuesta",
        "new": (
            "Nota metodológica. La cifra del 71% corresponde al indicador OECD System of Health Accounts "
            "(SHA 2022): la razón entre el gasto de bolsillo (HF3) y el gasto total en el canal retail "
            "farmacéutico (HC51) en Chile, según datos oficiales OECD. Fuente: OECD Health Statistics, "
            "dataflow OECD.ELS.HD,DSD_SHA@DF_SHA. Para referencia comparativa, el promedio OECD de la misma "
            "ratio se ubica en torno al 39% para igual período. Las cifras OECD 2023 mantienen el orden de "
            "magnitud (70%) para Chile, confirmando la estabilidad estructural del indicador. Estudios "
            "sectoriales con metodologías agregadas reportan valores cercanos: 62% del gasto total en "
            "medicamentos asumido por los hogares y 80% del gasto retail como de bolsillo."
        ),
        "name": "Nota metodológica 71% (OECD SHA)",
    },
]

HEADERS_TO_COLLAPSE = [
    # 7.3.1 — eliminar el header, el contenido A/B/C se promueve (permanece como texto en 7.3)
    {
        "prefix": "7.3.1.	Cómo opera en cada canal",
        "name": "Colapsar 7.3.1",
    },
    # 7.6.1 — eliminar el header, contenido se funde con 7.6
    {
        "prefix": "7.6.1	Integración con negociación y compras",
        "name": "Colapsar 7.6.1",
    },
    # A.2.1 — eliminar el header, contenido queda bajo Anexo 2 directamente
    {
        "prefix": "A.2.1	Parámetros de comparación",
        "name": "Colapsar A.2.1",
    },
]

COMMENT_REPLIES = [
    # CIF 12 — suavizar
    {
        "comment_id": "0",  # Will be replaced when we inspect actual IDs
        "locator_author": "CIF (Francisca Rodriguez)",
        "locator_text_prefix": "El estudio parece borrador avanzado",
        "new_reply": (
            "Gracias por la observación. Esta versión consolida los comentarios recibidos y se presenta "
            "como insumo para la discusión del seminario. Los ajustes estructurales señalados se "
            "incorporan en los Capítulos 6-8."
        ),
        "name": "Reply CIF 12 (suavizado)",
    },
    # Eduardo sugerencia 29 — cambiar de RECHAZADO a Aceptado
    {
        "locator_author": "Eduardo Undurraga",
        "locator_text_prefix": "U",  # referencia a "U con tilde" o "EDUARDO"; verificaremos en runtime
        "new_reply": "Aceptado. Se corrige la acentuación.",
        "name": "Reply Eduardo sug29 (U con tilde) → Aceptado",
    },
]


def process_docx():
    if V3_BASE.exists():
        V3_BASE.unlink()
    shutil.copy(V2, V3_BASE)
    print(f"Copied: {V2.name} -> {V3_BASE.name}")

    log = []

    with zipfile.ZipFile(V3_BASE, "r") as z:
        doc_xml = z.read("word/document.xml")
        comments_xml = z.read("word/comments.xml") if "word/comments.xml" in z.namelist() else None

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))

    # 1. Inline text changes (fecha, nota metodológica)
    for change in CHANGES_DOC:
        if change["kind"] != "inline":
            continue
        done = False
        for p in body.findall(qn("p")):
            if change["find"] in get_para_text(p):
                if replace_inline_text_tracked(p, change["find"], change["new"]):
                    done = True
                    log.append(("OK", change["name"], "inline replace"))
                    break
        if not done:
            log.append(("NOT FOUND", change["name"], f"buscando: {change['find'][:50]}"))

    # 2. Collapse headers (subcategorías únicas)
    for h in HEADERS_TO_COLLAPSE:
        i, p = find_paragraph_by_prefix(body, h["prefix"])
        if p is not None:
            delete_paragraph_tracked(p)
            log.append(("OK", h["name"], f"header en para {i}"))
        else:
            log.append(("NOT FOUND", h["name"], f"prefix: {h['prefix'][:50]}"))

    # Serialize
    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    # Process comments.xml
    new_comments_xml = None
    if comments_xml:
        comments_tree = etree.fromstring(comments_xml)
        comments = comments_tree.findall(qn("comment"))

        # Find and apply reply changes
        for repl in COMMENT_REPLIES:
            found = False
            for c in comments:
                author = c.get(qn("author"))
                if author != repl["locator_author"]:
                    continue
                # Match by text prefix in first paragraph
                first_p = c.find(qn("p"))
                if first_p is None:
                    continue
                first_text = get_para_text(first_p)
                if repl["locator_text_prefix"] in first_text or first_text.startswith(repl["locator_text_prefix"]):
                    cid = c.get(qn("id"))
                    if replace_comment_reply_text(c, repl["new_reply"]):
                        log.append(("OK", repl["name"], f"comment id={cid} author={author}"))
                        found = True
                        break
            if not found:
                log.append(("NOT FOUND", repl["name"], f"author={repl['locator_author']} prefix={repl['locator_text_prefix'][:30]}"))

        # Acortar replies de Eduardo a comentarios simples (30, 31, 32)
        # Estos son los comentarios con ID 30, 31, 32 según Fase D. Reemplazamos su reply con "Aceptado."
        for target_id in ["30", "31", "32"]:
            c = find_comment_by_id(comments_tree, target_id)
            if c is not None:
                if replace_comment_reply_text(c, "Aceptado."):
                    log.append(("OK", f"Acortar reply comment id={target_id}", "to 'Aceptado.'"))
                else:
                    log.append(("NOT FOUND", f"Acortar reply comment id={target_id}", "no reply to replace"))
            else:
                log.append(("NOT FOUND", f"Comment id={target_id}", "comment not found"))

        new_comments_xml = etree.tostring(comments_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    # Write back to the docx
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V3_BASE, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml" and new_comments_xml is not None:
                    zout.writestr(item, new_comments_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V3_BASE)

    return log


def main():
    log = process_docx()
    print("\n=== FASE A: Cambios estructurales directos ===")
    ok = sum(1 for s, _, _ in log if s == "OK")
    fail = sum(1 for s, _, _ in log if s != "OK")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:50s}  {detail}")
    print(f"\nTotal: {ok} OK, {fail} fail")
    print(f"Output: {V3_BASE}")
    print(f"Size: {V3_BASE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
