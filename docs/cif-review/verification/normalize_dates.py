"""Normaliza TODAS las fechas de tracked changes y comments de Martín Illanes a
2026-01-01T00:00:00Z, para ocultar cronología de edición.

Afecta:
- <w:ins w:date="..." />
- <w:del w:date="..." />
- <w:comment w:date="..." />
- <w:pPr>/<w:rPr>/<w:ins w:date="..." /> (paragraph insertion marks)

Solo cambia fechas del autor "Martín Illanes". NO modifica fechas de otros autores
(Eduardo Undurraga, Carla Castillo, CIF, etc.).

Input: v3.14a.docx
Output: in-place (v3.14a.docx actualizado)
"""

from __future__ import annotations
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

V314A = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.14a.docx")

NEW_DATE = "2026-01-01T00:00:00Z"
AUTHOR_UTF8 = 'Mart\xc3\xadn Illanes'  # UTF-8 encoded as bytes


def normalize_dates_in_xml(xml_bytes: bytes) -> tuple[bytes, int]:
    """Replace w:date within elements that have w:author='Martín Illanes'.
    Works at bytes level with regex for speed and safety.
    """
    # Find patterns like: w:author="Martín Illanes" w:date="...Z"
    # Two orderings possible: author before date, or date before author.
    # Pattern 1: date AFTER author
    pattern1 = re.compile(
        rb'(w:author="Mart\xc3\xadn Illanes")\s+w:date="[^"]*"',
        re.DOTALL,
    )
    # Pattern 2: date BEFORE author
    pattern2 = re.compile(
        rb'w:date="[^"]*"(\s+w:author="Mart\xc3\xadn Illanes")',
        re.DOTALL,
    )

    count = 0
    new_date = NEW_DATE.encode("utf-8")

    def repl1(m):
        nonlocal count
        count += 1
        return m.group(1) + b' w:date="' + new_date + b'"'

    def repl2(m):
        nonlocal count
        count += 1
        return b'w:date="' + new_date + b'"' + m.group(1)

    out = pattern1.sub(repl1, xml_bytes)
    out = pattern2.sub(repl2, out)
    return out, count


def process():
    with zipfile.ZipFile(V314A, "r") as z:
        doc_xml = z.read("word/document.xml")
        com_xml = z.read("word/comments.xml") if "word/comments.xml" in z.namelist() else None

    new_doc_xml, count_doc = normalize_dates_in_xml(doc_xml)
    print(f"  Document.xml: {count_doc} fechas normalizadas a {NEW_DATE}")

    new_com_xml = None
    count_com = 0
    if com_xml:
        new_com_xml, count_com = normalize_dates_in_xml(com_xml)
        print(f"  Comments.xml: {count_com} fechas normalizadas a {NEW_DATE}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    with zipfile.ZipFile(V314A, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                if item == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item == "word/comments.xml" and new_com_xml is not None:
                    zout.writestr(item, new_com_xml)
                else:
                    zout.writestr(item, zin.read(item))

    shutil.move(tmp_path, V314A)
    print(f"\n  Total: {count_doc + count_com} fechas normalizadas")
    print(f"  Archivo actualizado: {V314A}")


if __name__ == "__main__":
    process()
