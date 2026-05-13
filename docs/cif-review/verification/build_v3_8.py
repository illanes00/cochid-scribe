"""Build v3.8: consolidar Agente C + feedback Cap 2 final (Carla 40, 53, 54, 56, 57, 58).

Sobre v3.7.

Input:  informe-final-v3.7.docx
Output: informe-final-v3.8.docx
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

V37 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.7.docx")
V38 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.8.docx")
JSON_C = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/edits_agenteC.json")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_id = 900000


def next_id():
    global _next_id
    _next_id += 1
    return str(_next_id)


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
        if elem.tag == qn("t") and not _is_inside_del(elem):
            parts.append(elem.text or "")
        elif elem.tag == qn("tab") and not _is_inside_del(elem):
            parts.append("\t")
    return "".join(parts)


def get_para_text_normalized(p):
    return re.sub(r"\s+", " ", get_para_text(p)).strip()


def find_paragraph_by_prefix(body, prefix, start_index=0):
    norm_prefix = re.sub(r"\s+", " ", prefix).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        if get_para_text_normalized(p).startswith(norm_prefix):
            return i, p
    return None, None


def find_paragraph_contains(body, needle, start_index=0):
    norm_needle = re.sub(r"\s+", " ", needle).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        if norm_needle in get_para_text_normalized(p):
            return i, p
    return None, None


def replace_paragraph_content_tracked(p, new_text):
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
    ins = etree.SubElement(p, qn("ins"))
    ins.set(qn("id"), next_id())
    ins.set(qn("author"), AUTHOR)
    ins.set(qn("date"), DATE)
    r = etree.SubElement(ins, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = new_text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def make_inserted_paragraph_like(text, reference_p, is_heading=False):
    new_p = etree.Element(qn("p"))
    ref_pPr = reference_p.find(qn("pPr"))
    if ref_pPr is not None:
        pPr = deepcopy(ref_pPr)
        if not is_heading:
            for pStyle in pPr.findall(qn("pStyle")):
                val = pStyle.get(qn("val"))
                if val and val.startswith("Heading"):
                    pPr.remove(pStyle)
        new_p.append(pPr)
    else:
        pPr = etree.SubElement(new_p, qn("pPr"))
    rPr = pPr.find(qn("rPr"))
    if rPr is None:
        rPr = etree.SubElement(pPr, qn("rPr"))
    ins_mark = etree.SubElement(rPr, qn("ins"))
    ins_mark.set(qn("id"), next_id())
    ins_mark.set(qn("author"), AUTHOR)
    ins_mark.set(qn("date"), DATE)
    ins = etree.SubElement(new_p, qn("ins"))
    ins.set(qn("id"), next_id())
    ins.set(qn("author"), AUTHOR)
    ins.set(qn("date"), DATE)
    r = etree.SubElement(ins, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return new_p


def replace_comment_reply(comment_elem, new_reply_text):
    paragraphs = comment_elem.findall(qn("p"))
    if len(paragraphs) < 2:
        new_p = etree.SubElement(comment_elem, qn("p"))
        if paragraphs:
            src_pPr = paragraphs[0].find(qn("pPr"))
            if src_pPr is not None:
                new_p.insert(0, deepcopy(src_pPr))
    else:
        for p in paragraphs[1:]:
            comment_elem.remove(p)
        new_p = etree.SubElement(comment_elem, qn("p"))
        src_pPr = paragraphs[0].find(qn("pPr"))
        if src_pPr is not None:
            new_p.append(deepcopy(src_pPr))
    r = etree.SubElement(new_p, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = new_reply_text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return True


def apply_edit(body, edit):
    etype = edit.get("type")
    if etype == "replace_paragraph":
        loc = edit["locator"]
        mode = loc.get("mode", "prefix")
        value = loc["value"]
        if mode == "prefix":
            i, p = find_paragraph_by_prefix(body, value)
        else:
            i, p = find_paragraph_contains(body, value)
        if p is None:
            return "NOT FOUND", f"{value[:60]}..."
        replace_paragraph_content_tracked(p, edit["new"])
        return "OK", f"para {i}"
    elif etype == "insert_paragraph":
        anchor = edit.get("anchor") or edit.get("locator") or {}
        mode = anchor.get("mode", "contains")
        value = anchor.get("value", "")
        position = edit.get("position", "after")
        style = edit.get("style")
        text = edit.get("text") or edit.get("new", "")
        if not value:
            return "NO ANCHOR", ""
        if mode == "prefix":
            i, anchor_p = find_paragraph_by_prefix(body, value)
        else:
            i, anchor_p = find_paragraph_contains(body, value)
        if anchor_p is None:
            return "NOT FOUND", f"{value[:60]}..."
        is_heading = style == "Heading2"
        new_p = make_inserted_paragraph_like(text, anchor_p, is_heading=is_heading)
        if position == "before":
            anchor_p.addprevious(new_p)
        else:
            anchor_p.addnext(new_p)
        return "OK", f"insert {position} para {i}"
    return "UNKNOWN", etype


# Feedback específico Cap 2 final del usuario
REPLIES_CAP2_FINAL = {
    "56": (  # CC-DOCX40 — separar impuestos vs 7%
        "Aceptado y matizado. La distinción entre financiamiento contributivo (cotización 7% obligatoria) "
        "y tributario (impuestos generales) dentro de FONASA es metodológicamente relevante, aunque "
        "el ejercicio presupuestario reporta gasto agregado sin etiquetar la fuente. En términos "
        "conceptuales, el Estado opera simultáneamente como (i) comprador directo vía programas propios "
        "(Servicios de Salud, PNI, Ricarte Soto, DAC), y (ii) asegurador obligatorio que recauda "
        "cotizaciones del 7% para financiar el plan FONASA. Se agrega nota al texto explicitando esta "
        "doble naturaleza para evitar la interpretación de que el Estado solo ejecuta recursos "
        "tributarios."
    ),
    "57": (  # CC-DOCX53 — qué proyecto exactamente
        "Aceptado. La referencia corresponde al 'Plan de Salud Universal' elaborado por el MINSAL durante "
        "el segundo gobierno Piñera (Ministerio de Salud, 2020), que definía un conjunto priorizado de "
        "prestaciones con copagos protegidos y listado explícito de medicamentos ambulatorios. Se cita en "
        "formato APA: Ministerio de Salud de Chile (2020), 'Bases para una política sostenible de acceso "
        "a medicamentos', Subsecretaría de Redes Asistenciales. Se incorpora la cita al texto."
    ),
    "58": (  # CC-DOCX54 — MLE/MAI
        "El Beneficio Farmacéutico Ambulatorio Universal (BFAU) opera independientemente de la "
        "modalidad MLE/MAI de FONASA: aplica a ambas con canasta y copagos comunes. La diferencia "
        "operativa está en el punto de dispensación (APS/hospital en MAI; farmacia retail en MLE), "
        "pero las reglas de cobertura, copagos protegidos y tope anual son homogéneas. La articulación "
        "con los programas específicos (GES, LRS, DAC, FOFAR) se da por jerarquía: cuando un "
        "medicamento está cubierto por un régimen específico, se aplican las reglas de ese régimen; el "
        "BFAU actúa como piso para medicamentos fuera de esos regímenes."
    ),
    "59": (  # CC-DOCX56 — compras públicas ChileCompra
        "Precisado. ChileCompra y las compras públicas operan principalmente como mecanismo de "
        "intermediación de demanda institucional (hospitales, APS, CENABAST), no como canal de "
        "cobertura retail directa. Una extensión posible, que se deja abierta como propuesta a discutir "
        "en el seminario, es que CENABAST (bajo Ley 21.198) intermedie también para farmacias privadas "
        "con precios máximos transparentes, ampliando el efecto pro-competencia hacia el retail. Esta "
        "opción se desarrolla en la sección 7.6.1 como uno de los instrumentos pro-competencia."
    ),
    "60": (  # CC-DOCX57 — regulación precios retail
        "Sí, la regulación de precios de referencia aplica al canal retail: establece un precio máximo "
        "cubierto por el subsidio del BFAU vinculado al precio del medicamento bioequivalente más "
        "económico dentro del mismo grupo terapéutico. Esto cumple dos funciones: (i) evita que el "
        "aumento de cobertura se traduzca en inflación de precios en retail (captura del subsidio por "
        "las farmacias), y (ii) orienta la sustitución hacia el medicamento de menor precio dentro del "
        "grupo. Si el paciente elige un medicamento de precio superior al de referencia, la diferencia "
        "queda a su cargo. Se agrega esta precisión al texto de la sección correspondiente."
    ),
    "61": (  # CC-DOCX58 — política universal sustitución + bioequivalencia
        "Aceptado. La sustitución obligatoria por bioequivalente requiere como condición previa o "
        "simultánea una política universal de sustitución con listados ampliados de bioequivalencia y "
        "biosimilaridad. El listado ISP actual es acotado y no cubre universos terapéuticos completos; "
        "la ampliación es una pieza técnica fundamental para que la política de precios de referencia "
        "funcione. Se incorpora párrafo específico en la sección 7.4.3 (Sustitución genérica/"
        "bioequivalencia) planteando la ampliación del listado ISP como condición habilitante, junto con "
        "certificación obligatoria para todos los medicamentos de síntesis química y estándares "
        "explícitos para biosimilares."
    ),
}


def process_docx():
    if V38.exists():
        V38.unlink()
    shutil.copy(V37, V38)
    print(f"Copied: {V37.name} -> {V38.name}")

    log = []

    with zipfile.ZipFile(V38, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))
    com_tree = etree.fromstring(com_xml)

    # === Agente C: edits ===
    with open(JSON_C) as f:
        data_c = json.load(f)

    for i, edit in enumerate(data_c.get("edits", [])):
        status, detail = apply_edit(body, edit)
        log.append((status, f"C edit #{i+1}", detail))

    # === Cap 2 feedback final (replies) ===
    for cid, new_reply in REPLIES_CAP2_FINAL.items():
        c = next((cc for cc in com_tree.findall(qn("comment")) if cc.get(qn("id")) == cid), None)
        if c is None:
            log.append(("NOT FOUND", f"reply id={cid}", ""))
            continue
        replace_comment_reply(c, new_reply)
        log.append(("OK", f"Cap2 reply id={cid}", ""))

    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V38, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V38)

    return log


def main():
    log = process_docx()
    ok = sum(1 for s, _, _ in log if s == "OK")
    fail = sum(1 for s, _, _ in log if s != "OK")
    print(f"\n=== v3.8: Agente C + Cap 2 feedback final ===")
    print(f"OK: {ok}, fail: {fail}")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:30s} {detail[:70]}")
    print(f"\nOutput: {V38}")
    print(f"Size: {V38.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
