"""Tests for assets API."""

from pathlib import Path


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
