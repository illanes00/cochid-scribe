"""Notes API endpoints for Knowledge Base."""

from fastapi import APIRouter, Depends, HTTPException, Query
from slugify import slugify
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.note import Link, Note
from app.schemas.note import (
    LinkResponse,
    NoteCreate,
    NoteList,
    NoteResponse,
    NoteUpdate,
)
from app.services.content_links import update_document_links
from app.services.conversion import html_to_markdown, markdown_to_html

router = APIRouter()


def generate_unique_slug(db: Session, title: str, existing_slug: str | None = None) -> str:
    """Generate a unique slug for a note."""
    base_slug = slugify(title, max_length=50)
    if not base_slug:
        base_slug = "note"

    slug = base_slug
    counter = 1

    while True:
        existing = db.query(Note).filter(Note.slug == slug).first()
        if not existing or (existing_slug and existing.slug == existing_slug):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def normalize_content(
    content: dict | None,
    markdown: str | None,
) -> tuple[dict, str | None]:
    """Ensure content has HTML and markdown is available."""
    content = content or {}
    html = content.get("html") if isinstance(content, dict) else None

    if html and not markdown:
        try:
            markdown = html_to_markdown(html)
        except Exception:
            markdown = markdown or ""
    elif markdown and not html:
        try:
            html = markdown_to_html(markdown)
            content["html"] = html
        except Exception:
            pass

    return content, markdown


@router.get("", response_model=NoteList)
async def list_notes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    note_type: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    """List all notes with pagination and filtering."""
    query = db.query(Note)

    if search:
        query = query.filter(
            or_(
                Note.title.ilike(f"%{search}%"),
                Note.markdown.ilike(f"%{search}%"),
            )
        )

    if note_type:
        query = query.filter(Note.note_type == note_type)

    # Tag filtering (JSON array search)
    if tag:
        # SQLite JSON search
        query = query.filter(Note.tags.contains(f'"{tag}"'))

    total = query.count()
    notes = (
        query.order_by(Note.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Add backlink counts
    note_responses = []
    for note in notes:
        backlink_count = (
            db.query(Link)
            .filter(Link.target_type == "note", Link.target_id == note.id)
            .count()
        )
        response = NoteResponse(
            id=note.id,
            slug=note.slug,
            title=note.title,
            content=note.content,
            markdown=note.markdown,
            note_type=note.note_type,
            tags=note.tags or [],
            created_at=note.created_at,
            updated_at=note.updated_at,
            backlink_count=backlink_count,
        )
        note_responses.append(response)

    return NoteList(
        notes=note_responses,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db),
):
    """Create a new note."""
    slug = note_in.slug or generate_unique_slug(db, note_in.title)

    content, markdown = normalize_content(note_in.content, note_in.markdown)

    note = Note(
        slug=slug,
        title=note_in.title,
        content=content,
        markdown=markdown or "",
        note_type=note_in.note_type,
        tags=note_in.tags,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    update_document_links(db, note.id, "note", content.get("json"), content.get("html"))

    return NoteResponse(
        id=note.id,
        slug=note.slug,
        title=note.title,
        content=note.content,
        markdown=note.markdown,
        note_type=note.note_type,
        tags=note.tags or [],
        created_at=note.created_at,
        updated_at=note.updated_at,
        backlink_count=0,
    )


@router.get("/{slug}", response_model=NoteResponse)
async def get_note(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get a note by slug."""
    note = db.query(Note).filter(Note.slug == slug).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    backlink_count = (
        db.query(Link)
        .filter(Link.target_type == "note", Link.target_id == note.id)
        .count()
    )

    return NoteResponse(
        id=note.id,
        slug=note.slug,
        title=note.title,
        content=note.content,
        markdown=note.markdown,
        note_type=note.note_type,
        tags=note.tags or [],
        created_at=note.created_at,
        updated_at=note.updated_at,
        backlink_count=backlink_count,
    )


@router.put("/{slug}", response_model=NoteResponse)
async def update_note(
    slug: str,
    note_in: NoteUpdate,
    db: Session = Depends(get_db),
):
    """Update a note."""
    note = db.query(Note).filter(Note.slug == slug).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = note_in.model_dump(exclude_unset=True)
    if "content" in update_data or "markdown" in update_data:
        content, markdown = normalize_content(
            update_data.get("content"),
            update_data.get("markdown"),
        )
        update_data["content"] = content
        update_data["markdown"] = markdown
    for field, value in update_data.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)

    if "content" in update_data:
        update_document_links(
            db,
            note.id,
            "note",
            update_data.get("content", {}).get("json"),
            update_data.get("content", {}).get("html"),
        )

    backlink_count = (
        db.query(Link)
        .filter(Link.target_type == "note", Link.target_id == note.id)
        .count()
    )

    return NoteResponse(
        id=note.id,
        slug=note.slug,
        title=note.title,
        content=note.content,
        markdown=note.markdown,
        note_type=note.note_type,
        tags=note.tags or [],
        created_at=note.created_at,
        updated_at=note.updated_at,
        backlink_count=backlink_count,
    )


@router.delete("/{slug}", status_code=204)
async def delete_note(
    slug: str,
    db: Session = Depends(get_db),
):
    """Delete a note."""
    note = db.query(Note).filter(Note.slug == slug).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Delete associated links (both incoming and outgoing)
    db.query(Link).filter(
        or_(
            (Link.source_type == "note") & (Link.source_id == note.id),
            (Link.target_type == "note") & (Link.target_id == note.id),
        )
    ).delete()

    db.delete(note)
    db.commit()


@router.get("/{slug}/backlinks", response_model=list[LinkResponse])
async def get_backlinks(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get all backlinks to a note."""
    note = db.query(Note).filter(Note.slug == slug).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    links = (
        db.query(Link)
        .filter(Link.target_type == "note", Link.target_id == note.id)
        .all()
    )

    return links
