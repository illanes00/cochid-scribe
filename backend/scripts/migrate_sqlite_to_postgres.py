"""One-shot SQLite → Postgres migration for the scribe DB.

Usage:
    python -m backend.scripts.migrate_sqlite_to_postgres \\
        --sqlite backend/scribe.db \\
        --postgres "postgresql://cochid_scribe:***@127.0.0.1:6432/cochid_scribe"

If --postgres is omitted, falls back to DATABASE_URL in the environment.

Behavior:
    * Reads schema from Postgres (SQLAlchemy MetaData reflect).
    * Inserts rows in FK dependency order (topological sort).
    * Skips alembic_version (schema migrated separately via alembic upgrade).
    * Batches at 1000 rows for tables > 10k rows; otherwise commits per table.
    * On FK / unique violations, logs the row and skips it — does not abort.
    * Prints row counts before/after per table.

Intentionally uses psycopg2 (sync) + sqlite3 stdlib to keep the dependency
surface tiny. The scribe.db is < 10 MB so streaming / COPY is overkill.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from typing import Any, Iterable

from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

SKIP_TABLES = {"alembic_version"}
BATCH_THRESHOLD = 10_000
BATCH_SIZE = 1_000


def _topo_sort(metadata: MetaData) -> list[Table]:
    """Return tables in FK dependency order (parents before children)."""
    return list(metadata.sorted_tables)


def _sqlite_tables(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cur.fetchall()}


def _sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def _sqlite_row_count(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
    return int(cur.fetchone()[0])


def _pg_row_count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        result = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {table}")
        return int(result.scalar() or 0)


def _coerce_row(row: sqlite3.Row, sqlite_cols: list[str], pg_cols: set[str]) -> dict[str, Any]:
    """Map a sqlite row to a dict, only including columns also in the PG table."""
    out: dict[str, Any] = {}
    for col in sqlite_cols:
        if col not in pg_cols:
            continue
        out[col] = row[col]
    return out


def _insert_rows(engine: Engine, table: Table, rows: Iterable[dict[str, Any]]) -> tuple[int, int]:
    """Insert rows one by one, skipping failures. Returns (inserted, skipped)."""
    inserted = 0
    skipped = 0
    for row in rows:
        try:
            with engine.begin() as conn:
                conn.execute(table.insert().values(**row))
            inserted += 1
        except (IntegrityError, SQLAlchemyError) as exc:
            skipped += 1
            print(
                f"  ! skip row in {table.name}: {type(exc).__name__}: {str(exc)[:140]}",
                file=sys.stderr,
            )
    return inserted, skipped


def _insert_batch(engine: Engine, table: Table, rows: list[dict[str, Any]]) -> tuple[int, int]:
    """Try a bulk insert; on failure, fall back to per-row inserts."""
    if not rows:
        return 0, 0
    try:
        with engine.begin() as conn:
            conn.execute(table.insert(), rows)
        return len(rows), 0
    except (IntegrityError, SQLAlchemyError):
        # Fall back: row-by-row to identify the bad ones.
        return _insert_rows(engine, table, rows)


def migrate(sqlite_path: str, pg_url: str) -> int:
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    pg_engine = create_engine(pg_url, pool_pre_ping=True)
    metadata = MetaData()
    metadata.reflect(bind=pg_engine)

    sqlite_table_names = _sqlite_tables(sqlite_conn)
    tables_in_order = _topo_sort(metadata)

    print(f"[migrate] sqlite={sqlite_path}")
    print(f"[migrate] postgres tables={len(tables_in_order)}  sqlite tables={len(sqlite_table_names)}")
    print()

    grand_inserted = 0
    grand_skipped = 0

    for table in tables_in_order:
        name = table.name
        if name in SKIP_TABLES:
            print(f"[skip] {name} (skip list)")
            continue
        if name not in sqlite_table_names:
            print(f"[skip] {name} (not in sqlite)")
            continue

        sqlite_cols = _sqlite_columns(sqlite_conn, name)
        pg_cols = {c.name for c in table.columns}
        common_cols = [c for c in sqlite_cols if c in pg_cols]
        if not common_cols:
            print(f"[skip] {name} (no overlapping columns)")
            continue

        before_sqlite = _sqlite_row_count(sqlite_conn, name)
        before_pg = _pg_row_count(pg_engine, name)
        if before_sqlite == 0:
            print(f"[{name}] sqlite=0 pg={before_pg} → nothing to copy")
            continue

        print(f"[{name}] sqlite={before_sqlite} pg(before)={before_pg} cols={len(common_cols)}")

        cursor = sqlite_conn.execute(
            f"SELECT {','.join(common_cols)} FROM {name}"
        )

        inserted_table = 0
        skipped_table = 0

        if before_sqlite > BATCH_THRESHOLD:
            batch: list[dict[str, Any]] = []
            for row in cursor:
                batch.append(_coerce_row(row, common_cols, pg_cols))
                if len(batch) >= BATCH_SIZE:
                    ins, skp = _insert_batch(pg_engine, table, batch)
                    inserted_table += ins
                    skipped_table += skp
                    batch.clear()
            if batch:
                ins, skp = _insert_batch(pg_engine, table, batch)
                inserted_table += ins
                skipped_table += skp
        else:
            rows = [_coerce_row(r, common_cols, pg_cols) for r in cursor]
            ins, skp = _insert_batch(pg_engine, table, rows)
            inserted_table += ins
            skipped_table += skp

        after_pg = _pg_row_count(pg_engine, name)
        print(
            f"[{name}] inserted={inserted_table} skipped={skipped_table} "
            f"pg(after)={after_pg}"
        )
        grand_inserted += inserted_table
        grand_skipped += skipped_table

    sqlite_conn.close()
    print()
    print(f"[done] total inserted={grand_inserted} total skipped={grand_skipped}")
    return 0 if grand_skipped == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite",
        default="backend/scribe.db",
        help="Path to source SQLite DB (default: backend/scribe.db)",
    )
    parser.add_argument(
        "--postgres",
        default=None,
        help="Postgres DATABASE_URL. If omitted, reads DATABASE_URL env var.",
    )
    args = parser.parse_args()

    pg_url = args.postgres or os.environ.get("DATABASE_URL")
    if not pg_url:
        print(
            "ERROR: pass --postgres or set DATABASE_URL env var",
            file=sys.stderr,
        )
        return 2
    if not os.path.exists(args.sqlite):
        print(f"ERROR: sqlite db not found at {args.sqlite}", file=sys.stderr)
        return 2

    return migrate(args.sqlite, pg_url)


if __name__ == "__main__":
    sys.exit(main())
