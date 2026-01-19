"""Tests for Google integration endpoints."""


class TestGoogleIntegration:
    """Ensure endpoints guard against missing integration."""

    def test_google_docs_import_requires_integration(self, client):
        response = client.post(
            "/api/v1/google/docs/import",
            json={"file_id": "test-file"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Google integration not connected"

    def test_google_docs_export_requires_integration(self, client):
        response = client.post(
            "/api/v1/google/docs/export",
            json={"slug": "missing-doc"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Google integration not connected"

    def test_google_slides_import_requires_integration(self, client):
        response = client.post(
            "/api/v1/google/slides/import",
            json={"file_id": "test-file"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Google integration not connected"

    def test_google_slides_export_requires_integration(self, client):
        response = client.post(
            "/api/v1/google/slides/export",
            json={"slug": "missing-slides"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Google integration not connected"
