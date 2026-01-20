"""Tests for Track Changes API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import engine
from app.models import Document
from app.models.track_change import TrackChange, ChangeType, ChangeStatus


client = TestClient(app)


@pytest.fixture
def db_session():
    """Get database session for tests."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_document(db_session):
    """Create a test document."""
    doc = Document(
        title="Track Changes Test Doc",
        slug="track-changes-test",
        doc_type="document",
        content={"json": {"type": "doc", "content": []}},
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    yield doc

    # Cleanup
    db_session.query(TrackChange).filter(TrackChange.document_id == doc.id).delete()
    db_session.query(Document).filter(Document.id == doc.id).delete()
    db_session.commit()


class TestTrackChangesAPI:
    """Test Track Changes API endpoints."""

    def test_list_changes_empty(self, test_document):
        """Should return empty list when no changes exist."""
        response = client.get(f"/api/v1/documents/{test_document.slug}/changes")

        assert response.status_code == 200
        data = response.json()
        assert data["changes"] == []
        assert data["total"] == 0
        assert data["pending_count"] == 0
        assert data["accepted_count"] == 0
        assert data["rejected_count"] == 0

    def test_create_change(self, test_document, db_session):
        """Should create a tracked change."""
        response = client.post(
            f"/api/v1/documents/{test_document.slug}/changes",
            json={
                "change_id": "TC-001",
                "change_type": "insert",
                "content": "Test inserted text",
                "position_start": 0,
                "position_end": 18,
                "author_name": "Test Author",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["change_id"] == "TC-001"
        assert data["change_type"] == "insert"
        assert data["content"] == "Test inserted text"
        assert data["status"] == "pending"
        assert data["author_name"] == "Test Author"

    def test_list_changes_with_data(self, test_document, db_session):
        """Should return changes after creating them."""
        # Create a change
        change = TrackChange(
            document_id=test_document.id,
            change_id="TC-002",
            change_type=ChangeType.INSERT,
            content="Another change",
            status=ChangeStatus.PENDING,
            author_name="Author 2",
        )
        db_session.add(change)
        db_session.commit()

        response = client.get(f"/api/v1/documents/{test_document.slug}/changes")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["pending_count"] >= 1

        # Clean up
        db_session.delete(change)
        db_session.commit()

    def test_get_single_change(self, test_document, db_session):
        """Should get a single change by ID."""
        # Create a change
        change = TrackChange(
            document_id=test_document.id,
            change_id="TC-003",
            change_type=ChangeType.DELETE,
            content="Deleted text",
            status=ChangeStatus.PENDING,
        )
        db_session.add(change)
        db_session.commit()

        response = client.get(f"/api/v1/documents/{test_document.slug}/changes/TC-003")

        assert response.status_code == 200
        data = response.json()
        assert data["change_id"] == "TC-003"
        assert data["change_type"] == "delete"

        # Clean up
        db_session.delete(change)
        db_session.commit()

    def test_resolve_change_accept(self, test_document, db_session):
        """Should accept a pending change."""
        # Create a change
        change = TrackChange(
            document_id=test_document.id,
            change_id="TC-004",
            change_type=ChangeType.INSERT,
            content="To be accepted",
            status=ChangeStatus.PENDING,
        )
        db_session.add(change)
        db_session.commit()

        response = client.post(
            f"/api/v1/documents/{test_document.slug}/changes/TC-004/resolve",
            json={"action": "accept", "resolved_by": "Resolver"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["change"]["status"] == "accepted"
        assert data["change"]["resolved_by"] == "Resolver"

        # Verify in DB
        db_session.refresh(change)
        assert change.status == ChangeStatus.ACCEPTED

        # Clean up
        db_session.delete(change)
        db_session.commit()

    def test_resolve_change_reject(self, test_document, db_session):
        """Should reject a pending change."""
        # Create a change
        change = TrackChange(
            document_id=test_document.id,
            change_id="TC-005",
            change_type=ChangeType.DELETE,
            content="To be rejected",
            status=ChangeStatus.PENDING,
        )
        db_session.add(change)
        db_session.commit()

        response = client.post(
            f"/api/v1/documents/{test_document.slug}/changes/TC-005/resolve",
            json={"action": "reject", "resolved_by": "Reviewer"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["change"]["status"] == "rejected"

        # Verify in DB
        db_session.refresh(change)
        assert change.status == ChangeStatus.REJECTED

        # Clean up
        db_session.delete(change)
        db_session.commit()

    def test_accept_all_changes(self, test_document, db_session):
        """Should accept all pending changes."""
        # Create multiple pending changes
        changes = []
        for i in range(3):
            change = TrackChange(
                document_id=test_document.id,
                change_id=f"TC-BULK-{i}",
                change_type=ChangeType.INSERT,
                content=f"Bulk change {i}",
                status=ChangeStatus.PENDING,
            )
            db_session.add(change)
            changes.append(change)
        db_session.commit()

        response = client.post(
            f"/api/v1/documents/{test_document.slug}/changes/accept-all",
            json={"resolved_by": "Bulk Accepter"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["resolved_count"] >= 3

        # Verify all are accepted
        for change in changes:
            db_session.refresh(change)
            assert change.status == ChangeStatus.ACCEPTED

        # Clean up
        for change in changes:
            db_session.delete(change)
        db_session.commit()

    def test_reject_all_changes(self, test_document, db_session):
        """Should reject all pending changes."""
        # Create multiple pending changes
        changes = []
        for i in range(2):
            change = TrackChange(
                document_id=test_document.id,
                change_id=f"TC-REJ-{i}",
                change_type=ChangeType.DELETE,
                content=f"Reject change {i}",
                status=ChangeStatus.PENDING,
            )
            db_session.add(change)
            changes.append(change)
        db_session.commit()

        response = client.post(
            f"/api/v1/documents/{test_document.slug}/changes/reject-all",
            json={"resolved_by": "Bulk Rejecter"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["resolved_count"] >= 2

        # Verify all are rejected
        for change in changes:
            db_session.refresh(change)
            assert change.status == ChangeStatus.REJECTED

        # Clean up
        for change in changes:
            db_session.delete(change)
        db_session.commit()

    def test_delete_change(self, test_document, db_session):
        """Should delete a tracked change."""
        # Create a change
        change = TrackChange(
            document_id=test_document.id,
            change_id="TC-DEL",
            change_type=ChangeType.INSERT,
            content="To be deleted",
            status=ChangeStatus.REJECTED,
        )
        db_session.add(change)
        db_session.commit()

        response = client.delete(f"/api/v1/documents/{test_document.slug}/changes/TC-DEL")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted from DB
        deleted_change = db_session.query(TrackChange).filter(
            TrackChange.change_id == "TC-DEL"
        ).first()
        assert deleted_change is None

    def test_filter_changes_by_status(self, test_document, db_session):
        """Should filter changes by status."""
        # Create changes with different statuses
        pending = TrackChange(
            document_id=test_document.id,
            change_id="TC-FILTER-P",
            change_type=ChangeType.INSERT,
            content="Pending",
            status=ChangeStatus.PENDING,
        )
        accepted = TrackChange(
            document_id=test_document.id,
            change_id="TC-FILTER-A",
            change_type=ChangeType.INSERT,
            content="Accepted",
            status=ChangeStatus.ACCEPTED,
        )
        db_session.add_all([pending, accepted])
        db_session.commit()

        # Filter by pending
        response = client.get(f"/api/v1/documents/{test_document.slug}/changes?status=pending")
        assert response.status_code == 200
        data = response.json()
        change_ids = [c["change_id"] for c in data["changes"]]
        assert "TC-FILTER-P" in change_ids
        assert "TC-FILTER-A" not in change_ids

        # Filter by accepted
        response = client.get(f"/api/v1/documents/{test_document.slug}/changes?status=accepted")
        assert response.status_code == 200
        data = response.json()
        change_ids = [c["change_id"] for c in data["changes"]]
        assert "TC-FILTER-A" in change_ids
        assert "TC-FILTER-P" not in change_ids

        # Clean up
        db_session.delete(pending)
        db_session.delete(accepted)
        db_session.commit()

    def test_change_not_found(self, test_document):
        """Should return 404 for non-existent change."""
        response = client.get(f"/api/v1/documents/{test_document.slug}/changes/NONEXISTENT")

        assert response.status_code == 404

    def test_document_not_found(self):
        """Should return 404 for non-existent document."""
        response = client.get("/api/v1/documents/nonexistent-doc/changes")

        assert response.status_code == 404
