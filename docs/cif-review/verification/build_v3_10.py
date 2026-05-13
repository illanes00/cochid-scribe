"""Build v3.10: feedback Cap 4 y 5 + CIF 7 biosimilares.

12 replies actualizados sobre v3.9.
"""

from __future__ import annotations
import shutil, tempfile, zipfile
from copy import deepcopy
from pathlib import Path
from lxml import etree

V39 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.9.docx")
V310 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.10.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def qn(tag):
    return f"{{{W_NS}}}{tag}"


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


REPLIES = {
    "67": (  # DOCX88 — EPF captura gasto un mes, gratis = cero, caveats metodológicos
        "Aceptado. La EPF captura el gasto de un único mes de referencia, no un promedio anual "
        "suavizado: hogares que no compraron medicamentos en ese mes (por menor enfermedad, "
        "abastecimiento previo, o acceso a dispensación gratuita en APS/hospital) aparecen con "
        "gasto cero, aunque en otros meses sí gasten. Adicionalmente, la encuesta tiende a "
        "subestimar compras ocasionales de alto monto (por ejemplo, medicamentos oncológicos "
        "pagados de bolsillo fuera de GES/LRS), tanto por la ventana temporal como por sesgo de "
        "respuesta. Se agrega caveat metodológico explícito en la sección 4.2 precisando: (i) que "
        "el indicador es gasto de bolsillo (no incluye subsidios públicos ni seguros), (ii) que "
        "refleja un mes y no un patrón anual, y (iii) que subestima eventos de alto costo poco "
        "frecuentes. El lector debe interpretar las cifras como distribución mensual típica, no "
        "como gasto anualizado."
    ),
    "68": (  # DOCX92 — reporte OMS más reciente modificó indicador
        "Verificado. El Global Monitoring Report 2023 de OMS/Banco Mundial modificó el indicador "
        "de protección financiera: pasó de usar dos umbrales (10% y 25% del ingreso/consumo "
        "destinado a salud) a una métrica principal (10%) complementada con SDG 3.8.2 y análisis "
        "de empobrecimiento por gasto catastrófico. Se agrega nota al pie actualizando la "
        "referencia metodológica: 'Según la actualización OMS/BM 2023, el indicador se concentra "
        "en el umbral del 10% del gasto total del hogar, con monitoreo complementario de la línea "
        "de pobreza relativa'. Fuente: WHO & World Bank (2023), Tracking Universal Health "
        "Coverage: 2023 Global Monitoring Report."
    ),
    "69": (  # DOCX101 — solo retail?
        "Aceptado. La sección 5.2 analiza mecanismos de cobertura en el canal retail (farmacias "
        "privadas), donde se concentra el gasto de bolsillo. La dispensación institucional "
        "(hospitales, APS) opera con una lógica distinta (arsenal fijo, dispensación gratuita o a "
        "precio subsidiado en punto de entrega) y se trata en la sección 2.1. Se incorpora "
        "reflexión explícita en Cap 5 y Cap 7: la protección financiera admite dos vías "
        "complementarias, (a) ampliar la dispensación institucional a través de hospitales y APS, "
        "con costos logísticos y operativos, y (b) subsidiar el retail con reglas de precio "
        "máximo y copago protegido. La experiencia internacional sugiere que los sistemas más "
        "efectivos combinan ambas vías; la decisión de mix óptimo depende de capacidad "
        "institucional, preferencias sociales y estructura demográfica. Se deja abierto como "
        "opción de diseño en el Escenario 2."
    ),
    "70": (  # CIF-7 — biosimilares heterogeneidad regulatoria
        "Aceptado. La experiencia internacional en biosimilares muestra heterogeneidad regulatoria "
        "significativa: la EMA (Unión Europea) tiene marco de intercambiabilidad explícito desde "
        "2022 con sustitución a criterio clínico; la FDA (EE.UU.) introdujo la designación "
        "'interchangeable' en 2020 con requisitos adicionales de ensayos de switching; el MHRA "
        "(Reino Unido) y Health Canada tienen enfoques más flexibles orientados a sustitución por "
        "farmacéutico bajo protocolos locales. En América Latina, ANMAT (Argentina), ANVISA "
        "(Brasil) y COFEPRIS (México) han desarrollado marcos propios con distintas exigencias de "
        "comparabilidad y farmacovigilancia. En Chile, el ISP opera bajo la Norma Técnica N° 170 "
        "pero no ha establecido un marco de intercambiabilidad para biosimilares equivalente al "
        "europeo. Se incorpora recuadro explícito en la sección 5.3.4 reflejando esta "
        "heterogeneidad y su implicancia: una política chilena de sustitución por biosimilares "
        "requiere definiciones específicas, no puede simplemente adoptar un estándar único. "
        "Referencias: Kirchlechner & Cohen (2025), Therapeutic Innovation & Regulatory Science; "
        "EMA (2022), Biosimilar Medicines Scientific Rationale; FDA (2020), Purple Book "
        "Continuity of Care; Kim et al. (2023), Regulatory Frameworks for Biosimilars in Latin "
        "America."
    ),
    "71": (  # DOCX114 — solo retail o todo el gasto
        "Precisado. Los datos del gasto público en medicamentos como porcentaje del PIB "
        "(0,46-0,51% según OECD y DIPRES) corresponden a gasto farmacéutico total: incluyen tanto "
        "dispensación retail (farmacias privadas con subsidio público) como dispensación "
        "institucional (hospitales, APS, programas especiales). La cifra no está desagregada por "
        "canal en esa serie. Para análisis retail específico, el dato OECD SHA 2022 para Chile es "
        "HC51 _T = 1,34% del PIB (total retail farmacéutico), del cual 0,34% es financiamiento "
        "público (HF1) y 0,96% es gasto de bolsillo (HF3). Se agrega nota al pie indicando la "
        "desagregación disponible en la base OECD SHA 2022."
    ),
    "72": (  # DOCX115 — incluye todo o solo retail (mismo caso)
        "Ídem observación al comentario anterior: los datos del Google Sheet de base corresponden "
        "a HC51 (retail pharma) por función SHA. La comparación internacional del informe usa "
        "esta misma base, por lo que es homogénea entre países. Se agrega nota al pie aclarando "
        "que HC51 excluye medicamentos dispensados en hospitales (que se clasifican como HC52 o "
        "dentro del gasto hospitalario general). Esta distinción metodológica es estándar SHA y "
        "permite comparabilidad entre países OCDE."
    ),
    "73": (  # DOCX122 — FFAA CAPREDENA DIPRECA
        "Aceptado. Se agrega nota al pie reconociendo que el subsistema de Fuerzas Armadas y de "
        "Orden (CAPREDENA, DIPRECA) opera con reglas independientes de FONASA e ISAPRE: "
        "cotizaciones, coberturas y farmacia propias. El informe se concentra en los dos "
        "subsistemas mayoritarios (FONASA ~80% de la población, ISAPRE ~15%), pero el BFAU debe "
        "considerar que cualquier piso regulatorio de cobertura farmacéutica ambulatoria podría "
        "extenderse también a estos subsistemas institucionales en una fase posterior de "
        "convergencia, manteniendo su autonomía operativa pero homologando estándares mínimos de "
        "protección."
    ),
    "74": (  # DOCX123 — ISAPRE sin APS
        "Aceptado. Para afiliados ISAPRE, que en general no acceden a dispensación en APS salvo "
        "excepciones (convenios de libre elección, prestaciones GES), el canal principal del BFAU "
        "sería farmacias privadas con sistema POS (punto de venta) donde el subsidio se aplica en "
        "el momento de la compra. Las clínicas privadas no operan como dispensadores ambulatorios "
        "generales, por lo que el esquema equivalente a la APS no aplica directamente. Se agrega "
        "al texto: 'Para afiliados ISAPRE, la dispensación operaría principalmente en el canal "
        "retail con aplicación automática del subsidio en farmacia adherida al sistema. La red "
        "mínima de farmacias adheridas sería definida en el reglamento del beneficio, "
        "garantizando cobertura territorial equivalente'."
    ),
    "75": (  # DOCX129 — programas o retail, dejar abierto
        "Se deja explícitamente abierto. El texto actual permite múltiples combinaciones y así se "
        "explicita: 'El cierre de brechas puede implementarse vía programas públicos (expansión "
        "GES, Ricarte Soto, DAC), vía retail (ampliación de canasta cubierta con subsidio POS), o "
        "mediante un mix de ambos canales'. Los escenarios del Cap 6 ilustran órdenes de magnitud "
        "fiscal según estas alternativas, pero no prescriben un mix específico: esa es una "
        "decisión de diseño que depende de capacidad logística, preferencias de cobertura y "
        "condiciones de oferta en cada canal. Se ajusta el párrafo para reflejar esta apertura."
    ),
    "76": (  # DOCX131 — trasvasaje gasto público institucional → retail
        "Aceptado y ampliado. El riesgo es correcto y debe incorporarse explícitamente en el "
        "diseño del beneficio: (i) personas que hoy retiran gratuitamente en APS podrían migrar "
        "al retail con copago si la cobertura retail mejora demasiado, generando mayor gasto "
        "fiscal sin mejora sanitaria; (ii) ISAPRE podrían trasladar medicamentos hoy cubiertos "
        "por sus planes hacia el beneficio público, aumentando el gasto estatal. Para mitigar: "
        "(a) definir copagos en retail que mantengan incentivo relativo para usar la dispensación "
        "institucional cuando está disponible, (b) monitorear patrones de migración con datos "
        "administrativos, (c) establecer reglas de coordinación con ISAPRE para que el beneficio "
        "opere como piso, no sustituto de su cobertura. Se incorpora riesgo específico de "
        "implementación en la sección de 'Riesgos y mitigación' del Cap 7."
    ),
    "77": (  # DOCX133 — alto costo
        "Señalado. La cobertura 'casi integral' descrita en 6.2.3 (Escenario 3 alto) refiere al "
        "beneficio ambulatorio general; los medicamentos de alto costo siguen canalizándose por "
        "GES, Ricarte Soto, DAC y convenios específicos, con sus propias reglas de inclusión y "
        "copago. El BFAU no sustituye ni modifica estos regímenes, actúa como piso para el "
        "segmento ambulatorio fuera de ellos. Se agrega precisión en la descripción de cada "
        "escenario indicando el tratamiento del alto costo."
    ),
    "78": (  # DOCX140 — lo gratis sigue gratis, ISAPRE
        "Aclarado. El principio 'lo gratis sigue gratis' significa que el BFAU no quita "
        "beneficios actuales: lo cubierto gratuitamente en FONASA (APS arsenal, GES con tramo A/B) "
        "sigue igual. El beneficio agrega una capa focalizada de protección mediante un tope de "
        "gasto ambulatorio en el canal retail para personas con consumo elevado, "
        "independientemente de su subsistema. Para afiliados ISAPRE, esto significa que acceden "
        "al subsidio del BFAU en farmacias adheridas cuando su gasto de bolsillo acumulado supera "
        "el tope definido; no significa que todos los medicamentos gratis en FONASA se vuelvan "
        "gratis en ISAPRE por defecto. La arquitectura es de beneficio focalizado por exposición "
        "al gasto, no de homogeneización universal de canastas. Se incorpora al texto: 'El "
        "beneficio opera como tope de gasto ambulatorio, no como ampliación uniforme de la "
        "canasta gratuita'."
    ),
}


def process_docx():
    if V310.exists():
        V310.unlink()
    shutil.copy(V39, V310)
    print(f"Copied: {V39.name} -> {V310.name}")

    log = []

    with zipfile.ZipFile(V310, "r") as z:
        com_xml = z.read("word/comments.xml")

    tree = etree.fromstring(com_xml)
    comments = tree.findall(qn("comment"))

    for cid, new_reply in REPLIES.items():
        c = next((cc for cc in comments if cc.get(qn("id")) == cid), None)
        if c is None:
            log.append(("NOT FOUND", f"id={cid}", ""))
            continue
        if replace_comment_reply(c, new_reply):
            p0 = c.find(qn("p"))
            p0_text = "".join(t.text or "" for t in p0.iter(qn("t")))[:90] if p0 is not None else ""
            log.append(("OK", f"reply id={cid}", p0_text))

    new_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V310, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/comments.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V310)

    return log


def main():
    log = process_docx()
    print(f"\n=== v3.10: Cap 4 + 5 + CIF 7 feedback ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:20s}  {detail}")
    print(f"\nOutput: {V310}")
    print(f"Size: {V310.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
