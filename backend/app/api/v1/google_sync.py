"""Google Docs/Slides bidirectional sync endpoints."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.google_sync import (
    LinkRequest,
    LinkResponse,
    PullResponse,
    PushResponse,
    ResolveRequest,
    ResolveResponse,
    SyncStatusResponse,
)
from app.services.google import build_docs_service, build_drive_service, build_slides_service
from app.services.google_docs_transform import (
    GoogleDocsToTipTap,
    TipTapToGoogleDocs,
    compute_content_hash,
)
from app.services.google_slides_transform import (
    GoogleSlidesToScribe,
    ScribeToGoogleSlides,
    delete_all_slides_requests,
)


class DriveUrlResponse(BaseModel):
    """Response with Google Drive URL."""

    url: str
    file_type: str  # "document" or "presentation"

router = APIRouter()


def get_document_or_404(db: Session, slug: str) -> Document:
    """Get document by slug or raise 404."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def detect_sync_status(
    doc: Document,
    current_google_revision: str | None,
) -> str:
    """Detect the current sync status based on revision and content hash.

    Returns: none|synced|local_changed|remote_changed|conflict
    """
    if not doc.source_id or doc.source_provider != "google":
        return "none"

    # Check if Google doc has changed
    google_changed = (
        current_google_revision is not None
        and doc.google_revision_id is not None
        and doc.google_revision_id != current_google_revision
    )

    # Check if local content has changed
    current_hash = compute_content_hash(doc.content or {})
    local_changed = (
        doc.local_version_hash is not None
        and doc.local_version_hash != current_hash
    )

    if google_changed and local_changed:
        return "conflict"
    elif google_changed:
        return "remote_changed"
    elif local_changed:
        return "local_changed"
    return "synced"


@router.post("/docs/{slug}/link", response_model=LinkResponse)
async def link_document(
    slug: str,
    payload: LinkRequest,
    db: Session = Depends(get_db),
):
    """Link a Scribe document with an existing Google Doc.

    This establishes the sync relationship and stores the initial revision ID.
    """
    doc = get_document_or_404(db, slug)
    drive = build_drive_service(db)

    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    try:
        # Verify the Google Doc exists and get its revision
        file_meta = drive.files().get(
            fileId=payload.google_doc_id,
            fields="id,name,mimeType,headRevisionId",
        ).execute()

        # Verify it's a Google Doc
        if file_meta.get("mimeType") != "application/vnd.google-apps.document":
            raise HTTPException(
                status_code=400,
                detail="The specified file is not a Google Doc"
            )

        revision_id = file_meta.get("headRevisionId")

        # Update document with sync info
        doc.source_provider = "google"
        doc.source_id = payload.google_doc_id
        doc.google_revision_id = revision_id
        doc.last_synced_at = datetime.utcnow()
        doc.sync_status = "synced"
        doc.local_version_hash = compute_content_hash(doc.content or {})

        db.commit()

        return LinkResponse(
            success=True,
            google_doc_id=payload.google_doc_id,
            google_revision_id=revision_id,
            message=f"Successfully linked to Google Doc: {file_meta.get('name')}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link document: {str(e)}")


@router.delete("/docs/{slug}/link")
async def unlink_document(
    slug: str,
    db: Session = Depends(get_db),
):
    """Unlink a Scribe document from Google Docs.

    This removes the sync relationship but preserves the document content.
    """
    doc = get_document_or_404(db, slug)

    # Clear sync-related fields
    doc.google_revision_id = None
    doc.last_synced_at = None
    doc.sync_status = "none"
    doc.local_version_hash = None
    # Keep source_provider and source_id for reference

    db.commit()

    return {"success": True, "message": "Document unlinked from Google Docs"}


@router.get("/docs/{slug}/status", response_model=SyncStatusResponse)
async def get_sync_status(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get the current sync status of a document.

    This checks both the local state and fetches the current Google Doc revision
    to detect any changes.
    """
    doc = get_document_or_404(db, slug)
    warnings = []

    # Check if document is linked
    linked = bool(doc.source_id and doc.source_provider == "google")

    if not linked:
        return SyncStatusResponse(
            linked=False,
            sync_status="none",
        )

    # Get current Google Doc revision
    drive = build_drive_service(db)
    current_revision = None

    if drive:
        try:
            file_meta = drive.files().get(
                fileId=doc.source_id,
                fields="headRevisionId",
            ).execute()
            current_revision = file_meta.get("headRevisionId")
        except Exception as e:
            warnings.append(f"Could not fetch Google Doc status: {str(e)}")

    # Detect sync status
    sync_status = detect_sync_status(doc, current_revision)

    # Update sync_status in database if changed
    if doc.sync_status != sync_status:
        doc.sync_status = sync_status
        db.commit()

    return SyncStatusResponse(
        linked=True,
        google_doc_id=doc.source_id,
        sync_status=sync_status,
        last_synced_at=doc.last_synced_at,
        google_revision_id=doc.google_revision_id,
        local_version_hash=doc.local_version_hash,
        warnings=warnings,
    )


@router.post("/docs/{slug}/push", response_model=PushResponse)
async def push_to_google(
    slug: str,
    db: Session = Depends(get_db),
):
    """Push local changes to the linked Google Doc.

    This transforms the TipTap content to Google Docs format and applies
    updates via the batchUpdate API.
    """
    doc = get_document_or_404(db, slug)
    warnings = []

    if not doc.source_id or doc.source_provider != "google":
        raise HTTPException(status_code=400, detail="Document is not linked to Google Docs")

    docs_service = build_docs_service(db)
    drive = build_drive_service(db)

    if not docs_service or not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    try:
        # Transform TipTap content to Google Docs requests
        content = doc.content or {}
        tiptap_json = content.get("json", {"type": "doc", "content": []})

        transformer = TipTapToGoogleDocs()
        result = transformer.transform(tiptap_json)

        warnings.extend(result.warnings)

        # Clear the existing document content first
        # Get current document to find end index
        google_doc = docs_service.documents().get(documentId=doc.source_id).execute()
        body = google_doc.get("body", {})
        body_content = body.get("content", [])

        # Find the end index of the document
        end_index = 1
        for element in body_content:
            if "endIndex" in element:
                end_index = max(end_index, element["endIndex"])

        # Prepare requests: delete existing content, then insert new
        requests = []

        # Delete existing content (if any)
        if end_index > 2:
            requests.append({
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": end_index - 1,
                    }
                }
            })

        # Add the transformed requests
        requests.extend(result.requests)

        # Execute batchUpdate
        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc.source_id,
                body={"requests": requests},
            ).execute()

        # Get the new revision ID
        file_meta = drive.files().get(
            fileId=doc.source_id,
            fields="headRevisionId",
        ).execute()
        new_revision_id = file_meta.get("headRevisionId")

        # Update sync state
        doc.google_revision_id = new_revision_id
        doc.last_synced_at = datetime.utcnow()
        doc.sync_status = "synced"
        doc.local_version_hash = compute_content_hash(doc.content or {})

        db.commit()

        return PushResponse(
            success=True,
            new_revision_id=new_revision_id,
            claims_preserved=result.claims_count,
            citations_preserved=result.citations_count,
            warnings=warnings,
        )

    except HTTPException:
        raise
    except Exception as e:
        return PushResponse(
            success=False,
            error=str(e),
            warnings=warnings,
        )


@router.post("/docs/{slug}/pull", response_model=PullResponse)
async def pull_from_google(
    slug: str,
    db: Session = Depends(get_db),
):
    """Pull changes from the linked Google Doc to local.

    This fetches the Google Doc content, transforms it to TipTap format,
    and updates the local document.
    """
    doc = get_document_or_404(db, slug)
    warnings = []

    if not doc.source_id or doc.source_provider != "google":
        raise HTTPException(status_code=400, detail="Document is not linked to Google Docs")

    docs_service = build_docs_service(db)
    drive = build_drive_service(db)

    if not docs_service or not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    try:
        # Fetch the Google Doc
        google_doc = docs_service.documents().get(documentId=doc.source_id).execute()

        # Transform to TipTap
        transformer = GoogleDocsToTipTap()
        tiptap_json, claims_restored, citations_restored, transform_warnings = transformer.transform(google_doc)

        warnings.extend(transform_warnings)

        # Get the new revision ID
        file_meta = drive.files().get(
            fileId=doc.source_id,
            fields="headRevisionId",
        ).execute()
        new_revision_id = file_meta.get("headRevisionId")

        # Update document content
        doc.content = {
            "json": tiptap_json,
            "html": "",  # Will be regenerated by frontend
        }
        doc.google_revision_id = new_revision_id
        doc.last_synced_at = datetime.utcnow()
        doc.sync_status = "synced"
        doc.local_version_hash = compute_content_hash(doc.content)

        db.commit()

        return PullResponse(
            success=True,
            claims_restored=claims_restored,
            citations_restored=citations_restored,
            warnings=warnings,
        )

    except HTTPException:
        raise
    except Exception as e:
        return PullResponse(
            success=False,
            error=str(e),
            warnings=warnings,
        )


@router.post("/docs/{slug}/resolve", response_model=ResolveResponse)
async def resolve_conflict(
    slug: str,
    payload: ResolveRequest,
    db: Session = Depends(get_db),
):
    """Resolve a sync conflict using the specified strategy.

    Strategies:
    - keep_local: Push local changes, overwriting Google Doc
    - keep_remote: Pull Google Doc changes, overwriting local
    """
    doc = get_document_or_404(db, slug)

    if doc.sync_status != "conflict":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not in conflict state (current: {doc.sync_status})"
        )

    if payload.strategy == "keep_local":
        # Push local changes
        result = await push_to_google(slug, db)
        if result.success:
            return ResolveResponse(
                success=True,
                new_sync_status="synced",
                message="Conflict resolved: local changes pushed to Google Docs",
            )
        return ResolveResponse(
            success=False,
            new_sync_status="conflict",
            message=f"Failed to resolve: {result.error}",
        )

    elif payload.strategy == "keep_remote":
        # Pull Google changes
        result = await pull_from_google(slug, db)
        if result.success:
            return ResolveResponse(
                success=True,
                new_sync_status="synced",
                message="Conflict resolved: Google Doc changes pulled to local",
            )
        return ResolveResponse(
            success=False,
            new_sync_status="conflict",
            message=f"Failed to resolve: {result.error}",
        )

    raise HTTPException(status_code=400, detail=f"Unknown strategy: {payload.strategy}")


# =============================================================================
# Google Slides Sync Endpoints (for presentations)
# =============================================================================


def compute_slides_hash(slides_data: dict) -> str:
    """Compute hash for slides_data to detect changes."""
    return compute_content_hash(slides_data)


@router.post("/slides/{slug}/link", response_model=LinkResponse)
async def link_presentation(
    slug: str,
    payload: LinkRequest,
    db: Session = Depends(get_db),
):
    """Link a Scribe presentation with an existing Google Slides.

    This establishes the sync relationship for presentations.
    """
    doc = get_document_or_404(db, slug)
    drive = build_drive_service(db)

    if doc.doc_type != "presentation":
        raise HTTPException(status_code=400, detail="Document is not a presentation")

    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    try:
        # Verify the Google Slides exists
        file_meta = drive.files().get(
            fileId=payload.google_doc_id,
            fields="id,name,mimeType,headRevisionId",
        ).execute()

        # Verify it's a Google Slides presentation
        if file_meta.get("mimeType") != "application/vnd.google-apps.presentation":
            raise HTTPException(
                status_code=400,
                detail="The specified file is not a Google Slides presentation"
            )

        revision_id = file_meta.get("headRevisionId")

        # Get slides_data for hashing
        slides_data = (doc.front_matter or {}).get("slides_data", {})

        # Update document with sync info
        doc.source_provider = "google"
        doc.source_id = payload.google_doc_id
        doc.google_revision_id = revision_id
        doc.last_synced_at = datetime.utcnow()
        doc.sync_status = "synced"
        doc.local_version_hash = compute_slides_hash(slides_data)

        db.commit()

        return LinkResponse(
            success=True,
            google_doc_id=payload.google_doc_id,
            google_revision_id=revision_id,
            message=f"Successfully linked to Google Slides: {file_meta.get('name')}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link presentation: {str(e)}")


@router.delete("/slides/{slug}/link")
async def unlink_presentation(
    slug: str,
    db: Session = Depends(get_db),
):
    """Unlink a Scribe presentation from Google Slides."""
    doc = get_document_or_404(db, slug)

    # Clear sync-related fields
    doc.google_revision_id = None
    doc.last_synced_at = None
    doc.sync_status = "none"
    doc.local_version_hash = None

    db.commit()

    return {"success": True, "message": "Presentation unlinked from Google Slides"}


@router.get("/slides/{slug}/status", response_model=SyncStatusResponse)
async def get_slides_sync_status(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get the current sync status of a presentation."""
    doc = get_document_or_404(db, slug)
    warnings = []

    # Check if document is linked
    linked = bool(doc.source_id and doc.source_provider == "google")

    if not linked:
        return SyncStatusResponse(
            linked=False,
            sync_status="none",
        )

    # Get current Google Slides revision
    drive = build_drive_service(db)
    current_revision = None

    if drive:
        try:
            file_meta = drive.files().get(
                fileId=doc.source_id,
                fields="headRevisionId",
            ).execute()
            current_revision = file_meta.get("headRevisionId")
        except Exception as e:
            warnings.append(f"Could not fetch Google Slides status: {str(e)}")

    # Detect sync status (using slides_data hash)
    slides_data = (doc.front_matter or {}).get("slides_data", {})
    current_hash = compute_slides_hash(slides_data)

    google_changed = (
        current_revision is not None
        and doc.google_revision_id is not None
        and doc.google_revision_id != current_revision
    )

    local_changed = (
        doc.local_version_hash is not None
        and doc.local_version_hash != current_hash
    )

    if google_changed and local_changed:
        sync_status = "conflict"
    elif google_changed:
        sync_status = "remote_changed"
    elif local_changed:
        sync_status = "local_changed"
    else:
        sync_status = "synced"

    # Update sync_status in database if changed
    if doc.sync_status != sync_status:
        doc.sync_status = sync_status
        db.commit()

    return SyncStatusResponse(
        linked=True,
        google_doc_id=doc.source_id,
        sync_status=sync_status,
        last_synced_at=doc.last_synced_at,
        google_revision_id=doc.google_revision_id,
        local_version_hash=doc.local_version_hash,
        warnings=warnings,
    )


@router.post("/slides/{slug}/push", response_model=PushResponse)
async def push_slides_to_google(
    slug: str,
    db: Session = Depends(get_db),
):
    """Push local presentation to the linked Google Slides."""
    doc = get_document_or_404(db, slug)
    warnings = []

    if not doc.source_id or doc.source_provider != "google":
        raise HTTPException(status_code=400, detail="Presentation is not linked to Google Slides")

    slides_service = build_slides_service(db)
    drive = build_drive_service(db)

    if not slides_service or not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    try:
        slides_data = (doc.front_matter or {}).get("slides_data", {})

        # Get current presentation to delete existing slides
        presentation = slides_service.presentations().get(
            presentationId=doc.source_id
        ).execute()

        # Delete all existing slides
        delete_requests = delete_all_slides_requests(presentation)

        # Transform Scribe slides to Google Slides requests
        transformer = ScribeToGoogleSlides()
        create_requests, transform_warnings = transformer.transform(slides_data, doc.source_id)
        warnings.extend(transform_warnings)

        # Combine requests: delete first, then create
        all_requests = delete_requests + create_requests

        # Execute batchUpdate
        if all_requests:
            slides_service.presentations().batchUpdate(
                presentationId=doc.source_id,
                body={"requests": all_requests},
            ).execute()

        # Get the new revision ID
        file_meta = drive.files().get(
            fileId=doc.source_id,
            fields="headRevisionId",
        ).execute()
        new_revision_id = file_meta.get("headRevisionId")

        # Update sync state
        doc.google_revision_id = new_revision_id
        doc.last_synced_at = datetime.utcnow()
        doc.sync_status = "synced"
        doc.local_version_hash = compute_slides_hash(slides_data)

        db.commit()

        return PushResponse(
            success=True,
            new_revision_id=new_revision_id,
            claims_preserved=0,
            citations_preserved=0,
            warnings=warnings,
        )

    except HTTPException:
        raise
    except Exception as e:
        return PushResponse(
            success=False,
            error=str(e),
            warnings=warnings,
        )


@router.post("/slides/{slug}/pull", response_model=PullResponse)
async def pull_slides_from_google(
    slug: str,
    db: Session = Depends(get_db),
):
    """Pull changes from the linked Google Slides to local."""
    doc = get_document_or_404(db, slug)
    warnings = []

    if not doc.source_id or doc.source_provider != "google":
        raise HTTPException(status_code=400, detail="Presentation is not linked to Google Slides")

    slides_service = build_slides_service(db)
    drive = build_drive_service(db)

    if not slides_service or not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    try:
        # Fetch the Google Slides presentation
        presentation = slides_service.presentations().get(
            presentationId=doc.source_id
        ).execute()

        # Transform to Scribe slides_data
        transformer = GoogleSlidesToScribe()
        slides_data, transform_warnings = transformer.transform(presentation)
        warnings.extend(transform_warnings)

        # Get the new revision ID
        file_meta = drive.files().get(
            fileId=doc.source_id,
            fields="headRevisionId",
        ).execute()
        new_revision_id = file_meta.get("headRevisionId")

        # Update document front_matter with new slides_data
        front_matter = doc.front_matter or {}
        front_matter["slides_data"] = slides_data
        doc.front_matter = front_matter

        doc.google_revision_id = new_revision_id
        doc.last_synced_at = datetime.utcnow()
        doc.sync_status = "synced"
        doc.local_version_hash = compute_slides_hash(slides_data)

        db.commit()

        return PullResponse(
            success=True,
            claims_restored=0,
            citations_restored=0,
            warnings=warnings,
        )

    except HTTPException:
        raise
    except Exception as e:
        return PullResponse(
            success=False,
            error=str(e),
            warnings=warnings,
        )


@router.post("/slides/{slug}/resolve", response_model=ResolveResponse)
async def resolve_slides_conflict(
    slug: str,
    payload: ResolveRequest,
    db: Session = Depends(get_db),
):
    """Resolve a sync conflict for presentations."""
    doc = get_document_or_404(db, slug)

    if doc.sync_status != "conflict":
        raise HTTPException(
            status_code=400,
            detail=f"Presentation is not in conflict state (current: {doc.sync_status})"
        )

    if payload.strategy == "keep_local":
        result = await push_slides_to_google(slug, db)
        if result.success:
            return ResolveResponse(
                success=True,
                new_sync_status="synced",
                message="Conflict resolved: local changes pushed to Google Slides",
            )
        return ResolveResponse(
            success=False,
            new_sync_status="conflict",
            message=f"Failed to resolve: {result.error}",
        )

    elif payload.strategy == "keep_remote":
        result = await pull_slides_from_google(slug, db)
        if result.success:
            return ResolveResponse(
                success=True,
                new_sync_status="synced",
                message="Conflict resolved: Google Slides changes pulled to local",
            )
        return ResolveResponse(
            success=False,
            new_sync_status="conflict",
            message=f"Failed to resolve: {result.error}",
        )

    raise HTTPException(status_code=400, detail=f"Unknown strategy: {payload.strategy}")


# =============================================================================
# View in Drive URL
# =============================================================================


@router.get("/{slug}/drive-url", response_model=DriveUrlResponse)
async def get_drive_url(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get the Google Drive URL for the linked document or presentation."""
    doc = get_document_or_404(db, slug)

    if not doc.source_id or doc.source_provider != "google":
        raise HTTPException(status_code=400, detail="Document is not linked to Google")

    if doc.doc_type == "presentation":
        url = f"https://docs.google.com/presentation/d/{doc.source_id}/edit"
        file_type = "presentation"
    else:
        url = f"https://docs.google.com/document/d/{doc.source_id}/edit"
        file_type = "document"

    return DriveUrlResponse(url=url, file_type=file_type)
