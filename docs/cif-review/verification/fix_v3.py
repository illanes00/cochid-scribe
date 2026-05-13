"""Fix v3: sacar "(Propuesta IA)" del autor + arreglar estilos de párrafos que quedaron como Heading incorrectamente.

Problema detectado:
1. 52 tracked changes tienen autor "Martín Illanes (Propuesta IA)" (del v2 original). → Cambiar a "Martín Illanes" simple.
2. Los párrafos insertados por los agentes heredaron estilo Heading1/Heading2 del anchor, poblando el índice.
   Hay que cambiar a "Normal" todos los párrafos de cuerpo que tienen Heading style:
   - Para 849, 850 (Cap 7.13 cuerpo - Heading1)
   - Para 861-865 (Cap 8.3 contenido - Heading2) — excepto el título que SÍ debe quedar Heading2
   - Para 869-877 (Cap 8.4 preguntas - Heading1) — excepto el título 8.4 que SÍ debe quedar Heading2

Input: informe-final-v3.docx
Output: informe-final-v3.1.docx (misma carpeta)
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

V3 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.docx")
V31 = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.1.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


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


def is_true_heading_title(text):
    """Identifica si un texto es un título real (empieza con número de sección).

    Ejemplos true: "7.13 Síntesis", "8.3 Clasificación", "8.4 Preguntas", "9 Bibliografía"
    Ejemplos false: "Las medidas analizadas...", "1. Viabilidad política. ¿Qué...", "El desarrollo detallado..."
    """
    text = text.strip()
    if not text:
        return False
    # Match: digit(s), optionally .digit(s), optionally tab or whitespace, then short title text
    m = re.match(r"^(\d+(?:\.\d+)*)[\s\t]", text)
    if m:
        rest = text[len(m.group(0)):].strip()
        # A real heading title is short (<80 chars) and doesn't end with period
        if len(rest) < 80 and not rest.endswith("."):
            return True
        # Also accept titles ending with colon
        if len(rest) < 100 and rest.endswith(":"):
            return True
    # Also allow titles that don't start with number (anexos, bibliografía, etc.)
    # but only if they are short
    if len(text) < 80 and not text.endswith("."):
        # Must start with capital letter and not be a question or enumeration item
        if text[0].isupper() and not text.startswith(("¿", "-", "•", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            # Short unambiguous titles
            if any(text.startswith(kw) for kw in ["Anexo", "Bibliografía", "Tabla ", "Figura ", "Tarjeta ", "Índice", "Resumen", "Mensajes"]):
                return True
    return False


def process_docx():
    if V31.exists():
        V31.unlink()
    shutil.copy(V3, V31)
    print(f"Copied: {V3.name} -> {V31.name}")

    with zipfile.ZipFile(V31, "r") as z:
        doc_xml = z.read("word/document.xml")
        comments_xml = z.read("word/comments.xml") if "word/comments.xml" in z.namelist() else None

    # === 1. Replace author "(Propuesta IA)" ===
    # Do it at bytes level first (simplest)
    old_author = b'w:author="Mart\xc3\xadn Illanes (Propuesta IA)"'
    new_author = b'w:author="Mart\xc3\xadn Illanes"'
    count_doc = doc_xml.count(old_author)
    doc_xml = doc_xml.replace(old_author, new_author)
    print(f"  ✓ Replaced {count_doc} '(Propuesta IA)' authors in document.xml")

    count_com = 0
    if comments_xml:
        count_com = comments_xml.count(old_author)
        comments_xml = comments_xml.replace(old_author, new_author)

        # También em dashes en comments
        comments_tree = etree.fromstring(comments_xml)
        em_dash_comm = 0
        for t in comments_tree.iter(qn("t")):
            if _is_inside_del(t):
                continue
            original = t.text
            if not original or "—" not in original:
                continue
            new_text = re.sub(r"—([^—]{1,120})—", r"(\1)", original)
            new_text = re.sub(r"\s*—\s*", ", ", new_text)
            new_text = re.sub(r",\s*,", ",", new_text)
            if new_text != original:
                em_dash_comm += 1
                t.text = new_text
        comments_xml = etree.tostring(comments_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

        print(f"  ✓ Replaced {count_com} '(Propuesta IA)' authors in comments.xml")
        print(f"  ✓ Replaced em dashes in {em_dash_comm} <w:t> nodes in comments.xml")

    # === 1.5 Replace em dashes with commas / parentheses ===
    # Estrategia: para cada <w:t> (fuera de <w:del>), reemplazar:
    #   "—texto—" → "(texto)"  (pares cerrados)
    #   "— " o " —" → ","       (individuales)
    # Aplicado directo (no tracked) porque es corrección ortotipográfica global.
    doc_tree = etree.fromstring(doc_xml)
    body = doc_tree.find(qn("body"))

    em_dash_count = 0
    for t in body.iter(qn("t")):
        if _is_inside_del(t):
            continue
        original = t.text
        if not original or "—" not in original:
            continue
        # Paréntesis para pares: —texto de hasta ~100 chars sin — interno—
        new_text = re.sub(r"—([^—]{1,120})—", r"(\1)", original)
        # Restantes: em dash individual → coma. Mantener espacios.
        # Caso " — " (con espacios) → ", "
        new_text = re.sub(r"\s*—\s*", ", ", new_text)
        # Remover doble coma/espacio si quedara
        new_text = re.sub(r",\s*,", ",", new_text)
        new_text = re.sub(r",+", ",", new_text)

        if new_text != original:
            em_dash_count += 1
            t.text = new_text

    print(f"  ✓ Replaced em dashes in {em_dash_count} <w:t> nodes")

    # === 2. Fix Heading style on body paragraphs ===

    fixed_headings = 0
    kept_headings = 0

    # Estrategia correcta: solo cambiar estilo en párrafos NUEVOS (insertados por los agentes).
    # Un párrafo insertado se identifica porque tiene <w:ins .../> dentro de pPr/rPr (marca de
    # "paragraph-mark inserted"). Los párrafos originales mantienen su estilo intacto.
    def is_inserted_paragraph(p):
        pPr = p.find(qn("pPr"))
        if pPr is None:
            return False
        rPr = pPr.find(qn("rPr"))
        if rPr is None:
            return False
        return rPr.find(qn("ins")) is not None

    for i, p in enumerate(body.findall(qn("p"))):
        pPr = p.find(qn("pPr"))
        if pPr is None:
            continue
        pStyle = pPr.find(qn("pStyle"))
        if pStyle is None:
            continue
        style_val = pStyle.get(qn("val"))
        if not style_val or not style_val.startswith("Heading"):
            continue

        # Solo actuar si es un párrafo insertado (nuevo)
        if not is_inserted_paragraph(p):
            kept_headings += 1
            continue

        text = get_para_text(p).strip()
        if not text:
            continue

        # Si es un título real nuevo (ej. "7.13 Síntesis", "8.3 Clasificación", "8.4 Preguntas"),
        # mantener el Heading
        if is_true_heading_title(text) and len(text) < 80:
            kept_headings += 1
            continue

        # Párrafo nuevo con estilo Heading pero contenido largo → fix a Normal
        pPr.remove(pStyle)
        fixed_headings += 1
        print(f"  ✓ Para {i} (insertado): Heading→Normal (text: {text[:80]}...)")

    print(f"\n  Summary headings: kept {kept_headings} real titles, fixed {fixed_headings} malformed heading-style paragraphs")

    new_doc_xml = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    # === 3. Write back ===
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V31, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml" and comments_xml is not None:
                    zout.writestr(item, comments_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V31)

    print(f"\nOutput: {V31}")
    print(f"Size: {V31.stat().st_size:,} bytes")


def main():
    process_docx()


if __name__ == "__main__":
    main()
