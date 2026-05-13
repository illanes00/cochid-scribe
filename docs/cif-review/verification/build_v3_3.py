"""Build v3.3: renumerar tablas + aplicar feedbacks Resumen Ejecutivo.

=== BLOQUE A: Renumeración de tablas ===

Orden actual en el documento (por posición de aparición):
  Para 641: "Tabla 6: Gasto público adicional..."    → renombrar a "Tabla 1"
  Para 1087: "Tabla 2: Propuestas presidenciales"    → renombrar a "Tabla 2" (sin cambio)
  Para 1144: "Tabla 3: Gasto de bolsillo..."         → sin cambio
  Para 1147: "Tabla 4: Comparación internacional..." → sin cambio
  Para 1152: "Tabla 5: Normativa..."                  → sin cambio

Wait: actualmente son 5 labels y hay 9 tablas en el doc (incluyendo Tabla 0 "ficha Chile").
Decisión: la "Tabla 6" que aparece en para 641 (dentro de Cap 6.2.3) es la única con número
alto; el resto (2-5) van secuenciales. Falta una Tabla 1.

Renumeración final (secuencial por aparición):
  Tabla 6 (pos 641) → Tabla 1
  Tabla 2 (pos 1087) → Tabla 2
  Tabla 3 (pos 1144) → Tabla 3
  Tabla 4 (pos 1147) → Tabla 4
  Tabla 5 (pos 1152) → Tabla 5

Las tablas-ficha (Chile, Alemania, Argentina en las Tarjetas) no llevan número, mantienen
su formato actual porque son recuadros visuales, no tablas numeradas.

=== BLOQUE B: Feedback Resumen Ejecutivo ===

Aplicar reply updates sobre los comentarios mencionados por Martín:

1. id=28 Eduardo (mensajes clave hipervínculos) → "Aceptado. Se agregará columna con referencia al capítulo..."
2. id=29/34 Eduardo (jargon "canal retail") → "Aceptado. Se reemplaza 'canal retail' por 'farmacias privadas (canal retail)'..."
3. id=31 Carla 9 (alto costo) → cambiar de "Aceptado." a respuesta completa sobre cobertura universal
4. id=37 Carla 12 (GES alto costo) → ya tenía reply; verificar que sea adecuado
5. id=39 Eduardo 37 "y coordinada" → cambiar de RECHAZADO a ACEPTADO
6. id=36 Eduardo 41 "brechas de canasta" → ya aceptado, sin cambio
7. id=40 Eduardo 27 (párrafo efectividad conjunta) → cambiar de PENDIENTE a ACEPTADO
8. id=42 Carla 15 (FONASA MLE/MAI) → ya tiene respuesta, sin cambio
9. id=44 Eduardo 42 (informada por evidencia) → ya aceptado, sin cambio

Input:  informe-final-v3.2.docx
Output: informe-final-v3.3.docx
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V32 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.2.docx")
V33 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.3.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_id = 500000


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


def replace_comment_reply(comment_elem, new_reply_text):
    paragraphs = comment_elem.findall(qn("p"))
    if len(paragraphs) < 2:
        # Add reply as new paragraph
        new_p = etree.SubElement(comment_elem, qn("p"))
        if paragraphs:
            src_pPr = paragraphs[0].find(qn("pPr"))
            if src_pPr is not None:
                new_p.insert(0, deepcopy(src_pPr))
        r = etree.SubElement(new_p, qn("r"))
        t = etree.SubElement(r, qn("t"))
        t.text = new_reply_text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return True
    # Remove existing replies
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


# ============================================================
# BLOQUE A: Renumeración de tablas
# ============================================================
#
# Plan: la única tabla desordenada es "Tabla 6" en pos 641 (cap 6.2.3).
# Las demás ya están en orden 2-5. El problema: falta Tabla 1.
# Solución: renumerar todas secuencialmente.
#
# Tabla 6 → Tabla 1
# Tabla 2 → Tabla 2 (keep)
# Tabla 3 → Tabla 3 (keep)
# Tabla 4 → Tabla 4 (keep)
# Tabla 5 → Tabla 5 (keep)

TABLE_RENUMBER = [
    # (old_prefix, new_prefix)
    ("Tabla 6: Gasto público adicional para convergencia hacia niveles internacionales",
     "Tabla 1: Gasto público adicional para convergencia hacia niveles internacionales"),
]

# ============================================================
# BLOQUE B: Reply updates Resumen Ejecutivo
# ============================================================

COMMENT_REPLY_UPDATES = [
    # (comment_id, new_reply)
    (
        "28",
        "Aceptado. Se agregará una columna o nota al margen en el cuadro de mensajes clave indicando el capítulo y sección donde se desarrolla cada tema, para facilitar la navegación del lector.",
    ),
    (
        "29",  # jargon retail — primer comentario sobre esto
        "Aceptado. Se revisa el uso de 'canal retail' en el Resumen Ejecutivo: se privilegia 'farmacias privadas' como denominación principal, dejando 'canal retail' entre paréntesis cuando corresponda por rigor técnico (sólo primera mención en cada capítulo). En el cuerpo analítico se mantiene 'canal retail' por ser el concepto formal del System of Health Accounts.",
    ),
    (
        "31",  # Carla 9 — alto costo
        "Sí, incluye alto costo. El tope anual del Beneficio Farmacéutico Ambulatorio aplica indistintamente a medicamentos de bajo costo con consumo repetido (crónicos) y a medicamentos de alto costo ambulatorios. El diseño es orientado al gasto acumulado por persona u hogar, no al tipo de medicamento: una vez alcanzado el cap, la protección se activa con independencia del canal o del precio unitario del fármaco.",
    ),
    (
        "39",  # Eduardo 37 "y coordinada" — cambiar a ACEPTADO
        "Aceptado. Se acepta la sugerencia de Eduardo, manteniendo 'simultánea y coordinadamente' como estaba en el texto. La observación confirma la redacción actual.",
    ),
    (
        "40",  # Eduardo 27 párrafo efectividad
        "Aceptado. Se incorpora el párrafo propuesto por Eduardo sobre la efectividad conjunta de los instrumentos en el Resumen Ejecutivo; refuerza el argumento central del informe sobre la necesidad de un paquete coordinado de políticas.",
    ),
    (
        "42",  # Carla 15 FONASA MLE/MAI — ya tiene buena respuesta, la mejoro
        "En FONASA, el Beneficio Farmacéutico Ambulatorio aplicaría tanto a la Modalidad de Atención Institucional (MAI) como a la Modalidad de Libre Elección (MLE), con una misma canasta y reglas de copago comunes. La trazabilidad se apoya en el RUT del beneficiario: tanto las prescripciones electrónicas como las dispensaciones quedan asociadas al RUT, lo que permite acumular el gasto sujeto al tope con independencia del canal utilizado. La diferencia operativa está en el punto de dispensación, no en la cobertura o en los copagos.",
    ),
    (
        "37",  # Carla 12 GES alto costo
        "Aceptado y matizado. La observación es correcta: GES sí cubre medicamentos de alto costo para varios problemas de salud garantizados (por ejemplo, el DS 22/2025 incorporó elexacaftor/tezacaftor/ivacaftor para fibrosis quística). El informe corrige esta precisión en el diagnóstico: GES, Ley Ricarte Soto, DAC y Fondo de Farmacia cubren de manera conjunta una parte importante de los medicamentos, incluyendo segmentos de alto costo. La propuesta del Beneficio Farmacéutico Ambulatorio Universal está dirigida específicamente a los medicamentos que quedan fuera de estos regímenes especiales, manteniéndolos intactos como piso de cobertura. Se ajusta la redacción para evitar sugerir que el sistema chileno carece de mecanismos de cobertura; los tiene y son relevantes, pero dejan un segmento sin cobertura sistemática que es el foco de la propuesta.",
    ),
]


def process_docx():
    if V33.exists():
        V33.unlink()
    shutil.copy(V32, V33)
    print(f"Copied: {V32.name} -> {V33.name}")

    log = []

    with zipfile.ZipFile(V33, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    # === BLOQUE A: Renumeración ===
    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))

    for old_prefix, new_prefix in TABLE_RENUMBER:
        for p in body.findall(qn("p")):
            text = get_para_text(p)
            if text.strip().startswith(old_prefix[:30]):
                # Replace the full paragraph (label + caption) with the new label
                # We need to keep the rest of the caption, just renumber
                full_text = text.strip()
                # Replace only "Tabla 6" → "Tabla 1"
                if "Tabla 6" in full_text:
                    new_text = full_text.replace("Tabla 6", "Tabla 1", 1)
                    replace_paragraph_content_tracked(p, new_text)
                    log.append(("OK", f"Renumerar: {old_prefix[:50]}...", f"-> {new_prefix[:50]}..."))
                    break
        else:
            continue

    # === BLOQUE B: Comment reply updates ===
    com_tree = etree.fromstring(com_xml)
    comments = com_tree.findall(qn("comment"))

    for cid, new_reply in COMMENT_REPLY_UPDATES:
        c = next((cc for cc in comments if cc.get(qn("id")) == cid), None)
        if c is None:
            log.append(("NOT FOUND", f"reply id={cid}", ""))
            continue
        author = c.get(qn("author"))
        p0_text = "".join(t.text or "" for t in c.find(qn("p")).iter(qn("t")))[:60] if c.find(qn("p")) is not None else ""
        if replace_comment_reply(c, new_reply):
            log.append(("OK", f"reply id={cid} ({author[:15]})", p0_text))
        else:
            log.append(("FAIL", f"reply id={cid}", ""))

    # === Write back ===
    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V33, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V33)

    return log


def main():
    log = process_docx()
    print("\n=== v3.3: Renumeración + feedback Resumen Ejecutivo ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:55s}  {detail[:80]}")
    print(f"\nOutput: {V33}")
    print(f"Size: {V33.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
