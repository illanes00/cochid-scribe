"""Tests for bibliography API."""


class TestBibliographyAPI:
    """Test bibliography CRUD operations."""

    def test_list_bibliography_empty(self, client):
        """Test listing bibliography when empty."""
        response = client.get("/api/v1/bibliography")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_bibliography_entry(self, client):
        """Test creating a new bibliography entry."""
        response = client.post(
            "/api/v1/bibliography",
            json={
                "bib_key": "smith2024",
                "entry_type": "article",
                "title": "Test Article",
                "author": "Smith, John",
                "year": 2024,
                "journal": "Test Journal",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["bib_key"] == "smith2024"
        assert data["title"] == "Test Article"

    def test_create_duplicate_key_fails(self, client):
        """Test that creating duplicate bib_key fails."""
        # Create first
        client.post(
            "/api/v1/bibliography",
            json={
                "bib_key": "duplicate2024",
                "entry_type": "book",
                "title": "First Book",
                "author": "Author, First",
            },
        )

        # Try duplicate
        response = client.post(
            "/api/v1/bibliography",
            json={
                "bib_key": "duplicate2024",
                "entry_type": "book",
                "title": "Second Book",
                "author": "Author, Second",
            },
        )
        assert response.status_code == 409

    def test_get_bibliography_entry(self, client):
        """Test getting a bibliography entry by key."""
        # Create first
        client.post(
            "/api/v1/bibliography",
            json={
                "bib_key": "get2024",
                "entry_type": "article",
                "title": "Get This Article",
                "author": "Get, Author",
            },
        )

        # Get it
        response = client.get("/api/v1/bibliography/get2024")
        assert response.status_code == 200
        assert response.json()["title"] == "Get This Article"

    def test_get_bibliography_not_found(self, client):
        """Test getting a non-existent entry."""
        response = client.get("/api/v1/bibliography/nonexistent2024")
        assert response.status_code == 404

    def test_delete_bibliography_entry(self, client):
        """Test deleting a bibliography entry."""
        # Create
        client.post(
            "/api/v1/bibliography",
            json={
                "bib_key": "delete2024",
                "entry_type": "book",
                "title": "To Delete",
                "author": "Delete, Me",
            },
        )

        # Delete
        response = client.delete("/api/v1/bibliography/delete2024")
        assert response.status_code == 204

        # Verify gone
        response = client.get("/api/v1/bibliography/delete2024")
        assert response.status_code == 404

    def test_search_bibliography(self, client):
        """Test searching bibliography entries."""
        # Create entries
        client.post(
            "/api/v1/bibliography",
            json={
                "bib_key": "python2024",
                "entry_type": "article",
                "title": "Python Machine Learning",
                "author": "Python, Expert",
            },
        )
        client.post(
            "/api/v1/bibliography",
            json={
                "bib_key": "java2024",
                "entry_type": "book",
                "title": "Java Programming",
                "author": "Java, Master",
            },
        )

        # Search
        response = client.get("/api/v1/bibliography/search?q=Python")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["title"] == "Python Machine Learning"
