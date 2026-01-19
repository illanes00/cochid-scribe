"""Tests for claims API."""


class TestClaimsAPI:
    """Test claims CRUD operations."""

    def test_list_document_claims_empty(self, client, db_document):
        """Test listing claims when empty."""
        response = client.get(f"/api/v1/claims/document/{db_document['slug']}")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_document_claim(self, client, db_document):
        """Test creating a new claim."""
        response = client.post(
            f"/api/v1/claims/document/{db_document['slug']}",
            json={
                "document_slug": db_document["slug"],
                "claim_text": "This is a test claim",
                "claim_type": "HYPOTHESIS",
                "evidence": [],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["claim_text"] == "This is a test claim"
        assert data["claim_type"] == "HYPOTHESIS"
        assert "claim_id" in data

    def test_get_claim(self, client, db_document):
        """Test getting a claim by ID."""
        # Create first
        create_resp = client.post(
            f"/api/v1/claims/document/{db_document['slug']}",
            json={
                "document_slug": db_document["slug"],
                "claim_text": "Get this claim",
                "claim_type": "DATA",
                "evidence": [],
            },
        )
        claim_id = create_resp.json()["claim_id"]

        # Get it
        response = client.get(f"/api/v1/claims/{claim_id}")
        assert response.status_code == 200
        assert response.json()["claim_text"] == "Get this claim"

    def test_get_claim_not_found(self, client):
        """Test getting a non-existent claim."""
        response = client.get("/api/v1/claims/nonexistent-claim-id")
        assert response.status_code == 404

    def test_update_claim(self, client, db_document):
        """Test updating a claim."""
        # Create
        create_resp = client.post(
            f"/api/v1/claims/document/{db_document['slug']}",
            json={
                "document_slug": db_document["slug"],
                "claim_text": "Original claim",
                "claim_type": "HYPOTHESIS",
                "evidence": [],
            },
        )
        claim_id = create_resp.json()["claim_id"]

        # Update
        response = client.put(
            f"/api/v1/claims/{claim_id}",
            json={"claim_text": "Updated claim"},
        )
        assert response.status_code == 200
        assert response.json()["claim_text"] == "Updated claim"

    def test_delete_claim(self, client, db_document):
        """Test deleting a claim."""
        # Create
        create_resp = client.post(
            f"/api/v1/claims/document/{db_document['slug']}",
            json={
                "document_slug": db_document["slug"],
                "claim_text": "To delete",
                "claim_type": "DATA",
                "evidence": [],
            },
        )
        claim_id = create_resp.json()["claim_id"]

        # Delete
        response = client.delete(f"/api/v1/claims/{claim_id}")
        assert response.status_code == 204

        # Verify gone
        response = client.get(f"/api/v1/claims/{claim_id}")
        assert response.status_code == 404

    def test_verify_claim(self, client, db_document):
        """Test verifying a claim."""
        # Create
        create_resp = client.post(
            f"/api/v1/claims/document/{db_document['slug']}",
            json={
                "document_slug": db_document["slug"],
                "claim_text": "To verify",
                "claim_type": "DATA",
                "evidence": [],
            },
        )
        claim_id = create_resp.json()["claim_id"]

        # Verify
        response = client.post(f"/api/v1/claims/{claim_id}/verify")
        assert response.status_code == 200
        assert response.json()["status"] == "verified"
