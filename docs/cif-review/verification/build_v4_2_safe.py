"""v4.2 SAFE: cambios atómicos verificados sobre v3.18 (preserva formato 100%).

Cambios aplicados (todos verificados que existen en v3.18):
1. V05 Cap 3 — cifra LRS judicialización corregida ($269M no se sostiene)
2. Antítesis "no es un fenómeno meramente administrativo, sino..." → reformulado
3. "Una opción priorizada para la discusión" → "El informe profundiza..."
4. "Beneficio Farmacéutico Ambulatorio Universal (BFAU)" → "BFU" (residuales)
5. Em-dashes globales limpiados
6. Mensajes clave numerados (1., 2., ...)
7. Bibliografía: 5 referencias agregadas

Salida:
- informe-final-v4.2.docx (con tracked changes)
- informe-final-v4.2-aceptada.docx (limpia)
"""

from __future__ import annotations

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
)

BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
SRC = BASE / "output/informe-final-v3.18.docx"
V42 = BASE / "output/informe-final-v4.2.docx"
V42A = BASE / "output/informe-final-v4.2-aceptada.docx"

DATE_V42 = "2026-05-07T19:30:00-04:00"

import build_v3_18
build_v3_18.DATE = DATE_V42


# ============================================================
# Cambios verificados sobre v3.18
# ============================================================
CHANGES = [
    # V05 — Cap 3 cifra LRS judicialización: corregir
    (
        "el presupuesto de la Ley Ricarte Soto en 2024 registró una ejecución por vía judicial del orden de los $175 mil millones CLP, con una proyección cercana a los $269 mil millones CLP al cierre del año (fuente: MINSAL, reportes de ejecución LRS)",
        "la judicialización vía recursos de protección representó cerca de MM$ 81.000 en 2024, equivalente a 5,3% del gasto público en medicamentos (Fonasa, cuenta pública 2024; CIF/UC, 2025). Esta cifra se suma al presupuesto regular de la Ley Ricarte Soto (MM$ 175.672 en 2025, Dipres), que en su diseño original buscaba reducir la presión judicial sobre tratamientos de alto costo",
        "V05 LRS judicialización corregida (cifra $269M no se sostiene)",
    ),

    # Antítesis cap1 — "no es un fenómeno meramente administrativo, sino"
    (
        "La judicialización, por tanto, no es un fenómeno meramente administrativo, sino un síntoma estructural de insuficiencia del beneficio explícito, que traslada a los tribunales decisiones que deberían resolverse por mecanismos formales de priorización",
        "La judicialización, en este contexto, opera como síntoma estructural de la insuficiencia del beneficio explícito y traslada a los tribunales decisiones que deberían resolverse por mecanismos formales de priorización",
        "Antítesis cap1: 'no es un fenómeno meramente administrativo, sino' → reformulación afirmativa",
    ),

    # "Una opción priorizada" en mensajes-clave (también está en cap8)
    (
        "Una opción priorizada para la discusión es un escenario intermedio de convergencia OCDE. Su eje estructural sería un Beneficio Farmacéutico Ambulatorio Universal",
        "El informe profundiza en uno de los tres escenarios analizados, el de convergencia intermedia con el cluster OCDE. Su eje estructural sería un Beneficio Farmacéutico Universal",
        "Mensajes Clave: sacar prescriptividad de 'opción priorizada'",
    ),

    # Beneficio Farmacéutico Ambulatorio Universal residual (en mensajes-clave que no fue limpiado)
    (
        "Beneficio Farmacéutico Ambulatorio Universal, aplicable a beneficiarios",
        "Beneficio Farmacéutico Universal (BFU), aplicable a beneficiarios",
        "BFAU residual en mensajes clave",
    ),

    # Cap 8: "una opción priorizada para la discusión y no como una prescripción"
    (
        "el Beneficio Farmacéutico Universal se incluye dentro del tercer horizonte como una opción priorizada para la discusión y no como una prescripción: los escenarios 1 y 3 del Capítulo 6 representan alternativas igualmente válidas para la ponderación en el seminario.",
        "el Beneficio Farmacéutico Universal se desarrolla en el tercer horizonte como ejercicio analítico del Escenario 2; los escenarios 1 y 3 del Capítulo 6 ofrecen alternativas igualmente válidas para la ponderación en el seminario.",
        "Cap 8: sacar 'opción priorizada' y antítesis",
    ),

    # Patrón "no como recomendación priorizada" / "no como mecanismo ordinario"
    (
        "La judicialización de la cobertura, cuando ocurre, conviene interpretarla como síntoma de vacíos del beneficio explícito, no como mecanismo ordinario de acceso.",
        "La judicialización de la cobertura, cuando ocurre, conviene interpretarla como síntoma de vacíos del beneficio explícito; su crecimiento sostenido sugiere un problema estructural de diseño antes que un canal regular de acceso.",
        "RE/Mensajes: 'no como mecanismo ordinario de acceso'",
    ),
]


def number_mensajes_clave(body):
    """Buscar la sección 'Mensajes clave' y numerar los párrafos siguientes."""
    paragraphs = list(body.iter(qn("p")))
    in_mk = False
    counter = 0
    numbered = 0

    for p in paragraphs:
        pStyle = p.find(f".//{qn('pPr')}/{qn('pStyle')}")
        style = pStyle.get(qn("val"), "") if pStyle is not None else ""

        texts = []
        for t in p.iter(qn("t")):
            if t.text:
                texts.append(t.text)
        full = "".join(texts).strip()

        if style == "Heading1":
            if "Mensajes clave" in full and "Tarjeta" not in full and "Tabla" not in full and "Índice" not in full:
                in_mk = True
                counter = 0
                continue
            else:
                if in_mk:
                    in_mk = False

        if in_mk and full and len(full) > 30:
            counter += 1
            for t in p.iter(qn("t")):
                if t.text:
                    if not t.text.lstrip()[:3].rstrip(".").isdigit():
                        t.text = f"{counter}. " + t.text.lstrip()
                        numbered += 1
                    break
    return numbered


def append_bibliography(body):
    """Append 5 referencias al bloque de Bibliografía."""
    new_refs = [
        "Aguilera, R., y Castillo, C. (2022). Ruta del medicamento en Chile: análisis institucional. Universidad del Desarrollo, Centro de Políticas Públicas UDD.",
        "Bitrán, R. (2018). El financiamiento de la salud y los medicamentos en América Latina y el Caribe. Banco Interamericano de Desarrollo.",
        "Vargas-Pelaez, C. M., et al. (2019). Judicialization of access to medicines in four Latin American countries: a comparative qualitative analysis. International Journal for Equity in Health, 18(1), 1-13.",
        "Kirchlechner, T., y Cohen, J. (2025). Biosimilars and interchangeability: regulatory frameworks and policy implications. Therapeutic Innovation and Regulatory Science.",
        "CIF y Escuela de Gobierno UC (2025). Caracterización del gasto público en medicamentos en Chile. Segunda edición. Cámara de Innovación Farmacéutica de Chile y Pontificia Universidad Católica de Chile.",
    ]

    paragraphs = list(body.iter(qn("p")))
    biblio_idx = None
    end_idx = None
    for i, p in enumerate(paragraphs):
        pStyle = p.find(f".//{qn('pPr')}/{qn('pStyle')}")
        style = pStyle.get(qn("val"), "") if pStyle is not None else ""
        if style == "Heading1":
            texts = []
            for t in p.iter(qn("t")):
                if t.text:
                    texts.append(t.text)
            text = "".join(texts).strip()
            if biblio_idx is None and "bibliograf" in text.lower():
                biblio_idx = i
                continue
            if biblio_idx is not None and end_idx is None:
                end_idx = i
                break

    if biblio_idx is None:
        return 0

    if end_idx is None:
        anchor = paragraphs[-1]
    else:
        anchor = paragraphs[end_idx]

    inserted = 0
    for ref in new_refs:
        new_p = etree.Element(qn("p"))
        pPr = etree.SubElement(new_p, qn("pPr"))
        rPr_pPr = etree.SubElement(pPr, qn("rPr"))
        ins_pPr = etree.SubElement(rPr_pPr, qn("ins"))
        ins_pPr.set(qn("id"), next_rev())
        ins_pPr.set(qn("author"), AUTHOR)
        ins_pPr.set(qn("date"), DATE_V42)

        ins = etree.SubElement(new_p, qn("ins"))
        ins.set(qn("id"), next_rev())
        ins.set(qn("author"), AUTHOR)
        ins.set(qn("date"), DATE_V42)
        r = etree.SubElement(ins, qn("r"))
        rPr = etree.SubElement(r, qn("rPr"))
        rtl = etree.SubElement(rPr, qn("rtl"))
        rtl.set(qn("val"), "0")
        t = etree.SubElement(r, qn("t"))
        t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = ref

        anchor.addprevious(new_p)
        inserted += 1
    return inserted


def clean_em_dashes(body):
    """Reemplazar em-dashes residuales."""
    count = 0
    for t in list(body.iter(qn("t"))):
        if t.text and "—" in t.text:
            new_text = t.text.replace(" —", ",").replace("—", ",")
            if new_text != t.text:
                t.text = new_text
                count += 1
    return count


def main():
    print(f"=== build_v4_2_safe.py ===")
    print(f"SRC: {SRC.name}\n")

    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

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

        # Cambios puntuales
        for old, new, label in CHANGES:
            n = find_and_replace_text(body, old, new)
            if n:
                applied.append(f"  ✓ {label} ({n})")
            else:
                skipped.append(f"  ✗ {label} (no match)")

        # Numerar mensajes clave
        mk = number_mensajes_clave(body)
        if mk:
            applied.append(f"  ✓ Mensajes clave numerados: {mk}")

        # Em-dashes
        em = clean_em_dashes(body)
        if em:
            applied.append(f"  ✓ Em-dashes limpiados: {em} runs")

        # Bibliografía
        bib = append_bibliography(body)
        if bib:
            applied.append(f"  ✓ Bibliografía: {bib} referencias agregadas")

        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        if V42.exists():
            V42.unlink()
        V42.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(V42, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))
        size = V42.stat().st_size
        print(f"✓ {V42.name} ({size:,} bytes)\n")

        print("Applied:")
        for line in applied:
            print(line)
        if skipped:
            print("\nSkipped:")
            for line in skipped:
                print(line)
        print(f"\nTotal: {len(applied)} applied, {len(skipped)} skipped")

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


if __name__ == "__main__":
    main()
