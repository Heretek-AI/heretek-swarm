"""Tests for config CLI commands and integration.

Verifies that all config subcommands (wizard, list, remove, set-default,
validate) work correctly through Click's CliRunner. Also tests the
``set_global_model_garage()`` function and ``get_router()`` wiring.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from heretek_swarm.cli import cli
from heretek_swarm.cli.config_wizard import (
    AVAILABLE_PROVIDERS,
    HERETEK_CONFIG_FILE,
    _load_config,
    _save_config,
    add_provider,
    list_configured_providers,
    remove_provider,
    set_default_provider,
    validate_provider,
)
from heretek_swarm.routing.model_router import (
    AgentModelRouter,
    get_router,
    set_global_model_garage,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner() -> CliRunner:
    """Return a Click CliRunner for invoking CLI commands."""
    return CliRunner()


@pytest.fixture(autouse=True)
def _cleanup_router_registry() -> None:
    """Clear the global router registry and garage between tests."""
    from heretek_swarm.routing import model_router as mr

    mr._router_registry.clear()
    mr._global_model_garage = None
    yield


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory and patch the config file path.

    Returns the path to the temporary config file.
    """
    config_file = tmp_path / ".heretek-swarm" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    # Seed with empty config
    seed = {"version": "1.0.0", "modelProviders": []}
    config_file.write_text(json.dumps(seed))

    # Patch the config file path
    with patch.object(HERETEK_CONFIG_FILE.__class__, "parent", new_callable=lambda: tmp_path):
        with patch("heretek_swarm.cli.config_wizard.HERETEK_CONFIG_FILE", config_file):
            yield config_file


@pytest.fixture
def seeded_config(temp_config_dir: Path) -> Path:
    """Create a config with one pre-seeded provider and return the path."""
    provider = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "ollama",
        "name": "Local Ollama",
        "baseUrl": "http://localhost:11434",
        "defaultModel": "llama3.2",
        "isEnabled": True,
        "isDefault": True,
        "priority": 1,
    }
    config = {"version": "1.0.0", "modelProviders": [provider]}
    temp_config_dir.write_text(json.dumps(config, indent=2))
    return temp_config_dir


# ---------------------------------------------------------------------------
# Config File Helpers
# ---------------------------------------------------------------------------


class TestConfigFileHelpers:
    """Tests for low-level config file helpers."""

    def test_load_config_empty(self, temp_config_dir: Path) -> None:
        """Loading a file with empty providers returns an empty list."""
        cfg = _load_config()
        assert cfg["version"] == "1.0.0"
        assert cfg["modelProviders"] == []

    def test_load_config_missing_file(self, tmp_path: Path) -> None:
        """Loading a non-existent file returns a default config."""
        missing = tmp_path / "nope" / "config.json"
        with patch("heretek_swarm.cli.config_wizard.HERETEK_CONFIG_FILE", missing):
            cfg = _load_config()
            assert cfg["modelProviders"] == []

    def test_load_config_corrupted(self, temp_config_dir: Path) -> None:
        """Loading corrupted JSON returns a default config."""
        temp_config_dir.write_text("{invalid json")
        cfg = _load_config()
        assert cfg["modelProviders"] == []

    def test_save_and_reload(self, temp_config_dir: Path) -> None:
        """Saving then loading preserves provider data."""
        provider = {
            "id": "test-id-001",
            "type": "openai",
            "name": "Test Provider",
            "baseUrl": "https://api.example.com",
            "defaultModel": "gpt-4o",
            "isEnabled": True,
            "isDefault": False,
            "priority": 50,
        }
        cfg = _load_config()
        cfg["modelProviders"].append(provider)
        _save_config(cfg)

        reloaded = _load_config()
        assert len(reloaded["modelProviders"]) == 1
        assert reloaded["modelProviders"][0]["id"] == "test-id-001"


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------


class TestProviderCRUD:
    """Tests for add_provider, remove_provider, set_default_provider,
    list_configured_providers."""

    def test_add_provider(self, temp_config_dir: Path) -> None:
        """Adding a provider persists it and returns the entry."""
        entry = {
            "id": str(uuid.uuid4()),
            "type": "openai",
            "name": "OpenAI Test",
            "baseUrl": "https://api.openai.com/v1",
            "defaultModel": "gpt-4o",
            "isEnabled": True,
            "isDefault": False,
            "priority": 100,
        }
        result = add_provider(entry)
        assert result["id"] == entry["id"]

        providers = list_configured_providers()
        assert len(providers) == 1
        assert providers[0]["name"] == "OpenAI Test"

    def test_remove_provider_found(self, seeded_config: Path) -> None:
        """Removing an existing provider returns True and it disappears."""
        assert remove_provider("550e8400-e29b-41d4-a716-446655440000") is True
        providers = list_configured_providers()
        assert len(providers) == 0

    def test_remove_provider_not_found(self, seeded_config: Path) -> None:
        """Removing a non-existent provider returns False."""
        assert remove_provider("nonexistent-id") is False
        providers = list_configured_providers()
        assert len(providers) == 1  # unchanged

    def test_set_default_provider(self, seeded_config: Path) -> None:
        """Setting a provider as default marks it and clears others."""
        # Add a second provider first
        add_provider({
            "id": "second-id-001",
            "type": "openai",
            "name": "Second Provider",
            "baseUrl": "https://api.example.com",
            "defaultModel": "gpt-4o",
            "isEnabled": True,
            "isDefault": False,
            "priority": 50,
        })

        # Set the second as default
        assert set_default_provider("second-id-001") is True

        providers = list_configured_providers()
        for p in providers:
            if p["id"] == "second-id-001":
                assert p["isDefault"] is True
            else:
                assert p["isDefault"] is False

    def test_set_default_not_found(self, seeded_config: Path) -> None:
        """Setting default for a missing ID returns False."""
        assert set_default_provider("does-not-exist") is False

    def test_list_configured_providers_empty(self, temp_config_dir: Path) -> None:
        """list_configured_providers returns empty list when empty."""
        assert list_configured_providers() == []

    def test_list_configured_providers_seeded(self, seeded_config: Path) -> None:
        """list_configured_providers returns the seeded provider."""
        providers = list_configured_providers()
        assert len(providers) == 1
        assert providers[0]["name"] == "Local Ollama"


# ---------------------------------------------------------------------------
# Validate Provider (dispatch)
# ---------------------------------------------------------------------------


class TestValidateProvider:
    """Tests for ``validate_provider()`` dispatch logic.

    Note: actual network validators are tested by mocking httpx internally.
    These tests verify the dispatch, error paths, and skip logic.
    """

    def test_unknown_provider(self) -> None:
        """An unknown provider ID returns an error."""
        result = validate_provider("nonexistent", None, "http://localhost", "model")
        assert result["valid"] is False
        assert "Unknown" in result["error"]

    def test_validator_not_available(self) -> None:
        """A provider type without a registered validator returns valid
        with a skip message."""
        with patch.dict(
            "heretek_swarm.cli.config_wizard.AVAILABLE_PROVIDERS",
            {"custom": {
                "id": "custom",
                "type": "custom_protocol",
                "name": "Custom",
                "description": "Test",
                "default_model": "test",
                "requires_api_key": False,
                "base_url": "http://localhost",
            }},
            clear=False,
        ):
            result = validate_provider("custom", None, "http://localhost", "test")
            assert result["valid"] is True
            assert "Validation not available" in result["message"]

    def test_missing_api_key_required_provider(self) -> None:
        """A provider that requires an API key returns invalid when key is
        missing."""
        result = validate_provider(
            "openai", None, "https://api.openai.com/v1", "gpt-4o"
        )
        assert result["valid"] is False
        assert "API key is required" in result["error"]

    @patch("httpx.Client")
    def test_ollama_validator_success(self, mock_client_cls: MagicMock) -> None:
        """Ollama validator returns valid on 200."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3.2"}]}
        mock_client.get.return_value = mock_response

        result = validate_provider(
            "ollama", None, "http://localhost:11434", "llama3.2"
        )
        assert result["valid"] is True
        assert "Connected" in result["message"]

    @patch("httpx.Client")
    def test_ollama_validator_failure(self, mock_client_cls: MagicMock) -> None:
        """Ollama validator returns invalid on bad connection."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        from httpx import ConnectError
        mock_client.get.side_effect = ConnectError("Connection refused")

        result = validate_provider(
            "ollama", None, "http://localhost:11434", "llama3.2"
        )
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# CLI Commands (CliRunner)
# ---------------------------------------------------------------------------


class TestConfigListCommand:
    """Tests for ``heretek-swarm config list``."""

    def test_list_empty(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Running config list with no providers shows the empty message."""
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        assert "No LLM providers configured" in result.output

    def test_list_seeded(self, runner: CliRunner, seeded_config: Path) -> None:
        """Running config list shows provider details."""
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        assert "Local Ollama" in result.output
        assert "ollama" in result.output
        assert "llama3.2" in result.output
        assert "http://localhost:11434" in result.output
        assert "[default]" in result.output.lower()


class TestConfigRemoveCommand:
    """Tests for ``heretek-swarm config remove``."""

    def test_remove_exact_id(self, runner: CliRunner, seeded_config: Path) -> None:
        """Removing by exact ID works with confirmation."""
        result = runner.invoke(
            cli, ["config", "remove", "550e8400-e29b-41d4-a716-446655440000"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Removed provider" in result.output

    def test_remove_partial_id(self, runner: CliRunner, seeded_config: Path) -> None:
        """Removing by partial ID (first 8+ chars) works."""
        result = runner.invoke(
            cli, ["config", "remove", "550e8400"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Removed provider" in result.output

    def test_remove_cancelled(self, runner: CliRunner, seeded_config: Path) -> None:
        """Removing is cancelled when the user says no."""
        result = runner.invoke(
            cli, ["config", "remove", "550e8400-e29b-41d4-a716-446655440000"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert "Cancelled" in result.output
        # Provider still exists
        assert len(list_configured_providers()) == 1

    def test_remove_not_found(self, runner: CliRunner, seeded_config: Path) -> None:
        """Removing a non-existent ID shows not-found message."""
        result = runner.invoke(cli, ["config", "remove", "not-here"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()


class TestConfigSetDefaultCommand:
    """Tests for ``heretek-swarm config set-default``."""

    def test_set_default_exact(self, runner: CliRunner, seeded_config: Path) -> None:
        """Setting default by exact ID works."""
        result = runner.invoke(
            cli, ["config", "set-default", "550e8400-e29b-41d4-a716-446655440000"],
        )
        assert result.exit_code == 0
        assert "set as default" in result.output.lower()

    def test_set_default_partial(self, runner: CliRunner, seeded_config: Path) -> None:
        """Setting default by partial ID works."""
        result = runner.invoke(cli, ["config", "set-default", "550e8400"])
        assert result.exit_code == 0
        assert "set as default" in result.output.lower()

    def test_set_default_not_found(self, runner: CliRunner, seeded_config: Path) -> None:
        """Setting default for non-existent ID shows not-found message."""
        result = runner.invoke(cli, ["config", "set-default", "bad-id"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()


class TestConfigValidateCommand:
    """Tests for ``heretek-swarm config validate``.

    These tests mock httpx.Client so no real network calls are made.
    """

    @patch("httpx.Client")
    def test_validate_all(
        self,
        mock_client_cls: MagicMock,
        runner: CliRunner,
        seeded_config: Path,
    ) -> None:
        """Validating all providers runs without error."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3.2"}]}
        mock_client.get.return_value = mock_response

        result = runner.invoke(cli, ["config", "validate"])
        assert result.exit_code == 0
        assert "Provider Validation" in result.output
        assert "Local Ollama" in result.output

    @patch("httpx.Client")
    def test_validate_specific_provider(
        self,
        mock_client_cls: MagicMock,
        runner: CliRunner,
        seeded_config: Path,
    ) -> None:
        """Validating a specific provider by ID works."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3.2"}]}
        mock_client.get.return_value = mock_response

        result = runner.invoke(
            cli, ["config", "validate", "550e8400"],
        )
        assert result.exit_code == 0
        assert "Local Ollama" in result.output
        # Should only validate one provider
        assert mock_client.get.call_count == 1

    def test_validate_empty(
        self, runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """Validating with no configured providers shows appropriate message."""
        result = runner.invoke(cli, ["config", "validate"])
        assert result.exit_code == 0
        assert "No providers configured" in result.output

    @patch("httpx.Client")
    def test_validate_not_found(
        self,
        mock_client_cls: MagicMock,
        runner: CliRunner,
        seeded_config: Path,
    ) -> None:
        """Validating a non-existent provider ID shows error."""
        result = runner.invoke(cli, ["config", "validate", "deadbeef"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    @patch("httpx.Client")
    def test_validate_failure_shows_error(
        self,
        mock_client_cls: MagicMock,
        runner: CliRunner,
        seeded_config: Path,
    ) -> None:
        """When validation fails, the error is displayed."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        from httpx import ConnectError
        mock_client.get.side_effect = ConnectError("Ollama not running")

        result = runner.invoke(cli, ["config", "validate"])
        assert result.exit_code == 0
        assert "Some validations failed" in result.output


# ---------------------------------------------------------------------------
# Config Wizard Command
# ---------------------------------------------------------------------------


class TestConfigWizardCommand:
    """Tests for ``heretek-swarm config wizard``."""

    @staticmethod
    def _ollama_inputs() -> str:
        """Returns CliRunner input for adding an Ollama provider via wizard."""
        # Selection of Ollama (3rd in list), enter URL, skip API key,
        # default model, skip validation, done adding
        return "\n".join([
            "3",         # Ollama
            "",          # default URL
            "",          # skip API key
            "",          # default model
            "n",         # skip validation
            "n",         # don't add another
        ])

    def test_wizard_adds_provider(
        self, runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """Running the wizard and completing the flow adds a provider."""
        result = runner.invoke(
            cli, ["config", "wizard"],
            input=self._ollama_inputs(),
        )
        assert result.exit_code == 0
        assert "Configuration complete" in result.output
        assert "1 provider(s) saved" in result.output

        providers = list_configured_providers()
        assert len(providers) == 1
        assert providers[0]["type"] == "ollama"

    def test_wizard_cancels_cleanly(
        self, runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """Cancelling the wizard at the provider selection prompt shows
        no providers configured and exits cleanly."""
        result = runner.invoke(
            cli, ["config", "wizard"],
            input="q\n",
        )
        assert result.exit_code == 0
        assert "No providers configured" in result.output

    def test_wizard_shows_summary_commands(
        self, runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """After completing the wizard, summary shows management commands."""
        result = runner.invoke(
            cli, ["config", "wizard"],
            input=self._ollama_inputs(),
        )
        assert result.exit_code == 0
        assert "config list" in result.output
        assert "config remove" in result.output
        assert "config set-default" in result.output


# ---------------------------------------------------------------------------
# CLI Help and Group Structure
# ---------------------------------------------------------------------------


class TestConfigHelp:
    """Tests for CLI help output and command structure."""

    def test_config_group_help(self, runner: CliRunner) -> None:
        """``heretek-swarm config --help`` shows all subcommands."""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "wizard" in result.output
        assert "list" in result.output
        assert "remove" in result.output
        assert "set-default" in result.output
        assert "validate" in result.output

    def test_config_group_in_cli_help(self, runner: CliRunner) -> None:
        """``heretek-swarm --help`` includes the config group."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "config" in result.output


# ---------------------------------------------------------------------------
# set_global_model_garage Integration
# ---------------------------------------------------------------------------


def _make_mock_garage() -> MagicMock:
    """Build a mock ModelGarage with one provider."""
    garage = MagicMock()
    garage.list_providers.return_value = [
        {
            "id": "test-provider",
            "baseUrl": "http://localhost:11434",
            "apiKey": "",
            "models": ["llama3.2"],
            "priority": 1,
            "health_status": "healthy",
        },
    ]
    return garage


class TestSetGlobalModelGarage:
    """Tests for ``set_global_model_garage()`` and ``get_router()`` wiring."""

    def test_set_global_garage_wires_to_get_router(self) -> None:
        """After calling set_global_model_garage, get_router() creates
        routers with the garage wired."""
        garage = _make_mock_garage()
        set_global_model_garage(garage)

        router = get_router("test-agent")
        stats = router.get_stats()
        assert stats["source"] == "garage"
        assert stats["providers_registered"] == 1
        assert stats["providers_healthy"] == 1

    def test_get_router_without_garage(self) -> None:
        """get_router() works without any garage set (standalone mode)."""
        router = get_router("standalone-agent")
        stats = router.get_stats()
        assert stats["source"] == "standalone"
        assert stats["providers_registered"] == 0

    def test_garage_providers_appear_in_route(self) -> None:
        """Providers from the garage appear in the router's provider dict."""
        garage = _make_mock_garage()
        set_global_model_garage(garage)
        router = get_router("route-test")

        providers = router._get_providers()
        assert "test-provider" in providers
        assert providers["test-provider"].base_url == "http://localhost:11434"
        assert providers["test-provider"].health_status is True

    def test_set_global_garage_none_clears(self) -> None:
        """Setting the global garage to None clears it, so subsequent
        get_router() calls return standalone routers."""
        garage = _make_mock_garage()
        set_global_model_garage(garage)
        set_global_model_garage(None)

        router = get_router("post-clear-agent")
        stats = router.get_stats()
        assert stats["source"] == "standalone"

    def test_standalone_configs_override_garage(self) -> None:
        """Standalone configs registered on a router take precedence over
        garage-derived configs for the same provider_id."""
        from heretek_swarm.routing.model_router import RouterProviderConfig

        garage = _make_mock_garage()
        set_global_model_garage(garage)
        router = get_router("override-test")

        # Register a standalone config with the same ID but different URL
        standalone = RouterProviderConfig(
            provider_id="test-provider",
            base_url="http://custom:11434",
            api_key="custom-key",
            models=["custom-model"],
            priority=1,
        )
        router.register_provider(standalone)

        providers = router._get_providers()
        assert providers["test-provider"].base_url == "http://custom:11434"
        assert providers["test-provider"].api_key == "custom-key"

    def test_router_routing_with_garage(self) -> None:
        """A router wired to a garage can actually route (simplified test)."""
        garage = MagicMock()
        garage.list_providers.return_value = [
            {
                "id": "fast-llm",
                "baseUrl": "http://localhost:11434",
                "apiKey": "",
                "models": ["llama3.1", "gemini-flash"],
                "priority": 1,
                "health_status": "healthy",
            },
        ]
        router = AgentModelRouter(agent_id="garage-route-test", model_garage=garage)

        decision = router.route("format this text", None, None, False)
        assert decision.provider_id == "fast-llm"
        assert decision.complexity.value == "simple"


# ---------------------------------------------------------------------------
# Edge Cases and Negative Tests
# ---------------------------------------------------------------------------


class TestConfigEdgeCases:
    """Tests for edge cases and error paths in config operations."""

    def test_provider_display_name_fallback(self) -> None:
        """_provider_display_name handles missing keys gracefully."""
        from heretek_swarm.cli.config_wizard import _provider_display_name

        minimal = {"type": "test"}
        name = _provider_display_name(minimal)
        assert "test" in name
        assert "no default model" in name

    def test_find_provider_by_id_not_found(self) -> None:
        """_find_provider_by_id returns None for unknown ID."""
        from heretek_swarm.cli.config_wizard import _find_provider_by_id

        assert _find_provider_by_id([], "nope") is None

    def test_find_providers_by_type(self, seeded_config: Path) -> None:
        """_find_providers_by_type matches on type field."""
        from heretek_swarm.cli.config_wizard import _find_providers_by_type

        providers = list_configured_providers()
        ollama_providers = _find_providers_by_type(providers, "ollama")
        assert len(ollama_providers) == 1
        assert _find_providers_by_type(providers, "openai") == []

    def test_remove_provider_empty_config(self, temp_config_dir: Path) -> None:
        """Removing from empty config returns False."""
        assert remove_provider("any-id") is False

    def test_config_command_structure(self) -> None:
        """The config command group has exactly the expected subcommands."""
        from heretek_swarm.cli import config

        cmd_names = set(config.commands.keys())
        expected = {"wizard", "list", "remove", "set-default", "validate"}
        assert cmd_names == expected, f"Got {cmd_names}, expected {expected}"

    def test_cli_re_exports_config_wizard_symbols(self) -> None:
        """All public config_wizard symbols are re-exported from cli."""
        from heretek_swarm.cli import (
            AVAILABLE_PROVIDERS as cli_ap,
            add_provider as cli_add,
            list_configured_providers as cli_lcp,
            prompt_for_provider as cli_pfp,
            remove_provider as cli_rp,
            run_wizard as cli_rw,
            set_default_provider as cli_sdp,
            validate_provider as cli_vp,
        )
        # Smoke test — all imports resolved
        assert callable(cli_add)
        assert callable(cli_lcp)
        assert callable(cli_pfp)
        assert callable(cli_rp)
        assert callable(cli_rw)
        assert callable(cli_sdp)
        assert callable(cli_vp)

    def test_list_shows_disabled_providers(self, seeded_config: Path) -> None:
        """Disabled providers still appear in the list."""
        add_provider({
            "id": "disabled-id",
            "type": "openai",
            "name": "Disabled Provider",
            "baseUrl": "https://api.example.com",
            "defaultModel": "gpt-4o",
            "isEnabled": False,
            "isDefault": False,
            "priority": 99,
        })
        providers = list_configured_providers()
        names = [p["name"] for p in providers]
        assert "Disabled Provider" in names
        assert "Local Ollama" in names

    def test_set_default_no_providers(self, temp_config_dir: Path) -> None:
        """set_default_provider returns False when no providers exist."""
        assert set_default_provider("any-id") is False
