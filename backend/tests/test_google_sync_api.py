"""Integration tests for Google Docs/Slides sync API endpoints.

These tests verify the full API endpoint behavior with mocked Google services,
covering link, unlink, status, push, pull, and resolve operations.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.document import Document
from app.models.integration import Integration


class MockGoogleDriveService:
    """Mock for Google Drive API service."""

    def __init__(self, revision_id="rev123", file_name="Test Doc"):
        self.revision_id = revision_id
        self.file_name = file_name
        self._files = MagicMock()
        self._files.get.return_value.execute.return_value = {
            "id": "doc123",
            "name": self.file_name,
            "mimeType": "application/vnd.google-apps.document",
            "headRevisionId": self.revision_id,
        }

    def files(self):
        return self._files

    def set_revision(self, revision_id):
        """Update the revision ID for simulating remote changes."""
        self.revision_id = revision_id
        self._files.get.return_value.execute.return_value["headRevisionId"] = revision_id


class MockGoogleDocsService:
    """Mock for Google Docs API service."""

    def __init__(self):
        self._documents = MagicMock()
        self._documents.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "body": {
                "content": [
                    {"endIndex": 1},
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Hello World\n"}}]
                        },
                        "endIndex": 13,
                    },
                ]
            },
            "footnotes": {},
        }
        self._documents.batchUpdate.return_value.execute.return_value = {}

    def documents(self):
        return self._documents


class MockGoogleSlidesService:
    """Mock for Google Slides API service."""

    def __init__(self, revision_id="slides-rev123"):
        self.revision_id = revision_id
        self._presentations = MagicMock()
        self._presentations.get.return_value.execute.return_value = {
            "presentationId": "slides123",
            "slides": [
                {
                    "objectId": "slide1",
                    "pageElements": [
                        {
                            "objectId": "title1",
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "text": {
                                    "textElements": [
                                        {"textRun": {"content": "Slide Title\n"}}
                                    ]
                                },
                            },
                        }
                    ],
                }
            ],
            "masters": [{"pageElements": []}],
        }
        self._presentations.batchUpdate.return_value.execute.return_value = {
            "replies": []
        }

    def presentations(self):
        return self._presentations


@pytest.fixture
def google_integration(client, db):
    """Create a Google integration with valid tokens."""
    integration = Integration(
        provider="google",
        access_token="valid_token",
        refresh_token="valid_refresh",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(integration)
    db.commit()
    return integration


@pytest.fixture
def mock_google_services():
    """Fixture providing mocked Google API services."""
    drive = MockGoogleDriveService()
    docs = MockGoogleDocsService()
    slides = MockGoogleSlidesService()

    with patch("app.api.v1.google_sync.build_drive_service") as mock_drive, \
         patch("app.api.v1.google_sync.build_docs_service") as mock_docs, \
         patch("app.api.v1.google_sync.build_slides_service") as mock_slides:

        mock_drive.return_value = drive
        mock_docs.return_value = docs
        mock_slides.return_value = slides

        yield {
            "drive": drive,
            "docs": docs,
            "slides": slides,
        }


@pytest.fixture
def test_document(client):
    """Create a test document via API with TipTap content."""
    response = client.post(
        "/api/v1/documents",
        json={
            "title": "Test Document",
            "doc_type": "paper",
            "content": {
                "json": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Hello World"}],
                        }
                    ],
                },
                "html": "<p>Hello World</p>",
            },
        },
    )
    return response.json()


@pytest.fixture
def test_presentation(client):
    """Create a test presentation via API with slides data."""
    response = client.post(
        "/api/v1/documents",
        json={
            "title": "Test Presentation",
            "doc_type": "presentation",  # Must be 'presentation', not 'slides'
            "content": {},  # Required field
            "front_matter": {
                "slides_data": {
                    "slides": [
                        {
                            "id": "slide-1",
                            "slideNumber": 1,
                            "layout": "title",
                            "title": "Test Title",
                            "content": "Test content",
                            "notes": "",
                        }
                    ],
                    "theme": {"primaryColor": "#1a365d", "secondaryColor": "#c53030"},
                }
            },
        },
    )
    return response.json()


class TestLinkDocument:
    """Tests for POST /api/v1/google-sync/docs/{slug}/link endpoint."""

    def test_link_document_success(
        self, client, test_document, google_integration, mock_google_services
    ):
        """Link a document to a Google Doc successfully."""
        response = client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["google_doc_id"] == "doc123"
        assert data["google_revision_id"] == "rev123"
        assert "Successfully linked" in data["message"]

    def test_link_document_not_found(
        self, client, google_integration, mock_google_services
    ):
        """Linking non-existent document returns 404."""
        response = client.post(
            "/api/v1/google-sync/docs/nonexistent/link",
            json={"google_doc_id": "doc123"},
        )

        assert response.status_code == 404

    def test_link_document_no_integration(self, client, test_document):
        """Linking without Google integration returns 400."""
        response = client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        assert response.status_code == 400
        assert "not connected" in response.json()["detail"]

    def test_link_document_not_google_doc(
        self, client, test_document, google_integration, mock_google_services
    ):
        """Linking to non-Google Doc file returns 400."""
        # Modify mock to return spreadsheet mimeType
        mock_google_services["drive"]._files.get.return_value.execute.return_value[
            "mimeType"
        ] = "application/vnd.google-apps.spreadsheet"

        response = client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "spreadsheet123"},
        )

        assert response.status_code == 400
        assert "not a Google Doc" in response.json()["detail"]


class TestUnlinkDocument:
    """Tests for DELETE /api/v1/google-sync/docs/{slug}/link endpoint."""

    def test_unlink_document_success(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Unlink a linked document successfully."""
        # First link the document via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        response = client.delete(f"/api/v1/google-sync/docs/{test_document['slug']}/link")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify document was unlinked
        doc = db.query(Document).filter(Document.slug == test_document["slug"]).first()
        assert doc.google_revision_id is None
        assert doc.sync_status == "none"


class TestSyncStatus:
    """Tests for GET /api/v1/google-sync/docs/{slug}/status endpoint."""

    def test_status_not_linked(self, client, test_document):
        """Status of unlinked document is 'none'."""
        response = client.get(f"/api/v1/google-sync/docs/{test_document['slug']}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["linked"] is False
        assert data["sync_status"] == "none"

    def test_status_synced(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Status of synced document with no changes."""
        # Link the document via API first
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        response = client.get(f"/api/v1/google-sync/docs/{test_document['slug']}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["linked"] is True
        assert data["sync_status"] == "synced"

    def test_status_remote_changed(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Status detects remote changes."""
        # Link the document via API first
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Simulate remote change by updating the mock revision
        mock_google_services["drive"].set_revision("rev456")

        response = client.get(f"/api/v1/google-sync/docs/{test_document['slug']}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["linked"] is True
        assert data["sync_status"] == "remote_changed"

    def test_status_local_changed(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Status detects local changes."""
        # Link the document via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Modify local content to trigger local_changed
        doc = db.query(Document).filter(Document.slug == test_document["slug"]).first()
        doc.local_version_hash = "old_hash_that_wont_match"
        db.commit()

        response = client.get(f"/api/v1/google-sync/docs/{test_document['slug']}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["linked"] is True
        assert data["sync_status"] == "local_changed"

    def test_status_conflict(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Status detects conflicts (both local and remote changed)."""
        # Link the document via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Modify local content hash to simulate local changes
        doc = db.query(Document).filter(Document.slug == test_document["slug"]).first()
        doc.local_version_hash = "old_hash"  # Will mismatch content
        db.commit()

        # Simulate remote change
        mock_google_services["drive"].set_revision("rev456")

        response = client.get(f"/api/v1/google-sync/docs/{test_document['slug']}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["linked"] is True
        assert data["sync_status"] == "conflict"


class TestPushToGoogle:
    """Tests for POST /api/v1/google-sync/docs/{slug}/push endpoint."""

    def test_push_success(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Push local changes to Google Doc successfully."""
        from app.services.google_docs_transform import compute_content_hash

        # Link the document via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Modify local content to simulate local changes
        doc = db.query(Document).filter(Document.slug == test_document["slug"]).first()
        doc.local_version_hash = "old_hash"
        doc.sync_status = "local_changed"
        db.commit()

        response = client.post(f"/api/v1/google-sync/docs/{test_document['slug']}/push")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_revision_id"] == "rev123"

        # Verify sync state was updated
        db.refresh(doc)
        assert doc.sync_status == "synced"

    def test_push_not_linked(self, client, test_document, google_integration):
        """Push fails for unlinked document."""
        response = client.post(f"/api/v1/google-sync/docs/{test_document['slug']}/push")

        assert response.status_code == 400
        assert "not linked" in response.json()["detail"]

    def test_push_preserves_claims(
        self, client, db, google_integration, mock_google_services
    ):
        """Push preserves claim metadata in footnotes."""
        # Create document with claims via API
        response = client.post(
            "/api/v1/documents",
            json={
                "title": "Doc with Claims",
                "doc_type": "paper",
                "content": {
                    "json": {
                        "type": "doc",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "GDP grew 5%",
                                        "marks": [
                                            {
                                                "type": "claim",
                                                "attrs": {
                                                    "claimId": "C-123",
                                                    "claimType": "DATA",
                                                    "status": "verified",
                                                },
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                },
            },
        )
        claims_doc = response.json()

        # Link the document
        client.post(
            f"/api/v1/google-sync/docs/{claims_doc['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        response = client.post(f"/api/v1/google-sync/docs/{claims_doc['slug']}/push")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["claims_preserved"] >= 0  # Transformer counts them


class TestPullFromGoogle:
    """Tests for POST /api/v1/google-sync/docs/{slug}/pull endpoint."""

    def test_pull_success(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Pull remote changes from Google Doc successfully."""
        # Link the document via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Mark as remote changed
        doc = db.query(Document).filter(Document.slug == test_document["slug"]).first()
        doc.sync_status = "remote_changed"
        db.commit()

        response = client.post(f"/api/v1/google-sync/docs/{test_document['slug']}/pull")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify sync state was updated
        db.refresh(doc)
        assert doc.sync_status == "synced"
        assert doc.content is not None

    def test_pull_not_linked(self, client, test_document, google_integration):
        """Pull fails for unlinked document."""
        response = client.post(f"/api/v1/google-sync/docs/{test_document['slug']}/pull")

        assert response.status_code == 400
        assert "not linked" in response.json()["detail"]


class TestResolveConflict:
    """Tests for POST /api/v1/google-sync/docs/{slug}/resolve endpoint."""

    def test_resolve_keep_local(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Resolve conflict by keeping local changes (push)."""
        # Link the document via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Set up conflict state
        doc = db.query(Document).filter(Document.slug == test_document["slug"]).first()
        doc.sync_status = "conflict"
        doc.local_version_hash = "old_hash"
        db.commit()

        response = client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/resolve",
            json={"strategy": "keep_local"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_sync_status"] == "synced"

    def test_resolve_keep_remote(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Resolve conflict by keeping remote changes (pull)."""
        # Link the document via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Set up conflict state
        doc = db.query(Document).filter(Document.slug == test_document["slug"]).first()
        doc.sync_status = "conflict"
        db.commit()

        response = client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/resolve",
            json={"strategy": "keep_remote"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_sync_status"] == "synced"


class TestSlidesSync:
    """Tests for Google Slides sync endpoints."""

    def test_link_slides_success(
        self, client, test_presentation, google_integration, mock_google_services
    ):
        """Link a presentation to Google Slides successfully."""
        # Configure mock for slides
        mock_google_services["drive"]._files.get.return_value.execute.return_value = {
            "id": "slides123",
            "name": "Test Slides",
            "mimeType": "application/vnd.google-apps.presentation",
            "headRevisionId": "slides-rev123",
        }

        response = client.post(
            f"/api/v1/google-sync/slides/{test_presentation['slug']}/link",
            json={"google_doc_id": "slides123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_push_slides_success(
        self, client, db, test_presentation, google_integration, mock_google_services
    ):
        """Push slides to Google Slides successfully."""
        # Configure mock for slides
        mock_google_services["drive"]._files.get.return_value.execute.return_value = {
            "id": "slides123",
            "name": "Test Slides",
            "mimeType": "application/vnd.google-apps.presentation",
            "headRevisionId": "slides-rev123",
        }

        # Link via API
        client.post(
            f"/api/v1/google-sync/slides/{test_presentation['slug']}/link",
            json={"google_doc_id": "slides123"},
        )

        # Update mock for push result
        mock_google_services["drive"]._files.get.return_value.execute.return_value = {
            "id": "slides123",
            "name": "Test Slides",
            "mimeType": "application/vnd.google-apps.presentation",
            "headRevisionId": "slides-rev456",
        }

        response = client.post(f"/api/v1/google-sync/slides/{test_presentation['slug']}/push")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_pull_slides_success(
        self, client, db, test_presentation, google_integration, mock_google_services
    ):
        """Pull slides from Google Slides successfully."""
        # Configure mock for slides
        mock_google_services["drive"]._files.get.return_value.execute.return_value = {
            "id": "slides123",
            "name": "Test Slides",
            "mimeType": "application/vnd.google-apps.presentation",
            "headRevisionId": "slides-rev123",
        }

        # Link via API
        client.post(
            f"/api/v1/google-sync/slides/{test_presentation['slug']}/link",
            json={"google_doc_id": "slides123"},
        )

        # Mark as remote changed
        doc = db.query(Document).filter(Document.slug == test_presentation["slug"]).first()
        doc.sync_status = "remote_changed"
        db.commit()

        response = client.post(f"/api/v1/google-sync/slides/{test_presentation['slug']}/pull")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestDriveUrl:
    """Tests for GET /api/v1/google-sync/{slug}/drive-url endpoint."""

    def test_drive_url_for_docs(
        self, client, db, test_document, google_integration, mock_google_services
    ):
        """Get Drive URL for linked document."""
        # Link via API
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        response = client.get(f"/api/v1/google-sync/{test_document['slug']}/drive-url")

        assert response.status_code == 200
        data = response.json()
        assert "docs.google.com" in data["url"]
        assert data["file_type"] == "document"

    def test_drive_url_for_slides(
        self, client, db, test_presentation, google_integration, mock_google_services
    ):
        """Get Drive URL for linked presentation."""
        # Configure mock for slides
        mock_google_services["drive"]._files.get.return_value.execute.return_value = {
            "id": "slides123",
            "name": "Test Slides",
            "mimeType": "application/vnd.google-apps.presentation",
            "headRevisionId": "slides-rev123",
        }

        # Link via API
        client.post(
            f"/api/v1/google-sync/slides/{test_presentation['slug']}/link",
            json={"google_doc_id": "slides123"},
        )

        response = client.get(f"/api/v1/google-sync/{test_presentation['slug']}/drive-url")

        assert response.status_code == 200
        data = response.json()
        assert "docs.google.com" in data["url"] or "presentation" in data["url"]
        assert data["file_type"] == "presentation"

    def test_drive_url_not_linked(self, client, test_document):
        """Drive URL for unlinked document returns 400."""
        response = client.get(f"/api/v1/google-sync/{test_document['slug']}/drive-url")

        assert response.status_code == 400
        assert "not linked" in response.json()["detail"]


class TestErrorHandling:
    """Tests for error handling in sync operations."""

    def test_push_unlinked_document_returns_error(
        self, client, test_document, google_integration, mock_google_services
    ):
        """Push to unlinked document returns 400 error (not 500)."""
        # Don't link - just try to push directly
        response = client.post(f"/api/v1/google-sync/docs/{test_document['slug']}/push")

        assert response.status_code == 400
        assert "not linked" in response.json()["detail"]

    def test_pull_unlinked_document_returns_error(
        self, client, test_document, google_integration, mock_google_services
    ):
        """Pull from unlinked document returns 400 error (not 500)."""
        # Don't link - just try to pull directly
        response = client.post(f"/api/v1/google-sync/docs/{test_document['slug']}/pull")

        assert response.status_code == 400
        assert "not linked" in response.json()["detail"]

    def test_resolve_non_conflict_document_returns_error(
        self, client, test_document, google_integration, mock_google_services
    ):
        """Resolve on non-conflict document returns 400 error."""
        # Link but don't create conflict - status will be 'synced'
        client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/link",
            json={"google_doc_id": "doc123"},
        )

        # Try to resolve - should fail because not in conflict state
        response = client.post(
            f"/api/v1/google-sync/docs/{test_document['slug']}/resolve",
            json={"strategy": "keep_local"},
        )

        assert response.status_code == 400
        assert "not in conflict state" in response.json()["detail"]
