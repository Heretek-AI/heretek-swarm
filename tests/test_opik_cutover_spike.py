"""Tests for the Phase 2A.3 opik cutover spike."""

from __future__ import annotations

from opik import track

from heretek_swarm.observability.opik_cutover_spike import (
    run_dry_spike,
    spike_tracked_llm_call,
)


def test_dry_spike_passes():
    """The opik cutover API surface is valid."""
    run_dry_spike()


def test_track_decorator_wraps_function():
    """@opik.track wraps a function and preserves its return value."""
    out = spike_tracked_llm_call(prompt="Hello", model="gpt-4o-mini")
    assert out == "[gpt-4o-mini] response to: Hello"


def test_track_decorator_preserves_callability():
    """A @opik.track-decorated function is still callable."""
    assert callable(spike_tracked_llm_call)


def test_track_decorator_importable():
    """@opik.track is importable from the opik package."""
    assert callable(track)
