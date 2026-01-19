"""Tests for notes API (Knowledge Base)."""


class TestNotesAPI:
    """Test notes CRUD operations."""

    def test_list_notes_empty(self, client):
        """Test listing notes when empty."""
        response = client.get("/api/v1/notes")
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == []
        assert data["total"] == 0

    def test_create_note(self, client):
        """Test creating a new note."""
        response = client.post(
            "/api/v1/notes",
            json={
                "title": "Test Note",
                "content": {"type": "doc", "content": []},
                "markdown": "# Test Note",
                "note_type": "idea",
                "tags": ["test"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Note"
        assert data["note_type"] == "idea"
        assert "slug" in data

    def test_get_note(self, client):
        """Test getting a note by slug."""
        # Create first
        create_resp = client.post(
            "/api/v1/notes",
            json={
                "title": "Get This Note",
                "content": {},
                "markdown": "",
                "note_type": "question",
            },
        )
        slug = create_resp.json()["slug"]

        # Get it
        response = client.get(f"/api/v1/notes/{slug}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get This Note"

    def test_get_note_not_found(self, client):
        """Test getting a non-existent note."""
        response = client.get("/api/v1/notes/nonexistent-note")
        assert response.status_code == 404

    def test_update_note(self, client):
        """Test updating a note."""
        # Create
        create_resp = client.post(
            "/api/v1/notes",
            json={
                "title": "Original Note",
                "content": {},
                "markdown": "",
                "note_type": "idea",
            },
        )
        slug = create_resp.json()["slug"]

        # Update
        response = client.put(
            f"/api/v1/notes/{slug}",
            json={"title": "Updated Note"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Note"

    def test_delete_note(self, client):
        """Test deleting a note."""
        # Create
        create_resp = client.post(
            "/api/v1/notes",
            json={
                "title": "To Delete",
                "content": {},
                "markdown": "",
                "note_type": "idea",
            },
        )
        slug = create_resp.json()["slug"]

        # Delete
        response = client.delete(f"/api/v1/notes/{slug}")
        assert response.status_code == 204

        # Verify gone
        response = client.get(f"/api/v1/notes/{slug}")
        assert response.status_code == 404

    def test_search_notes(self, client):
        """Test searching notes."""
        # Create notes
        client.post(
            "/api/v1/notes",
            json={
                "title": "Python Guide",
                "content": {},
                "markdown": "Python programming tips",
                "note_type": "reference",
            },
        )
        client.post(
            "/api/v1/notes",
            json={
                "title": "JavaScript Tips",
                "content": {},
                "markdown": "JS best practices",
                "note_type": "reference",
            },
        )

        # Search
        response = client.get("/api/v1/notes?search=Python")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["notes"][0]["title"] == "Python Guide"
