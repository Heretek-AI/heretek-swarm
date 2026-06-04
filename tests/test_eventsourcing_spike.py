"""Tests for the Phase 2B.6 eventsourcing spike."""

from eventsourcing.domain import Aggregate

from heretek_swarm.state.eventsourcing_spike import (
    ConsensusVoteAggregate,
    run_dry_spike,
)


def test_dry_spike_passes():
    """The eventsourcing cutover API surface is valid."""
    run_dry_spike()


def test_aggregate_is_base_class():
    """ConsensusVoteAggregate inherits from Aggregate."""
    assert issubclass(ConsensusVoteAggregate, Aggregate)


def test_aggregate_creation():
    """An aggregate can be created via the v9 @event-decorated __init__."""
    agg = ConsensusVoteAggregate(voter_id="alpha", proposal_id="prop-1")
    assert agg.voter_id == "alpha"
    assert agg.proposal_id == "prop-1"


def test_event_triggered():
    """vote() triggers a Voted event and updates state."""
    agg = ConsensusVoteAggregate(voter_id="beta", proposal_id="prop-2")
    agg.vote(decision="approve", confidence=0.85)
    assert agg.decision == "approve"
    assert agg.confidence == 0.85
