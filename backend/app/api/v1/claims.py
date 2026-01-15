"""Claims API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.models.document import Document
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate

router = APIRouter()


def generate_claim_id() -> str:
    """Generate a unique claim ID."""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    import uuid

    random_part = uuid.uuid4().hex[:6]
    return f"C-{date_part}-{random_part}"


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """Get a claim by ID."""
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return claim


@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: str,
    data: ClaimUpdate,
    db: Session = Depends(get_db),
):
    """Update a claim."""
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

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
    db: Session = Depends(get_db),
):
    """Delete a claim."""
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    db.delete(claim)
    db.commit()


@router.post("/{claim_id}/verify", response_model=ClaimResponse)
async def verify_claim(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """Mark a claim as verified."""
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.status = "verified"
    db.commit()
    db.refresh(claim)

    return claim


# Document-scoped endpoints
@router.get("/document/{slug}", response_model=list[ClaimResponse])
async def list_document_claims(
    slug: str,
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List all claims for a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    query = db.query(Claim).filter(Claim.document_id == doc.id)

    if status:
        query = query.filter(Claim.status == status)

    claims = query.order_by(Claim.created_at).all()
    return claims


@router.post("/document/{slug}", response_model=ClaimResponse, status_code=201)
async def create_document_claim(
    slug: str,
    data: ClaimCreate,
    db: Session = Depends(get_db),
):
    """Create a new claim for a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

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
