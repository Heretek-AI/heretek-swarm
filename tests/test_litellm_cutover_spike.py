"""Tests for the Phase 2B.1 litellm cutover spike."""

from __future__ import annotations

from litellm import Router

from heretek_swarm.llm.litellm_cutover_spike import run_dry_spike


def test_dry_spike_passes():
    """The litellm cutover API surface is valid."""
    run_dry_spike()


def test_litellm_router_is_migration_target():
    """litellm.Router is the canonical multi-provider routing primitive."""
    assert Router is not None
    assert callable(Router)
