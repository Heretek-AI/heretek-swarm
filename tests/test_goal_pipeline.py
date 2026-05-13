"""Tests for the Goal Pipeline.

Verifies that the autonomous goal cycle correctly:
- Proposes a new goal when the queue is empty
- Runs consensus voting on proposed goals
- Transitions goals to accepted or rejected based on voting
- Logs events to historian
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from heretek_swarm.goals.models import Goal, Vote
from heretek_swarm.goals.pipeline import run_goal_cycle
from heretek_swarm.goals.store import FileGoalStore


@pytest.fixture
def mock_historian() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def store(tmp_path) -> FileGoalStore:
    return FileGoalStore(tmp_path / "goals.json")


@pytest.fixture
def mock_metis() -> AsyncMock:
    metis = AsyncMock()
    goal = Goal(
        id="goal-metis",
        title="Test Metis Proposal",
        description="A proposed goal by Metis.",
        success_criteria=["Tests pass"],
        status="proposed",
    )
    metis.generate_goal_proposal.return_value = {"goal": goal}
    return metis


@pytest.fixture
def mock_coordinator() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sample_goal() -> Goal:
    return Goal(
        id="goal-001",
        title="Proposed Goal",
        description="A test goal",
        success_criteria=[],
        status="proposed",
    )


@pytest.mark.asyncio
async def test_propose_new_goal(store, mock_metis, mock_coordinator, mock_historian):
    """When no proposed goals exist, it should ask Metis for a new proposal."""
    goal = await run_goal_cycle(
        store=store,
        metis=mock_metis,
        coordinator=mock_coordinator,
        actors={},
        historian=mock_historian,
    )

    assert goal is not None
    assert goal.id == "goal-metis"
    assert goal.status == "proposed"
    mock_metis.generate_goal_proposal.assert_called_once()

    saved = store.load("goal-metis")
    assert saved is not None
    mock_historian.log_event.assert_called_with(
        "goal_proposed",
        "goal_pipeline",
        {
            "goal_id": goal.id,
            "title": goal.title,
            "description_preview": goal.description[:200],
        },
    )


@pytest.mark.asyncio
async def test_vote_proposed_goal_accepted(
    store, mock_metis, mock_coordinator, mock_historian, sample_goal
):
    """When a proposed goal exists, it should run consensus and transition to accepted."""
    store.save(sample_goal)

    # Mock GoalConsensus.run_goal_consensus to return accepted=True
    with patch("heretek_swarm.goals.pipeline.GoalConsensus") as mock_consensus_cls:
        mock_consensus = AsyncMock()
        mock_consensus.run_goal_consensus.return_value = (
            True,  # accepted
            [Vote(agent_id="alpha", decision="approve", confidence=0.9)],  # votes
            1,  # rounds
        )
        mock_consensus_cls.return_value = mock_consensus

        goal = await run_goal_cycle(
            store=store,
            metis=mock_metis,
            coordinator=mock_coordinator,
            actors={"alpha": {}},
            historian=mock_historian,
        )

        assert goal is not None
        assert goal.id == "goal-001"
        assert goal.status == "accepted"
        assert len(goal.votes) == 1

        mock_consensus.run_goal_consensus.assert_called_once()
        mock_metis.generate_goal_proposal.assert_not_called()

        saved = store.load("goal-001")
        assert saved.status == "accepted"


@pytest.mark.asyncio
async def test_vote_proposed_goal_rejected(
    store, mock_metis, mock_coordinator, mock_historian, sample_goal
):
    """When a proposed goal fails consensus, it should transition to rejected."""
    store.save(sample_goal)

    # Mock GoalConsensus.run_goal_consensus to return accepted=False
    with patch("heretek_swarm.goals.pipeline.GoalConsensus") as mock_consensus_cls:
        mock_consensus = AsyncMock()
        mock_consensus.run_goal_consensus.return_value = (
            False,  # accepted
            [Vote(agent_id="alpha", decision="reject", confidence=0.9)],  # votes
            1,  # rounds
        )
        mock_consensus_cls.return_value = mock_consensus

        goal = await run_goal_cycle(
            store=store,
            metis=mock_metis,
            coordinator=mock_coordinator,
            actors={"alpha": {}},
            historian=mock_historian,
        )

        assert goal is not None
        assert goal.id == "goal-001"
        assert goal.status == "rejected"
        assert len(goal.votes) == 1

        mock_consensus.run_goal_consensus.assert_called_once()
        mock_metis.generate_goal_proposal.assert_not_called()

        saved = store.load("goal-001")
        assert saved.status == "rejected"
