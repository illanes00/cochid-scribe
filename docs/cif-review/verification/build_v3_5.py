"""Build v3.5: feedback del Capítulo 1.

1. CIF 2 (id=45): ampliar desarrollo del problema de patologías complejas (cáncer, enfermedades
   genéticas/autoinmunes), judicialización como vía de acceso (recurso de protección, demoras,
   agravamiento clínico en la espera). Incorporar dimensión humana.
   → Cambiar reply a aceptado completo + agregar párrafo al Cap 1.1 con el desarrollo.

2. Carla 19 (id=47): "Por qué sólo Ricarte Soto?" — no centrar solo en LRS, mencionar GES, DAC,
   FOFAR como parte del conjunto.
   → Mejorar reply con aclaración y ajustar el párrafo donde aparece la mención para ampliar el
   set de regímenes.

3. Eduardo 43 (id=46): precios accesibles → reducciones precio efectivo. ✅ ya aceptado.
4. Eduardo 44 (id=48): sostienen el → explican fracción. ✅ ya aceptado.
5. Eduardo 45 (id=49): cotidiano → persistente. ✅ ya aceptado.

Además: simplificar replies largos de Eduardo 43/44/45 a formato conciso ("Aceptado.") ya que
son cambios de wording puntuales. Mantener breve explicación.

Input:  informe-final-v3.4.docx
Output: informe-final-v3.5.docx
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V34 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.4.docx")
V35 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.5.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_id = 700000


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


def make_inserted_paragraph_like(text, reference_p):
    new_p = etree.Element(qn("p"))
    ref_pPr = reference_p.find(qn("pPr"))
    if ref_pPr is not None:
        pPr = deepcopy(ref_pPr)
        # Remove any heading style — we want body
        for pStyle in pPr.findall(qn("pStyle")):
            val = pStyle.get(qn("val"))
            if val and val.startswith("Heading"):
                pPr.remove(pStyle)
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


def replace_comment_reply(comment_elem, new_reply_text):
    paragraphs = comment_elem.findall(qn("p"))
    if len(paragraphs) < 2:
        new_p = etree.SubElement(comment_elem, qn("p"))
        if paragraphs:
            src_pPr = paragraphs[0].find(qn("pPr"))
            if src_pPr is not None:
                new_p.insert(0, deepcopy(src_pPr))
    else:
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
# Content: nuevo párrafo sobre dimensión humana + judicialización
# ============================================================

# Este párrafo se inserta después del primer párrafo de 1.1 o en un lugar adecuado del Cap 1
# Ancla: buscamos un párrafo en el Cap 1 que hable de "frentes" o "lógicas distintas"
NUEVO_PARRAFO_PATOLOGIAS = (
    "La dimensión humana de estas brechas no se limita al gasto acumulado. En patologías "
    "complejas y de alto costo, como cánceres avanzados, enfermedades genéticas raras, "
    "patologías autoinmunes graves o enfermedades neurodegenerativas, la ausencia de cobertura "
    "explícita se traduce en trayectorias de acceso marcadas por la incertidumbre. Cuando el "
    "medicamento requerido no está incluido en GES, Ley Ricarte Soto, DAC ni Fondo de Farmacia, "
    "pacientes y familias recurren a vías extraordinarias: financiamiento por colectas, "
    "endeudamiento, o acciones judiciales (recursos de protección ante Cortes de Apelaciones y "
    "Corte Suprema). Estas vías tienen costos económicos, emocionales y de tiempo: la "
    "tramitación de un recurso de protección puede tomar semanas o meses, plazo durante el cual "
    "la enfermedad puede progresar y reducir la ventana terapéutica útil. La judicialización, "
    "por tanto, no es solo un fenómeno administrativo: es un síntoma estructural de insuficiencia "
    "del beneficio explícito, que traslada a los tribunales decisiones que deberían resolverse "
    "por mecanismos formales de priorización."
)

# Buscar ancla: en el Cap 1 hay un párrafo que menciona "dos frentes con lógicas distintas"
ANCHOR_PREFIX = "El problema se compone de dos frentes con lógicas distintas"


# Nuevos replies
REPLIES = {
    "45": (  # CIF 2 — patologías complejas
        "Aceptado. Se amplía el desarrollo del frente de alto costo y patologías complejas en el "
        "Capítulo 1 (sección 1.1), incorporando: (i) tipología clínica explícita (oncológicas, genéticas "
        "raras, autoinmunes, neurodegenerativas); (ii) dimensión humana de la exclusión (trayectorias "
        "de acceso marcadas por recursos de protección, demoras judiciales, agravamiento clínico en la "
        "espera); (iii) articulación con la judicialización como síntoma estructural. Se agrega párrafo "
        "nuevo y se reenmarcan referencias dispersas al problema."
    ),
    "47": (  # Carla 19 — no solo Ricarte Soto
        "Aceptado. El texto se amplía para incluir explícitamente que los regímenes de cobertura de alto "
        "costo en Chile son un conjunto: GES, Ley Ricarte Soto, Diagnóstico de Alto Costo (DAC) y Fondo "
        "de Farmacia (FOFAR). LRS se menciona como ejemplo paradigmático de alto costo y baja prevalencia, "
        "pero no es el único instrumento. Se ajusta la redacción para evitar sugerir que LRS es sinónimo "
        "de cobertura de alto costo en Chile."
    ),
    "46": "Aceptado.",  # Eduardo 43
    "48": "Aceptado.",  # Eduardo 44
    "49": "Aceptado.",  # Eduardo 45
}


def process_docx():
    if V35.exists():
        V35.unlink()
    shutil.copy(V34, V35)
    print(f"Copied: {V34.name} -> {V35.name}")

    log = []

    with zipfile.ZipFile(V35, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    # === 1. Insert new paragraph in Cap 1 ===
    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))

    anchor_p = None
    anchor_idx = None
    for i, p in enumerate(body.findall(qn("p"))):
        text = get_para_text(p)
        if ANCHOR_PREFIX in text:
            anchor_p = p
            anchor_idx = i
            break

    if anchor_p is not None:
        new_p = make_inserted_paragraph_like(NUEVO_PARRAFO_PATOLOGIAS, anchor_p)
        anchor_p.addnext(new_p)
        log.append(("OK", "Cap 1: párrafo patologías complejas + dimensión humana", f"after para {anchor_idx}"))
    else:
        log.append(("NOT FOUND", "Cap 1: anchor 'dos frentes con lógicas distintas'", ""))

    # === 2. Update comment replies ===
    com_tree = etree.fromstring(com_xml)
    comments = com_tree.findall(qn("comment"))

    for cid, new_reply in REPLIES.items():
        c = next((cc for cc in comments if cc.get(qn("id")) == cid), None)
        if c is None:
            log.append(("NOT FOUND", f"reply id={cid}", ""))
            continue
        if replace_comment_reply(c, new_reply):
            author = c.get(qn("author"))
            p0 = c.find(qn("p"))
            p0_text = "".join(t.text or "" for t in p0.iter(qn("t")))[:50] if p0 is not None else ""
            log.append(("OK", f"reply id={cid} ({author[:15]})", p0_text))

    # Write back
    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V35, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V35)

    return log


def main():
    log = process_docx()
    print("\n=== v3.5: Feedback Capítulo 1 ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:55s}  {detail[:80]}")
    print(f"\nOutput: {V35}")
    print(f"Size: {V35.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
