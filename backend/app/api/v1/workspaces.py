"""Workspace endpoints for deterministic project bundles.

Workspaces are filesystem-backed bundles under ``docs/`` that expose the
canonical report markdown plus its review / verification / figure corpus.
Routes are parametrized by ``{workspace_slug}`` so future workspaces can
register their own document slug + report path without code changes.

For backwards compatibility, the legacy ``cif-medicamentos`` slug is registered
in ``WORKSPACE_REGISTRY`` so existing frontend callers keep working.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse

from app.api.v1.auth import require_document_access, require_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[4]
DOCS_ROOT = REPO_ROOT / "docs"

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".csv",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".yml",
    ".yaml",
    ".css",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


# Registry of known filesystem-backed workspaces.
# Each entry maps a workspace_slug to its on-disk layout. Adding a new workspace
# requires no code edits beyond appending here (or, later, moving to DB-backed
# registration). The recommended_document_slug is used by the frontend to
# resolve the workspace to a Document for ACL checks.
WORKSPACE_REGISTRY: dict[str, dict[str, Any]] = {
    "cif-medicamentos": {
        "title": "CIF Medicamentos Workspace",
        "description": (
            "Workspace determinista del informe CIF con texto base, corpus de revisión, "
            "scripts de verificación y figuras auditables."
        ),
        "report_file": "cif-medicamentos-resumen-final.md",
        "review_root": "cif-review",
        "recommended_document_slug": "cif-medicamentos-workspace",
        "report_title": "Resumen final CIF medicamentos",
    },
}


def _get_workspace(workspace_slug: str) -> dict[str, Any]:
    spec = WORKSPACE_REGISTRY.get(workspace_slug)
    if spec is None:
        raise HTTPException(status_code=404, detail="Workspace not registered")
    return spec


def _gate_workspace(request: Request, workspace_slug: str) -> None:
    """Resolve workspace access via the underlying Document's ACL."""
    spec = _get_workspace(workspace_slug)
    doc_slug = spec.get("recommended_document_slug")
    if doc_slug:
        # If the document doesn't exist yet, fall back to require_user so we
        # still 401 unauthenticated callers but don't 404 on the workspace.
        try:
            require_document_access(request, doc_slug)
            return
        except HTTPException as exc:
            if exc.status_code == 404:
                # Document not yet created → at least require an authenticated user.
                pass
            else:
                raise
    # No registered doc, or doc missing: require auth.
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Authentication required")


def _parse_sections(markdown: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        title = stripped[level:].strip()
        if title:
            sections.append({"level": level, "title": title})
    return sections


def _summarize_file(path: Path, workspace_slug: str) -> dict[str, Any]:
    relative = path.relative_to(DOCS_ROOT).as_posix()
    category = relative.split("/", 1)[0] if "/" in relative else "root"
    preview_url = f"/api/v1/workspaces/{workspace_slug}/asset?path={relative}"

    kind = "binary"
    if path.suffix.lower() in TEXT_SUFFIXES:
        kind = "text"
    elif path.suffix.lower() in IMAGE_SUFFIXES:
        kind = "image"

    return {
        "name": path.name,
        "relative_path": relative,
        "category": category,
        "kind": kind,
        "size_bytes": path.stat().st_size,
        "preview_url": preview_url,
    }


def _safe_resolve(relative_path: str) -> Path:
    candidate = (DOCS_ROOT / relative_path).resolve()
    if not str(candidate).startswith(str(DOCS_ROOT.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return candidate


def _build_workspace_bundle(workspace_slug: str) -> dict[str, Any]:
    spec = _get_workspace(workspace_slug)
    report_file = DOCS_ROOT / spec["report_file"]
    review_root = DOCS_ROOT / spec.get("review_root", "")

    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Workspace report not found")

    report_markdown = report_file.read_text(encoding="utf-8")
    sections = _parse_sections(report_markdown)

    source_files = [_summarize_file(report_file, workspace_slug)]
    verification_files: list[dict[str, Any]] = []
    figure_files: list[dict[str, Any]] = []
    review_files: list[dict[str, Any]] = []

    if review_root.exists() and review_root.is_dir():
        for file_path in sorted(p for p in review_root.rglob("*") if p.is_file()):
            summary = _summarize_file(file_path, workspace_slug)
            review_files.append(summary)
            if "/verification/" in summary["relative_path"]:
                verification_files.append(summary)
            if file_path.suffix.lower() in IMAGE_SUFFIXES:
                figure_files.append(summary)

    return {
        "workspace": {
            "slug": workspace_slug,
            "title": spec["title"],
            "description": spec["description"],
            "recommended_document_slug": spec["recommended_document_slug"],
        },
        "report": {
            "title": spec.get("report_title", spec["title"]),
            "relative_path": report_file.relative_to(DOCS_ROOT).as_posix(),
            "preview_url": (
                f"/api/v1/workspaces/{workspace_slug}/asset?"
                f"path={report_file.relative_to(DOCS_ROOT).as_posix()}"
            ),
            "sections": sections,
            "excerpt": report_markdown[:4000],
        },
        "sources": {
            "report_files": source_files,
            "review_files": review_files[:200],
            "verification_files": verification_files[:100],
            "figure_files": figure_files[:100],
        },
    }


@router.get("/{workspace_slug}")
def get_workspace(
    workspace_slug: str,
    request: Request,
    _: dict = Depends(require_user),
) -> dict[str, Any]:
    """Return deterministic bundle metadata for a registered workspace."""
    _gate_workspace(request, workspace_slug)
    return _build_workspace_bundle(workspace_slug)


@router.get("/{workspace_slug}/file", response_class=PlainTextResponse)
def get_workspace_file(
    workspace_slug: str,
    request: Request,
    path: str = Query(..., description="Relative path under docs/"),
    _: dict = Depends(require_user),
) -> str:
    """Return plain-text file contents from the workspace corpus."""
    _gate_workspace(request, workspace_slug)
    resolved = _safe_resolve(path)
    if resolved.suffix.lower() not in TEXT_SUFFIXES:
        raise HTTPException(status_code=400, detail="File is not a text preview")
    return resolved.read_text(encoding="utf-8", errors="replace")


@router.get("/{workspace_slug}/asset")
def get_workspace_asset(
    workspace_slug: str,
    request: Request,
    path: str = Query(..., description="Relative path under docs/"),
    _: dict = Depends(require_user),
) -> FileResponse:
    """Return a protected asset from a workspace corpus."""
    _gate_workspace(request, workspace_slug)
    resolved = _safe_resolve(path)
    return FileResponse(resolved)
