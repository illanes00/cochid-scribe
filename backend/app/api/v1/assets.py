"""Asset upload endpoints."""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"


@router.post("/upload")
async def upload_asset(file: UploadFile):
    """Upload an asset and return its URL."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix or ""
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / filename

    content = await file.read()
    dest.write_bytes(content)

    return {"url": f"/uploads/{filename}", "name": filename}
