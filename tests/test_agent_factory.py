"""Unit tests for ``heretek_swarm.agents.agent_factory.build_agent_for``.

The function under test reads ``OPENAI_API_KEY``, ``OPENAI_BASE_URL``, and
``LLM_MODEL`` from the environment **inside its body** (not at module level)
and constructs a ``swarms.Agent`` via its ``__init__``.

Because ``swarms.Agent`` is imported lazily inside the function body (not at
module level), we patch ``"swarms.Agent"`` directly rather than trying to
patch the module-level reference which does not exist until the function runs.
"""

import ast
import inspect
import textwrap
from unittest.mock import MagicMock, patch

import pytest

from heretek_swarm.runtime.main_loop import AutonomousSwarm


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


# ---------------------------------------------------------------------------
# System-prompt coverage tests (M003/S01)
# ---------------------------------------------------------------------------


_ALL_AGENT_IDS: list[str] = [
    # Tier 1: Core Triad (Governance)
    "steward", "alpha", "beta", "charlie",
    # Tier 2: Support Agents (Knowledge & Memory)
    "historian", "metis", "empath", "perceiver", "echo",
    # Tier 3: Exploration Agents (Discovery & Creation)
    "explorer", "examiner", "dreamer", "coder",
    # Tier 4: Safety & Security (Protection)
    "sentinel", "sentinel-prime", "arbiter",
    # Tier 5: Coordination Agents (Integration)
    "coordinator", "nexus", "catalyst", "chronos",
    # Tier 6: Enhancement Agents (Optimization)
    "prism", "habit-forge", "perceiver-plus",
]


def _extract_system_prompts_from_source() -> dict[str, str | None]:
    """Read ``_SYSTEM_PROMPTS`` keys from the ``main_loop.py`` source file.

    Because ``_SYSTEM_PROMPTS`` is a local variable inside an async method,
    we find it by scanning for the dict-literal pattern ``"key": name``
    in the source lines.  This returns a dict keyed by agent ID with a
    dummy value — our tests only care about which IDs exist and whether
    the value is ``None``.
    """
    import re

    source = textwrap.dedent(
        inspect.getsource(AutonomousSwarm._spawn_all_actors)  # noqa: SLF001
    )

    prompts: dict[str, str | None] = {}
    # Look for patterns like:  "historian": _HISTORIAN_SYSTEM_PROMPT,
    in_system_prompts = False
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("_SYSTEM_PROMPTS"):
            in_system_prompts = True
            continue
        if in_system_prompts:
            if stripped == "}":
                break
            # Match:  "key": value_pattern,
            m = re.match(r'^\s*"([^"]+)"\s*:\s*(.+?),?\s*$', stripped)
            if m:
                agent_id = m.group(1)
                value_expr = m.group(2).rstrip(",").strip()
                # If the value is "None" (bare Python None), set to None
                # Otherwise it's a variable reference — treat as non-None
                prompts[agent_id] = None if value_expr == "None" else value_expr

    return prompts


def test_all_23_agent_ids_have_system_prompts() -> None:
    """Every agent ID in ``_ALL_AGENT_IDS`` has a non-``None`` entry in
    ``_SYSTEM_PROMPTS``."""
    prompts = _extract_system_prompts_from_source()

    # Every expected ID must be present
    for agent_id in _ALL_AGENT_IDS:
        assert agent_id in prompts, (
            f"Agent {agent_id!r} is missing from _SYSTEM_PROMPTS"
        )

    # Every entry must be a non-None string (not auto-generated default)
    for agent_id, prompt in prompts.items():
        assert prompt is not None, (
            f"Agent {agent_id!r} has None system_prompt"
        )


def test_all_23_agent_ids_have_exactly_23_prompts() -> None:
    """The ``_SYSTEM_PROMPTS`` dict contains exactly 23 entries, one per
    agent."""
    prompts = _extract_system_prompts_from_source()
    assert len(prompts) == 23, (
        f"Expected exactly 23 system prompts, got {len(prompts)}"
    )


def test_every_agent_gets_system_prompt_through_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Call ``build_agent_for`` for every agent ID with its system prompt
    and verify the ``system_prompt`` kwarg is forwarded to ``Agent(...)``."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    prompts = _extract_system_prompts_from_source()
    from heretek_swarm.agents.agent_factory import build_agent_for

    for agent_id in _ALL_AGENT_IDS:
        prompt = prompts[agent_id]
        mock_cls = _mock_agent_class()
        with patch("swarms.Agent", mock_cls):
            agent = build_agent_for(agent_id, f"{agent_id.title()}Agent", system_prompt=prompt)

        mock_cls.assert_called_once()
        assert mock_cls.call_args.kwargs.get("system_prompt") == prompt, (
            f"system_prompt not forwarded for agent {agent_id!r}"
        )
        assert mock_cls.call_args.kwargs.get("agent_name") == agent_id, (
            f"agent_name mismatch for {agent_id!r}"
        )
        assert agent is mock_cls.return_value
        mock_cls.reset_mock()
