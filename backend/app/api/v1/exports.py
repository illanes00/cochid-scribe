"""Export job endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.session import get_db
from app.models.export import ExportJob
from app.schemas.export import ExportJobResponse

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
