"""Integration tests for ``AutonomousSwarm.run_deliberation()``.

Tests the deliberation flow end-to-end using ``no_infra=True`` mode with
mock agents injected into ``supervisor.actors`` rather than relying on the
full 23-agent ``_spawn_all_actors()`` call.

Key patterns (see MEM020):
- Mock ``swarms.Agent.run()`` via ``MagicMock`` for fast LLM bypass
- Inject mock results directly into per-agent dict attributes
  (``analysis_history``, ``_analyses``, ``_challenges``) to skip mailbox
  processing when testing result-reading logic
- Use ``get_supervisor().actors.update()`` for global registry setup only
  when testing the full code path
- ``conftest`` autouse fixture clears ``get_supervisor().actors`` after
  every test to prevent singleton state leaking
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from heretek_swarm.actors.triad.agent import AlphaAgent, BetaAgent, CharlieAgent, StewardAgent
from heretek_swarm.runtime.main_loop import AutonomousSwarm


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunDeliberation:
    """Integration tests for ``AutonomousSwarm.run_deliberation()``."""

    # ------------------------------------------------------------------
    # Test 1: All three agents present with pre-injected state
    # ------------------------------------------------------------------

    @staticmethod
    async def test_all_three_agents_return_results() -> None:
        """``run_deliberation`` returns a dict with keys ``alpha``,
        ``beta``, ``charlie`` when all three triad agents are in
        ``supervisor.actors`` with pre-injected state attributes."""
        swarm = AutonomousSwarm(no_infra=True)
        await swarm.initialize()
        swarm.supervisor.actors.clear()

        # Pre-injected state — no mailbox processing needed.
        # run_deliberation reads alpha.analysis_history (list, last 3),
        # beta._analyses (dict values, last 3), and
        # charlie._challenges (dict values, last 3).
        steward = MagicMock(spec=StewardAgent)
        steward.coordinate_triad = AsyncMock(return_value="delib-001")

        alpha = MagicMock()
        alpha.analysis_history = [{"decision": "alpha_first_pass"}]

        beta = MagicMock()
        beta._analyses = {"delib-001": {"analysis": {"decision": "beta_second_pass"}}}

        charlie = MagicMock()
        charlie._challenges = {"delib-001": {"challenges": ["red_flag_detected"]}}

        swarm.supervisor.actors.update({
            "steward": steward,
            "alpha": alpha,
            "beta": beta,
            "charlie": charlie,
        })

        result = await swarm.run_deliberation("test prompt", timeout=0.01)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"alpha", "beta", "charlie"}
        assert result["alpha"]["analyses"] == [{"decision": "alpha_first_pass"}]
        # run_deliberation reads beta._analyses values — each value is a
        # dict that wraps the analysis under an "analysis" key
        assert result["beta"]["analyses"] == [
            {"analysis": {"decision": "beta_second_pass"}},
        ]
        # run_deliberation reads charlie._challenges values — each value
        # contains "challenges" inside the entry dict
        assert result["charlie"]["challenges"] == [
            {"challenges": ["red_flag_detected"]},
        ]

    # ------------------------------------------------------------------
    # Test 2: One agent missing — partial results
    # ------------------------------------------------------------------

    @staticmethod
    async def test_returns_partial_results_when_agent_missing() -> None:
        """When ``beta`` is absent from ``supervisor.actors`` the result
        dict includes an ``error`` entry for ``beta`` while ``alpha`` and
        ``charlie`` still contain their data."""
        swarm = AutonomousSwarm(no_infra=True)
        await swarm.initialize()
        swarm.supervisor.actors.clear()

        steward = MagicMock(spec=StewardAgent)
        steward.coordinate_triad = AsyncMock(return_value="delib-002")

        alpha = MagicMock()
        alpha.analysis_history = [{"decision": "alpha_ok"}]

        # beta deliberately absent

        charlie = MagicMock()
        charlie._challenges = {"delib-002": {"challenges": ["issue_found"]}}

        swarm.supervisor.actors.update({
            "steward": steward,
            "alpha": alpha,
            "charlie": charlie,
        })

        result = await swarm.run_deliberation("test prompt", timeout=0.01)

        assert "alpha" in result
        assert "beta" in result
        assert "charlie" in result
        assert result["beta"] == {"error": "Agent beta not found"}
        assert result["alpha"]["analyses"] == [{"decision": "alpha_ok"}]
        # run_deliberation reads charlie._challenges values — each value
        # is the full entry dict containing challenges
        assert result["charlie"]["challenges"] == [
            {"challenges": ["issue_found"]},
        ]

    # ------------------------------------------------------------------
    # Test 3: Steward missing raises RuntimeError
    # ------------------------------------------------------------------

    @staticmethod
    async def test_raises_runtime_error_when_steward_missing() -> None:
        """When ``steward`` is absent from ``supervisor.actors``,
        ``run_deliberation`` raises ``RuntimeError`` immediately."""
        swarm = AutonomousSwarm(no_infra=True)
        await swarm.initialize()
        swarm.supervisor.actors.clear()

        # Only triad members, no steward
        swarm.supervisor.actors.update({
            "alpha": MagicMock(),
            "beta": MagicMock(),
            "charlie": MagicMock(),
        })

        with pytest.raises(RuntimeError, match="Steward agent not found"):
            await swarm.run_deliberation("test prompt")

    # ------------------------------------------------------------------
    # Test 4: Full code path with real agents and mocked swarms_agent
    # ------------------------------------------------------------------

    @staticmethod
    async def test_full_code_path_with_real_mock_agents() -> None:
        """With real ``TriadAgent`` instances, the full code path through
        ``run_deliberation`` runs without error.

        ``run_deliberation`` calls ``steward.coordinate_triad()`` which is
        a real method on the real ``StewardAgent`` — it calls ``send()`` to
        route a message to triad members.  In ``no_infra`` mode the message
        is queued but delivery to the event mesh or the registry actor
        fails silently (no NATS, no direct delivery).  The method still
        returns a result dict with the correct structure because
        ``coordinate_triad`` returns a deliberation_id and the result
        reader handles missing/empty state gracefully.

        This test verifies that:
        1. ``run_deliberation`` completes without raising.
        2. The result dict contains all three expected keys.
        3. The ``steerard`` was called via ``coordinate_triad`` — we
           verify the deliberation was recorded in
           ``steward.active_deliberations``.
        """
        swarm = AutonomousSwarm(no_infra=True)
        await swarm.initialize()
        swarm.supervisor.actors.clear()

        # Create real agent instances
        steward = StewardAgent(agent_id="steward")
        alpha = AlphaAgent(agent_id="alpha")
        beta = BetaAgent(agent_id="beta")
        charlie = CharlieAgent(agent_id="charlie")

        # Mock swarms_agent on each so run_with_llm returns instantly
        mock_swarms = MagicMock()
        mock_swarms.run = AsyncMock(return_value="mock LLM response")
        steward.swarms_agent = mock_swarms
        alpha.swarms_agent = mock_swarms
        beta.swarms_agent = mock_swarms
        charlie.swarms_agent = mock_swarms

        # Register in supervisor's actors dict
        swarm.supervisor.actors.update({
            "steward": steward,
            "alpha": alpha,
            "beta": beta,
            "charlie": charlie,
        })

        result = await swarm.run_deliberation(
            "test problem for full path",
            timeout=0.01,
        )

        assert isinstance(result, dict)
        assert "alpha" in result
        assert "beta" in result
        assert "charlie" in result

        # The deliberation was recorded on the real steward
        assert len(steward.active_deliberations) > 0

        # Agent state is empty because the async message chain doesn't
        # process within the tiny timeout — the mailbox processing loop
        # runs but message delivery fails silently (no event mesh).
        # The method still returns gracefully with empty result entries.
        assert result["alpha"]["analyses"] == []
        assert result["beta"]["analyses"] == []
        assert result["charlie"]["challenges"] == []
