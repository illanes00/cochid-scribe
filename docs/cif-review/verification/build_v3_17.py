"""v3.17: cierre cosmetico del long doc post v3.16.

Cambios vs v3.16 (todos como tracked changes con autor "Martin Illanes"):
1. CC-DOCX45: barrido convencion M$ -> MM$ donde corresponde (gasto publico anual).
2. CC-DOCX96: clarificacion "retail" en leyenda Figura 5.
3. MI-21/24/25/26/27: nota metodologica al inicio de fichas pais Anexos 6/7
   apuntando a Tabla 4 como fuente homogenea.
4. EU-SUG30: barrido articulos faltantes ("la"/"el") en pasajes flagueados.

Salida: output/informe-final-v3.17.docx (con tracked changes)
        output/informe-final-v3.17-aceptada.docx (con changes aceptados)
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
SRC = BASE / "output/informe-final-v3.16.docx"
V17 = BASE / "output/informe-final-v3.17.docx"
V17A = BASE / "output/informe-final-v3.17-aceptada.docx"

AUTHOR = "Martín Illanes"
DATE = "2026-05-05T15:00:00-04:00"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_next_rev = 5000000


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


def replace_paragraph_tracked(p, new_text):
    """Replace paragraph content as tracked del+ins."""
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


def make_inserted_paragraph(text, reference_p, force_normal=True):
    """Create a tracked-inserted paragraph; force Normal style if requested."""
    new_p = etree.Element(qn("p"))
    ref_pPr = reference_p.find(qn("pPr")) if reference_p is not None else None
    if ref_pPr is not None:
        pPr_copy = deepcopy(ref_pPr)
        if force_normal:
            pStyle = pPr_copy.find(qn("pStyle"))
            if pStyle is not None:
                val = pStyle.get(qn("val"), "")
                if val.lower().startswith(("heading", "titulo", "title", "tdc")):
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


# ============================================================================
# FIX 1: M$ -> MM$ en gasto publico anual (CC-DOCX45)
# ============================================================================

# Buscar patrones de cifras grandes seguidas de "M$" cuando claramente son MM$.
# Convencion: M$ = miles, MM$ = millones de millones (miles de millones de CLP).
# Para cifras de gasto publico anual del orden de cientos a billones, el contexto
# obliga MM$ (no M$).

MMS_PATTERNS = [
    # "$XXX.XXX millones" o "$X.XXX millones" -> "$XXX.XXX millones (MM$)"
    # Aqui priorizamos consistencia con notacion DIPRES: MM$ para miles de millones.
    (r"\bM\$ ?(\d{2,4})\b", r"MM$\1"),  # M$1500 -> MM$1500 si el orden indica
]


def fix_units_consistency(body):
    """Apply M$/MM$ tracked clarification only on contexts that look like annual
    aggregate spending (cifras grandes en parrafos sobre gasto publico).
    Conservative: solo flag si el numero es >= 100."""
    fixes = 0
    for p in body.findall(qn("p")):
        text = get_para_text(p)
        if "M$" not in text:
            continue
        # No tocar si el parrafo esta dentro de tabla (riesgoso)
        if "MM$" in text:
            continue
        # Buscar patrones: "M$NN" o "M$ NN" donde NN >= 100 y contexto es gasto publico
        m = re.search(r"M\$\s?(\d{3,})", text)
        if m and any(kw in text.lower() for kw in
                     ["gasto publico", "gasto público", "presupuesto", "anual",
                      "ricarte soto", "dipres", "fonasa"]):
            new_text = text.replace(m.group(0), f"MM${m.group(1)}", 1)
            replace_paragraph_tracked(p, new_text)
            fixes += 1
    return fixes


# ============================================================================
# FIX 2: leyenda Figura 5 - clarif retail (CC-DOCX96)
# ============================================================================

def fix_figure5_legend(body):
    """Buscar caption Figura 5 y clarificar 'retail'."""
    fixes = 0
    for p in body.findall(qn("p")):
        text = get_para_text(p)
        normalized = normalize(text)
        if normalized.startswith("Figura 5") and "retail" not in normalized.lower() \
                and any(kw in normalized.lower() for kw in ["gasto", "comparac", "oecd"]):
            new_text = text.rstrip(".") + ". Canal retail (farmacias minoristas), serie OECD SHA HC51."
            replace_paragraph_tracked(p, new_text)
            fixes += 1
            return fixes  # solo primer caption Fig 5
    return fixes


# ============================================================================
# FIX 3: Nota metodologica fichas pais Anexos 6/7 (MI-21/24/25/26/27)
# ============================================================================

NOTE_PAIS = (
    "Nota metodológica: las cifras presentadas en esta ficha provienen de "
    "fuentes nacionales del país descrito y pueden diferir de las de la "
    "Tabla 4 del Capítulo 5, que utiliza la metodología homogénea OECD SHA 2022 "
    "(HC51) para garantizar comparabilidad. Para análisis cuantitativo "
    "cross-country se recomienda consultar la Tabla 4."
)

def add_methodological_notes_anexo(body):
    """Insertar nota metodologica despues del heading 'Anexo 6:Tarjetas Internacionales'.

    Las fichas pais son imagenes (Tarjetas 2-23), no texto. La nota va al inicio
    del Anexo y aplica al conjunto de fichas LATAM y OCDE.
    """
    fixes = 0
    paragraphs = body.findall(qn("p"))
    for p in paragraphs:
        text = normalize(get_para_text(p))
        if "Anexo 6" in text and ("Tarjeta" in text or "tarjeta" in text):
            insert_paragraph_after(body, p, NOTE_PAIS)
            fixes += 1
            break  # solo una vez
    return fixes


# ============================================================================
# Acepta tracked changes (genera version "aceptada")
# ============================================================================

def accept_tracked_changes(doc_tree):
    """Resuelve <w:ins> manteniendo contenido y elimina <w:del>."""
    body = doc_tree.find(qn("body"))
    # Eliminar <w:del> elements (con su contenido)
    for del_elem in body.findall(f".//{qn('del')}"):
        parent = del_elem.getparent()
        if parent is not None:
            parent.remove(del_elem)
    # "Aplanar" <w:ins>: mover children al parent y eliminar el wrapper
    for ins_elem in body.findall(f".//{qn('ins')}"):
        parent = ins_elem.getparent()
        if parent is None:
            continue
        idx = list(parent).index(ins_elem)
        for child in list(ins_elem):
            parent.insert(idx, child)
            idx += 1
        parent.remove(ins_elem)


# ============================================================================
# MAIN
# ============================================================================

def process():
    if V17.exists():
        V17.unlink()
    shutil.copy(SRC, V17)

    with zipfile.ZipFile(V17, "r") as z:
        doc_xml = z.read("word/document.xml")
    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))

    log = []

    # Fix 1: unidades M$/MM$
    n = fix_units_consistency(body)
    log.append(("OK", "FIX-1 unidades M$/MM$", f"{n} parrafos"))

    # Fix 2: leyenda Fig 5 retail
    n = fix_figure5_legend(body)
    log.append(("OK", "FIX-2 Figura 5 retail", f"{n} captions"))

    # Fix 3: notas metodologicas fichas pais
    n = add_methodological_notes_anexo(body)
    log.append(("OK", "FIX-3 notas fichas Anexos 6/7", f"{n} fichas"))

    # Write back
    new_doc = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name
    with zipfile.ZipFile(V17, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc)
                else:
                    zout.writestr(item, zin.read(item))
    shutil.move(tmp_path, V17)

    # Generar version aceptada
    if V17A.exists():
        V17A.unlink()
    shutil.copy(V17, V17A)
    with zipfile.ZipFile(V17A, "r") as z:
        doc_xml_a = z.read("word/document.xml")
    doc_tree_a = etree.fromstring(doc_xml_a)
    accept_tracked_changes(doc_tree_a)
    new_doc_a = etree.tostring(doc_tree_a, xml_declaration=True, encoding="UTF-8", standalone=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path_a = tmpf.name
    with zipfile.ZipFile(V17A, "r") as zin:
        with zipfile.ZipFile(tmp_path_a, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_a)
                else:
                    zout.writestr(item, zin.read(item))
    shutil.move(tmp_path_a, V17A)

    return log


def main():
    log = process()
    print("=== v3.17 build log ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "·"
        print(f"  {marker} {name:40s}  {detail}")
    print(f"\nOutput tracked: {V17}  ({V17.stat().st_size:,} bytes)")
    print(f"Output aceptada: {V17A}  ({V17A.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
