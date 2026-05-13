"""Build v2 of the reviewed docx — as TRACKED CHANGES (suggestions).

Starts from informe-final-revisado.docx (v1 with 91 comments + replies from 17 abr,
plus 86 ins + 100 del already applied by Corrector and Eduardo).

All new edits go as w:ins (insertions) and w:del (deletions) with author
"Martín Illanes" so Google Docs imports them as suggestions and the user
can toggle "see with changes" / "see without changes".

Edits applied:
- Tracked-change cleanup of 14 broken fragments (dobles artículos, duplicaciones, typos).
- Editorial reframing of Mensaje clave #4, Resumen Ejecutivo (6 blocks), Cap 7 title/intro.
- Softening "En este informe se recomienda la Alternativa C" in 7.3.1.
- Completing the truncated first paragraph of Cap 8.
- Reframing Cap 8 final paragraph.
- Adding new 7.13 "Síntesis y remisión al debate".
- Adding new 8.4 "Preguntas para la discusión" with 8 fundamented questions.
- Adding methodological footnote on the 71% OOP figure.

Output: informe-final-v2.docx
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from copy import deepcopy

from lxml import etree

V1 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-gdoc-snapshot.docx")
V2 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v2.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

# Counter for unique revision IDs (starting high to avoid collisions)
_next_id = 90000


def next_id() -> str:
    global _next_id
    _next_id += 1
    return str(_next_id)


def qn(tag: str) -> str:
    """Build a fully-qualified w:* tag."""
    return f"{{{W_NS}}}{tag}"


# ============================================================================
# XML HELPERS FOR TRACKED CHANGES
# ============================================================================

def make_ins_run(text: str) -> etree._Element:
    """Create a <w:ins> element wrapping a run with the given text."""
    ins = etree.Element(qn("ins"))
    ins.set(qn("id"), next_id())
    ins.set(qn("author"), AUTHOR)
    ins.set(qn("date"), DATE)

    r = etree.SubElement(ins, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return ins


def make_del_wrapper_from_run(run_elem: etree._Element) -> etree._Element:
    """Wrap an existing <w:r> inside a <w:del> and convert its <w:t> to <w:delText>."""
    # Clone the run
    r_copy = deepcopy(run_elem)
    # Convert all w:t to w:delText
    for t_elem in r_copy.findall(qn("t")):
        t_elem.tag = qn("delText")

    del_elem = etree.Element(qn("del"))
    del_elem.set(qn("id"), next_id())
    del_elem.set(qn("author"), AUTHOR)
    del_elem.set(qn("date"), DATE)
    del_elem.append(r_copy)
    return del_elem


def _is_inside_del(elem: etree._Element) -> bool:
    """Check if an element has a <w:del> ancestor (up to w:p)."""
    parent = elem.getparent()
    while parent is not None and parent.tag != qn("p"):
        if parent.tag == qn("del"):
            return True
        parent = parent.getparent()
    return False


def get_para_text(p: etree._Element) -> str:
    """Get the visible text of a <w:p>, ignoring deleted text.
    Also includes <w:tab/> as a tab character so prefix matching works.
    """
    parts = []
    # Walk through all descendants in doc order
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


def get_para_text_normalized(p: etree._Element) -> str:
    """Get paragraph text with tabs normalized to single space for matching."""
    text = get_para_text(p)
    # Replace multiple whitespace chars with single space
    import re
    return re.sub(r'\s+', ' ', text).strip()


def find_paragraph_by_prefix(body: etree._Element, prefix: str, start_index: int = 0):
    """Find first <w:p> whose visible text starts with prefix.
    Uses normalized whitespace matching (tabs -> spaces) for robustness.
    """
    import re
    norm_prefix = re.sub(r'\s+', ' ', prefix).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        text = get_para_text_normalized(p)
        if text.startswith(norm_prefix):
            return i, p
    return None, None


def find_paragraph_contains(body: etree._Element, needle: str, start_index: int = 0):
    """Find first <w:p> whose visible text contains needle."""
    import re
    norm_needle = re.sub(r'\s+', ' ', needle).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        text = get_para_text_normalized(p)
        if norm_needle in text:
            return i, p
    return None, None


def replace_paragraph_content_tracked(p: etree._Element, new_text: str) -> None:
    """Replace a paragraph's content with tracked changes:
    - wrap existing runs in <w:del> (convert w:t to w:delText)
    - append a new <w:ins> with the new text

    Keeps <w:pPr> (paragraph properties) intact.
    """
    # Save pPr
    pPr = p.find(qn("pPr"))

    # Collect all direct children that are NOT pPr
    # We'll wrap them in a <w:del>
    content_children = []
    for child in list(p):
        if child.tag == qn("pPr"):
            continue
        content_children.append(child)

    # Remove them from p
    for child in content_children:
        p.remove(child)

    # For each existing run-like element, wrap in <w:del>.
    # Non-run elements (hyperlinks, etc) — we wrap as best we can.
    # Simplest: if it's a <w:r>, convert to <w:delText> and wrap in <w:del>.
    # Other elements (links, smartTag): keep as-is wrapped in <w:del> for simplicity.
    for child in content_children:
        if child.tag == qn("r"):
            # Convert <w:t> to <w:delText>
            for t_elem in child.findall(qn("t")):
                t_elem.tag = qn("delText")
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_id())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)
        else:
            # Wrap whole thing in <w:del>
            del_elem = etree.SubElement(p, qn("del"))
            del_elem.set(qn("id"), next_id())
            del_elem.set(qn("author"), AUTHOR)
            del_elem.set(qn("date"), DATE)
            del_elem.append(child)

    # Append new <w:ins> with new text
    ins = make_ins_run(new_text)
    p.append(ins)


def replace_inline_text_tracked(p: etree._Element, old: str, new: str) -> bool:
    """Replace an inline substring within paragraph text using tracked changes.
    Since runs may be fragmented (especially after prior tracked changes),
    we match on normalized text and replace the full paragraph content.
    """
    import re
    text = get_para_text(p)
    norm_text = re.sub(r'\s+', ' ', text).strip()
    norm_old = re.sub(r'\s+', ' ', old).strip()

    if norm_old not in norm_text:
        return False

    # Build new text by replacing in normalized space
    new_full = norm_text.replace(norm_old, new)
    replace_paragraph_content_tracked(p, new_full)
    return True


def make_new_paragraph_tracked(text: str, style_from: etree._Element | None = None,
                                is_heading: bool = False) -> etree._Element:
    """Create a new paragraph marked as inserted (all content wrapped in <w:ins>),
    and with <w:pPr><w:rPr><w:ins .../></w:rPr></w:pPr> to mark the paragraph itself
    as inserted.
    """
    p = etree.Element(qn("p"))

    # pPr with insertion mark
    pPr = etree.SubElement(p, qn("pPr"))

    if is_heading:
        # Apply Heading 2 style
        pStyle = etree.SubElement(pPr, qn("pStyle"))
        pStyle.set(qn("val"), "Heading2")
    elif style_from is not None:
        # Copy pStyle if present
        src_pPr = style_from.find(qn("pPr"))
        if src_pPr is not None:
            src_pStyle = src_pPr.find(qn("pStyle"))
            if src_pStyle is not None:
                pStyle = etree.SubElement(pPr, qn("pStyle"))
                pStyle.set(qn("val"), src_pStyle.get(qn("val"), ""))

    # Mark paragraph itself as inserted (ins in rPr of pPr)
    rPr = etree.SubElement(pPr, qn("rPr"))
    ins_mark = etree.SubElement(rPr, qn("ins"))
    ins_mark.set(qn("id"), next_id())
    ins_mark.set(qn("author"), AUTHOR)
    ins_mark.set(qn("date"), DATE)

    # Insert content wrapped in w:ins
    ins = make_ins_run(text)
    p.append(ins)

    return p


# ============================================================================
# EDITS — SPEC
# ============================================================================

# Each edit is a dict with:
#   op: "replace_paragraph" | "replace_inline" | "insert_after"
#   find: dict with mode ("prefix" | "contains") and value
#   new: new text
#   name: label for logging

EDITS = [
    # =============== CLEANUPS reales (inline replace) ===============
    # Fix typo "problemá" -> "problemática"
    {"op": "inline", "find": "analiza el problemá de acceso", "new": "analiza la problemática de acceso", "name": "limpieza: 'problemá' typo"},

    # =============== MENSAJES CLAVE ===============
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Recomendación: avanzar hacia un escenario intermedio",
        "new": (
            "Una opción priorizada para la discusión de política es un escenario intermedio de convergencia OCDE, "
            "cuyo eje estructural sería un Beneficio Farmacéutico Ambulatorio Universal (para beneficiarios de "
            "FONASA e ISAPRE bajo reglas comunes), con lista positiva, copagos y topes anuales, y mecanismos de "
            "pago/dispensación consistentes con sostenibilidad y gestión de precios. El Capítulo 7 desarrolla "
            "esta opción en detalle como insumo para el debate, sin zanjar preferencias entre los escenarios analizados."
        ),
        "name": "MK#4 reframing",
    },

    # =============== RESUMEN EJECUTIVO ===============
    # RE-intro: se aplica DESPUÉS del cleanup de "problemá" → buscamos el prefix YA CORREGIDO
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Este informe analiza la problemática de acceso",
        "new": (
            "Este informe analiza la problemática de acceso y protección financiera frente a medicamentos en Chile, "
            "con foco en su inclusión sostenible en los planes de salud. Pese a avances relevantes en coberturas "
            "explícitas y mecanismos de compra pública, el país mantiene una exposición financiera elevada para los "
            "hogares, particularmente en el canal de medicamentos dispensados fuera del hospital. La experiencia "
            "internacional comparada muestra que reducir de manera sostenible el gasto de bolsillo en medicamentos "
            "no depende de una sola medida, sino de un paquete de políticas que articula (i) una canasta explícita "
            "(beneficio), (ii) reglas de copagos y protección financiera (incluyendo topes), y (iii) un modelo de "
            "provisión, dispensación y pago que permita la continuidad de tratamiento y el control de costos."
        ),
        "name": "RE-intro reescritura (post-cleanup)",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Recomendación: Beneficio Farmacéutico Ambulatorio Universal (escenario intermedio)",
        "new": "Una opción priorizada para la discusión: Beneficio Farmacéutico Ambulatorio Universal (escenario intermedio)",
        "name": "RE-recom título",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "El informe recomienda avanzar hacia un escenario intermedio de convergencia OCDE, cuyo cambio estructural",
        "new": (
            "Entre los tres escenarios analizados, este informe desarrolla en detalle el escenario intermedio de "
            "convergencia OCDE como base para la discusión de política. Su eje estructural sería la creación de un "
            "Beneficio Farmacéutico Ambulatorio Universal, aplicable a beneficiarios de FONASA e ISAPRE bajo reglas "
            "comunes. Sus componentes centrales se detallan en el Capítulo 7 e incluyen:"
        ),
        "name": "RE-recom cuerpo",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "En síntesis, el informe propone pasar desde una cobertura fragmentada",
        "new": (
            "En síntesis, el informe plantea como eje de discusión la transición desde una cobertura fragmentada "
            "hacia un modelo con reglas explícitas, protección financiera verificable y un beneficio farmacéutico "
            "ambulatorio universal. Los tres escenarios analizados entregan un marco para que actores públicos, "
            "privados y ciudadanos ponderen los trade-offs entre protección financiera, viabilidad administrativa "
            "y esfuerzo fiscal. Este documento es un insumo para esa discusión y no pretende zanjar preferencias "
            "entre opciones de política."
        ),
        "name": "RE-cierre",
    },

    # =============== CAP 7 ===============
    {
        "op": "replace_paragraph",
        "find_mode": "contains",
        "find_value": "Seguro Universal con tope de gasto ambulatorio en medicamentos",
        "new": "7.\tDesarrollo del Escenario 2: Beneficio Farmacéutico Ambulatorio Universal",
        "name": "Cap7 título",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "La propuesta se estructura como un Beneficio Farmacéutico Ambulatorio Universal",
        "new": (
            "Este capítulo desarrolla en detalle el Escenario 2 presentado en la Sección 6 (convergencia intermedia "
            "OCDE) como insumo analítico para el debate de política. El análisis detallado se concentra en este "
            "escenario por tres razones: (i) su magnitud fiscal (0,7-0,75% del PIB) cae en un rango políticamente "
            "tractable; (ii) cuenta con experiencia internacional documentada en el cluster OCDE intermedio "
            "(España, Países Bajos, Reino Unido, Canadá); y (iii) concentra las decisiones de diseño más informativas "
            "para iluminar también los Escenarios 1 y 3. No constituye una prescripción: los escenarios 1 y 3 son "
            "alternativas válidas con trade-offs distintos, descritos en el capítulo anterior. El escenario se "
            "estructura como un Beneficio Farmacéutico Ambulatorio Universal bajo reglas comunes —aplicable a "
            "FONASA y a las ISAPRE, como piso de protección— con canasta explícita, copagos protegidos y un tope "
            "(cap) de gasto. Operaría de manera híbrida entre provisión institucional y canal retail (farmacias "
            "privadas), y se articularía con compras, regulación de precios y sistemas de información interoperables, "
            "con el fin de mejorar acceso, continuidad y sostenibilidad."
        ),
        "name": "Cap7 intro",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Los objetivos del seguro universal con tope de gasto son:",
        "new": "Los objetivos del beneficio farmacéutico ambulatorio universal son:",
        "name": "Cap7.1 intro (beneficio vs seguro)",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Propuesta de diseño: seguro universal con tope de gasto.",
        "new": "Diseño del beneficio: componentes operacionales.",
        "name": "Cap7.3 header",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Se propone estructurar el beneficio como un seguro universal de medicamentos ambulatorios",
        "new": (
            "El beneficio se estructura como un esquema universal de medicamentos ambulatorios con los siguientes "
            "componentes:"
        ),
        "name": "Cap7.3 cuerpo",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "En este informe se recomienda la Alternativa C",
        "new": (
            "Este capítulo desarrolla en detalle la Alternativa C (híbrida), porque aborda simultáneamente los dos "
            "motores del gasto de bolsillo: (i) brechas de canasta y cobertura ambulatoria, y (ii) brechas de "
            "acceso efectivo por fallas de dispensación y transición forzada a retail. Las alternativas A y B se "
            "describen como opciones contrastables para el debate."
        ),
        "name": "Cap7.3.1 suavizar 'recomienda'",
    },

    # =============== CAP 8 ===============
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Este informe sostiene que la brecha de protección financiera en medicamentos no puede resolverse",
        "new": (
            "Este capítulo cierra el documento recogiendo los principales hallazgos del análisis y planteando las "
            "preguntas que el seminario de discusión busca ordenar. El diagnóstico muestra que el gasto de bolsillo "
            "en medicamentos —especialmente en el segmento ambulatorio adquirido en farmacias— responde a una "
            "combinación de brechas de canasta y cobertura, estructura de copagos, precios y fallas de dispensación. "
            "En consecuencia, resolver la brecha de protección financiera requiere actuar simultáneamente sobre esas "
            "cuatro dimensiones, articuladas dentro de una arquitectura común aplicable a FONASA e ISAPRE."
        ),
        "name": "Cap8 párrafo 1 (completado)",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "La conclusión principal es que Chile requiere transitar",
        "new": (
            "Una conclusión central del análisis es que transitar desde un conjunto de instrumentos fragmentados hacia "
            "un beneficio farmacéutico ambulatorio integrado, con reglas comunes aplicables como piso para FONASA e "
            "ISAPRE, ofrece la mayor tracción para reducir el gasto de bolsillo de forma sostenida. La fragmentación "
            "actual genera resultados heterogéneos: para una parte de la población, la cobertura depende del plan, "
            "de la modalidad de atención o del canal de compra; para otra, depende de la disponibilidad efectiva del "
            "arsenal y del stock. Un beneficio integrado permite actuar simultáneamente sobre las fuentes predominantes "
            "del gasto de bolsillo, evitando que la protección financiera se reduzca a un parche en un punto del "
            "sistema mientras el problema se reproduce en otro."
        ),
        "name": "Cap8 párrafo 2 (una conclusión vs la conclusión)",
    },
    {
        "op": "replace_paragraph",
        "find_mode": "prefix",
        "find_value": "Finalmente, a partir de los escenarios desarrollados, la trayectoria recomendada",
        "new": (
            "Finalmente, entre los escenarios desarrollados, la trayectoria de convergencia intermedia se destaca "
            "como una opción analíticamente rica para el debate: combina un potencial significativo de reducción "
            "del gasto de bolsillo con exigencias institucionales y fiscales abordables, siempre que se fortalezcan "
            "de manera coordinada los habilitantes críticos (precios, compras, datos interoperables y fiscalización). "
            "Los escenarios 1 y 3 representan rutas alternativas con trade-offs distintos, cuya elección depende de "
            "preferencias sociales y políticas que este informe no pretende zanjar."
        ),
        "name": "Cap8 último párrafo",
    },
]


# New paragraphs to insert (after a specific anchor)
NEW_PARAGRAPHS = [
    # ---- Cap 7.13 ----
    {
        "anchor_mode": "contains",
        "anchor": "Conclusiones y recomendaciones",
        "position": "before",  # insert before Cap 8
        "paragraphs": [
            {"text": "7.13\tSíntesis y remisión al debate", "style": "Heading2"},
            {"text": (
                "El desarrollo detallado de este escenario permite evaluar su viabilidad técnica, sus requerimientos "
                "institucionales y sus implicancias fiscales y distributivas. Lo desarrollado en este capítulo no "
                "agota el espacio de diseño: los escenarios 1 y 3 son alternativas válidas cuyo análisis cuantitativo "
                "se presenta en el Capítulo 6 y en el Anexo 4."
            ), "style": None},
            {"text": (
                "La decisión entre escenarios no es principalmente técnica. Depende de preferencias sociales sobre "
                "tres dimensiones: (i) protección financiera frente a esfuerzo fiscal, (ii) universalidad frente a "
                "focalización, y (iii) gradualidad frente a profundidad de la reforma. Estas preferencias son las "
                "que el seminario de discusión busca explicitar. El Capítulo 8 cierra con preguntas abiertas que "
                "ordenan ese debate."
            ), "style": None},
        ],
        "name": "Cap7.13 nueva",
    },
    # ---- Cap 8.4 ----
    {
        "anchor_mode": "prefix",
        "anchor": "Bibliografía",
        "position": "before",
        "paragraphs": [
            {"text": "8.4\tPreguntas para la discusión", "style": "Heading2"},
            {"text": (
                "Para ordenar el debate del seminario, este informe cierra con ocho preguntas abiertas. Cada pregunta "
                "se deriva de una tensión que el informe identificó pero no zanjó; su resolución depende de preferencias "
                "sociales y decisiones políticas que exceden el alcance de este documento."
            ), "style": None},
            {"text": "1. Viabilidad política. ¿Qué combinación de protección financiera, esfuerzo fiscal y gradualidad resulta políticamente viable en Chile hoy, considerando los tres escenarios analizados (0,6%, 0,7-0,75% y 1,4% del PIB)?", "style": None},
            {"text": "2. Arquitectura FONASA/ISAPRE. ¿Debe el beneficio aplicar como piso común a FONASA e ISAPRE desde el inicio, o avanzar primero en FONASA con convergencia progresiva hacia ISAPRE?", "style": None},
            {"text": "3. Rol del HTA/ETESA. ¿Qué rol debe jugar el HTA/ETESA en la priorización de inclusiones, y qué capacidades institucionales se requieren para que sea vinculante?", "style": None},
            {"text": "4. Modalidad de dispensación. ¿Qué modalidad de dispensación (institucional, POS en retail, reembolso, híbrida) protege mejor a los grupos vulnerables sin erosionar la continuidad terapéutica?", "style": None},
            {"text": "5. Innovación y sostenibilidad. ¿Cómo se aborda la tensión entre incentivos a la innovación farmacéutica y sostenibilidad del gasto público, considerando los acuerdos de acceso gestionado y la revisión por HTA?", "style": None},
            {"text": "6. Judicialización. ¿Qué rol debe jugar la judicialización en un sistema con reglas explícitas de inclusión, y cómo se evita que reemplace al mecanismo formal de priorización?", "style": None},
            {"text": "7. Transparencia y legitimidad. ¿Qué mecanismos de transparencia, monitoreo y rendición de cuentas son necesarios para sostener la legitimidad social del beneficio, siguiendo experiencias como AMNOG (Alemania) o NICE (Reino Unido)?", "style": None},
            {"text": "8. Integración con reformas estructurales. ¿Cómo se integra este beneficio con las reformas estructurales en discusión (seguro único, modernización del GES, reforma de ISAPRE), y qué secuenciamiento resulta más viable?", "style": None},
        ],
        "name": "Cap8.4 nueva (8 preguntas)",
    },
    # ---- Nota metodológica del 71% ----
    {
        "anchor_mode": "contains",
        "anchor": "los hogares financiaron 71% del gasto en fármacos",
        "position": "after",
        "paragraphs": [
            {"text": (
                "Nota metodológica. La cifra del 71% corresponde a un cálculo propio elaborado sobre la IX Encuesta "
                "de Presupuestos Familiares (EPF, 2022-2023; INE, 2023) y datos de gasto público en el canal retail "
                "farmacéutico (CENABAST y FONASA). Estudios recientes con metodologías alternativas reportan cifras "
                "consistentes: la Cámara de Innovación Farmacéutica (CIF, 2025) estima que el 80% del gasto retail "
                "en medicamentos es de bolsillo y que el 62% del gasto total en medicamentos lo asumen los hogares; "
                "la OCDE (Health at a Glance, 2023) reporta 78% de gasto de bolsillo sobre el gasto farmacéutico "
                "total en Chile para 2021 (frente a 39% promedio OCDE). Las diferencias entre cifras corresponden "
                "principalmente a los denominadores considerados (retail frente a total), los años de referencia y "
                "los tratamientos de los subsidios públicos al canal privado. La magnitud del orden (70-80%) es "
                "estable entre fuentes."
            ), "style": None},
        ],
        "name": "Nota metodológica 71%",
    },
]


# ============================================================================
# MAIN LOGIC
# ============================================================================

def process_docx():
    # Copy v1 to v2
    if V2.exists():
        V2.unlink()
    shutil.copy(V1, V2)
    print(f"Copied: {V1.name} -> {V2.name}")

    # Read document.xml from the zip
    import io
    with zipfile.ZipFile(V2, "r") as z:
        doc_xml_bytes = z.read("word/document.xml")

    # Parse
    tree = etree.fromstring(doc_xml_bytes)
    body = tree.find(qn("body"))

    log = []

    # Apply inline edits first (cleanups)
    cleanup_hits = 0
    for edit in EDITS:
        if edit["op"] == "inline":
            # Find any paragraph containing the old string
            done = False
            for p in body.findall(qn("p")):
                text = get_para_text(p)
                if edit["find"] in text:
                    if replace_inline_text_tracked(p, edit["find"], edit["new"]):
                        cleanup_hits += 1
                        log.append(("OK", edit["name"], "inline"))
                        done = True
                        break
            if not done:
                log.append(("NOT FOUND", edit["name"], "inline"))

    # Apply paragraph-level replaces
    for edit in EDITS:
        if edit["op"] != "replace_paragraph":
            continue
        if edit["find_mode"] == "prefix":
            i, p = find_paragraph_by_prefix(body, edit["find_value"])
        else:
            i, p = find_paragraph_contains(body, edit["find_value"])
        if p is not None:
            replace_paragraph_content_tracked(p, edit["new"])
            log.append(("OK", edit["name"], f"para {i}"))
        else:
            log.append(("NOT FOUND", edit["name"], f"looking for: {edit['find_value'][:50]}"))

    # Apply new paragraph insertions
    for new_block in NEW_PARAGRAPHS:
        if new_block["anchor_mode"] == "prefix":
            i, anchor_p = find_paragraph_by_prefix(body, new_block["anchor"])
        else:
            i, anchor_p = find_paragraph_contains(body, new_block["anchor"])
        if anchor_p is None:
            log.append(("NOT FOUND", new_block["name"], f"anchor: {new_block['anchor'][:50]}"))
            continue

        # Determine insertion point
        if new_block["position"] == "before":
            insert_index = list(body).index(anchor_p)
        else:  # after
            insert_index = list(body).index(anchor_p) + 1

        # Create new paragraphs in reverse so each is inserted at insert_index
        for para_spec in reversed(new_block["paragraphs"]):
            is_heading = para_spec.get("style") == "Heading2"
            new_p = make_new_paragraph_tracked(
                para_spec["text"],
                style_from=anchor_p,
                is_heading=is_heading,
            )
            body.insert(insert_index, new_p)
        log.append(("OK", new_block["name"], f"inserted at {insert_index} ({len(new_block['paragraphs'])} paras)"))

    # Serialize back
    new_doc_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    # Write back to docx
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V2, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V2)

    return log


def main():
    log = process_docx()
    print("\n=== EDICIONES APLICADAS ===")
    ok = sum(1 for s, _, _ in log if s == "OK")
    fail = sum(1 for s, _, _ in log if s != "OK")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:45s}  {detail}")
    print(f"\nTotal: {ok} OK, {fail} fail")
    print(f"Salida: {V2}")
    print(f"Tamaño: {V2.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
