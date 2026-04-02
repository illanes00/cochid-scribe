"""Integrated review export — document with inline diffs + margin comments.

Single A3 landscape page showing:
- Left (65%): Document with inline diff markers (green=added, red=removed)
- Right (35%): Comments anchored to document sections, bibliography with links

Each section header in the document shows a badge with comment count.
Changes appear inline as colored blocks within the document text.
Comments in the margin link back to the section they reference.
"""

from __future__ import annotations

import html
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.bibliography import BibliographyEntry
from app.models.claim import Claim
from app.models.comment import Comment
from app.models.document import Document
from app.models.track_change import TrackChange

# Section-level diffs: maps section heading text → list of changes
SECTION_CHANGES: dict[str, list[dict]] = {
    "Resumen Ejecutivo": [
        {"type": "alert", "text": "⚠ El resumen sigue diciendo \"propone el BFAU\" — debería alinearse con sección 4 (\"opciones de política\")"},
    ],
    "Marco Institucional": [
        {"type": "add", "text": "DAC (Decreto de Acceso Complementario): Operativo desde 2019, cubre drogas oncológicas de alto costo para pacientes FONASA. Presupuesto 2026: $91.200M (MINSAL, 2026)."},
        {"type": "add", "text": "GES actualizado: 90 patologías (Decreto GES 2025-2028)"},
    ],
    "Dos Dimensiones": [
        {"type": "add", "text": "Ambos frentes responden a lógicas distintas de riesgo financiero y requieren instrumentos diferenciados de protección."},
    ],
    "Judicialización": [
        {"type": "add", "text": "Sección nueva. Fuentes: Vargas-Pelaez et al. (2019), Corte Suprema (feb 2026)."},
    ],
    "Comparación Internacional": [
        {"type": "add", "text": "Nota metodológica: selección de países, años base, limitaciones de extrapolación."},
        {"type": "alert", "text": "⚠ Dato US$206 PPA posiblemente incorrecto — OCDE 2025 reporta US$455 PPP. Verificar metodología."},
        {"type": "replace", "before": "Reglas de sustitución por bioequivalentes y genéricos para contener costos", "after": "Reglas diferenciadas: (a) genéricos → sustitución directa; (b) biosimilares → supervisión médica (Kirchlechner & Cohen, 2025)"},
        {"type": "replace", "before": "ETESA con criterios transparentes", "after": "ETESA como priorización por valor sanitario, social y económico — no contención de gasto (Armijo et al., 2022)"},
    ],
    "Innovación con Valor": [
        {"type": "add", "text": "Sección nueva. Biosimilares Europa (-20-40% costos), diabetes + digital (-15-25% hospitalizaciones). Cortez, Medici & Singh, 2023."},
    ],
    "Lección de Costa Rica": [
        {"type": "alert", "text": "⚠ CCSS cubre 91-93%, no 95%. Verificar dato."},
    ],
    "Opciones de Política": [
        {"type": "replace", "before": "## 4. Propuesta: Beneficio Farmacéutico Ambulatorio Universal", "after": "## 4. Opciones de Política: Hacia un Beneficio Farmacéutico"},
        {"type": "add", "text": "Tabla de medidas por nivel de reforma: sin ley / ajuste regulatorio / rediseño sistémico."},
    ],
    "Requisitos Institucionales": [
        {"type": "add", "text": "La efectividad depende de implementación conjunta y coordinada, no aplicación aislada."},
    ],
    "Marco para la Discusión": [
        {"type": "replace", "before": "## 7. Conclusiones y Recomendaciones", "after": "## 7. Marco para la Discusión"},
    ],
    "Seminario de Discusión": [
        {"type": "add", "text": "Sección nueva. 5 preguntas para deliberación: cobertura, financiamiento, articulación, ETESA, innovación."},
    ],
    "Verificación de Datos": [
        {"type": "alert", "text": "⚠ GES dice 87 en tabla pero ya se actualizó a 90 en el texto. Tabla necesita actualización."},
    ],
}


def generate_review_html(db: Session, slug: str) -> str:
    """Generate integrated review with inline diffs and margin comments."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise ValueError(f"Document '{slug}' not found")

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

    # Group comments by section
    comments_by_section: dict[str, list[Comment]] = {}
    general_comments: list[Comment] = []
    for c in root_comments:
        sec = getattr(c, "section", None)
        if sec:
            comments_by_section.setdefault(sec, []).append(c)
        else:
            general_comments.append(c)

    # Build document HTML with inline diffs
    md = doc.markdown or ""
    doc_html = _markdown_to_html_with_diffs(md, comments_by_section, root_comments, replies_map)

    # Build margin comments
    margin_html = _build_margin_comments(root_comments, replies_map, general_comments)

    # Bibliography
    bib_html = _build_bib_html(bibliography)

    # Stats
    resolved = sum(1 for c in root_comments if c.resolved)
    pending = len(root_comments) - resolved
    inline_count = sum(1 for c in root_comments if getattr(c, "comment_scope", "") == "inline")
    section_count = sum(1 for c in root_comments if getattr(c, "comment_scope", "") == "section")
    general_count = len(general_comments)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Review: {html.escape(doc.title)}</title>
<style>
@page {{ size: A3 landscape; margin: 1.2cm; }}
@media print {{ body {{ font-size: 8.5pt; }} .no-print {{ display: none; }} }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'IBM Plex Sans', -apple-system, sans-serif;
  font-size: 9.5pt; line-height: 1.55; color: #0f1113; background: #fff;
}}
a {{ color: #3763e0; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* Header */
.hdr {{ padding: 0.8rem 1.5rem; border-bottom: 2px solid #0f1113; display: flex; justify-content: space-between; align-items: baseline; }}
.hdr h1 {{ font-size: 1.2rem; font-weight: 800; }}
.hdr .meta {{ font-size: 0.7rem; color: #4b5563; }}
.stats {{ display: flex; gap: 1.5rem; padding: 0.5rem 1.5rem; border-bottom: 1px solid #d5dbe3; font-size: 0.7rem; background: #fafbfc; }}
.stat {{ display: flex; align-items: center; gap: 0.25rem; }}
.dot {{ width: 7px; height: 7px; display: inline-block; }}
.dot-g {{ background: #0b7e59; }} .dot-a {{ background: #d97706; }} .dot-b {{ background: #3763e0; }} .dot-r {{ background: #c0352b; }} .dot-y {{ background: #6b7280; }}

/* Layout */
.cols {{ display: flex; min-height: calc(100vh - 80px); }}
.col-doc {{ flex: 1; padding: 1.5rem 2rem; overflow-wrap: break-word; }}
.col-margin {{ width: 380px; flex-shrink: 0; padding: 1rem; background: #f8f9fa; border-left: 1px solid #d5dbe3; font-size: 0.78rem; overflow-y: auto; }}

/* Document typography */
.col-doc h1 {{ font-size: 1.3rem; font-weight: 800; margin: 1.2rem 0 0.4rem; }}
.col-doc h2 {{ font-size: 1.05rem; font-weight: 700; margin: 1rem 0 0.3rem; padding-bottom: 0.2rem; border-bottom: 1px solid #d5dbe3; }}
.col-doc h3 {{ font-size: 0.95rem; font-weight: 600; margin: 0.8rem 0 0.25rem; }}
.col-doc p {{ margin: 0 0 0.5rem; }}
.col-doc table {{ border-collapse: collapse; width: 100%; margin: 0.6rem 0; font-size: 0.85em; }}
.col-doc th {{ border-bottom: 2px solid #0f1113; padding: 0.25rem 0.4rem; text-align: left; font-weight: 700; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.03em; color: #4b5563; }}
.col-doc td {{ border-bottom: 1px solid #d5dbe3; padding: 0.25rem 0.4rem; }}
.col-doc ul, .col-doc ol {{ padding-left: 1.3rem; margin: 0.3rem 0; }}
.col-doc blockquote {{ border-left: 3px solid #3763e0; padding-left: 0.6rem; color: #4b5563; margin: 0.4rem 0; font-style: italic; }}
.col-doc em {{ font-style: italic; }} .col-doc strong {{ font-weight: 700; }}
.col-doc code {{ background: #f0f1f3; padding: 0.1rem 0.2rem; font-size: 0.85em; font-family: 'JetBrains Mono', monospace; }}

/* Inline diff markers */
.diff-add {{ background: #dcfce7; border-left: 3px solid #0b7e59; padding: 0.3rem 0.5rem; margin: 0.3rem 0; font-size: 0.85em; }}
.diff-del {{ background: #fef2f2; border-left: 3px solid #c0352b; padding: 0.3rem 0.5rem; margin: 0.3rem 0; font-size: 0.85em; text-decoration: line-through; color: #c0352b; }}
.diff-replace {{ margin: 0.3rem 0; }}
.diff-replace .old {{ background: #fef2f2; border-left: 3px solid #c0352b; padding: 0.2rem 0.5rem; font-size: 0.82em; text-decoration: line-through; color: #991b1b; }}
.diff-replace .new {{ background: #dcfce7; border-left: 3px solid #0b7e59; padding: 0.2rem 0.5rem; font-size: 0.82em; color: #065f46; }}
.diff-alert {{ background: #fef9c3; border-left: 3px solid #d97706; padding: 0.3rem 0.5rem; margin: 0.3rem 0; font-size: 0.82em; color: #92400e; }}
.diff-label {{ font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.1rem; }}
.diff-label-add {{ color: #0b7e59; }} .diff-label-del {{ color: #c0352b; }} .diff-label-alert {{ color: #d97706; }}

/* Section comment badge */
.sec-badge {{ display: inline-flex; align-items: center; gap: 0.2rem; font-size: 0.6rem; font-weight: 600; padding: 0.1rem 0.3rem; border: 1px solid #3763e0; color: #3763e0; vertical-align: middle; margin-left: 0.4rem; }}
.sec-badge-amber {{ border-color: #d97706; color: #d97706; }}

/* Margin comments */
.m-section {{ font-weight: 700; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; color: #3763e0; margin: 0.8rem 0 0.3rem; padding-bottom: 0.15rem; border-bottom: 1px solid #d5dbe3; }}
.m-card {{ padding: 0.4rem 0.5rem; margin-bottom: 0.4rem; border-left: 3px solid #d97706; background: #fff; }}
.m-card.resolved {{ border-left-color: #0b7e59; opacity: 0.85; }}
.m-author {{ font-weight: 600; font-size: 0.68rem; }}
.m-text {{ font-size: 0.72rem; line-height: 1.5; margin-top: 0.15rem; }}
.m-reply {{ margin-top: 0.2rem; padding: 0.25rem 0.4rem; background: #f0f4ff; border-left: 2px solid #3763e0; font-size: 0.68rem; }}
.m-provider {{ font-size: 0.55rem; text-transform: uppercase; letter-spacing: 0.04em; color: #4b5563; }}
.m-scope {{ font-size: 0.55rem; font-weight: 600; padding: 0.05rem 0.25rem; border: 1px solid; display: inline-block; margin-left: 0.3rem; }}

/* Bibliography */
.bib-entry {{ font-size: 0.7rem; margin-bottom: 0.25rem; line-height: 1.4; }}
.bib-key {{ font-weight: 600; color: #3763e0; }}
</style>
</head>
<body>

<div class="hdr">
  <div>
    <h1>{html.escape(doc.title)}</h1>
    <div class="meta">Espacio Público · Review integrado · {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
  </div>
  <div class="meta">
    <a href="https://scribe.illanes00.cl/editor/{slug}">Scribe</a>
    {f' · <a href="https://docs.google.com/document/d/{doc.source_id}/edit">Google Doc</a>' if doc.source_id else ''}
  </div>
</div>

<div class="stats">
  <div class="stat"><span class="dot dot-g"></span> {resolved} resueltos</div>
  <div class="stat"><span class="dot dot-a"></span> {pending} pendientes</div>
  <div class="stat"><span class="dot dot-b"></span> {section_count} de sección · {inline_count} inline · {general_count} generales</div>
  <div class="stat"><span class="dot dot-y"></span> {len(changes)} cambios · {len(bibliography)} refs</div>
</div>

<div class="cols">
  <div class="col-doc">
    {doc_html}
  </div>
  <div class="col-margin">
    {margin_html}
    <div class="m-section" style="color:#4b5563">Bibliografía ({len(bibliography)})</div>
    {bib_html}
  </div>
</div>

</body>
</html>"""


def _markdown_to_html_with_diffs(
    md: str,
    comments_by_section: dict[str, list[Comment]],
    all_comments: list[Comment],
    replies_map: dict,
) -> str:
    """Convert markdown to HTML, injecting inline diffs at section boundaries."""
    lines = md.split("\n")
    result = []
    in_table = False
    in_list = False
    current_section = ""
    comment_idx = 0

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
                continue
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

        # Headers — inject diff markers and comment badges
        is_heading = False
        heading_text = ""
        heading_level = 0

        if stripped.startswith("### "):
            heading_text = stripped[4:]
            heading_level = 3
            is_heading = True
        elif stripped.startswith("## "):
            heading_text = stripped[3:]
            heading_level = 2
            is_heading = True
        elif stripped.startswith("# "):
            heading_text = stripped[2:]
            heading_level = 1
            is_heading = True

        if is_heading:
            if in_list:
                result.append("</ul>")
                in_list = False

            heading_id = heading_text.lower().replace(" ", "-").replace(".", "").replace(":", "")[:40]
            current_section = heading_text

            # Count comments for this section
            section_comment_count = 0
            for sec_key, sec_comments in comments_by_section.items():
                if _section_matches(sec_key, heading_text):
                    section_comment_count += len(sec_comments)

            badge = ""
            if section_comment_count > 0:
                badge = f' <span class="sec-badge">{section_comment_count} comentarios</span>'

            # Check for diffs at this section
            diffs_html = _get_section_diffs(heading_text)

            tag = f"h{heading_level}"
            result.append(f'<{tag} id="sec-{heading_id}">{_inline(heading_text)}{badge}</{tag}>')
            if diffs_html:
                result.append(diffs_html)
            continue

        # Lists
        if stripped.startswith("- "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{_inline(stripped[2:])}</li>")
        elif stripped.startswith("> "):
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f"<blockquote>{_inline(stripped[2:])}</blockquote>")
        elif re.match(r"^\d+\.\s", stripped):
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f"<p>{_inline(stripped)}</p>")
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


def _get_section_diffs(heading_text: str) -> str:
    """Get inline diff HTML for changes at this section."""
    parts = []
    for sec_key, changes in SECTION_CHANGES.items():
        if _section_matches(sec_key, heading_text):
            for change in changes:
                if change["type"] == "add":
                    parts.append(f'<div class="diff-add"><div class="diff-label diff-label-add">+ Agregado</div>{html.escape(change["text"])}</div>')
                elif change["type"] == "alert":
                    parts.append(f'<div class="diff-alert"><div class="diff-label diff-label-alert">⚠ Verificar</div>{html.escape(change["text"])}</div>')
                elif change["type"] == "replace":
                    parts.append(f'<div class="diff-replace"><div class="old"><div class="diff-label diff-label-del">− Antes</div>{html.escape(change["before"])}</div><div class="new"><div class="diff-label diff-label-add">+ Después</div>{html.escape(change["after"])}</div></div>')
    return "\n".join(parts)


def _section_matches(key: str, heading: str) -> bool:
    """Check if a section key matches a heading."""
    return key.lower() in heading.lower() or heading.lower() in key.lower()


def _inline(text: str) -> str:
    """Process inline markdown."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" target="_blank">\1</a>', text)
    return text


def _build_margin_comments(
    root_comments: list[Comment],
    replies_map: dict,
    general_comments: list[Comment],
) -> str:
    """Build margin comments grouped by section."""
    parts = []

    # Group by section
    by_section: dict[str, list[tuple[int, Comment]]] = {}
    inline_comments: list[tuple[int, Comment]] = []
    general: list[tuple[int, Comment]] = []

    for i, c in enumerate(root_comments, 1):
        scope = getattr(c, "comment_scope", "general")
        section = getattr(c, "section", None)
        if scope == "section" and section:
            by_section.setdefault(section, []).append((i, c))
        elif scope == "inline":
            inline_comments.append((i, c))
        else:
            general.append((i, c))

    # Section comments
    if by_section:
        parts.append('<div class="m-section">Por sección</div>')
        for section_name, section_comments in sorted(by_section.items()):
            sec_id = section_name.lower().replace(" ", "-").replace(".", "")[:40]
            parts.append(f'<div style="font-size:0.68rem;font-weight:600;color:#3763e0;margin:0.4rem 0 0.15rem"><a href="#sec-{sec_id}">{html.escape(section_name)}</a></div>')
            for idx, c in section_comments:
                parts.append(_render_margin_card(idx, c, replies_map))

    # Inline
    if inline_comments:
        parts.append('<div class="m-section" style="color:#d97706">Ediciones inline</div>')
        for idx, c in inline_comments:
            parts.append(_render_margin_card(idx, c, replies_map))

    # General
    if general:
        parts.append('<div class="m-section" style="color:#4b5563">Generales</div>')
        for idx, c in general:
            parts.append(_render_margin_card(idx, c, replies_map))

    return "\n".join(parts)


def _render_margin_card(idx: int, c: Comment, replies_map: dict) -> str:
    status = "resolved" if c.resolved else ""
    provider = {"email": "Email", "google-docs": "GDocs", "local": "Scribe", "scribe-ai": "AI"}.get(c.provider, c.provider)
    scope = getattr(c, "comment_scope", "general")
    scope_color = {"inline": "#d97706", "section": "#3763e0", "general": "#4b5563"}.get(scope, "#4b5563")

    parts = [f'<div class="m-card {status}">']
    parts.append(f'<div class="m-author">#{idx} · {html.escape(c.author or "Anon")} <span class="m-provider">{provider}</span></div>')
    parts.append(f'<div class="m-text">{html.escape(c.content[:150])}</div>')

    for reply in replies_map.get(c.id, []):
        parts.append(f'<div class="m-reply"><strong>{html.escape(reply.author or "Scribe")[:20]}</strong>: {html.escape(reply.content[:120])}</div>')

    parts.append("</div>")
    return "\n".join(parts)


def _build_bib_html(entries: list[BibliographyEntry]) -> str:
    parts = []
    for e in entries:
        url = ""
        if e.url:
            url = f' <a href="{html.escape(e.url)}" target="_blank">[link]</a>'
        if e.doi:
            url += f' <a href="https://doi.org/{html.escape(e.doi)}" target="_blank">[DOI]</a>'
        parts.append(
            f'<div class="bib-entry">'
            f'<span class="bib-key">[{html.escape(e.bib_key)}]</span> '
            f'{html.escape(e.author or "")} ({e.year or "s/f"}). '
            f'<em>{html.escape(e.title or "")}</em>. '
            f'{html.escape(e.journal or "")}'
            f'{url}</div>'
        )
    return "\n".join(parts) if parts else '<div style="font-size:0.7rem;color:#4b5563">Sin bibliografía.</div>'
