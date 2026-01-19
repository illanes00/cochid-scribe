"""Documents API endpoints."""

import difflib
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.v1.llm import extract_claims_from_text
from app.config import get_settings
from app.db.session import SessionLocal, get_db
from app.models.claim import Claim
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.export import ExportJob
from app.schemas.document import (
    DocumentCreate,
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
)
from app.schemas.document_version import (
    DocumentVersionCreate,
    DocumentVersionDetail,
    DocumentVersionResponse,
)
from app.schemas.export import ExportJobResponse, ExportRequest
from app.services.claim_positions import find_claim_offsets
from app.services.content_links import update_document_links
from app.services.conversion import (
    get_default_template,
    html_to_markdown,
    markdown_to_binary,
    markdown_to_html,
    temp_output_path,
)
from app.services.slides_export import create_presentation

router = APIRouter()
settings = get_settings()


def normalize_content(
    content: dict | None,
    markdown: str | None,
) -> tuple[dict, str | None]:
    """Ensure content has HTML and markdown is available."""
    content = content or {}
    html = content.get("html") if isinstance(content, dict) else None

    if html and not markdown:
        try:
            markdown = html_to_markdown(html)
        except Exception:
            markdown = markdown or ""
    elif markdown and not html:
        try:
            html = markdown_to_html(markdown)
            content["html"] = html
        except Exception:
            pass

    return content, markdown


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


def is_significant_change(old_text: str, new_text: str) -> bool:
    """Check if content changed enough to re-run claim extraction."""
    old_text = (old_text or "").strip()
    new_text = (new_text or "").strip()

    if not new_text:
        return False
    if not old_text:
        return len(new_text) > 50
    if old_text == new_text:
        return False

    length_delta = abs(len(new_text) - len(old_text))
    similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()
    return length_delta > 50 or similarity < 0.85


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
        db.query(Document).order_by(Document.updated_at.desc()).offset(offset).limit(per_page).all()
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

    content, markdown = normalize_content(data.content, data.markdown)

    doc = Document(
        slug=slug,
        title=data.title,
        doc_type=data.doc_type,
        content=content,
        markdown=markdown,
        front_matter=data.front_matter,
        source_provider=data.source_provider,
        source_id=data.source_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    update_document_links(db, doc.id, "document", content.get("json"), content.get("html"))

    return get_document_response(doc, db)


@router.get("/{slug}/versions", response_model=list[DocumentVersionResponse])
async def list_document_versions(
    slug: str,
    db: Session = Depends(get_db),
):
    """List version snapshots for a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc.id)
        .order_by(DocumentVersion.created_at.desc())
        .all()
    )
    return versions


@router.post("/{slug}/versions", response_model=DocumentVersionResponse, status_code=201)
async def create_document_version(
    slug: str,
    data: DocumentVersionCreate,
    db: Session = Depends(get_db),
):
    """Create a version snapshot for a document."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    label = data.label or datetime.utcnow().strftime("snapshot-%Y%m%d-%H%M%S")
    version = DocumentVersion(
        document_id=doc.id,
        label=label,
        content=doc.content or {},
        markdown=doc.markdown,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.post("/{slug}/versions/{version_id}/restore", response_model=DocumentResponse)
async def restore_document_version(
    slug: str,
    version_id: str,
    db: Session = Depends(get_db),
):
    """Restore a document to a previous version snapshot."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    version = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.id == version_id, DocumentVersion.document_id == doc.id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    doc.content = version.content or {}
    doc.markdown = version.markdown
    doc.version = version.label or doc.version
    db.commit()
    db.refresh(doc)

    update_document_links(db, doc.id, "document", doc.content.get("json"), doc.content.get("html"))

    return get_document_response(doc, db)


@router.get("/{slug}/versions/{version_id}", response_model=DocumentVersionDetail)
async def get_document_version(
    slug: str,
    version_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific document version snapshot."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    version = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.id == version_id, DocumentVersion.document_id == doc.id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return version


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

    old_markdown = doc.markdown or ""

    update_data = data.model_dump(exclude_unset=True)
    if "content" in update_data or "markdown" in update_data:
        content, markdown = normalize_content(
            update_data.get("content"),
            update_data.get("markdown"),
        )
        update_data["content"] = content
        update_data["markdown"] = markdown
    for field, value in update_data.items():
        setattr(doc, field, value)

    db.commit()
    db.refresh(doc)

    if "content" in update_data:
        update_document_links(
            db,
            doc.id,
            "document",
            update_data.get("content", {}).get("json"),
            update_data.get("content", {}).get("html"),
        )

    if (
        settings.anthropic_api_key
        and ("content" in update_data or "markdown" in update_data)
        and is_significant_change(old_markdown, doc.markdown or "")
    ):
        try:
            text = doc.markdown or ""
            if not text and isinstance(doc.content, dict):
                text = str(doc.content.get("html") or "")

            claims = await run_in_threadpool(extract_claims_from_text, text)
            existing_texts = {
                row[0]
                for row in db.query(Claim.claim_text).filter(Claim.document_id == doc.id).all()
            }
            created = 0
            for claim in claims:
                claim_text = str(claim.get("claim_text") or claim.get("text") or "").strip()
                if not claim_text or claim_text in existing_texts:
                    continue
                start_offset, end_offset = find_claim_offsets(text, claim_text)

                claim_type = str(claim.get("claim_type") or claim.get("type") or "MIXED").upper()
                evidence_needed = claim.get("evidence_needed")
                evidence = (
                    [{"kind": "OBSERVATION", "ref": "LLM", "notes": str(evidence_needed)}]
                    if evidence_needed
                    else []
                )

                claim_obj = Claim(
                    claim_id=f"C-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
                    document_id=doc.id,
                    claim_text=claim_text,
                    claim_type=claim_type,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    section=str(claim.get("section") or "").strip() or None,
                    evidence=evidence,
                    source_sentences=[],
                )
                db.add(claim_obj)
                existing_texts.add(claim_text)
                created += 1

            if created:
                db.commit()
        except Exception as exc:
            print(f"Claim extraction failed: {exc}")

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


@router.post("/import", response_model=DocumentResponse, status_code=201)
async def import_document(
    file: UploadFile,
    title: str | None = Form(default=None),
    doc_type: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """Import a document file (md, docx, pptx) into Scribe."""
    import tempfile

    import pypandoc

    raw = await file.read()
    filename = file.filename or "document"
    suffix = filename.split(".")[-1].lower()
    base_title = title or filename.rsplit(".", 1)[0]

    content_html = ""
    markdown = ""

    if suffix in {"md", "markdown"}:
        markdown = raw.decode("utf-8", errors="ignore")
        content_html = markdown_to_html(markdown)
    elif suffix in {"docx", "pptx"}:
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as tmp:
                tmp.write(raw)
                tmp_path = tmp.name
            content_html = pypandoc.convert_file(tmp_path, "html", format=suffix)
            try:
                import os

                os.remove(tmp_path)
            except OSError:
                pass
        except Exception:
            content_html = ""
    else:
        markdown = raw.decode("utf-8", errors="ignore")
        content_html = markdown_to_html(markdown)

    content = {"html": content_html}
    content, markdown = normalize_content(content, markdown)

    slug = slugify(base_title)
    existing = db.query(Document).filter(Document.slug == slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    doc = Document(
        slug=slug,
        title=base_title,
        doc_type=doc_type or "paper",
        content=content,
        markdown=markdown,
        front_matter={},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    update_document_links(db, doc.id, "document", content.get("json"), content.get("html"))

    return get_document_response(doc, db)


def run_export_job(job_id: str, doc_id: str, export_format: str) -> None:
    """Execute an export job and update status."""
    db = SessionLocal()
    try:
        job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not job or not doc:
            return
        job.status = "running"
        db.commit()

        html = ""
        if isinstance(doc.content, dict):
            html = str(doc.content.get("html") or "")

        try:
            if export_format == "markdown":
                output = doc.markdown or html_to_markdown(html or "")
                output_path = temp_output_path(".md")
                output_path.write_text(output, encoding="utf-8")
            elif export_format == "html":
                output = html or markdown_to_html(doc.markdown or "")
                output_path = temp_output_path(".html")
                output_path.write_text(output, encoding="utf-8")
            elif export_format == "latex":
                output_path = temp_output_path(".tex")
                markdown_to_binary(
                    doc.markdown or html_to_markdown(html or ""),
                    "latex",
                    output_path,
                    extra_args=["--template", str(get_default_template())],
                )
            elif export_format == "docx":
                output_path = temp_output_path(".docx")
                markdown_to_binary(
                    doc.markdown or html_to_markdown(html or ""), "docx", output_path
                )
            elif export_format == "pptx":
                output_path = temp_output_path(".pptx")
                slides_data = {}
                if isinstance(doc.front_matter, dict):
                    slides_data = doc.front_matter.get("slides_data") or {}
                if doc.doc_type == "presentation":
                    buffer = create_presentation(slides_data or {"slides": [], "theme": {}})
                    output_path.write_bytes(buffer.getvalue())
                else:
                    markdown_to_binary(
                        doc.markdown or html_to_markdown(html or ""), "pptx", output_path
                    )
            elif export_format == "pdf":
                output_path = temp_output_path(".pdf")
                markdown_to_binary(
                    doc.markdown or html_to_markdown(html or ""),
                    "pdf",
                    output_path,
                    extra_args=["--template", str(get_default_template())],
                )
            else:
                raise ValueError("Unsupported export format")

            job.status = "done"
            job.output_path = str(output_path)
            job.error = None
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)

        db.commit()
    finally:
        db.close()


@router.post("/{slug}/export", response_model=ExportJobResponse)
async def export_document(
    slug: str,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Export a document to a given format as a background job."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    job = ExportJob(document_id=doc.id, format=request.format, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_export_job, job.id, doc.id, request.format)

    return job
