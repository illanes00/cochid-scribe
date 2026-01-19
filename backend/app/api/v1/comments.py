"""Comments API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.comment import Comment
from app.models.document import Document
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.google import build_drive_service

router = APIRouter()


@router.get("/document/{slug}", response_model=list[CommentResponse])
async def list_document_comments(slug: str, db: Session = Depends(get_db)):
    """List comments for a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
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
    db: Session = Depends(get_db),
):
    """Create a local comment for a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

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
async def sync_google_comments(slug: str, db: Session = Depends(get_db)):
    """Sync Google Docs comments into local storage."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
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

    comments = (
        drive.comments()
        .list(
            fileId=doc.source_id,
            fields="comments(id,author,content,quotedFileContent,createdTime,resolved)",
        )
        .execute()
    )
    created = 0

    for item in comments.get("comments", []):
        external_id = item.get("id")
        if not external_id or external_id in existing_ids:
            continue
        author = None
        if isinstance(item.get("author"), dict):
            author = item.get("author", {}).get("displayName")
        quote = None
        if isinstance(item.get("quotedFileContent"), dict):
            quote = item.get("quotedFileContent", {}).get("value")

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
        created += 1

    db.commit()

    return {"created": created}


@router.post("/document/{slug}/google")
async def create_google_comment(
    slug: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
):
    """Create a Google Docs comment and store it locally."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
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
    db: Session = Depends(get_db),
):
    """Update a comment (local state only)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    db.commit()
    db.refresh(comment)
    return comment
