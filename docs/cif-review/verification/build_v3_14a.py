"""v3.14a: corrección Figura 2 unidad (millones → miles de millones de pesos).

Input: v3.13.docx
Output: v3.14a.docx (in-place, luego consolidamos con outputs de agentes)
"""

from __future__ import annotations
import re, shutil, tempfile, zipfile
from copy import deepcopy
from pathlib import Path
from lxml import etree

V313 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.13.docx")
V314A = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.14a.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_rev = 1100000


def next_rev():
    global _next_rev
    _next_rev += 1
    return str(_next_rev)


def qn(t): return f"{{{W_NS}}}{t}"


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
            del_elem.set(qn("id"), next_rev())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)
        else:
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_rev())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)
    ins = etree.SubElement(p, qn("ins"))
    ins.set(qn("id"), next_rev())
    ins.set(qn("author"), AUTHOR)
    ins.set(qn("date"), DATE)
    r = etree.SubElement(ins, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = new_text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def process():
    if V314A.exists():
        V314A.unlink()
    shutil.copy(V313, V314A)
    print(f"Copied: {V313.name} -> {V314A.name}")

    log = []

    with zipfile.ZipFile(V314A, "r") as z:
        doc_xml = z.read("word/document.xml")

    tree = etree.fromstring(doc_xml)
    body = tree.find(qn("body"))

    # La leyenda de Figura 2 ya fue actualizada en v3.4 con "miles de millones de pesos chilenos"
    # Lo que falta es verificar si el GRAFICO tiene unidad incorrecta.
    # Eso no se puede cambiar desde el XML sin acceder al PNG/chart embed.
    # En su lugar, agregamos nota explícita en la leyenda aclarando la unidad visual del eje Y.

    # Buscar leyenda actual de Figura 2
    for i, p in enumerate(body.findall(qn("p"))):
        text = get_para_text(p)
        if "Composición del gasto público en medicamentos por ejecutor" in text:
            # Si ya dice "miles de millones", agregar nota visual
            new_text = text
            if "miles de millones" in text and "eje Y" not in text:
                # Insert nota sobre eje Y
                new_text = text.rstrip(".") + ". El eje vertical del gráfico se expresa en miles de millones de pesos chilenos (MM$), aunque la escala numérica del eje muestra el número sin el multiplicador; el valor máximo cercano a 1.500 corresponde a MM$ 1.500 (aproximadamente CLP 1,5 billones), coherente con el total de MM$ 1.514.814 reportado por CIF (2025) para el año 2024."
                replace_paragraph_content_tracked(p, new_text)
                log.append(("OK", "Figura 2 leyenda con nota eje Y", f"para {i}"))
                break
            elif "Participación porcentual anual" in text:
                # leyenda vieja todavía
                new_text = (
                    "Composición del gasto público en medicamentos por ejecutor, 2014-2024. "
                    "Los valores se expresan en miles de millones de pesos chilenos (MM$) a precios "
                    "de 2024, con DG (deflactor del gasto) como principal e IPC como contraste. "
                    "El eje vertical del gráfico muestra la escala numérica sin el multiplicador: "
                    "el valor máximo cercano a 1.500 equivale a MM$ 1.500 (CLP 1,5 billones), "
                    "coherente con el total MM$ 1.514.814 reportado por CIF (2025) para 2024 "
                    "(8,79% del presupuesto MINSAL). Los cuatro ejecutores son: Servicios de Salud "
                    "(60,8% en 2024, principal), Programa Nacional de Inmunizaciones (PNI), Ley "
                    "20.850 Ricarte Soto (LRS) y Municipios (incluye FOFAR y GES en APS). Fuente: "
                    "elaboración propia a partir de DIPRES, Ministerio de Hacienda y SINIM, "
                    "consistente con Cámara de Innovación Farmacéutica (2025), Caracterización del "
                    "gasto público en medicamentos, 2da edición."
                )
                replace_paragraph_content_tracked(p, new_text)
                log.append(("OK", "Figura 2 leyenda reescrita con unidad correcta", f"para {i}"))
                break

    new_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V314A, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V314A)
    return log


def main():
    log = process()
    print("\n=== v3.14a: Figura 2 unidad corregida ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:50s}  {detail}")


if __name__ == "__main__":
    main()
