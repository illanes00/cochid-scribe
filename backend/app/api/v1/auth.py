"""Auth API — current user info and workspace access."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import compare_digest
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()
settings = get_settings()
PROTECTED_DOCUMENTS = {"cif-medicamentos-workspace"}
PROTECTED_WORKSPACES = {"cif-medicamentos"}
SESSION_TTL_SECONDS = 60 * 60 * 8


class WorkspaceLoginRequest(BaseModel):
    password: str


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_session_expiry(raw_value: Any) -> datetime | None:
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value, tz=timezone.utc)
    if isinstance(raw_value, str):
        normalized = raw_value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _get_session_user(request: Request) -> dict[str, Any] | None:
    user = request.session.get("user")
    if not isinstance(user, dict):
        request.session.pop("user", None)
        request.session.pop("auth_expires_at", None)
        return None

    email = user.get("email")
    if not isinstance(email, str) or not email.strip():
        request.session.clear()
        return None

    expires_at = _parse_session_expiry(request.session.get("auth_expires_at"))
    if expires_at and expires_at <= _now_utc():
        request.session.clear()
        return None

    return user


def is_authenticated(request: Request) -> bool:
    """Return whether the request has an authenticated session."""
    return _get_session_user(request) is not None


def is_protected_workspace_slug(workspace_slug: str | None) -> bool:
    return bool(workspace_slug and workspace_slug in PROTECTED_WORKSPACES)


def is_protected_document_slug(slug: str | None) -> bool:
    return bool(slug and slug in PROTECTED_DOCUMENTS)


def is_protected_document_record(document: Any) -> bool:
    slug = getattr(document, "slug", None)
    if is_protected_document_slug(slug):
        return True

    front_matter = getattr(document, "front_matter", None)
    if isinstance(front_matter, dict):
        workspace_slug = front_matter.get("workspace_slug")
        if is_protected_workspace_slug(workspace_slug):
            return True

    return False


def require_workspace_access(request: Request, workspace_slug: str) -> None:
    """Protect selected workspace slugs behind session auth."""
    if is_protected_workspace_slug(workspace_slug) and not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")


def require_user(request: Request) -> dict:
    """Enforce a logged-in session."""
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_document_access(request: Request, slug: str) -> None:
    """Protect selected document slugs behind session auth."""
    if is_protected_document_slug(slug) and not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")


def require_document_record_access(request: Request, document: Any) -> None:
    """Protect CIF-linked documents behind session auth even if slug differs."""
    if is_protected_document_record(document) and not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")


@router.get("/me")
async def get_current_user(request: Request) -> dict:
    """Get current user info from session."""
    user = _get_session_user(request)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


@router.post("/logout")
async def logout(request: Request) -> dict:
    """Clear session."""
    request.session.clear()
    return {"ok": True}


@router.post("/workspace-login")
async def workspace_login(data: WorkspaceLoginRequest, request: Request) -> dict:
    """Authenticate access to protected CIF workspace routes."""
    if not settings.workspace_access_password:
        raise HTTPException(status_code=503, detail="Workspace password is not configured")
    provided_password = data.password or ""
    expected_password = settings.workspace_access_password
    if not provided_password or not compare_digest(provided_password, expected_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    request.session["user"] = {
        "email": "workspace@illanes00.local",
        "name": "Workspace User",
        "role": "owner",
    }
    request.session["auth_expires_at"] = (_now_utc() + timedelta(seconds=SESSION_TTL_SECONDS)).isoformat()
    return {"ok": True, "authenticated": True, "user": request.session["user"]}
