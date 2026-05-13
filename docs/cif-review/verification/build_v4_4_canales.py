"""v4.4: completar canales 2.1 y sub-bloques 2.5 que quedaron vacíos en v4.3.

Inserts manuales con anchors específicos sobre v4.3-aceptada.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from lxml import etree

sys.path.insert(0, str(Path(__file__).parent))
from build_v3_18 import qn, AUTHOR, get_para_text, normalize

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

import build_v3_18
DATE_V44 = "2026-05-07T22:00:00-04:00"
build_v3_18.DATE = DATE_V44

BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
SRC = BASE / "output/informe-final-v4.3.docx"
V44 = BASE / "output/informe-final-v4.4.docx"
V44A = BASE / "output/informe-final-v4.4-aceptada.docx"


# =============================================================
# Sub-bloques nuevos a insertar
# =============================================================

# Sec 2.1 — Canales faltantes (insertar ENTRE bloques existentes)
SEC_2_1_INSERTS = [
    # Después del intro de canales (cap2-016), insertar Retail comercial PRIMERO
    {
        "anchor": "Los canales de dispensacion corresponden al circuito fisico mediante el cual el medicamento llega a la persona",
        "blocks": [
            ("Heading3", "Retail comercial (cadenas e independientes)"),
            ("p", "El canal retail comercial concentra la mayor parte del gasto de bolsillo en medicamentos. Las tres cadenas con mayor cobertura territorial (Cruz Verde, Salcobrand y Ahumada) operan junto con farmacias independientes en todo el país. La compra es directa, sin intermediación de cobertura para la mayoría de los medicamentos no GES, y los precios responden a estructura de mercado, márgenes minoristas y bonificaciones por convenios con seguros complementarios. Para los hogares sin cobertura efectiva en el sistema público o sin seguro complementario, este canal define la exposición financiera mes a mes."),
        ],
    },
    # Después del bloque APS, antes del de farmacias municipales: Hospitalario
    {
        "anchor": "La APS dispensa medicamentos asociados a las prestaciones del nivel primario a la poblacion inscrita en el sistema publico",
        "blocks": [
            ("Heading3", "Farmacia hospitalaria (intra-hospitalaria y ambulatoria de especialidad)"),
            ("p", "Los hospitales públicos y privados operan farmacias internas que dispensan medicamentos durante la hospitalización (incluidos en el costo del egreso) y, en muchos casos, mantienen una farmacia ambulatoria de especialidad para pacientes en tratamientos prolongados de alta complejidad. Los oncológicos institucionales, los biológicos administrados en infusión y los medicamentos GES de patologías de tratamiento hospitalario se dispensan habitualmente por este canal. La cobertura financiera para el paciente depende del subsistema (Fonasa, Isapre) y del régimen aplicable (GES, Ley Ricarte Soto, DAC, CAEC), con copagos que pueden ser cero o significativos según el caso."),
        ],
    },
    # Después de farmacias municipales: Cenabast retail (Ley 21.198)
    {
        "anchor": "Las farmacias municipales surgieron desde 2015 como iniciativa local para reducir precios mediante intermediacion de Cenabast",
        "blocks": [
            ("Heading3", "Cenabast retail (Ley 21.198, farmacias adheridas)"),
            ("p", "La Ley 21.198 de 2020 habilita a Cenabast para intermediar la compra de un catálogo definido de medicamentos esenciales destinados a hogares mediante farmacias adheridas, públicas y privadas. En 2024 el sistema operó con cerca de 1.100 farmacias adheridas en 155 comunas, con $17.640 millones facturados y un ahorro estimado de $26.824 millones para los hogares respecto del precio retail comercial (Anuario Cenabast 2024). El alcance es acotado al catálogo definido por Cenabast y la cobertura territorial sigue concentrada en zonas con mayor densidad poblacional."),
        ],
    },
]

# Sec 2.5 — Sub-bloques pro-competencia faltantes (después de cap2-074 que sí se aplicó)
SEC_2_5_INSERTS = [
    # Después del intro de 2.5 (cap2-074): cuatro sub-bloques
    {
        "anchor": "Junto con los instrumentos de cobertura, Chile ha desarrollado politicas orientadas a mejorar la competencia",
        "blocks": [
            ("Heading3", "Cenabast Ley 21.198 (intermediación retail)"),
            ("p", "La Ley 21.198 amplía el rol histórico de Cenabast como central de compras institucionales hacia la intermediación para hogares vía farmacias adheridas. Los datos 2024 (Anuario Cenabast) muestran $17.640 millones facturados y un ahorro estimado de $26.824 millones para los hogares respecto del precio retail comercial, sobre un catálogo acotado de medicamentos esenciales. Su impacto sobre el gasto de bolsillo agregado es modesto en términos de cobertura del problema, dado que el catálogo y la cobertura territorial son limitados, pero el mecanismo de intermediación opera sobre el precio efectivo y resulta replicable a mayor escala si se decide ampliarlo."),
            ("Heading3", "Ley de Fármacos II (Ley 21.198, 2020)"),
            ("p", "La denominada Ley de Fármacos II se aprobó como Ley 21.198 en 2020 y combina la habilitación de Cenabast retail con disposiciones sobre prescripción por denominación común internacional, sustitución bioequivalente obligatoria en farmacia y publicación de precios. La implementación efectiva ha avanzado de forma desigual entre componentes: la prescripción por denominación común se aplica de manera generalizada en el sistema público pero menos en el privado, y la sustitución obligatoria depende de stock y disponibilidad en cada farmacia."),
            ("Heading3", "Bioequivalencia ISP"),
            ("p", "El Instituto de Salud Pública certifica la bioequivalencia de medicamentos genéricos respecto del producto referente. La cobertura del sistema ha crecido sostenidamente, con cerca de 5.300 productos certificados a 2024 según el registro ISP. La bioequivalencia es condición habilitante para que la sustitución obligatoria opere sin pérdida de eficacia clínica esperada, pero su impacto sobre el gasto de bolsillo depende de que la sustitución efectivamente ocurra en el punto de dispensación."),
            ("Heading3", "Observatorio de precios MINSAL"),
            ("p", "El Observatorio de Precios de Medicamentos publica precios de venta a público de las principales cadenas y de farmacias adheridas a Cenabast. Su utilidad para la toma de decisiones del consumidor depende del acceso digital y del conocimiento del recurso. La cobertura no incluye todos los puntos de venta y no integra automáticamente la información con la receta electrónica, lo que limita su impacto agregado sobre la formación de precios."),
            ("Heading3", "Reducción del IVA a medicamentos (Ley 21.713, abril 2026)"),
            ("p", "En abril de 2026 se aprobó una reducción del impuesto al valor agregado aplicable a medicamentos como medida de alivio del gasto de bolsillo. La discusión técnica sobre su impacto agregado y su distribución por quintil queda fuera del alcance de este informe, que se concentra en la arquitectura de cobertura. Cabe registrar la medida como contexto del momento legislativo en que se publica este documento."),
        ],
    },
]


def make_inserted_paragraph(text: str, style: str | None = None) -> etree.Element:
    """Crea <w:p> con tracked insert + estructura compatible con v3.18."""
    p = etree.Element(qn("p"))
    pPr = etree.SubElement(p, qn("pPr"))
    if style:
        pStyle = etree.SubElement(pPr, qn("pStyle"))
        pStyle.set(qn("val"), style)
    rPr_pPr = etree.SubElement(pPr, qn("rPr"))
    ins_pPr = etree.SubElement(rPr_pPr, qn("ins"))
    ins_pPr.set(qn("id"), str(8000000))
    ins_pPr.set(qn("author"), AUTHOR)
    ins_pPr.set(qn("date"), DATE_V44)

    if text:
        ins = etree.SubElement(p, qn("ins"))
        ins.set(qn("id"), str(8000001))
        ins.set(qn("author"), AUTHOR)
        ins.set(qn("date"), DATE_V44)
        r = etree.SubElement(ins, qn("r"))
        rPr = etree.SubElement(r, qn("rPr"))
        rtl = etree.SubElement(rPr, qn("rtl"))
        rtl.set(qn("val"), "0")
        t = etree.SubElement(r, qn("t"))
        t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = text
    return p


def find_para_with_text(body, prefix: str):
    """Encuentra el primer párrafo cuyo texto empieza con `prefix` (~80 chars)."""
    prefix_norm = normalize(prefix)[:80]
    for p in body.iter(qn("p")):
        text = normalize(get_para_text(p))
        if text.startswith(prefix_norm[:60]):
            return p
    return None


def replace_in_paragraph_runs(p, old, new):
    text_elements = []
    pos = 0
    for elem in p.iter():
        if elem.tag != qn("t"):
            continue
        cur = elem
        in_del = False
        while cur is not None:
            if cur.tag == qn("del"):
                in_del = True
                break
            cur = cur.getparent()
        if in_del or elem.text is None:
            continue
        text_elements.append((elem, pos))
        pos += len(elem.text)

    full_text = "".join(t.text for t, _ in text_elements)
    if old not in full_text:
        return False

    start = full_text.find(old)
    end = start + len(old)
    placed = False

    for i, (elem, base) in enumerate(text_elements):
        text = elem.text or ""
        e_start, e_end = base, base + len(text)
        if e_end <= start or e_start >= end:
            continue
        local_start = max(0, start - e_start)
        local_end = min(len(text), end - e_start)
        if not placed:
            elem.text = text[:local_start] + new + text[local_end:]
            elem.set(f"{{{XML_NS}}}space", "preserve")
            placed = True
        else:
            new_text = text[:local_start] + text[local_end:]
            if new_text != text:
                elem.text = new_text
                elem.set(f"{{{XML_NS}}}space", "preserve")
    return placed


def main():
    print("=== build_v4_4_canales.py ===")
    print(f"SRC: {SRC.name} → {V44.name}\n")

    if not SRC.exists():
        raise SystemExit(f"⚠ {SRC} no existe")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shutil.copy2(SRC, tmp / "src.docx")
        with zipfile.ZipFile(tmp / "src.docx") as z:
            z.extractall(tmp / "src")

        doc_xml = tmp / "src/word/document.xml"
        tree = etree.parse(str(doc_xml))
        root = tree.getroot()
        body = root.find(qn("body"))

        # ==================================================
        # PASO 1: Insertar canales 2.1 y sub-bloques 2.5
        # ==================================================
        all_groups = SEC_2_1_INSERTS + SEC_2_5_INSERTS
        applied = 0
        skipped = 0

        for group in all_groups:
            anchor_text = group["anchor"]
            blocks = group["blocks"]
            anchor_p = find_para_with_text(body, anchor_text)
            if anchor_p is None:
                print(f"  ✗ Anchor no encontrado: {anchor_text[:60]}...")
                skipped += 1
                continue

            current = anchor_p
            for style, text in blocks:
                new_p = make_inserted_paragraph(text, style=style)
                current.addnext(new_p)
                current = new_p
                applied += 1

            print(f"  ✓ Insertados {len(blocks)} bloques tras: {anchor_text[:60]}...")

        print(f"\nTotal bloques insertados: {applied}")
        print(f"Anchors fallidos: {skipped}")

        # ==================================================
        # PASO 2: Limpiar 3 patrones IA residuales
        # ==================================================
        print("\n=== Limpieza patrones IA residuales ===")
        ia_fixes = [
            ("requiere no solo definir beneficios, sino asegurar su materialización efectiva en la dispensación.",
             "requiere definir beneficios y asegurar su materialización efectiva en la dispensación."),
            ('Es importante notar que "alto costo" no equivale a "baja prevalencia"',
             'La etiqueta "alto costo" puede coexistir con alta prevalencia poblacional'),
            ("aprovechando la plataforma ChileCompra para estandarizar",
             "utilizando la plataforma ChileCompra para estandarizar"),
        ]
        for p in body.iter(qn("p")):
            for old, new in ia_fixes:
                if replace_in_paragraph_runs(p, old, new):
                    print(f"  ✓ '{old[:60]}...' aplicado")

        # Guardar
        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        if V44.exists():
            V44.unlink()
        V44.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(V44, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))
        print(f"\n✓ {V44.name} ({V44.stat().st_size:,} bytes)")

        # Aceptada
        with tempfile.TemporaryDirectory() as tmpdir2:
            tmp2 = Path(tmpdir2)
            shutil.copy2(V44, tmp2 / "src.docx")
            with zipfile.ZipFile(tmp2 / "src.docx") as z:
                z.extractall(tmp2 / "src")
            doc_xml_a = tmp2 / "src/word/document.xml"
            tree_a = etree.parse(str(doc_xml_a))
            root_a = tree_a.getroot()
            for ins in list(root_a.iter(qn("ins"))):
                parent = ins.getparent()
                idx = list(parent).index(ins)
                for child in list(ins):
                    ins.remove(child)
                    parent.insert(idx, child)
                    idx += 1
                parent.remove(ins)
            for d in list(root_a.iter(qn("del"))):
                d.getparent().remove(d)
            tree_a.write(str(doc_xml_a), xml_declaration=True, encoding="UTF-8", standalone=True)
            if V44A.exists():
                V44A.unlink()
            with zipfile.ZipFile(V44A, "w", zipfile.ZIP_DEFLATED) as z:
                for path in (tmp2 / "src").rglob("*"):
                    if path.is_file():
                        z.write(path, path.relative_to(tmp2 / "src"))
            print(f"✓ {V44A.name} ({V44A.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
