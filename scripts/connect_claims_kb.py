#!/usr/bin/env python3
"""
Conecta Claims con Knowledge Base (Notas) creando notas por claim y vínculos en el grafo.

Objetivo:
- Para cada claim de un documento, crear/actualizar una Nota tipo "claim"
- Crear Link claim -> note y document -> note (trazabilidad y navegación)

Uso:
  python scripts/connect_claims_kb.py --db backend/scribe.db --docs cif-medicamentos bid-seguridad-resumen
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import uuid
from datetime import datetime


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def sanitize_inline(text: str) -> str:
    return (text or "").strip()


def parse_inline_formatting(text: str) -> list[dict]:
    """Parsea negrita e itálica a nodos TipTap."""
    nodes: list[dict] = []
    pattern = r"\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_"
    last_end = 0

    for match in re.finditer(pattern, text or ""):
        if match.start() > last_end:
            plain = (text or "")[last_end : match.start()]
            if plain:
                nodes.append({"type": "text", "text": plain})

        if match.group(1):  # bold
            nodes.append({"type": "text", "marks": [{"type": "bold"}], "text": match.group(1)})
        elif match.group(2) or match.group(3):  # italic
            nodes.append(
                {
                    "type": "text",
                    "marks": [{"type": "italic"}],
                    "text": match.group(2) or match.group(3),
                }
            )
        last_end = match.end()

    if last_end < len(text or ""):
        remaining = (text or "")[last_end:]
        if remaining:
            nodes.append({"type": "text", "text": remaining})

    if not nodes and text:
        nodes = [{"type": "text", "text": text}]
    return nodes


def create_paragraph(text: str) -> dict:
    content = parse_inline_formatting(sanitize_inline(text))
    return {"type": "paragraph", "content": content} if content else {"type": "paragraph"}


def create_heading(text: str, level: int) -> dict:
    return {"type": "heading", "attrs": {"level": level}, "content": parse_inline_formatting(text)}


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


def markdown_to_tiptap(markdown: str) -> dict:
    """Conversión minimalista Markdown -> TipTap JSON (suficiente para notas/claims)."""
    content: list[dict] = []
    lines = (markdown or "").split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue

        if line.startswith("# "):
            content.append(create_heading(line[2:], 1))
            i += 1
            continue
        if line.startswith("## "):
            content.append(create_heading(line[3:], 2))
            i += 1
            continue
        if line.startswith("### "):
            content.append(create_heading(line[4:], 3))
            i += 1
            continue

        if line == "---":
            content.append({"type": "horizontalRule"})
            i += 1
            continue

        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            content.append({"type": "blockquote", "content": [create_paragraph(" ".join(quote_lines))]})
            continue

        if line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            content.append(
                {
                    "type": "codeBlock",
                    "content": [{"type": "text", "text": "\n".join(code_lines)}] if code_lines else [],
                }
            )
            continue

        if line.startswith("- ") or line.startswith("* "):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("* ")):
                items.append(lines[i][2:])
                i += 1
            content.append(
                {
                    "type": "bulletList",
                    "content": [{"type": "listItem", "content": [create_paragraph(it)]} for it in items],
                }
            )
            continue

        if re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            content.append(
                {
                    "type": "orderedList",
                    "content": [{"type": "listItem", "content": [create_paragraph(it)]} for it in items],
                }
            )
            continue

        if "|" in line and i + 1 < len(lines) and is_markdown_table_separator(lines[i + 1]):
            headers = split_markdown_table_row(line)
            i += 2
            rows: list[list[str]] = []
            while i < len(lines):
                row_line = lines[i].rstrip()
                if not row_line.strip() or "|" not in row_line:
                    break
                rows.append(split_markdown_table_row(row_line))
                i += 1
            content.append(create_table(headers, rows))
            continue

        # Paragraph
        para_lines = []
        while i < len(lines):
            current = lines[i]
            if not current:
                break
            if current.startswith("#") or current.startswith("> ") or current == "---" or current.startswith("```"):
                break
            if current.startswith("- ") or current.startswith("* ") or re.match(r"^\d+\. ", current):
                break
            if "|" in current and i + 1 < len(lines) and is_markdown_table_separator(lines[i + 1]):
                break
            para_lines.append(current)
            i += 1
        if para_lines:
            content.append(create_paragraph(" ".join(para_lines)))

    return {"type": "doc", "content": content}


def note_slug_for_claim(claim_id: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", (claim_id or "").lower()).strip("-")
    return f"claim-{slug}" if slug else f"claim-{uuid.uuid4().hex[:8]}"


def note_title_for_claim(claim_id: str, claim_text: str) -> str:
    clean = re.sub(r"\s+", " ", (claim_text or "").strip())
    snippet = clean[:80] + ("…" if len(clean) > 80 else "")
    if snippet:
        return f"{claim_id} — {snippet}"
    return f"{claim_id}"


def build_claim_note_markdown(doc_title: str, doc_slug: str, claim: dict) -> str:
    claim_id = claim.get("claim_id") or ""
    claim_text = claim.get("claim_text") or ""
    claim_type = claim.get("claim_type") or ""
    status = claim.get("status") or ""
    section = claim.get("section") or ""

    lines = [
        f"# {claim_id}",
        "",
        f"**Documento**: {doc_title} (`{doc_slug}`)",
        f"**Tipo**: {claim_type} · **Estado**: {status}",
    ]
    if section:
        lines.append(f"**Sección**: {section}")
    lines.extend(
        [
            "",
            "## Texto del claim",
            "",
            claim_text.strip(),
            "",
            "## Evidencia",
            "",
            "- [ ] Agregar evidencia (fuente / dato / cita)",
            "",
            "## Notas",
            "",
            "- ",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def upsert_note(
    cursor: sqlite3.Cursor,
    slug: str,
    title: str,
    markdown: str,
    note_type: str,
    tags: list[str],
) -> str:
    cursor.execute("SELECT id FROM notes WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    note_id = row[0] if row else str(uuid.uuid4())

    tiptap = markdown_to_tiptap(markdown)
    content = json.dumps({"json": tiptap, "html": ""})

    if row:
        cursor.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, markdown = ?, note_type = ?, tags = ?, updated_at = ?
            WHERE slug = ?
            """,
            (title, content, markdown, note_type, json.dumps(tags), now_iso(), slug),
        )
    else:
        now = now_iso()
        cursor.execute(
            """
            INSERT INTO notes (id, slug, title, content, markdown, note_type, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note_id,
                slug,
                title,
                content,
                markdown,
                note_type,
                json.dumps(tags),
                now,
                now,
            ),
        )
    return note_id


def ensure_link(cursor: sqlite3.Cursor, source_type: str, source_id: str, target_type: str, target_id: str, link_type: str, context: str) -> None:
    cursor.execute(
        """
        SELECT id FROM links
        WHERE source_type = ? AND source_id = ? AND target_type = ? AND target_id = ? AND link_type = ?
        """,
        (source_type, source_id, target_type, target_id, link_type),
    )
    if cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO links (id, source_type, source_id, target_type, target_id, link_type, context, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            source_type,
            source_id,
            target_type,
            target_id,
            link_type,
            context or "",
            now_iso(),
        ),
    )


def reset_links_for_document(cursor: sqlite3.Cursor, doc_slug: str, doc_id: str) -> tuple[int, int]:
    """
    Remove previously generated links so re-runs don't accumulate stale references.

    Strategy:
    - claim -> note links created by this script use context=doc_slug
    - document -> note links created by this script use context=claim_id (typically starts with 'C-')
    """
    cursor.execute(
        """
        DELETE FROM links
        WHERE source_type='claim'
          AND target_type='note'
          AND link_type='reference'
          AND context=?
        """,
        (doc_slug,),
    )
    deleted_claim_links = cursor.rowcount or 0

    cursor.execute(
        """
        DELETE FROM links
        WHERE source_type='document'
          AND source_id=?
          AND target_type='note'
          AND link_type='reference'
          AND context LIKE 'C-%'
        """,
        (doc_id,),
    )
    deleted_doc_links = cursor.rowcount or 0

    return deleted_claim_links, deleted_doc_links


def prune_orphan_claim_notes(cursor: sqlite3.Cursor, doc_slug: str) -> int:
    """
    Remove auto-generated claim notes for a document that are no longer linked.

    Safety:
    - Only deletes notes tagged exactly as [doc_slug, 'claim']
    - Only deletes notes that appear untouched (updated_at == created_at)
    - Only deletes notes that are not referenced by any link (as source or target)
    """
    tags_json = json.dumps([doc_slug, "claim"])

    cursor.execute(
        "SELECT id, markdown, created_at, updated_at FROM notes WHERE note_type='claim' AND tags=?",
        (tags_json,),
    )
    candidates = cursor.fetchall()
    if not candidates:
        return 0

    cursor.execute("SELECT DISTINCT target_id FROM links WHERE target_type='note'")
    linked = {row[0] for row in cursor.fetchall()}
    cursor.execute("SELECT DISTINCT source_id FROM links WHERE source_type='note'")
    linked |= {row[0] for row in cursor.fetchall()}

    deleted = 0
    template_re = re.compile(
        r"## Evidencia\s*\n\s*-\s*\[\s*\]\s*Agregar evidencia \(fuente / dato / cita\)\s*\n\s*## Notas\s*\n\s*-\s*\n\s*$",
        re.IGNORECASE | re.DOTALL,
    )
    for note_id, markdown, created_at, updated_at in candidates:
        if note_id in linked:
            continue

        md = markdown or ""
        if "- [ ] Agregar evidencia (fuente / dato / cita)" not in md:
            continue
        # Only delete notes that still match the untouched template (safer default)
        if not template_re.search(md):
            continue

        cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
        deleted += 1

    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="backend/scribe.db", help="Ruta a SQLite (scribe.db)")
    parser.add_argument(
        "--docs",
        nargs="+",
        default=["cif-medicamentos", "bid-seguridad-resumen"],
        help="Slugs de documentos a procesar",
    )
    parser.add_argument(
        "--reset-links",
        action="store_true",
        help="Elimina links previos (claim↔nota/document↔nota) para evitar duplicados",
    )
    parser.add_argument(
        "--prune-orphans",
        action="store_true",
        help="Elimina notas de claims huérfanas (solo auto-generadas y sin edición)",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()

    total_notes = 0
    total_links = 0

    for doc_slug in args.docs:
        cursor.execute("SELECT id, title FROM documents WHERE slug = ?", (doc_slug,))
        row = cursor.fetchone()
        if not row:
            print(f"SKIP: documento no encontrado: {doc_slug}")
            continue
        doc_id, doc_title = row

        if args.reset_links:
            deleted_claim_links, deleted_doc_links = reset_links_for_document(cursor, doc_slug, doc_id)
            if deleted_claim_links or deleted_doc_links:
                print(
                    f"{doc_slug}: reset links (claim→note: {deleted_claim_links}, document→note: {deleted_doc_links})"
                )

        cursor.execute(
            "SELECT id, claim_id, claim_text, claim_type, status, section FROM claims WHERE document_id = ? ORDER BY created_at ASC",
            (doc_id,),
        )
        claims = cursor.fetchall()
        print(f"{doc_slug}: {len(claims)} claims")

        for claim_db_id, claim_id, claim_text, claim_type, status, section in claims:
            note_slug = note_slug_for_claim(claim_id)
            note_title = note_title_for_claim(claim_id, claim_text)
            markdown = build_claim_note_markdown(
                doc_title=doc_title,
                doc_slug=doc_slug,
                claim={
                    "claim_id": claim_id,
                    "claim_text": claim_text,
                    "claim_type": claim_type,
                    "status": status,
                    "section": section,
                },
            )

            note_id = upsert_note(
                cursor,
                slug=note_slug,
                title=note_title,
                markdown=markdown,
                note_type="claim",
                tags=[doc_slug, "claim"],
            )
            total_notes += 1

            ensure_link(
                cursor,
                source_type="claim",
                source_id=claim_db_id,
                target_type="note",
                target_id=note_id,
                link_type="reference",
                context=doc_slug,
            )
            ensure_link(
                cursor,
                source_type="document",
                source_id=doc_id,
                target_type="note",
                target_id=note_id,
                link_type="reference",
                context=claim_id,
            )
            total_links += 2

        if args.prune_orphans:
            deleted_notes = prune_orphan_claim_notes(cursor, doc_slug)
            if deleted_notes:
                print(f"{doc_slug}: pruned orphan claim notes: {deleted_notes}")

    conn.commit()
    conn.close()

    print(f"OK: notas creadas/actualizadas: {total_notes}")
    print(f"OK: links asegurados: {total_links}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
