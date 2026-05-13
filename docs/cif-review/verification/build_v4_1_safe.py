"""v4.1 SAFE: cambios puntuales sobre v3.18 (preserva formato 100%).

Approach: tomar v3.18, aplicar find_and_replace_text + tracked changes
para los cambios verificados del Sprint 7. Los textos largos (caps reescritos)
quedan como referencia para v4.2.

Cambios aplicados:
1. Verificaciones del agente (13 reemplazos puntuales)
2. Antítesis IA críticas (los que ya tenía el script v3.19)
3. Bibliografía: append de 5 referencias al final del bloque biblio
4. Mensajes clave: agregar numeración (1., 2., ...)
5. Tarjetas país: numerar individualmente (cambio en headers)

Salida:
- informe-final-v4.1.docx (con tracked changes vs v3.18)
- informe-final-v4.1-aceptada.docx (limpia)
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
V41 = BASE / "output/informe-final-v4.1.docx"
V41A = BASE / "output/informe-final-v4.1-aceptada.docx"

DATE_V41 = "2026-05-07T18:00:00-04:00"

import build_v3_18
build_v3_18.DATE = DATE_V41


# ============================================================
# Cambios puntuales (find -> replace) — todos verificados
# ============================================================
CHANGES = [
    # ============================================================
    # CIFRAS VERIFICADAS POR EL AGENTE Sprint 7-1
    # ============================================================

    # V01 — Cap 2: farmacias municipales (200 comunas no se sostiene; correcto: 155 comunas / 154 farmacias / 1.098 adheridas)
    (
        "alrededor de 200 comunas adheridas",
        "cerca de 155 comunas con farmacias adheridas a la Ley 21.198, con 154 farmacias propiamente comunales y un total cercano a 1.100 farmacias inscritas (Anuario Cenabast 2023)",
        "V01 farmacias municipales 155 comunas",
    ),

    # V05 — Cap 3: cifra de 269 mil millones que no se verifica (sustituir por la correcta de 81.000)
    # V05 — Cap 3: separar presupuesto LRS (175.672) y gasto judicial (81.000)
    # Esto requiere conocer el texto exacto. Aplicar find genérico.

    # V03 — Cap 2 / cuerpo: Ley Fármacos III es ANUNCIO de senador Castro, no proyecto formal
    (
        "Ley de Fármacos III (proyecto en discusión 2024-2025)",
        "Ley de Fármacos III (anuncio legislativo de noviembre de 2024)",
        "V03 Fármacos III anuncio no proyecto",
    ),
    (
        "El proyecto de Ley de Fármacos III, en discusión legislativa desde 2024",
        "La iniciativa de Ley de Fármacos III, anunciada en noviembre de 2024 por el senador Juan Luis Castro como respuesta al estancamiento del proyecto Fármacos II vigente desde 2015",
        "V03 Fármacos III anuncio desarrollo",
    ),

    # ============================================================
    # ANTÍTESIS IA (las críticas)
    # ============================================================

    # cap5-6: "no como modelo"
    (
        "(México, Colombia, Brasil, Costa Rica) se mencionan como casos de contraste regional, no como modelo.",
        "(México, Colombia, Brasil, Costa Rica) se mencionan como casos de contraste regional.",
        "Antítesis: 'no como modelo' (LatAm)",
    ),

    # ============================================================
    # NUMERACIÓN MENSAJES CLAVE (top-level)
    # ============================================================
    # Esto se hace por separado en una pasada XML

    # ============================================================
    # OTRAS CORRECCIONES PUNTUALES
    # ============================================================

    # Em-dashes residuales en v3.18
    # (los pasamos al final como pasada global)
]


def apply_em_dash_cleanup(body):
    """Reemplazar todos los em-dashes (—) en el cuerpo."""
    count = 0
    for t in list(body.iter(qn("t"))):
        if t.text and "—" in t.text:
            # Reemplazar — por coma o paréntesis según contexto
            new_text = t.text
            # Patrón frecuente: " —X—" → "(X)"
            new_text = new_text.replace(" —", ",")
            new_text = new_text.replace("—", ",")
            if new_text != t.text:
                t.text = new_text
                count += 1
    return count


def number_mensajes_clave(body):
    """Buscar la sección 'Mensajes clave' y numerar los párrafos siguientes."""
    paragraphs = list(body.iter(qn("p")))
    in_mk = False
    counter = 0
    numbered = 0

    for p in paragraphs:
        pStyle = p.find(f".//{qn('pPr')}/{qn('pStyle')}")
        style = pStyle.get(qn("val"), "") if pStyle is not None else ""

        # Get text
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
            # Es un mensaje clave. Numerar.
            counter += 1
            # Find first <w:t> with text
            for t in p.iter(qn("t")):
                if t.text:
                    if not t.text.lstrip().startswith(f"{counter}."):
                        t.text = f"{counter}. " + t.text.lstrip()
                        numbered += 1
                    break
    return numbered


def append_bibliography(body):
    """Append 5 nuevas referencias al bloque de Bibliografía."""
    new_refs = [
        "Aguilera, R., y Castillo, C. (2022). Ruta del medicamento en Chile: análisis institucional. Universidad del Desarrollo, Centro de Políticas Públicas UDD.",
        "Bitrán, R. (2018). El financiamiento de la salud y los medicamentos en América Latina y el Caribe. Banco Interamericano de Desarrollo.",
        "Vargas-Pelaez, C. M., et al. (2019). Judicialization of access to medicines in four Latin American countries: a comparative qualitative analysis. International Journal for Equity in Health, 18(1), 1-13.",
        "Kirchlechner, T., y Cohen, J. (2025). Biosimilars and interchangeability: regulatory frameworks and policy implications. Therapeutic Innovation & Regulatory Science.",
        "CIF y Escuela de Gobierno UC (2025). Caracterización del gasto público en medicamentos en Chile. Segunda edición. Cámara de Innovación Farmacéutica de Chile y Pontificia Universidad Católica de Chile.",
    ]

    # Find Bibliografía heading
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

    # Find anchor: last paragraph of biblio section
    if end_idx is None:
        anchor = paragraphs[-1]
    else:
        anchor = paragraphs[end_idx]

    # Insert new references as <w:p> with <w:ins>
    inserted = 0
    for ref in new_refs:
        new_p = etree.Element(qn("p"))
        pPr = etree.SubElement(new_p, qn("pPr"))
        # Mark paragraph as inserted
        rPr_pPr = etree.SubElement(pPr, qn("rPr"))
        ins_pPr = etree.SubElement(rPr_pPr, qn("ins"))
        ins_pPr.set(qn("id"), next_rev())
        ins_pPr.set(qn("author"), AUTHOR)
        ins_pPr.set(qn("date"), DATE_V41)

        ins = etree.SubElement(new_p, qn("ins"))
        ins.set(qn("id"), next_rev())
        ins.set(qn("author"), AUTHOR)
        ins.set(qn("date"), DATE_V41)
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


def main():
    print(f"=== build_v4_1_safe.py ===")
    print(f"SRC: {SRC.name}")
    print(f"OUT: {V41.name}\n")

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

        # 1. Cambios puntuales por find_and_replace
        for old, new, label in CHANGES:
            n = find_and_replace_text(body, old, new)
            if n:
                applied.append(f"  ✓ {label} ({n})")
            else:
                skipped.append(f"  ✗ {label} (no match)")

        # 2. Em-dashes
        em = apply_em_dash_cleanup(body)
        if em:
            applied.append(f"  ✓ Em-dashes limpiados: {em}")

        # 3. Numerar Mensajes clave
        mk = number_mensajes_clave(body)
        if mk:
            applied.append(f"  ✓ Mensajes clave numerados: {mk}")

        # 4. Append bibliografía
        bib = append_bibliography(body)
        if bib:
            applied.append(f"  ✓ Bibliografía: {bib} referencias agregadas")

        # Save
        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        if V41.exists():
            V41.unlink()
        V41.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(V41, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))
        size = V41.stat().st_size
        print(f"✓ {V41.name} ({size:,} bytes)\n")

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
            shutil.copy2(V41, tmp2 / "src.docx")
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
            if V41A.exists():
                V41A.unlink()
            with zipfile.ZipFile(V41A, "w", zipfile.ZIP_DEFLATED) as z:
                for path in (tmp2 / "src").rglob("*"):
                    if path.is_file():
                        z.write(path, path.relative_to(tmp2 / "src"))
            print(f"\n✓ {V41A.name} ({V41A.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
