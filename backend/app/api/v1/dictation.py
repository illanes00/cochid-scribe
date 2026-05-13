"""Chunked dictation endpoints for workspace authoring flows."""

from __future__ import annotations

import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from openai import OpenAI
from sqlalchemy.orm import Session

from app.api.v1.auth import require_user
from app.api.v1.workspaces import WORKSPACE_REGISTRY
from app.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.dictation_session import DictationSession
from app.models.document import Document

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()

REPO_ROOT = Path(__file__).resolve().parents[4]
DOCS_ROOT = REPO_ROOT / "docs"
PRIVATE_UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "private_uploads" / "dictation"
PRIVATE_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    base = text.lower().strip()
    base = re.sub(r"[^\w\s-]", "", base)
    base = re.sub(r"[\s_]+", "-", base)
    return re.sub(r"-+", "-", base).strip("-") or str(uuid.uuid4())[:8]


def _get_openai_client() -> OpenAI:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the server",
        )
    return OpenAI(api_key=settings.openai_api_key)


def _serialize_session(session: DictationSession) -> dict[str, Any]:
    sanitized_chunk_log = []
    for chunk in session.chunk_log or []:
        sanitized_chunk_log.append(
            {
                "chunk_index": chunk.get("chunk_index"),
                "file_name": chunk.get("file_name"),
                "transcript": chunk.get("transcript"),
                "created_at": chunk.get("created_at"),
            }
        )

    return {
        "id": session.id,
        "slug": session.slug,
        "title": session.title,
        "workspace_slug": session.workspace_slug,
        "document_slug": session.document_slug,
        "status": session.status,
        "transcript": session.transcript,
        "notes": session.notes,
        "chunk_count": session.chunk_count,
        "chunk_log": sanitized_chunk_log,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@router.post("/workspace/{workspace_slug}/seed")
def seed_workspace_document(
    workspace_slug: str,
    _: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create or refresh the canonical workspace document from its on-disk report."""
    spec = WORKSPACE_REGISTRY.get(workspace_slug)
    if spec is None:
        raise HTTPException(status_code=404, detail="Workspace not registered")

    report_file = DOCS_ROOT / spec["report_file"]
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Workspace report not found")

    slug = spec["recommended_document_slug"]
    markdown = report_file.read_text(encoding="utf-8")
    front_matter = {
        "workspace_slug": workspace_slug,
        "workspace_type": "dictation",
        "source_report": spec["report_file"],
        "deterministic": True,
    }

    document = db.query(Document).filter(Document.slug == slug).first()
    if document is None:
        document = Document(
            slug=slug,
            title=spec["title"],
            doc_type="policy",
            markdown=markdown,
            front_matter=front_matter,
            content={},
            status="draft",
        )
        db.add(document)
    else:
        document.title = spec["title"]
        document.doc_type = "policy"
        document.markdown = markdown
        # Preserve any non-managed front_matter keys (style, layout, etc.).
        merged = dict(document.front_matter or {})
        merged.update(front_matter)
        document.front_matter = merged

    db.commit()
    db.refresh(document)
    return {
        "slug": document.slug,
        "title": document.title,
        "workspace_slug": workspace_slug,
    }


@router.post("/sessions")
def create_session(
    title: str = Form("Dictado CIF medicamentos"),
    workspace_slug: str = Form("cif-medicamentos"),
    document_slug: str | None = Form(None),
    _: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a persistent dictation session."""
    base_slug = _slugify(title)
    slug = base_slug
    counter = 1
    while db.query(DictationSession).filter(DictationSession.slug == slug).first():
        counter += 1
        slug = f"{base_slug}-{counter}"

    session = DictationSession(
        slug=slug,
        title=title,
        workspace_slug=workspace_slug,
        document_slug=document_slug,
        status="idle",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _serialize_session(session)


@router.get("/sessions/{slug}")
def get_session(
    slug: str,
    _: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Fetch a dictation session."""
    session = db.query(DictationSession).filter(DictationSession.slug == slug).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _serialize_session(session)


@router.post("/sessions/{slug}/chunks")
async def transcribe_chunk(
    slug: str,
    audio: UploadFile = File(...),
    chunk_index: int = Form(...),
    _: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Transcribe and append a chunk to the session transcript."""
    session = db.query(DictationSession).filter(DictationSession.slug == slug).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    client = _get_openai_client()
    session.status = "transcribing"

    session_dir = PRIVATE_UPLOAD_ROOT / slug
    session_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(audio.filename or f"chunk-{chunk_index}.webm").suffix or ".webm"
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    file_name = f"{chunk_index:04d}-{timestamp}{suffix}"
    saved_path = session_dir / file_name

    with saved_path.open("wb") as handle:
        shutil.copyfileobj(audio.file, handle)

    with saved_path.open("rb") as handle:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=handle,
            response_format="text",
        )

    transcript_text = str(result).strip()
    if transcript_text:
        session.transcript = (
            f"{session.transcript.rstrip()}\n\n{transcript_text}".strip()
            if session.transcript
            else transcript_text
        )

    chunk_log = list(session.chunk_log or [])
    chunk_log.append(
        {
            "chunk_index": chunk_index,
            "file_name": file_name,
            "transcript": transcript_text,
            "created_at": datetime.utcnow().isoformat(),
        }
    )

    session.chunk_log = chunk_log
    session.chunk_count = len(chunk_log)
    session.status = "idle"
    db.commit()
    db.refresh(session)

    return {
        "chunk_index": chunk_index,
        "transcript": transcript_text,
        "session": _serialize_session(session),
    }
