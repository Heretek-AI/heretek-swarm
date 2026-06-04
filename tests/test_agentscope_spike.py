"""Tests for the Phase 3A AgentScope spike."""

from heretek_swarm.actors.agentscope_spike import run_dry_spike


def test_dry_spike_passes():
    """The AgentScope cutover API surface is valid."""
    run_dry_spike()
