"""Claims API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.v1.auth import require_document_access, require_document_record_access
from app.db.session import get_db
from app.models.claim import Claim
from app.models.document import Document
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate

router = APIRouter()


def get_claim_or_404(db: Session, claim_id: str) -> Claim:
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


def get_claim_document_or_404(db: Session, claim: Claim) -> Document:
    doc = db.query(Document).filter(Document.id == claim.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def generate_claim_id() -> str:
    """Generate a unique claim ID."""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    import uuid

    random_part = uuid.uuid4().hex[:6]
    return f"C-{date_part}-{random_part}"


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get a claim by ID."""
    claim = get_claim_or_404(db, claim_id)
    require_document_record_access(request, get_claim_document_or_404(db, claim))
    return claim


@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: str,
    data: ClaimUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update a claim."""
    claim = get_claim_or_404(db, claim_id)
    require_document_record_access(request, get_claim_document_or_404(db, claim))
    update_data = data.model_dump(exclude_unset=True)

    # Convert Evidence models to dicts if present
    if "evidence" in update_data and update_data["evidence"] is not None:
        update_data["evidence"] = [e.model_dump() for e in update_data["evidence"]]

    for field, value in update_data.items():
        setattr(claim, field, value)

    db.commit()
    db.refresh(claim)

    return claim


@router.delete("/{claim_id}", status_code=204)
async def delete_claim(
    claim_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a claim."""
    claim = get_claim_or_404(db, claim_id)
    require_document_record_access(request, get_claim_document_or_404(db, claim))
    db.delete(claim)
    db.commit()


@router.post("/{claim_id}/verify", response_model=ClaimResponse)
async def verify_claim(
    claim_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Mark a claim as verified."""
    claim = get_claim_or_404(db, claim_id)
    require_document_record_access(request, get_claim_document_or_404(db, claim))
    claim.status = "verified"
    db.commit()
    db.refresh(claim)

    return claim


# Document-scoped endpoints
@router.get("/document/{slug}", response_model=list[ClaimResponse])
async def list_document_claims(
    slug: str,
    request: Request,
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List all claims for a document."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)

    query = db.query(Claim).filter(Claim.document_id == doc.id)

    if status:
        query = query.filter(Claim.status == status)

    claims = query.order_by(Claim.created_at).all()
    return claims


@router.post("/document/{slug}", response_model=ClaimResponse, status_code=201)
async def create_document_claim(
    slug: str,
    data: ClaimCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new claim for a document."""
    require_document_access(request, slug)
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    require_document_record_access(request, doc)

    claim = Claim(
        claim_id=generate_claim_id(),
        document_id=doc.id,
        claim_text=data.claim_text,
        claim_type=data.claim_type,
        section=data.section,
        evidence=[e.model_dump() for e in data.evidence],
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    return claim
