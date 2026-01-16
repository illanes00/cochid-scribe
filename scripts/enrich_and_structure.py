#!/usr/bin/env python3
"""
Enrich documents with claims detection and structure slides.
Works without external APIs using pattern matching.
"""
import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/srv/projects/illanes00-scribe/backend/scribe.db")
DOCS_DIR = Path("/srv/projects/illanes00-scribe/docs")

# Patterns for detecting claims (verifiable statements with data)
CLAIM_PATTERNS = [
    # Percentages: "61% de la población", "aumentaron 23,5%"
    r'(\d+[,.]?\d*)\s*%',
    # Currency amounts: "$4,47 billones", "US$511"
    r'[\$US]+\s*[\d,.]+(?: billones| millones| mil)?',
    # Years with data: "en 2024", "2018-2022"
    r'(?:en|desde|hasta|entre)\s+\d{4}(?:\s*[-–]\s*\d{4})?',
    # Numeric comparisons: "de 4,7 a 6,7", "aumentó de X a Y"
    r'(?:de|desde)\s+[\d,.]+ (?:a|hasta) [\d,.]+',
    # Rankings/positions: "1,43% del PIB", "5,82% del gasto"
    r'[\d,.]+\s*%\s+del?\s+\w+',
]

# Keywords that indicate verifiable claims
CLAIM_KEYWORDS = [
    'según', 'muestra', 'indica', 'demuestra', 'evidencia',
    'datos', 'cifras', 'estadísticas', 'encuesta', 'estudio',
    'aumentó', 'disminuyó', 'creció', 'bajó', 'subió',
    'total', 'promedio', 'mediana', 'máximo', 'mínimo',
]


def detect_claims_in_text(text: str) -> list[dict]:
    """Detect claims using pattern matching."""
    claims = []
    sentences = re.split(r'[.!?]\s+', text)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue

        # Check for patterns
        has_pattern = False
        claim_type = "MIXED"

        for pattern in CLAIM_PATTERNS:
            if re.search(pattern, sentence):
                has_pattern = True
                if '$' in sentence or 'US' in sentence or 'billones' in sentence:
                    claim_type = "DATA"
                elif '%' in sentence or re.search(r'\d+[,.]?\d*', sentence):
                    claim_type = "DATA"
                break

        # Check for keywords
        has_keyword = any(kw in sentence.lower() for kw in CLAIM_KEYWORDS)

        if has_pattern or has_keyword:
            claims.append({
                "text": sentence[:500],  # Limit length
                "type": claim_type,
                "confidence": 0.8 if has_pattern and has_keyword else 0.6
            })

    return claims


def parse_inline_formatting(text: str) -> list:
    """Parse bold and italic formatting for TipTap."""
    nodes = []
    pattern = r'\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_'
    last_end = 0

    for match in re.finditer(pattern, text):
        if match.start() > last_end:
            plain = text[last_end:match.start()]
            if plain:
                nodes.append({"type": "text", "text": plain})

        if match.group(1):  # Bold
            nodes.append({
                "type": "text",
                "marks": [{"type": "bold"}],
                "text": match.group(1)
            })
        elif match.group(2) or match.group(3):  # Italic
            nodes.append({
                "type": "text",
                "marks": [{"type": "italic"}],
                "text": match.group(2) or match.group(3)
            })
        last_end = match.end()

    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            nodes.append({"type": "text", "text": remaining})

    if not nodes and text:
        nodes = [{"type": "text", "text": text}]

    return nodes


def create_heading(text: str, level: int) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": parse_inline_formatting(text)
    }


def create_paragraph(text: str, claim_id: str = None) -> dict:
    content = parse_inline_formatting(text)

    # If this is a claim, wrap content with claim mark
    if claim_id and content:
        for node in content:
            if node.get("type") == "text":
                marks = node.get("marks", [])
                marks.append({"type": "claim", "attrs": {"claimId": claim_id}})
                node["marks"] = marks

    return {"type": "paragraph", "content": content} if content else {"type": "paragraph"}


def create_bullet_list(items: list) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [create_paragraph(item)]}
            for item in items
        ]
    }


def markdown_to_tiptap_with_claims(markdown: str, claims: list[dict]) -> dict:
    """Convert markdown to TipTap JSON, marking detected claims."""
    content = []
    lines = markdown.split("\n")
    i = 0

    # Build a map of claim texts to IDs
    claim_map = {}
    for claim in claims:
        claim_id = f"C-{uuid.uuid4().hex[:10]}"
        claim_map[claim["text"][:100]] = claim_id  # Use first 100 chars as key

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
            content.append({
                "type": "orderedList",
                "content": [
                    {"type": "listItem", "content": [create_paragraph(item)]}
                    for item in list_items
                ]
            })
            continue

        # Blockquotes
        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            content.append({
                "type": "blockquote",
                "content": [create_paragraph(" ".join(quote_lines))]
            })
            continue

        # Horizontal rule / slide break
        if line == "---":
            content.append({"type": "horizontalRule"})
            i += 1
            continue

        # Code blocks
        if line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # Skip closing ```
            content.append({
                "type": "codeBlock",
                "content": [{"type": "text", "text": "\n".join(code_lines)}] if code_lines else []
            })
            continue

        # Tables (simplified - as paragraphs)
        if "|" in line:
            table_lines = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            content.append(create_paragraph(" | ".join([l.strip() for l in table_lines])))
            continue

        # Regular paragraph - check if it's a claim
        para_lines = []
        while i < len(lines):
            current = lines[i]
            if not current or current.startswith("#") or current.startswith("- ") or \
               current.startswith("* ") or current.startswith("> ") or current == "---" or \
               re.match(r"^\d+\. ", current) or current.startswith("```"):
                break
            para_lines.append(current)
            i += 1

        if para_lines:
            para_text = " ".join(para_lines)

            # Check if this paragraph matches a detected claim
            claim_id = None
            for claim_key, cid in claim_map.items():
                if claim_key in para_text[:150]:
                    claim_id = cid
                    break

            content.append(create_paragraph(para_text, claim_id))

    return {"type": "doc", "content": content}


def parse_presentation_slides(markdown: str) -> list[dict]:
    """Parse markdown presentation into slide structure."""
    # Remove YAML frontmatter
    if markdown.startswith("---"):
        end_idx = markdown.find("---", 3)
        if end_idx > 0:
            markdown = markdown[end_idx + 3:].strip()

    # Split by slide separator
    slides_raw = re.split(r'\n---+\n', markdown)

    slides = []
    for idx, slide_content in enumerate(slides_raw):
        slide_content = slide_content.strip()
        if not slide_content:
            continue

        # Determine slide layout based on content
        lines = slide_content.split("\n")
        first_line = lines[0] if lines else ""

        if first_line.startswith("# ") and len(lines) <= 5:
            layout = "title"
        elif "```" in slide_content:
            layout = "code"
        elif "|" in slide_content and "---" in slide_content:
            layout = "table"
        else:
            layout = "content"

        # Extract title from first heading
        title = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break
            elif line.startswith("## "):
                title = line[3:].strip()
                break

        slides.append({
            "id": f"slide-{idx + 1}",
            "slideNumber": idx + 1,
            "layout": layout,
            "title": title,
            "content": slide_content,
            "notes": ""
        })

    return slides


def process_policy_brief(slug: str, markdown: str, conn: sqlite3.Connection):
    """Process a policy brief document with claims detection."""
    cursor = conn.cursor()

    # Remove YAML frontmatter
    if markdown.startswith("---"):
        end_idx = markdown.find("---", 3)
        if end_idx > 0:
            markdown = markdown[end_idx + 3:].strip()

    # Detect claims
    claims = detect_claims_in_text(markdown)
    print(f"  Found {len(claims)} potential claims")

    # Convert to TipTap with claims marked
    tiptap_json = markdown_to_tiptap_with_claims(markdown, claims)

    # Update document content
    content = json.dumps({"json": tiptap_json, "html": ""})
    cursor.execute(
        "UPDATE documents SET content = ?, doc_type = ? WHERE slug = ?",
        (content, "policy", slug)
    )

    # Create claim records
    cursor.execute("SELECT id FROM documents WHERE slug = ?", (slug,))
    doc_row = cursor.fetchone()
    if doc_row:
        doc_id = doc_row[0]
        for claim in claims:
            claim_id = f"C-{uuid.uuid4().hex[:10]}"
            cursor.execute("""
                INSERT OR IGNORE INTO claims
                (id, claim_id, document_id, claim_text, claim_type, status, evidence, source_sentences, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                claim_id,
                doc_id,
                claim["text"][:500],
                claim["type"],
                "draft",
                json.dumps([]),
                json.dumps([]),
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))

    return len(claims)


def process_presentation(slug: str, markdown: str, conn: sqlite3.Connection):
    """Process a presentation document with slide structure."""
    cursor = conn.cursor()

    # Parse into slides
    slides = parse_presentation_slides(markdown)
    print(f"  Found {len(slides)} slides")

    # Convert full content to TipTap
    clean_md = markdown
    if clean_md.startswith("---"):
        end_idx = clean_md.find("---", 3)
        if end_idx > 0:
            clean_md = clean_md[end_idx + 3:].strip()

    # Simple TipTap conversion for the full content
    tiptap_json = markdown_to_tiptap_with_claims(clean_md, [])

    # Create slides_data JSON
    slides_data = {
        "slides": slides,
        "theme": {
            "primaryColor": "#1a365d",  # Espacio Público azul
            "secondaryColor": "#c53030",  # Rojo institucional
            "fontFamily": "IBM Plex Sans",
            "logoUrl": None
        }
    }

    # Update document
    content = json.dumps({"json": tiptap_json, "html": ""})
    cursor.execute("""
        UPDATE documents
        SET content = ?, doc_type = ?, front_matter = ?
        WHERE slug = ?
    """, (
        content,
        "presentation",
        json.dumps({"slides_data": slides_data}),
        slug
    ))

    return len(slides)


def main():
    # Document mappings
    POLICY_BRIEFS = {
        "bid-seguridad-resumen": "bid-resumen-ejecutivo.md",
        "cif-medicamentos": "cif-medicamentos-resumen.md",
    }

    PRESENTATIONS = {
        "bid-seguridad-presentacion": "bid-presentacion-final.md",
        "bid-seguridad-final": "bid-presentacion-mejorada.md",
    }

    conn = sqlite3.connect(str(DB_PATH))

    print("=" * 60)
    print("Processing Policy Briefs (with claims detection)")
    print("=" * 60)

    for slug, filename in POLICY_BRIEFS.items():
        filepath = DOCS_DIR / filename
        if not filepath.exists():
            print(f"SKIP: {filename} not found")
            continue

        print(f"\n{slug}:")
        markdown = filepath.read_text(encoding="utf-8")
        claims_count = process_policy_brief(slug, markdown, conn)
        print(f"  OK: {claims_count} claims detected")

    print("\n" + "=" * 60)
    print("Processing Presentations (with slide structure)")
    print("=" * 60)

    for slug, filename in PRESENTATIONS.items():
        filepath = DOCS_DIR / filename
        if not filepath.exists():
            print(f"SKIP: {filename} not found")
            continue

        print(f"\n{slug}:")
        markdown = filepath.read_text(encoding="utf-8")
        slides_count = process_presentation(slug, markdown, conn)
        print(f"  OK: {slides_count} slides structured")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("Done! Documents enriched with claims and slide structure.")
    print("=" * 60)


if __name__ == "__main__":
    main()
