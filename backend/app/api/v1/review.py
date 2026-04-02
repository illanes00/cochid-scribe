"""Review API endpoints for AI-assisted comment response."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.comment import Comment
from app.models.document import Document
from app.models.track_change import ChangeStatus, ChangeType, TrackChange
from app.services.google import build_drive_service
from fastapi.responses import HTMLResponse

from app.services.diff_export import generate_diff_html
from app.services.review_export import generate_review_html
from app.services.review_respond import ReviewAnalysis, ReviewRespondService

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.get("/{slug}/status")
async def review_status(slug: str, db: Session = Depends(get_db)):
    """Get the review status for a document — pending comments, etc."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    service = ReviewRespondService(db)
    pending = service.get_pending_comments(doc)

    total_comments = (
        db.query(Comment)
        .filter(Comment.document_id == doc.id, Comment.parent_id == None)  # noqa: E711
        .count()
    )
    resolved_comments = (
        db.query(Comment)
        .filter(
            Comment.document_id == doc.id,
            Comment.parent_id == None,  # noqa: E711
            Comment.resolved == True,  # noqa: E712
        )
        .count()
    )

    return {
        "document_slug": slug,
        "total_comments": total_comments,
        "pending_comments": len(pending),
        "resolved_comments": resolved_comments,
        "has_google_link": doc.source_provider == "google" and bool(doc.source_id),
    }


@router.post("/{slug}/analyze", response_model=ReviewAnalysis)
async def analyze_comments(slug: str, db: Session = Depends(get_db)):
    """AI analyzes all pending comments and generates suggested responses."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="LLM service not configured")

    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    service = ReviewRespondService(db)
    analysis = service.analyze_and_respond(doc)

    logger.info(
        "review.analyze_complete",
        slug=slug,
        total_comments=analysis.total_comments,
        responses=len(analysis.responses),
    )

    return analysis


@router.get("/{slug}/export", response_class=HTMLResponse)
async def export_review(slug: str, db: Session = Depends(get_db)):
    """Export the full review as a printable A3 HTML document.

    Open in browser and print to PDF (Ctrl+P → A3 landscape).
    """
    try:
        html_content = generate_review_html(db, slug)
        return HTMLResponse(content=html_content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{slug}/pdf")
async def download_pdf(slug: str, db: Session = Depends(get_db)):
    """Generate and download the review as a PDF file."""
    import subprocess
    from pathlib import Path

    from fastapi.responses import FileResponse

    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    exports_dir = Path("/srv/projects/cochid/cochid-scribe/backend/exports")
    exports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = exports_dir / f"review-{slug}.pdf"

    # Generate HTML to temp file first (avoids deadlock with Chrome → uvicorn)
    html_content = generate_review_html(db, slug)
    html_path = exports_dir / f"review-{slug}.html"
    html_path.write_text(html_content, encoding="utf-8")

    # Chrome renders the local file
    subprocess.run(
        [
            "google-chrome",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={pdf_path}",
            "--print-to-pdf-no-header",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=5000",
            f"file://{html_path}",
        ],
        capture_output=True,
        timeout=30,
    )

    if not pdf_path.exists():
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"review-{slug}.pdf",
    )


@router.get("/{slug}/diff", response_class=HTMLResponse)
async def export_diff(slug: str, db: Session = Depends(get_db)):
    """Export visual diff showing each comment with its text change (git-style)."""
    try:
        return HTMLResponse(content=generate_diff_html(db, slug))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class ApplyItem(BaseModel):
    comment_id: str
    response_text: str
    apply_edit: bool = False
    push_to_google: bool = False


class ApplyRequest(BaseModel):
    items: list[ApplyItem]


@router.post("/{slug}/apply")
async def apply_responses(
    slug: str,
    payload: ApplyRequest,
    db: Session = Depends(get_db),
):
    """Apply approved responses: create track changes and/or push replies to Google Docs."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    drive = None
    if any(item.push_to_google for item in payload.items):
        if doc.source_provider != "google" or not doc.source_id:
            raise HTTPException(
                status_code=400,
                detail="Document is not linked to Google Docs (cannot push to Google)",
            )
        drive = build_drive_service(db)
        if not drive:
            raise HTTPException(status_code=400, detail="Google integration not connected")

    applied_replies = 0
    applied_edits = 0
    errors: list[str] = []

    for item in payload.items:
        comment = db.query(Comment).filter(Comment.id == item.comment_id).first()
        if not comment:
            errors.append(f"Comment {item.comment_id} not found")
            continue

        # Push reply to Google Docs
        if item.push_to_google and drive and comment.external_id:
            # Extract the root comment external_id (strip reply suffix if present)
            root_ext_id = comment.external_id.split(":reply:")[0]
            try:
                drive.replies().create(
                    fileId=doc.source_id,
                    commentId=root_ext_id,
                    body={"content": item.response_text},
                    fields="id",
                ).execute()
                applied_replies += 1
            except Exception as exc:
                logger.warning(
                    "review.google_reply_failed",
                    comment_id=item.comment_id,
                    error=str(exc),
                )
                errors.append(f"Failed to push reply for {item.comment_id}: {exc}")

        # Create local reply comment
        reply = Comment(
            document_id=doc.id,
            parent_id=comment.id,
            provider="scribe-ai",
            anchor_id=comment.anchor_id or comment.id,
            author="Scribe AI (reviewed by author)",
            content=item.response_text,
            resolved=False,
        )
        db.add(reply)

        # Mark original comment as resolved
        comment.resolved = True
        applied_edits += 1

    db.commit()
    logger.info(
        "review.apply_complete",
        slug=slug,
        applied_replies=applied_replies,
        applied_edits=applied_edits,
        errors=len(errors),
    )

    return {
        "applied_replies": applied_replies,
        "applied_edits": applied_edits,
        "errors": errors,
    }
