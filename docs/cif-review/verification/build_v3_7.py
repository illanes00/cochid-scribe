"""Build v3.7: consolidar outputs de Agente A (DEFER Carla) + Agente B (barrido terminológico).

Aplica todos los edits + reply_updates como tracked changes sobre v3.6.

Input:  informe-final-v3.6.docx
Output: informe-final-v3.7.docx
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

V36 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.6.docx")
V37 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.7.docx")

JSON_A = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/edits_agenteA.json")
JSON_B = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/edits_agenteB.json")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_id = 800000


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


def apply_edit(body, edit, agent):
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
            return "NOT FOUND", ""
        replace_paragraph_content_tracked(p, edit["new"])
        return "OK", f"para {i}"
    elif etype == "insert_paragraph":
        # Some agents use "locator" instead of "anchor"
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
            return "NOT FOUND", ""
        is_heading = style == "Heading2"
        new_p = make_inserted_paragraph_like(text, anchor_p, is_heading=is_heading)
        if position == "before":
            anchor_p.addprevious(new_p)
        else:
            anchor_p.addnext(new_p)
        return "OK", f"insert {position} para {i}"
    return "UNKNOWN", etype


def process_docx():
    if V37.exists():
        V37.unlink()
    shutil.copy(V36, V37)
    print(f"Copied: {V36.name} -> {V37.name}")

    log = []

    with zipfile.ZipFile(V37, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))
    com_tree = etree.fromstring(com_xml)

    # === Agente A: reply_updates + edits ===
    with open(JSON_A) as f:
        data_a = json.load(f)

    for ru in data_a.get("reply_updates", []):
        cid = ru["comment_id"]
        new_reply = ru["new_reply"]
        c = next((cc for cc in com_tree.findall(qn("comment")) if cc.get(qn("id")) == str(cid)), None)
        if c is None:
            log.append(("NOT FOUND", f"A reply id={cid}", ""))
            continue
        replace_comment_reply(c, new_reply)
        log.append(("OK", f"A reply id={cid}", ""))

    for i, edit in enumerate(data_a.get("edits", [])):
        status, detail = apply_edit(body, edit, "A")
        log.append((status, f"A edit #{i+1}", detail))

    # === Agente B: edits solamente ===
    with open(JSON_B) as f:
        data_b = json.load(f)

    for i, edit in enumerate(data_b.get("edits", [])):
        status, detail = apply_edit(body, edit, "B")
        log.append((status, f"B edit #{i+1}", detail))

    # === Write back ===
    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V37, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V37)

    return log


def main():
    log = process_docx()
    ok = sum(1 for s, _, _ in log if s == "OK")
    fail = sum(1 for s, _, _ in log if s != "OK")
    print(f"\n=== v3.7: Agente A + Agente B aplicados ===")
    print(f"OK: {ok}, fail: {fail}")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:20s} {detail[:70]}")
    print(f"\nOutput: {V37}")
    print(f"Size: {V37.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
