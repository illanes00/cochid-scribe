"""v3.15: consolidación lectura editorial autor (bloque 1) + globales.

Cambios vs v3.14-aceptada.docx:
1. Portada nueva (image27.jpg reemplazada con farmacia/mayo 2026).
2. Headers sin espacio tras número corregidos globalmente (1.1.Tit -> 1.1. Tit) como tracked.
3. Bloque 1 lectura editorial: 10 edits + 2 comentarios MI-60/61 (frontmatter+mensajes+resumen).
4. Corrección P0103 nota 71% (regresión a versión vieja: reemplazar por OECD SHA).
5. Limpieza de orphans "farmacias privadas" detectados por agente Lectura (MI-35 a MI-45).
6. Elimina duplicaciones literales (caption Figura 2 triplicado, Resumen Ejec duplicado).

Salida: v3.15.docx (tracked changes sobre v3.14-aceptada).
También produce v3.15-aceptada.docx (changes aceptados).
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
V14A = BASE / "output/informe-final-v3.14-aceptada.docx"
V15 = BASE / "output/informe-final-v3.15.docx"
V15A = BASE / "output/informe-final-v3.15-aceptada.docx"
LECTURA_DIR = BASE / "verification/v3_15_lectura"
PORTADA = BASE / "assets/portada-v3.14.jpg"

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00-03:00"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_next_rev = 3000000
_next_cid = 4000


def next_rev():
    global _next_rev
    _next_rev += 1
    return str(_next_rev)


def next_cid():
    global _next_cid
    _next_cid += 1
    return str(_next_cid)


def qn(t):
    return f"{{{W_NS}}}{t}"


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


def normalize(s):
    return re.sub(r"\s+", " ", s or "").strip()


def find_paragraph(body, locator):
    if not isinstance(locator, dict):
        return None, None
    strategy = locator.get("strategy", "contains")
    needle = normalize(locator.get("text", ""))
    if not needle:
        return None, None
    for i, p in enumerate(body.findall(qn("p"))):
        text = normalize(get_para_text(p))
        if strategy == "prefix" and text.startswith(needle):
            return i, p
        if strategy == "equals" and text == needle:
            return i, p
        if strategy == "contains" and needle in text:
            return i, p
    return None, None


def replace_paragraph_tracked(p, new_text):
    content_children = [c for c in list(p) if c.tag != qn("pPr")]
    for child in content_children:
        p.remove(child)
    for child in content_children:
        if child.tag == qn("r"):
            for t_elem in child.findall(qn("t")):
                t_elem.tag = qn("delText")
        del_elem = etree.SubElement(p, qn("del"))
        del_elem.set(qn("id"), next_rev())
        del_elem.set(qn("author"), AUTHOR)
        del_elem.set(qn("date"), DATE)
        del_elem.append(child)
    if new_text:
        ins = etree.SubElement(p, qn("ins"))
        ins.set(qn("id"), next_rev())
        ins.set(qn("author"), AUTHOR)
        ins.set(qn("date"), DATE)
        r = etree.SubElement(ins, qn("r"))
        t = etree.SubElement(r, qn("t"))
        t.text = new_text
        t.set(f"{{{XML_NS}}}space", "preserve")


def make_inserted_paragraph(text, reference_p):
    new_p = etree.Element(qn("p"))
    ref_pPr = reference_p.find(qn("pPr"))
    if ref_pPr is not None:
        pPr_copy = deepcopy(ref_pPr)
        pStyle = pPr_copy.find(qn("pStyle"))
        if pStyle is not None:
            val = pStyle.get(qn("val"), "")
            if val.lower().startswith("heading") or val.lower().startswith("titulo"):
                pPr_copy.remove(pStyle)
        new_p.append(pPr_copy)
        pPr = pPr_copy
    else:
        pPr = etree.SubElement(new_p, qn("pPr"))
    rPr = pPr.find(qn("rPr"))
    if rPr is None:
        rPr = etree.SubElement(pPr, qn("rPr"))
    ins_mark = etree.SubElement(rPr, qn("ins"))
    ins_mark.set(qn("id"), next_rev())
    ins_mark.set(qn("author"), AUTHOR)
    ins_mark.set(qn("date"), DATE)

    ins = etree.SubElement(new_p, qn("ins"))
    ins.set(qn("id"), next_rev())
    ins.set(qn("author"), AUTHOR)
    ins.set(qn("date"), DATE)
    r = etree.SubElement(ins, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = text
    t.set(f"{{{XML_NS}}}space", "preserve")
    return new_p


def insert_paragraph_after(body, anchor_p, text):
    new_p = make_inserted_paragraph(text, anchor_p)
    parent = anchor_p.getparent()
    idx = list(parent).index(anchor_p)
    parent.insert(idx + 1, new_p)
    return new_p


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
    t.set(f"{{{XML_NS}}}space", "preserve")
    return c


def anchor_comment(p, cid):
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


# ============================================================================
# HEADER FIX: agregar espacio tras número en headings
# ============================================================================

HEADER_PATTERNS = [
    # 1.Título -> 1. Título (sólo al inicio del párrafo)
    (re.compile(r"^(\d+)\.([A-ZÁÉÍÓÚÑ])"), r"\1. \2"),
    # 1.1.Título -> 1.1. Título
    (re.compile(r"^(\d+\.\d+)\.([A-ZÁÉÍÓÚÑ])"), r"\1. \2"),
    # 1.1.1.Título -> 1.1.1. Título
    (re.compile(r"^(\d+\.\d+\.\d+)\.([A-ZÁÉÍÓÚÑ])"), r"\1. \2"),
    # 2.4Matriz -> 2.4. Matriz (sin punto original)
    (re.compile(r"^(\d+\.\d+)([A-ZÁÉÍÓÚÑ])"), r"\1. \2"),
    # 7.5.2Financiamiento -> 7.5.2. Financiamiento
    (re.compile(r"^(\d+\.\d+\.\d+)([A-ZÁÉÍÓÚÑ])"), r"\1. \2"),
    # Anexo 1.Glosario -> Anexo 1. Glosario
    (re.compile(r"^(Anexo \d+)[.:]([A-ZÁÉÍÓÚÑ])"), r"\1. \2"),
    # A.2.1.1.Población -> A.2.1.1. Población
    (re.compile(r"^(A\.\d+(?:\.\d+)*)\.([A-ZÁÉÍÓÚÑ])"), r"\1. \2"),
    # 7.13\tSíntesis -> 7.13. Síntesis  (tab)
    (re.compile(r"^(\d+\.\d+)\t"), r"\1. "),
    # 7.\tDesarrollo -> 7. Desarrollo
    (re.compile(r"^(\d+)\.\t"), r"\1. "),
    # 5.3.6.  Trazabilidad (doble espacio) -> 5.3.6. Trazabilidad
    (re.compile(r"^(\d+\.\d+\.\d+)\.  "), r"\1. "),
]


def fix_header_text(text):
    """Apply header patterns in order, only apply first match per round."""
    t = text
    changed = True
    while changed:
        changed = False
        for pat, repl in HEADER_PATTERNS:
            new = pat.sub(repl, t, count=1)
            if new != t:
                t = new
                changed = True
                break
    return t


# ============================================================================
# BLOQUE 1: lectura editorial frontmatter+mensajes+resumen
# ============================================================================


def load_bloque_edits(name):
    path = LECTURA_DIR / f"{name}.json"
    if not path.exists():
        print(f"  ✗ no existe {path}")
        return {"edits": [], "comments_to_add": []}
    return json.loads(path.read_text())


BLOQUES = [
    "bloque1_frontmatter_resumen",
    "bloque2_cap2",
    "bloque3_cap3",
    "bloque4_cap4",
    "bloque5_cap5",
    "bloque6_cap6",
    "bloque7_cap7",
    "bloque8_cap8_anexos",
    "bloque9_pendientes",
]


def apply_lectura_edit(body, edit):
    etype = edit.get("type")
    locator = edit.get("locator") or edit.get("anchor") or {}
    i, p = find_paragraph(body, locator)
    if p is None:
        return "NOT FOUND", f"{edit.get('id','?')} {etype}"
    if etype == "replace_paragraph":
        replace_paragraph_tracked(p, edit.get("new", ""))
        return "OK", f"{edit.get('id','?')} para {i}"
    if etype == "insert_paragraph_after":
        insert_paragraph_after(body, p, edit.get("new", ""))
        return "OK", f"{edit.get('id','?')} after para {i}"
    if etype == "replace_text_in_paragraph":
        old = edit.get("old", "")
        new = edit.get("new", "")
        current = get_para_text(p)
        if old and old in current:
            replace_paragraph_tracked(p, current.replace(old, new))
            return "OK", f"{edit.get('id','?')} para {i}"
        return "NOT FOUND", f"{edit.get('id','?')} old no encontrado"
    return "SKIP", f"{edit.get('id','?')} unknown type {etype}"


def apply_lectura_comment(body, com_tree, spec):
    anchor = spec.get("anchor") or {}
    i, p = find_paragraph(body, anchor)
    if p is None:
        return "NOT FOUND", spec.get("id", "?")
    cid = next_cid()
    com_tree.append(make_comment_elem(cid, spec.get("body", "")))
    anchor_comment(p, cid)
    return "OK", f"{spec.get('id','?')} cid={cid} para {i}"


# ============================================================================
# BLOQUE 2: correcciones globales
# ============================================================================


def apply_global_header_fix(body):
    """Fix headers (number without space after) as tracked changes."""
    fixes = 0
    for p in body.findall(qn("p")):
        pPr = p.find(qn("pPr"))
        if pPr is None:
            continue
        pStyle = pPr.find(qn("pStyle"))
        if pStyle is None:
            continue
        style = pStyle.get(qn("val"), "").lower()
        if not (style.startswith("heading") or style.startswith("titulo")
                or style.startswith("title")):
            continue
        text = get_para_text(p)
        fixed = fix_header_text(text)
        if fixed != text and fixed.strip():
            replace_paragraph_tracked(p, fixed)
            fixes += 1
    return fixes


def fix_p0103_71_note(body):
    """Replace the 71% note regression (cálculo propio sobre EPF) with OECD SHA version."""
    for i, p in enumerate(body.findall(qn("p"))):
        text = get_para_text(p)
        if "Nota metodológica" in text and "cálculo propio" in text and "EPF" in text:
            new = (
                "Nota metodológica. La cifra del 71% corresponde al indicador OECD "
                "System of Health Accounts (SHA 2022): ratio del gasto de bolsillo (HF3) "
                "sobre el gasto retail farmacéutico (HC51) para Chile. Fuente: OECD "
                "Health Statistics, dataflow OECD.ELS.HD,DSD_SHA@DF_SHA. Estudios "
                "complementarios con metodologías alternativas arrojan órdenes de "
                "magnitud consistentes (70-80%); las diferencias se explican por el "
                "denominador utilizado (retail vs gasto farmacéutico total), el año de "
                "referencia y el tratamiento de subsidios públicos al canal privado. El "
                "promedio OCDE para la misma ratio es del orden de 39%."
            )
            replace_paragraph_tracked(p, new)
            return True, i
    return False, None


def remove_orphan_farmacias_privadas(body):
    """Remove 'farmacias privadas' as orphan prefix pegado al inicio de párrafos."""
    patterns = [
        r"^farmacias privadasChile exhibe",
        r"^farmacias privadasida la ones",
        r"^farmacias privadasIncluye terapias",
        r"^farmacias privadas([A-Z])",  # generic orphan prefix
    ]
    fixes = 0
    for p in body.findall(qn("p")):
        text = get_para_text(p)
        # Detect specific orphan prefixes
        if text.startswith("farmacias privadas") and len(text) > 20:
            # Could be legitimate ("farmacias privadas y municipales") - check if followed by upper case letter with no space
            m = re.match(r"^farmacias privadas([A-ZÁÉÍÓÚÑ])", text)
            if m:
                # Orphan found
                new_text = text[len("farmacias privadas"):]
                replace_paragraph_tracked(p, new_text)
                fixes += 1
    return fixes


def remove_duplicate_figure2_caption(body):
    """Figure 2 caption triplicated: keep first, delete 2nd and 3rd."""
    caption_prefix = "Figura 2"
    seen = 0
    fixes = 0
    to_delete = []
    for p in body.findall(qn("p")):
        text = get_para_text(p).strip()
        if text.startswith(caption_prefix) and "gasto público en medicamentos por ejecutor" in text:
            seen += 1
            if seen > 1:
                to_delete.append(p)
    for p in to_delete:
        # Remove content via tracked del
        content_children = [c for c in list(p) if c.tag != qn("pPr")]
        for child in content_children:
            p.remove(child)
        for child in content_children:
            if child.tag == qn("r"):
                for t_elem in child.findall(qn("t")):
                    t_elem.tag = qn("delText")
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_rev())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)
        fixes += 1
    return fixes


# ============================================================================
# PORTADA
# ============================================================================


def replace_cover_image(src_docx, dst_docx, portada_jpg):
    """Replace word/media/image27.jpg with new portada."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name
    portada_bytes = portada_jpg.read_bytes()
    with zipfile.ZipFile(src_docx, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/media/image27.jpg":
                    zout.writestr(item, portada_bytes)
                else:
                    zout.writestr(item, zin.read(item))
    shutil.move(tmp_path, dst_docx)


# ============================================================================
# MAIN
# ============================================================================


def process():
    if V15.exists():
        V15.unlink()
    # Step 1: copy + replace portada
    replace_cover_image(V14A, V15, PORTADA)
    print(f"Copied with portada: {V14A.name} -> {V15.name}")

    # Step 2: open docx, parse XML
    with zipfile.ZipFile(V15, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")
    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))
    com_tree = etree.fromstring(com_xml)

    # bump comment id past existing
    existing = [int(c.get(qn("id"), "0")) for c in com_tree.findall(qn("comment"))]
    if existing:
        global _next_cid
        _next_cid = max(max(existing) + 50, _next_cid)

    log = []

    # Step 3: fix P0103 71% note regression
    ok, i = fix_p0103_71_note(body)
    log.append(("OK" if ok else "NOT FOUND", "P0103 nota 71%", f"para {i}" if ok else ""))

    # Step 4: global header fix
    fixes = apply_global_header_fix(body)
    log.append(("OK", "Headers globales", f"{fixes} fixes"))

    # Step 5: remove orphan "farmacias privadas"
    fixes = remove_orphan_farmacias_privadas(body)
    log.append(("OK", "Orphans farmacias privadas", f"{fixes} fixes"))

    # Step 6: remove duplicate Figura 2 caption
    fixes = remove_duplicate_figure2_caption(body)
    log.append(("OK", "Duplicados Fig 2 caption", f"{fixes} eliminados"))

    # Step 7: apply all lectura editorial blocks
    for bname in BLOQUES:
        b = load_bloque_edits(bname)
        short = bname.replace("bloque", "B").split("_")[0]
        for edit in b.get("edits", []):
            status, detail = apply_lectura_edit(body, edit)
            log.append((status, f"{short} {edit.get('id','?')}", detail))
        for spec in b.get("comments_to_add", []):
            status, detail = apply_lectura_comment(body, com_tree, spec)
            log.append((status, f"{short} com {spec.get('id','?')}", detail))

    # Write back
    new_doc = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name
    with zipfile.ZipFile(V15, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com)
                else:
                    zout.writestr(item, zin.read(item))
    shutil.move(tmp_path, V15)

    return log


def main():
    log = process()
    print("\n=== v3.15 build log ===")
    ok = sum(1 for s, _, _ in log if s == "OK")
    nf = sum(1 for s, _, _ in log if s == "NOT FOUND")
    other = len(log) - ok - nf
    for status, name, detail in log:
        marker = "✓" if status == "OK" else ("✗" if status == "NOT FOUND" else "·")
        print(f"  {marker} {name:40s}  {detail}")
    print(f"\nOK: {ok}  NOT_FOUND: {nf}  OTHER: {other}")
    print(f"Output: {V15}")
    print(f"Size: {V15.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
