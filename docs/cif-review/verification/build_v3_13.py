"""Build v3.13: últimos replies Cap 7/8 + MI-12 a MI-15 trazables."""

from __future__ import annotations
import re, shutil, tempfile, zipfile
from copy import deepcopy
from pathlib import Path
from lxml import etree

V312 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.12.docx")
V313 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.13.docx")

AUTHOR = "Martín Illanes"
DATE = "2026-01-01T00:00:00Z"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


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


def get_para_text_normalized(p):
    return re.sub(r"\s+", " ", get_para_text(p)).strip()


def find_paragraph_contains(body, needle, start_index=0):
    norm_needle = re.sub(r"\s+", " ", needle).strip()
    paragraphs = body.findall(qn("p"))
    for i, p in enumerate(paragraphs[start_index:], start=start_index):
        if norm_needle in get_para_text_normalized(p):
            return i, p
    return None, None


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


def make_comment_elem(cid, text):
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


def anchor_comment(p, cid):
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
    p.insert(pos, cr_start)
    p.append(cr_end)
    p.append(r_ref)


REPLIES = {
    "84": (  # DOCX157 financiamiento FONASA/ISAPRE
        "Aclarado como decisión abierta. El informe no se casa con un mecanismo específico de "
        "financiamiento. La arquitectura admite varias opciones: (a) fondos públicos con cargo al "
        "presupuesto general (FONASA + ISAPRE universalmente con fiscos), (b) cotización "
        "adicional específica para el beneficio farmacéutico, (c) FONASA cubre a sus afiliados y "
        "las ISAPRE a los suyos con incorporación obligatoria del piso del beneficio en sus planes, "
        "(d) combinaciones híbridas. Dependiendo del escenario fiscal (1/2/3), la magnitud del "
        "aumento de gasto converge hacia distintos niveles OCDE. La recomendación implícita del "
        "informe es que, al tratarse de un beneficio universal, el financiamiento principal "
        "provenga del presupuesto nacional, con contribuciones sectoriales complementarias; pero "
        "la decisión específica queda abierta para el debate político y el seminario."
    ),
    "85": (  # DOCX166 cambio ley compras
        "Aceptado. El mecanismo de 'no dispensación' requiere modificaciones legales a la Ley de "
        "Compras Públicas y/o a normativa de CENABAST para habilitar compras excepcionales en "
        "canal retail con reembolso cuando el canal institucional falla. El principio rector es "
        "que el paciente siempre debe tener garantizado el acceso oportuno al medicamento: los "
        "quiebres de stock, demoras de dispensación o problemas logísticos no pueden trasladarse "
        "como carga financiera o como retraso terapéutico al hogar. Las modificaciones incluirían: "
        "(i) habilitar compra de urgencia en retail por parte del asegurador con reembolso, "
        "(ii) definir criterios y umbrales para activar el mecanismo, (iii) establecer "
        "trazabilidad administrativa, (iv) cláusula de excepción en la normativa de compras "
        "públicas para este canal. Se incorpora al texto como condición habilitante."
    ),
    "86": (  # DOCX171 MAI a MLE
        "Aceptado y ampliado. El riesgo de trasvasaje entre modalidades MAI y MLE es una "
        "instancia específica del riesgo general de desbalance entre subsistemas. Su gestión "
        "requiere: (i) mantener copagos diferenciados que preserven incentivos relativos al canal "
        "institucional cuando está disponible, (ii) monitorear migración de beneficiarios entre "
        "modalidades con datos administrativos, (iii) coordinar reglas entre subsistemas para "
        "evitar que el BFAU genere desbalances de caja. Este riesgo es simétrico: también podría "
        "haber migración FONASA→ISAPRE o viceversa si el beneficio genera incentivos desbalanceados "
        "por subsistema. Se incorpora al texto como riesgo general de implementación en el Cap 7."
    ),
    "87": (  # DOCX173 fragmentación
        "Aclarado. El BFAU no elimina la fragmentación existente (GES, Ricarte Soto, DAC, FOFAR "
        "siguen con sus reglas), sino que actúa como una malla de seguridad o 'segundo piso' que "
        "atrapa al paciente cuando ningún programa lo cubre en un nivel significativo. La idea "
        "es: (i) los programas existentes operan como primer piso, cada uno con su lógica de "
        "inclusión; (ii) cuando un paciente queda fuera de todos ellos, o enfrenta gasto de "
        "bolsillo acumulado que supera el tope, el BFAU actúa como red de protección financiera; "
        "(iii) en términos prácticos, el sistema se unifica desde la perspectiva del beneficiario "
        "(siempre hay una capa que cubre), aunque operativamente persista la fragmentación "
        "institucional. Esta lógica de 'red de seguridad financiera' evita una reforma sistémica "
        "grande que requeriría unificar todos los regímenes, y permite convergencia gradual. Se "
        "incorpora al texto como principio de diseño explícito."
    ),
}


# Nuevos MI-NN asociados a este feedback
NUEVOS_MI = [
    {
        "code": "MI-12",
        "anchor": "Financiamiento: principios y opciones",
        "body": (
            "[MI-12] Financiamiento abierto: no nos casamos con un mecanismo. El informe presenta "
            "opciones (fondos públicos con cargo a presupuesto nacional; cotización adicional; "
            "FONASA+ISAPRE con sus propias fuentes con piso regulatorio; combinaciones híbridas). "
            "La recomendación implícita es que, siendo un beneficio universal, el financiamiento "
            "principal provenga del fisco general, pero la decisión específica queda abierta para "
            "el debate político. Responde a Carla Castillo (DOCX157)."
        ),
    },
    {
        "code": "MI-13",
        "anchor": "Mecanismo operativo para",
        "body": (
            "[MI-13] Modificaciones legales a compras públicas. La habilitación del mecanismo de "
            "'no dispensación' requiere ajustes a la Ley de Compras Públicas y normativa CENABAST. "
            "El principio rector: el paciente siempre tiene garantizado el acceso oportuno; quiebres "
            "de stock no pueden trasladarse como carga financiera o retraso terapéutico al hogar. "
            "Se agrega esta precisión como condición habilitante del Cap 7. Responde a Carla "
            "Castillo (DOCX166)."
        ),
    },
    {
        "code": "MI-14",
        "anchor": "Riesgos de implementación",
        "body": (
            "[MI-14] Trasvasaje entre modalidades y subsistemas. El riesgo MAI→MLE (Carla DOCX171) "
            "es instancia del riesgo general de desbalance por incentivos. Mitigaciones aplicables "
            "simétricamente a todas las migraciones posibles (MAI↔MLE, FONASA↔ISAPRE, "
            "institucional↔retail): copagos diferenciados, monitoreo administrativo, coordinación "
            "inter-subsistemas. Responde a Carla Castillo (DOCX171)."
        ),
    },
    {
        "code": "MI-15",
        "anchor": "resuelve la fragmentación",
        "body": (
            "[MI-15] BFAU como malla de seguridad financiera, no unificación de regímenes. El "
            "beneficio no elimina la fragmentación institucional (GES, LRS, DAC, FOFAR siguen con "
            "sus reglas); actúa como segundo piso o red de protección que atrapa al paciente "
            "cuando ningún programa lo cubre. Desde la perspectiva del beneficiario, el sistema se "
            "unifica (siempre hay capa que cubre); operativamente persiste la fragmentación pero "
            "con continuidad financiera garantizada. Esto evita una reforma sistémica grande, "
            "permite convergencia gradual. Responde a Carla Castillo (DOCX173)."
        ),
    },
]


def process_docx():
    if V313.exists():
        V313.unlink()
    shutil.copy(V312, V313)
    print(f"Copied: {V312.name} -> {V313.name}")

    log = []

    with zipfile.ZipFile(V313, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml")

    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))
    com_tree = etree.fromstring(com_xml)

    # Reply updates
    for cid, new_reply in REPLIES.items():
        c = next((cc for cc in com_tree.findall(qn("comment")) if cc.get(qn("id")) == cid), None)
        if c is None:
            log.append(("NOT FOUND", f"reply id={cid}", ""))
            continue
        replace_comment_reply(c, new_reply)
        log.append(("OK", f"reply id={cid}", ""))

    # New MI comments
    existing_ids = [int(c.get(qn("id"), "0")) for c in com_tree.findall(qn("comment"))]
    max_id = max(existing_ids) if existing_ids else 0
    next_id = max(max_id + 1, 1020)

    for spec in NUEVOS_MI:
        code = spec["code"]
        anchor = spec["anchor"]
        body_text = spec["body"]

        i, p = find_paragraph_contains(body, anchor)
        if p is None:
            log.append(("NOT FOUND", code, anchor[:40]))
            continue

        cid = str(next_id)
        next_id += 1

        comment_elem = make_comment_elem(cid, body_text)
        com_tree.append(comment_elem)
        anchor_comment(p, cid)

        log.append(("OK", f"{code} (cid={cid}, para {i})", ""))

    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_com_xml = etree.tostring(com_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V313, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml":
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V313)
    return log


def main():
    log = process_docx()
    print("\n=== v3.13: Cap 7/8 final + MI-12 a MI-15 ===")
    for status, name, detail in log:
        marker = "✓" if status == "OK" else "✗"
        print(f"  {marker} {name:25s}  {detail[:60]}")
    print(f"\nOutput: {V313}")
    print(f"Size: {V313.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
