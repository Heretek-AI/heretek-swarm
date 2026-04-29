"""Unit tests for ``heretek_swarm.agents.agent_factory.build_agent_for``.

The function under test reads ``OPENAI_API_KEY``, ``OPENAI_BASE_URL``, and
``LLM_MODEL`` from the environment **inside its body** (not at module level)
and constructs a ``swarms.Agent`` via its ``__init__``.

Because ``swarms.Agent`` is imported lazily inside the function body (not at
module level), we patch ``"swarms.Agent"`` directly rather than trying to
patch the module-level reference which does not exist until the function runs.
"""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _mock_agent_class() -> MagicMock:
    """Return a MagicMock that, when called, returns another MagicMock.

    Using ``return_value`` on the class itself means ``Agent(...)`` produces
    a fresh ``MagicMock`` instance that carries the attributes set by
    ``build_agent_for`` — chiefly ``agent_name``.
    """
    cls = MagicMock()
    cls.return_value = MagicMock()
    return cls


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBuildAgentFor:
    """Group for ``build_agent_for`` unit tests."""

    def test_raises_value_error_when_api_key_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing ``OPENAI_API_KEY`` raises ``ValueError``."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from heretek_swarm.agents.agent_factory import build_agent_for

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            build_agent_for("alpha", "AlphaAgent")

    def test_returns_agent_with_correct_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Agent's ``agent_name`` matches the supplied ``agent_id``."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        mock_cls = _mock_agent_class()
        with patch("swarms.Agent", mock_cls):
            from heretek_swarm.agents.agent_factory import build_agent_for

            agent = build_agent_for("alpha", "AlphaAgent")

        # Verify the constructor was called with the expected name
        mock_cls.assert_called_once()
        _call_kwargs = mock_cls.call_args.kwargs
        assert _call_kwargs.get("agent_name") == "alpha"
        assert agent is mock_cls.return_value

    def test_default_model_is_gpt_4_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When ``LLM_MODEL`` is unset the default ``gpt-4.1`` is used."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.delenv("LLM_MODEL", raising=False)

        mock_cls = _mock_agent_class()
        with patch("swarms.Agent", mock_cls):
            from heretek_swarm.agents.agent_factory import build_agent_for

            build_agent_for("alpha", "AlphaAgent")

        mock_cls.assert_called_once()
        assert mock_cls.call_args.kwargs.get("model_name") == "gpt-4.1"

    def test_custom_model_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``LLM_MODEL=gpt-4o`` is passed through to ``Agent(model_name=...)``."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")

        mock_cls = _mock_agent_class()
        with patch("swarms.Agent", mock_cls):
            from heretek_swarm.agents.agent_factory import build_agent_for

            build_agent_for("alpha", "AlphaAgent")

        mock_cls.assert_called_once()
        assert mock_cls.call_args.kwargs.get("model_name") == "gpt-4o"

    def test_system_prompt_passed_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Optional ``system_prompt`` is forwarded to the ``Agent``."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        custom_prompt = "You are a test agent."
        mock_cls = _mock_agent_class()
        with patch("swarms.Agent", mock_cls):
            from heretek_swarm.agents.agent_factory import build_agent_for

            build_agent_for("alpha", "AlphaAgent", system_prompt=custom_prompt)

        mock_cls.assert_called_once()
        assert mock_cls.call_args.kwargs.get("system_prompt") == custom_prompt

    def test_default_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When ``OPENAI_BASE_URL`` is unset the default URL is used."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        mock_cls = _mock_agent_class()
        with patch("swarms.Agent", mock_cls):
            from heretek_swarm.agents.agent_factory import build_agent_for

            build_agent_for("alpha", "AlphaAgent")

        mock_cls.assert_called_once()
        assert mock_cls.call_args.kwargs.get("llm_base_url") == "https://api.openai.com/v1"
