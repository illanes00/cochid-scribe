"""Tests for Google integration endpoints."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.integration import Integration
from app.services.google import get_google_credentials


class TestTokenRefresh:
    """Tests for Google token refresh persistence."""

    def test_token_refresh_persists_to_database(self, db):
        """Verify that refreshed tokens are committed to the database."""
        # Create an expired integration
        expired_time = datetime.utcnow() - timedelta(hours=1)
        integration = Integration(
            provider="google",
            access_token="old_token",
            refresh_token="valid_refresh",
            expires_at=expired_time,
        )
        db.add(integration)
        db.commit()

        with patch("app.services.google.Credentials") as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.expired = True
            mock_creds.refresh_token = "valid_refresh"
            mock_creds.token = "new_token"
            mock_creds.expiry = datetime.utcnow() + timedelta(hours=1)
            mock_creds_class.return_value = mock_creds

            with patch("app.services.google.Request"):
                result = get_google_credentials(db)

        # Verify token was refreshed and persisted
        db.refresh(integration)
        assert integration.access_token == "new_token"

    def test_token_refresh_failure_returns_none(self, db):
        """Verify that failed token refresh returns None for re-auth."""
        expired_time = datetime.utcnow() - timedelta(hours=1)
        integration = Integration(
            provider="google",
            access_token="old_token",
            refresh_token="invalid_refresh",
            expires_at=expired_time,
        )
        db.add(integration)
        db.commit()

        with patch("app.services.google.Credentials") as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.expired = True
            mock_creds.refresh_token = "invalid_refresh"
            mock_creds.refresh.side_effect = Exception("Token refresh failed")
            mock_creds_class.return_value = mock_creds

            with patch("app.services.google.Request"):
                result = get_google_credentials(db)

        assert result is None


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
