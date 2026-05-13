"""Workspace endpoints for deterministic project bundles."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse

from app.api.v1.auth import require_user, require_workspace_access
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[4]
DOCS_ROOT = REPO_ROOT / "docs"
WORKSPACE_SLUG = "cif-medicamentos"
REPORT_FILE = DOCS_ROOT / "cif-medicamentos-resumen-final.md"
REVIEW_ROOT = DOCS_ROOT / "cif-review"

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


def _summarize_file(path: Path) -> dict[str, Any]:
    relative = path.relative_to(DOCS_ROOT).as_posix()
    category = relative.split("/", 1)[0] if "/" in relative else "root"
    preview_url = f"/api/v1/workspaces/cif-medicamentos/asset?path={relative}"

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


def _build_workspace_bundle() -> dict[str, Any]:
    if not REPORT_FILE.exists():
        raise HTTPException(status_code=404, detail="Workspace report not found")

    report_markdown = REPORT_FILE.read_text(encoding="utf-8")
    sections = _parse_sections(report_markdown)

    source_files = [_summarize_file(REPORT_FILE)]
    verification_files: list[dict[str, Any]] = []
    figure_files: list[dict[str, Any]] = []
    review_files: list[dict[str, Any]] = []

    if REVIEW_ROOT.exists():
        for file_path in sorted(p for p in REVIEW_ROOT.rglob("*") if p.is_file()):
            summary = _summarize_file(file_path)
            review_files.append(summary)
            if "/verification/" in summary["relative_path"]:
                verification_files.append(summary)
            if file_path.suffix.lower() in IMAGE_SUFFIXES:
                figure_files.append(summary)

    bundle = {
        "workspace": {
            "slug": WORKSPACE_SLUG,
            "title": "CIF Medicamentos Workspace",
            "description": (
                "Workspace determinista del informe CIF con texto base, corpus de revisión, "
                "scripts de verificación y figuras auditables."
            ),
            "recommended_document_slug": "cif-medicamentos-workspace",
        },
        "report": {
            "title": "Resumen final CIF medicamentos",
            "relative_path": REPORT_FILE.relative_to(DOCS_ROOT).as_posix(),
            "preview_url": (
                f"/api/v1/workspaces/cif-medicamentos/asset?"
                f"path={REPORT_FILE.relative_to(DOCS_ROOT).as_posix()}"
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
    return bundle


@router.get("/cif-medicamentos")
def get_cif_workspace(request: Request, _: dict = Depends(require_user)) -> dict[str, Any]:
    """Return deterministic bundle metadata for the CIF medications workspace."""
    require_workspace_access(request, WORKSPACE_SLUG)
    return _build_workspace_bundle()


@router.get("/cif-medicamentos/file", response_class=PlainTextResponse)
def get_cif_workspace_file(
    request: Request,
    path: str = Query(..., description="Relative path under docs/"),
    _: dict = Depends(require_user),
) -> str:
    """Return plain-text file contents from the workspace corpus."""
    require_workspace_access(request, WORKSPACE_SLUG)
    resolved = _safe_resolve(path)
    if resolved.suffix.lower() not in TEXT_SUFFIXES:
        raise HTTPException(status_code=400, detail="File is not a text preview")
    return resolved.read_text(encoding="utf-8", errors="replace")


@router.get("/cif-medicamentos/asset")
def get_cif_workspace_asset(
    request: Request,
    path: str = Query(..., description="Relative path under docs/"),
    _: dict = Depends(require_user),
) -> FileResponse:
    """Return a protected asset from the CIF workspace corpus."""
    require_workspace_access(request, WORKSPACE_SLUG)
    resolved = _safe_resolve(path)
    return FileResponse(resolved)
