"""Comments API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.v1.auth import require_document_access, require_document_record_access
from app.db.session import get_db
from app.models.comment import Comment
from app.models.document import Document
from app.core.logging import get_logger
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    ImportFeedbackRequest,
    ReplyGoogleCreate,
)
from app.services.google import build_drive_service

router = APIRouter()
logger = get_logger(__name__)


def get_comment_or_404(db: Session, comment_id: str) -> Comment:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


def get_comment_document_or_404(db: Session, comment: Comment) -> Document:
    doc = db.query(Document).filter(Document.id == comment.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/document/{slug}", response_model=list[CommentResponse])
async def list_document_comments(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """List comments for a document."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)
    return (
        db.query(Comment)
        .filter(Comment.document_id == doc.id)
        .order_by(Comment.created_at.asc())
        .all()
    )


@router.post("/document/{slug}", response_model=CommentResponse, status_code=201)
async def create_document_comment(
    slug: str,
    payload: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a local comment for a document."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)

    anchor_id = payload.anchor_id
    if payload.parent_id and not anchor_id:
        parent = (
            db.query(Comment)
            .filter(Comment.id == payload.parent_id, Comment.document_id == doc.id)
            .first()
        )
        if parent:
            anchor_id = parent.anchor_id or parent.id

    comment = Comment(
        document_id=doc.id,
        parent_id=payload.parent_id,
        anchor_id=anchor_id,
        provider="local",
        content=payload.content,
        quote=payload.quote,
        resolved=False,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    if not comment.anchor_id:
        comment.anchor_id = comment.id
        db.commit()
        db.refresh(comment)
    return comment


@router.post("/document/{slug}/sync")
async def sync_google_comments(slug: str, request: Request, db: Session = Depends(get_db)):
    """Sync Google Docs comments and replies into local storage."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)
    if doc.source_provider != "google" or not doc.source_id:
        raise HTTPException(status_code=400, detail="Document is not linked to Google Docs")

    drive = build_drive_service(db)
    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    existing_ids = {
        c.external_id
        for c in db.query(Comment).filter(Comment.document_id == doc.id).all()
        if c.external_id
    }

    comments_response = (
        drive.comments()
        .list(
            fileId=doc.source_id,
            fields="comments(id,author,content,quotedFileContent,createdTime,resolved,replies(id,author,content,createdTime))",
            includeDeleted=False,
        )
        .execute()
    )
    created_comments = 0
    created_replies = 0

    for item in comments_response.get("comments", []):
        external_id = item.get("id")
        if not external_id:
            continue

        # Import root comment if new
        local_comment_id = None
        if external_id not in existing_ids:
            author = None
            if isinstance(item.get("author"), dict):
                author = item["author"].get("displayName")
            quote = None
            if isinstance(item.get("quotedFileContent"), dict):
                quote = item["quotedFileContent"].get("value")

            comment = Comment(
                document_id=doc.id,
                provider="google",
                external_id=external_id,
                anchor_id=external_id,
                author=author,
                content=item.get("content") or "",
                quote=quote,
                resolved=bool(item.get("resolved", False)),
            )
            db.add(comment)
            db.flush()
            local_comment_id = comment.id
            existing_ids.add(external_id)
            created_comments += 1
        else:
            # Find existing local comment to use as parent for replies
            existing = (
                db.query(Comment)
                .filter(Comment.external_id == external_id, Comment.document_id == doc.id)
                .first()
            )
            if existing:
                local_comment_id = existing.id

        # Import replies for this comment
        for reply in item.get("replies", []):
            reply_ext_id = f"{external_id}:reply:{reply.get('id', '')}"
            if reply_ext_id in existing_ids:
                continue
            reply_author = None
            if isinstance(reply.get("author"), dict):
                reply_author = reply["author"].get("displayName")
            reply_comment = Comment(
                document_id=doc.id,
                parent_id=local_comment_id,
                provider="google",
                external_id=reply_ext_id,
                anchor_id=external_id,
                author=reply_author,
                content=reply.get("content") or "",
                resolved=False,
            )
            db.add(reply_comment)
            existing_ids.add(reply_ext_id)
            created_replies += 1

    db.commit()
    logger.info(
        "comments.sync_complete",
        slug=slug,
        created_comments=created_comments,
        created_replies=created_replies,
    )

    return {"created_comments": created_comments, "created_replies": created_replies}


@router.post("/document/{slug}/google")
async def create_google_comment(
    slug: str,
    payload: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a Google Docs comment and store it locally."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)
    if doc.source_provider != "google" or not doc.source_id:
        raise HTTPException(status_code=400, detail="Document is not linked to Google Docs")

    drive = build_drive_service(db)
    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    created = (
        drive.comments()
        .create(
            fileId=doc.source_id,
            body={"content": payload.content},
            fields="id,author,content,createdTime,resolved",
        )
        .execute()
    )

    external_id = created.get("id")
    comment = Comment(
        document_id=doc.id,
        provider="google",
        external_id=external_id,
        anchor_id=external_id,
        author=(created.get("author") or {}).get("displayName"),
        content=created.get("content") or payload.content,
        quote=None,
        resolved=bool(created.get("resolved", False)),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    payload: CommentUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update a comment (local state only)."""
    comment = get_comment_or_404(db, comment_id)
    require_document_record_access(request, get_comment_document_or_404(db, comment))
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    db.commit()
    db.refresh(comment)
    return comment


@router.post("/document/{slug}/import-feedback")
async def import_feedback(
    slug: str,
    payload: ImportFeedbackRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Import structured feedback (from email, meetings, etc.) as comments."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)

    created = 0
    for item in payload.items:
        comment = Comment(
            document_id=doc.id,
            provider=payload.source,
            author=item.author,
            content=item.content,
            quote=item.quote,
            resolved=False,
        )
        db.add(comment)
        db.flush()
        comment.anchor_id = comment.id
        created += 1

    db.commit()
    logger.info("comments.import_feedback", slug=slug, source=payload.source, created=created)
    return {"created": created, "source": payload.source}


@router.post("/document/{slug}/reply-google")
async def reply_google_comment(
    slug: str,
    payload: ReplyGoogleCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Push a reply to a Google Docs comment and store it locally."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)
    if doc.source_provider != "google" or not doc.source_id:
        raise HTTPException(status_code=400, detail="Document is not linked to Google Docs")

    drive = build_drive_service(db)
    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    # Find the local parent comment
    parent = (
        db.query(Comment)
        .filter(
            Comment.external_id == payload.comment_external_id,
            Comment.document_id == doc.id,
        )
        .first()
    )
    if not parent:
        raise HTTPException(status_code=404, detail="Parent comment not found locally")

    # Push reply to Google Docs
    created = (
        drive.replies()
        .create(
            fileId=doc.source_id,
            commentId=payload.comment_external_id,
            body={"content": payload.content},
            fields="id,author,content,createdTime",
        )
        .execute()
    )

    reply_ext_id = f"{payload.comment_external_id}:reply:{created.get('id', '')}"
    reply_author = None
    if isinstance(created.get("author"), dict):
        reply_author = created["author"].get("displayName")

    reply_comment = Comment(
        document_id=doc.id,
        parent_id=parent.id,
        provider="google",
        external_id=reply_ext_id,
        anchor_id=payload.comment_external_id,
        author=reply_author,
        content=created.get("content") or payload.content,
        resolved=False,
    )
    db.add(reply_comment)
    db.commit()
    db.refresh(reply_comment)

    logger.info("comments.reply_pushed", slug=slug, comment_id=payload.comment_external_id)
    return reply_comment
