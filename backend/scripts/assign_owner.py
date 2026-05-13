"""Assign a Document to a user and mark it private + dictation workspace.

Usage:
    python -m backend.scripts.assign_owner \\
        --email martinillanesv@gmail.com \\
        --doc-slug cif-medicamentos-workspace

Behavior:
    1. Upsert a User row by email. Creates with display_name=email.split('@')[0]
       if not present.
    2. Find the Document by slug. Set:
        - owner_id = user.id
        - visibility = 'private'
        - front_matter['workspace_type'] = 'dictation'
    3. Print before/after values for verification.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.user import User


def upsert_user(db, email: str) -> User:
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user
    user = User(
        email=email,
        display_name=email.split("@", 1)[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[user] created id={user.id} email={user.email}")
    return user


def assign(email: str, doc_slug: str) -> int:
    db = SessionLocal()
    try:
        user = upsert_user(db, email)
        doc = db.query(Document).filter(Document.slug == doc_slug).first()
        if doc is None:
            print(f"ERROR: document slug={doc_slug} not found", file=sys.stderr)
            return 2

        before: dict[str, Any] = {
            "owner_id": doc.owner_id,
            "visibility": doc.visibility,
            "front_matter.workspace_type": (doc.front_matter or {}).get("workspace_type"),
        }

        doc.owner_id = user.id
        doc.visibility = "private"
        front_matter = dict(doc.front_matter or {})
        front_matter["workspace_type"] = "dictation"
        doc.front_matter = front_matter

        db.commit()
        db.refresh(doc)

        after: dict[str, Any] = {
            "owner_id": doc.owner_id,
            "visibility": doc.visibility,
            "front_matter.workspace_type": (doc.front_matter or {}).get("workspace_type"),
        }

        print(f"[user] id={user.id} email={user.email} display_name={user.display_name}")
        print(f"[doc]  id={doc.id} slug={doc.slug} title={doc.title}")
        print(f"[doc]  before: {before}")
        print(f"[doc]  after:  {after}")
        return 0
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="User email to assign as owner")
    parser.add_argument(
        "--doc-slug",
        default="cif-medicamentos-workspace",
        help="Document slug to assign (default: cif-medicamentos-workspace)",
    )
    args = parser.parse_args()
    return assign(args.email, args.doc_slug)


if __name__ == "__main__":
    sys.exit(main())
