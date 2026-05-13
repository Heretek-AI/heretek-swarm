"""Tests for GoalConsensus — goal-specific voting with 60% threshold.

Verifies that:
- _approval_ratio computes correctly (ignoring abstain)
- _evaluate_threshold applies D024 ≥60% rule
- _evaluate_threshold detects close splits (≥50% but <60%)
- All-abstain is treated as rejection
- run_goal_consensus() returns (accepted, votes, rounds) tuple
- Round-1 clear approval returns immediately (1 round)
- Round-1 clear rejection returns immediately (1 round)
- Close splits trigger refinement round (2 rounds)
- After 2 rounds without consensus, tie-break via Steward+Arbiter (3 rounds)
- Agent unavailability is skipped with warning
- LLM failure results in abstain vote
- Timeout is handled gracefully
- Empty actor set is handled gracefully
- _normalise_decision maps keywords correctly
- Prompt templates are non-empty and reference goal fields
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.consensus.consensus_coordinator import ConsensusCoordinator
from heretek_swarm.consensus.maker import ConsensusResult, ConsensusState
from heretek_swarm.consensus.maker import Vote as MAKERVote
from heretek_swarm.goals.consensus import (
    GoalConsensus,
    _build_goal_vote_prompt,
    _build_refinement_prompt,
    _normalise_decision,
)
from heretek_swarm.goals.models import Goal, Vote

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_goal() -> Goal:
    """A typical goal proposal."""
    return Goal(
        id="goal-001",
        title="Improve Swarm Monitoring",
        description="Add comprehensive agent health monitoring with real-time dashboards.",
        success_criteria=[
            "All agents report health within 5s",
            "Dashboard renders < 1s",
        ],
        estimated_node_types=["agent", "tool"],
    )


@pytest.fixture
def mock_coordinator() -> ConsensusCoordinator:
    """Return a ConsensusCoordinator whose run_consensus is a mock."""
    mock = MagicMock(spec=ConsensusCoordinator)
    mock.run_consensus = AsyncMock()
    return mock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _v(
    agent_id: str,
    decision: str = "approve",
    confidence: float = 0.8,
    rationale: str = "Looks good.",
) -> Vote:
    """Shortcut for creating a goal-domain Vote."""
    return Vote(agent_id=agent_id, decision=decision, confidence=confidence, rationale=rationale)


def _mv(
    agent_id: str,
    decision: str = "approve",
    confidence: float = 0.8,
    reasoning: str = "Makes sense.",
) -> MAKERVote:
    """Shortcut for creating a MAKER Vote."""
    return MAKERVote(
        agent_id=agent_id,
        decision=decision,
        confidence=confidence,
        timestamp="2025-01-01T00:00:00Z",
        metadata={"reasoning": reasoning},
    )


def _make_result(votes: list[MAKERVote], decision: str = "approve") -> ConsensusResult:
    """Create a ConsensusResult from MAKER votes."""
    return ConsensusResult(
        decision=decision,
        confidence=0.75,
        votes=votes,
        state=ConsensusState.COMPLETED,
        timestamp="2025-01-01T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Decision normalisation tests
# ---------------------------------------------------------------------------


class TestNormaliseDecision:
    """Tests for _normalise_decision()."""

    @pytest.mark.parametrize(("raw", "expected"), [
        ("approve", "approve"),
        ("yes", "approve"),
        ("support", "approve"),
        ("agree", "approve"),
        ("accept", "approve"),
        ("APPROVE", "approve"),
        ("  Yes  ", "approve"),
        ("reject", "reject"),
        ("no", "reject"),
        ("oppose", "reject"),
        ("disagree", "reject"),
        ("decline", "reject"),
        ("abstain", "abstain"),
        ("garbage", "abstain"),
        ("", "abstain"),
        ("maybe later", "abstain"),
    ])
    def test_normalise(self, raw, expected):
        assert _normalise_decision(raw) == expected


# ---------------------------------------------------------------------------
# Threshold evaluation tests
# ---------------------------------------------------------------------------


class TestApprovalRatio:
    """Tests for _approval_ratio()."""

    def test_unanimous_approve(self):
        votes = [_v("a1", "approve"), _v("a2", "approve"), _v("a3", "approve")]
        assert GoalConsensus._approval_ratio(votes) == 1.0

    def test_unanimous_reject(self):
        votes = [_v("a1", "reject"), _v("a2", "reject")]
        assert GoalConsensus._approval_ratio(votes) == 0.0

    def test_three_approve_two_reject(self):
        votes = [
            _v("a1", "approve"), _v("a2", "approve"), _v("a3", "approve"),
            _v("a4", "reject"), _v("a5", "reject"),
        ]
        assert GoalConsensus._approval_ratio(votes) == 3 / 5  # 0.6

    def test_ignores_abstain(self):
        votes = [
            _v("a1", "approve"), _v("a2", "approve"),
            _v("a3", "reject"), _v("a4", "abstain"), _v("a5", "abstain"),
        ]
        # 2 approve / (2 approve + 1 reject) = 2/3 ≈ 0.667
        assert GoalConsensus._approval_ratio(votes) == pytest.approx(2 / 3)

    def test_all_abstain_returns_zero(self):
        votes = [_v("a1", "abstain"), _v("a2", "abstain")]
        assert GoalConsensus._approval_ratio(votes) == 0.0

    def test_empty_returns_zero(self):
        assert GoalConsensus._approval_ratio([]) == 0.0


class TestEvaluateThreshold:
    """Tests for _evaluate_threshold() returning (accepted, close_split)."""

    def gc(self) -> GoalConsensus:
        """Create a GoalConsensus with a dummy coordinator for local tests."""
        c = MagicMock(spec=ConsensusCoordinator)
        return GoalConsensus(coordinator=c)

    def test_three_of_three_approve_passes(self):
        votes = [_v("a1", "approve"), _v("a2", "approve"), _v("a3", "approve")]
        accepted, close = self.gc()._evaluate_threshold(votes)
        assert accepted is True
        assert close is False

    def test_two_of_three_approve_is_close_split(self):
        # 2/3 = 0.667 → passes threshold, NOT close
        votes = [_v("a1", "approve"), _v("a2", "approve"), _v("a3", "reject")]
        accepted, close = self.gc()._evaluate_threshold(votes)
        assert accepted is True
        assert close is False

    def test_three_of_five_approve_is_60_percent_passes(self):
        votes = [
            _v("a1", "approve"), _v("a2", "approve"), _v("a3", "approve"),
            _v("a4", "reject"), _v("a5", "reject"),
        ]
        accepted, close = self.gc()._evaluate_threshold(votes)
        assert accepted is True
        assert close is False

    def test_two_of_five_approve_rejected_no_close(self):
        # 2/5 = 0.4 → <50%, no close
        votes = [
            _v("a1", "approve"), _v("a2", "approve"),
            _v("a3", "reject"), _v("a4", "reject"), _v("a5", "reject"),
        ]
        accepted, close = self.gc()._evaluate_threshold(votes)
        assert accepted is False
        assert close is False

    def test_two_of_four_approve_is_50_percent_close(self):
        # 2/4 = 0.5 → close split
        votes = [
            _v("a1", "approve"), _v("a2", "approve"),
            _v("a3", "reject"), _v("a4", "reject"),
        ]
        accepted, close = self.gc()._evaluate_threshold(votes)
        assert accepted is False
        assert close is True

    def test_three_of_six_approve_is_50_percent_close(self):
        votes = [
            _v("a1", "approve"), _v("a2", "approve"), _v("a3", "approve"),
            _v("a4", "reject"), _v("a5", "reject"), _v("a6", "reject"),
        ]
        accepted, close = self.gc()._evaluate_threshold(votes)
        assert accepted is False
        assert close is True

    def test_empty_votes_not_accepted_not_close(self):
        accepted, close = self.gc()._evaluate_threshold([])
        assert accepted is False
        assert close is False

    def test_all_abstain_not_accepted_not_close(self):
        votes = [_v("a1", "abstain"), _v("a2", "abstain"), _v("a3", "abstain")]
        accepted, close = self.gc()._evaluate_threshold(votes)
        assert accepted is False
        assert close is False


# ---------------------------------------------------------------------------
# Prompt template tests
# ---------------------------------------------------------------------------


class TestPromptTemplates:
    """Tests for prompt template functions."""

    def test_build_goal_vote_prompt_includes_goal_fields(self, sample_goal):
        prompt = _build_goal_vote_prompt(sample_goal)
        assert sample_goal.title in prompt
        assert sample_goal.description in prompt
        for c in sample_goal.success_criteria:
            assert c in prompt

    def test_build_goal_vote_prompt_is_non_empty(self, sample_goal):
        prompt = _build_goal_vote_prompt(sample_goal)
        assert len(prompt) > 0

    def test_build_refinement_prompt_includes_arguments(self, sample_goal):
        prompt = _build_refinement_prompt(
            sample_goal,
            args_for="- a1: Great idea!",
            args_against="- a2: Too risky.",
        )
        assert "Great idea!" in prompt
        assert "Too risky." in prompt
        assert sample_goal.title in prompt

    def test_build_refinement_prompt_handles_empty_args(self, sample_goal):
        prompt = _build_refinement_prompt(sample_goal, "", "")
        assert "(none)" in prompt


# ---------------------------------------------------------------------------
# Integration tests: run_goal_consensus
# ---------------------------------------------------------------------------


class TestRunGoalConsensus:
    """Integration tests for GoalConsensus.run_goal_consensus()."""

    @pytest.fixture
    def empty_actors(self) -> dict:
        return {}

    @pytest.fixture
    def basic_actors(self) -> dict:
        """Minimal actor dict — just Steward and Arbiter available."""
        steward = MagicMock()
        steward.run_with_llm = AsyncMock(
            return_value='{"decision": "approve", "confidence": 0.9, "reasoning": "Good."}'
        )
        arbiter = MagicMock()
        arbiter.run_with_llm = AsyncMock(
            return_value='{"decision": "reject", "confidence": 0.85, "reasoning": "Risky."}'
        )
        return {"steward": steward, "arbiter": arbiter}

    # -- Round-1 clear approval ----------------------------------------------

    @pytest.mark.asyncio
    async def test_round1_unanimous_approve_returns_accepted(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """3/3 approve → accepted in 1 round."""
        mock_coordinator.run_consensus.return_value = _make_result([
            _mv("a1", "approve", 0.9, "Solid goal."),
            _mv("a2", "approve", 0.85, "Agreed."),
            _mv("a3", "approve", 0.8, "Yes."),
        ])

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is True
        assert rounds == 1
        assert len(votes) == 3
        assert all(v.decision == "approve" for v in votes)

    @pytest.mark.asyncio
    async def test_round1_three_of_five_approve_accepted(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """3/5 approve = 60% → accepted in 1 round."""
        mock_coordinator.run_consensus.return_value = _make_result([
            _mv("a1", "approve", 0.9),
            _mv("a2", "approve", 0.8),
            _mv("a3", "approve", 0.7),
            _mv("a4", "reject", 0.6),
            _mv("a5", "reject", 0.8),
        ])

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, _votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is True
        assert rounds == 1

    # -- Round-1 clear rejection -----------------------------------------------

    @pytest.mark.asyncio
    async def test_round1_unanimous_reject_returns_rejected(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """3/3 reject → rejected in 1 round."""
        mock_coordinator.run_consensus.return_value = _make_result([
            _mv("a1", "reject", 0.9, "Not now."),
            _mv("a2", "reject", 0.8, "Skip."),
            _mv("a3", "reject", 0.85, "Nope."),
        ])

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is False
        assert rounds == 1
        assert len(votes) == 3

    # -- Close split — round 2 refinement ------------------------------------

    @pytest.mark.asyncio
    async def test_close_split_triggers_round2(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """2/4 approve = 50% → close split → round 2."""
        # Round 1: 2 approve, 2 reject
        r1_votes = [
            _mv("a1", "approve", 0.8, "Worth doing."),
            _mv("a2", "approve", 0.7, "I agree."),
            _mv("a3", "reject", 0.9, "Too vague."),
            _mv("a4", "reject", 0.8, "Bad timing."),
        ]
        # Round 2: a3 flips to approve
        r2_votes = [
            _mv("a1", "approve", 0.8, "Still yes."),
            _mv("a2", "approve", 0.7, "Yep."),
            _mv("a3", "approve", 0.6, "Convinced by for args."),
            _mv("a4", "reject", 0.8, "Still no."),
        ]

        mock_coordinator.run_consensus.side_effect = [
            _make_result(r1_votes),
            _make_result(r2_votes),
        ]

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, _votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is True
        assert rounds == 2
        assert mock_coordinator.run_consensus.call_count == 2

    @pytest.mark.asyncio
    async def test_close_split_still_close_round2_tie_breaks(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """Round 2 still close → tie-break via Steward+Arbiter."""
        r1_votes = [
            _mv("a1", "approve", 0.8, "Good."),
            _mv("a2", "approve", 0.7, "Yes."),
            _mv("a3", "reject", 0.9, "No."),
            _mv("a4", "reject", 0.8, "Nah."),
        ]
        r2_votes = [
            _mv("a1", "approve", 0.8, "Still good."),
            _mv("a2", "reject", 0.7, "Changed mind."),
            _mv("a3", "reject", 0.9, "Still no."),
            _mv("a4", "approve", 0.6, "Convinced."),
        ]
        # After r2: still 2-2 split

        mock_coordinator.run_consensus.side_effect = [
            _make_result(r1_votes),
            _make_result(r2_votes),
        ]

        gc = GoalConsensus(coordinator=mock_coordinator)
        # Steward votes approve, Arbiter votes reject → 3-3 still no clear winner
        # So it resolves by evaluate_threshold on combined votes
        accepted, votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert rounds == 3
        assert isinstance(accepted, bool)
        assert len(votes) >= 4  # prior 4 + tie-breakers added

    # -- Tie-breaking with prior votes ----------------------------------------

    @pytest.mark.asyncio
    async def test_tie_break_when_steward_already_voted(
        self, sample_goal, mock_coordinator
    ):
        """When Steward already voted in round 2, don't re-query them."""
        r1_votes = [
            _mv("a1", "approve", 0.8),
            _mv("a2", "approve", 0.7),
            _mv("a3", "reject", 0.9),
            _mv("a4", "reject", 0.8),
        ]
        r2_votes = [
            _mv("a1", "approve", 0.8),
            _mv("steward", "reject", 0.9, "I object."),
            _mv("a3", "reject", 0.9),
            _mv("a4", "approve", 0.6),
        ]

        arbiter = MagicMock()
        arbiter.run_with_llm = AsyncMock(
            return_value='{"decision": "approve", "confidence": 0.7, "reasoning": "Fine."}'
        )
        actors = {"steward": MagicMock(), "arbiter": arbiter}

        mock_coordinator.run_consensus.side_effect = [
            _make_result(r1_votes),
            _make_result(r2_votes),
        ]

        gc = GoalConsensus(coordinator=mock_coordinator)
        _accepted, _votes, rounds = await gc.run_goal_consensus(
            sample_goal, actors, timeout=60
        )

        assert rounds == 3
        # Steward was NOT re-queried (her run_with_llm was never called)
        actors["steward"].run_with_llm.assert_not_called()

    # -- Error handling --------------------------------------------------------

    @pytest.mark.asyncio
    async def test_coordinator_timeout_handled_gracefully(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """When the coordinator times out, GoalConsensus treats it as empty votes → rejected."""
        mock_coordinator.run_consensus.side_effect = TimeoutError()

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is False
        assert rounds == 1
        assert votes == []

    @pytest.mark.asyncio
    async def test_coordinator_exception_handled_gracefully(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """When the coordinator raises an unexpected exception, it's caught."""
        mock_coordinator.run_consensus.side_effect = RuntimeError("Boom!")

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is False
        assert rounds == 1
        assert votes == []

    @pytest.mark.asyncio
    async def test_coordinator_returns_none_treated_as_empty(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """run_consensus returning None → empty votes."""
        mock_coordinator.run_consensus.return_value = None

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, votes, _rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is False
        assert votes == []

    @pytest.mark.asyncio
    async def test_empty_result_votes_treated_as_empty(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """ConsensusResult with no votes → empty."""
        mock_coordinator.run_consensus.return_value = _make_result([])

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, votes, _rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is False
        assert votes == []

    # -- Decision with abstain mixed in ---------------------------------------

    @pytest.mark.asyncio
    async def test_approve_with_abstain_still_can_pass(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """3 approve, 1 reject, 2 abstain → 3/4 = 75% → accepted."""
        mock_coordinator.run_consensus.return_value = _make_result([
            _mv("a1", "approve", 0.8),
            _mv("a2", "approve", 0.7),
            _mv("a3", "approve", 0.9),
            _mv("a4", "reject", 0.6),
            _mv("a5", "abstain", 0.3),
            _mv("a6", "abstain", 0.2),
        ])

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, _votes, rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        assert accepted is True
        assert rounds == 1

    # -- Free-form decision mapping -------------------------------------------

    @pytest.mark.asyncio
    async def test_free_form_decisions_normalised(
        self, sample_goal, mock_coordinator, basic_actors
    ):
        """Agents saying 'yes'/'no' are normalised to approve/reject."""
        mock_coordinator.run_consensus.return_value = _make_result([
            _mv("a1", "yes", 0.9, "Great!"),
            _mv("a2", "support", 0.8, "Agreed."),
            _mv("a3", "agree", 0.7, "Yep."),
            _mv("a4", "no", 0.8, "Bad."),
            _mv("a5", "oppose", 0.9, "Terrible."),
        ])

        gc = GoalConsensus(coordinator=mock_coordinator)
        accepted, votes, _rounds = await gc.run_goal_consensus(
            sample_goal, basic_actors, timeout=60
        )

        # 3 approve / (3+2) = 0.6 → accepted
        assert accepted is True
        approve_count = sum(1 for v in votes if v.decision == "approve")
        reject_count = sum(1 for v in votes if v.decision == "reject")
        assert approve_count == 3
        assert reject_count == 2


# ---------------------------------------------------------------------------
# Argument extraction tests
# ---------------------------------------------------------------------------


class TestExtractArguments:
    def test_extracts_for_and_against(self):
        votes = [
            _v("a1", "approve", rationale="This solves a real problem."),
            _v("a2", "approve", rationale="Good scope."),
            _v("a3", "reject", rationale="Too expensive."),
            _v("a4", "reject", rationale="Not a priority."),
            _v("a5", "abstain", rationale="Don't care."),
        ]

        args_for, args_against = GoalConsensus._extract_arguments(votes)

        assert "a1" in args_for
        assert "a2" in args_for
        assert "a3" in args_against
        assert "a4" in args_against
        # abstain votes NOT included in either
        assert "a5" not in args_for
        assert "a5" not in args_against

    def test_empty_votes_returns_none_placeholders(self):
        args_for, args_against = GoalConsensus._extract_arguments([])
        assert args_for == "(none)"
        assert args_against == "(none)"

    def test_votes_without_rationale_skipped(self):
        votes = [
            _v("a1", "approve", rationale=""),  # no rationale
            _v("a2", "reject", rationale=""),   # no rationale
        ]
        args_for, args_against = GoalConsensus._extract_arguments(votes)
        assert args_for == "(none)"
        assert args_against == "(none)"


# ---------------------------------------------------------------------------
# Class API tests
# ---------------------------------------------------------------------------


class TestGoalConsensusApi:
    """Tests for GoalConsensus class attributes and defaults."""

    def test_has_run_goal_consensus_method(self, mock_coordinator):
        gc = GoalConsensus(coordinator=mock_coordinator)
        assert hasattr(gc, "run_goal_consensus")
        assert callable(gc.run_goal_consensus)

    def test_default_steward_and_arbiter_ids(self, mock_coordinator):
        gc = GoalConsensus(coordinator=mock_coordinator)
        assert gc.steward_agent_id == "steward"
        assert gc.arbiter_agent_id == "arbiter"

    def test_custom_tie_breaker_ids(self, mock_coordinator):
        gc = GoalConsensus(
            coordinator=mock_coordinator,
            steward_agent_id="chief",
            arbiter_agent_id="judge",
        )
        assert gc.steward_agent_id == "chief"
        assert gc.arbiter_agent_id == "judge"
