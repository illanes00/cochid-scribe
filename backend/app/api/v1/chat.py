"""Chat API endpoint using Claude Code CLI as subprocess.

Uses `claude -p` (print mode) with document context, giving the AI access
to all MCP tools including the Scribe MCP server.
"""

import subprocess
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.bibliography import BibliographyEntry
from app.models.claim import Claim
from app.models.comment import Comment
from app.models.document import Document

router = APIRouter()
logger = get_logger(__name__)

CLAUDE_CLI = "/home/illanes00/.local/bin/claude"


class ChatRequest(BaseModel):
    message: str
    include_document: bool = True
    include_comments: bool = True
    include_claims: bool = True
    include_bibliography: bool = True


class ChatResponse(BaseModel):
    response: str
    model: str | None = None


def _build_context(db: Session, doc: Document, req: ChatRequest) -> str:
    """Build context string with document, comments, claims, bibliography."""
    parts = []

    if req.include_document:
        md = doc.markdown or ""
        if not md and isinstance(doc.content, dict):
            md = doc.content.get("html", "")
        parts.append(f"## DOCUMENTO: {doc.title}\n\n{md[:40000]}")

    if req.include_comments:
        comments = (
            db.query(Comment)
            .filter(Comment.document_id == doc.id, Comment.parent_id == None)  # noqa: E711
            .order_by(Comment.created_at.asc())
            .all()
        )
        if comments:
            lines = []
            for i, c in enumerate(comments, 1):
                status = "RESUELTO" if c.resolved else "PENDIENTE"
                lines.append(f"{i}. [{status}] [{c.author or 'Anon'}]: {c.content}")
            parts.append("## COMENTARIOS DE REVISIÓN\n\n" + "\n".join(lines))

    if req.include_claims:
        claims = db.query(Claim).filter(Claim.document_id == doc.id).all()
        if claims:
            lines = [f"- [{c.claim_type}/{c.status}] {c.claim_text}" for c in claims]
            parts.append("## CLAIMS VERIFICADOS\n\n" + "\n".join(lines))

    if req.include_bibliography:
        bib = db.query(BibliographyEntry).limit(30).all()
        if bib:
            lines = [
                f"- [{e.bib_key}] {e.author or ''} ({e.year or ''}). {e.title}. {e.journal or ''}"
                for e in bib
            ]
            parts.append("## BIBLIOGRAFÍA\n\n" + "\n".join(lines))

    return "\n\n---\n\n".join(parts)


@router.post("/{slug}", response_model=ChatResponse)
async def chat_with_document(
    slug: str,
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    """Chat about a document using Claude Code CLI subprocess.

    This gives the AI access to all MCP tools (including Scribe MCP server),
    file system, web search, and the full Claude Code toolkit.
    """
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    context = _build_context(db, doc, req)

    system_prompt = (
        "Eres un investigador senior de política pública chilena trabajando en Espacio Público. "
        "Tienes acceso al documento completo, comentarios de revisión (CIF y directores), "
        "claims verificados y bibliografía. "
        "Responde en español. Sé factual, riguroso y diplomático. "
        "Cita datos específicos del documento y la bibliografía cuando sea relevante. "
        "Tienes acceso a tools MCP de Scribe (scribe_*) para consultar datos adicionales."
    )

    full_prompt = f"{context}\n\n---\n\nPREGUNTA DEL USUARIO:\n{req.message}"

    try:
        result = subprocess.run(
            [
                CLAUDE_CLI,
                "-p",
                "--output-format", "text",
                "--append-system-prompt", system_prompt,
                "--model", "sonnet",
            ],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/srv/projects/cochid/cochid-scribe",
        )

        if result.returncode != 0:
            logger.warning("chat.claude_error", stderr=result.stderr[:500])
            raise HTTPException(
                status_code=502,
                detail=f"Claude CLI error: {result.stderr[:200]}",
            )

        response_text = result.stdout.strip()
        if not response_text:
            raise HTTPException(status_code=502, detail="Empty response from Claude CLI")

        logger.info("chat.success", slug=slug, response_length=len(response_text))

        return ChatResponse(response=response_text, model="claude-sonnet")

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Claude CLI timed out (120s)")
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Claude CLI not found. Install Claude Code first.",
        )
