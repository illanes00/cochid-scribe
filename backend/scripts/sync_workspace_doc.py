"""Bidirectional sync between docs/cif-medicamentos-resumen-final.md and the
cif-medicamentos-workspace document in scribe.db.

Modes (mutually exclusive):
    --pull   DB -> .md   (export workspace markdown to file)
    --push   .md -> DB   (import file into workspace document)
    --check  show timestamps + byte-diff, no writes (default)

Safety: by default refuses to overwrite when the destination is newer than the
source. Pass --force to override.

Usage:
    cd /srv/projects/cochid/cochid-scribe/backend
    source .venv/bin/activate
    python scripts/sync_workspace_doc.py --check
    python scripts/sync_workspace_doc.py --push          # .md  -> DB
    python scripts/sync_workspace_doc.py --pull          # DB   -> .md
    python scripts/sync_workspace_doc.py --push --force  # ignore newer-dest guard
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models import Document

SLUG = 'cif-medicamentos-workspace'
MD_PATH = Path(__file__).resolve().parents[2] / 'docs' / 'cif-medicamentos-resumen-final.md'


def _db_doc(session):
    doc = session.query(Document).filter(Document.slug == SLUG).first()
    if doc is None:
        raise SystemExit(f'No document with slug={SLUG} in DB')
    return doc


def _file_mtime_aware(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _db_updated_at_aware(doc) -> datetime:
    ts = doc.updated_at
    if ts is None:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


def cmd_check() -> int:
    session = SessionLocal()
    try:
        doc = _db_doc(session)
        db_md = doc.markdown or ''
        file_md = MD_PATH.read_text() if MD_PATH.exists() else ''
        db_ts = _db_updated_at_aware(doc)
        file_ts = _file_mtime_aware(MD_PATH) if MD_PATH.exists() else None
        print(f'DB   slug={SLUG}')
        print(f'     bytes={len(db_md)}  lines={db_md.count(chr(10))+1}  updated_at={db_ts.isoformat()}')
        print(f'File {MD_PATH}')
        print(f'     bytes={len(file_md)}  lines={file_md.count(chr(10))+1}  mtime={file_ts.isoformat() if file_ts else "missing"}')
        if db_md == file_md:
            print('STATE: in-sync (bit-identical)')
            return 0
        print(f'STATE: diverged ({len(file_md)-len(db_md):+d} bytes file vs db)')
        if file_ts and file_ts > db_ts:
            print('       file is NEWER -> --push would overwrite DB safely')
        elif file_ts and file_ts < db_ts:
            print('       DB is NEWER -> --pull would overwrite file safely')
        return 1
    finally:
        session.close()


def cmd_push(force: bool) -> int:
    session = SessionLocal()
    try:
        doc = _db_doc(session)
        if not MD_PATH.exists():
            raise SystemExit(f'Missing {MD_PATH}')
        file_md = MD_PATH.read_text()
        if file_md == (doc.markdown or ''):
            print('Already in sync, nothing to push.')
            return 0
        db_ts = _db_updated_at_aware(doc)
        file_ts = _file_mtime_aware(MD_PATH)
        if db_ts > file_ts and not force:
            print(f'REFUSE: DB updated_at={db_ts.isoformat()} > file mtime={file_ts.isoformat()}.')
            print('       Pass --force to overwrite DB anyway, or --pull first.')
            return 2
        doc.markdown = file_md
        doc.updated_at = datetime.now(tz=timezone.utc)
        session.commit()
        print(f'PUSHED file -> DB (bytes {len(file_md)}, updated_at={doc.updated_at.isoformat()})')
        return 0
    finally:
        session.close()


def cmd_pull(force: bool) -> int:
    session = SessionLocal()
    try:
        doc = _db_doc(session)
        db_md = doc.markdown or ''
        if MD_PATH.exists() and MD_PATH.read_text() == db_md:
            print('Already in sync, nothing to pull.')
            return 0
        db_ts = _db_updated_at_aware(doc)
        if MD_PATH.exists():
            file_ts = _file_mtime_aware(MD_PATH)
            if file_ts > db_ts and not force:
                print(f'REFUSE: file mtime={file_ts.isoformat()} > DB updated_at={db_ts.isoformat()}.')
                print('       Pass --force to overwrite file anyway, or --push first.')
                return 2
        MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        MD_PATH.write_text(db_md)
        new_mtime = db_ts.timestamp()
        os.utime(MD_PATH, (new_mtime, new_mtime))
        print(f'PULLED DB -> file ({MD_PATH}, bytes {len(db_md)}, mtime aligned to DB updated_at)')
        return 0
    finally:
        session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='show timestamps + byte-diff (default)')
    group.add_argument('--pull', action='store_true', help='DB -> .md')
    group.add_argument('--push', action='store_true', help='.md -> DB')
    parser.add_argument('--force', action='store_true', help='ignore newer-destination guard')
    args = parser.parse_args()
    if args.push:
        return cmd_push(args.force)
    if args.pull:
        return cmd_pull(args.force)
    return cmd_check()


if __name__ == '__main__':
    sys.exit(main())
