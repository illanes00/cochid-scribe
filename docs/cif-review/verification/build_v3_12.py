"""Build v3.12: sistema de IDs trazables MI-NN para razonamientos Martín Illanes.

Agrega:
1. Comentarios nuevos en el texto del documento con autor "Martín Illanes" y prefix [MI-NN]
2. Revisa todos los replies previos de Martín para estandarizar formato con IDs
3. Re-ordena trazabilidad

Sistema de IDs:
- MI-01 a MI-99: comentarios/razonamientos nuevos de Martín en el texto
- Agrupados por capítulo/tema

Estructura de comentario [MI-NN]:
  "[MI-NN] <tema>: <razonamiento>. <acción propuesta>."

Input:  informe-final-v3.11.docx
Output: informe-final-v3.12.docx
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V311 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.11.docx")
V312 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.12.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_next_comment_id = 1000  # avoid collision with existing IDs
_next_rev_id = 1000000


def next_comment_id():
    global _next_comment_id
    _next_comment_id += 1
    return str(_next_comment_id)


def next_rev_id():
    global _next_rev_id
    _next_rev_id += 1
    return str(_next_rev_id)


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


def get_para_text_normalized(p):
    return re.sub(r"\s+", " ", get_para_text(p)).strip()


def find_paragraph_by_prefix(body, prefix, start_index=0):
    norm_prefix = re.sub(r"\s+", " ", prefix).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        if get_para_text_normalized(p).startswith(norm_prefix):
            return i, p
    return None, None


def find_paragraph_contains(body, needle, start_index=0):
    norm_needle = re.sub(r"\s+", " ", needle).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        if norm_needle in get_para_text_normalized(p):
            return i, p
    return None, None


# =============================================================================
# SISTEMA DE COMENTARIOS NUEVOS (MI-NN) anclados a texto
# =============================================================================
#
# Cada comentario tiene:
#   - id_code: "MI-NN" (Martín Illanes + número secuencial)
#   - anchor: {mode, value} para encontrar el párrafo
#   - body: texto del comentario (prefijado con [MI-NN])
#   - range_text: subtexto exacto a seleccionar dentro del párrafo (para anclaje Word)
#                 Si es None, ancla a todo el párrafo.
#
# Estos comentarios razonan sobre decisiones editoriales del autor, añadiendo
# trazabilidad al proceso.

NUEVOS_COMENTARIOS = [
    # --- Cap 2 / fragmentación y capa BFAU ---
    {
        "code": "MI-01",
        "anchor": {"mode": "contains", "value": "Beneficio Farmacéutico Ambulatorio Universal"},
        "range_text": None,
        "body": (
            "[MI-01] Arquitectura del BFAU como capa adicional. Decisión editorial: el BFAU no "
            "reemplaza los programas existentes (GES, LRS, DAC, FOFAR) sino que opera como una "
            "capa de continuidad que cubre los hoyos dejados por la fragmentación. Esto responde a "
            "la observación de Carla Castillo (DOCX142) sobre la subsistencia de la fragmentación "
            "y alinea con el principio de Eduardo (no sustituir sino complementar)."
        ),
    },
    # --- Cap 2 / sistema dual Estado ---
    {
        "code": "MI-02",
        "anchor": {"mode": "contains", "value": "financiamiento y ejecutores"},
        "range_text": None,
        "body": (
            "[MI-02] Estado dual: comprador directo + asegurador. El Estado chileno opera "
            "simultáneamente como (i) comprador directo vía programas propios (Servicios de Salud, "
            "PNI, Ricarte Soto, DAC) y (ii) asegurador obligatorio que recauda cotizaciones 7%. "
            "Esta distinción es metodológicamente relevante aunque el gasto agregado no separa "
            "ambas fuentes. Responde a Carla Castillo (DOCX40)."
        ),
    },
    # --- Cap 3 / judicialización ---
    {
        "code": "MI-03",
        "anchor": {"mode": "contains", "value": "judicialización"},
        "range_text": None,
        "body": (
            "[MI-03] Judicialización como síntoma estructural. El informe adopta deliberadamente "
            "el marco de Vargas-Pelaez et al. (2019): la judicialización no es un problema "
            "independiente sino el síntoma de la insuficiencia del beneficio explícito. Esto "
            "conecta con la propuesta del BFAU, que al proveer cobertura sistemática reduce la "
            "necesidad de recurrir a tribunales como vía de primer acceso. Responde a CIF "
            "(comentario original sept 2025) y a Carla Castillo (DOCX72, DOCX75)."
        ),
    },
    # --- Cap 4 / caveat EPF ---
    {
        "code": "MI-04",
        "anchor": {"mode": "contains", "value": "gasto de bolsillo en medicamentos"},
        "range_text": None,
        "body": (
            "[MI-04] Caveats metodológicos EPF. La EPF 2022 captura gasto de un mes de referencia, "
            "no un promedio anualizado. Subestima eventos de alto costo poco frecuentes y no "
            "captura hogares que obtuvieron medicamentos gratuitamente en APS. Esta limitación "
            "debe explicitarse al lector para evitar interpretaciones erróneas de los percentiles. "
            "Responde a Carla Castillo (DOCX88)."
        ),
    },
    # --- Cap 5 / retail vs institucional ---
    {
        "code": "MI-05",
        "anchor": {"mode": "contains", "value": "canal retail"},
        "range_text": None,
        "body": (
            "[MI-05] Foco retail es decisión analítica, no prescriptiva. El informe se concentra "
            "en el canal retail porque allí se materializa el 71% del gasto de bolsillo "
            "(HF3/HC51, OECD 2022). No implica que la dispensación institucional sea irrelevante; "
            "la expansión MAI/APS es vía complementaria que reduce gasto de bolsillo aumentando "
            "gasto público, con trade-offs logísticos distintos. El Escenario 2 permite ambos "
            "mix. Responde a Carla Castillo (DOCX101, DOCX145)."
        ),
    },
    # --- Cap 5 / biosimilares ---
    {
        "code": "MI-06",
        "anchor": {"mode": "contains", "value": "biosimilares"},
        "range_text": None,
        "body": (
            "[MI-06] Heterogeneidad regulatoria de biosimilares. El informe adopta un marco "
            "explícito reconociendo que EMA, FDA, MHRA y ANMAT tienen estándares distintos de "
            "intercambiabilidad. Una política chilena de sustitución debe definirse propia, no "
            "puede importar un estándar único. Refs: Kirchlechner & Cohen (2025). Responde a CIF-7."
        ),
    },
    # --- Cap 6 / diseño por canal ---
    {
        "code": "MI-07",
        "anchor": {"mode": "contains", "value": "escenarios alternativos"},
        "range_text": None,
        "body": (
            "[MI-07] Escenarios calibrados sobre protección financiera y costo fiscal total, no "
            "sobre mix específico entre canales. Los rangos fiscales de los Escenarios 1, 2 y 3 "
            "son compatibles con distintas combinaciones de ampliación institucional y cobertura "
            "retail. El informe no prescribe un mix operativo específico; esa es decisión de "
            "implementación. Responde a Carla Castillo (DOCX129, DOCX131, DOCX145)."
        ),
    },
    # --- Cap 7 / unidad del tope ---
    {
        "code": "MI-08",
        "anchor": {"mode": "contains", "value": "tope"},
        "range_text": None,
        "body": (
            "[MI-08] Unidad de acumulación del tope (cap/stop-loss). El diseño admite varias "
            "alternativas con distinta implicancia distributiva: (a) por persona (simple, usa RUT), "
            "(b) por hogar (vía Registro Social de Hogares, mayor protección a familias con "
            "múltiples enfermos crónicos), (c) por núcleo familiar cotizante, (d) vía sistema "
            "tributario como crédito. Recomendación del informe: opción por hogar como "
            "prioritaria, bajo el principio de que el hogar es la unidad económica que junta "
            "ingresos para financiar medicamentos. Responde a Carla Castillo (DOCX151)."
        ),
    },
    # --- Cap 7 / alcance del BFAU ---
    {
        "code": "MI-09",
        "anchor": {"mode": "contains", "value": "piso para lo ambulatorio"},
        "range_text": None,
        "body": (
            "[MI-09] Alcance del BFAU: ambulatorio con apertura a alto costo. El diseño original "
            "limita el BFAU al segmento ambulatorio no cubierto por GES/LRS/DAC/FOFAR. La "
            "observación de Carla Castillo (DOCX149) invita a considerar medicamentos de alto "
            "costo fuera de esos regímenes. Decisión: el BFAU opera primordialmente como piso "
            "ambulatorio, pero sin excluir alto costo ambulatorio cuando tenga evidencia ISP "
            "aprobada. Convergencia de regímenes en horizonte de tercera fase."
        ),
    },
    # --- Cap 7 / trasvasaje entre canales ---
    {
        "code": "MI-10",
        "anchor": {"mode": "contains", "value": "Riesgos de implementación"},
        "range_text": None,
        "body": (
            "[MI-10] Riesgo de trasvasaje institucional→retail. Si el beneficio retail mejora "
            "demasiado frente a la dispensación institucional, personas que hoy retiran en APS "
            "podrían migrar al retail generando gasto fiscal sin mejora sanitaria. Mitigaciones: "
            "copagos con incentivo relativo para el canal institucional, monitoreo "
            "administrativo, coordinación con ISAPRE para que el BFAU opere como piso (no "
            "sustituto). Responde a Carla Castillo (DOCX131)."
        ),
    },
    # --- Cap 8 / lo gratis sigue gratis ---
    {
        "code": "MI-11",
        "anchor": {"mode": "contains", "value": "lo gratis sigue"},
        "range_text": None,
        "body": (
            "[MI-11] Principio 'lo gratis sigue gratis'. El BFAU no quita beneficios actuales (APS "
            "arsenal, GES tramo A/B). Agrega una capa focalizada por exposición al gasto, no "
            "homogeneiza canastas universalmente. Para afiliados ISAPRE: accede al subsidio BFAU "
            "cuando gasto de bolsillo acumulado supera el tope, sin modificar su plan base. "
            "Responde a Carla Castillo (DOCX140)."
        ),
    },
]


def make_comment_elem(cid, text):
    """Create a <w:comment> element."""
    c = etree.Element(qn("comment"))
    c.set(qn("id"), cid)
    c.set(qn("author"), AUTHOR)
    c.set(qn("date"), DATE)
    c.set(qn("initials"), "MI")

    p = etree.SubElement(c, qn("p"))
    r = etree.SubElement(p, qn("r"))
    t = etree.SubElement(r, qn("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return c


def anchor_comment_to_paragraph(p, cid):
    """Insert commentRangeStart and commentRangeEnd + commentReference within paragraph p."""
    # Insert commentRangeStart at beginning (after pPr)
    pPr = p.find(qn("pPr"))
    pos = 0 if pPr is None else 1

    cr_start = etree.Element(qn("commentRangeStart"))
    cr_start.set(qn("id"), cid)

    cr_end = etree.Element(qn("commentRangeEnd"))
    cr_end.set(qn("id"), cid)

    r_ref = etree.Element(qn("r"))
    rPr = etree.SubElement(r_ref, qn("rPr"))
    rStyle = etree.SubElement(rPr, qn("rStyle"))
    rStyle.set(qn("val"), "CommentReference")
    cref = etree.SubElement(r_ref, qn("commentReference"))
    cref.set(qn("id"), cid)

    # Insert at start and append at end
    p.insert(pos, cr_start)
    p.append(cr_end)
    p.append(r_ref)


def process_docx():
    if V312.exists():
        V312.unlink()
    shutil.copy(V311, V312)
    print(f"Copied: {V311.name} -> {V312.name}")

    log = []

    with zipfile.ZipFile(V312, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))
    com_tree = etree.fromstring(com_xml)

    # Get max existing comment id
    existing_ids = [int(c.get(qn("id"), "0")) for c in com_tree.findall(qn("comment"))]
    max_id = max(existing_ids) if existing_ids else 0
    global _next_comment_id
    _next_comment_id = max(max_id + 100, 1000)

    # Insert each new comment
    for spec in NUEVOS_COMENTARIOS:
        code = spec["code"]
        anchor = spec["anchor"]
        body_text = spec["body"]

        # Find paragraph
        if anchor["mode"] == "prefix":
            i, p = find_paragraph_by_prefix(body, anchor["value"])
        else:
            i, p = find_paragraph_contains(body, anchor["value"])

        if p is None:
            log.append(("NOT FOUND", code, anchor["value"][:50]))
            continue

        # Create comment
        cid = next_comment_id()
        comment_elem = make_comment_elem(cid, body_text)
        com_tree.append(comment_elem)

        # Anchor to paragraph
        anchor_comment_to_paragraph(p, cid)

        log.append(("OK", f"{code} (cid={cid})", f"para {i}"))

    # Write back
    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V312, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V312)

    return log


def main():
    log = process_docx()
    print(f"\n=== v3.12: Comentarios MI-NN trazables ===")
    ok = sum(1 for s, _, _ in log if s == "OK")
    fail = sum(1 for s, _, _ in log if s != "OK")
    print(f"OK: {ok}, fail: {fail}")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:20s}  {detail}")
    print(f"\nOutput: {V312}")
    print(f"Size: {V312.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
