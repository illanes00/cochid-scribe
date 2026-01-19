"""Helpers to extract and maintain content links."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.bibliography import BibliographyEntry
from app.models.note import Link, Note

WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
QUOTE_RE = re.compile(r'"([^"]+)"')
BIB_KEY_RE = re.compile(r'data-bib-key="([^"]+)"')


def extract_wiki_links(text: str) -> list[str]:
    """Extract wiki-style links like [[slug]]."""
    return [match.strip() for match in WIKI_LINK_RE.findall(text or "") if match.strip()]


def extract_citation_keys(html: str) -> list[str]:
    """Extract citation keys from rendered HTML."""
    return [match.strip() for match in BIB_KEY_RE.findall(html or "") if match.strip()]


def extract_links_from_json(content: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Extract wiki links and citation keys from Tiptap JSON content."""
    links: list[str] = []
    citations: list[str] = []

    def traverse(node: Any) -> None:
        if isinstance(node, dict):
            node_type = node.get("type")
            if node_type == "text" and node.get("text"):
                links.extend(extract_wiki_links(node["text"]))
            if node_type == "citation":
                bib_key = node.get("attrs", {}).get("bibKey")
                if bib_key:
                    citations.append(str(bib_key))
            for child in node.get("content", []):
                traverse(child)

    traverse(content or {})
    return links, citations


def update_document_links(
    db: Session,
    source_id: str,
    source_type: str,
    content_json: dict[str, Any] | None,
    content_html: str | None,
) -> None:
    """Update Link rows for a document or note."""
    db.query(Link).filter(Link.source_type == source_type, Link.source_id == source_id).delete()

    wiki_links: list[str] = []
    citation_keys: list[str] = []
    if content_json:
        wiki_links, citation_keys = extract_links_from_json(content_json)
    if not wiki_links and content_html:
        wiki_links = extract_wiki_links(content_html)

    for linked_slug in wiki_links:
        target_note = db.query(Note).filter(Note.slug == linked_slug).first()
        if target_note:
            db.add(
                Link(
                    source_type=source_type,
                    source_id=source_id,
                    target_type="note",
                    target_id=target_note.id,
                    link_type="reference",
                )
            )

    if source_type == "document":
        html_keys = extract_citation_keys(content_html or "")
        for bib_key in list(set(html_keys + citation_keys)):
            entry = db.query(BibliographyEntry).filter(BibliographyEntry.bib_key == bib_key).first()
            if entry:
                db.add(
                    Link(
                        source_type="document",
                        source_id=source_id,
                        target_type="bib",
                        target_id=entry.id,
                        link_type="citation",
                    )
                )

    db.commit()
