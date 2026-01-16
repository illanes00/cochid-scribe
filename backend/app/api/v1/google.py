"""Google Docs/Slides import/export endpoints."""

import tempfile
from datetime import datetime

import pypandoc
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from googleapiclient.http import MediaFileUpload
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.services.conversion import html_to_markdown, markdown_to_binary, markdown_to_html
from app.services.google import build_drive_service
from app.services.content_links import update_document_links

router = APIRouter()


class GoogleImportRequest(BaseModel):
    file_id: str
    title: str | None = None
    format: str | None = None  # html or docx/pptx


class GoogleExportRequest(BaseModel):
    slug: str
    folder_id: str | None = None


def normalize_content(content: dict | None, markdown: str | None) -> tuple[dict, str | None]:
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


@router.post("/docs/import")
async def import_google_doc(
    payload: GoogleImportRequest,
    db: Session = Depends(get_db),
):
    """Import a Google Doc by file ID."""
    drive = build_drive_service(db)
    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    file_meta = drive.files().get(fileId=payload.file_id, fields="mimeType,name").execute()
    mime_type = (file_meta.get("mimeType") or "").lower()

    export_format = (payload.format or "html").lower()
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        data = drive.files().get_media(fileId=payload.file_id).execute()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            html = pypandoc.convert_file(tmp_path, "html", format="docx")
        except Exception:
            html = ""
        finally:
            try:
                import os

                os.remove(tmp_path)
            except OSError:
                pass
    elif export_format == "docx":
        data = drive.files().export_media(
            fileId=payload.file_id,
            mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ).execute()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            html = pypandoc.convert_file(tmp_path, "html", format="docx")
        except Exception:
            html = ""
        finally:
            try:
                import os

                os.remove(tmp_path)
            except OSError:
                pass
    else:
        data = drive.files().export_media(fileId=payload.file_id, mimeType="text/html").execute()
        html = data.decode("utf-8", errors="ignore")

    content = {"html": html}
    content, markdown = normalize_content(content, None)

    doc_title = payload.title or f"Imported Doc {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    slug = doc_title.lower().strip().replace(" ", "-")[:100]
    existing = db.query(Document).filter(Document.slug == slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    doc = Document(
        slug=slug,
        title=doc_title,
        doc_type="paper",
        content=content,
        markdown=markdown,
        front_matter={},
        source_provider="google",
        source_id=payload.file_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    update_document_links(db, doc.id, "document", content.get("json"), content.get("html"))

    return {"slug": doc.slug, "title": doc.title}


@router.post("/docs/export")
async def export_google_doc(
    payload: GoogleExportRequest,
    db: Session = Depends(get_db),
):
    """Export a document to Google Docs and return the file ID."""
    drive = build_drive_service(db)
    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    doc = db.query(Document).filter(Document.slug == payload.slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    output_path = tempfile.NamedTemporaryFile(suffix=".docx", delete=False).name
    html = doc.content.get("html") if isinstance(doc.content, dict) else ""
    markdown_to_binary(doc.markdown or html_to_markdown(html or ""), "docx", output_path)

    media = MediaFileUpload(
        output_path,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    file_metadata = {"name": doc.title, "mimeType": "application/vnd.google-apps.document"}
    if payload.folder_id:
        file_metadata["parents"] = [payload.folder_id]

    created = drive.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
    doc.source_provider = "google"
    doc.source_id = created.get("id")
    db.commit()
    try:
        import os

        os.remove(output_path)
    except OSError:
        pass
    return {"file_id": created.get("id"), "url": created.get("webViewLink")}


@router.post("/slides/export")
async def export_google_slides(
    payload: GoogleExportRequest,
    db: Session = Depends(get_db),
):
    """Export a document to Google Slides (via PPTX)."""
    drive = build_drive_service(db)
    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    doc = db.query(Document).filter(Document.slug == payload.slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    output_path = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False).name
    html = doc.content.get("html") if isinstance(doc.content, dict) else ""
    markdown_to_binary(doc.markdown or html_to_markdown(html or ""), "pptx", output_path)

    media = MediaFileUpload(
        output_path,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    file_metadata = {"name": doc.title, "mimeType": "application/vnd.google-apps.presentation"}
    if payload.folder_id:
        file_metadata["parents"] = [payload.folder_id]

    created = drive.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
    doc.source_provider = "google"
    doc.source_id = created.get("id")
    db.commit()
    try:
        import os

        os.remove(output_path)
    except OSError:
        pass
    return {"file_id": created.get("id"), "url": created.get("webViewLink")}


@router.post("/slides/import")
async def import_google_slides(
    payload: GoogleImportRequest,
    db: Session = Depends(get_db),
):
    """Import a Google Slides deck by file ID."""
    drive = build_drive_service(db)
    if not drive:
        raise HTTPException(status_code=400, detail="Google integration not connected")

    file_meta = drive.files().get(fileId=payload.file_id, fields="mimeType,name").execute()
    mime_type = (file_meta.get("mimeType") or "").lower()
    export_format = (payload.format or "pptx").lower()
    if export_format != "pptx":
        export_format = "pptx"

    if mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        data = drive.files().get_media(fileId=payload.file_id).execute()
    else:
        data = drive.files().export_media(
            fileId=payload.file_id,
            mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ).execute()

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        html = pypandoc.convert_file(tmp_path, "html", format="pptx")
    except Exception:
        html = ""
    finally:
        try:
            import os

            os.remove(tmp_path)
        except OSError:
            pass

    content = {"html": html}
    content, markdown = normalize_content(content, None)

    doc_title = payload.title or f"Imported Slides {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    slug = doc_title.lower().strip().replace(" ", "-")[:100]
    existing = db.query(Document).filter(Document.slug == slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    doc = Document(
        slug=slug,
        title=doc_title,
        doc_type="policy",
        content=content,
        markdown=markdown,
        front_matter={},
        source_provider="google",
        source_id=payload.file_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    update_document_links(db, doc.id, "document", content.get("json"), content.get("html"))

    return {"slug": doc.slug, "title": doc.title}
