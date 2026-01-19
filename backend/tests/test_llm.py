"""Tests for LLM endpoints (mocked)."""

from unittest.mock import MagicMock, patch

import app.api.v1.llm as llm_module


class TestLlmRewrite:
    """Tests for /api/v1/llm/rewrite."""

    def test_rewrite_returns_503_without_key(self, client, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "anthropic_api_key", "")
        response = client.post(
            "/api/v1/llm/rewrite",
            json={"text": "Hello", "instruction": "Rewrite", "tone": "academic"},
        )
        assert response.status_code == 503

    def test_rewrite_success(self, client, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "anthropic_api_key", "test-key")

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Rewritten text")]
        mock_client.messages.create.return_value = mock_message

        with patch("anthropic.Anthropic", return_value=mock_client):
            response = client.post(
                "/api/v1/llm/rewrite",
                json={"text": "Hello", "instruction": "Rewrite", "tone": "academic"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "Hello"
        assert data["rewritten"] == "Rewritten text"


class TestLlmExtractClaims:
    """Tests for /api/v1/llm/extract-claims and document extraction."""

    def test_extract_claims_success(self, client, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "anthropic_api_key", "test-key")

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(
                text='[{"claim_text":"El gasto aumentó 23%","claim_type":"DATA","evidence_needed":"BID"}]'
            )
        ]
        mock_client.messages.create.return_value = mock_message

        with patch("anthropic.Anthropic", return_value=mock_client):
            response = client.post("/api/v1/llm/extract-claims", json={"text": "X"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["claims"]) == 1
        assert data["claims"][0]["claim_type"] == "DATA"

    def test_extract_claims_document_dedupes(self, client, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "anthropic_api_key", "test-key")

        create_doc = client.post(
            "/api/v1/documents",
            json={
                "title": "Doc",
                "doc_type": "paper",
                "markdown": "El gasto aumentó 23% en 2024.",
                "content": {},
            },
        )
        assert create_doc.status_code == 201
        slug = create_doc.json()["slug"]

        claims = [
            {"claim_text": "El gasto aumentó 23%", "claim_type": "DATA", "evidence_needed": "BID"}
        ]
        with patch.object(llm_module, "extract_claims_from_text", return_value=claims):
            first = client.post(f"/api/v1/llm/extract-claims-document/{slug}")
            assert first.status_code == 200
            assert first.json()["created"] == 1

            second = client.post(f"/api/v1/llm/extract-claims-document/{slug}")
            assert second.status_code == 200
            assert second.json()["created"] == 0
