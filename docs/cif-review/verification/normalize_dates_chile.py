"""Normaliza TODAS las fechas de Martín Illanes en un docx a 2026-01-01 00:00 Chile.

Cobertura:
- word/document.xml: <w:ins>, <w:del>, <w:pPrChange>, <w:rPrChange>
- word/comments.xml: <w:comment>
- word/footnotes.xml, word/endnotes.xml: w:date en nodos de notas
- word/people.xml: w:dateTime en reacciones

Formato final: 2026-01-01T00:00:00-03:00 (00:00 hora Chile Continental, verano).
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

AUTHOR_ENCODED = b'Mart\xc3\xadn Illanes'
NEW_DATE = b'2026-01-01T00:00:00-03:00'

# Files in the docx that may contain w:date or w:dateTime with author Martín Illanes
TARGET_FILES = (
    'word/document.xml',
    'word/comments.xml',
    'word/commentsExtended.xml',
    'word/commentsIds.xml',
    'word/footnotes.xml',
    'word/endnotes.xml',
    'word/people.xml',
)

# Matches w:author="Martín Illanes" followed by w:date="..."
PATTERN_AUTHOR_THEN_DATE = re.compile(
    rb'(w:author="' + AUTHOR_ENCODED + rb'"\s+w:date=")([^"]*)(")',
    re.DOTALL,
)
# Matches w:date="..." followed by w:author="Martín Illanes"
PATTERN_DATE_THEN_AUTHOR = re.compile(
    rb'(w:date=")([^"]*)("\s+w:author="' + AUTHOR_ENCODED + rb'")',
    re.DOTALL,
)
# Matches w:dateTime="..." followed by w:author="Martín Illanes" (reactions)
PATTERN_DATETIME_THEN_AUTHOR = re.compile(
    rb'(w:dateTime=")([^"]*)("\s+w:author="' + AUTHOR_ENCODED + rb'")',
    re.DOTALL,
)
PATTERN_AUTHOR_THEN_DATETIME = re.compile(
    rb'(w:author="' + AUTHOR_ENCODED + rb'"\s+w:dateTime=")([^"]*)(")',
    re.DOTALL,
)


def normalize_xml_bytes(xml_bytes: bytes) -> tuple[bytes, int]:
    count = 0

    def _repl_middle(m):
        nonlocal count
        count += 1
        return m.group(1) + NEW_DATE + m.group(3)

    xml_bytes = PATTERN_AUTHOR_THEN_DATE.sub(_repl_middle, xml_bytes)
    xml_bytes = PATTERN_DATE_THEN_AUTHOR.sub(_repl_middle, xml_bytes)
    xml_bytes = PATTERN_AUTHOR_THEN_DATETIME.sub(_repl_middle, xml_bytes)
    xml_bytes = PATTERN_DATETIME_THEN_AUTHOR.sub(_repl_middle, xml_bytes)
    return xml_bytes, count


def normalize_docx(src: Path, dst: Path):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpf:
        tmp_path = tmpf.name

    total = 0
    with zipfile.ZipFile(src, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                raw = zin.read(item)
                if item in TARGET_FILES:
                    new, count = normalize_xml_bytes(raw)
                    total += count
                    zout.writestr(item, new)
                else:
                    zout.writestr(item, raw)

    shutil.move(tmp_path, dst)
    print(f"Normalized {total} date fields in {dst.name}")
    return total


def main():
    if len(sys.argv) != 3:
        print("Usage: normalize_dates_chile.py input.docx output.docx")
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    normalize_docx(src, dst)


if __name__ == "__main__":
    main()
