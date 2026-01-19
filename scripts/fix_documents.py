#!/usr/bin/env python3
"""Fix document content - convert markdown to proper TipTap JSON."""
import json
import re
import sqlite3
from pathlib import Path

DOCS_DIR = Path("/srv/projects/illanes00-scribe/docs")
DB_PATH = Path("/srv/projects/illanes00-scribe/backend/scribe.db")

# Mapping of slugs to markdown files
SLUG_TO_FILE = {
    "bid-seguridad-resumen": "bid-resumen-ejecutivo.md",
    "bid-seguridad-presentacion": "bid-presentacion-final.md",
    "bid-seguridad-final": "bid-presentacion-mejorada.md",
    "cif-medicamentos": "cif-medicamentos-resumen.md",
}

def parse_inline_formatting(text):
    """Parse bold and italic formatting."""
    nodes = []
    pattern = r'\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_'
    last_end = 0
    for match in re.finditer(pattern, text):
        if match.start() > last_end:
            nodes.append({"type": "text", "text": text[last_end:match.start()]})
        if match.group(1):
            nodes.append({"type": "text", "marks": [{"type": "bold"}], "text": match.group(1)})
        elif match.group(2) or match.group(3):
            nodes.append({"type": "text", "marks": [{"type": "italic"}], "text": match.group(2) or match.group(3)})
        last_end = match.end()
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            nodes.append({"type": "text", "text": remaining})
    if not nodes:
        return [{"type": "text", "text": text}] if text else []
    return nodes

def create_heading(text, level):
    return {"type": "heading", "attrs": {"level": level}, "content": parse_inline_formatting(text)}

def create_paragraph(text):
    content = parse_inline_formatting(text)
    return {"type": "paragraph", "content": content} if content else {"type": "paragraph"}

def create_blockquote(text):
    return {"type": "blockquote", "content": [create_paragraph(text)]}

def create_bullet_list(items):
    return {"type": "bulletList", "content": [{"type": "listItem", "content": [create_paragraph(item)]} for item in items]}

def create_ordered_list(items):
    return {"type": "orderedList", "content": [{"type": "listItem", "content": [create_paragraph(item)]} for item in items]}

def is_markdown_table_separator(line: str) -> bool:
    if "|" not in line:
        return False
    candidate = line.strip().replace("|", "").strip()
    if not candidate:
        return False
    return "-" in candidate and set(candidate) <= set("-: ")

def split_markdown_table_row(line: str) -> list[str]:
    raw = line.strip().strip("|")
    return [cell.strip() for cell in raw.split("|")]

def create_table(headers: list[str], rows: list[list[str]]) -> dict:
    max_cols = max(len(headers), max((len(r) for r in rows), default=0))
    headers = (headers + [""] * max_cols)[:max_cols]
    normalized_rows = [(r + [""] * max_cols)[:max_cols] for r in rows]

    header_row = {
        "type": "tableRow",
        "content": [
            {"type": "tableHeader", "content": [create_paragraph(cell)]}
            for cell in headers
        ],
    }

    body_rows = []
    for row in normalized_rows:
        body_rows.append(
            {
                "type": "tableRow",
                "content": [
                    {"type": "tableCell", "content": [create_paragraph(cell)]}
                    for cell in row
                ],
            }
        )

    return {"type": "table", "content": [header_row, *body_rows]}

def markdown_to_tiptap(markdown):
    """Convert markdown to TipTap JSON format."""
    content = []
    lines = markdown.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line:
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            content.append(create_heading(line[2:], 1))
            i += 1
            continue
        elif line.startswith("## "):
            content.append(create_heading(line[3:], 2))
            i += 1
            continue
        elif line.startswith("### "):
            content.append(create_heading(line[4:], 3))
            i += 1
            continue

        # Blockquotes
        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            content.append(create_blockquote(" ".join(quote_lines)))
            continue

        # Bullet lists
        if line.startswith("- ") or line.startswith("* "):
            list_items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("* ")):
                list_items.append(lines[i][2:])
                i += 1
            content.append(create_bullet_list(list_items))
            continue

        # Ordered lists
        if re.match(r"^\d+\. ", line):
            list_items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                list_items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            content.append(create_ordered_list(list_items))
            continue

        # Horizontal rule
        if line == "---":
            content.append({"type": "horizontalRule"})
            i += 1
            continue

        # Markdown tables
        if "|" in line and i + 1 < len(lines) and is_markdown_table_separator(lines[i + 1]):
            headers = split_markdown_table_row(line)
            i += 2  # skip header + separator
            rows = []
            while i < len(lines):
                row_line = lines[i].rstrip()
                if not row_line.strip():
                    break
                if "|" not in row_line:
                    break
                rows.append(split_markdown_table_row(row_line))
                i += 1
            content.append(create_table(headers, rows))
            continue

        # Paragraph - collect lines until we hit something else
        para_lines = []
        while i < len(lines):
            current = lines[i]
            if not current:
                break
            if current.startswith("#"):
                break
            if "|" in current and i + 1 < len(lines) and is_markdown_table_separator(lines[i + 1]):
                break
            if current.startswith("- ") or current.startswith("* "):
                break
            if current.startswith("> "):
                break
            if current == "---":
                break
            if re.match(r"^\d+\. ", current):
                break
            para_lines.append(current)
            i += 1

        if para_lines:
            content.append(create_paragraph(" ".join(para_lines)))

    return {"type": "doc", "content": content}

def main():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    for slug, filename in SLUG_TO_FILE.items():
        filepath = DOCS_DIR / filename
        if not filepath.exists():
            print(f"SKIP: {filename} not found")
            continue

        markdown = filepath.read_text(encoding="utf-8")

        # Skip YAML frontmatter
        if markdown.startswith("---"):
            end_idx = markdown.find("---", 3)
            if end_idx > 0:
                markdown = markdown[end_idx + 3:].strip()

        tiptap_json = markdown_to_tiptap(markdown)
        content = json.dumps({"json": tiptap_json, "html": ""})

        cursor.execute("UPDATE documents SET content = ? WHERE slug = ?", (content, slug))
        node_count = len(tiptap_json.get("content", []))
        print(f"OK: {slug} updated ({len(markdown)} chars -> {node_count} nodes)")

    conn.commit()
    conn.close()
    print("Done!")

if __name__ == "__main__":
    main()
