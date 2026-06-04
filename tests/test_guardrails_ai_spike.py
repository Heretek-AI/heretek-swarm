"""Tests for the Phase 3B Guardrails AI spike."""

from guardrails import Guard

from heretek_swarm.security.guardrails_ai_spike import run_dry_spike


def test_dry_spike_passes():
    """The Guardrails AI cutover API surface is valid."""
    run_dry_spike()


def test_guard_class_importable():
    """Guard is the migration target."""
    assert Guard is not None
    assert callable(Guard)
