"""Build v3 final: aplica los edits de los 3 agentes editoriales como tracked changes.

Toma como input:
- informe-final-v3-base.docx (resultado de build_v3_base.py)
- edits_agente1.json (Resumen Ejec + Mensajes Clave + Intro Cap 1)
- edits_agente2.json (Caps 2-5 diagnóstico + comparación internacional)
- edits_agente3.json (Caps 6-8 alternativas + conclusiones)

Produce: informe-final-v3.docx con todas las sugerencias aplicadas.

Cada edit del JSON es un objeto con:
- type: "replace_paragraph" | "insert_paragraph"
- locator (para replace) o anchor (para insert): {mode, value} con mode=prefix|contains
- new (replace) o text (insert)
- position (insert): "before"|"after"
- style (insert): null|"Heading2"
- rationale: string (info, no se usa)
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

V3_BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3-base.docx")
V3 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.docx")

JSON_PATHS = [
    Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/edits_agente1.json"),
    Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/edits_agente2.json"),
    Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/edits_agente3.json"),
]

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_id = 300000


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

    ins = make_ins_run(new_text)
    p.append(ins)


def make_new_paragraph_tracked(text, style_from=None, is_heading=False):
    p = etree.Element(qn("p"))
    pPr = etree.SubElement(p, qn("pPr"))

    if is_heading:
        pStyle = etree.SubElement(pPr, qn("pStyle"))
        pStyle.set(qn("val"), "Heading2")
    elif style_from is not None:
        src_pPr = style_from.find(qn("pPr"))
        if src_pPr is not None:
            src_pStyle = src_pPr.find(qn("pStyle"))
            if src_pStyle is not None:
                pStyle = etree.SubElement(pPr, qn("pStyle"))
                pStyle.set(qn("val"), src_pStyle.get(qn("val"), ""))

    # Mark as inserted via rPr.ins
    rPr = etree.SubElement(pPr, qn("rPr"))
    ins_mark = etree.SubElement(rPr, qn("ins"))
    ins_mark.set(qn("id"), next_id())
    ins_mark.set(qn("author"), AUTHOR)
    ins_mark.set(qn("date"), DATE)

    ins = make_ins_run(text)
    p.append(ins)

    return p


def apply_edits(body, edits, agent_name):
    log = []
    for idx, edit in enumerate(edits, 1):
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
                log.append(("NOT FOUND", f"{agent_name} #{idx}", f"replace loc: {value[:50]}"))
                continue
            new_text = edit["new"]
            replace_paragraph_content_tracked(p, new_text)
            log.append(("OK", f"{agent_name} #{idx}", f"replace para {i}"))

        elif etype == "insert_paragraph":
            anchor = edit["anchor"]
            mode = anchor.get("mode", "contains")
            value = anchor["value"]
            position = edit.get("position", "after")
            style = edit.get("style")
            text = edit.get("text") or edit.get("new", "")

            if mode == "prefix":
                i, anchor_p = find_paragraph_by_prefix(body, value)
            else:
                i, anchor_p = find_paragraph_contains(body, value)

            if anchor_p is None:
                log.append(("NOT FOUND", f"{agent_name} #{idx}", f"insert anchor: {value[:50]}"))
                continue

            is_heading = style == "Heading2"
            new_p = make_new_paragraph_tracked(text, style_from=anchor_p, is_heading=is_heading)

            if position == "before":
                anchor_p.addprevious(new_p)
            else:  # after
                anchor_p.addnext(new_p)

            log.append(("OK", f"{agent_name} #{idx}", f"insert {position} para {i}"))

        else:
            log.append(("SKIP", f"{agent_name} #{idx}", f"unknown type: {etype}"))

    return log


def process_docx():
    if V3.exists():
        V3.unlink()
    shutil.copy(V3_BASE, V3)
    print(f"Copied: {V3_BASE.name} -> {V3.name}")

    with zipfile.ZipFile(V3, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))

    all_log = []

    for json_path in JSON_PATHS:
        if not json_path.exists():
            print(f"WARNING: {json_path.name} not found, skipping")
            all_log.append(("MISSING", json_path.name, ""))
            continue

        with open(json_path) as f:
            data = json.load(f)

        agent_name = data.get("agent", json_path.stem)
        edits = data.get("edits", [])
        print(f"\n=== {agent_name} ({len(edits)} edits) ===")

        log = apply_edits(body, edits, agent_name)
        all_log.extend(log)

        for status, name, detail in log:
            marker = "✓" if status == "OK" else "✗"
            print(f"  {marker} {name}  {detail}")

    # Serialize
    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V3, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V3)

    return all_log


def main():
    log = process_docx()
    ok = sum(1 for s, _, _ in log if s == "OK")
    fail = sum(1 for s, _, _ in log if s not in ("OK",))
    print(f"\n=== TOTAL v3 ===")
    print(f"{ok} OK, {fail} fail/missing")
    print(f"Output: {V3}")
    print(f"Size: {V3.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
