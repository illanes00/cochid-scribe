#!/usr/bin/env python3
"""
Genera un informe de trazabilidad (publicaciones + vínculos + claims) desde backend/scribe.db.

Uso:
  python scripts/generate_traceability_report.py --db backend/scribe.db --out docs/trazabilidad-publicaciones.md
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path


def fmt_dt(value: str | None) -> str:
    if not value:
        return ""
    # SQLite stores ISO strings; keep short for readability
    return value.replace("T", " ")[:19]


def google_url(doc_type: str, file_id: str) -> str:
    if doc_type == "presentation":
        return f"https://docs.google.com/presentation/d/{file_id}"
    return f"https://docs.google.com/document/d/{file_id}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="backend/scribe.db")
    parser.add_argument("--out", default="docs/trazabilidad-publicaciones.md")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, slug, title, doc_type, status, version, source_provider, source_id, updated_at
        FROM documents
        WHERE status = 'final'
        ORDER BY updated_at DESC
        """
    )
    docs = cur.fetchall()

    lines: list[str] = []
    lines.append("# Trazabilidad de publicaciones (Scribe)")
    lines.append("")
    lines.append(f"**Generado**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append(f"**DB**: `{db_path}`")
    lines.append("")
    lines.append("## Publicaciones")
    lines.append("")
    lines.append("| Slug | Tipo | Versión | Últ. actualización | Claims (verif/total) | Notas (KB) | Google |")
    lines.append("|------|------|--------|-------------------|----------------------|------------|--------|")

    for doc_id, slug, title, doc_type, status, version, source_provider, source_id, updated_at in docs:
        cur.execute("SELECT COUNT(*), SUM(CASE WHEN status='verified' THEN 1 ELSE 0 END) FROM claims WHERE document_id = ?", (doc_id,))
        total_claims, verified_claims = cur.fetchone()
        verified_claims = verified_claims or 0

        cur.execute(
            "SELECT COUNT(*) FROM links WHERE source_type='document' AND source_id=? AND target_type='note'",
            (doc_id,),
        )
        note_links = cur.fetchone()[0]

        google_cell = "—"
        if source_provider == "google" and source_id:
            google_cell = f"[abrir]({google_url(doc_type, source_id)})"

        lines.append(
            f"| `{slug}` | {doc_type} | {version} | {fmt_dt(updated_at)} | {verified_claims}/{total_claims} | {note_links} | {google_cell} |"
        )

    lines.append("")
    lines.append("## Flujo recomendado (TipTap + Google Drive)")
    lines.append("")
    lines.append("1. Conectar Google en `/integrations` (OAuth).")
    lines.append("2. Editar el documento en Scribe (TipTap).")
    lines.append("3. Guardar un snapshot en **Versions** antes de cambios mayores.")
    lines.append("4. Exportar a Google Docs/Slides desde el editor (menú ⋮).")
    lines.append("5. Sincronizar comentarios desde **Comments → Sync** (si está vinculado a Google).")
    lines.append("6. Revisar claims en **Claims** y vincularlos a la KB (notas) cuando aplique.")
    lines.append("")
    lines.append("Nota: la API soporta `folder_id` en export (Docs/Slides) para guardar en un folder específico.")
    lines.append("")
    lines.append("## Scripts de soporte")
    lines.append("")
    lines.append("- `python scripts/enrich_and_structure.py` — reestructura presentaciones y (re)detecta claims en policy briefs.")
    lines.append("- `python scripts/connect_claims_kb.py` — crea notas por claim y enlaces claim↔nota y documento↔nota.")
    lines.append("- `python scripts/fix_documents.py` — actualiza JSON TipTap desde Markdown (útil para reimportar).")
    lines.append("- `python scripts/create_kb_scaffolding.py` — crea notas de metodología y enlaces (documento/claim → metodología).")
    lines.append("- `python scripts/create_baseline_versions.py` — guarda snapshots en `document_versions` (Versions).")
    lines.append("- `python scripts/generate_claim_register.py` — genera `docs/registro-claims-bid-cif.md` desde la DB.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    conn.close()

    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
