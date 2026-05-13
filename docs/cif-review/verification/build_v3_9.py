"""Build v3.9: feedback Capítulo 3 y 4 de Carla (DOCX 72, 75, 78, 79, 85).

Input:  informe-final-v3.8.docx
Output: informe-final-v3.9.docx
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V38 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.8.docx")
V39 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.9.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
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


# Feedback Cap 3 y 4 del usuario sobre v3.8
REPLIES = {
    "62": (  # DOCX72 — judicialización sin criterio sanitario / evitar judicialización
        "Aceptado. La observación es central y se explicita en el texto: la judicialización opera "
        "frecuentemente sin criterio sanitario homogéneo, lo que introduce decisiones de cobertura "
        "sin evaluación técnica previa, con pérdidas potenciales en costo-efectividad y equidad. "
        "Según el informe CIF (2025), la judicialización es un problema creciente en magnitud y "
        "presupuesto. La propuesta del BFAU, con canasta explícita y proceso HTA/ETESA robusto, "
        "busca reducir la necesidad de recurrir a tribunales fortaleciendo el mecanismo formal de "
        "priorización técnica del MINSAL. Se incorpora esta tensión en la sección 3.2.6 como eje "
        "argumental: la judicialización es síntoma de falla institucional, no solución."
    ),
    "63": (  # DOCX75 — sistema judicial que respeta reglas
        "Aceptado. Un sistema judicial que respete o 'juegue' bajo las reglas del mecanismo formal "
        "de priorización es una configuración institucional deseable: los tribunales aplican el "
        "derecho a la protección de la salud reconociendo el marco HTA/ETESA del MINSAL como "
        "criterio técnico vinculante, salvo casos excepcionales de error manifiesto o denegación "
        "arbitraria. Se incorpora esta precisión: el objetivo del BFAU no es eliminar la vía "
        "judicial, sino reducir su uso como canal de primer acceso y alinearla con el sistema "
        "formal de priorización."
    ),
    "64": (  # DOCX78 — categorías hogares y medicamentos no excluyentes
        "Aceptado. Las categorías propuestas para la tipología de hogares (adquisición principal "
        "por canal, frecuencia de gasto, tipo de condición clínica) no son excluyentes: un hogar "
        "puede tener simultáneamente medicamentos crónicos de consumo repetido y medicamentos "
        "agudos de alto costo ocasional. Se ajusta la redacción para presentar las categorías como "
        "características descriptivas que pueden coexistir, no como segmentos mutuamente "
        "excluyentes. La tipología sirve para mapear perfiles de exposición al gasto de bolsillo, "
        "no para clasificar hogares de manera binaria."
    ),
    "65": (  # DOCX79 — GES incluye alto costo
        "Aceptado. GES incluye medicamentos de alto costo para varios problemas de salud "
        "garantizados: cánceres (leucemias, linfomas, mama, próstata), fibrosis quística "
        "(moduladores CFTR desde DS 22/2025), esclerosis múltiple, VIH, trasplantes, entre otros. "
        "Se revisa todo el documento para que la expresión 'alto costo' no sea sinónimo exclusivo "
        "de Ley Ricarte Soto y DAC, sino que refleje correctamente que los instrumentos de "
        "cobertura de alto costo en Chile son un conjunto articulado (GES + Ricarte Soto + DAC + "
        "FOFAR), con distintos criterios de inclusión y mecanismos de copago. La propuesta del "
        "BFAU se dirige al segmento de medicamentos ambulatorios que queda fuera de estos "
        "regímenes, no los sustituye."
    ),
    "66": (  # DOCX85 — gasto total medicamentos vs retail, caveat
        "Aceptado y matizado. La lectura es correcta: las coberturas bajas específicamente en el "
        "canal retail explican buena parte del gasto de bolsillo, pero no reflejan el cuadro "
        "completo. Para contexto comparado: Chile tiene un gasto farmacéutico total per cápita de "
        "US$394 PPA (OECD SHA 2022), alto para estándares latinoamericanos (Costa Rica US$145, "
        "México US$251, Brasil US$330) pero bajo frente al promedio OCDE de US$614. El foco del "
        "informe es el canal retail porque es donde se materializa el 71% del gasto de bolsillo "
        "(HF3/HC51, OECD 2022), y donde el BFAU tendría mayor impacto en protección financiera. "
        "Se agrega caveat explícito en la sección 4.1 reconociendo que (a) la comparación "
        "internacional debe hacerse con cuidado por diferencias de composición del arsenal, canales "
        "de dispensación y precios negociados; (b) el foco retail es decisión analítica, no "
        "implica que el gasto institucional sea irrelevante; (c) cualquier intervención debe "
        "monitorear efectos cruzados entre canales."
    ),
}


def process_docx():
    if V39.exists():
        V39.unlink()
    shutil.copy(V38, V39)
    print(f"Copied: {V38.name} -> {V39.name}")

    log = []

    with zipfile.ZipFile(V39, "r") as z:
        com_xml = z.read("word/comments.xml")

    tree = etree.fromstring(com_xml)
    comments = tree.findall(qn("comment"))

    for cid, new_reply in REPLIES.items():
        c = next((cc for cc in comments if cc.get(qn("id")) == cid), None)
        if c is None:
            log.append(("NOT FOUND", f"reply id={cid}", ""))
            continue
        if replace_comment_reply(c, new_reply):
            p0 = c.find(qn("p"))
            p0_text = "".join(t.text or "" for t in p0.iter(qn("t")))[:80] if p0 is not None else ""
            log.append(("OK", f"reply id={cid}", p0_text))

    new_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V39, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/comments.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V39)

    return log


def main():
    log = process_docx()
    print("\n=== v3.9: Cap 3 + 4 feedback (Carla 72/75/78/79/85) ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:20s}  {detail[:90]}")
    print(f"\nOutput: {V39}")
    print(f"Size: {V39.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
