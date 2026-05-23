"""Tests for fail-fast TypeError guards on mixin methods.

Covers TribunalMixin (all 6 dependency-dependent methods) plus a
happy-path regression test for LearningMixin.

Does NOT test hasattr-guarded mixins (HealthReportingMixin,
MemoryAccessMixin, PatternConsumerMixin, DeliberationMixin, AuditMixin)
as those check for optional subsystems, not required dependencies.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest


pytestmark = [pytest.mark.unit]

from heretek_swarm.actors.mixins.learning import LearningMixin
from heretek_swarm.actors.mixins.memory import MemoryMixin
from heretek_swarm.actors.mixins.pattern import PatternMixin
from heretek_swarm.actors.mixins.tribunal import TribunalMixin

# ===================================================================
# TribunalMixin guard tests
# ===================================================================


class _TribunalStub(TribunalMixin):
    """Minimal subclass of TribunalMixin with ``tribunal = None``."""

    tribunal: Any = None
    agent_id: str = "test-agent"


@pytest.fixture
def stub_tribunal() -> _TribunalStub:
    return _TribunalStub()


@pytest.mark.asyncio
async def test_submit_tribunal_case_raises(stub_tribunal: _TribunalStub) -> None:
    with pytest.raises(TypeError, match="requires tribunal"):
        await stub_tribunal._submit_tribunal_case(
            original_decision_id="d1",
            grounds="test",
            description="desc",
        )


@pytest.mark.asyncio
async def test_submit_tribunal_evidence_raises(stub_tribunal: _TribunalStub) -> None:
    with pytest.raises(TypeError, match="requires tribunal"):
        await stub_tribunal._submit_tribunal_evidence(
            case_id="c1",
            content="evidence text",
        )


@pytest.mark.asyncio
async def test_get_tribunal_case_raises(stub_tribunal: _TribunalStub) -> None:
    with pytest.raises(TypeError, match="requires tribunal"):
        await stub_tribunal._get_tribunal_case("c1")


@pytest.mark.asyncio
async def test_issue_tribunal_ruling_raises(stub_tribunal: _TribunalStub) -> None:
    with pytest.raises(TypeError, match="requires tribunal"):
        await stub_tribunal._issue_tribunal_ruling(
            case_id="c1",
            ruling_type=MagicMock(),
            reasoning="because",
        )


@pytest.mark.asyncio
async def test_get_tribunal_precedents_raises(stub_tribunal: _TribunalStub) -> None:
    with pytest.raises(TypeError, match="requires tribunal"):
        await stub_tribunal._get_tribunal_precedents()


@pytest.mark.asyncio
async def test_find_similar_precedents_raises(stub_tribunal: _TribunalStub) -> None:
    with pytest.raises(TypeError, match="requires tribunal"):
        await stub_tribunal._find_similar_precedents("c1")


# ===================================================================
# MemoryMixin guard tests
# ===================================================================


class _MemoryStub(MemoryMixin):
    """Minimal subclass with ``access_analyzer = None``."""

    access_analyzer: Any = None
    agent_id: str = "test-agent"


class _MemoryHappy(MemoryMixin):
    """Subclass with a mock access_analyzer for happy-path."""

    access_analyzer: Any = None
    agent_id: str = "test-agent"


@pytest.fixture
def stub_memory() -> _MemoryStub:
    return _MemoryStub()


def test_track_memory_access_raises(stub_memory: _MemoryStub) -> None:
    with pytest.raises(TypeError, match="requires access_analyzer"):
        stub_memory._track_memory_access("i1", "code")


def test_get_memory_tier_raises(stub_memory: _MemoryStub) -> None:
    with pytest.raises(TypeError, match="requires access_analyzer"):
        stub_memory._get_memory_tier("i1", "code")


@pytest.mark.asyncio
async def test_prefetch_relevant_raises(stub_memory: _MemoryStub) -> None:
    with pytest.raises(TypeError, match="requires access_analyzer"):
        await stub_memory._prefetch_relevant("agent", "code")


# ===================================================================
# PatternMixin guard tests
# ===================================================================


class _PatternStub(PatternMixin):
    """Minimal subclass with ``pattern_extractor = None``."""

    pattern_extractor: Any = None
    _pattern_emitted: Any = None
    agent_id: str = "test-agent"


@pytest.fixture
def stub_pattern() -> _PatternStub:
    return _PatternStub()


@pytest.mark.asyncio
async def test_emit_pattern_raises(stub_pattern: _PatternStub) -> None:
    with pytest.raises(TypeError, match="requires pattern_extractor"):
        await stub_pattern._emit_pattern("i1", "code", "success", {})


@pytest.mark.asyncio
async def test_consume_patterns_raises(stub_pattern: _PatternStub) -> None:
    with pytest.raises(TypeError, match="requires pattern_extractor"):
        await stub_pattern._consume_patterns()


# ===================================================================
# LearningMixin happy-path regression test
# ===================================================================


class _LearningHappy(LearningMixin):
    """LearningMixin subclass for happy-path regression.

    Only _active_deliberations is relevant — pattern_extractor,
    deliberation_engine, and access_analyzer are all None, but
    guarded by ternaries, so get_learning_status should not crash.
    """

    agent_id: str = "test-agent"
    _active_deliberations: dict[str, str] = None
    pattern_extractor: Any = None
    deliberation_engine: Any = None
    access_analyzer: Any = None


def test_learning_get_learning_status_with_None_active_deliberations() -> None:
    """get_learning_status must not crash when _active_deliberations is None."""
    mixin = _LearningHappy()
    result = mixin.get_learning_status()
    assert result["agent_id"] == "test-agent"
    assert result["collective_learning"]["patterns_extracted"] == 0
    assert result["consensus"]["active_deliberations"] == 0
