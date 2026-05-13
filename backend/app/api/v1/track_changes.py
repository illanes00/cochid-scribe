"""Track Changes API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.v1.auth import require_document_access
from app.db.session import get_db
from app.models.document import Document
from app.models.track_change import ChangeStatus, ChangeType, TrackChange
from app.schemas.track_change import (
    BulkResolveRequest,
    BulkResolveResponse,
    ExtractChangesRequest,
    ResolveChangeRequest,
    ResolveChangeResponse,
    TrackChangeCreate,
    TrackChangeResponse,
    TrackChangesListResponse,
)

router = APIRouter()


def get_document_or_404(db: Session, slug: str) -> Document:
    """Get document by slug or raise 404."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def get_protected_document(db: Session, request: Request, slug: str) -> Document:
    """Require access before loading a document."""
    require_document_access(request, slug)
    return get_document_or_404(db, slug)


@router.get("/{slug}/changes", response_model=TrackChangesListResponse)
async def list_changes(
    slug: str,
    request: Request,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all tracked changes for a document.

    Returns changes with counts by status.
    """
    doc = get_protected_document(db, request, slug)

    query = db.query(TrackChange).filter(TrackChange.document_id == doc.id)

    if status:
        query = query.filter(TrackChange.status == ChangeStatus(status))

    changes = query.order_by(TrackChange.created_at.desc()).all()

    # Get counts
    all_changes = db.query(TrackChange).filter(TrackChange.document_id == doc.id)
    pending_count = all_changes.filter(TrackChange.status == ChangeStatus.PENDING).count()
    accepted_count = all_changes.filter(TrackChange.status == ChangeStatus.ACCEPTED).count()
    rejected_count = all_changes.filter(TrackChange.status == ChangeStatus.REJECTED).count()

    return TrackChangesListResponse(
        changes=[TrackChangeResponse.model_validate(c) for c in changes],
        total=len(changes),
        pending_count=pending_count,
        accepted_count=accepted_count,
        rejected_count=rejected_count,
    )


@router.post("/{slug}/changes", response_model=TrackChangeResponse)
async def create_change(
    slug: str,
    change: TrackChangeCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new tracked change.

    Called when the editor detects a new change.
    """
    doc = get_protected_document(db, request, slug)

    # Check if change with this ID already exists
    existing = db.query(TrackChange).filter(
        TrackChange.document_id == doc.id,
        TrackChange.change_id == change.change_id,
    ).first()

    if existing:
        # Update existing change
        existing.content = change.content
        existing.position_start = change.position_start
        existing.position_end = change.position_end
        if change.author_name:
            existing.author_name = change.author_name
        if change.author_email:
            existing.author_email = change.author_email
        db.commit()
        db.refresh(existing)
        return TrackChangeResponse.model_validate(existing)

    # Create new change
    db_change = TrackChange(
        document_id=doc.id,
        change_id=change.change_id,
        change_type=ChangeType(change.change_type.value),
        content=change.content,
        position_start=change.position_start,
        position_end=change.position_end,
        author_name=change.author_name,
        author_email=change.author_email,
        status=ChangeStatus.PENDING,
    )

    db.add(db_change)
    db.commit()
    db.refresh(db_change)

    return TrackChangeResponse.model_validate(db_change)


@router.get("/{slug}/changes/{change_id}", response_model=TrackChangeResponse)
async def get_change(
    slug: str,
    change_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get a specific tracked change."""
    doc = get_protected_document(db, request, slug)

    change = db.query(TrackChange).filter(
        TrackChange.document_id == doc.id,
        TrackChange.change_id == change_id,
    ).first()

    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    return TrackChangeResponse.model_validate(change)


@router.post("/{slug}/changes/{change_id}/resolve", response_model=ResolveChangeResponse)
async def resolve_change(
    slug: str,
    change_id: str,
    request: ResolveChangeRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Accept or reject a tracked change.

    - accept: The change becomes part of the final document
    - reject: The change is undone
    """
    doc = get_protected_document(db, http_request, slug)

    change = db.query(TrackChange).filter(
        TrackChange.document_id == doc.id,
        TrackChange.change_id == change_id,
    ).first()

    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    if change.status != ChangeStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Change already resolved with status: {change.status.value}"
        )

    if request.action == "accept":
        change.accept(resolved_by=request.resolved_by, comment=request.comment)
        message = "Change accepted successfully"
    else:
        change.reject(resolved_by=request.resolved_by, comment=request.comment)
        message = "Change rejected successfully"

    db.commit()
    db.refresh(change)

    return ResolveChangeResponse(
        success=True,
        change=TrackChangeResponse.model_validate(change),
        message=message,
    )


@router.post("/{slug}/changes/bulk-resolve", response_model=BulkResolveResponse)
async def bulk_resolve_changes(
    slug: str,
    request: BulkResolveRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Accept or reject multiple changes at once."""
    doc = get_protected_document(db, http_request, slug)

    changes = db.query(TrackChange).filter(
        TrackChange.document_id == doc.id,
        TrackChange.change_id.in_(request.change_ids),
        TrackChange.status == ChangeStatus.PENDING,
    ).all()

    resolved_count = 0
    for change in changes:
        if request.action == "accept":
            change.accept(resolved_by=request.resolved_by, comment=request.comment)
        else:
            change.reject(resolved_by=request.resolved_by, comment=request.comment)
        resolved_count += 1

    db.commit()

    return BulkResolveResponse(
        success=True,
        resolved_count=resolved_count,
        message=f"{resolved_count} changes {request.action}ed successfully",
    )


@router.post("/{slug}/changes/accept-all", response_model=BulkResolveResponse)
async def accept_all_changes(
    slug: str,
    request: Request,
    resolved_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Accept all pending changes in the document."""
    doc = get_protected_document(db, request, slug)

    changes = db.query(TrackChange).filter(
        TrackChange.document_id == doc.id,
        TrackChange.status == ChangeStatus.PENDING,
    ).all()

    for change in changes:
        change.accept(resolved_by=resolved_by)

    db.commit()

    return BulkResolveResponse(
        success=True,
        resolved_count=len(changes),
        message=f"All {len(changes)} pending changes accepted",
    )


@router.post("/{slug}/changes/reject-all", response_model=BulkResolveResponse)
async def reject_all_changes(
    slug: str,
    request: Request,
    resolved_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Reject all pending changes in the document."""
    doc = get_protected_document(db, request, slug)

    changes = db.query(TrackChange).filter(
        TrackChange.document_id == doc.id,
        TrackChange.status == ChangeStatus.PENDING,
    ).all()

    for change in changes:
        change.reject(resolved_by=resolved_by)

    db.commit()

    return BulkResolveResponse(
        success=True,
        resolved_count=len(changes),
        message=f"All {len(changes)} pending changes rejected",
    )


@router.delete("/{slug}/changes/{change_id}")
async def delete_change(
    slug: str,
    change_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a tracked change record."""
    doc = get_protected_document(db, request, slug)

    change = db.query(TrackChange).filter(
        TrackChange.document_id == doc.id,
        TrackChange.change_id == change_id,
    ).first()

    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    db.delete(change)
    db.commit()

    return {"success": True, "message": "Change deleted"}


@router.post("/{slug}/changes/extract", response_model=TrackChangesListResponse)
async def extract_changes_from_content(
    slug: str,
    request: ExtractChangesRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Extract and store tracked changes from TipTap content.

    This scans the TipTap JSON for change marks and creates/updates
    track change records in the database.
    """
    doc = get_protected_document(db, http_request, slug)

    # Extract changes from TipTap content
    extracted_changes = _extract_changes_from_tiptap(request.content)

    # Store/update each change
    for change_data in extracted_changes:
        existing = db.query(TrackChange).filter(
            TrackChange.document_id == doc.id,
            TrackChange.change_id == change_data["change_id"],
        ).first()

        if existing:
            existing.content = change_data["content"]
            existing.position_start = change_data["position_start"]
            existing.position_end = change_data["position_end"]
        else:
            db_change = TrackChange(
                document_id=doc.id,
                change_id=change_data["change_id"],
                change_type=change_data["change_type"],
                content=change_data["content"],
                position_start=change_data["position_start"],
                position_end=change_data["position_end"],
                author_name=request.author_name,
                author_email=request.author_email,
                status=ChangeStatus.PENDING,
            )
            db.add(db_change)

    db.commit()

    # Return updated list
    return await list_changes(slug, request=http_request, db=db)


def _extract_changes_from_tiptap(content: dict) -> list[dict]:
    """Extract change marks from TipTap JSON content.

    Walks through the document tree looking for text nodes with
    change marks (type: 'change' with attrs.kind: 'insert' or 'delete').
    """
    changes = []
    position = 0

    def walk_node(node: dict, current_position: int) -> int:
        nonlocal changes
        pos = current_position

        if node.get("type") == "text":
            text = node.get("text", "")
            marks = node.get("marks", [])

            for mark in marks:
                if mark.get("type") == "change":
                    kind = mark.get("attrs", {}).get("kind", "insert")
                    change_id = mark.get("attrs", {}).get("changeId")

                    if not change_id:
                        # Generate a change ID if not present
                        change_id = f"change-{uuid.uuid4().hex[:8]}"

                    changes.append({
                        "change_id": change_id,
                        "change_type": ChangeType.INSERT if kind == "insert" else ChangeType.DELETE,
                        "content": text,
                        "position_start": pos,
                        "position_end": pos + len(text),
                    })

            pos += len(text)

        elif "content" in node:
            for child in node.get("content", []):
                pos = walk_node(child, pos)

        return pos

    walk_node(content, 0)
    return changes
