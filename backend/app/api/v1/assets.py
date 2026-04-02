"""Asset API endpoints."""

import os
import re
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.asset import Asset
from app.schemas.asset import AssetResponse

router = APIRouter(tags=["assets"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "assets"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Pattern for valid asset filenames: UUID followed by extension
VALID_FILENAME_PATTERN = re.compile(r"^[a-f0-9\-]{36}\.[a-zA-Z0-9]+$")


def safe_asset_path(filename: str) -> Path:
    """
    Safely resolve an asset path, preventing path traversal attacks.

    Args:
        filename: The filename to resolve (should be UUID + extension)

    Returns:
        Resolved Path within UPLOAD_DIR

    Raises:
        HTTPException: If the path would escape UPLOAD_DIR or filename is invalid
    """
    # Extract just the filename component (defense against ../../../)
    safe_name = Path(filename).name

    # Validate filename format (should be UUID.ext from our upload)
    if not VALID_FILENAME_PATTERN.match(safe_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid asset filename format"
        )

    # Construct and resolve the full path
    filepath = (UPLOAD_DIR / safe_name).resolve()

    # Verify the resolved path is still within UPLOAD_DIR
    # This catches symlink attacks and edge cases
    try:
        filepath.relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid asset path"
        )

    return filepath


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    document_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List assets, optionally filtered by document_id."""
    query = db.query(Asset)
    if document_id:
        query = query.filter(Asset.document_id == document_id)
    return (
        query.order_by(Asset.created_at.desc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 200))
        .all()
    )


@router.post("/upload", response_model=AssetResponse)
async def upload_asset(
    file: UploadFile = File(...),
    document_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Upload a new asset and persist metadata."""
    asset_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1]
    safe_name = f"{asset_id}{ext}"
    filepath = UPLOAD_DIR / safe_name

    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    filepath.write_bytes(content)

    asset = Asset(
        id=asset_id,
        document_id=document_id,
        filename=file.filename or safe_name,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        url=f"/uploads/assets/{safe_name}",
        source_url=None,
        created_at=datetime.utcnow(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """Get asset metadata by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    """Delete an asset and its file."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Safely resolve the file path, preventing path traversal
    try:
        filepath = safe_asset_path(Path(asset.url).name)
        if filepath.exists():
            filepath.unlink()
    except HTTPException:
        # If path validation fails, log but continue with DB deletion
        # The file may have been manually deleted or the URL was corrupted
        pass

    db.delete(asset)
    db.commit()
    return {"status": "deleted"}
