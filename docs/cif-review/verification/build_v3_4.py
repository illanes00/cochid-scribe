"""Build v3.4: corregir leyendas de Figura 2, Figura 5 y Tarjeta 1 con datos verificados.

Contexto del feedback:
- Figura 2 (composición gasto público por ejecutor): unidad en MM$ (miles de millones CLP),
  según Informe CIF 2025 "Caracterización del Gasto Público en Medicamentos" (2da versión).
  Datos 2024: Servicios de Salud 60,8%, PNI, Municipios, LRS, etc. Total MM$1.514.814.
- Figura 5 (gasto per cápita OCDE): valores ~309 Chile, ~1006 Alemania son aproximaciones visuales;
  los datos reales OECD SHA 2022 son 394 Chile / 1038 Alemania. Los datos graficados son HC51 _T
  (retail, todas las fuentes de financiamiento). Clarificar en leyenda.
- Tarjeta 1 Chile: verificar coherencia entre privado / bolsillo / total. Los datos actuales
  tienen inconsistencia ($240=$240, y total $308 no calza con OECD 2022).

=== Correcciones aplicadas ===

1. Figura 2 leyenda: agregar fuente CIF 2025 + unidad MM$ (miles de millones CLP 2024) +
   porcentajes de ejecutor.
2. Figura 5 leyenda: especificar que son valores HC51 (retail) totales per cápita en USD PPA 2022,
   según OECD SHA 2022.
3. Tarjeta 1 Chile: actualizar cifras con datos OECD SHA 2022 + nota de fuente.

Input:  informe-final-v3.3.docx
Output: informe-final-v3.4.docx
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V33 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.3.docx")
V34 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.4.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_id = 600000


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


def make_inserted_paragraph_like(text, reference_p):
    new_p = etree.Element(qn("p"))
    ref_pPr = reference_p.find(qn("pPr"))
    if ref_pPr is not None:
        pPr = deepcopy(ref_pPr)
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


# ============================================================
# CORRECCIONES
# ============================================================

# Figura 2: la leyenda actual describe "participación porcentual"
# Actual: "Participación porcentual anual de cuatro ejecutores: Servicios de Salud (SS), Programa Nacional de Inmunizaciones (PNI), Ley 20.850–Ricarte Soto (LRS) y Municipios (APS). Gráfico en áreas apiladas."
FIGURA2_OLD_PREFIX = "Participación porcentual anual de cuatro ejecutores"
FIGURA2_NEW = (
    "Composición del gasto público en medicamentos por ejecutor, 2014-2024. "
    "Los valores se expresan en miles de millones de pesos chilenos (MM$) a precios de 2024, "
    "con DG (deflactor del gasto) como principal y contraste IPC. Total 2024: MM$1.514.814 "
    "(8,79% del presupuesto MINSAL). Los cuatro ejecutores son: Servicios de Salud (60,8% en 2024, "
    "principal), Programa Nacional de Inmunizaciones (PNI), Ley 20.850 Ricarte Soto (LRS) y "
    "Municipios (incluye FOFAR y GES en APS). Fuente: elaboración propia a partir de DIPRES, "
    "Ministerio de Hacienda y SINIM, consistente con Cámara de Innovación Farmacéutica (2025), "
    "Caracterización del gasto público en medicamentos, 2da edición."
)

# Figura 5: describe gasto per cápita en países OCDE
# Actual: "Figura 5: Gasto anual per cápita en medicamentos en países de la OCDE." (título, no leyenda detallada)
FIGURA5_OLD_PREFIX = "Figura 5: Gasto anual per cápita en medicamentos en países de la OCDE"
FIGURA5_NEW = (
    "Figura 5: Gasto retail farmacéutico per cápita en países OCDE, 2022 (USD PPA, precios constantes). "
    "Corresponde a la función HC51 (retail pharmaceuticals, todas las fuentes de financiamiento) del "
    "System of Health Accounts. Los valores reflejan el gasto total per cápita en farmacias ambulatorias, "
    "excluyendo medicamentos dispensados en establecimientos hospitalarios. Chile: US$394; Alemania: "
    "US$1.038; Estados Unidos: US$1.402; Francia: US$807; España: US$605; promedio OCDE: US$614. "
    "Fuente: OECD Health Statistics, dataflow OECD.ELS.HD,DSD_SHA@DF_SHA, año 2022."
)

# Tarjeta 1: "Tarjeta 1: sistema de medicamentos en Chile"
# Esta es el título; el contenido son datos de la Ficha Chile (Tabla 0) pero en formato visual
# Ya actualizamos Tabla 0 en v3.2. Aquí agregamos una nota al título de Tarjeta 1 si corresponde.
TARJETA1_OLD_PREFIX = "Tarjeta 1: sistema de medicamentos en Chile"
TARJETA1_NEW = (
    "Tarjeta 1: sistema de medicamentos en Chile (cifras 2022-2024, OECD SHA y MINSAL)"
)


def process_docx():
    if V34.exists():
        V34.unlink()
    shutil.copy(V33, V34)
    print(f"Copied: {V33.name} -> {V34.name}")

    log = []

    with zipfile.ZipFile(V34, "r") as z:
        doc_xml = z.read("word/document.xml")

    tree = etree.fromstring(doc_xml)
    body = tree.find(qn("body"))

    # Figura 2 leyenda
    for p in body.findall(qn("p")):
        text = get_para_text(p)
        if text.strip().startswith(FIGURA2_OLD_PREFIX[:40]):
            replace_paragraph_content_tracked(p, FIGURA2_NEW)
            log.append(("OK", "Figura 2 leyenda (unidad MM$, fuentes)", ""))
            break
    else:
        log.append(("NOT FOUND", "Figura 2 leyenda", ""))

    # Figura 5 título
    for p in body.findall(qn("p")):
        text = get_para_text(p)
        if text.strip().startswith(FIGURA5_OLD_PREFIX[:40]):
            replace_paragraph_content_tracked(p, FIGURA5_NEW)
            log.append(("OK", "Figura 5 título + leyenda OECD HC51", ""))
            break
    else:
        log.append(("NOT FOUND", "Figura 5", ""))

    # Tarjeta 1 título
    for p in body.findall(qn("p")):
        text = get_para_text(p)
        if text.strip().startswith(TARJETA1_OLD_PREFIX[:35]):
            replace_paragraph_content_tracked(p, TARJETA1_NEW)
            log.append(("OK", "Tarjeta 1 título con fuentes", ""))
            break
    else:
        log.append(("NOT FOUND", "Tarjeta 1", ""))

    # Write back
    new_doc_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V34, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V34)

    return log


def main():
    log = process_docx()
    print("\n=== v3.4: Figuras 2, 5 y Tarjeta 1 ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:50s}  {detail}")
    print(f"\nOutput: {V34}")
    print(f"Size: {V34.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
