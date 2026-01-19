#!/usr/bin/env python3
"""
Generate a claims register (markdown) from backend/scribe.db for editorial/evidence work.

Usage:
  python scripts/generate_claim_register.py --db backend/scribe.db --out docs/registro-claims-bid-cif.md
  python scripts/generate_claim_register.py --db backend/scribe.db --docs cif-medicamentos bid-seguridad-resumen
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path


def fmt_dt(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("T", " ")[:19]


def safe_json_loads(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except Exception:
        return []


def compact(text: str, max_len: int = 160) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1] + "…"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="backend/scribe.db")
    parser.add_argument("--out", default="docs/registro-claims-bid-cif.md")
    parser.add_argument(
        "--docs",
        nargs="*",
        default=["cif-medicamentos", "bid-seguridad-resumen"],
        help="Slugs de documentos a incluir en el registro",
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in args.docs)
    cur.execute(
        f"""
        SELECT d.id, d.slug, d.title, d.doc_type, d.status, d.updated_at
        FROM documents d
        WHERE d.slug IN ({placeholders})
        ORDER BY d.slug ASC
        """,
        tuple(args.docs),
    )
    docs = cur.fetchall()
    doc_by_id = {row[0]: row for row in docs}

    cur.execute(
        f"""
        SELECT c.id, c.claim_id, c.document_id, c.claim_text, c.claim_type, c.status, c.evidence, c.created_at, c.updated_at
        FROM claims c
        WHERE c.document_id IN ({",".join("?" for _ in doc_by_id.keys())})
        ORDER BY c.document_id ASC, c.created_at ASC
        """,
        tuple(doc_by_id.keys()),
    )
    claims = cur.fetchall()

    # Map claim_db_id -> note slug (if linked)
    note_slug_by_claim_db_id: dict[str, str] = {}
    if claims:
        claim_db_ids = [row[0] for row in claims]
        placeholders = ",".join("?" for _ in claim_db_ids)
        cur.execute(
            f"""
            SELECT l.source_id, n.slug
            FROM links l
            JOIN notes n ON n.id = l.target_id
            WHERE l.source_type='claim'
              AND l.target_type='note'
              AND l.link_type='reference'
              AND n.note_type='claim'
              AND l.source_id IN ({placeholders})
            """,
            tuple(claim_db_ids),
        )
        for source_id, note_slug in cur.fetchall():
            note_slug_by_claim_db_id[source_id] = note_slug

    # Stats per doc + overall
    stats_by_doc: dict[str, dict[str, int]] = {}
    for _, claim_id, document_id, _, _, status, evidence, _, _ in claims:
        doc_slug = doc_by_id[document_id][1]
        stats = stats_by_doc.setdefault(
            doc_slug, {"total": 0, "verified": 0, "draft": 0, "needs_revision": 0, "rejected": 0, "no_evidence": 0}
        )
        stats["total"] += 1
        stats[status or "draft"] = stats.get(status or "draft", 0) + 1
        ev = safe_json_loads(evidence)
        if not ev:
            stats["no_evidence"] += 1

    lines: list[str] = []
    lines.append("# Registro de claims (BID / CIF)")
    lines.append("")
    lines.append(f"**Generado**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append(f"**DB**: `{args.db}`")
    lines.append("")
    lines.append("Este registro sirve para trabajar evidencia y verificación (Claims ↔ KB) de manera trazable.")
    lines.append("")

    lines.append("## Resumen por documento")
    lines.append("")
    lines.append("| Documento | Claims | Sin evidencia | Verified | Needs revision | Rejected | Draft | Últ. actualización |")
    lines.append("|----------|--------|--------------|----------|----------------|----------|-------|-------------------|")
    for doc_id, slug, title, doc_type, status, updated_at in docs:
        stats = stats_by_doc.get(slug, {})
        lines.append(
            "| `{slug}` | {total} | {no_ev} | {ver} | {nr} | {rej} | {draft} | {upd} |".format(
                slug=slug,
                total=stats.get("total", 0),
                no_ev=stats.get("no_evidence", 0),
                ver=stats.get("verified", 0),
                nr=stats.get("needs_revision", 0),
                rej=stats.get("rejected", 0),
                draft=stats.get("draft", 0),
                upd=fmt_dt(updated_at),
            )
        )
    lines.append("")

    lines.append("## Claims (detalle)")
    lines.append("")
    lines.append("| Doc | Claim ID | Estado | Tipo | Evidencias | Nota KB | Texto |")
    lines.append("|-----|----------|--------|------|------------|---------|-------|")
    for claim_db_id, claim_id, document_id, claim_text, claim_type, status, evidence, created_at, updated_at in claims:
        doc_slug = doc_by_id[document_id][1]
        note_slug = note_slug_by_claim_db_id.get(claim_db_id, "—")
        ev = safe_json_loads(evidence)
        lines.append(
            "| `{doc}` | `{cid}` | {status} | {ctype} | {evc} | `{note}` | {txt} |".format(
                doc=doc_slug,
                cid=claim_id,
                status=status or "draft",
                ctype=claim_type or "MIXED",
                evc=len(ev) if isinstance(ev, list) else 0,
                note=note_slug,
                txt=compact(claim_text, 140).replace("|", "\\|"),
            )
        )

    lines.append("")
    lines.append("## Cómo trabajar (operativo)")
    lines.append("")
    lines.append("1. Abrir el documento en Scribe y revisar el panel **Claims**.")
    lines.append("2. Para cada claim, abrir su nota KB y completar:")
    lines.append("   - Fuente (dataset / documento / bibliografía)")
    lines.append("   - Definición de indicador, año y universo")
    lines.append("   - Observaciones (limitaciones / supuestos)")
    lines.append("3. Actualizar estado: `draft` → `verified` / `needs_revision` / `rejected`.")
    lines.append("4. Guardar snapshot en **Versions** antes de cambios grandes.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    conn.close()
    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
