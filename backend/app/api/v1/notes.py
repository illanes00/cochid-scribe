"""Notes API endpoints for Knowledge Base."""

import re

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


def extract_wiki_links(content: dict) -> list[str]:
    """Extract [[wiki links]] from Tiptap content."""
    links = []

    def traverse(node):
        if isinstance(node, dict):
            # Check for text nodes with wiki link pattern
            if node.get("type") == "text" and node.get("text"):
                # Find [[link]] patterns
                matches = re.findall(r"\[\[([^\]]+)\]\]", node["text"])
                links.extend(matches)

            # Traverse children
            for child in node.get("content", []):
                traverse(child)

    traverse(content)
    return links


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

    note = Note(
        slug=slug,
        title=note_in.title,
        content=note_in.content,
        markdown=note_in.markdown,
        note_type=note_in.note_type,
        tags=note_in.tags,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    # Process wiki links and create Link records
    wiki_links = extract_wiki_links(note_in.content)
    for linked_slug in wiki_links:
        # Find target note by slug
        target_note = db.query(Note).filter(Note.slug == linked_slug).first()
        if target_note:
            link = Link(
                source_type="note",
                source_id=note.id,
                target_type="note",
                target_id=target_note.id,
                link_type="reference",
            )
            db.add(link)

    db.commit()

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
    for field, value in update_data.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)

    # Update links if content changed
    if "content" in update_data:
        # Remove old outgoing links
        db.query(Link).filter(
            Link.source_type == "note",
            Link.source_id == note.id,
        ).delete()

        # Create new links
        wiki_links = extract_wiki_links(update_data["content"])
        for linked_slug in wiki_links:
            target_note = db.query(Note).filter(Note.slug == linked_slug).first()
            if target_note:
                link = Link(
                    source_type="note",
                    source_id=note.id,
                    target_type="note",
                    target_id=target_note.id,
                    link_type="reference",
                )
                db.add(link)

        db.commit()

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
