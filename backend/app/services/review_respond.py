"""AI-assisted review and respond service for document comments.

Analyzes unresolved comments on a document and generates factual,
well-argued responses with optional suggested edits.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

import httpx as _httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.bibliography import BibliographyEntry
from app.models.claim import Claim
from app.models.comment import Comment
from app.models.document import Document

_log = logging.getLogger(__name__)
settings = get_settings()

_MODEL = "claude-sonnet-4-20250514"

_ANTHROPIC_COSTS: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-20250514": (3.0, 15.0),
}


# ── Schemas ──────────────────────────────────────────────────────


class SuggestedEdit(BaseModel):
    original_text: str
    replacement_text: str
    rationale: str


class CommentResponse(BaseModel):
    comment_id: str
    comment_content: str
    comment_author: str | None
    response_type: str  # agree | disagree | partial | clarification | editorial
    response_text: str
    suggested_edit: SuggestedEdit | None = None


class ReviewAnalysis(BaseModel):
    document_slug: str
    total_comments: int
    responses: list[CommentResponse]
    summary: str


# ── Usage logging ────────────────────────────────────────────────


def _log_ai_usage(model: str, message: Any, endpoint: str) -> None:
    try:
        usage = message.usage
        input_tokens = usage.input_tokens or 0
        output_tokens = usage.output_tokens or 0
    except Exception:
        return

    costs = _ANTHROPIC_COSTS.get(model, (3.0, 15.0))
    cost_usd = (input_tokens / 1_000_000 * costs[0]) + (output_tokens / 1_000_000 * costs[1])

    def _post():
        try:
            _httpx.post(
                "http://localhost:8190/api/v1/ai/log",
                json={
                    "project": "cochid-scribe",
                    "provider": "anthropic",
                    "model": model,
                    "endpoint": endpoint,
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "cost_usd": round(cost_usd, 6),
                    "task": endpoint,
                },
                headers={"X-API-Key": os.environ.get("ILLANES00_SERVER_API_KEY", "")},
                timeout=5,
            )
        except Exception as e:
            _log.debug("ai_usage.log_failed: %s", e)

    threading.Thread(target=_post, daemon=True).start()


# ── Service ──────────────────────────────────────────────────────


class ReviewRespondService:
    """Generates AI-assisted responses to document review comments."""

    def __init__(self, db: Session):
        self.db = db

    def get_pending_comments(self, doc: Document) -> list[Comment]:
        return (
            self.db.query(Comment)
            .filter(
                Comment.document_id == doc.id,
                Comment.resolved == False,  # noqa: E712
                Comment.parent_id == None,  # noqa: E711 — root comments only
            )
            .order_by(Comment.created_at.asc())
            .all()
        )

    def get_replies(self, comment: Comment) -> list[Comment]:
        return (
            self.db.query(Comment)
            .filter(Comment.parent_id == comment.id)
            .order_by(Comment.created_at.asc())
            .all()
        )

    def _build_context(self, doc: Document) -> dict[str, str]:
        # Document content
        markdown = doc.markdown or ""
        if not markdown and isinstance(doc.content, dict):
            markdown = doc.content.get("html", "")

        # Bibliography
        bib_entries = self.db.query(BibliographyEntry).all()
        bib_text = ""
        if bib_entries:
            bib_lines = []
            for entry in bib_entries[:50]:
                bib_lines.append(
                    f"- [{entry.bib_key}] {entry.author or ''} ({entry.year or ''}). "
                    f"{entry.title or ''}. {entry.journal or ''}"
                )
            bib_text = "\n".join(bib_lines)

        # Verified claims
        claims = (
            self.db.query(Claim)
            .filter(Claim.document_id == doc.id, Claim.status == "verified")
            .all()
        )
        claims_text = ""
        if claims:
            claim_lines = []
            for c in claims:
                claim_lines.append(f"- [{c.claim_id}] {c.claim_text} (type: {c.claim_type})")
            claims_text = "\n".join(claim_lines)

        return {
            "document": markdown[:80000],  # Limit to ~80k chars
            "bibliography": bib_text,
            "claims": claims_text,
        }

    def _format_comments(self, doc: Document) -> str:
        comments = self.get_pending_comments(doc)
        if not comments:
            return ""

        sections = []
        for i, comment in enumerate(comments, 1):
            replies = self.get_replies(comment)
            section = f"## Comment {i} (ID: {comment.id})\n"
            section += f"**Author:** {comment.author or 'Unknown'}\n"
            if comment.quote:
                section += f"**Quoted text:** \"{comment.quote}\"\n"
            section += f"**Comment:** {comment.content}\n"

            if replies:
                for reply in replies:
                    section += f"\n  > **Reply by {reply.author or 'Unknown'}:** {reply.content}\n"

            sections.append(section)

        return "\n\n".join(sections)

    def analyze_and_respond(self, doc: Document) -> ReviewAnalysis:
        """Generate AI responses for all pending comments on a document."""
        import subprocess

        context = self._build_context(doc)
        comments_text = self._format_comments(doc)
        pending = self.get_pending_comments(doc)

        if not pending:
            return ReviewAnalysis(
                document_slug=doc.slug,
                total_comments=0,
                responses=[],
                summary="No hay comentarios pendientes.",
            )

        system_prompt = (
            "Eres un investigador senior de politica publica en un think tank chileno (Espacio Publico). "
            "Analiza comentarios de revision sobre un informe academico y genera respuestas profesionales. "
            "SIEMPRE responde en espanol. Se factual, cita datos del documento y bibliografia. "
            "Para cada comentario responde con JSON: "
            '{"comment_id":"ID","response_type":"agree|partial|disagree|clarification|editorial",'
            '"response_text":"respuesta argumentada",'
            '"suggested_edit":{"original_text":"texto original","replacement_text":"texto nuevo","rationale":"razon"}} '
            "Responde con un JSON array [...] seguido de RESUMEN: ..."
        )

        user_content = (
            f"DOCUMENTO:\n{context['document'][:40000]}\n\n"
            f"BIBLIOGRAFIA:\n{context['bibliography'] or '(ninguna)'}\n\n"
            f"CLAIMS:\n{context['claims'] or '(ninguno)'}\n\n---\n\n"
            f"COMENTARIOS:\n{comments_text}\n\n---\n\n"
            "Genera respuesta para CADA comentario. Se riguroso y factual."
        )

        _log.info("review_respond: calling claude CLI for %d comments", len(pending))

        result = subprocess.run(
            [
                "/home/illanes00/.local/bin/claude",
                "-p",
                "--output-format", "text",
                "--append-system-prompt", system_prompt,
                "--model", "sonnet",
            ],
            input=user_content,
            capture_output=True,
            text=True,
            timeout=180,
            cwd="/srv/projects/cochid/cochid-scribe",
        )

        if result.returncode != 0:
            _log.warning("review_respond: claude CLI error: %s", result.stderr[:300])
            raise ValueError(f"Claude CLI error: {result.stderr[:200]}")

        response_text = result.stdout.strip()
        if not response_text:
            raise ValueError("Empty response from Claude CLI")

        # Parse JSON from response
        responses = self._parse_responses(response_text, pending)

        # Extract summary
        summary = ""
        if "RESUMEN:" in response_text:
            summary = response_text.split("RESUMEN:")[-1].strip()
        elif "resumen:" in response_text.lower():
            parts = response_text.lower().split("resumen:")
            summary = response_text[response_text.lower().rfind("resumen:") + 8 :].strip()

        return ReviewAnalysis(
            document_slug=doc.slug,
            total_comments=len(pending),
            responses=responses,
            summary=summary or "Analisis completado.",
        )

    def _parse_responses(
        self, response_text: str, pending: list[Comment]
    ) -> list[CommentResponse]:
        """Parse the AI response JSON into CommentResponse objects."""
        responses: list[CommentResponse] = []

        # Extract JSON array
        json_start = response_text.find("[")
        json_end = response_text.rfind("]") + 1

        if json_start < 0 or json_end <= json_start:
            _log.warning("review_respond: Could not find JSON array in response")
            return responses

        try:
            raw_items = json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError as exc:
            _log.warning("review_respond: JSON parse error: %s", exc)
            return responses

        comment_map = {c.id: c for c in pending}

        for item in raw_items:
            comment_id = str(item.get("comment_id", ""))
            comment = comment_map.get(comment_id)

            suggested_edit = None
            if item.get("suggested_edit"):
                se = item["suggested_edit"]
                if se.get("original_text") and se.get("replacement_text"):
                    suggested_edit = SuggestedEdit(
                        original_text=se["original_text"],
                        replacement_text=se["replacement_text"],
                        rationale=se.get("rationale", ""),
                    )

            responses.append(
                CommentResponse(
                    comment_id=comment_id,
                    comment_content=comment.content if comment else item.get("comment_id", ""),
                    comment_author=comment.author if comment else None,
                    response_type=item.get("response_type", "clarification"),
                    response_text=item.get("response_text", ""),
                    suggested_edit=suggested_edit,
                )
            )

        return responses
