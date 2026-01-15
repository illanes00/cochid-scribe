"""Tests for documents API."""



class TestDocumentsAPI:
    """Test document CRUD operations."""

    def test_list_documents_empty(self, client):
        """Test listing documents when empty."""
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    def test_create_document(self, client):
        """Test creating a new document."""
        response = client.post(
            "/api/v1/documents",
            json={
                "title": "Test Paper",
                "doc_type": "paper",
                "content": {},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Paper"
        assert data["slug"] == "test-paper"
        assert data["doc_type"] == "paper"

    def test_get_document(self, client):
        """Test getting a document by slug."""
        # Create first
        client.post(
            "/api/v1/documents",
            json={"title": "My Document", "doc_type": "paper"},
        )

        # Get it
        response = client.get("/api/v1/documents/my-document")
        assert response.status_code == 200
        assert response.json()["title"] == "My Document"

    def test_get_document_not_found(self, client):
        """Test getting a non-existent document."""
        response = client.get("/api/v1/documents/nonexistent")
        assert response.status_code == 404

    def test_update_document(self, client):
        """Test updating a document."""
        # Create
        client.post(
            "/api/v1/documents",
            json={"title": "Original Title", "doc_type": "paper"},
        )

        # Update
        response = client.put(
            "/api/v1/documents/original-title",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_delete_document(self, client):
        """Test deleting a document."""
        # Create
        client.post(
            "/api/v1/documents",
            json={"title": "To Delete", "doc_type": "paper"},
        )

        # Delete
        response = client.delete("/api/v1/documents/to-delete")
        assert response.status_code == 204

        # Verify gone
        response = client.get("/api/v1/documents/to-delete")
        assert response.status_code == 404
