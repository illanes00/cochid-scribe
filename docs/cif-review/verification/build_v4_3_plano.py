"""v4.3 PLANO: extrae todo el texto del informe sin formato visual.

Genera un .docx mínimo con todo el contenido (paragraphs, headings, tablas)
en orden. Sirve como baseline de texto para comparar diferencias contra
el v4.3 con formato (que puede haber perdido cosas en el upload).

NO incluye:
- Figuras (embebidas, no son texto)
- Estilos visuales (colores, fuentes especiales)

SÍ incluye:
- TODO el texto de cada párrafo, en orden
- Estilo Heading mantenido (para navegación)
- Tablas con sus celdas
- Captions de figuras (texto)

Salida: informe-final-v4.3-plano.docx
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def qn(tag: str) -> str:
    return f"{{{W}}}{tag}"


BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
SRC = BASE / "output/informe-final-v4.3-aceptada.docx"
OUT = BASE / "output/informe-final-v4.3-plano.docx"


def get_paragraph_text(p) -> str:
    """Extrae texto plano de un <w:p>, excluyendo <w:del> (tracked deletions)."""
    parts = []
    for elem in p.iter():
        if elem.tag != qn("t"):
            continue
        # Skip si está dentro de <w:del>
        cur = elem
        in_del = False
        while cur is not None:
            if cur.tag == qn("del"):
                in_del = True
                break
            cur = cur.getparent()
        if in_del:
            continue
        if elem.text:
            parts.append(elem.text)
        # Conservar tabs como separadores
        if elem.tag == qn("tab"):
            parts.append("\t")
    # Si hay <w:tab> dentro del párrafo, lo expandemos
    for tab in p.iter(qn("tab")):
        # Solo agregar si no está dentro de del
        cur = tab
        in_del = False
        while cur is not None:
            if cur.tag == qn("del"):
                in_del = True
                break
            cur = cur.getparent()
    return "".join(parts).strip()


def get_paragraph_style(p) -> str | None:
    pStyle = p.find(f".//{qn('pPr')}/{qn('pStyle')}")
    if pStyle is None:
        return None
    return pStyle.get(qn("val"))


def get_table_data(tbl) -> list[list[str]]:
    """Extrae filas/celdas de una tabla."""
    rows = []
    for tr in tbl.findall(qn("tr")):
        cells = []
        for tc in tr.findall(qn("tc")):
            # Cada celda tiene paragraphs
            cell_parts = []
            for p in tc.findall(qn("p")):
                t = get_paragraph_text(p)
                if t:
                    cell_parts.append(t)
            cells.append(" ".join(cell_parts))
        rows.append(cells)
    return rows


def main():
    print(f"=== build_v4_3_plano.py ===")
    print(f"SRC: {SRC.name}\n")

    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

    # Strategy: parse XML del SRC y construir un nuevo document.xml
    # con solo párrafos básicos. Mantenemos los pStyle de Heading1-6 para
    # navegación, pero sin runs decorados — runs vacíos minimalistas.

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shutil.copy2(SRC, tmp / "src.docx")
        with zipfile.ZipFile(tmp / "src.docx") as z:
            z.extractall(tmp / "src")

        doc_xml = tmp / "src/word/document.xml"
        tree = etree.parse(str(doc_xml))
        root = tree.getroot()
        body = root.find(qn("body"))

        # Recolectar elementos en orden (paragraphs y tablas)
        items = []  # list of dicts
        # iter(body): solo nivel directo (paragraphs y tablas hijas del body)
        for child in list(body):
            if child.tag == qn("p"):
                text = get_paragraph_text(child)
                style = get_paragraph_style(child)
                items.append({"kind": "p", "text": text, "style": style})
            elif child.tag == qn("tbl"):
                rows = get_table_data(child)
                items.append({"kind": "tbl", "rows": rows})
            elif child.tag == qn("sectPr"):
                continue
            # Otros (sdt, etc): inspeccionar paragraphs anidados
            else:
                for p in child.iter(qn("p")):
                    text = get_paragraph_text(p)
                    style = get_paragraph_style(p)
                    items.append({"kind": "p", "text": text, "style": style})

        print(f"Items recolectados: {len(items)}")
        n_p = sum(1 for i in items if i["kind"] == "p")
        n_t = sum(1 for i in items if i["kind"] == "tbl")
        n_h = sum(1 for i in items if i["kind"] == "p" and (i.get("style") or "").startswith("Heading"))
        n_text = sum(1 for i in items if i["kind"] == "p" and i.get("text"))
        print(f"  Párrafos: {n_p} ({n_text} con texto, {n_h} headings)")
        print(f"  Tablas: {n_t}")

        # ===== Construir nuevo document.xml =====
        # Crear estructura mínima
        nsmap = {
            "w": W,
            "xml": XML_NS,
        }
        new_root = etree.Element(qn("document"), nsmap={"w": W})
        new_body = etree.SubElement(new_root, qn("body"))

        for item in items:
            if item["kind"] == "p":
                p = etree.SubElement(new_body, qn("p"))
                pPr = etree.SubElement(p, qn("pPr"))
                # Mantener Heading style para navegación
                if item.get("style") and item["style"].startswith("Heading"):
                    pStyle = etree.SubElement(pPr, qn("pStyle"))
                    pStyle.set(qn("val"), item["style"])
                if item.get("text"):
                    r = etree.SubElement(p, qn("r"))
                    t = etree.SubElement(r, qn("t"))
                    t.set(f"{{{XML_NS}}}space", "preserve")
                    t.text = item["text"]
            elif item["kind"] == "tbl":
                # Tabla simple
                rows = item.get("rows", [])
                if not rows:
                    continue
                tbl = etree.SubElement(new_body, qn("tbl"))
                # tblPr básico
                tblPr = etree.SubElement(tbl, qn("tblPr"))
                tblStyle = etree.SubElement(tblPr, qn("tblStyle"))
                tblStyle.set(qn("val"), "TableGrid")
                tblW = etree.SubElement(tblPr, qn("tblW"))
                tblW.set(qn("w"), "0")
                tblW.set(qn("type"), "auto")
                # Borders
                tblBorders = etree.SubElement(tblPr, qn("tblBorders"))
                for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
                    b = etree.SubElement(tblBorders, qn(side))
                    b.set(qn("val"), "single")
                    b.set(qn("sz"), "4")
                    b.set(qn("space"), "0")
                    b.set(qn("color"), "auto")
                # tblGrid
                tblGrid = etree.SubElement(tbl, qn("tblGrid"))
                if rows[0]:
                    for _ in rows[0]:
                        etree.SubElement(tblGrid, qn("gridCol"))
                # Filas
                for row in rows:
                    tr = etree.SubElement(tbl, qn("tr"))
                    for cell_text in row:
                        tc = etree.SubElement(tr, qn("tc"))
                        tcPr = etree.SubElement(tc, qn("tcPr"))
                        tcW = etree.SubElement(tcPr, qn("tcW"))
                        tcW.set(qn("w"), "0")
                        tcW.set(qn("type"), "auto")
                        cell_p = etree.SubElement(tc, qn("p"))
                        if cell_text:
                            cell_r = etree.SubElement(cell_p, qn("r"))
                            cell_t = etree.SubElement(cell_r, qn("t"))
                            cell_t.set(f"{{{XML_NS}}}space", "preserve")
                            cell_t.text = cell_text

        # Preservar sectPr al final
        for child in list(body):
            if child.tag == qn("sectPr"):
                new_body.append(etree.fromstring(etree.tostring(child)))
                break

        # Reemplazar document.xml
        new_tree = etree.ElementTree(new_root)
        new_tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        # Re-zipear
        if OUT.exists():
            OUT.unlink()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))

        size = OUT.stat().st_size
        print(f"\n✓ {OUT.name} ({size:,} bytes)")

        # Reporte de palabras
        total_words = sum(len(i.get("text", "").split()) for i in items if i["kind"] == "p")
        print(f"  Palabras totales: {total_words:,}")


if __name__ == "__main__":
    main()
