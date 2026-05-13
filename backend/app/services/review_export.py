"""Google Docs-style review export — document with inline suggestions + margin comments.

Renders a full-page document with:
- Inline suggestions: <del>old</del> <ins>new</ins> in the text flow
- Highlighted text where comments reference specific passages
- Margin comments positioned at the same height as their referenced text
- SVG connector lines from highlights to margin comments
- JavaScript positioning for accurate alignment (works in Chrome headless for PDF)

Inspired by Google Docs review/suggestion mode.
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

# ── Section-level diffs ──────────────────────────────────────────────────────
# Maps section heading text → list of inline changes to render
SECTION_CHANGES: dict[str, list[dict]] = {
    "Resumen Ejecutivo": [
        {
            "type": "alert",
            "text": 'El resumen sigue diciendo "propone el BFAU" — debería alinearse con sección 4 ("opciones de política")',
        },
    ],
    "Marco Institucional": [
        {
            "type": "add",
            "text": "DAC (Decreto de Acceso Complementario): Operativo desde 2019, cubre drogas oncológicas de alto costo para pacientes FONASA. Presupuesto 2026: $91.200M (MINSAL, 2026).",
        },
        {"type": "add", "text": "GES actualizado: 90 patologías (Decreto GES 2025-2028)"},
    ],
    "Dos Dimensiones": [
        {
            "type": "add",
            "text": "Ambos frentes responden a lógicas distintas de riesgo financiero y requieren instrumentos diferenciados de protección.",
        },
    ],
    "Judicialización": [
        {
            "type": "add",
            "text": "Sección nueva. Fuentes: Vargas-Pelaez et al. (2019), Corte Suprema (feb 2026).",
        },
    ],
    "Comparación Internacional": [
        {
            "type": "add",
            "text": "Nota metodológica: selección de países, años base, limitaciones de extrapolación.",
        },
        {
            "type": "alert",
            "text": "Dato US$206 PPA posiblemente incorrecto — OCDE 2025 reporta US$455 PPP. Verificar metodología.",
        },
        {
            "type": "replace",
            "before": "Reglas de sustitución por bioequivalentes y genéricos para contener costos",
            "after": "Reglas diferenciadas: (a) genéricos → sustitución directa; (b) biosimilares → supervisión médica (Kirchlechner & Cohen, 2025)",
        },
        {
            "type": "replace",
            "before": "ETESA con criterios transparentes",
            "after": "ETESA como priorización por valor sanitario, social y económico — no contención de gasto (Armijo et al., 2022)",
        },
    ],
    "Innovación con Valor": [
        {
            "type": "add",
            "text": "Sección nueva. Biosimilares Europa (-20-40% costos), diabetes + digital (-15-25% hospitalizaciones). Cortez, Medici & Singh, 2023.",
        },
    ],
    "Lección de Costa Rica": [
        {"type": "alert", "text": "CCSS cubre 91-93%, no 95%. Verificar dato."},
    ],
    "Opciones de Política": [
        {
            "type": "replace",
            "before": "## 4. Propuesta: Beneficio Farmacéutico Ambulatorio Universal",
            "after": "## 4. Opciones de Política: Hacia un Beneficio Farmacéutico",
        },
        {
            "type": "add",
            "text": "Tabla de medidas por nivel de reforma: sin ley / ajuste regulatorio / rediseño sistémico.",
        },
    ],
    "Requisitos Institucionales": [
        {
            "type": "add",
            "text": "La efectividad depende de implementación conjunta y coordinada, no aplicación aislada.",
        },
    ],
    "Marco para la Discusión": [
        {
            "type": "replace",
            "before": "## 7. Conclusiones y Recomendaciones",
            "after": "## 7. Marco para la Discusión",
        },
    ],
    "Seminario de Discusión": [
        {
            "type": "add",
            "text": "Sección nueva. 5 preguntas para deliberación: cobertura, financiamiento, articulación, ETESA, innovación.",
        },
    ],
    "Verificación de Datos": [
        {
            "type": "alert",
            "text": "GES dice 87 en tabla pero ya se actualizó a 90 en el texto. Tabla necesita actualización.",
        },
    ],
}

CITATION_MAP = {
    "INE, 2023": "ine_2023",
    "Instituto Nacional de Estadísticas [INE], 2023, Cuadro 8.1, cálculo del autor": "ine_2023",
    "Instituto Nacional de Estadísticas [INE], 2023": "ine_2023",
    "OCDE, 2025": "oecd_2025",
    "Organización para la Cooperación y el Desarrollo Económicos [OCDE], 2025": "oecd_2025",
    "OMS, 2024": "who_ghed_2024",
    "Organización Mundial de la Salud [OMS], 2024": "who_ghed_2024",
    "Armijo et al., 2022": "armijo_espinoza_2022",
    "Kirchlechner & Cohen, 2025": "kirchlechner_cohen_2025",
    "Kirchlechner &amp; Cohen, 2025": "kirchlechner_cohen_2025",
    "Cortez, Medici & Singh, 2023": "cortez_medici_singh_2023",
    "Cortez, Medici &amp; Singh, 2023": "cortez_medici_singh_2023",
    "Vargas-Pelaez et al., 2019": "vargas_pelaez_2019",
    "Corte Suprema, 2026": "corte_suprema_2026",
    "MINSAL, 2026": "minsal_dac_2026",
    "FONASA, 2023": "fonasa_2023",
}


# ── Main export function ─────────────────────────────────────────────────────


def generate_review_html(db: Session, slug: str) -> str:
    """Generate Google Docs-style review export with inline suggestions + margin comments."""
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
    bibliography = db.query(BibliographyEntry).all()

    # Assign sequential reference numbers to root comments
    # Order: section comments (by section order in doc), then inline, then general
    section_comments = [c for c in root_comments if getattr(c, "comment_scope", "") == "section"]
    inline_comments = [c for c in root_comments if getattr(c, "comment_scope", "") == "inline"]
    general_comments = [
        c
        for c in root_comments
        if getattr(c, "comment_scope", "general") not in ("section", "inline")
    ]
    ordered_comments = section_comments + inline_comments + general_comments
    comment_ref: dict[str, int] = {}
    for i, c in enumerate(ordered_comments, 1):
        comment_ref[c.id] = i

    # Group comments by section for inline badges
    comments_by_section: dict[str, list[Comment]] = {}
    for c in root_comments:
        sec = getattr(c, "section", None)
        if sec:
            comments_by_section.setdefault(sec, []).append(c)

    # Compute section resolution status: section_key → (resolved, total)
    section_status: dict[str, tuple[int, int]] = {}
    for sec_key, sec_comments in comments_by_section.items():
        res = sum(1 for c in sec_comments if c.resolved)
        section_status[sec_key] = (res, len(sec_comments))

    # Build document HTML
    md = doc.markdown or ""
    doc_html = _markdown_to_html_with_suggestions(
        md, comments_by_section, comment_ref, section_status
    )

    # Build margin comment cards
    margin_cards = _build_margin_cards(ordered_comments, replies_map, comment_ref)

    # Bibliography
    bib_html = _build_bib_html(bibliography)

    # Stats
    resolved = sum(1 for c in root_comments if c.resolved)
    pending = len(root_comments) - resolved

    title_escaped = html.escape(doc.title)
    source_link = ""
    if doc.source_id:
        source_link = f' &middot; <a href="https://docs.google.com/document/d/{html.escape(doc.source_id)}/edit">Google Doc</a>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Review: {title_escaped}</title>
<style>
{_get_css()}
</style>
</head>
<body>

<header class="doc-header">
  <div class="doc-header-left">
    <h1 class="doc-title">{title_escaped}</h1>
    <div class="doc-meta">Espacio Publico &middot; {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
  </div>
  <div class="doc-header-right">
    <div class="doc-stats">
      <span class="stat stat-resolved">{resolved} resueltos</span>
      <span class="stat stat-pending">{pending} pendientes</span>
      <span class="stat stat-total">{len(changes)} cambios</span>
      <span class="stat stat-bib">{len(bibliography)} refs</span>
    </div>
    <div class="doc-links">
      <a href="https://scribe.illanes00.cl/editor/{slug}">Abrir en Scribe</a>
      {source_link}
    </div>
  </div>
</header>

<div class="page-container">
  <svg class="connectors" id="connectors"></svg>
  <div class="doc-body" id="doc-body">
    {doc_html}
    <div class="bib-section">
      <h2>Referencias</h2>
      {bib_html}
    </div>
  </div>
  <div class="margin-comments" id="margin-comments">
    {margin_cards}
  </div>
</div>

<script>
{_get_js()}
</script>
</body>
</html>"""


# ── Markdown to HTML with inline suggestions ─────────────────────────────────


def _markdown_to_html_with_suggestions(
    md: str,
    comments_by_section: dict[str, list[Comment]],
    comment_ref: dict[str, int],
    section_status: dict[str, tuple[int, int]],
) -> str:
    """Convert markdown to HTML with inline del/ins suggestions, status badges, and section separators."""
    lines = md.split("\n")
    result: list[str] = []
    in_table = False
    in_list = False
    h2_count = 0  # Track H2s for separators

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

        # ── Table ──
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

        # ── Headers ──
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

            heading_id = re.sub(r"[^a-z0-9-]", "", heading_text.lower().replace(" ", "-"))[:40]
            tag = f"h{heading_level}"

            # Section separator before H2 (not the first one)
            if heading_level == 2:
                h2_count += 1
                if h2_count > 1:
                    # Build section status summary for the separator
                    sep_status = _section_separator_status(heading_text, section_status)
                    result.append(f'<div class="section-sep">{sep_status}</div>')

            # Find comment references for this section
            refs_html = _section_comment_refs(heading_text, comments_by_section, comment_ref)

            # Section-level changes with resolution status
            section_resolved = _is_section_resolved(heading_text, section_status)
            suggestions_html = _get_section_suggestions(heading_text, section_resolved)

            # Wrap heading in a mark if it has comments
            heading_inner = _inline(heading_text)
            if refs_html:
                heading_inner = (
                    f'<mark class="cm" data-section="{html.escape(heading_id)}">'
                    f"{heading_inner}</mark>{refs_html}"
                )

            result.append(f'<{tag} id="sec-{heading_id}">{heading_inner}</{tag}>')
            if suggestions_html:
                result.append(suggestions_html)
            continue

        # ── Lists ──
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


def _section_comment_refs(
    heading_text: str,
    comments_by_section: dict[str, list[Comment]],
    comment_ref: dict[str, int],
) -> str:
    """Build superscript reference numbers for comments on this section."""
    refs: list[str] = []
    for sec_key, sec_comments in comments_by_section.items():
        if _section_matches(sec_key, heading_text):
            for c in sec_comments:
                num = comment_ref.get(c.id, 0)
                if num:
                    refs.append(f'<sup class="cref" data-cref="{num}">{num}</sup>')
    return "".join(refs)


def _is_section_resolved(
    heading_text: str, section_status: dict[str, tuple[int, int]]
) -> bool | None:
    """Check if all comments in this section are resolved. None if no comments."""
    for sec_key, (resolved, total) in section_status.items():
        if _section_matches(sec_key, heading_text):
            return resolved == total
    return None


def _section_separator_status(
    heading_text: str, section_status: dict[str, tuple[int, int]]
) -> str:
    """Build a small status summary for the section separator line."""
    for sec_key, (resolved, total) in section_status.items():
        if _section_matches(sec_key, heading_text):
            if total == 0:
                return ""
            if resolved == total:
                return f'<span class="sep-badge sep-resolved">{resolved}/{total} resueltos</span>'
            return f'<span class="sep-badge sep-pending">{resolved}/{total} resueltos</span>'
    return ""


def _get_section_suggestions(heading_text: str, section_resolved: bool | None) -> str:
    """Render inline suggestions with status badges for changes at this section."""
    parts: list[str] = []
    for sec_key, changes in SECTION_CHANGES.items():
        if _section_matches(sec_key, heading_text):
            for change in changes:
                if change["type"] == "add":
                    if section_resolved:
                        badge = '<span class="sg-badge sg-applied">Agregado</span>'
                    elif section_resolved is False:
                        badge = '<span class="sg-badge sg-pending">Pendiente</span>'
                    else:
                        badge = '<span class="sg-badge sg-applied">Agregado</span>'
                    parts.append(
                        f'<div class="suggestion sg-add">'
                        f"{badge}"
                        f'<ins>{html.escape(change["text"])}</ins>'
                        f"</div>"
                    )
                elif change["type"] == "alert":
                    badge = '<span class="sg-badge sg-verify">Verificar</span>'
                    parts.append(
                        f'<div class="suggestion sg-alert">'
                        f"{badge}"
                        f'{html.escape(change["text"])}'
                        f"</div>"
                    )
                elif change["type"] == "replace":
                    if section_resolved:
                        badge = '<span class="sg-badge sg-corrected">Corregido</span>'
                    elif section_resolved is False:
                        badge = '<span class="sg-badge sg-pending">Pendiente</span>'
                    else:
                        badge = '<span class="sg-badge sg-corrected">Corregido</span>'
                    parts.append(
                        f'<div class="suggestion sg-replace">'
                        f"{badge}"
                        f'<del>{html.escape(change["before"])}</del> '
                        f'<ins>{html.escape(change["after"])}</ins>'
                        f"</div>"
                    )
    return "\n".join(parts)


def _section_matches(key: str, heading: str) -> bool:
    """Check if a section key matches a heading."""
    return key.lower() in heading.lower() or heading.lower() in key.lower()


def _inline(text: str) -> str:
    """Process inline markdown + citation hyperlinks."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" target="_blank">\1</a>', text)

    for citation_text, bib_key in CITATION_MAP.items():
        escaped = html.escape(citation_text)
        if escaped in text:
            link = (
                f'<a href="#bib-{bib_key}" class="cite-link" '
                f'title="Ver referencia">{escaped}</a>'
            )
            text = text.replace(f"({escaped})", f"({link})")

    return text


# ── Margin comment cards ─────────────────────────────────────────────────────


def _build_margin_cards(
    ordered_comments: list[Comment],
    replies_map: dict[str, list[Comment]],
    comment_ref: dict[str, int],
) -> str:
    """Build flat margin comment cards with reference numbers."""
    parts: list[str] = []

    for c in ordered_comments:
        num = comment_ref.get(c.id, 0)
        scope = getattr(c, "comment_scope", "general")
        section = getattr(c, "section", None)
        resolved = c.resolved
        provider = {
            "email": "Email",
            "google-docs": "GDocs",
            "local": "Scribe",
            "scribe-ai": "AI",
        }.get(c.provider, c.provider)

        status_cls = "resolved" if resolved else "pending"
        scope_cls = f"scope-{scope}"

        sec_id = ""
        if section:
            sec_id = re.sub(r"[^a-z0-9-]", "", section.lower().replace(" ", "-"))[:40]

        card_parts: list[str] = []
        card_parts.append(
            f'<div class="mc {status_cls} {scope_cls}" '
            f'data-cid="{num}" data-section="{html.escape(sec_id)}">'
        )
        card_parts.append('  <div class="mc-head">')
        card_parts.append(f'    <span class="mc-num">{num}</span>')
        card_parts.append(
            f'    <span class="mc-author">{html.escape(c.author or "Anon")}</span>'
        )
        card_parts.append(f'    <span class="mc-provider">{provider}</span>')
        if resolved:
            card_parts.append('    <span class="mc-status mc-resolved">Resuelto</span>')
        card_parts.append("  </div>")
        card_parts.append(f'  <div class="mc-body">{html.escape(c.content)}</div>')

        for reply in replies_map.get(c.id, []):
            card_parts.append('  <div class="mc-reply">')
            card_parts.append(
                f'    <span class="mc-reply-author">'
                f"{html.escape(reply.author or 'Scribe')}</span>"
            )
            card_parts.append(f"    {html.escape(reply.content)}")
            card_parts.append("  </div>")

        card_parts.append("</div>")
        parts.append("\n".join(card_parts))

    return "\n".join(parts)


# ── Bibliography ─────────────────────────────────────────────────────────────


def _build_bib_html(entries: list[BibliographyEntry]) -> str:
    """Build APA-style bibliography entries with clickable links."""
    parts: list[str] = []
    for e in entries:
        author = html.escape(e.author or "")
        year = e.year or "s/f"
        title = html.escape(e.title or "")
        journal = html.escape(e.journal or "")

        if e.doi:
            doi_escaped = html.escape(e.doi)
            title_html = (
                f'<a href="https://doi.org/{doi_escaped}" target="_blank">'
                f"<em>{title}</em></a>"
            )
        elif e.url:
            url_escaped = html.escape(e.url)
            title_html = (
                f'<a href="{url_escaped}" target="_blank"><em>{title}</em></a>'
            )
        else:
            title_html = f"<em>{title}</em>"

        citation = f"{author} ({year}). {title_html}."
        if journal:
            citation += f" <em>{journal}</em>."
        if e.doi:
            citation += f' <span class="bib-doi">doi:{html.escape(e.doi)}</span>'

        bib_key_escaped = html.escape(e.bib_key)
        parts.append(
            f'<div class="bib-entry" id="bib-{bib_key_escaped}">'
            f'<span class="bib-key">[{bib_key_escaped}]</span> {citation}'
            f"</div>"
        )

    return "\n".join(parts) if parts else '<p class="bib-empty">Sin referencias.</p>'


# ── CSS ──────────────────────────────────────────────────────────────────────


def _get_css() -> str:
    return """
@page { size: A3 landscape; margin: 1.2cm; }
@media print {
  body { font-size: 8.5pt; }
  .no-print { display: none; }
  .page-container { overflow: visible; }
}
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Google Sans', 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 11pt;
  line-height: 1.6;
  color: #202124;
  background: #f8f9fa;
}
a { color: #1a73e8; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Header ── */
.doc-header {
  background: #fff;
  border-bottom: 1px solid #dadce0;
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.doc-title {
  font-size: 18px;
  font-weight: 500;
  color: #202124;
}
.doc-meta {
  font-size: 11px;
  color: #5f6368;
  margin-top: 2px;
}
.doc-stats {
  display: flex;
  gap: 12px;
  font-size: 11px;
}
.stat {
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}
.stat-resolved { background: #e6f4ea; color: #137333; }
.stat-pending { background: #fce8e6; color: #c5221f; }
.stat-total { background: #e8f0fe; color: #1967d2; }
.stat-bib { background: #f1f3f4; color: #5f6368; }
.doc-links {
  font-size: 11px;
  margin-top: 4px;
  text-align: right;
}

/* ── Page layout: document + margin ── */
.page-container {
  position: relative;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  background: #fff;
  min-height: calc(100vh - 60px);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.doc-body {
  flex: 1;
  padding: 40px 60px 60px 60px;
  max-width: 860px;
  min-width: 0;
}
.margin-comments {
  width: 380px;
  flex-shrink: 0;
  position: relative;
  padding: 40px 16px 60px 8px;
  border-left: 1px solid #dadce0;
}
.connectors {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

/* ── Document typography ── */
.doc-body h1 {
  font-size: 24px;
  font-weight: 400;
  color: #202124;
  margin: 28px 0 12px;
  line-height: 1.3;
}
.doc-body h2 {
  font-size: 18px;
  font-weight: 500;
  color: #202124;
  margin: 24px 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #e8eaed;
}
.doc-body h3 {
  font-size: 14px;
  font-weight: 600;
  color: #3c4043;
  margin: 16px 0 6px;
}
.doc-body p {
  margin: 0 0 8px;
  color: #3c4043;
}
.doc-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 0.9em;
}
.doc-body th {
  border-bottom: 2px solid #202124;
  padding: 6px 8px;
  text-align: left;
  font-weight: 600;
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  color: #5f6368;
}
.doc-body td {
  border-bottom: 1px solid #e8eaed;
  padding: 6px 8px;
}
.doc-body ul, .doc-body ol {
  padding-left: 24px;
  margin: 4px 0;
}
.doc-body blockquote {
  border-left: 3px solid #1a73e8;
  padding-left: 12px;
  color: #5f6368;
  margin: 8px 0;
  font-style: italic;
}
.doc-body strong { font-weight: 600; }
.doc-body em { font-style: italic; }
.doc-body code {
  background: #f1f3f4;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 0.88em;
  font-family: 'Roboto Mono', monospace;
}

/* ── Section separators ── */
.section-sep {
  border-top: 1px solid #dadce0;
  margin: 28px 0 8px;
  padding-top: 6px;
  min-height: 20px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.sep-badge {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
}
.sep-resolved { background: #e6f4ea; color: #137333; }
.sep-pending { background: #fef7e0; color: #7c4d12; }

/* ── Inline suggestions (Google Docs style) ── */
.suggestion {
  margin: 6px 0 10px;
  padding: 6px 10px;
  line-height: 1.7;
  border-radius: 4px;
  position: relative;
}
.suggestion del {
  background: #fce8e6;
  color: #c5221f;
  text-decoration: line-through;
  text-decoration-color: #c5221f;
  padding: 1px 3px;
  border-radius: 2px;
}
.suggestion ins {
  background: #e6f4ea;
  color: #137333;
  text-decoration: none;
  padding: 1px 3px;
  border-radius: 2px;
}

/* Suggestion type variants */
.sg-add {
  background: #f0fdf4;
  border-left: 3px solid #137333;
}
.sg-replace {
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
}
.sg-alert {
  background: #fef7e0;
  border-left: 3px solid #f9ab00;
  color: #7c4d12;
  font-size: 0.88em;
}

/* Status badges on suggestions */
.sg-badge {
  display: inline-block;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 2px 7px;
  border-radius: 3px;
  margin-right: 6px;
  vertical-align: middle;
}
.sg-applied { background: #137333; color: #fff; }
.sg-corrected { background: #1967d2; color: #fff; }
.sg-verify { background: #f9ab00; color: #fff; }
.sg-pending { background: #80868b; color: #fff; }
.sg-rejected { background: #c5221f; color: #fff; }

/* ── Comment highlight marks ── */
mark.cm {
  background: #fcefb4;
  padding: 1px 0;
  border-bottom: 2px solid #f9ab00;
  border-radius: 0;
}

/* ── Superscript comment references ── */
sup.cref {
  font-size: 9px;
  font-weight: 600;
  color: #f9ab00;
  cursor: default;
  margin-left: 1px;
  vertical-align: super;
  line-height: 0;
}

/* ── Margin comment cards (Google Docs style) ── */
.mc {
  border: 1px solid #dadce0;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #fff;
  font-size: 12px;
  line-height: 1.5;
  transition: box-shadow 0.15s;
  position: relative;
}
.mc:hover {
  box-shadow: 0 1px 6px rgba(0,0,0,0.12);
}
.mc.resolved {
  opacity: 0.7;
  border-color: #e8eaed;
}
.mc.resolved .mc-body {
  text-decoration: line-through;
  color: #80868b;
}
.mc.scope-section { border-left: 3px solid #1a73e8; }
.mc.scope-inline { border-left: 3px solid #f9ab00; }
.mc.scope-general { border-left: 3px solid #80868b; }

.mc-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.mc-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1a73e8;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}
.mc.scope-inline .mc-num { background: #f9ab00; }
.mc.scope-general .mc-num { background: #80868b; }

.mc-author {
  font-weight: 600;
  font-size: 12px;
  color: #202124;
}
.mc-provider {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #80868b;
}
.mc-status {
  margin-left: auto;
  font-size: 10px;
  font-weight: 500;
}
.mc-resolved { color: #137333; }

.mc-body {
  font-size: 12px;
  color: #3c4043;
  line-height: 1.5;
}

.mc-reply {
  margin-top: 6px;
  padding: 6px 8px;
  background: #f1f3f4;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.4;
  color: #3c4043;
}
.mc-reply-author {
  font-weight: 600;
  font-size: 11px;
  margin-right: 4px;
}

/* ── Bibliography ── */
.bib-section {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #dadce0;
}
.bib-section h2 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}
.bib-entry {
  font-size: 11px;
  margin-bottom: 4px;
  line-height: 1.5;
  color: #3c4043;
}
.bib-key {
  font-weight: 600;
  color: #1a73e8;
}
.bib-doi {
  font-size: 9px;
  color: #80868b;
}
.bib-empty {
  font-size: 12px;
  color: #80868b;
}
.cite-link {
  color: #1a73e8;
  border-bottom: 1px dotted #1a73e8;
}

/* ── Connector lines ── */
.connector-line {
  stroke: #dadce0;
  stroke-width: 1;
  fill: none;
}
.connector-dot {
  fill: #f9ab00;
}
"""


# ── JavaScript for positioning + connectors ──────────────────────────────────


def _get_js() -> str:
    return r"""
(function() {
  function position() {
    var docBody = document.getElementById('doc-body');
    var marginCol = document.getElementById('margin-comments');
    var svg = document.getElementById('connectors');
    var cards = marginCol.querySelectorAll('.mc');
    var container = document.querySelector('.page-container');
    var containerRect = container.getBoundingClientRect();

    // Reset SVG dimensions
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute('width', containerRect.width);
    svg.setAttribute('height', Math.max(containerRect.height, document.body.scrollHeight));

    var lastBottom = 0;

    cards.forEach(function(card) {
      var cid = card.getAttribute('data-cid');
      var sectionId = card.getAttribute('data-section');

      // Find the corresponding mark or heading in the document
      var mark = null;
      var cref = docBody.querySelector('sup[data-cref="' + cid + '"]');
      if (cref) {
        mark = cref.closest('mark.cm') || cref;
      }
      if (!mark && sectionId) {
        mark = docBody.querySelector('#sec-' + sectionId) ||
               docBody.querySelector('[data-section="' + sectionId + '"]');
      }

      if (!mark) return;

      var markRect = mark.getBoundingClientRect();
      var marginRect = marginCol.getBoundingClientRect();

      // Align card top with the mark vertical center
      var targetY = markRect.top - marginRect.top + (markRect.height / 2) - 12;
      var actualY = Math.max(targetY, lastBottom + 6);
      actualY = Math.max(actualY, 0);

      card.style.position = 'absolute';
      card.style.top = actualY + 'px';
      card.style.left = '8px';
      card.style.right = '16px';

      lastBottom = actualY + card.offsetHeight;

      // Draw connector: dot on mark → L-shaped line → card
      var markCenterY = markRect.top - containerRect.top + markRect.height / 2;
      var cardCenterY = marginRect.top - containerRect.top + actualY + 16;
      var markRight = markRect.right - containerRect.left;
      var marginLeft = marginRect.left - containerRect.left;

      var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      var midX = marginLeft - 4;

      if (Math.abs(markCenterY - cardCenterY) < 3) {
        path.setAttribute('d',
          'M ' + markRight + ' ' + markCenterY +
          ' L ' + marginLeft + ' ' + cardCenterY);
      } else {
        path.setAttribute('d',
          'M ' + markRight + ' ' + markCenterY +
          ' L ' + midX + ' ' + markCenterY +
          ' L ' + midX + ' ' + cardCenterY +
          ' L ' + marginLeft + ' ' + cardCenterY);
      }
      path.setAttribute('class', 'connector-line');
      svg.appendChild(path);

      var dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('cx', markRight);
      dot.setAttribute('cy', markCenterY);
      dot.setAttribute('r', '3');
      dot.setAttribute('class', 'connector-dot');
      svg.appendChild(dot);
    });

    marginCol.style.minHeight = (lastBottom + 40) + 'px';
  }

  if (document.readyState === 'complete') {
    position();
  } else {
    window.addEventListener('load', position);
  }
  // Chrome headless needs a brief delay for layout
  setTimeout(position, 500);
})();
"""
