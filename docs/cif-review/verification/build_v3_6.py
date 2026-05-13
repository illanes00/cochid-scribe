"""Build v3.6: feedback Capítulo 2 — Carla 29, 30, 33, 34, 37, 38.

Responde 6 comentarios de Carla Castillo sobre el Cap 2:

- id=50 (CC-DOCX29): "las personas también serían ejecutoras, no?"
  → Aceptar: las personas son ejecutoras del gasto de bolsillo; agregar al listado.

- id=51 (CC-DOCX30): "publica?" — se refiere a cobertura efectiva con barreras en red pública
  → Aclarar: barreras de disponibilidad/dispensación/red empujan compra fuera del canal
  protegido (importación, compra en retail, etc.).

- id=52 (CC-DOCX33): "Acá muchas veces se entregan medicamentos de alto costo, no?"
  → Matizar: la farmacia hospitalaria ambulatoria sí entrega medicamentos de alto costo
  (DAC oncológico, Ricarte Soto); no es taxativo 1:1 retail vs hospital.

- id=53 (CC-DOCX34): "También en convenio con ISAPRE en el caso de las GES..."
  → Aceptar: convenios ISAPRE, descuentos, seguro complementario, CAEC (Cobertura
  Adicional para Enfermedades Catastróficas) son mecanismos relevantes.

- id=54 (CC-DOCX37): "Mayoritariamente varía entre FONASA 0 e ISAPRE 20% del arancel de
  referencia, aunque operan deducibles definidos por ley"
  → Aceptar y precisar: FONASA A/B = 0%, C = 10%, D = 20% del valor garantizado; ISAPRE
  = 20% del arancel de referencia con deducibles anuales por ley.

- id=55 (CC-DOCX38): "Acá no se consideran las GES, verdad?"
  → Aclarar: GES se analiza en sec 2.2 (punto 3), plan ISAPRE en sec 2.2 (punto 7);
  aunque plan ISAPRE incluye GES, se describen por separado.

Input:  informe-final-v3.5.docx
Output: informe-final-v3.6.docx
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

V35 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.5.docx")
V36 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.6.docx")

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


REPLIES = {
    "50": (  # CC-DOCX29 — personas ejecutoras
        "Aceptado. Las personas son ejecutoras del gasto en la dimensión del gasto de bolsillo "
        "(compras directas en farmacia, copagos, gastos no cubiertos). Se ajusta el listado de "
        "ejecutores para incluir a los hogares como actor ejecutor en el segmento de gasto privado "
        "y de bolsillo, diferenciándolo de los ejecutores institucionales (Servicios de Salud, PNI, "
        "LRS, Municipios)."
    ),
    "51": (  # CC-DOCX30 — publica/barreras
        "Aceptado. La observación apunta a una distinción importante: la cobertura nominal no "
        "garantiza acceso efectivo. Aun cuando el medicamento esté formalmente cubierto por la red "
        "pública, existen barreras de disponibilidad (quiebres de stock), dispensación (capacidad de "
        "las farmacias hospitalarias o APS) y de red (derivaciones, filas, tiempos de espera) que "
        "empujan al paciente a comprarlo fuera del canal protegido: retail privado, importación "
        "personal, o judicialización. Se agrega esta aclaración al párrafo y se articula con la "
        "sección sobre judicialización (3.2.6)."
    ),
    "52": (  # CC-DOCX33 — alto costo hospital ambulatorio
        "Aceptado. La farmacia hospitalaria ambulatoria es canal primario de dispensación de "
        "medicamentos de alto costo: cobertura GES de patologías hospitalarias, Ley Ricarte Soto, "
        "DAC oncológico y quimioterapia ambulatoria. Se ajusta la redacción para evitar el binarismo "
        "retail privado / hospital: el arsenal hospitalario incluye medicamentos de alto costo que "
        "se dispensan ambulatoriamente."
    ),
    "53": (  # CC-DOCX34 — convenios ISAPRE + CAEC
        "Aceptado. Bajo GES, las ISAPRE operan redes preferentes que pueden incluir farmacias de "
        "cadena o independientes como puntos formales de dispensación. Adicionalmente, las ISAPRE "
        "ofrecen: (i) convenios con farmacias retail que entregan descuentos sobre el precio lista; "
        "(ii) seguros complementarios contratados por el afiliado; y (iii) la Cobertura Adicional "
        "para Enfermedades Catastróficas (CAEC), que limita el gasto de bolsillo para atenciones "
        "de alto costo en la red cerrada de la ISAPRE. Se agrega mención a estos tres mecanismos."
    ),
    "54": (  # CC-DOCX37 — copagos FONASA/ISAPRE
        "Aceptado y precisado. El copago GES varía por subsistema: en FONASA depende del tramo del "
        "beneficiario (A y B = 0% del valor garantizado; C = 10%; D = 20%). En ISAPRE el copago es "
        "20% del arancel de referencia, aunque operan deducibles anuales definidos por ley para "
        "problemas de alto costo. Se actualiza la redacción con estas cifras precisas."
    ),
    "55": (  # CC-DOCX38 — GES en instrumentos
        "Aclarado. GES se analiza en la sección 2.2 punto 3 (instrumentos específicos), mientras el "
        "plan ISAPRE se aborda en el punto 7. Aunque el plan ISAPRE incluye por ley las prestaciones "
        "GES, se describen por separado para reflejar la distinción entre el régimen universal "
        "(GES) y los planes complementarios privados. Se agrega esta nota de estructura al comienzo "
        "de la sección para evitar ambigüedad."
    ),
}


def process_docx():
    if V36.exists():
        V36.unlink()
    shutil.copy(V35, V36)
    print(f"Copied: {V35.name} -> {V36.name}")

    log = []

    with zipfile.ZipFile(V36, "r") as z:
        com_xml = z.read("word/comments.xml")

    tree = etree.fromstring(com_xml)
    comments = tree.findall(qn("comment"))

    for cid, new_reply in REPLIES.items():
        c = next((cc for cc in comments if cc.get(qn("id")) == cid), None)
        if c is None:
            log.append(("NOT FOUND", f"reply id={cid}", ""))
            continue
        if replace_comment_reply(c, new_reply):
            author = c.get(qn("author"))
            p0 = c.find(qn("p"))
            p0_text = "".join(t.text or "" for t in p0.iter(qn("t")))[:60] if p0 is not None else ""
            log.append(("OK", f"reply id={cid} ({author[:15]})", p0_text))

    new_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V36, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/comments.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V36)

    return log


def main():
    log = process_docx()
    print("\n=== v3.6: Cap 2 feedback (Carla 29/30/33/34/37/38) ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:30s}  {detail[:80]}")
    print(f"\nOutput: {V36}")
    print(f"Size: {V36.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
