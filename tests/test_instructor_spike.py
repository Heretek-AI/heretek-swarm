"""Tests for the Phase 1.1 Instructor spike (dry-mode only).

The live-mode call (run_live_spike) requires OPENAI_API_KEY and is
covered by an integration test that is opt-in via the env var.
"""

from __future__ import annotations

import os

import pytest

from heretek_swarm.llm.instructor_spike import (
    Channel,
    Message,
    StyleGuide,
    TranslationPlan,
    run_dry_spike,
)


def test_dry_spike_passes():
    """The 4-level Pydantic model + Instructor API surface is valid."""
    run_dry_spike()


def test_translation_plan_roundtrip():
    """4-level nested Pydantic model round-trips through JSON."""
    plan = TranslationPlan(
        source_text="Hello, world!",
        target_language="es",
        message=Message(subject="Greeting", body="¡Hola, mundo!"),
        style=StyleGuide(tone="warm", formality="casual", language="es"),
        channels=[
            Channel(name="email", audience="external"),
            Channel(name="slack", audience="internal"),
        ],
    )
    blob = plan.model_dump_json()
    restored = TranslationPlan.model_validate_json(blob)
    assert restored == plan
    # Depth check: TranslationPlan -> Message, StyleGuide, List[Channel] -> Channel
    assert isinstance(restored.message, Message)
    assert isinstance(restored.style, StyleGuide)
    assert all(isinstance(c, Channel) for c in restored.channels)


def test_live_spike_requires_api_key():
    """run_live_spike raises a clear error when OPENAI_API_KEY is missing."""
    from heretek_swarm.llm.instructor_spike import run_live_spike

    if "OPENAI_API_KEY" in os.environ:
        pytest.skip("OPENAI_API_KEY set; live call is a manual exercise")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        run_live_spike()
