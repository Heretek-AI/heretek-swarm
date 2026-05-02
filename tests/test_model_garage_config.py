"""Tests for ModelGarage configuration management.

Covers:
* ``get_config_path()`` with and without ``HEREKET_CONFIG_PATH`` env var.
* Atomic write survives crash (partial write == old state preserved).
* ``reload_config()`` re-populates after external file edits.
* ``update_provider()`` changes reflected in ``list_providers()``.
* ``test_provider()`` for enabled / disabled / unknown provider IDs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.config import get_config_path
from heretek_swarm.llm.model_garage import (
    ModelGarage,
    ProviderConfig,
    ProviderType,
    register_provider_class,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_config_file(path: Path, providers: list[dict] | None = None) -> dict:
    """Write a minimal valid config.json and return the dict."""
    data: dict = {"version": "1.0.0", "modelProviders": providers or []}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return data


# ---------------------------------------------------------------------------
# Tests: get_config_path
# ---------------------------------------------------------------------------


class TestGetConfigPath:
    """Tests for the shared ``get_config_path()`` utility."""

    def test_default_returns_dot_heretek_swarm_config_json(self) -> None:
        """Without env var, returns ~/.heretek-swarm/config.json."""
        with patch.dict(os.environ, {}, clear=True):
            path = get_config_path()
            assert path.name == "config.json"
            assert ".heretek-swarm" in str(path)

    def test_env_var_overrides_config_path(self, tmp_path: Path) -> None:
        """``HEREKET_CONFIG_PATH`` env var takes precedence."""
        custom = tmp_path / "custom-config.json"
        with patch.dict(os.environ, {"HEREKET_CONFIG_PATH": str(custom)}):
            path = get_config_path()
            assert path == custom

    def test_env_var_not_resolved_expanduser(self) -> None:
        """Env var value is used as-is (no tilde expansion)."""
        with patch.dict(os.environ, {"HEREKET_CONFIG_PATH": "~/override.json"}):
            path = get_config_path()
            assert str(path) in ("~/override.json", "~\\override.json")


# ---------------------------------------------------------------------------
# Tests: atomic write
# ---------------------------------------------------------------------------


class TestAtomicWrite:
    """Tests for atomic config persistence."""

    def test_atomic_write_writes_valid_json(self, tmp_path: Path) -> None:
        """Atomic write produces valid JSON at the target path."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file)

        garage = ModelGarage(config_file=config_file)
        garage.add_provider(ProviderConfig(
            id="test-atomic",
            name="Test Atomic",
            provider_type=ProviderType.OLLAMA,
            base_url="http://localhost:11434",
            default_model="llama3.1",
        ))

        # Verify the file is valid JSON with the provider
        saved = json.loads(config_file.read_text())
        providers = saved["modelProviders"]
        assert len(providers) == 1
        assert providers[0]["id"] == "test-atomic"

    def test_partial_write_does_not_corrupt_original(self, tmp_path: Path) -> None:
        """If the write fails mid-flight, the original file stays intact."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file, providers=[{
            "id": "original-id",
            "type": "ollama",
            "name": "Original",
            "baseUrl": "http://localhost:11434",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])

        original_text = config_file.read_text()
        garage = ModelGarage(config_file=config_file)

        # Inject a provider that will fail during serialization
        garage._provider_configs["new-one"] = ProviderConfig(
            id="new-one",
            name="New One",
            provider_type=ProviderType.OLLAMA,
            base_url="http://localhost:11434",
        )

        # Monkey-patch open to raise OSError during write
        original_open = open
        def _failing_open(*args, **kwargs):  # noqa: ANN002,ANN003
            if str(args[0]).endswith(".json.tmp"):
                raise OSError("disk full")
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=_failing_open):
            garage._save_config()

        # Original file must be unchanged
        assert config_file.read_text() == original_text

    def test_temp_file_cleaned_up_on_error(self, tmp_path: Path) -> None:
        """After a write failure, the .tmp file is removed."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file)

        garage = ModelGarage(config_file=config_file)
        garage._provider_configs["x"] = ProviderConfig(
            id="x", name="X", provider_type=ProviderType.OLLAMA,
            base_url="http://localhost:11434",
        )

        original_open = open
        def _failing_os_replace(*args, **kwargs):  # noqa: ANN002,ANN003
            raise OSError("atomic replace failed")
        def _real_open(*args, **kwargs):  # noqa: ANN002,ANN003
            return original_open(*args, **kwargs)

        with patch("os.replace", side_effect=_failing_os_replace):
            garage._save_config()

        # Temp file should not exist
        assert not config_file.with_suffix(config_file.suffix + ".tmp").exists()


# ---------------------------------------------------------------------------
# Tests: reload_config
# ---------------------------------------------------------------------------


class TestReloadConfig:
    """Tests for ``ModelGarage.reload_config()``."""

    def test_reload_picks_up_external_edits(self, tmp_path: Path) -> None:
        """Edits made directly to config.json are visible after reload."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file, providers=[{
            "id": "before-reload",
            "type": "ollama",
            "name": "Before Reload",
            "baseUrl": "http://localhost:11434",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])

        garage = ModelGarage(config_file=config_file)
        initial = garage.list_providers()
        assert len(initial) == 1
        assert initial[0]["id"] == "before-reload"

        # Simulate external edit: CLI wizard adds a provider
        existing = json.loads(config_file.read_text())
        existing["modelProviders"].append({
            "id": "after-reload",
            "type": "ollama",
            "name": "After Reload",
            "baseUrl": "http://localhost:11434",
            "isEnabled": True,
            "isDefault": False,
            "priority": 200,
        })
        config_file.write_text(json.dumps(existing, indent=2))

        garage.reload_config()
        after = garage.list_providers()
        assert len(after) == 2
        ids = {p["id"] for p in after}
        assert "before-reload" in ids
        assert "after-reload" in ids


# ---------------------------------------------------------------------------
# Tests: update_provider
# ---------------------------------------------------------------------------


class TestUpdateProvider:
    """Tests for ``ModelGarage.update_provider()``."""

    def test_update_changes_list_providers_output(self, tmp_path: Path) -> None:
        """After update_provider, list_providers reflects the change."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file, providers=[{
            "id": "to-update",
            "type": "ollama",
            "name": "Original Name",
            "baseUrl": "http://localhost:11434",
            "defaultModel": "llama3.1",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])

        garage = ModelGarage(config_file=config_file)
        updated = ProviderConfig(
            id="to-update",
            name="Updated Name",
            provider_type=ProviderType.OLLAMA,
            base_url="http://localhost:11434",
            default_model="llama3.2",
            is_enabled=False,
        )
        garage.update_provider("to-update", updated)

        providers = garage.list_providers()
        assert len(providers) == 1
        p = providers[0]
        assert p["name"] == "Updated Name"
        assert p["default_model"] == "llama3.2"
        assert p["is_enabled"] is False

    def test_update_unknown_provider_raises_keyerror(self, tmp_path: Path) -> None:
        """Updating a non-existent ID raises KeyError."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file)

        garage = ModelGarage(config_file=config_file)
        fake = ProviderConfig(
            id="does-not-exist",
            name="Fake",
            provider_type=ProviderType.OLLAMA,
            base_url="http://localhost:11434",
        )
        with pytest.raises(KeyError, match="does-not-exist"):
            garage.update_provider("does-not-exist", fake)

    def test_update_persists_to_file(self, tmp_path: Path) -> None:
        """update_provider writes the change to config.json on disk."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file, providers=[{
            "id": "disk-test",
            "type": "ollama",
            "name": "Disk Test",
            "baseUrl": "http://localhost:11434",
            "defaultModel": "llama3.1",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])

        garage = ModelGarage(config_file=config_file)
        garage.update_provider("disk-test", ProviderConfig(
            id="disk-test",
            name="Disk Test Updated",
            provider_type=ProviderType.OLLAMA,
            base_url="http://localhost:11434",
            default_model="llama3.2",
            is_enabled=False,
        ))

        # Read the file fresh to confirm disk persistence
        saved = json.loads(config_file.read_text())
        assert saved["modelProviders"][0]["name"] == "Disk Test Updated"
        assert saved["modelProviders"][0]["defaultModel"] == "llama3.2"


# ---------------------------------------------------------------------------
# Tests: test_provider
# ---------------------------------------------------------------------------


class TestTestProvider:
    """Tests for ``ModelGarage.test_provider()``."""

    @pytest.mark.asyncio
    async def test_unknown_id_returns_not_found(self, tmp_path: Path) -> None:
        """Testing an unknown provider returns reachable=False with error."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file)
        garage = ModelGarage(config_file=config_file)

        result = await garage.test_provider("does-not-exist")
        assert result["reachable"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_enabled_provider_calls_health_check(self, tmp_path: Path) -> None:
        """A healthy provider returns reachable=True with latency."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"

        # Use openai type which has a simpler health_check (just GET /)
        _seed_config_file(config_file, providers=[{
            "id": "test-openai",
            "type": "openai",
            "name": "Test OpenAI",
            "baseUrl": "http://localhost:8080",
            "apiKey": "sk-test",
            "defaultModel": "gpt-4o",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])

        garage = ModelGarage(config_file=config_file)

        with patch("heretek_swarm.llm.model_garage.httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
            mock_client.is_closed = False
            mock_client_cls.return_value = mock_client

            # Also mock instrumented_httpx_client to return mock_client directly
            with patch("heretek_swarm.llm.model_garage.instrumented_httpx_client", return_value=mock_client):
                result = await garage.test_provider("test-openai")

        assert result["reachable"] is True
        assert result["latency_ms"] >= 0
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_failing_health_check_returns_unreachable(self, tmp_path: Path) -> None:
        """If health_check throws, result is reachable=False with error."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file, providers=[{
            "id": "bad-openai",
            "type": "openai",
            "name": "Bad OpenAI",
            "baseUrl": "http://localhost:9999",
            "apiKey": "sk-bad",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])

        garage = ModelGarage(config_file=config_file)

        with patch("heretek_swarm.llm.model_garage.httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
            mock_client.is_closed = False
            mock_client_cls.return_value = mock_client

            with patch("heretek_swarm.llm.model_garage.instrumented_httpx_client", return_value=mock_client):
                result = await garage.test_provider("bad-openai")

        assert result["reachable"] is False
        assert "health check failed" in str(result["error"]).lower()

    @pytest.mark.asyncio
    async def test_test_provider_does_not_leave_stale_connection(self, tmp_path: Path) -> None:
        """After test_provider, the provider is NOT in the internal _providers dict."""
        config_file = tmp_path / ".heretek-swarm" / "config.json"
        _seed_config_file(config_file, providers=[{
            "id": "cleanup-test",
            "type": "openai",
            "name": "Cleanup Test",
            "baseUrl": "http://localhost:8080",
            "apiKey": "sk-test",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }])

        garage = ModelGarage(config_file=config_file)

        with patch("heretek_swarm.llm.model_garage.httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
            mock_client.is_closed = False
            mock_client_cls.return_value = mock_client

            with patch("heretek_swarm.llm.model_garage.instrumented_httpx_client", return_value=mock_client):
                await garage.test_provider("cleanup-test")

        # Provider must NOT be in _providers after test
        assert "cleanup-test" not in garage._providers
