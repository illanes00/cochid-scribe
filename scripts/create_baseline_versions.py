#!/usr/bin/env python3
"""
Create baseline snapshots in document_versions for reproducible publishing.

Usage:
  python scripts/create_baseline_versions.py --db backend/scribe.db --label "BASELINE 2026-01-16 UTC"
  python scripts/create_baseline_versions.py --db backend/scribe.db --slugs cif-medicamentos bid-seguridad-final
"""

from __future__ import annotations

import argparse
import sqlite3
import uuid
from datetime import datetime


def now_iso() -> str:
    return datetime.utcnow().isoformat(sep=" ")


def create_version(
    cur: sqlite3.Cursor,
    document_id: str,
    label: str,
    content: str,
    markdown: str,
) -> bool:
    cur.execute(
        "SELECT id FROM document_versions WHERE document_id = ? AND label = ?",
        (document_id, label),
    )
    if cur.fetchone():
        return False

    cur.execute(
        """
        INSERT INTO document_versions (id, document_id, label, content, markdown, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), document_id, label, content, markdown or "", now_iso()),
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="backend/scribe.db")
    parser.add_argument(
        "--label",
        default=None,
        help="Etiqueta para la versión (por defecto: BASELINE <UTC timestamp>)",
    )
    parser.add_argument(
        "--slugs",
        nargs="*",
        default=None,
        help="Slugs específicos a snapshotear (por defecto: todos los status='final')",
    )
    args = parser.parse_args()

    label = args.label or f"BASELINE {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    if args.slugs:
        placeholders = ",".join("?" for _ in args.slugs)
        cur.execute(
            f"""
            SELECT id, slug, content, markdown
            FROM documents
            WHERE slug IN ({placeholders})
            """,
            tuple(args.slugs),
        )
    else:
        cur.execute(
            """
            SELECT id, slug, content, markdown
            FROM documents
            WHERE status='final'
            ORDER BY updated_at DESC
            """
        )

    rows = cur.fetchall()
    created = 0
    skipped = 0

    for doc_id, slug, content, markdown in rows:
        if create_version(cur, doc_id, label, content, markdown):
            created += 1
            print(f"OK: version created for {slug} ({label})")
        else:
            skipped += 1
            print(f"SKIP: version exists for {slug} ({label})")

    conn.commit()
    conn.close()

    print(f"Done: created={created}, skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

