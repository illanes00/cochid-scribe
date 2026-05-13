"""Build v3.11: feedback Cap 7 (Carla 142, 143, 145, 149, 151)."""

from __future__ import annotations
import shutil, tempfile, zipfile
from copy import deepcopy
from pathlib import Path
from lxml import etree

V310 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.10.docx")
V311 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.11.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def qn(t): return f"{{{W_NS}}}{t}"

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
    "79": (  # DOCX142 — programas siguen existiendo, capa adicional
        "Aceptado y aclarado. El diseño propuesto del Beneficio Farmacéutico Ambulatorio Universal "
        "(BFAU) no reemplaza ni fusiona los programas existentes (GES, Ley Ricarte Soto, DAC, FOFAR): "
        "estos continúan operando con sus propias reglas de inclusión y cobertura. El BFAU actúa como "
        "una capa adicional de protección que cubre los hoyos dejados por la fragmentación: "
        "medicamentos ambulatorios fuera de los regímenes existentes, o medicamentos cubiertos "
        "nominalmente pero con brechas de acceso efectivo (quiebres de stock, falta de red). La "
        "fragmentación actual subsiste estructuralmente, pero deja de traducirse en exposición "
        "financiera del hogar cuando el gasto acumulado supera el tope del BFAU. Se agrega al texto: "
        "'El BFAU opera como capa de continuidad sobre el sistema fragmentado existente, no como "
        "sustitución de los regímenes actuales.'"
    ),
    "80": (  # DOCX143 — mecanismo operativo no-dispensación, reembolso retail
        "Aceptado. El mecanismo operativo funciona como principio general aplicable a cualquier "
        "régimen donde el Estado garantiza la dispensación: si GES, Ricarte Soto, DAC, FOFAR o el "
        "arsenal público no pueden entregar el medicamento garantizado por quiebre de stock u otra "
        "causal validada, se activa una vía de continuidad en canal retail con cobertura automática "
        "bajo las reglas del régimen original (copago equivalente, reembolso posterior, o pago "
        "directo al retail desde el programa). En FONASA opera principalmente como reembolso o "
        "mecanismo de compensación de stock; en ISAPRE, donde ya existe red retail mediante "
        "convenios, opera como extensión de la cobertura garantizada a farmacias adheridas. El "
        "principio clave es que la falla operativa del canal institucional no debe trasladarse como "
        "carga financiera al hogar. Se incorpora al texto como principio de continuidad de acceso."
    ),
    "81": (  # DOCX145 — expansión MAI/APS modifica estadísticas
        "Aceptado y precisado. Una expansión de la Modalidad Atención Institucional (MAI) y del "
        "arsenal APS reduciría el gasto de bolsillo (HF3) pero aumentaría el gasto público (HF1), "
        "manteniendo aproximadamente constante el gasto farmacéutico total (HC51 _T). Los "
        "escenarios del Cap 6 se calibran sobre la protección financiera resultante (reducción de "
        "gasto de bolsillo) y el costo fiscal total, no sobre el mix específico entre canales. Por "
        "lo tanto, las estadísticas comparadas siguen siendo válidas como punto de calibración: "
        "los países OCDE que lograron reducir el gasto de bolsillo lo hicieron mediante mix de "
        "ampliación institucional y cobertura retail con copagos protegidos, en proporciones "
        "variables. El informe no prescribe un mix específico; propone rangos fiscales y de "
        "protección que son compatibles con distintas combinaciones operativas. Se agrega nota "
        "metodológica en 7.3.1 explicitando que la expansión MAI/APS y la cobertura retail son "
        "sustitutos parciales desde la perspectiva del beneficiario, pero implican costos "
        "logísticos y capacidades institucionales distintas."
    ),
    "82": (  # DOCX149 — cobertura diferencial GES vs no-GES, largo plazo reducir fragmentación
        "Aceptado y ampliado. La observación es correcta y orienta una decisión de diseño "
        "importante. La lógica propuesta del BFAU es la siguiente: (i) si un medicamento está "
        "aprobado por el ISP y tiene evidencia clínica, opera el régimen más favorable al paciente "
        "según su condición; (ii) si el uso está dentro del listado GES para la patología "
        "garantizada, prevalece GES con sus reglas de copago y red; (iii) para el mismo "
        "medicamento usado en otra patología no garantizada (off-label autorizado o uso en "
        "patología no-GES), aplica el BFAU con canasta explícita y tope de gasto acumulado; "
        "(iv) el BFAU no se limita exclusivamente al segmento ambulatorio: cubre también "
        "medicamentos de alto costo fuera de Ricarte Soto y DAC, siempre que tengan evidencia y "
        "aprobación ISP. Se amplía la redacción actual que decía 'piso para lo ambulatorio fuera "
        "de esos regímenes' por 'piso para medicamentos no cubiertos por GES/LRS/DAC/FOFAR, con "
        "énfasis en el segmento ambulatorio pero sin excluir alto costo ambulatorio cuando "
        "corresponda'. En el largo plazo, el diseño debería converger a reducir la fragmentación "
        "entre regímenes para que un mismo medicamento tenga tratamiento consistente entre usos; "
        "esta convergencia se deja planteada como horizonte de política de tercera fase."
    ),
    "83": (  # DOCX151 — cap por hogar o persona
        "Aceptado y ampliado. El tope de gasto acumulado admite distintas unidades de acumulación, "
        "cada una con implicancias distributivas y operativas. Las opciones posibles son: (a) por "
        "persona (simple, usa sólo el RUT, pero penaliza hogares con varios enfermos crónicos que "
        "suman gastos individuales sin llegar al tope); (b) por hogar, acumulando gasto de todos "
        "los miembros (mayor protección a familias con alta carga de enfermedad, requiere "
        "definición operativa de hogar, puede apoyarse en el Registro Social de Hogares); (c) por "
        "núcleo familiar declarado (alternativa intermedia vía cotizante y cargas FONASA/ISAPRE); "
        "(d) vía sistema tributario como crédito anual con tope, que cruza datos SII con registros "
        "farmacéuticos. La definición específica no corresponde a este informe y se deja a la "
        "etapa de implementación reglamentaria. El informe recomienda explorar la opción por "
        "hogar como prioritaria, bajo el principio de que el hogar es la unidad económica que "
        "junta ingresos para financiar medicamentos; la opción por persona puede generar "
        "desprotección a hogares con múltiples enfermos crónicos. Se incorpora esta discusión al "
        "texto del Cap 7 como nota de diseño y como pregunta abierta para el Cap 8."
    ),
}


def process_docx():
    if V311.exists():
        V311.unlink()
    shutil.copy(V310, V311)
    print(f"Copied: {V310.name} -> {V311.name}")

    log = []

    with zipfile.ZipFile(V311, "r") as z:
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
            log.append(("OK", f"id={cid}", p0_text))

    new_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V311, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/comments.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V311)
    return log


def main():
    log = process_docx()
    print(f"\n=== v3.11: Cap 7 feedback ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:15s}  {detail}")
    print(f"\nOutput: {V311}")
    print(f"Size: {V311.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
