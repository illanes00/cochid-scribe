#!/usr/bin/env python3
"""
Enrich documents with claims detection and structure slides.
Works without external APIs using pattern matching.
"""
import json
import hashlib
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
    # Year ranges without prepositions: "2018-2022", "2022–2023"
    r'\b\d{4}\s*[-–]\s*\d{4}\b',
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
    lines = (text or "").splitlines()
    skip_section_level: int | None = None
    skip_section = False
    skip_keywords = ("referencias", "bibliografía", "fuentes", "anexo")

    # Extract candidate text blocks while skipping markdown tables/headings
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue

        # Headings: manage skip sections (references/annex)
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            heading_text = stripped[level:].strip().lower()
            if any(k in heading_text for k in skip_keywords):
                skip_section = True
                skip_section_level = level
            elif skip_section and skip_section_level is not None and level <= skip_section_level:
                # Leaving references/annex section
                skip_section = False
                skip_section_level = None
            i += 1
            continue

        if skip_section:
            i += 1
            continue
        if stripped == "---":
            i += 1
            continue

        # Skip markdown table blocks entirely (claims should be captured in narrative bullets)
        if "|" in stripped and i + 1 < len(lines) and is_markdown_table_separator(lines[i + 1]):
            i += 2  # skip header + separator
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                i += 1
            continue

        # Bullet/ordered list items are good atomic claim candidates
        if stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append(stripped[2:].strip())
            i += 1
            continue
        if re.match(r"^\d+\. ", stripped):
            blocks.append(re.sub(r"^\d+\. ", "", stripped).strip())
            i += 1
            continue

        # Paragraph block: collect contiguous non-empty lines until a structural boundary
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if nxt.startswith("#") or nxt == "---":
                break
            if nxt.startswith("- ") or nxt.startswith("* ") or re.match(r"^\d+\. ", nxt):
                break
            if "|" in nxt and i + 1 < len(lines) and is_markdown_table_separator(lines[i + 1]):
                break
            if nxt.startswith("|"):
                break
            para_lines.append(nxt)
            i += 1

        blocks.append(" ".join(para_lines).strip())

    # Split blocks into sentences (keeps bullets atomic while splitting paragraphs)
    sentences: list[str] = []
    for block in blocks:
        # Protect common abbreviations that contain a dot and shouldn't split sentences
        safe_block = re.sub(r"\bvs\.\s*", "vs ", block, flags=re.IGNORECASE)
        for sentence in re.split(r"[.!?]\s+", safe_block):
            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)

    for sentence in sentences:
        if len(sentence) < 20:
            continue

        # Avoid labeling section headers as claims (colons typically introduce lists/tables)
        if sentence.endswith(":"):
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
        has_digit = bool(re.search(r"\d", sentence))

        if has_pattern or (has_keyword and has_digit):
            claims.append({
                "text": sentence[:500],  # Limit length
                "type": claim_type,
                "confidence": 0.8 if has_pattern and has_keyword else 0.6
            })

    return claims


def normalize_for_match(text: str) -> str:
    """Normalize text for loose matching (strip markdown emphasis, collapse whitespace)."""
    text = (text or "").lower()
    text = re.sub(r"[*_`]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_for_match_loose(text: str) -> str:
    """More permissive normalization for matching text spans (keeps claim_id stability)."""
    text = normalize_for_match(text)
    # Drop most punctuation so minor formatting changes don't break matches
    text = re.sub(r"[^\w\s%$]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def stable_claim_id(doc_slug: str, claim_text: str) -> str:
    """Stable claim_id per document, derived from normalized text."""
    payload = f"{doc_slug}|{normalize_for_match(claim_text)}".encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest()[:12]
    return f"C-{digest}"


def is_markdown_table_separator(line: str) -> bool:
    """Return True if line looks like a markdown table separator row."""
    if "|" not in line:
        return False
    candidate = line.strip().replace("|", "").strip()
    if not candidate:
        return False
    # Typical separator contains only dashes/colons/spaces
    return "-" in candidate and set(candidate) <= set("-: ")


def split_markdown_table_row(line: str) -> list[str]:
    """Split a markdown table row into cell strings."""
    # Remove leading/trailing pipes, then split
    raw = line.strip().strip("|")
    return [cell.strip() for cell in raw.split("|")]


def create_table(headers: list[str], rows: list[list[str]]) -> dict:
    """Create a TipTap table node from header + rows."""
    max_cols = max(
        len(headers),
        max((len(r) for r in rows), default=0),
    )
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

    # Build a map of claim texts to stable IDs (provided by caller)
    claim_map: dict[str, str] = {}
    for claim in claims:
        claim_text = str(claim.get("text") or "").strip()
        claim_id = str(claim.get("claim_id") or "").strip()
        if not claim_text or not claim_id:
            continue
        key = normalize_for_match_loose(claim_text)[:80]
        if key:
            claim_map[key] = claim_id

    def match_claim_id(text: str) -> str | None:
        candidate = normalize_for_match_loose(text)
        if not candidate:
            return None
        for key, cid in claim_map.items():
            if key and key in candidate:
                return cid
        return None

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
            content.append(
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [create_paragraph(item, match_claim_id(item))],
                        }
                        for item in list_items
                    ],
                }
            )
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
                    {"type": "listItem", "content": [create_paragraph(item, match_claim_id(item))]}
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

        # Tables (markdown pipes) -> TipTap table nodes
        if (
            "|" in line
            and i + 1 < len(lines)
            and is_markdown_table_separator(lines[i + 1])
        ):
            header_cells = split_markdown_table_row(line)
            i += 2  # skip header + separator
            row_cells: list[list[str]] = []
            while i < len(lines):
                row_line = lines[i].rstrip()
                if not row_line.strip():
                    break
                if "|" not in row_line:
                    break
                row_cells.append(split_markdown_table_row(row_line))
                i += 1
            content.append(create_table(header_cells, row_cells))
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
            content.append(create_paragraph(para_text, match_claim_id(para_text)))

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

        # Map to layouts supported by the UI
        if first_line.startswith("# ") and len(lines) <= 5:
            layout = "title"
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


def extract_title_from_markdown(markdown: str, fallback: str) -> str:
    """Extract a reasonable document title from the first markdown heading."""
    text = (markdown or "").strip()
    if text.startswith("---"):
        end_idx = text.find("---", 3)
        if end_idx > 0:
            text = text[end_idx + 3 :].strip()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def ensure_document(slug: str, title: str, doc_type: str, conn: sqlite3.Connection) -> str:
    """Ensure a document row exists for a slug; returns document id."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM documents WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    if row:
        return row[0]

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat(sep=" ")
    empty_doc = {"type": "doc", "content": []}
    content = json.dumps({"json": empty_doc, "html": ""})
    cursor.execute(
        """
        INSERT INTO documents
            (id, slug, title, doc_type, content, markdown, front_matter, version, status, created_at, updated_at, source_provider, source_id)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            slug,
            title,
            doc_type,
            content,
            "",
            json.dumps({}),
            "1.0.0",
            "final",
            now,
            now,
            None,
            None,
        ),
    )
    return doc_id


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

    # Assign stable claim IDs so marks match stored claim records
    for claim in claims:
        claim["claim_id"] = stable_claim_id(slug, claim.get("text") or "")

    # Convert to TipTap with claims marked
    tiptap_json = markdown_to_tiptap_with_claims(markdown, claims)

    # Update document content + markdown
    content = json.dumps({"json": tiptap_json, "html": ""})
    cursor.execute(
        "UPDATE documents SET content = ?, markdown = ?, doc_type = ?, updated_at = ? WHERE slug = ?",
        (content, markdown, "policy", datetime.utcnow().isoformat(sep=" "), slug),
    )

    # Create claim records
    cursor.execute("SELECT id FROM documents WHERE slug = ?", (slug,))
    doc_row = cursor.fetchone()
    if doc_row:
        doc_id = doc_row[0]
        # Cache existing fields so we can preserve manual work and ids
        cursor.execute(
            "SELECT id, claim_id, status, evidence, source_sentences, created_at FROM claims WHERE document_id = ?",
            (doc_id,),
        )
        existing = {
            row[1]: {
                "id": row[0],
                "status": row[2] or "draft",
                "evidence": row[3] or json.dumps([]),
                "source_sentences": row[4] or json.dumps([]),
                "created_at": row[5] or datetime.utcnow().isoformat(),
            }
            for row in cursor.fetchall()
        }

        detected_ids: set[str] = set()
        for claim in claims:
            claim_id = claim["claim_id"]
            detected_ids.add(claim_id)
            prev = existing.get(claim_id) or {}
            claim_db_id = prev.get("id") or str(uuid.uuid4())
            created_at = prev.get("created_at") or datetime.utcnow().isoformat()
            status = prev.get("status") or "draft"
            evidence = prev.get("evidence") or json.dumps([])
            source_sentences = prev.get("source_sentences") or json.dumps([])

            cursor.execute(
                """
                INSERT INTO claims
                    (id, claim_id, document_id, claim_text, claim_type, status, evidence, source_sentences, created_at, updated_at)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(claim_id) DO UPDATE SET
                    document_id = excluded.document_id,
                    claim_text = excluded.claim_text,
                    claim_type = excluded.claim_type,
                    updated_at = excluded.updated_at
                """,
                (
                    claim_db_id,
                    claim_id,
                    doc_id,
                    claim["text"][:500],
                    claim["type"],
                    status,
                    evidence,
                    source_sentences,
                    created_at,
                    datetime.utcnow().isoformat(),
                ),
            )

        # Prune stale auto-detected claims (keeps verified/manual ones)
        if detected_ids:
            placeholders = ",".join("?" for _ in detected_ids)
            cursor.execute(
                f"""
                DELETE FROM claims
                WHERE document_id = ?
                  AND status = 'draft'
                  AND claim_id NOT IN ({placeholders})
                """,
                (doc_id, *sorted(detected_ids)),
            )

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
    cursor.execute(
        """
        UPDATE documents
        SET content = ?, markdown = ?, doc_type = ?, front_matter = ?, updated_at = ?
        WHERE slug = ?
    """,
        (
            content,
            markdown,
            "presentation",
            json.dumps({"slides_data": slides_data}),
            datetime.utcnow().isoformat(sep=" "),
            slug,
        ),
    )

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
        "cif-medicamentos-presentacion": "cif-medicamentos-presentacion.md",
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
        ensure_document(
            slug,
            extract_title_from_markdown(markdown, slug),
            "policy",
            conn,
        )
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
        ensure_document(
            slug,
            extract_title_from_markdown(markdown, slug),
            "presentation",
            conn,
        )
        slides_count = process_presentation(slug, markdown, conn)
        print(f"  OK: {slides_count} slides structured")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("Done! Documents enriched with claims and slide structure.")
    print("=" * 60)


if __name__ == "__main__":
    main()
