"""Stage 8: Entrega — sube docx a Drive y genera outputs para Benja."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

from googleapiclient.http import MediaFileUpload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.google import build_drive_service
from app.services.review_critic.io.state import load_stage
from app.services.review_critic.io.verification_ledger import load_ledger
from app.services.review_critic.schemas import (
    ClassifiedComment,
    EditPatch,
    QAReport,
    ReplyEntry,
    ResolvedDecision,
)

_log = logging.getLogger(__name__)

OUTPUT_DIR = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/output")
DOCX_FILE = OUTPUT_DIR / "informe-final-revisado.docx"
SUMMARY_MD = OUTPUT_DIR / "tabla-decisiones-91.md"
EMAIL_DRAFT = OUTPUT_DIR / "email-benja-draft.md"
MASTER_DOC = OUTPUT_DIR / "80_benja_summary.md"


def get_drive():
    engine = create_engine("sqlite:///scribe.db")
    Session = sessionmaker(bind=engine)
    db = Session()
    return build_drive_service(db), db


def upload_docx_to_drive(docx: Path) -> tuple[str, str]:
    """Upload docx as Google Doc. Returns (doc_id, url)."""
    drive, db = get_drive()
    try:
        media = MediaFileUpload(
            str(docx),
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        body = {
            "name": "[CIF-EP] Informe Medicamentos — Revisión Crítica IA",
            "mimeType": "application/vnd.google-apps.document",
        }
        result = drive.files().create(
            body=body, media_body=media, fields="id,webViewLink"
        ).execute()
        doc_id = result["id"]
        url = result.get(
            "webViewLink",
            f"https://docs.google.com/document/d/{doc_id}/edit",
        )
        return doc_id, url
    finally:
        db.close()


def upload_summary_to_drive(md_path: Path, name: str) -> tuple[str, str]:
    """Upload markdown as Google Doc. Returns (doc_id, url)."""
    drive, db = get_drive()
    try:
        media = MediaFileUpload(str(md_path), mimetype="text/markdown")
        body = {
            "name": name,
            "mimeType": "application/vnd.google-apps.document",
        }
        result = drive.files().create(
            body=body, media_body=media, fields="id,webViewLink"
        ).execute()
        doc_id = result["id"]
        url = result.get(
            "webViewLink",
            f"https://docs.google.com/document/d/{doc_id}/edit",
        )
        return doc_id, url
    finally:
        db.close()


def generate_summary_table(
    decisions: list[ResolvedDecision],
    classified: list[ClassifiedComment],
    edits: list[EditPatch],
    replies: list[ReplyEntry],
) -> str:
    """Generate a markdown summary table."""
    classified_by_id = {c.id: c for c in classified}
    edits_by_comment: dict[str, list[EditPatch]] = {}
    for e in edits:
        for cid in e.source_comment_ids:
            edits_by_comment.setdefault(cid, []).append(e)
    replies_by_id = {r.comment_id: r for r in replies}

    rec_counts = Counter(d.final_recommendation for d in decisions)
    edit_counts = Counter(e.scope for e in edits)
    label_counts = Counter(r.decision_label for r in replies)
    by_author = Counter(c.author for c in classified)

    lines = []
    lines.append("# Tabla de Decisiones — Revisión Crítica del Informe CIF-EP")
    lines.append("")
    lines.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Total comentarios:** {len(decisions)}")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append("### Por decisión")
    lines.append("")
    for rec, n in rec_counts.most_common():
        pct = 100 * n / len(decisions)
        lines.append(f"- **{rec}**: {n} ({pct:.1f}%)")
    lines.append("")
    lines.append("### Por autor")
    lines.append("")
    for author, n in by_author.most_common():
        lines.append(f"- {author}: {n}")
    lines.append("")
    lines.append("### Edits generados")
    lines.append(f"- Total: {len(edits)}")
    for scope, n in edit_counts.items():
        lines.append(f"- **{scope}**: {n}")
    lines.append("")

    # Top facts (from ledger)
    ledger = load_ledger()
    refuted = [f for f in ledger.facts if f.status == "refuted"]
    if refuted:
        lines.append("## Discrepancias factuales detectadas")
        lines.append("")
        for f in refuted:
            lines.append(f"### {f.claim_id}")
            lines.append(f"**Claim:** {f.claim_text}")
            lines.append(f"**Evidencia:** {f.evidence}")
            lines.append(f"**Fuente autoritativa:** {f.authoritative_source}")
            lines.append("")

    # Per-comment table
    lines.append("## Detalle por comentario")
    lines.append("")
    lines.append("| ID | Autor | Tipo | Decisión | Edit | Justificación |")
    lines.append("|----|-------|------|----------|------|---------------|")
    for d in decisions:
        c = classified_by_id.get(d.comment_id)
        if not c:
            continue
        edit_marker = "✓" if edits_by_comment.get(d.comment_id) else ""
        if d.requires_director_approval:
            edit_marker += " ⚠️"
        reasoning = (d.final_reasoning or "")[:120].replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {d.comment_id} | {c.author[:25]} | {c.type} | "
            f"{d.final_recommendation} | {edit_marker} | {reasoning} |"
        )
    lines.append("")

    return "\n".join(lines)


def generate_email_draft(
    decisions: list[ResolvedDecision],
    edits: list[EditPatch],
    google_doc_url: str,
    summary_url: str,
) -> str:
    """Generate WhatsApp/email draft for Benja."""
    rec_counts = Counter(d.final_recommendation for d in decisions)

    n_accept = rec_counts.get("ACCEPT", 0) + rec_counts.get("ACCEPT_PARTIAL", 0)
    n_reject = rec_counts.get("REJECT", 0)
    n_defer = rec_counts.get("DEFER", 0)
    n_data = rec_counts.get("NEEDS_DATA", 0)

    return f"""Hola Benja!

Quería compartirte el avance: hice una revisión crítica completa de los 91 comentarios del informe de medicamentos y dejé propuestas de cambio como sugerencias en Google Docs.

**Resumen:**
- {n_accept} comentarios aceptados (con edición aplicada como sugerencia)
- {n_reject} rechazados con justificación basada en evidencia
- {n_defer} pendientes de tu/de los directores decisión
- {n_data} pendientes de verificación de datos
- {len(edits)} cambios propuestos en total

**Documento principal (con sugerencias modo Sugerir):**
{google_doc_url}

**Tabla de decisiones (resumen ejecutivo por comentario):**
{summary_url}

**Hallazgos factuales relevantes:**
- GES: el informe dice 87 patologías, en realidad son 90 (Decreto 2025-2028)
- US$206 está mal atribuido (es OMS GHED 2022, no OECD 2025; corrientes no PPA)
- Costa Rica CCSS: dice 95%, real es 86.4% (Encuesta Actualidades 2024)
- Mediana OCDE retail per cápita: dice US$600, real ~US$533-550
- 71% del retail OOP: requiere combinar EPF (28% solo en EPF) + datos públicos

Cuando lo revises, podés ir aceptando/rechazando las sugerencias directo en el doc. Yo dejé replies en cada comentario explicando la decisión.

Saludos,
Martín
"""


def run() -> dict:
    """Run delivery: assemble docx, upload to Drive, generate outputs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    decisions = load_stage("41_resolved_decisions.json", ResolvedDecision)
    classified = load_stage("10_classified.json", ClassifiedComment)
    edits = load_stage("50_edit_patches.json", EditPatch)
    replies = load_stage("60_replies.json", ReplyEntry)

    print(f"Decisions: {len(decisions)}, Edits: {len(edits)}, Replies: {len(replies)}")

    # Generate summary table
    summary_md = generate_summary_table(decisions, classified, edits, replies)
    SUMMARY_MD.write_text(summary_md)
    print(f"Summary written: {SUMMARY_MD}")

    # Upload docx to Drive
    if DOCX_FILE.exists():
        doc_id, doc_url = upload_docx_to_drive(DOCX_FILE)
        print(f"Docx uploaded: {doc_url}")
    else:
        doc_url = "(docx not found — run docx_assembler.run() first)"
        doc_id = None

    # Upload summary
    summary_doc_id, summary_url = upload_summary_to_drive(
        SUMMARY_MD, "[CIF-EP] Tabla Decisiones Revisión IA"
    )
    print(f"Summary uploaded: {summary_url}")

    # Generate email draft
    email_text = generate_email_draft(decisions, edits, doc_url, summary_url)
    EMAIL_DRAFT.write_text(email_text)
    print(f"Email draft: {EMAIL_DRAFT}")

    # Master summary
    master = f"""# Entrega Final — Revisión Crítica Informe CIF-EP

## Outputs

- **Documento revisado** (con sugerencias modo Sugerir): {doc_url}
- **Tabla de decisiones**: {summary_url}
- **Email draft para Benja**: `{EMAIL_DRAFT}`
- **Docx local**: `{DOCX_FILE}`

## Stats

- Comentarios procesados: {len(decisions)}
- Edits aplicados: {len(edits)}
- Replies generados: {len(replies)}
"""
    MASTER_DOC.write_text(master)
    print(f"Master: {MASTER_DOC}")

    return {
        "doc_url": doc_url,
        "summary_url": summary_url,
        "email_draft": str(EMAIL_DRAFT),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(run())
