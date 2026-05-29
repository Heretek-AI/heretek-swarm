"""Integration tests for LLM output validation wired through run_with_llm().

Tests both the garage path and swarms_agent fallback path for:
- Dangerous LLM output → ValueError raised with truncated output
- Valid LLM output → response returned unchanged
- Truncated raw output in ValueError message
- _archetype_response fallback pattern

Uses unittest.mock.AsyncMock for Python 3.14 compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]


# ===========================================================================
# Helper: build a minimal AgentActor-like stub with run_with_llm
# ===========================================================================


@dataclass
class FakeLLMResponse:
    """Minimal fake LLMResponse matching the structure used in message_handling."""

    content: str
    model: str = "test-model"
    total_tokens: int = 10
    latency_ms: float = 50.0


class _AgentStub:
    """Minimal stub that mimics an AgentActor with run_with_llm.

    Provides the attributes run_with_llm inspects (agent_id, swarms_agent,
    actor_type) and a mockable model_router with an optional model_garage.
    """

    def __init__(self, agent_id: str = "test-agent", swarms_agent: Any = None) -> None:
        self.agent_id = agent_id
        self.swarms_agent = swarms_agent
        self.actor_type = "test"
        self._model_router: Any = None

    # We monkey-patch run_with_llm from the module after construction.
    # This avoids circular import issues.


def _make_stub_with_garage(
    garage_response: str,
    model: str = "test-model",
    agent_id: str = "test-agent",
) -> _AgentStub:
    """Build a stub with a mock model_garage that returns the given response."""
    stub = _AgentStub(agent_id=agent_id)

    # Build mock garage
    mock_garage = MagicMock()
    mock_garage.complete = AsyncMock(
        return_value=FakeLLMResponse(content=garage_response, model=model)
    )

    # Build mock router
    mock_router = MagicMock()
    mock_router.route.return_value = MagicMock(
        model=model,
        provider_id="mock-provider",
        complexity=MagicMock(value="low"),
        confidence=0.9,
    )
    mock_router._model_garage = mock_garage
    mock_router.record_usage = MagicMock()

    stub._model_router = mock_router
    return stub


def _make_stub_with_swarms_only(swarms_response: str) -> _AgentStub:
    """Build a stub with only a swarms_agent (no router/garage)."""
    mock_agent = MagicMock()
    mock_agent.run.return_value = swarms_response
    return _AgentStub(agent_id="swarms-agent", swarms_agent=mock_agent)


# ===========================================================================
# Tests: garage path validation
# ===========================================================================


class TestGaragePathValidation:
    """Tests for the model_garage code path in run_with_llm."""

    @pytest.mark.asyncio
    async def test_dangerous_output_raises_value_error(self) -> None:
        """When garage returns dangerous output, run_with_llm raises ValueError."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_garage("You should run eval('rm -rf /') to clean up.")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(stub, "test prompt", timeout=10)

    @pytest.mark.asyncio
    async def test_safe_output_returns_unchanged(self) -> None:
        """When garage returns safe output, run_with_llm returns it unchanged."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        safe_text = "This is a safe, well-formed response about system architecture."
        stub = _make_stub_with_garage(safe_text)
        result = await AgentActorMessageHandling.run_with_llm(stub, "test prompt", timeout=10)
        assert result == safe_text

    @pytest.mark.asyncio
    async def test_truncated_output_in_valuerror_message(self) -> None:
        """ValueError message includes truncated raw output from the LLM."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        # Build a long dangerous string so truncation applies
        dangerous = ("Use eval('1+1') for computing. " * 50)[:800]
        stub = _make_stub_with_garage(dangerous)
        with pytest.raises(ValueError) as excinfo:
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)
        error_msg = str(excinfo.value)
        assert "LLM output validation failed" in error_msg
        assert "test-agent" in error_msg

    @pytest.mark.asyncio
    async def test_dangerous_subprocess_output_raises(self) -> None:
        """subprocess patterns in LLM output are caught by validation."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_garage("Call subprocess.run(['cat', '/etc/passwd'])")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)

    @pytest.mark.asyncio
    async def test_dangerous_pickle_output_raises(self) -> None:
        """pickle.loads patterns in LLM output are caught."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_garage("Deserialize with pickle.loads(data)")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)

    @pytest.mark.asyncio
    async def test_os_system_output_raises(self) -> None:
        """os.system patterns in LLM output are caught."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_garage("Execute os.system('rm -rf /')")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)

    @pytest.mark.asyncio
    async def test_path_traversal_output_raises(self) -> None:
        """Path traversal patterns in LLM output are caught."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_garage("Read from ../../../etc/shadow")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)


# ===========================================================================
# Tests: swarms_agent fallback path
# ===========================================================================


class TestSwarmsAgentFallbackPath:
    """Tests for the swarms_agent fallback code path in run_with_llm."""

    @pytest.mark.asyncio
    async def test_safe_output_via_swarms_returns_unchanged(self) -> None:
        """When swarms_agent returns safe output, it is returned unchanged."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        safe = "A thoughtful analysis of the system architecture suggests modular design."
        stub = _make_stub_with_swarms_only(safe)
        result = await AgentActorMessageHandling.run_with_llm(stub, "test prompt", timeout=10)
        assert result == safe

    @pytest.mark.asyncio
    async def test_dangerous_output_via_swarms_raises_value_error(self) -> None:
        """When swarms_agent returns dangerous output, ValueError is raised."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_swarms_only("Call exec('import os; os.system(\"rm -rf /\")')")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)

    @pytest.mark.asyncio
    async def test_dangerous_output_via_swarms_includes_agent_id(self) -> None:
        """ValueError from swarms path includes agent_id."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_swarms_only("Try __import__('os').system('ls')")
        with pytest.raises(ValueError) as excinfo:
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)
        assert "swarms-agent" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_no_llm_path_raises_runtime_error(self) -> None:
        """When neither router nor swarms_agent is available, RuntimeError is raised."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _AgentStub(agent_id="orphan", swarms_agent=None)
        stub._model_router = None
        with pytest.raises(RuntimeError, match="No LLM path available"):
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)

    @pytest.mark.asyncio
    async def test_swarms_agent_truncated_output_in_error(self) -> None:
        """When swarms returns long dangerous output, truncated output appears in error."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        dangerous = "eval('x') " * 200  # Long dangerous text
        stub = _make_stub_with_swarms_only(dangerous)
        with pytest.raises(ValueError) as excinfo:
            await AgentActorMessageHandling.run_with_llm(stub, "test", timeout=10)
        assert "LLM output validation failed" in str(excinfo.value)


# ===========================================================================
# Tests: _archetype_response fallback pattern
# ===========================================================================


class TestArchetypeResponse:
    """Tests for the _archetype_response function used when LLM is unavailable."""

    def test_known_agent_returns_typed_response(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("analyst_agent", "Should we upgrade?")
        assert "analyst" in result.lower() or "Analyzing" in result

    def test_critic_agent_returns_critical_response(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("critic_agent", "Proposal X")
        assert "Critical" in result or "risk" in result.lower() or "caution" in result.lower()

    def test_synthesizer_agent_returns_integration_response(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("synthesizer", "Merge perspectives")
        assert "synthes" in result.lower() or "Integrating" in result or "convergence" in result.lower()

    def test_explorer_agent_returns_exploratory_response(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("explorer", "New directions?")
        assert "explor" in result.lower() or "Novel" in result or "unconventional" in result.lower()

    def test_validator_agent_returns_validation_response(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("validator", "Is this correct?")
        assert "Validating" in result or "consistency" in result.lower() or "aligns" in result.lower()

    def test_steward_agent_returns_governance_response(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("steward", "How to proceed?")
        assert "Steward" in result or "governance" in result.lower() or "deliberation" in result.lower()

    def test_unknown_agent_returns_generic_fallback(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("unknown_xyz", "What now?")
        assert "unknown_xyz" in result
        assert "What now?" in result

    def test_alpha_agent_returns_alpha_response(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("alpha", "Direction?")
        assert "Alpha" in result or "primary" in result.lower()

    def test_historian_agent_returns_historical_context(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        result = _archetype_response("historian", "Past patterns?")
        assert "Historical" in result or "prior deliberation" in result.lower()

    def test_response_includes_prompt(self) -> None:
        from heretek_swarm.api.main import _archetype_response

        prompt = "Should we refactor the auth module?"
        result = _archetype_response("analyst", prompt)
        # Prompt should be referenced in the response
        assert "refactor" in result.lower() or prompt.lower() in result.lower()


# ===========================================================================
# Tests: both paths validate (garage + swarms convergence)
# ===========================================================================


class TestBothPathsValidate:
    """Confirm that both the garage and swarms paths use the single choke point."""

    @pytest.mark.asyncio
    async def test_garage_path_validates(self) -> None:
        """Garage path: safe passes, dangerous fails."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        # Safe
        safe_stub = _make_stub_with_garage("This is safe text.")
        result = await AgentActorMessageHandling.run_with_llm(safe_stub, "prompt", timeout=10)
        assert result == "This is safe text."

        # Dangerous
        bad_stub = _make_stub_with_garage("import os; os.system('ls')")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(bad_stub, "prompt", timeout=10)

    @pytest.mark.asyncio
    async def test_swarms_path_validates(self) -> None:
        """Swarms path: safe passes, dangerous fails."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        # Safe
        safe_stub = _make_stub_with_swarms_only("Safe text from swarms agent.")
        result = await AgentActorMessageHandling.run_with_llm(safe_stub, "prompt", timeout=10)
        assert result == "Safe text from swarms agent."

        # Dangerous
        bad_stub = _make_stub_with_swarms_only("__import__('shutil').rmtree('/')")
        with pytest.raises(ValueError, match="LLM output validation failed"):
            await AgentActorMessageHandling.run_with_llm(bad_stub, "prompt", timeout=10)

    @pytest.mark.asyncio
    async def test_garage_fallback_to_swarms_when_router_fails(self) -> None:
        """When router exists but garage is None, falls back to swarms_agent."""
        from heretek_swarm.actors.base.message_handling import (
            AgentActorMessageHandling,
        )

        stub = _make_stub_with_swarms_only("Safe fallback response.")
        # Add a router with no garage (so raw_response stays None initially)
        mock_router = MagicMock()
        mock_router._model_garage = None  # No garage
        stub._model_router = mock_router

        result = await AgentActorMessageHandling.run_with_llm(stub, "prompt", timeout=10)
        assert result == "Safe fallback response."
