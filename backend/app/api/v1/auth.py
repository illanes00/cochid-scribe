"""Auth API — session, current user, document ACL helpers.

Authentication is delegated to Authentik via OIDC. The OIDC login/callback/
logout routes are wired in app.main (using illanes_auth.OIDCHandler). This
module only provides:

- `/api/v1/auth/me`    → current user from session
- `/api/v1/auth/logout` → clear session (alternative to OIDC logout)
- Helper dependencies used by other routers: require_user(),
  require_document_read(), require_document_write().

Access model:
- Documents have `owner_id` (FK users.id) and `visibility` in {private, shared, public}.
- private: only owner can read or write.
- shared:  any authenticated user can read; only owner can write.
- public:  anyone (no auth) can read; only owner can write.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.user import User

router = APIRouter()


# ─── Session helpers ──────────────────────────────────────────────────────────


def _get_session_user(request: Request) -> dict[str, Any] | None:
    """Return raw session user dict (set by illanes_auth.OIDCHandler), or None."""
    user = request.session.get("user")
    if not isinstance(user, dict):
        return None
    email = user.get("email")
    if not isinstance(email, str) or not email.strip():
        return None
    return user


def is_authenticated(request: Request) -> bool:
    return _get_session_user(request) is not None


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Resolve the logged-in user to a User row. Upsert on first contact."""
    session_user = _get_session_user(request)
    if not session_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    email = session_user["email"].strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # First login for this email — auto-provision a row.
        user = User(
            email=email,
            display_name=session_user.get("name") or email.split("@")[0],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif session_user.get("name") and user.display_name != session_user["name"]:
        user.display_name = session_user["name"]
        db.commit()
    return user


def _maybe_user(request: Request, db: Session) -> User | None:
    """Like require_user but returns None if anonymous (no 401)."""
    if not is_authenticated(request):
        return None
    return require_user(request, db)


# ─── Document ACL helpers ─────────────────────────────────────────────────────


def _doc_or_404(db: Session, slug: str) -> Document:
    doc = db.query(Document).filter(Document.slug == slug).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def require_document_read(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Document:
    """Resolve a document the caller is allowed to *read* (or 404)."""
    doc = _doc_or_404(db, slug)
    visibility = getattr(doc, "visibility", "private") or "private"

    if visibility == "public":
        return doc

    user = _maybe_user(request, db)
    if user is None:
        # We treat private/shared docs as 404 for anonymous callers to avoid
        # leaking existence.
        raise HTTPException(status_code=404, detail="Document not found")

    if visibility == "shared":
        return doc
    # private
    if doc.owner_id and doc.owner_id == user.id:
        return doc
    raise HTTPException(status_code=404, detail="Document not found")


def require_document_write(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> tuple[Document, User]:
    """Resolve a document the caller is allowed to *write*. Returns (doc, user)."""
    doc = _doc_or_404(db, slug)
    user = require_user(request, db)
    if doc.owner_id and doc.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # Docs with no owner are write-protected to require explicit assignment.
    if not doc.owner_id:
        raise HTTPException(status_code=403, detail="Document has no owner; cannot write")
    return doc, user


# ─── Backwards-compat helpers (called by older routers) ──────────────────────
# These exist so we don't have to touch every router in this refactor. They
# implement the same access semantics as require_document_read but don't return
# the document (the caller does its own query).


def require_document_access(request: Request, slug: str) -> None:
    """[Compat] Raise 401/404 if the caller can't read this document."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        require_document_read(slug, request, db)
    finally:
        db.close()


def require_document_record_access(request: Request, document: Any) -> None:
    """[Compat] Same semantics as require_document_read, applied to an already-loaded doc."""
    if document is None:
        return
    visibility = getattr(document, "visibility", "private") or "private"
    if visibility == "public":
        return
    if not is_authenticated(request):
        raise HTTPException(status_code=404, detail="Document not found")
    if visibility == "shared":
        return
    # private — require ownership
    owner_id = getattr(document, "owner_id", None)
    if not owner_id:
        raise HTTPException(status_code=404, detail="Document not found")
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = require_user(request, db)
        if owner_id != user.id:
            raise HTTPException(status_code=404, detail="Document not found")
    finally:
        db.close()


# ─── Public endpoints ─────────────────────────────────────────────────────────


@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    """Get current user info from session, with role/profile."""
    session_user = _get_session_user(request)
    if not session_user:
        return {"authenticated": False, "user": None}
    user = require_user(request, db)
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "avatar_url": user.avatar_url,
        },
    }


@router.post("/logout")
async def logout(request: Request) -> dict:
    """Clear local session. Authentik logout is at /api/auth/logout (OIDC)."""
    request.session.clear()
    return {"ok": True}
