"""Build v3.2: correcciones Bloque 1 + Bloque 2 aplicadas como tracked changes.

Bloque 1 (mecánico, datos verificados contra OECD SHA 2022):
1. Ficha Chile Tabla 0: corregir 4 cifras + agregar nota fuente
   - Privado per cápita: $240 → $293 PPA
   - De bolsillo: $240 → $281 PPA (estaba igual a privado, error)
   - Total per cápita: $308 → $394 PPA
   - Gasto público en medicamentos: 0.2% PIB → 0.34% PIB (2022) [Carla 42]
2. Figura 1 leyenda: agregar fuente OECD SHA explícita
3. Numeración tablas/subtítulos: detectar inconsistencias (lectura, sin aplicar)

Bloque 2 (verificación):
1. U con tilde: revisar locator correcto
2. Headers 2.4 y 5.3.4: verificar que los párrafos vacíos dentro están limpios

Input:  informe-final-v3.1.docx
Output: informe-final-v3.2.docx
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V31 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.1.docx")
V32 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.2.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_id = 400000


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
    """Replace a paragraph's content as tracked changes: wrap existing in <w:del>, add <w:ins>."""
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


def make_inserted_paragraph_in_cell(text, reference_p):
    """Create a new <w:p> marked as inserted, copying pPr style from reference."""
    new_p = etree.Element(qn("p"))
    # Copy pPr from reference
    ref_pPr = reference_p.find(qn("pPr"))
    if ref_pPr is not None:
        pPr_copy = deepcopy(ref_pPr)
        new_p.append(pPr_copy)
        pPr = pPr_copy
    else:
        pPr = etree.SubElement(new_p, qn("pPr"))
    # Mark as inserted via rPr.ins
    rPr = pPr.find(qn("rPr"))
    if rPr is None:
        rPr = etree.SubElement(pPr, qn("rPr"))
    ins_mark = etree.SubElement(rPr, qn("ins"))
    ins_mark.set(qn("id"), next_id())
    ins_mark.set(qn("author"), AUTHOR)
    ins_mark.set(qn("date"), DATE)
    # Content
    ins = make_ins_run(text)
    new_p.append(ins)
    return new_p


# Corrections for Ficha Chile (Tabla 0, Cell [0][1])
FICHA_CORRECTIONS = [
    ("Privado per cápita (US$ 2022): $ 240",
     "Privado per cápita (US$ PPA 2022): US$ 293"),
    ("De bolsillo (US$ corrientes): $ 240",
     "Gasto de bolsillo per cápita (US$ PPA 2022): US$ 281"),
    ("Total per cápita: $ 308",
     "Total per cápita (US$ PPA 2022): US$ 394"),
    ("Gasto público en medicamentos: 0.2%",
     "Gasto público en medicamentos retail: 0,34% (HC51 HF1, 2022)"),
]

# Nota de fuente a agregar al final del cell [0][1] de Tabla 0
FICHA_FUENTE_NOTE = (
    "Fuente: OECD Health Statistics, dataflow OECD.ELS.HD,DSD_SHA@DF_SHA, función HC51 (retail pharma), año 2022."
)

# Figura 1 leyenda: reemplazar párrafo actual
FIGURA1_OLD_PREFIX = "Serie anual de dos indicadores: (i) gasto público en medicamentos como % del PIB"
FIGURA1_NEW = (
    "Serie anual del gasto público en medicamentos (HC51 HF1) como % del PIB y como % del gasto corriente "
    "del Ministerio de Salud. Los datos 2019-2023 se obtienen de OECD Health Statistics (dataflow "
    "OECD.ELS.HD,DSD_SHA@DF_SHA, función HC51 retail pharma); el dato 2024 corresponde a ejecución "
    "presupuestaria DIPRES (provisional). Notar el salto entre 2019 (0,22%) y 2020 (0,37%) asociado a la "
    "ampliación de programas post-pandemia. Fuente: elaboración propia a partir de OECD SHA 2024 y DIPRES."
)


def process_docx():
    if V32.exists():
        V32.unlink()
    shutil.copy(V31, V32)
    print(f"Copied: {V31.name} -> {V32.name}")

    log = []

    with zipfile.ZipFile(V32, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))

    # === BLOQUE 1.1 — Ficha Chile Tabla 0 ===
    tables = body.findall(qn("tbl"))
    if tables:
        t0 = tables[0]
        first_row = t0.find(qn("tr"))
        if first_row is not None:
            cells = first_row.findall(qn("tc"))
            if len(cells) >= 2:
                cell = cells[1]  # Cell [0][1] with vital stats
                paragraphs = cell.findall(qn("p"))

                for old, new in FICHA_CORRECTIONS:
                    found = False
                    for p in paragraphs:
                        text = get_para_text(p)
                        if old in text:
                            replace_paragraph_content_tracked(p, new)
                            log.append(("OK", f"Ficha: {old[:40]}...", f"-> {new[:40]}..."))
                            found = True
                            break
                    if not found:
                        log.append(("NOT FOUND", f"Ficha: {old[:60]}...", ""))

                # Add fuente note as new paragraph at end of cell
                if paragraphs:
                    last_p = paragraphs[-1]
                    fuente_p = make_inserted_paragraph_in_cell(FICHA_FUENTE_NOTE, last_p)
                    cell.append(fuente_p)
                    log.append(("OK", "Ficha: nota de fuente OECD SHA", "agregada al final del cell"))
        else:
            log.append(("NOT FOUND", "Ficha Chile: Tabla 0 sin filas", ""))
    else:
        log.append(("NOT FOUND", "Ficha Chile: no hay tablas", ""))

    # === BLOQUE 1.2 — Figura 1 leyenda ===
    for p in body.findall(qn("p")):
        text = get_para_text(p)
        if text.startswith(FIGURA1_OLD_PREFIX):
            replace_paragraph_content_tracked(p, FIGURA1_NEW)
            log.append(("OK", "Figura 1: leyenda con OECD SHA explícito", ""))
            break
    else:
        log.append(("NOT FOUND", "Figura 1 leyenda", ""))

    # === BLOQUE 1.3 — Verificar numeración tablas y subtítulos ===
    # Detectar: "Tabla N:" / "Figura N:" / "Tarjeta N:" y reportar inconsistencias
    table_numbers = []
    figure_numbers = []
    card_numbers = []

    for p in body.findall(qn("p")):
        text = get_para_text(p).strip()
        # Match headers
        m_t = re.match(r"Tabla (\d+)[:\. ]", text)
        m_f = re.match(r"Figura (\d+)[:\. ]", text)
        m_c = re.match(r"Tarjeta (\d+)[:\. ]", text)
        if m_t:
            table_numbers.append(int(m_t.group(1)))
        if m_f:
            figure_numbers.append(int(m_f.group(1)))
        if m_c:
            card_numbers.append(int(m_c.group(1)))

    def check_seq(nums, name):
        if not nums:
            return f"{name}: ninguno encontrado"
        nums_sorted = sorted(nums)
        issues = []
        expected = 1
        for n in nums_sorted:
            if n != expected:
                if n < expected:
                    issues.append(f"duplicado/repetido {n}")
                else:
                    issues.append(f"salto {expected}→{n}")
            expected = n + 1
        return f"{name}: {len(nums)} entries, rango {min(nums)}-{max(nums)}, secuencia {'OK' if not issues else 'issues: ' + '; '.join(issues[:5])}"

    log.append(("INFO", "Numeración Tablas", check_seq(table_numbers, "Tablas")))
    log.append(("INFO", "Numeración Figuras", check_seq(figure_numbers, "Figuras")))
    log.append(("INFO", "Numeración Tarjetas", check_seq(card_numbers, "Tarjetas")))

    # Write back
    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V32, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V32)

    return log


def main():
    log = process_docx()
    print("\n=== v3.2 Bloque 1 aplicado ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else ("ℹ" if status == "INFO" else "✗")
        print(f"  {marker} {name:55s}  {detail}")
    print(f"\nOutput: {V32}")
    print(f"Size: {V32.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
