"""Export document review as formatted HTML for PDF generation.

Generates a two-column A3/tabloid layout:
- Left: Document with inline highlights for changes, claims, and citations
- Right: Comments, track changes, and bibliography with links

Output is HTML that can be printed to PDF via browser or converted via weasyprint.
"""

from __future__ import annotations

import html
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.bibliography import BibliographyEntry
from app.models.claim import Claim
from app.models.comment import Comment
from app.models.document import Document
from app.models.track_change import TrackChange


def generate_review_html(db: Session, slug: str) -> str:
    """Generate a full review document as printable HTML."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise ValueError(f"Document '{slug}' not found")

    # Gather all data
    comments = (
        db.query(Comment)
        .filter(Comment.document_id == doc.id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    root_comments = [c for c in comments if not c.parent_id]
    replies_map: dict[str, list[Comment]] = {}
    for c in comments:
        if c.parent_id:
            replies_map.setdefault(c.parent_id, []).append(c)

    changes = (
        db.query(TrackChange)
        .filter(TrackChange.document_id == doc.id)
        .order_by(TrackChange.created_at.asc())
        .all()
    )

    claims = db.query(Claim).filter(Claim.document_id == doc.id).all()

    bibliography = db.query(BibliographyEntry).all()

    # Build HTML
    md = doc.markdown or ""
    doc_html = _markdown_to_html(md)

    comments_html = _build_comments_html(root_comments, replies_map)
    changes_html = _build_changes_html(changes)
    claims_html = _build_claims_html(claims)
    bib_html = _build_bibliography_html(bibliography)

    # Stats
    resolved = sum(1 for c in root_comments if c.resolved)
    pending = len(root_comments) - resolved
    pending_changes = sum(1 for c in changes if c.status.value == "pending")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Review: {html.escape(doc.title)}</title>
<style>
@page {{
  size: A3 landscape;
  margin: 1.5cm;
}}
@media print {{
  body {{ font-size: 9pt; }}
  .no-print {{ display: none; }}
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'IBM Plex Sans', -apple-system, sans-serif;
  font-size: 10pt;
  line-height: 1.5;
  color: #0f1113;
  background: #fff;
}}
.header {{
  padding: 1rem 2rem;
  border-bottom: 2px solid #0f1113;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}}
.header h1 {{ font-size: 1.3rem; font-weight: 800; }}
.header .meta {{ font-size: 0.75rem; color: #4b5563; }}
.stats {{
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem 2rem;
  border-bottom: 1px solid #d5dbe3;
  font-size: 0.75rem;
}}
.stat {{ display: flex; align-items: center; gap: 0.3rem; }}
.stat .dot {{ width: 8px; height: 8px; display: inline-block; }}
.dot-green {{ background: #0b7e59; }}
.dot-amber {{ background: #d97706; }}
.dot-blue {{ background: #3763e0; }}
.dot-red {{ background: #c0352b; }}
.dot-gray {{ background: #6b7280; }}
.columns {{
  display: flex;
  min-height: calc(100vh - 120px);
}}
.col-doc {{
  flex: 1;
  padding: 2rem;
  border-right: 1px solid #d5dbe3;
  overflow-wrap: break-word;
}}
.col-review {{
  width: 420px;
  flex-shrink: 0;
  padding: 1.5rem;
  background: #f6f7f8;
  overflow-y: auto;
  font-size: 0.8rem;
}}
/* Document styles */
.col-doc h1 {{ font-size: 1.4rem; font-weight: 800; margin: 1.5rem 0 0.5rem; }}
.col-doc h2 {{ font-size: 1.15rem; font-weight: 700; margin: 1.2rem 0 0.4rem; border-bottom: 1px solid #d5dbe3; padding-bottom: 0.2rem; }}
.col-doc h3 {{ font-size: 1rem; font-weight: 600; margin: 1rem 0 0.3rem; }}
.col-doc p {{ margin: 0 0 0.6rem; }}
.col-doc table {{ border-collapse: collapse; width: 100%; margin: 0.8rem 0; font-size: 0.85em; }}
.col-doc th {{ border-bottom: 2px solid #0f1113; padding: 0.3rem 0.5rem; text-align: left; font-weight: 700; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.03em; color: #4b5563; }}
.col-doc td {{ border-bottom: 1px solid #d5dbe3; padding: 0.3rem 0.5rem; }}
.col-doc ul, .col-doc ol {{ padding-left: 1.5rem; margin: 0.4rem 0; }}
.col-doc blockquote {{ border-left: 3px solid #3763e0; padding-left: 0.8rem; color: #4b5563; margin: 0.5rem 0; }}
.col-doc em {{ font-style: italic; }}
.col-doc strong {{ font-weight: 700; }}
/* Highlights */
.highlight-claim {{ background: rgba(55, 99, 224, 0.08); border-bottom: 2px solid rgba(55, 99, 224, 0.4); }}
.highlight-new {{ background: rgba(11, 126, 89, 0.1); border-left: 2px solid #0b7e59; padding-left: 0.3rem; }}
.highlight-delete {{ background: rgba(192, 53, 43, 0.08); text-decoration: line-through; color: #c0352b; }}
/* Review panel styles */
.section-title {{
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #4b5563;
  margin: 1.2rem 0 0.5rem;
  padding-bottom: 0.3rem;
  border-bottom: 1px solid #d5dbe3;
}}
.comment-card {{
  padding: 0.6rem;
  margin-bottom: 0.5rem;
  border-left: 3px solid #d97706;
  background: #fff;
}}
.comment-card.resolved {{ border-left-color: #0b7e59; opacity: 0.8; }}
.comment-author {{ font-weight: 600; font-size: 0.75rem; }}
.comment-text {{ margin-top: 0.2rem; font-size: 0.78rem; line-height: 1.5; }}
.comment-reply {{ margin-top: 0.3rem; padding: 0.4rem; background: #f0f7ff; border-left: 2px solid #3763e0; font-size: 0.75rem; }}
.change-card {{
  padding: 0.5rem;
  margin-bottom: 0.4rem;
  background: #fff;
}}
.change-insert {{ border-left: 3px solid #0b7e59; }}
.change-delete {{ border-left: 3px solid #c0352b; }}
.change-status {{ font-size: 0.65rem; text-transform: uppercase; font-weight: 600; }}
.change-content {{ font-size: 0.75rem; margin-top: 0.2rem; }}
.bib-entry {{ font-size: 0.72rem; margin-bottom: 0.3rem; line-height: 1.4; }}
.bib-key {{ font-weight: 600; color: #3763e0; }}
.claim-card {{ padding: 0.4rem; margin-bottom: 0.3rem; border-left: 3px solid #3763e0; background: #fff; font-size: 0.75rem; }}
.claim-type {{ font-size: 0.6rem; text-transform: uppercase; font-weight: 600; }}
.claim-verified {{ color: #0b7e59; }}
.claim-draft {{ color: #4b5563; }}
a {{ color: #3763e0; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>{html.escape(doc.title)}</h1>
    <div class="meta">Espacio Público · {doc.doc_type} · Generado {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
  </div>
  <div class="meta">
    <a href="https://scribe.illanes00.cl/editor/{slug}">Ver en Scribe</a>
    {f' · <a href="https://docs.google.com/document/d/{doc.source_id}/edit">Google Doc</a>' if doc.source_id else ''}
  </div>
</div>

<div class="stats">
  <div class="stat"><span class="dot dot-green"></span> {resolved} comentarios resueltos</div>
  <div class="stat"><span class="dot dot-amber"></span> {pending} pendientes</div>
  <div class="stat"><span class="dot dot-blue"></span> {len(changes)} cambios propuestos ({pending_changes} pendientes)</div>
  <div class="stat"><span class="dot dot-gray"></span> {len(claims)} claims · {len(bibliography)} referencias</div>
</div>

<div class="columns">
  <div class="col-doc">
    {doc_html}
  </div>
  <div class="col-review">
    <div class="section-title">Comentarios ({len(root_comments)})</div>
    {comments_html}

    <div class="section-title">Control de Cambios ({len(changes)})</div>
    {changes_html}

    <div class="section-title">Claims ({len(claims)})</div>
    {claims_html}

    <div class="section-title">Bibliografía ({len(bibliography)})</div>
    {bib_html}
  </div>
</div>

</body>
</html>"""


def _markdown_to_html(md: str) -> str:
    """Simple markdown to HTML conversion."""
    lines = md.split("\n")
    result = []
    in_table = False
    in_list = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if in_list:
                result.append("</ul>")
                in_list = False
            if in_table:
                result.append("</tbody></table>")
                in_table = False
            result.append("")
            continue

        # Table
        if "|" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(set(c) <= set("-: ") for c in cells):
                continue  # separator row
            if not in_table:
                result.append("<table><thead><tr>")
                for cell in cells:
                    result.append(f"<th>{_inline(cell)}</th>")
                result.append("</tr></thead><tbody>")
                in_table = True
            else:
                result.append("<tr>")
                for cell in cells:
                    result.append(f"<td>{_inline(cell)}</td>")
                result.append("</tr>")
            continue

        if in_table and not stripped.startswith("|"):
            result.append("</tbody></table>")
            in_table = False

        # Headers
        if stripped.startswith("### "):
            result.append(f"<h3>{_inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            result.append(f"<h2>{_inline(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            result.append(f"<h1>{_inline(stripped[2:])}</h1>")
        elif stripped.startswith("- "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{_inline(stripped[2:])}</li>")
        elif stripped.startswith("> "):
            result.append(f"<blockquote>{_inline(stripped[2:])}</blockquote>")
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f"<p>{_inline(stripped)}</p>")

    if in_list:
        result.append("</ul>")
    if in_table:
        result.append("</tbody></table>")

    return "\n".join(result)


def _inline(text: str) -> str:
    """Process inline markdown."""
    import re

    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[(.+?)\]\((.+?)\)",
        r'<a href="\2" target="_blank">\1</a>',
        text,
    )
    return text


def _build_comments_html(root_comments: list[Comment], replies_map: dict) -> str:
    parts = []
    for i, c in enumerate(root_comments, 1):
        status_class = "resolved" if c.resolved else ""
        parts.append(f'<div class="comment-card {status_class}">')
        parts.append(f'<div class="comment-author">#{i} · {html.escape(c.author or "Anon")} · {c.provider}</div>')
        parts.append(f'<div class="comment-text">{html.escape(c.content)}</div>')

        for reply in replies_map.get(c.id, []):
            parts.append(f'<div class="comment-reply">')
            parts.append(f'<strong>{html.escape(reply.author or "Scribe")}</strong>: {html.escape(reply.content[:200])}')
            parts.append("</div>")

        parts.append("</div>")
    return "\n".join(parts)


def _build_changes_html(changes: list[TrackChange]) -> str:
    parts = []
    for c in changes:
        change_class = "change-insert" if c.change_type.value == "insert" else "change-delete"
        status_color = {"pending": "#d97706", "accepted": "#0b7e59", "rejected": "#c0352b"}.get(c.status.value, "#4b5563")
        parts.append(f'<div class="change-card {change_class}">')
        parts.append(f'<div class="change-status" style="color:{status_color}">{c.change_type.value.upper()} · {c.status.value}</div>')
        parts.append(f'<div class="change-content">{html.escape((c.content or "")[:150])}</div>')
        if c.author_name:
            parts.append(f'<div style="font-size:0.65rem;color:#4b5563;margin-top:0.2rem">{html.escape(c.author_name)}</div>')
        parts.append("</div>")
    return "\n".join(parts)


def _build_claims_html(claims: list[Claim]) -> str:
    parts = []
    for c in claims:
        status_class = "claim-verified" if c.status == "verified" else "claim-draft"
        parts.append(f'<div class="claim-card">')
        parts.append(f'<span class="claim-type {status_class}">{c.claim_type} · {c.status}</span>')
        parts.append(f' {html.escape(c.claim_text[:120])}')
        parts.append("</div>")
    return "\n".join(parts) if parts else '<div style="font-size:0.75rem;color:#4b5563">No claims extraídos aún.</div>'


def _build_bibliography_html(entries: list[BibliographyEntry]) -> str:
    parts = []
    for e in entries:
        url_link = f' <a href="{html.escape(e.url)}">[link]</a>' if e.url else ""
        doi_link = f' <a href="https://doi.org/{html.escape(e.doi)}">[DOI]</a>' if e.doi else ""
        parts.append(
            f'<div class="bib-entry">'
            f'<span class="bib-key">[{html.escape(e.bib_key)}]</span> '
            f'{html.escape(e.author or "")} ({e.year or "s/f"}). '
            f'<em>{html.escape(e.title or "")}</em>. '
            f'{html.escape(e.journal or "")}'
            f'{url_link}{doi_link}'
            f"</div>"
        )
    return "\n".join(parts) if parts else '<div style="font-size:0.75rem;color:#4b5563">Sin bibliografía.</div>'
