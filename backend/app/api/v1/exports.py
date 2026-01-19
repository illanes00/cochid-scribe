"""Export job endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.export import ExportJob
from app.schemas.export import ExportJobResponse
from app.services.slides_export import create_presentation

router = APIRouter()


@router.get("/{job_id}", response_model=ExportJobResponse)
async def get_export_job(job_id: str, db: Session = Depends(get_db)):
    """Get export job status."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job


@router.get("/{job_id}/download")
async def download_export(job_id: str, db: Session = Depends(get_db)):
    """Download the exported file."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    if job.status != "done" or not job.output_path:
        raise HTTPException(status_code=400, detail="Export not ready")
    if not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="Export file missing")
    return FileResponse(job.output_path, filename=job.output_path.split("/")[-1])


@router.post("/{slug}/export-pptx")
async def export_presentation(slug: str, db: Session = Depends(get_db)):
    """Export a document's slides_data as a branded PPTX using python-pptx."""
    document = db.query(Document).filter(Document.slug == slug).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    slides_data = {}
    if isinstance(document.front_matter, dict):
        slides_data = document.front_matter.get("slides_data") or {}

    pptx_buffer = create_presentation(slides_data or {"slides": [], "theme": {}})

    return StreamingResponse(
        pptx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{slug}.pptx"'},
    )
