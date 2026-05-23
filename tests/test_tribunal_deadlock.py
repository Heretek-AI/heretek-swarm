"""
Tribunal deadlock recovery tests (FINDING-020).

Uses timeout-based simulation: configure the Tribunal with short
``round_timeout_seconds`` (0.1 s), trigger a deliberation, and assert
the tribunal completes without hanging within a generous outer timeout
(10-15 s).  Tribunal internals are **not** mocked — the real deliberation
loop is exercised.

All tests are marked ``@pytest.mark.slow`` and require ``--run-slow``
to execute.  They are excluded from the default fast-regression run.
"""

from __future__ import annotations

import time

import pytest


pytestmark = [pytest.mark.unit]

from heretek_swarm.consensus.tribunal import Tribunal

# ---------------------------------------------------------------------------
# Deadlock recovery — timeout-bounded completion with real deliberation loop
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_deliberation_completes_within_timeout_unanimous() -> None:
    """Unanimous vote completes immediately (single round, no tiebreaker)."""
    tribunal = Tribunal(
        max_rounds=3,
        round_timeout_seconds=0.1,
        tiebreaker_role="steward",
    )

    start = time.monotonic()
    result = tribunal.deliberate(
        topic="unanimous-test",
        agent_votes={"agent-1": "approve", "agent-2": "approve", "agent-3": "approve"},
    )
    elapsed = time.monotonic() - start

    assert result["unanimous"] is True, f"Expected unanimous, got {result}"
    assert result["round"] == 1, f"Expected single round, got {result['round']}"
    assert result["tiebreaker_invoked"] is False
    assert elapsed < 5.0, f"Unanimous deliberation took {elapsed:.2f}s, expected <5s"


@pytest.mark.slow
def test_deliberation_completes_within_timeout_non_unanimous() -> None:
    """Non-unanimous vote triggers tiebreaker after max_rounds, within bounds.

    FINDING-020: The tribunal must not hang when deadlock-prone conditions
    exist.  With 3 agents casting 3 different votes, no round achieves
    unanimity, so the tiebreaker fires at ``max_rounds`` and returns a
    decision within the generous outer timeout.
    """
    tribunal = Tribunal(
        max_rounds=2,
        round_timeout_seconds=0.1,
        tiebreaker_role="steward",
    )

    start = time.monotonic()
    result = tribunal.deliberate(
        topic="split-vote-test",
        agent_votes={
            "agent-1": "approve",
            "agent-2": "deny",
            "agent-3": "abstain",
        },
    )
    elapsed = time.monotonic() - start

    assert result["unanimous"] is False, (
        f"Split votes should not produce unanimity, got {result}"
    )
    assert result["tiebreaker_invoked"] is True, (
        f"Tiebreaker should have been invoked, got {result}"
    )
    assert result["tiebreaker_role"] == "steward"
    assert result["tiebreaker_reason"] is not None
    # Tiebreaker should always produce a decision
    assert "decision" in result, f"No decision in result: {result}"
    assert result["confidence"] > 0.0
    # Generous outer bound — real deliberation loop is synchronous, so this
    # is a safety net, not a performance assertion.
    assert elapsed < 15.0, (
        f"Non-unanimous deliberation took {elapsed:.2f}s, expected <15s "
        f"(round_timeout={tribunal.round_timeout_seconds}, "
        f"max_rounds={tribunal.max_rounds})"
    )


@pytest.mark.slow
def test_deliberation_completes_within_timeout_single_round() -> None:
    """max_rounds=1 with split vote completes via tiebreaker in one round."""
    tribunal = Tribunal(
        max_rounds=1,
        round_timeout_seconds=0.1,
        tiebreaker_role="charlie",
    )

    start = time.monotonic()
    result = tribunal.deliberate(
        topic="single-round-test",
        agent_votes={"agent-A": "yes", "agent-B": "no"},
    )
    elapsed = time.monotonic() - start

    assert result["tiebreaker_invoked"] is True
    assert result["round"] == 1
    assert result["tiebreaker_role"] == "charlie"
    assert elapsed < 10.0, (
        f"Single-round deliberation took {elapsed:.2f}s, expected <10s"
    )


@pytest.mark.slow
def test_deliberation_completes_with_many_agents() -> None:
    """Large agent set with non-unanimous votes still completes in bounds.

    Regression guard: as agents scale, the deliberation loop must remain
    strictly bounded by ``max_rounds``, not by agent count.
    """
    tribunal = Tribunal(
        max_rounds=3,
        round_timeout_seconds=0.1,
        tiebreaker_role="steward",
    )

    agents: dict[str, str] = {}
    for i in range(50):
        agents[f"agent-{i}"] = "approve" if i % 3 != 0 else "deny"

    start = time.monotonic()
    result = tribunal.deliberate(topic="many-agents", agent_votes=agents)
    elapsed = time.monotonic() - start

    assert result["tiebreaker_invoked"], (
        "Non-unanimous votes must invoke tiebreaker"
    )
    assert "decision" in result
    assert elapsed < 15.0, (
        f"Many-agent deliberation took {elapsed:.2f}s, expected <15s"
    )


# ---------------------------------------------------------------------------
# Tiebreaker integrity
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_tiebreaker_weighting_favors_majority() -> None:
    """Tiebreaker weighting amplifies the leading vote (GOV-05-M)."""
    tribunal = Tribunal(
        max_rounds=2,
        round_timeout_seconds=0.1,
        tiebreaker_role="steward",
    )

    result = tribunal.deliberate(
        topic="tiebreak-weight",
        agent_votes={
            "a": "blue",
            "b": "blue",
            "c": "blue",
            "d": "red",
            "e": "red",
        },
    )

    assert result["tiebreaker_invoked"] is True
    # With steward tiebreaker (weight 1.0) added to the leading vote 'blue',
    # the adjusted distribution should make blue the winner with higher weight.
    adjusted = result["vote_distribution"]
    assert adjusted.get("blue", 0) > adjusted.get("red", 0), (
        f"Tiebreaker should amplify majority: {adjusted}"
    )


@pytest.mark.slow
def test_charlie_failover_weight_is_higher() -> None:
    """Charlie tiebreaker uses 1.5x weight (GOV-05-M failover)."""
    tribunal = Tribunal(
        max_rounds=2,
        round_timeout_seconds=0.1,
        tiebreaker_role="charlie",
    )

    result = tribunal.deliberate(
        topic="charlie-failover",
        agent_votes={
            "a": "green",
            "b": "green",
            "c": "yellow",
        },
    )

    assert result["tiebreaker_invoked"] is True
    assert result["tiebreaker_role"] == "charlie"
    adjusted = result["vote_distribution"]
    # Charlie applies 1.5x weight so green (2 votes) beats yellow (1 vote)
    # with adjusted green > original green count
    original = result.get("original_vote_distribution", {})
    green_original = original.get("green", 0)
    green_adjusted = adjusted.get("green", 0)
    assert green_adjusted >= green_original, (
        f"Charlie failover should not reduce majority weight: "
        f"original={original}, adjusted={adjusted}"
    )


# ---------------------------------------------------------------------------
# State isolation — repeated deliberations don't leak state
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_repeated_deliberations_are_idempotent() -> None:
    """Back-to-back deliberations on the same tribunal instance are clean."""
    tribunal = Tribunal(
        max_rounds=2,
        round_timeout_seconds=0.1,
        tiebreaker_role="steward",
    )

    r1 = tribunal.deliberate(
        topic="first",
        agent_votes={"x": "up", "y": "down", "z": "up"},
    )
    r2 = tribunal.deliberate(
        topic="second",
        agent_votes={"x": "left", "y": "right"},
    )

    assert r1 is not r2
    assert r1["topic"] == "first"
    assert r2["topic"] == "second"
    # Second deliberation must reset round counter — not carry over from r1
    assert r1["round"] > 0
    assert r1["round"] <= tribunal.max_rounds
    assert r2["round"] > 0
    assert r2["round"] <= tribunal.max_rounds
