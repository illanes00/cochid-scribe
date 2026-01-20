"""Integration tests for Google Docs/Slides sync with real Google API.

These tests require:
1. A Google integration configured in the database with valid tokens
2. Network access to Google APIs
3. Test documents in Google Drive (created by the tests)

Run with: pytest tests/test_google_sync_integration.py -v --integration

Skip if no Google credentials are available.
"""

import os
import pytest
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.session import engine
from app.models import Document, Integration
from app.services.google import (
    build_docs_service,
    build_drive_service,
    build_slides_service,
)
from app.services.google_docs_transform import (
    TipTapToGoogleDocs,
    GoogleDocsToTipTap,
    HeaderFooterTransform,
)


def has_google_integration() -> bool:
    """Check if Google integration is configured."""
    with Session(engine) as db:
        integration = db.query(Integration).filter(
            Integration.provider == "google"
        ).first()
        return integration is not None and integration.refresh_token is not None


# Skip all tests in this module if no Google integration
pytestmark = pytest.mark.skipif(
    not has_google_integration(),
    reason="Google integration not configured"
)


@pytest.fixture(scope="module")
def db_session():
    """Get database session for tests."""
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="module")
def google_services(db_session):
    """Build Google API services."""
    docs_service = build_docs_service(db_session)
    drive_service = build_drive_service(db_session)
    slides_service = build_slides_service(db_session)

    if not docs_service or not drive_service:
        pytest.skip("Could not build Google services - check token refresh")

    return {
        "docs": docs_service,
        "drive": drive_service,
        "slides": slides_service,
    }


@pytest.fixture(scope="module")
def test_doc_id(google_services):
    """Create a test Google Doc and return its ID. Clean up after tests."""
    docs = google_services["docs"]
    drive = google_services["drive"]

    # Create a new Google Doc
    doc = docs.documents().create(body={
        "title": f"Scribe Integration Test - {datetime.utcnow().isoformat()}"
    }).execute()

    doc_id = doc["documentId"]
    yield doc_id

    # Clean up: delete the test document
    try:
        drive.files().delete(fileId=doc_id).execute()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="module")
def test_slides_id(google_services):
    """Create a test Google Slides and return its ID. Clean up after tests."""
    slides = google_services["slides"]
    drive = google_services["drive"]

    if not slides:
        pytest.skip("Slides service not available")

    # Create a new Google Slides presentation
    presentation = slides.presentations().create(body={
        "title": f"Scribe Integration Test - {datetime.utcnow().isoformat()}"
    }).execute()

    presentation_id = presentation["presentationId"]
    yield presentation_id

    # Clean up
    try:
        drive.files().delete(fileId=presentation_id).execute()
    except Exception:
        pass


class TestGoogleDocsIntegration:
    """Integration tests for Google Docs API."""

    def test_can_read_google_doc(self, google_services, test_doc_id):
        """Should be able to read a Google Doc."""
        docs = google_services["docs"]

        doc = docs.documents().get(documentId=test_doc_id).execute()

        assert doc is not None
        assert doc["documentId"] == test_doc_id
        assert "title" in doc
        assert "body" in doc

    def test_can_write_to_google_doc(self, google_services, test_doc_id):
        """Should be able to write content to a Google Doc."""
        docs = google_services["docs"]

        # Insert text
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": "Hello from Scribe integration test!\n"
                }
            }
        ]

        result = docs.documents().batchUpdate(
            documentId=test_doc_id,
            body={"requests": requests}
        ).execute()

        assert result is not None
        assert "replies" in result

        # Verify text was inserted
        doc = docs.documents().get(documentId=test_doc_id).execute()
        body_content = doc.get("body", {}).get("content", [])

        # Find the text we inserted
        text_found = False
        for element in body_content:
            if "paragraph" in element:
                for para_element in element["paragraph"].get("elements", []):
                    if "textRun" in para_element:
                        if "Hello from Scribe" in para_element["textRun"].get("content", ""):
                            text_found = True
                            break

        assert text_found, "Inserted text not found in document"

    def test_transform_tiptap_to_google_docs(self, google_services, test_doc_id):
        """Should correctly transform TipTap content to Google Docs format."""
        docs = google_services["docs"]

        # Create TipTap content
        tiptap_content = {
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Test Heading"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "This is "},
                        {"type": "text", "text": "bold text", "marks": [{"type": "bold"}]},
                        {"type": "text", "text": " and "},
                        {"type": "text", "text": "italic text", "marks": [{"type": "italic"}]},
                    ]
                },
                {
                    "type": "bulletList",
                    "content": [
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Item 1"}]}]},
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Item 2"}]}]},
                    ]
                }
            ]
        }

        # Transform to Google Docs requests
        transformer = TipTapToGoogleDocs()
        result = transformer.transform(tiptap_content)

        # Clear document first
        doc = docs.documents().get(documentId=test_doc_id).execute()
        body = doc.get("body", {})
        end_index = 1
        for element in body.get("content", []):
            if "endIndex" in element:
                end_index = max(end_index, element["endIndex"])

        clear_requests = []
        if end_index > 2:
            clear_requests.append({
                "deleteContentRange": {
                    "range": {"startIndex": 1, "endIndex": end_index - 1}
                }
            })

        all_requests = clear_requests + result.requests

        if all_requests:
            docs.documents().batchUpdate(
                documentId=test_doc_id,
                body={"requests": all_requests}
            ).execute()

        # Verify content
        doc = docs.documents().get(documentId=test_doc_id).execute()

        # Check for heading
        found_heading = False
        found_bold = False
        found_italic = False

        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                para = element["paragraph"]
                style = para.get("paragraphStyle", {}).get("namedStyleType", "")
                if "HEADING" in style:
                    found_heading = True

                for elem in para.get("elements", []):
                    if "textRun" in elem:
                        text_style = elem["textRun"].get("textStyle", {})
                        if text_style.get("bold"):
                            found_bold = True
                        if text_style.get("italic"):
                            found_italic = True

        assert found_heading, "Heading style not applied"
        assert found_bold, "Bold style not found"
        assert found_italic, "Italic style not found"

    def test_roundtrip_transform(self, google_services, test_doc_id):
        """TipTap -> Google Docs -> TipTap should preserve content."""
        docs = google_services["docs"]

        # Original TipTap content
        original_tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Roundtrip test paragraph."}]
                }
            ]
        }

        # Push to Google Docs
        to_google = TipTapToGoogleDocs()
        result = to_google.transform(original_tiptap)

        # Clear and insert
        doc = docs.documents().get(documentId=test_doc_id).execute()
        end_index = 1
        for element in doc.get("body", {}).get("content", []):
            if "endIndex" in element:
                end_index = max(end_index, element["endIndex"])

        requests = []
        if end_index > 2:
            requests.append({
                "deleteContentRange": {
                    "range": {"startIndex": 1, "endIndex": end_index - 1}
                }
            })
        requests.extend(result.requests)

        if requests:
            docs.documents().batchUpdate(
                documentId=test_doc_id,
                body={"requests": requests}
            ).execute()

        # Pull from Google Docs
        doc = docs.documents().get(documentId=test_doc_id).execute()
        from_google = GoogleDocsToTipTap()
        pulled_tiptap, _, _, _ = from_google.transform(doc)

        # Verify content was preserved
        def extract_text(node):
            if node.get("type") == "text":
                return node.get("text", "")
            texts = []
            for child in node.get("content", []):
                texts.append(extract_text(child))
            return "".join(texts)

        original_text = extract_text(original_tiptap)
        pulled_text = extract_text(pulled_tiptap)

        assert "Roundtrip test paragraph" in pulled_text


class TestGoogleDocsHeaderFooter:
    """Integration tests for Google Docs header/footer functionality."""

    def test_can_create_header(self, google_services, test_doc_id):
        """Should be able to create a header in Google Doc."""
        docs = google_services["docs"]

        # Create header
        requests = [{
            "createHeader": {
                "type": "DEFAULT",
                "sectionBreakLocation": {"index": 0}
            }
        }]

        result = docs.documents().batchUpdate(
            documentId=test_doc_id,
            body={"requests": requests}
        ).execute()

        # Get header ID from response
        header_id = None
        for reply in result.get("replies", []):
            if "createHeader" in reply:
                header_id = reply["createHeader"].get("headerId")

        assert header_id is not None, "Header was not created"

        # Verify header exists in document
        doc = docs.documents().get(documentId=test_doc_id).execute()
        assert "headers" in doc
        assert header_id in doc["headers"]

    def test_can_create_footer(self, google_services, test_doc_id):
        """Should be able to create a footer in Google Doc."""
        docs = google_services["docs"]

        # Create footer
        requests = [{
            "createFooter": {
                "type": "DEFAULT",
                "sectionBreakLocation": {"index": 0}
            }
        }]

        result = docs.documents().batchUpdate(
            documentId=test_doc_id,
            body={"requests": requests}
        ).execute()

        footer_id = None
        for reply in result.get("replies", []):
            if "createFooter" in reply:
                footer_id = reply["createFooter"].get("footerId")

        assert footer_id is not None, "Footer was not created"

        doc = docs.documents().get(documentId=test_doc_id).execute()
        assert "footers" in doc
        assert footer_id in doc["footers"]

    def test_can_set_page_margins(self, google_services, test_doc_id):
        """Should be able to set page margins."""
        docs = google_services["docs"]

        requests = [{
            "updateDocumentStyle": {
                "documentStyle": {
                    "marginTop": {"magnitude": 72, "unit": "PT"},
                    "marginBottom": {"magnitude": 72, "unit": "PT"},
                    "marginLeft": {"magnitude": 90, "unit": "PT"},
                    "marginRight": {"magnitude": 90, "unit": "PT"},
                },
                "fields": "marginTop,marginBottom,marginLeft,marginRight"
            }
        }]

        docs.documents().batchUpdate(
            documentId=test_doc_id,
            body={"requests": requests}
        ).execute()

        # Verify margins
        doc = docs.documents().get(documentId=test_doc_id).execute()
        style = doc.get("documentStyle", {})

        assert style.get("marginTop", {}).get("magnitude") == 72
        assert style.get("marginLeft", {}).get("magnitude") == 90

    def test_header_footer_transform_integration(self, google_services, test_doc_id):
        """HeaderFooterTransform should create valid requests."""
        docs = google_services["docs"]

        # First, check if header already exists
        doc = docs.documents().get(documentId=test_doc_id).execute()
        header_exists = bool(doc.get("headers"))

        if header_exists:
            # Just test page margins if header already exists
            requests = HeaderFooterTransform.create_header_footer_requests(
                header_content=None,
                footer_content=None,
                page_margins={"top": 72, "bottom": 72, "left": 72, "right": 72}
            )
        else:
            header_content = {
                "type": "doc",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Test Header"}]}]
            }
            requests = HeaderFooterTransform.create_header_footer_requests(
                header_content=header_content,
                footer_content=None,
                page_margins={"top": 72, "bottom": 72, "left": 72, "right": 72}
            )

        # Should have at least updateDocumentStyle request
        assert len(requests) >= 1

        result = docs.documents().batchUpdate(
            documentId=test_doc_id,
            body={"requests": requests}
        ).execute()

        # Verify document style was updated
        doc = docs.documents().get(documentId=test_doc_id).execute()
        style = doc.get("documentStyle", {})
        assert style.get("marginTop", {}).get("magnitude") == 72


class TestGoogleSlidesIntegration:
    """Integration tests for Google Slides API."""

    def test_can_read_presentation(self, google_services, test_slides_id):
        """Should be able to read a Google Slides presentation."""
        slides = google_services["slides"]

        presentation = slides.presentations().get(
            presentationId=test_slides_id
        ).execute()

        assert presentation is not None
        assert presentation["presentationId"] == test_slides_id
        assert "slides" in presentation

    def test_can_create_slide(self, google_services, test_slides_id):
        """Should be able to create a new slide."""
        slides = google_services["slides"]

        requests = [{
            "createSlide": {
                "objectId": "test_slide_1",
                "slideLayoutReference": {
                    "predefinedLayout": "TITLE_AND_BODY"
                }
            }
        }]

        result = slides.presentations().batchUpdate(
            presentationId=test_slides_id,
            body={"requests": requests}
        ).execute()

        assert result is not None

        # Verify slide was created
        presentation = slides.presentations().get(
            presentationId=test_slides_id
        ).execute()

        slide_ids = [s["objectId"] for s in presentation.get("slides", [])]
        assert "test_slide_1" in slide_ids


class TestDriveIntegration:
    """Integration tests for Google Drive API.

    Note: These tests require Google Drive API to be enabled in the GCP project.
    They will be skipped if the API is not available.
    """

    def test_can_get_file_metadata(self, google_services, test_doc_id):
        """Should be able to get file metadata."""
        drive = google_services["drive"]

        try:
            file_meta = drive.files().get(
                fileId=test_doc_id,
                fields="id,name,mimeType,headRevisionId"
            ).execute()

            assert file_meta["id"] == test_doc_id
            assert file_meta["mimeType"] == "application/vnd.google-apps.document"
            assert "headRevisionId" in file_meta
        except Exception as e:
            if "accessNotConfigured" in str(e) or "Drive API" in str(e):
                pytest.skip("Google Drive API not enabled in project")
            raise

    def test_can_get_revision_id(self, google_services, test_doc_id):
        """Should be able to get the current revision ID."""
        drive = google_services["drive"]

        try:
            file_meta = drive.files().get(
                fileId=test_doc_id,
                fields="headRevisionId"
            ).execute()

            revision_id = file_meta.get("headRevisionId")
            assert revision_id is not None
            assert len(revision_id) > 0
        except Exception as e:
            if "accessNotConfigured" in str(e) or "Drive API" in str(e):
                pytest.skip("Google Drive API not enabled in project")
            raise
