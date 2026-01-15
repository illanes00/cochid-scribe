"""Documents API endpoints."""

import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.models.document import Document
from app.schemas.document import (
    DocumentCreate,
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
)

router = APIRouter()


def slugify(text: str) -> str:
    """Convert text to slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:100]


def get_document_response(doc: Document, db: Session) -> DocumentResponse:
    """Convert Document model to response with claim counts."""
    claims = db.query(Claim).filter(Claim.document_id == doc.id).all()
    verified = sum(1 for c in claims if c.status == "verified")

    return DocumentResponse(
        id=doc.id,
        slug=doc.slug,
        title=doc.title,
        doc_type=doc.doc_type,
        content=doc.content or {},
        markdown=doc.markdown,
        front_matter=doc.front_matter or {},
        status=doc.status,
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        claim_count=len(claims),
        verified_count=verified,
    )


@router.get("", response_model=DocumentList)
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all documents with pagination."""
    offset = (page - 1) * per_page
    total = db.query(Document).count()
    docs = (
        db.query(Document)
        .order_by(Document.updated_at.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return DocumentList(
        documents=[get_document_response(doc, db) for doc in docs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
):
    """Create a new document."""
    slug = data.slug or slugify(data.title)

    # Check if slug exists
    existing = db.query(Document).filter(Document.slug == slug).first()
    if existing:
        # Append timestamp to make unique
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    doc = Document(
        slug=slug,
        title=data.title,
        doc_type=data.doc_type,
        content=data.content,
        markdown=data.markdown,
        front_matter=data.front_matter,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return get_document_response(doc, db)


@router.get("/{slug}", response_model=DocumentResponse)
async def get_document(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get a document by slug."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return get_document_response(doc, db)


@router.put("/{slug}", response_model=DocumentResponse)
async def update_document(
    slug: str,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
):
    """Update a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    db.commit()
    db.refresh(doc)

    return get_document_response(doc, db)


@router.delete("/{slug}", status_code=204)
async def delete_document(
    slug: str,
    db: Session = Depends(get_db),
):
    """Delete a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)
    db.commit()
