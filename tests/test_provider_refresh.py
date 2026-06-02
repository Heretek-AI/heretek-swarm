"""Tests for provider auto-refresh (env key hash comparison)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from heretek_swarm.llm.providers.factory import (
    ProviderManager,
    _config_hash,
    default_provider_manager,
)

# ---------------------------------------------------------------------------
# _config_hash unit tests
# ---------------------------------------------------------------------------


class TestConfigHash:
    """Tests for the _config_hash helper."""

    def test_same_config_same_hash(self):
        cfg = {"api_key": "sk-test", "base_url": "https://api.example.com"}
        assert _config_hash("openai", cfg) == _config_hash("openai", cfg)

    def test_different_api_key_different_hash(self):
        cfg_a = {"api_key": "sk-old", "base_url": "https://api.example.com"}
        cfg_b = {"api_key": "sk-new", "base_url": "https://api.example.com"}
        assert _config_hash("openai", cfg_a) != _config_hash("openai", cfg_b)

    def test_different_provider_type_different_hash(self):
        cfg = {"api_key": "sk-test"}
        assert _config_hash("openai", cfg) != _config_hash("ollama", cfg)

    def test_extra_config_order_independent(self):
        """Nested dict ordering must not affect the hash."""
        cfg_a = {"extra_config": {"b": 2, "a": 1}, "api_key": "k"}
        cfg_b = {"extra_config": {"a": 1, "b": 2}, "api_key": "k"}
        assert _config_hash("openai", cfg_a) == _config_hash("openai", cfg_b)

    def test_empty_config_hash_is_stable(self):
        h1 = _config_hash("ollama", {})
        h2 = _config_hash("ollama", {})
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest


# ---------------------------------------------------------------------------
# ProviderManager tests
# ---------------------------------------------------------------------------


class TestProviderManager:
    """Tests for the ProviderManager cache and auto-refresh logic."""

    def test_get_or_create_returns_provider(self):
        """First call should create and cache a provider."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider

            result = mgr.get_or_create("ollama", {"base_url": "http://localhost"})

            assert result is mock_provider
            mock_create.assert_called_once_with("ollama", {"base_url": "http://localhost"})
            assert mgr.cached_count == 1

    def test_get_or_create_returns_same_instance_on_identical_config(self):
        """Identical config should return cached instance (no rebuild)."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider

            first = mgr.get_or_create("ollama", {"base_url": "http://localhost"})
            second = mgr.get_or_create("ollama", {"base_url": "http://localhost"})

            assert first is second
            mock_create.assert_called_once()  # only built once

    def test_get_or_create_refreshes_on_config_change(self):
        """Changed config should evict old provider and create new one."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            old_provider = MagicMock()
            new_provider = MagicMock()
            mock_create.side_effect = [old_provider, new_provider]

            first = mgr.get_or_create("ollama", {"base_url": "http://localhost"})
            assert first is old_provider

            # Config changes -- different base_url
            second = mgr.get_or_create("ollama", {"base_url": "http://localhost:11434"})
            assert second is new_provider
            assert mock_create.call_count == 2
            # Old provider should have been scheduled for close
            old_provider.close.assert_not_called()  # fire-and-forget via asyncio

    def test_get_or_create_stale_eviction(self):
        """When a new config replaces an old one, the old entry is evicted."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            p1, p2 = MagicMock(), MagicMock()
            mock_create.side_effect = [p1, p2]

            mgr.get_or_create("openai", {"api_key": "key1"})
            mgr.get_or_create("openai", {"api_key": "key2"})

            assert mgr.cached_count == 1  # old was evicted

    def test_refresh_always_rebuilds(self):
        """refresh() should always create a new provider regardless of hash."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            p1, p2 = MagicMock(), MagicMock()
            mock_create.side_effect = [p1, p2]

            first = mgr.get_or_create("ollama", {"base_url": "http://localhost"})
            second = mgr.refresh("ollama", {"base_url": "http://localhost"})

            assert first is not second
            assert second is p2
            assert mock_create.call_count == 2

    def test_invalidate_all(self):
        """invalidate() with no args clears everything."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            mgr.get_or_create("ollama", {})
            mgr.get_or_create("openai", {"api_key": "k"})

            assert mgr.cached_count == 2
            mgr.invalidate()
            assert mgr.cached_count == 0

    def test_invalidate_by_type(self):
        """invalidate(provider_type) only clears that type."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            mgr.get_or_create("ollama", {})
            mgr.get_or_create("openai", {"api_key": "k"})

            mgr.invalidate("ollama")
            assert mgr.cached_count == 1
            assert "openai" in mgr.cached_types()

    def test_cached_types(self):
        """cached_types returns distinct provider type strings."""
        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            mgr.get_or_create("ollama", {})
            mgr.get_or_create("openai", {"api_key": "k"})

            types = mgr.cached_types()
            assert set(types) == {"ollama", "openai"}

    def test_default_manager_exists(self):
        """Module-level default_provider_manager is importable."""
        assert isinstance(default_provider_manager, ProviderManager)


class TestProviderManagerThreadSafety:
    """Basic concurrency smoke test."""

    def test_concurrent_get_or_create(self):
        """Multiple threads hitting get_or_create should not crash."""
        import concurrent.futures

        mgr = ProviderManager()
        with patch(
            "heretek_swarm.llm.providers.factory.create_llm_provider"
        ) as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider

            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                futures = [
                    pool.submit(mgr.get_or_create, "ollama", {"base_url": "http://localhost"})
                    for _ in range(20)
                ]
                for f in concurrent.futures.as_completed(futures):
                    results.append(f.result())

            # All 20 should get the same provider instance
            assert all(r is mock_provider for r in results)
            # Only one should have been created
            assert mock_create.call_count == 1
