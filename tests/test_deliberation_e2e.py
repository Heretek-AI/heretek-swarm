"""End-to-end contract tests for the deliberation orchestration flow.

Covers the full Alpha → Beta → Charlie → Coder chain with real agent
instances, polling early-return behaviour, specialist-handoff verification,
and structlog signal auditing.

Design decisions (see S04-PLAN.md, S04/T04-PLAN.md):
- Real ``TriadAgent`` / ``CoderAgent`` instances are used (not MagicMock)
  so that type contracts and attribute shapes match production.
- State is **pre-injected** into per-agent dict attributes
  (``analysis_history``, ``_analyses``, ``_challenges``, ``_tasks``,
  ``_task_counter``) so the polling loop finds results immediately
  without requiring spawned mailbox-processing tasks (which pull in
  aiohttp heartbeat loops that are hard to clean up).
- ``coordinate_triad`` and ``route_to_agent`` are mocked on the Steward
  instance so the orchestrator sees the expected return values without
  exercising the full topic-routing message chain.
- The conftest autouse fixture clears ``get_supervisor().actors`` after
  every test.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = [pytest.mark.unit]

from structlog.testing import capture_logs

from heretek_swarm.actors.coder.agent import CoderAgent
from heretek_swarm.actors.supervisor import get_supervisor
from heretek_swarm.actors.triad.agent import (
    AlphaAgent,
    BetaAgent,
    CharlieAgent,
    StewardAgent,
)
from heretek_swarm.runtime.main_loop import AutonomousSwarm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _teardown_swarm(swarm: AutonomousSwarm) -> None:
    """Terminate all actors and clear both supervisor and global registries."""
    if swarm.supervisor is not None:
        await swarm.supervisor.terminate_all()
    swarm.supervisor.actors.clear()
    get_supervisor().actors.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTriadDeliberationWithRealAgents:
    """End-to-end triad deliberation with real agent instances."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_triad_deliberation_with_real_agents() -> None:
        """All 3 triad agents produce results within timeout with mocked LLM.

        ``run_deliberation()`` returns a dict with ``alpha``, ``beta``,
        ``charlie`` keys and non-empty results when the agents have
        pre-injected state attributes.
        """
        swarm = AutonomousSwarm(no_infra=True)
        try:
            await swarm.initialize()
            swarm.supervisor.actors.clear()
            get_supervisor().actors.clear()

            steward = StewardAgent(agent_id="steward")
            alpha = AlphaAgent(agent_id="alpha")
            beta = BetaAgent(agent_id="beta")
            charlie = CharlieAgent(agent_id="charlie")

            # Mock run_with_llm for fast LLM bypass (called by _perform_analysis
            # if messages were actually being processed through the mailbox).
            mock_llm = AsyncMock(return_value="Mock analysis result from e2e test")
            steward.run_with_llm = mock_llm  # type: ignore[assignment]
            alpha.run_with_llm = mock_llm  # type: ignore[assignment]
            beta.run_with_llm = mock_llm  # type: ignore[assignment]
            charlie.run_with_llm = mock_llm  # type: ignore[assignment]

            # Mock coordinate_triad so we don't need spawned agent mailboxes.
            steward.coordinate_triad = AsyncMock(  # type: ignore[method-assign]
                return_value={"session_id": "delib-e2e-001"}
            )

            # Pre-inject state — what the agents' mailbox handlers would
            # have populated after processing messages (avoids requiring
            # spawned _process_mailbox tasks with aiohttp heartbeat loops).
            alpha.analysis_history = [  # type: ignore[attr-defined]
                {"decision": "build_string_reverser", "confidence": 0.92}
            ]
            beta._analyses = {  # type: ignore[attr-defined]
                "delib-e2e-001": {
                    "analysis": {"decision": "validated_approach", "confidence": 0.88}
                }
            }
            charlie._challenges = {  # type: ignore[attr-defined]
                "delib-e2e-001": {
                    "challenges": ["check_edge_cases", "verify_performance"]
                }
            }

            swarm.supervisor.actors.update(
                {
                    "steward": steward,
                    "alpha": alpha,
                    "beta": beta,
                    "charlie": charlie,
                }
            )

            result = await swarm.run_deliberation(
                "Write a Python function that reverses a string",
                timeout=2,
            )

            # Verify all three triad keys present with non-empty results.
            assert isinstance(result, dict)
            assert set(result.keys()) == {"alpha", "beta", "charlie"}
            assert len(result["alpha"]["analyses"]) > 0
            assert len(result["beta"]["analyses"]) > 0
            assert len(result["charlie"]["challenges"]) > 0
            assert result["alpha"]["analyses"][0]["decision"] == "build_string_reverser"
            assert (
                result["beta"]["analyses"][0]["analysis"]["decision"]
                == "validated_approach"
            )
            assert "check_edge_cases" in result["charlie"]["challenges"][0]["challenges"]
        finally:
            await _teardown_swarm(swarm)


class TestPollingReturnsEarly:
    """Verify polling (not sleep) is the wait mechanism."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_polling_returns_early() -> None:
        """All agents have pre-set state; ``run_deliberation`` returns in
        well under the full 120 s timeout, proving polling is the mechanism."""
        swarm = AutonomousSwarm(no_infra=True)
        try:
            await swarm.initialize()
            swarm.supervisor.actors.clear()
            get_supervisor().actors.clear()

            steward = StewardAgent(agent_id="steward")
            steward.coordinate_triad = AsyncMock(  # type: ignore[method-assign]
                return_value={"session_id": "delib-early"}
            )

            alpha = AlphaAgent(agent_id="alpha")
            alpha.analysis_history = [{"decision": "ready_now"}]  # type: ignore[attr-defined]

            beta = BetaAgent(agent_id="beta")
            beta._analyses = {"delib-early": {"analysis": {"decision": "valid"}}}  # type: ignore[attr-defined]

            charlie = CharlieAgent(agent_id="charlie")
            charlie._challenges = {"delib-early": {"challenges": ["none"]}}  # type: ignore[attr-defined]

            swarm.supervisor.actors.update(
                {
                    "steward": steward,
                    "alpha": alpha,
                    "beta": beta,
                    "charlie": charlie,
                }
            )

            start = time.monotonic()
            result = await swarm.run_deliberation(
                "test polling early return",
                timeout=120,
            )
            elapsed = time.monotonic() - start

            # The polling loop sleeps 0.5 s on the first iteration, then
            # discovers all state is ready and breaks.  Total wall-clock
            # should be well under 5 s — proving it's polling, not sleeping
            # the full 120 s.
            assert elapsed < 5.0, (
                f"Expected early return (polling), but took {elapsed:.2f}s"
            )
            assert "alpha" in result
            assert "beta" in result
            assert "charlie" in result
            assert len(result["alpha"]["analyses"]) > 0
        finally:
            await _teardown_swarm(swarm)


class TestSpecialistHandoffTriggersCoder:
    """Verify the specialist-handoff path from triad results to Coder."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_specialist_handoff_triggers_coder() -> None:
        """After triad completes, Coder's ``_process_route_task`` is invoked
        with ``implement_task`` type.  ``specialist_output`` key appears in
        results with code, tests, and documentation."""
        swarm = AutonomousSwarm(no_infra=True)
        try:
            await swarm.initialize()
            swarm.supervisor.actors.clear()
            get_supervisor().actors.clear()

            steward = StewardAgent(agent_id="steward")
            steward.coordinate_triad = AsyncMock(  # type: ignore[method-assign]
                return_value={"session_id": "delib-handoff"}
            )

            alpha = AlphaAgent(agent_id="alpha")
            alpha.analysis_history = [  # type: ignore[attr-defined]
                {"decision": "build_string_reverser", "analysis": "Reverse string utility"}
            ]

            beta = BetaAgent(agent_id="beta")
            beta._analyses = {"delib-handoff": {"analysis": {"decision": "approved"}}}  # type: ignore[attr-defined]

            charlie = CharlieAgent(agent_id="charlie")
            charlie._challenges = {"delib-handoff": {"challenges": ["test_edge_cases"]}}  # type: ignore[attr-defined]

            coder = CoderAgent(agent_id="coder")
            coder._task_counter = 0  # type: ignore[attr-defined]
            # Pre-populate _tasks with a completed task so the polling
            # loop finds it after _task_counter increments.
            from heretek_swarm.actors.coder.types import ImplementationTask

            task = ImplementationTask(
                id="task_handoff_1",
                description="Reverse string utility",
                requirements=["Python function", "Handle empty string"],
                language="python",
                status="completed",
                generated_code="def reverse(s): return s[::-1]",
                tests="def test_reverse(): assert reverse('abc') == 'cba'",
                documentation="Reverse a string.",
            )
            coder._tasks = {"task_handoff_1": task}  # type: ignore[attr-defined]

            # Mock route_to_agent: increment _task_counter so the poll
            # loop detects completion.
            async def _fake_route(**kwargs: object) -> str:
                coder._task_counter += 1  # type: ignore[attr-defined]
                return "msg-handoff-001"

            steward.route_to_agent = AsyncMock(side_effect=_fake_route)  # type: ignore[method-assign]

            swarm.supervisor.actors.update(
                {
                    "steward": steward,
                    "alpha": alpha,
                    "beta": beta,
                    "charlie": charlie,
                    "coder": coder,
                }
            )

            result = await swarm.run_deliberation(
                "Write a Python function that reverses a string",
                timeout=30,
            )

            # Assert specialist_output is present with real code.
            assert "specialist_output" in result
            specialist = result["specialist_output"]
            assert specialist["task_id"] == "task_handoff_1"
            assert specialist["status"] == "completed"
            assert "reverse" in specialist["code"]
            assert specialist["tests"] is not None
            assert specialist["documentation"] is not None

            # Triad results also returned.
            assert "alpha" in result
            assert "beta" in result
            assert "charlie" in result
        finally:
            await _teardown_swarm(swarm)


class TestStructuredLogSignals:
    """Verify structured log signals emitted during deliberation."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_structured_log_signals() -> None:
        """``capture_logs`` captures:
        ``deliberation_polling``,
        ``deliberation_all_agents_complete``,
        ``specialist_handoff_initiated``,
        ``specialist_handoff_complete``."""
        swarm = AutonomousSwarm(no_infra=True)
        try:
            await swarm.initialize()
            swarm.supervisor.actors.clear()
            get_supervisor().actors.clear()

            steward = StewardAgent(agent_id="steward")
            steward.coordinate_triad = AsyncMock(  # type: ignore[method-assign]
                return_value={"session_id": "delib-sig"}
            )

            alpha = AlphaAgent(agent_id="alpha")
            alpha.analysis_history = [{"decision": "signal_test"}]  # type: ignore[attr-defined]

            beta = BetaAgent(agent_id="beta")
            beta._analyses = {"delib-sig": {"analysis": {"decision": "ok"}}}  # type: ignore[attr-defined]

            charlie = CharlieAgent(agent_id="charlie")
            charlie._challenges = {"delib-sig": {"challenges": ["check"]}}  # type: ignore[attr-defined]

            coder = CoderAgent(agent_id="coder")
            coder._task_counter = 0  # type: ignore[attr-defined]

            from heretek_swarm.actors.coder.types import ImplementationTask

            task = ImplementationTask(
                id="task_sig_1",
                description="Signal test task",
                requirements=[],
                language="python",
                status="completed",
                generated_code="print('hello')",
            )
            coder._tasks = {"task_sig_1": task}  # type: ignore[attr-defined]

            async def _fake_route(**kwargs: object) -> str:
                coder._task_counter += 1  # type: ignore[attr-defined]
                return "msg-sig-001"

            steward.route_to_agent = AsyncMock(side_effect=_fake_route)  # type: ignore[method-assign]

            swarm.supervisor.actors.update(
                {
                    "steward": steward,
                    "alpha": alpha,
                    "beta": beta,
                    "charlie": charlie,
                    "coder": coder,
                }
            )

            with capture_logs() as cap:
                await swarm.run_deliberation(
                    "Write a Python function that reverses a string",
                    timeout=30,
                )

            # Collect log event names.
            events = [e.get("event", "") for e in cap]

            # Verify required signals.
            assert any("deliberation_polling" in ev for ev in events), (
                f"Missing deliberation_polling in {events}"
            )
            assert any("deliberation_all_agents_complete" in ev for ev in events), (
                f"Missing deliberation_all_agents_complete in {events}"
            )
            assert any("specialist_handoff_initiated" in ev for ev in events), (
                f"Missing specialist_handoff_initiated in {events}"
            )
            assert any("specialist_handoff_complete" in ev for ev in events), (
                f"Missing specialist_handoff_complete in {events}"
            )
        finally:
            await _teardown_swarm(swarm)


class TestNoInfraPath:
    """Verify the flow works without NATS (StubEventMesh only)."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_no_infra_path() -> None:
        """``no_infra=True`` mode completes deliberation without NATS."""
        swarm = AutonomousSwarm(no_infra=True)
        try:
            await swarm.initialize()
            swarm.supervisor.actors.clear()
            get_supervisor().actors.clear()

            steward = StewardAgent(agent_id="steward")
            steward.coordinate_triad = AsyncMock(  # type: ignore[method-assign]
                return_value={"session_id": "delib-noinfra"}
            )

            alpha = AlphaAgent(agent_id="alpha")
            alpha.analysis_history = [{"decision": "noinfra_test"}]  # type: ignore[attr-defined]

            beta = BetaAgent(agent_id="beta")
            beta._analyses = {"delib-noinfra": {"analysis": {"decision": "ok"}}}  # type: ignore[attr-defined]

            charlie = CharlieAgent(agent_id="charlie")
            charlie._challenges = {"delib-noinfra": {"challenges": ["check"]}}  # type: ignore[attr-defined]

            swarm.supervisor.actors.update(
                {
                    "steward": steward,
                    "alpha": alpha,
                    "beta": beta,
                    "charlie": charlie,
                }
            )

            result = await swarm.run_deliberation(
                "test no-infra path",
                timeout=2,
            )

            assert isinstance(result, dict)
            assert set(result.keys()) == {"alpha", "beta", "charlie"}
            assert len(result["alpha"]["analyses"]) > 0
            assert result["alpha"]["analyses"][0]["decision"] == "noinfra_test"
        finally:
            await _teardown_swarm(swarm)


class TestPartialResultsOnMissingAgent:
    """Graceful degradation when a triad member is absent."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_partial_results_on_missing_agent() -> None:
        """When Beta is missing, return partial results without crashing —
        ``alpha`` and ``charlie`` still contain their data, ``beta`` gets
        an error entry."""
        swarm = AutonomousSwarm(no_infra=True)
        try:
            await swarm.initialize()
            swarm.supervisor.actors.clear()
            get_supervisor().actors.clear()

            steward = StewardAgent(agent_id="steward")
            steward.coordinate_triad = AsyncMock(  # type: ignore[method-assign]
                return_value={"session_id": "delib-partial"}
            )

            alpha = AlphaAgent(agent_id="alpha")
            alpha.analysis_history = [{"decision": "alpha_only"}]  # type: ignore[attr-defined]

            charlie = CharlieAgent(agent_id="charlie")
            charlie._challenges = {  # type: ignore[attr-defined]
                "delib-partial": {"challenges": ["solo_check"]}
            }

            # Beta intentionally absent.
            swarm.supervisor.actors.update(
                {
                    "steward": steward,
                    "alpha": alpha,
                    "charlie": charlie,
                }
            )

            result = await swarm.run_deliberation(
                "test partial results",
                timeout=2,
            )

            assert "alpha" in result
            assert "beta" in result
            assert "charlie" in result
            assert result["beta"] == {"error": "Agent beta not found"}
            assert result["alpha"]["analyses"] == [{"decision": "alpha_only"}]
            assert len(result["charlie"]["challenges"]) > 0
        finally:
            await _teardown_swarm(swarm)


class TestHandoffBestEffortWhenCoderMissing:
    """Graceful specialist-handoff degradation when Coder is absent."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_handoff_best_effort_when_coder_missing() -> None:
        """When Coder is absent from the registry, ``specialist_handoff_failed``
        is logged and triad results are returned without ``specialist_output``."""
        swarm = AutonomousSwarm(no_infra=True)
        try:
            await swarm.initialize()
            swarm.supervisor.actors.clear()
            get_supervisor().actors.clear()

            steward = StewardAgent(agent_id="steward")
            steward.coordinate_triad = AsyncMock(  # type: ignore[method-assign]
                return_value={"session_id": "delib-nocoder"}
            )

            alpha = AlphaAgent(agent_id="alpha")
            alpha.analysis_history = [{"decision": "triad_only"}]  # type: ignore[attr-defined]

            beta = BetaAgent(agent_id="beta")
            beta._analyses = {  # type: ignore[attr-defined]
                "delib-nocoder": {"analysis": {"decision": "validated"}}
            }

            charlie = CharlieAgent(agent_id="charlie")
            charlie._challenges = {  # type: ignore[attr-defined]
                "delib-nocoder": {"challenges": ["red_flag"]}
            }

            # Coder intentionally absent.
            swarm.supervisor.actors.update(
                {
                    "steward": steward,
                    "alpha": alpha,
                    "beta": beta,
                    "charlie": charlie,
                }
            )

            with capture_logs() as cap:
                result = await swarm.run_deliberation(
                    "test handoff without Coder",
                    timeout=2,
                )

            # Verify no specialist_output.
            assert "specialist_output" not in result
            assert "alpha" in result
            assert "beta" in result
            assert "charlie" in result
            assert result["alpha"]["analyses"][0]["decision"] == "triad_only"

            # Verify the failure signal was logged.
            events = [e.get("event", "") for e in cap]
            assert any("specialist_handoff_failed" in ev for ev in events), (
                f"Expected specialist_handoff_failed log, got: {events}"
            )
        finally:
            await _teardown_swarm(swarm)
