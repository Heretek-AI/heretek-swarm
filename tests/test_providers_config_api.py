"""Tests for /api/v1/providers endpoints — LLM and embedding provider CRUD.

Tests against the FastAPI TestClient with temp config.json isolation
(via HEREKET_CONFIG_PATH env var).  All persistence goes through the
config.json file — zero Postgres.

Covers:
* List LLM providers
* Create LLM provider returns created shape
* Update LLM provider changes persist
* Delete LLM provider removes
* Test LLM provider endpoint returns connectivity result
* Embedding list / add / delete
* 404 for unknown provider update / delete / test
* Rate limit header is present on responses
* Negative: invalid provider type, empty name, missing base URL, bad ID
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from heretek_swarm.llm.model_garage import (
    ModelGarage,
    _model_garage,
)

from heretek_swarm.api.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_providers_config(path: Path, llm: list[dict] | None = None, emb: list[dict] | None = None) -> None:
    """Write a valid config.json with optional llm and embedding providers."""
    data: dict = {"version": "1.0.0"}
    if llm is not None:
        data["modelProviders"] = llm
    if emb is not None:
        data["embeddingProviders"] = emb
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


@pytest.fixture(autouse=True)
def _reset_global_garage() -> None:
    """Reset the global ModelGarage singleton between tests."""
    ModelGarage._model_garage = None
    import heretek_swarm.llm.model_garage as mg
    mg._model_garage = None


@pytest.fixture
def client_with_config(tmp_path: Path):
    """FastAPI TestClient with temp config.json."""
    config_file = tmp_path / ".heretek-swarm" / "config.json"
    _seed_providers_config(config_file)
    with patch.dict(os.environ, {"HEREKET_CONFIG_PATH": str(config_file)}):
        # Create a fresh garage pointing at the temp file
        fresh = ModelGarage(config_file=config_file)
        import heretek_swarm.llm.model_garage as mg
        mg._model_garage = fresh
        yield TestClient(app)


# ---------------------------------------------------------------------------
# Tests: LLM Provider List
# ---------------------------------------------------------------------------


class TestListLLMProviders:
    """``GET /api/v1/providers/llm``"""

    def test_empty_list_returns_empty_array(self, client_with_config: TestClient) -> None:
        resp = client_with_config.get("/api/v1/providers/llm")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert data["providers"] == []

    def test_rate_limit_header_present(self, client_with_config: TestClient) -> None:
        resp = client_with_config.get("/api/v1/providers/llm")
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers

    def test_list_includes_configured_provider(self, client_with_config: TestClient, tmp_path: Path) -> None:
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_providers_config(config_file, llm=[{
            "id": "ollama-1",
            "type": "ollama",
            "name": "Local Ollama",
            "baseUrl": "http://localhost:11434",
            "defaultModel": "llama3.1",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])
        fresh = ModelGarage(config_file=config_file)
        import heretek_swarm.llm.model_garage as mg
        mg._model_garage = fresh

        resp = client_with_config.get("/api/v1/providers/llm")
        assert resp.status_code == 200
        providers = resp.json()["providers"]
        assert len(providers) == 1
        assert providers[0]["id"] == "ollama-1"


# ---------------------------------------------------------------------------
# Tests: LLM Provider Create
# ---------------------------------------------------------------------------


class TestCreateLLMProvider:
    """``POST /api/v1/providers/llm``"""

    def test_create_returns_created_shape(self, client_with_config: TestClient) -> None:
        body = {
            "type": "ollama",
            "name": "Test Ollama",
            "baseUrl": "http://localhost:11434",
            "defaultModel": "llama3.1",
        }
        resp = client_with_config.post("/api/v1/providers/llm", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Ollama"
        assert "id" in data
        assert data["provider_type"] == "ollama"
        assert data["base_url"] == "http://localhost:11434"
        assert data["is_enabled"] is True

    def test_create_persists_in_list(self, client_with_config: TestClient) -> None:
        client_with_config.post("/api/v1/providers/llm", json={
            "type": "openai",
            "name": "OpenAI Prod",
            "baseUrl": "https://api.openai.com/v1",
            "apiKey": "sk-prod",
            "defaultModel": "gpt-4o",
        })
        resp = client_with_config.get("/api/v1/providers/llm")
        providers = resp.json()["providers"]
        assert len(providers) == 1
        assert providers[0]["name"] == "OpenAI Prod"

    def test_auto_generates_unique_ids(self, client_with_config: TestClient) -> None:
        p1 = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama", "name": "A", "baseUrl": "http://a:11434",
        }).json()
        p2 = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama", "name": "B", "baseUrl": "http://b:11434",
        }).json()
        assert p1["id"] != p2["id"]

    def test_default_enabled_flag(self, client_with_config: TestClient) -> None:
        body = {"type": "ollama", "name": "Explicit Disabled", "baseUrl": "http://localhost:11434", "isEnabled": False}
        resp = client_with_config.post("/api/v1/providers/llm", json=body)
        assert resp.json()["is_enabled"] is False


# ---------------------------------------------------------------------------
# Tests: LLM Provider Update
# ---------------------------------------------------------------------------


class TestUpdateLLMProvider:
    """``PUT /api/v1/providers/llm/{provider_id}``"""

    def test_update_changes_name(self, client_with_config: TestClient) -> None:
        created = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama", "name": "Original", "baseUrl": "http://localhost:11434",
        }).json()
        pid = created["id"]

        resp = client_with_config.put(f"/api/v1/providers/llm/{pid}", json={"name": "Renamed"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"

        # Confirm via list
        providers = client_with_config.get("/api/v1/providers/llm").json()["providers"]
        assert providers[0]["name"] == "Renamed"

    def test_update_persists_across_requests(self, client_with_config: TestClient) -> None:
        created = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama", "name": "Persist Me", "baseUrl": "http://localhost:11434",
        }).json()
        pid = created["id"]

        client_with_config.put(f"/api/v1/providers/llm/{pid}", json={
            "baseUrl": "http://localhost:11435", "defaultModel": "llama3.2",
        })

        providers = client_with_config.get("/api/v1/providers/llm").json()["providers"]
        p = providers[0]
        assert p["base_url"] == "http://localhost:11435"
        assert p["default_model"] == "llama3.2"

    def test_404_for_unknown_provider(self, client_with_config: TestClient) -> None:
        resp = client_with_config.put("/api/v1/providers/llm/nonexistent", json={"name": "No"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: LLM Provider Delete
# ---------------------------------------------------------------------------


class TestDeleteLLMProvider:
    """``DELETE /api/v1/providers/llm/{provider_id}``"""

    def test_delete_removes_provider(self, client_with_config: TestClient) -> None:
        created = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama", "name": "To Delete", "baseUrl": "http://localhost:11434",
        }).json()
        pid = created["id"]

        resp = client_with_config.delete(f"/api/v1/providers/llm/{pid}")
        assert resp.status_code == 200
        assert resp.json() == {"deleted": pid}

        providers = client_with_config.get("/api/v1/providers/llm").json()["providers"]
        assert len(providers) == 0

    def test_404_for_unknown_delete(self, client_with_config: TestClient) -> None:
        resp = client_with_config.delete("/api/v1/providers/llm/does-not-exist")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: LLM Provider Test
# ---------------------------------------------------------------------------


class TestLLMProviderTest:
    """``POST /api/v1/providers/llm/{provider_id}/test``"""

    def test_test_returns_structure(self, client_with_config: TestClient) -> None:
        created = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama", "name": "Testable", "baseUrl": "http://localhost:11434",
        }).json()
        pid = created["id"]

        # Mock httpx to avoid real network calls
        with patch("heretek_swarm.llm.model_garage.httpx.AsyncClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
            mock_client.is_closed = False
            mock_cls.return_value = mock_client
            with patch("heretek_swarm.llm.model_garage.instrumented_httpx_client", return_value=mock_client):
                resp = client_with_config.post(f"/api/v1/providers/llm/{pid}/test")

        assert resp.status_code == 200
        data = resp.json()
        assert "reachable" in data
        assert "latency_ms" in data
        assert "error" in data

    def test_404_for_unknown_test(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/llm/nope/test")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: Embedding Provider CRUD
# ---------------------------------------------------------------------------


class TestEmbeddingProviders:
    """Embedding endpoints under ``/api/v1/providers/embedding``"""

    def test_list_empty(self, client_with_config: TestClient) -> None:
        resp = client_with_config.get("/api/v1/providers/embedding")
        assert resp.status_code == 200
        assert resp.json()["providers"] == []

    def test_create_and_list(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/embedding", json={
            "type": "ollama",
            "name": "Ollama Embeddings",
            "baseUrl": "http://localhost:11434",
            "defaultModel": "nomic-embed-text",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Ollama Embeddings"
        assert "id" in data

        providers = client_with_config.get("/api/v1/providers/embedding").json()["providers"]
        assert len(providers) == 1
        assert providers[0]["name"] == "Ollama Embeddings"

    def test_delete(self, client_with_config: TestClient) -> None:
        created = client_with_config.post("/api/v1/providers/embedding", json={
            "type": "openai", "name": "OpenAI Emb", "baseUrl": "https://api.openai.com/v1",
        }).json()
        pid = created["id"]

        resp = client_with_config.delete(f"/api/v1/providers/embedding/{pid}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == pid

        providers = client_with_config.get("/api/v1/providers/embedding").json()["providers"]
        assert len(providers) == 0

    def test_update(self, client_with_config: TestClient) -> None:
        created = client_with_config.post("/api/v1/providers/embedding", json={
            "type": "ollama", "name": "Original Emb", "baseUrl": "http://localhost:11434",
        }).json()
        pid = created["id"]

        resp = client_with_config.put(f"/api/v1/providers/embedding/{pid}", json={"name": "Renamed Emb"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Emb"

    def test_404_for_unknown_update(self, client_with_config: TestClient) -> None:
        resp = client_with_config.put("/api/v1/providers/embedding/nope", json={"name": "No"})
        assert resp.status_code == 404

    def test_404_for_unknown_delete(self, client_with_config: TestClient) -> None:
        resp = client_with_config.delete("/api/v1/providers/embedding/nope")
        assert resp.status_code == 404

    def test_test_endpoint_returns_structure(self, client_with_config: TestClient) -> None:
        created = client_with_config.post("/api/v1/providers/embedding", json={
            "type": "ollama",
            "name": "Emb Test",
            "baseUrl": "http://localhost:11434",
        }).json()
        pid = created["id"]

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            resp = client_with_config.post(f"/api/v1/providers/embedding/{pid}/test")

        assert resp.status_code == 200
        data = resp.json()
        assert "reachable" in data
        assert "latency_ms" in data
        assert "error" in data

    def test_test_404_unknown(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/embedding/nope/test")
        assert resp.status_code == 404

    def test_rate_limit_header_present(self, client_with_config: TestClient) -> None:
        resp = client_with_config.get("/api/v1/providers/embedding")
        assert "X-RateLimit-Limit" in resp.headers


# ---------------------------------------------------------------------------
# Negative Tests (Q7)
# ---------------------------------------------------------------------------


class TestNegativeInputs:
    """Malformed inputs, error paths, boundary conditions."""

    def test_invalid_provider_type_returns_400(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/llm", json={
            "type": "not-a-real-type",
            "name": "Bad",
            "baseUrl": "http://localhost:11434",
        })
        assert resp.status_code == 400
        assert "Unknown provider type" in resp.json()["detail"]

    def test_empty_name_returns_422(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama",
            "name": "",
            "baseUrl": "http://localhost:11434",
        })
        assert resp.status_code == 422

    def test_missing_base_url_returns_422(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama",
            "name": "Missing URL",
        })
        assert resp.status_code == 422

    def test_long_name_is_accepted_or_validated(self, client_with_config: TestClient) -> None:
        """Names longer than 200 chars should be 422."""
        long_name = "A" * 201
        resp = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama",
            "name": long_name,
            "baseUrl": "http://localhost:11434",
        })
        assert resp.status_code == 422

    def test_negative_priority_rejected(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/llm", json={
            "type": "ollama",
            "name": "Bad Priority",
            "baseUrl": "http://localhost:11434",
            "priority": -1,
        })
        assert resp.status_code == 422

    def test_whitespace_only_provider_id_returns_400(self, client_with_config: TestClient) -> None:
        resp = client_with_config.put("/api/v1/providers/llm/   ", json={"name": "Nope"})
        assert resp.status_code == 400

    def test_embedding_missing_type_returns_422(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/embedding", json={
            "name": "NoType",
            "baseUrl": "http://localhost:11434",
        })
        assert resp.status_code == 422

    def test_embedding_empty_name_returns_422(self, client_with_config: TestClient) -> None:
        resp = client_with_config.post("/api/v1/providers/embedding", json={
            "type": "ollama",
            "name": "",
            "baseUrl": "http://localhost:11434",
        })
        assert resp.status_code == 422
