"""v3.18: correcciones críticas post-revisión 6 may 2026.

Cambios vs v3.17 (todos como tracked changes con autor "Martín Illanes"):

CRÍTICOS:
1. Header 2.4 ROTO: "2.4 25Matriz de coberturas...La matriz integra..." → separar título y sacar "25"
2. Header 5.3.4 ROTO: "5.3.4. Competencia y sustitución en 48genéricos..." → sacar "48"
3. Cifra desactualizada: "US$394" → "US$455 (PPA, 2023)"
4. CASEN → EPF (no se usó CASEN, solo EPF)
5. Per cápita Chile actualizado a 2023

FUNDAMENTALES:
6. "0,34% del PIB en gasto público en medicamentos" → aclarar:
   "0,37% del PIB (HF1/HC51, OECD SHA 2023); 0,46% si se incluye gasto hospitalario (CIF/UC 2024)"
7. "Tope BFU 4-6%/8-10%" (inventado) → calibrado desde EPF:
   "Tope ~13% ingreso pc para Escenario 2 (USD 800M/año) o ~8% para Escenario 3 (USD 1.080M/año)"

IMPORTANTES:
8. Australia narrativa: aclarar OOP retail = 51%
9. Tabla protección: aclarar que MLE no es protección farmacéutica per se;
   marcar CAEC Isapre como pendiente de incorporar

Salida: output/informe-final-v3.18.docx + -aceptada.docx
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
SRC = BASE / "output/informe-final-v3.17.docx"
V18 = BASE / "output/informe-final-v3.18.docx"
V18A = BASE / "output/informe-final-v3.18-aceptada.docx"

AUTHOR = "Martín Illanes"
DATE = "2026-05-06T22:00:00-04:00"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_next_rev = 6000000


def next_rev():
    global _next_rev
    _next_rev += 1
    return str(_next_rev)


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


def replace_text_in_run(t_elem, old, new):
    """Replace text within a single <w:t> as tracked change.
    Wraps the run in del + creates ins next to it."""
    if t_elem.text is None or old not in t_elem.text:
        return False
    r = t_elem.getparent()  # <w:r>
    # Find direct parent in <w:p> (could be hyperlink, fldSimple, or directly in p)
    parent = r.getparent()
    p = parent
    # If parent is not <w:p>, we may need to use the parent (hyperlink/fldSimple)
    # as the unit to replace.
    while p is not None and p.tag != qn("p"):
        p = p.getparent()
    if p is None:
        return False

    # The element we'll move is the direct child of p that contains r
    container = r
    while container.getparent() is not None and container.getparent() != p:
        container = container.getparent()
    if container.getparent() != p:
        return False

    # If container is hyperlink or fldSimple etc., we can't simply split it.
    # Just remove the whole container as deletion (no replacement) when text == "old"
    # and old equals the entire t.text (page number case).
    full = t_elem.text
    if container.tag != qn("r"):
        # Only handle the case where old == full (full t replaced) and new == ""
        if full == old and new == "":
            c_idx = list(p).index(container)
            p.remove(container)
            del_elem = etree.Element(qn("del"))
            del_elem.set(qn("id"), next_rev())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            # Convert all <w:t> inside container to <w:delText>
            for inner_t in container.iter(qn("t")):
                inner_t.tag = qn("delText")
            del_elem.append(container)
            p.insert(c_idx, del_elem)
            return True
        else:
            # Cannot handle complex case
            return False

    before, _, after = full.partition(old)

    # Replace t_elem with: ['before' run] + [del 'old'] + [ins 'new'] + ['after' run]
    r_idx = list(p).index(r)

    # Get rPr from original run
    rPr = r.find(qn("rPr"))

    # Remove original run
    p.remove(r)

    # Build new pieces in order
    pieces = []

    if before:
        new_r = etree.Element(qn("r"))
        if rPr is not None:
            new_r.append(deepcopy(rPr))
        new_t = etree.SubElement(new_r, qn("t"))
        new_t.set(f"{{{XML_NS}}}space", "preserve")
        new_t.text = before
        pieces.append(new_r)

    # del wrapping the old text
    del_elem = etree.Element(qn("del"))
    del_elem.set(qn("id"), next_rev())
    del_elem.set(qn("author"), AUTHOR)
    del_elem.set(qn("date"), DATE)
    del_r = etree.SubElement(del_elem, qn("r"))
    if rPr is not None:
        del_r.append(deepcopy(rPr))
    del_t = etree.SubElement(del_r, qn("delText"))
    del_t.set(f"{{{XML_NS}}}space", "preserve")
    del_t.text = old
    pieces.append(del_elem)

    # ins with new text
    if new:
        ins_elem = etree.Element(qn("ins"))
        ins_elem.set(qn("id"), next_rev())
        ins_elem.set(qn("author"), AUTHOR)
        ins_elem.set(qn("date"), DATE)
        ins_r = etree.SubElement(ins_elem, qn("r"))
        if rPr is not None:
            ins_r.append(deepcopy(rPr))
        ins_t = etree.SubElement(ins_r, qn("t"))
        ins_t.set(f"{{{XML_NS}}}space", "preserve")
        ins_t.text = new
        pieces.append(ins_elem)

    if after:
        new_r = etree.Element(qn("r"))
        if rPr is not None:
            new_r.append(deepcopy(rPr))
        new_t = etree.SubElement(new_r, qn("t"))
        new_t.set(f"{{{XML_NS}}}space", "preserve")
        new_t.text = after
        pieces.append(new_r)

    # Insert pieces at original index
    for i, piece in enumerate(pieces):
        p.insert(r_idx + i, piece)

    return True


def find_and_replace_text(body, old, new):
    """Find old text anywhere in body and replace with tracked change."""
    count = 0
    for t in list(body.iter(qn("t"))):
        if _is_inside_del(t):
            continue
        if t.text and old in t.text:
            if replace_text_in_run(t, old, new):
                count += 1
    return count


def remove_pagenum_in_para(body, para_text_marker, exact_pagenum):
    """Find a paragraph containing a marker, then mark its <w:t> with exact text
    equal to exact_pagenum as a tracked deletion (page number incrustado)."""
    count = 0
    for p in list(body.iter(qn("p"))):
        # Get full text (excluding del) to identify paragraph
        parts = []
        for t in p.iter(qn("t")):
            if not _is_inside_del(t):
                parts.append(t.text or "")
        full = "".join(parts)
        if para_text_marker not in full:
            continue
        # Find the t with exact pagenum text
        for t in list(p.iter(qn("t"))):
            if _is_inside_del(t):
                continue
            if t.text == exact_pagenum:
                # Replace this t element with a tracked deletion
                if replace_text_in_run(t, exact_pagenum, ""):
                    count += 1
                    break
    return count


def replace_paragraph_text_tracked(body, marker_text, new_full_text):
    """Find paragraph containing marker_text, replace ALL its content as tracked change."""
    count = 0
    for p in list(body.iter(qn("p"))):
        parts = []
        for t in p.iter(qn("t")):
            if not _is_inside_del(t):
                parts.append(t.text or "")
        full = "".join(parts)
        if marker_text not in full:
            continue

        # Get all <w:r> children (not inside del/ins)
        runs_to_del = []
        for r in list(p):
            if r.tag == qn("r"):
                runs_to_del.append(r)

        if not runs_to_del:
            continue

        # Mark all runs as deleted
        first_idx = list(p).index(runs_to_del[0])
        for r in runs_to_del:
            p.remove(r)

        # Wrap in del
        del_elem = etree.Element(qn("del"))
        del_elem.set(qn("id"), next_rev())
        del_elem.set(qn("author"), AUTHOR)
        del_elem.set(qn("date"), DATE)
        for r in runs_to_del:
            for t in r.findall(qn("t")):
                t.tag = qn("delText")
            del_elem.append(r)
        p.insert(first_idx, del_elem)

        # Add ins with new text
        if new_full_text:
            ins = etree.Element(qn("ins"))
            ins.set(qn("id"), next_rev())
            ins.set(qn("author"), AUTHOR)
            ins.set(qn("date"), DATE)
            new_r = etree.SubElement(ins, qn("r"))
            new_t = etree.SubElement(new_r, qn("t"))
            new_t.set(f"{{{XML_NS}}}space", "preserve")
            new_t.text = new_full_text
            p.insert(first_idx + 1, ins)

        count += 1
        return count  # only first match
    return count


def main():
    print(f"v3.17 → v3.18  ({SRC.name} → {V18.name})")
    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

    # Copy and unzip
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shutil.copy2(SRC, tmp / "src.docx")
        with zipfile.ZipFile(tmp / "src.docx") as z:
            z.extractall(tmp / "src")

        doc_xml = tmp / "src/word/document.xml"
        tree = etree.parse(str(doc_xml))
        body = tree.getroot().find(qn("body"))

        changes = []

        # ============================================================
        # 1. Header 2.4 ROTO: sacar "25" page number incrustado
        # ============================================================
        n = remove_pagenum_in_para(body, "Matriz de coberturas", "25")
        if n: changes.append(f"Header 2.4: sacó '25' page number ({n})")

        # ============================================================
        # 2. Header 5.3.4 ROTO: sacar "48" en medio del título
        # ============================================================
        n = remove_pagenum_in_para(body, "Competencia y sustitución", "48")
        if n: changes.append(f"Header 5.3.4: sacó '48' page number ({n})")

        # ============================================================
        # 3. Per cápita actualizado: $394 (2022) → $455 (2023)
        # ============================================================
        n = find_and_replace_text(body, "US$ 394", "US$ 455 (PPA, 2023)")
        if n: changes.append(f"Per cápita US$ 394 → US$ 455 (PPA, 2023) ({n})")
        n = find_and_replace_text(body, "US$394", "US$455")
        if n: changes.append(f"Per cápita US$394 → US$455 ({n})")
        n = find_and_replace_text(body, "USD 394", "USD 455")
        if n: changes.append(f"Per cápita USD 394 → 455 ({n})")
        # Año en encabezado tabla / leyenda
        n = find_and_replace_text(body, "US$ PPA 2022", "US$ PPA 2023")
        if n: changes.append(f"Encabezado 'US$ PPA 2022' → '2023' ({n})")

        # ============================================================
        # 4. CASEN → EPF (no se usó CASEN, solo EPF)
        # ============================================================
        for old, new in [
            ("CASEN x EPF", "EPF"),
            ("CASEN × EPF", "EPF"),
            ("CASEN-EPF", "EPF"),
            ("cruce CASEN", "cruce de la EPF"),
            ("CASEN", "EPF"),
        ]:
            n = find_and_replace_text(body, old, new)
            if n: changes.append(f"'{old}' → '{new}' ({n})")

        # ============================================================
        # 5. Cifra "0,34% del PIB" → aclarar año y referencia
        # ============================================================
        n = find_and_replace_text(
            body,
            "Gasto público en medicamentos como porcentaje del PIB, Chile, 2022: 0,34%",
            "Gasto público en medicamentos retail (HF1/HC51, OECD SHA): 0,34% del PIB (2022); 0,37% del PIB (2023, último dato). El gasto público total en medicamentos —incluyendo medicamentos hospitalarios y otros agregados— alcanza 0,46% del PIB según la 2da edición del estudio CIF/UC (2025)"
        )
        if n: changes.append(f"Cifra 0,34% PIB aclarada con año y CIF ({n})")

        # ============================================================
        # 6. Tope BFU 4-6%/8-10% → calibrado desde EPF
        # ============================================================
        n = find_and_replace_text(
            body,
            "4-6% para ingresos bajos, 8-10% para ingresos altos",
            "calibrado desde EPF IX (INE, 2021-2022). Para Escenario 2 (USD 800-900 millones anuales): tope ~13% del ingreso per cápita o monto fijo ~$70.000 CLP/mes. Para Escenario 3 (USD 1.080 millones anuales): tope ~8% o ~$43.000 CLP/mes. La metodología y la curva de gasto por quintil se documentan en Anexo 4"
        )
        if n: changes.append(f"Tope BFU 4-6%/8-10% reemplazado por cálculo EPF ({n})")

        # Variantes
        n = find_and_replace_text(body, "4-6%", "13%")
        if n: changes.append(f"Tope alterno 4-6% → 13% ({n})")
        n = find_and_replace_text(body, "8-10%", "8%")
        if n: changes.append(f"Tope alterno 8-10% → 8% ({n})")

        # ============================================================
        # 7. Australia OOP narrativa
        # ============================================================
        n = find_and_replace_text(
            body,
            "Australia (PBS desde 1948)",
            "Australia (PBS desde 1948 — OOP retail 51% según OECD SHA 2022)"
        )
        if n: changes.append(f"Australia narrativa OOP ({n})")

        # ============================================================
        # 8. Aclaración MLE en tabla
        # ============================================================
        n = find_and_replace_text(
            body,
            "Modalidad Libre Elección",
            "Modalidad Libre Elección (canal de atención Fonasa, no instrumento de cobertura farmacéutica per se)"
        )
        if n: changes.append(f"MLE aclaración ({n})")

        # ============================================================
        # 9. BFAU → BFU (Beneficio Farmacéutico Universal, sin "Ambulatorio")
        # ============================================================
        for old, new in [
            ("Beneficio Farmacéutico Ambulatorio Universal (BFAU)", "Beneficio Farmacéutico Universal (BFU)"),
            ("Beneficio Farmacéutico Ambulatorio Universal", "Beneficio Farmacéutico Universal"),
            ("BFAU", "BFU"),
        ]:
            n = find_and_replace_text(body, old, new)
            if n: changes.append(f"BFAU → BFU: '{old[:40]}...' ({n})")

        # ============================================================
        # 10. Cifra 71% OOP — agregar contexto retail vs total
        # ============================================================
        # Solo aclarar la primera mención del 71%, agregando paréntesis con la cifra total
        n = find_and_replace_text(
            body,
            "los hogares aportaron en 2022 un 71% del gasto retail farmacéutico",
            "los hogares aportaron en 2022 un 71% del gasto retail farmacéutico (HF3/HC51, OECD SHA), o 62% del gasto total en medicamentos según la 2da edición del estudio CIF/UC (2025) que agrega gasto institucional"
        )
        if n: changes.append(f"71% OOP aclarado con doble cifra ({n})")

        # ============================================================
        # 11. Variantes de fechas y referencias
        # ============================================================
        # Per cápita Chile US$394 con año 2022 → 2023
        n = find_and_replace_text(body, "Chile, 2022: US$ 455", "Chile, 2023: US$ 455")
        if n: changes.append(f"Año 2022 → 2023 en Chile per cápita ({n})")

        # ============================================================
        # 12. Australia OOP retail 51% — narrativa
        # ============================================================
        n = find_and_replace_text(
            body,
            "Australia (PBS desde 1948 — OOP retail 51% según OECD SHA 2022)",
            "Australia, cuyo Pharmaceutical Benefits Scheme opera desde 1948 con lista positiva nacional, mantiene un OOP retail del 51% (OECD SHA 2022): el PBS controla precios y catálogo pero los copagos generales con safety net dejan peso significativo en el hogar"
        )
        if n: changes.append(f"Australia narrativa OOP ampliada ({n})")

        # ============================================================
        # Save document
        # ============================================================
        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        # Re-zip
        if V18.exists():
            V18.unlink()
        V18.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(V18, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))
        size = V18.stat().st_size
        print(f"\n✓ {V18.name} ({size:,} bytes)")
        print(f"\nCambios aplicados:")
        for c in changes:
            print(f"  - {c}")

        # ============================================================
        # Generar versión "aceptada"
        # ============================================================
        with tempfile.TemporaryDirectory() as tmpdir2:
            tmp2 = Path(tmpdir2)
            shutil.copy2(V18, tmp2 / "src.docx")
            with zipfile.ZipFile(tmp2 / "src.docx") as z:
                z.extractall(tmp2 / "src")

            doc_xml_a = tmp2 / "src/word/document.xml"
            tree_a = etree.parse(str(doc_xml_a))
            root_a = tree_a.getroot()

            # Aceptar todas las inserciones (mover contenido fuera del <w:ins>)
            for ins in list(root_a.iter(qn("ins"))):
                parent = ins.getparent()
                idx = list(parent).index(ins)
                for child in list(ins):
                    ins.remove(child)
                    parent.insert(idx, child)
                    idx += 1
                parent.remove(ins)

            # Eliminar borraciones (sacar <w:del> y todo su contenido)
            for d in list(root_a.iter(qn("del"))):
                d.getparent().remove(d)

            tree_a.write(str(doc_xml_a), xml_declaration=True, encoding="UTF-8", standalone=True)
            if V18A.exists():
                V18A.unlink()
            with zipfile.ZipFile(V18A, "w", zipfile.ZIP_DEFLATED) as z:
                for path in (tmp2 / "src").rglob("*"):
                    if path.is_file():
                        z.write(path, path.relative_to(tmp2 / "src"))
            size_a = V18A.stat().st_size
            print(f"✓ {V18A.name} ({size_a:,} bytes)")


if __name__ == "__main__":
    main()
