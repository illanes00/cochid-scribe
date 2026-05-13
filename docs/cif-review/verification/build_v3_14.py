"""v3.14: Consolidador de los 4 agentes paralelos (fichas, lectura, estilo, factual).

Lee los 4 JSONs producidos por los agentes en v3_14_agents/ y aplica todos los
edits como tracked changes sobre v3.14a.docx -> v3.14.docx.

Tipos de edits soportados:
- replace_paragraph: reemplaza todo el contenido del párrafo (wrap en <w:del> + <w:ins>)
- replace_text_in_paragraph: reemplaza un substring dentro del párrafo
- insert_paragraph_after / insert_paragraph_before: inserta párrafo nuevo como <w:ins>
- add_comment: ancla comentario al párrafo con [MI-NN] o equivalente
- add_bibliography_entry: agrega entrada al final de la sección Referencias

Entrada:
- v3.14a.docx (ya tiene Figura 2 con nota eje Y + 537 fechas normalizadas)
- v3_14_agents/agent_fichas.json
- v3_14_agents/agent_lectura.json
- v3_14_agents/agent_estilo.json
- v3_14_agents/agent_factual.json

Salida:
- v3.14.docx (tracked changes consolidados)
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
V314A = BASE / "output/informe-final-v3.14a.docx"
V314 = BASE / "output/informe-final-v3.14.docx"
AGENTS_DIR = BASE / "verification/v3_14_agents"

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_next_rev = 2000000
_next_comment_id = 3000


def next_rev():
    global _next_rev
    _next_rev += 1
    return str(_next_rev)


def next_comment_id():
    global _next_comment_id
    _next_comment_id += 1
    return str(_next_comment_id)


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


def normalize(s):
    return re.sub(r"\s+", " ", s or "").strip()


def find_paragraph(body, locator):
    """locator: {'strategy': 'contains'|'prefix'|'equals', 'text': '...'}"""
    if not isinstance(locator, dict):
        return None, None
    strategy = locator.get("strategy", "contains")
    needle = normalize(locator.get("text", ""))
    if not needle:
        return None, None
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs):
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


def replace_text_in_paragraph_tracked(p, old_text, new_text):
    """Find old_text within p's text runs and replace as <w:del> + <w:ins>.

    Strategy: find the run containing old_text (single-run case); split or replace.
    If old_text spans multiple runs, fallback to full paragraph replacement.
    """
    # Try single-run substitution first
    for r in p.findall(qn("r")):
        t = r.find(qn("t"))
        if t is not None and t.text and old_text in t.text:
            before, _, after = t.text.partition(old_text)
            parent = r.getparent()
            idx = list(parent).index(r)

            # Keep existing run but trim to 'before'
            t.text = before
            t.set(f"{{{XML_NS}}}space", "preserve")

            # Build delete wrapper with old_text (as <w:delText>)
            r_del = deepcopy(r)
            t_del = r_del.find(qn("t"))
            t_del.tag = qn("delText")
            t_del.text = old_text
            t_del.set(f"{{{XML_NS}}}space", "preserve")
            del_elem = etree.Element(qn("del"))
            del_elem.set(qn("id"), next_rev())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(r_del)

            # Build insert wrapper with new_text
            r_ins = deepcopy(r)
            t_ins = r_ins.find(qn("t"))
            t_ins.text = new_text
            t_ins.set(f"{{{XML_NS}}}space", "preserve")
            ins_elem = etree.Element(qn("ins"))
            ins_elem.set(qn("id"), next_rev())
            ins_elem.set(qn("author"), AUTHOR)
            ins_elem.set(qn("date"), DATE)
            ins_elem.append(r_ins)

            # Build trailing run with 'after'
            r_after = deepcopy(r)
            t_after = r_after.find(qn("t"))
            t_after.text = after
            t_after.set(f"{{{XML_NS}}}space", "preserve")

            parent.insert(idx + 1, r_after)
            parent.insert(idx + 1, ins_elem)
            parent.insert(idx + 1, del_elem)
            return True
    return False


def make_inserted_paragraph(text, reference_p):
    new_p = etree.Element(qn("p"))
    ref_pPr = reference_p.find(qn("pPr"))
    if ref_pPr is not None:
        pPr_copy = deepcopy(ref_pPr)
        # strip heading style so new paragraph is body text
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


def insert_paragraph_before(body, anchor_p, text):
    new_p = make_inserted_paragraph(text, anchor_p)
    parent = anchor_p.getparent()
    idx = list(parent).index(anchor_p)
    parent.insert(idx, new_p)
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


def load_agent_jsons():
    agents = {}
    for name in ("fichas", "lectura", "estilo", "factual"):
        path = AGENTS_DIR / f"agent_{name}.json"
        if path.exists():
            try:
                agents[name] = json.loads(path.read_text())
            except json.JSONDecodeError as e:
                print(f"  ✗ {name}: JSON inválido — {e}")
                agents[name] = {"edits": [], "comments_to_add": []}
        else:
            print(f"  · {name}: no existe aún")
            agents[name] = {"edits": [], "comments_to_add": []}
    return agents


def apply_edit(body, edit):
    """Apply one edit. Returns (status, detail)."""
    etype = edit.get("type")
    locator = edit.get("locator") or edit.get("anchor") or {}

    i, p = find_paragraph(body, locator)
    if p is None:
        return "NOT FOUND", f"{etype} {str(locator)[:60]}"

    if etype == "replace_paragraph":
        new = edit.get("new", "")
        replace_paragraph_tracked(p, new)
        return "OK", f"{etype} para {i}"
    if etype == "replace_text_in_paragraph":
        old = edit.get("old", "")
        new = edit.get("new", "")
        if not old:
            return "SKIP", "empty old"
        ok = replace_text_in_paragraph_tracked(p, old, new)
        if not ok:
            # Fallback: replace full paragraph using get_para_text
            current = get_para_text(p)
            if old in current:
                replace_paragraph_tracked(p, current.replace(old, new))
                return "OK", f"{etype} (fallback full-para) para {i}"
            return "NOT FOUND", f"{etype} old no encontrado en para {i}"
        return "OK", f"{etype} para {i}"
    if etype == "insert_paragraph_after":
        new = edit.get("new", "")
        insert_paragraph_after(body, p, new)
        return "OK", f"{etype} after para {i}"
    if etype == "insert_paragraph_before":
        new = edit.get("new", "")
        insert_paragraph_before(body, p, new)
        return "OK", f"{etype} before para {i}"
    return "SKIP", f"unknown type {etype}"


def apply_comment(body, com_tree, spec):
    anchor = spec.get("anchor") or spec.get("locator") or {}
    i, p = find_paragraph(body, anchor)
    if p is None:
        return "NOT FOUND", spec.get("id", "?")
    cid = next_comment_id()
    body_text = spec.get("body") or spec.get("text") or ""
    com_tree.append(make_comment_elem(cid, body_text))
    anchor_comment_to_paragraph(p, cid)
    return "OK", f"{spec.get('id', '?')} cid={cid} para {i}"


def process():
    if V314.exists():
        V314.unlink()
    shutil.copy(V314A, V314)
    print(f"Copied: {V314A.name} -> {V314.name}")

    with zipfile.ZipFile(V314, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))
    com_tree = etree.fromstring(com_xml)

    # Bump comment id past existing
    existing_ids = [int(c.get(qn("id"), "0")) for c in com_tree.findall(qn("comment"))]
    if existing_ids:
        global _next_comment_id
        _next_comment_id = max(max(existing_ids) + 100, _next_comment_id)

    agents = load_agent_jsons()
    log_by_agent = {}

    # Apply edits per agent. Order: factual, fichas, estilo, lectura
    # (factual first because data corrections are atomic; lectura last because
    # it may move/restructure paragraphs)
    order = ("factual", "fichas", "estilo", "lectura")
    for name in order:
        data = agents.get(name, {})
        edits = data.get("edits", []) or []
        comments = data.get("comments_to_add", []) or []
        ok = 0
        nf = 0
        skip = 0
        for edit in edits:
            status, detail = apply_edit(body, edit)
            if status == "OK":
                ok += 1
            elif status == "NOT FOUND":
                nf += 1
            else:
                skip += 1
        for spec in comments:
            status, detail = apply_comment(body, com_tree, spec)
            if status == "OK":
                ok += 1
            else:
                nf += 1
        # bibliography additions handled separately (fin del documento)
        biblio_adds = data.get("bibliography_additions", []) or []
        for entry in biblio_adds:
            anchor = entry.get("anchor") or {"strategy": "contains", "text": "Referencias"}
            i, p = find_paragraph(body, anchor)
            if p is None:
                nf += 1
                continue
            insert_paragraph_after(body, p, entry.get("entry", ""))
            ok += 1
        log_by_agent[name] = (ok, nf, skip, len(edits) + len(comments) + len(biblio_adds))

    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name
    with zipfile.ZipFile(V314, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))
    shutil.move(tmp_path, V314)

    return log_by_agent


def main():
    stats = process()
    print("\n=== v3.14: Consolidación 4 agentes ===")
    total_ok = 0
    total_nf = 0
    total_skip = 0
    total = 0
    for name, (ok, nf, skip, n) in stats.items():
        print(f"  {name:10s}  {ok:4d} OK  {nf:3d} not-found  {skip:3d} skip  (/{n})")
        total_ok += ok
        total_nf += nf
        total_skip += skip
        total += n
    print(f"  {'TOTAL':10s}  {total_ok:4d} OK  {total_nf:3d} not-found  {total_skip:3d} skip  (/{total})")
    print(f"\nOutput: {V314}")
    print(f"Size: {V314.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
