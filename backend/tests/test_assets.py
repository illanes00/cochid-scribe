"""Tests for assets API."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.assets import safe_asset_path, UPLOAD_DIR


class TestPathTraversalProtection:
    """Tests for path traversal security."""

    def test_valid_uuid_filename_accepted(self):
        """Valid UUID.ext filenames should be accepted."""
        result = safe_asset_path("a1b2c3d4-e5f6-7890-abcd-ef1234567890.png")
        assert result.name == "a1b2c3d4-e5f6-7890-abcd-ef1234567890.png"
        assert result.parent == UPLOAD_DIR.resolve()

    def test_path_traversal_blocked(self):
        """Path traversal attempts should be blocked."""
        with pytest.raises(HTTPException) as exc_info:
            safe_asset_path("../../../etc/passwd")
        assert exc_info.value.status_code == 400
        assert "Invalid asset filename" in exc_info.value.detail

    def test_dotdot_in_filename_blocked(self):
        """Filenames with .. should be blocked."""
        with pytest.raises(HTTPException) as exc_info:
            safe_asset_path("..%2F..%2Fetc%2Fpasswd")
        assert exc_info.value.status_code == 400

    def test_absolute_path_blocked(self):
        """Absolute paths should be blocked."""
        with pytest.raises(HTTPException) as exc_info:
            safe_asset_path("/etc/passwd")
        assert exc_info.value.status_code == 400

    def test_invalid_filename_format_blocked(self):
        """Non-UUID filenames should be blocked."""
        with pytest.raises(HTTPException) as exc_info:
            safe_asset_path("malicious.txt")
        assert exc_info.value.status_code == 400
        assert "Invalid asset filename" in exc_info.value.detail

    def test_null_byte_injection_blocked(self):
        """Null byte injection attempts should be blocked."""
        with pytest.raises(HTTPException) as exc_info:
            safe_asset_path("a1b2c3d4-e5f6-7890-abcd-ef1234567890.png\x00.txt")
        assert exc_info.value.status_code == 400


class TestAssetsAPI:
    """Test asset upload and lifecycle."""

    def test_upload_get_delete_asset(self, client, db_document):
        document_id = db_document["id"]
        response = client.post(
            f"/api/v1/assets/upload?document_id={document_id}",
            files={"file": ("hello.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"]
        assert data["filename"] == "hello.txt"
        assert data["mime_type"] == "text/plain"
        assert data["size_bytes"] == 5
        assert data["url"].startswith("/uploads/assets/")

        asset_id = data["id"]
        url = data["url"]

        get_response = client.get(f"/api/v1/assets/{asset_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == asset_id

        list_response = client.get(f"/api/v1/assets?document_id={document_id}")
        assert list_response.status_code == 200
        assets = list_response.json()
        assert any(asset["id"] == asset_id for asset in assets)

        file_path = Path("uploads") / "assets" / Path(url).name
        assert file_path.exists()

        delete_response = client.delete(f"/api/v1/assets/{asset_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"

        missing_response = client.get(f"/api/v1/assets/{asset_id}")
        assert missing_response.status_code == 404
        assert not file_path.exists()
