"""v4.2: aplica cambios atómicos JSON sobre v3.18 (preserva formato).

Lee /tmp/v40-context/output/_changes/*.json (uno por sección) y aplica:
- replace_text: find_and_replace_text en runs
- replace_paragraph: replace_paragraph_text_tracked
- insert_after: insertar nuevo párrafo tracked-insert después de anchor
- delete_paragraph: marcar párrafo entero como tracked-delete
- replace_heading: cambiar texto de heading manteniendo el estilo

Más:
- Limpieza global de em-dashes
- Numerar mensajes clave (si no se hizo via JSON)
- Append bibliografía

Salida:
- informe-final-v4.2.docx (con tracked changes)
- informe-final-v4.2-aceptada.docx
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).parent))
from build_v3_18 import (
    AUTHOR,
    W_NS,
    XML_NS,
    qn,
    next_rev,
    find_and_replace_text,
    replace_paragraph_text_tracked,
    get_para_text,
    normalize,
)

BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
SRC = BASE / "output/informe-final-v3.18.docx"
V42 = BASE / "output/informe-final-v4.2.docx"
V42A = BASE / "output/informe-final-v4.2-aceptada.docx"

DATE_V42 = "2026-05-07T19:00:00-04:00"

import build_v3_18
build_v3_18.DATE = DATE_V42

CHANGES_DIR = Path("/tmp/v40-context/output/_changes")


# ============================================================
# Helpers
# ============================================================

def make_inserted_paragraph(text: str, style: str | None = None) -> etree.Element:
    """Crea párrafo nuevo con tracked insert + estructura compatible con v3.18."""
    p = etree.Element(qn("p"))
    pPr = etree.SubElement(p, qn("pPr"))
    if style:
        pStyle = etree.SubElement(pPr, qn("pStyle"))
        pStyle.set(qn("val"), style)
    rPr_pPr = etree.SubElement(pPr, qn("rPr"))
    ins_pPr = etree.SubElement(rPr_pPr, qn("ins"))
    ins_pPr.set(qn("id"), next_rev())
    ins_pPr.set(qn("author"), AUTHOR)
    ins_pPr.set(qn("date"), DATE_V42)

    if text:
        ins = etree.SubElement(p, qn("ins"))
        ins.set(qn("id"), next_rev())
        ins.set(qn("author"), AUTHOR)
        ins.set(qn("date"), DATE_V42)
        r = etree.SubElement(ins, qn("r"))
        rPr = etree.SubElement(r, qn("rPr"))
        rtl = etree.SubElement(rPr, qn("rtl"))
        rtl.set(qn("val"), "0")
        t = etree.SubElement(r, qn("t"))
        t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = text
    return p


import unicodedata


def normalize_fuzzy(text: str) -> str:
    """Normalización agresiva: lowercase, sin acentos, comillas curvas a rectas."""
    if not text:
        return ""
    # Normalize Unicode (NFKD descompone acentos)
    text = unicodedata.normalize("NFKD", text)
    # Strip combining marks (acentos)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Smart quotes -> straight
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("«", '"').replace("»", '"')
    # En/em dashes -> hyphen for matching
    text = text.replace("–", "-").replace("—", "-")
    # Lowercase
    text = text.lower()
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_md_prefix(text: str) -> str:
    """Quita marcadores markdown [p], [Heading*] del inicio."""
    text = re.sub(r"^\s*\[p\]\s*", "", text)
    text = re.sub(r"^\s*\[Heading\d\]\s*", "", text)
    return text.strip()


def find_paragraph_starting_with(body, prefix: str) -> etree.Element | None:
    """Encuentra primer <w:p> cuyo texto (sin tracked changes) coincide con `prefix`.
    Estrategia en cascada:
    1. startswith exacto en prefijo normalizado (60 chars)
    2. startswith fuzzy (sin acentos, sin smart quotes)
    3. substring fuzzy (40+ chars)
    """
    prefix_clean = clean_md_prefix(prefix)
    prefix_norm = normalize(prefix_clean)[:60]
    prefix_fuzzy = normalize_fuzzy(prefix_clean)[:60]

    if not prefix_norm:
        return None

    # Pass 1: exact prefix match
    for p in body.iter(qn("p")):
        text = normalize(get_para_text(p))
        if text.startswith(prefix_norm):
            return p

    # Pass 2: fuzzy prefix (no accents, normalized quotes)
    for p in body.iter(qn("p")):
        text_fuzzy = normalize_fuzzy(get_para_text(p))
        if text_fuzzy.startswith(prefix_fuzzy[:40]):
            return p

    # Pass 3: fuzzy substring (40 chars, somewhere in paragraph)
    if len(prefix_fuzzy) >= 30:
        substring = prefix_fuzzy[:30]
        for p in body.iter(qn("p")):
            text_fuzzy = normalize_fuzzy(get_para_text(p))
            if substring in text_fuzzy:
                return p

    return None


def mark_paragraph_deleted(p):
    """Marca todos los runs del <w:p> como tracked deletions."""
    runs_to_delete = []
    for child in list(p):
        if child.tag == qn("r"):
            runs_to_delete.append(child)
    if not runs_to_delete:
        return False
    for r in runs_to_delete:
        parent = r.getparent()
        idx = list(parent).index(r)
        parent.remove(r)
        del_elem = etree.Element(qn("del"))
        del_elem.set(qn("id"), next_rev())
        del_elem.set(qn("author"), AUTHOR)
        del_elem.set(qn("date"), DATE_V42)
        for t in r.findall(qn("t")):
            t.tag = qn("delText")
        del_elem.append(r)
        parent.insert(idx, del_elem)
    return True


def insert_after_paragraph(body, anchor_p, new_text: str, style: str | None = None):
    """Inserta nuevo párrafo después de anchor_p."""
    new_p = make_inserted_paragraph(new_text, style=style)
    anchor_p.addnext(new_p)
    return True


def get_para_style(p):
    pStyle = p.find(f".//{qn('pPr')}/{qn('pStyle')}")
    if pStyle is None:
        return None
    return pStyle.get(qn("val"), "")


# ============================================================
# Apply a change object
# ============================================================
def apply_change(body, change: dict) -> tuple[bool, str]:
    """Apply a single change object. Returns (success, message)."""
    cid = change.get("id", "?")
    ctype = change.get("type", "")
    reason = change.get("reason", "")[:60]

    try:
        if ctype == "replace_text":
            find = change.get("find", "")
            replace = change.get("replace", "")
            if not find:
                return False, f"{cid}: missing 'find'"
            n = find_and_replace_text(body, find, replace)
            if n > 0:
                return True, f"{cid} replace_text ({n}): {reason}"
            return False, f"{cid} replace_text NO MATCH: {find[:40]}..."

        elif ctype == "replace_paragraph":
            prefix = change.get("find_paragraph_starts_with", "")
            new_text = change.get("replace_with", "")
            if not prefix or not new_text:
                return False, f"{cid}: missing fields"
            p = find_paragraph_starting_with(body, prefix)
            if p is None:
                return False, f"{cid} replace_paragraph NO MATCH: {clean_md_prefix(prefix)[:40]}..."
            # Replace contents tracked
            style = get_para_style(p)
            new_text_clean = clean_md_prefix(new_text)
            # Strip inline markdown
            new_text_clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", new_text_clean)
            new_text_clean = re.sub(r"`([^`]+)`", r"\1", new_text_clean)
            mark_paragraph_deleted(p)
            insert_after_paragraph(body, p, new_text_clean, style=style)
            return True, f"{cid} replace_paragraph: {reason}"

        elif ctype == "insert_after":
            anchor_prefix = change.get("anchor_starts_with", "")
            new_text = change.get("new_text", "")
            if not anchor_prefix or not new_text:
                return False, f"{cid}: missing fields"
            anchor = find_paragraph_starting_with(body, anchor_prefix)
            if anchor is None:
                return False, f"{cid} insert_after NO ANCHOR: {clean_md_prefix(anchor_prefix)[:40]}..."
            new_text_clean = clean_md_prefix(new_text)
            new_text_clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", new_text_clean)
            new_text_clean = re.sub(r"`([^`]+)`", r"\1", new_text_clean)
            insert_after_paragraph(body, anchor, new_text_clean)
            return True, f"{cid} insert_after: {reason}"

        elif ctype == "delete_paragraph":
            prefix = change.get("find_paragraph_starts_with", "")
            if not prefix:
                return False, f"{cid}: missing prefix"
            p = find_paragraph_starting_with(body, prefix)
            if p is None:
                return False, f"{cid} delete_paragraph NO MATCH: {prefix[:40]}..."
            mark_paragraph_deleted(p)
            return True, f"{cid} delete_paragraph: {reason}"

        elif ctype == "replace_heading":
            prefix = change.get("find_paragraph_starts_with", "")
            new_text = change.get("replace_with", "")
            p = find_paragraph_starting_with(body, prefix)
            if p is None:
                return False, f"{cid} replace_heading NO MATCH: {prefix[:40]}..."
            style = get_para_style(p)
            # Solo reemplazar si es heading
            if not style or not style.startswith("Heading"):
                return False, f"{cid} replace_heading: target is not a heading"
            mark_paragraph_deleted(p)
            insert_after_paragraph(body, p, new_text, style=style)
            return True, f"{cid} replace_heading: {reason}"

        else:
            return False, f"{cid} unknown type: {ctype}"

    except Exception as e:
        return False, f"{cid} ERROR: {e}"


def main():
    print(f"=== build_v4_2.py — cambios atómicos sobre v3.18 ===")
    print(f"SRC: {SRC.name}\n")

    # Cargar todos los JSONs disponibles
    if not CHANGES_DIR.exists():
        raise SystemExit(f"⚠ No existe {CHANGES_DIR}")

    json_files = sorted(CHANGES_DIR.glob("*.json"))
    print(f"JSONs encontrados: {len(json_files)}")
    for jf in json_files:
        print(f"  - {jf.name}")
    print()

    if not json_files:
        raise SystemExit("Sin JSONs. Esperá a los agentes.")

    all_changes = []
    for jf in json_files:
        try:
            data = json.loads(jf.read_text())
            section = data.get("section", jf.stem)
            changes = data.get("changes", [])
            for c in changes:
                c["_source"] = section
            all_changes.extend(changes)
            print(f"  {jf.name}: {len(changes)} cambios")
        except Exception as e:
            print(f"  {jf.name} ERROR parse: {e}")

    print(f"\nTotal cambios a aplicar: {len(all_changes)}\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shutil.copy2(SRC, tmp / "src.docx")
        with zipfile.ZipFile(tmp / "src.docx") as z:
            z.extractall(tmp / "src")

        doc_xml = tmp / "src/word/document.xml"
        tree = etree.parse(str(doc_xml))
        root = tree.getroot()
        body = root.find(qn("body"))

        applied = []
        skipped = []

        for change in all_changes:
            ok, msg = apply_change(body, change)
            if ok:
                applied.append(msg)
            else:
                skipped.append(msg)

        # Pasada limpieza em-dashes
        em = 0
        for t in list(body.iter(qn("t"))):
            if t.text and "—" in t.text:
                t.text = t.text.replace(" —", ",").replace("—", ",")
                em += 1
        if em:
            applied.append(f"em-dashes limpiados en {em} runs")

        # Save
        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        if V42.exists():
            V42.unlink()
        V42.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(V42, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))
        print(f"✓ {V42.name} ({V42.stat().st_size:,} bytes)\n")

        print(f"Applied: {len(applied)}")
        for line in applied[:30]:
            print(f"  ✓ {line}")
        if len(applied) > 30:
            print(f"  ... +{len(applied)-30} más")
        print(f"\nSkipped: {len(skipped)}")
        for line in skipped[:20]:
            print(f"  ✗ {line}")
        if len(skipped) > 20:
            print(f"  ... +{len(skipped)-20} más")

        # Aceptada
        with tempfile.TemporaryDirectory() as tmpdir2:
            tmp2 = Path(tmpdir2)
            shutil.copy2(V42, tmp2 / "src.docx")
            with zipfile.ZipFile(tmp2 / "src.docx") as z:
                z.extractall(tmp2 / "src")

            doc_xml_a = tmp2 / "src/word/document.xml"
            tree_a = etree.parse(str(doc_xml_a))
            root_a = tree_a.getroot()

            for ins in list(root_a.iter(qn("ins"))):
                parent = ins.getparent()
                idx = list(parent).index(ins)
                for child in list(ins):
                    ins.remove(child)
                    parent.insert(idx, child)
                    idx += 1
                parent.remove(ins)

            for d in list(root_a.iter(qn("del"))):
                d.getparent().remove(d)

            tree_a.write(str(doc_xml_a), xml_declaration=True, encoding="UTF-8", standalone=True)
            if V42A.exists():
                V42A.unlink()
            with zipfile.ZipFile(V42A, "w", zipfile.ZIP_DEFLATED) as z:
                for path in (tmp2 / "src").rglob("*"):
                    if path.is_file():
                        z.write(path, path.relative_to(tmp2 / "src"))
            print(f"\n✓ {V42A.name} ({V42A.stat().st_size:,} bytes)")

        # Save log
        log_path = Path("/tmp/v40-context/output/_changes/_apply_log.txt")
        log_path.write_text(
            f"v4.2 applied: {len(applied)}, skipped: {len(skipped)}\n\n"
            "APPLIED:\n" + "\n".join(applied) + "\n\nSKIPPED:\n" + "\n".join(skipped)
        )
        print(f"\nLog: {log_path}")


if __name__ == "__main__":
    main()
