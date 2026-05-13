"""Integration smoke test for mixin imports and stub-injected agent.

Milestone M003 — Slice S03 — Task T01

Verifies milestone-level acceptance:
1. ``from heretek_swarm.actors.mixins import *`` resolves all 10 names.
2. ``AlphaAgent`` with injected stubs constructs without error.
3. Mixin methods dispatched via MRO return real stub data when
   dependencies are injected.
4. ``AlphaAgent()`` (no stubs) still constructs cleanly (backward compat).
"""

from __future__ import annotations

from typing import Any

from heretek_swarm.actors import AgentActor, AlphaAgent
from heretek_swarm.actors.mixins import (
    AuditMixin,
    DeliberationMixin,
    HealthReportingMixin,
    LearningMixin,
    MemoryAccessMixin,
    MemoryMixin,
    PatternConsumerMixin,
    PatternMixin,
    TribunalMixin,
    ValidationMixin,
)
from heretek_swarm.actors.mixins import (
    __all__ as mixins_all,
)
from heretek_swarm.actors.mixins.memory import AccessTier
from heretek_swarm.actors.stubs import (
    StubAccessAnalyzer,
    StubDeliberationEngine,
    StubPatternExtractor,
)

# ===================================================================
# Integration helpers
# ===================================================================


class _MemoryMixinHost(MemoryMixin):
    """Minimal host that inherits MemoryMixin so we can test its
    mixin methods through the real MRO dispatch chain.

    Sets ``agent_id`` (required by the mixin) and allows injecting
    ``access_analyzer`` (required by guarded methods).
    """

    access_analyzer: Any = None
    agent_id: str = "memory-host"

    def __init__(self, **kwargs: Any) -> None:
        # Call super().__init__ to let MemoryMixin pass through to
        # its own super (object), while allowing kwargs to override
        # the class-level defaults.
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__()


# ===================================================================
# Tests
# ===================================================================


class TestMixinIntegrationSmoke:
    """Integration-level smoke tests for M003 mixin machinery."""

    # ------------------------------------------------------------------
    # 1. Public import surface — all 10 names in __all__ are importable
    # ------------------------------------------------------------------

    @staticmethod
    def test_mixins_all_has_ten_names() -> None:
        """``from heretek_swarm.actors.mixins import *`` should expose
        exactly 10 names matching ``__all__``."""
        assert len(mixins_all) == 10, f"Expected 10 mixin names in __all__, got {len(mixins_all)}"

    @staticmethod
    def test_audit_mixin_importable() -> None:
        assert AuditMixin.__name__ == "AuditMixin"

    @staticmethod
    def test_deliberation_mixin_importable() -> None:
        assert DeliberationMixin.__name__ == "DeliberationMixin"

    @staticmethod
    def test_health_reporting_mixin_importable() -> None:
        assert HealthReportingMixin.__name__ == "HealthReportingMixin"

    @staticmethod
    def test_learning_mixin_importable() -> None:
        assert LearningMixin.__name__ == "LearningMixin"

    @staticmethod
    def test_memory_mixin_importable() -> None:
        assert MemoryMixin.__name__ == "MemoryMixin"

    @staticmethod
    def test_memory_access_mixin_importable() -> None:
        assert MemoryAccessMixin.__name__ == "MemoryAccessMixin"

    @staticmethod
    def test_pattern_mixin_importable() -> None:
        assert PatternMixin.__name__ == "PatternMixin"

    @staticmethod
    def test_pattern_consumer_mixin_importable() -> None:
        assert PatternConsumerMixin.__name__ == "PatternConsumerMixin"

    @staticmethod
    def test_tribunal_mixin_importable() -> None:
        assert TribunalMixin.__name__ == "TribunalMixin"

    @staticmethod
    def test_validation_mixin_importable() -> None:
        assert ValidationMixin.__name__ == "ValidationMixin"

    # ------------------------------------------------------------------
    # 2. AlphaAgent with stubs — construction + mixin method dispatch
    # ------------------------------------------------------------------

    @staticmethod
    def test_alpha_agent_with_stubs_constructs() -> None:
        """``AlphaAgent(access_analyzer=..., pattern_extractor=...)``
        constructs without error."""
        act = AlphaAgent(
            agent_id="alpha-stubbed",
            access_analyzer=StubAccessAnalyzer(),
            pattern_extractor=StubPatternExtractor(),
        )
        assert act.agent_id == "alpha-stubbed"
        assert act.access_analyzer is not None
        assert act.pattern_extractor is not None

    @staticmethod
    def test_learning_mixin_get_learning_status_with_stubs() -> None:
        """``get_learning_status()`` on an AlphaAgent with injected
        stubs returns real stub data (not None/empty)."""
        access_analyzer = StubAccessAnalyzer()
        pattern_extractor = StubPatternExtractor()
        deliberation_engine = StubDeliberationEngine()

        actor = AlphaAgent(
            agent_id="alpha-status",
            access_analyzer=access_analyzer,
            pattern_extractor=pattern_extractor,
            deliberation_engine=deliberation_engine,
        )

        status = actor.get_learning_status()
        assert status["agent_id"] == "alpha-status"

        cl = status["collective_learning"]
        assert cl["patterns_extracted"] == 0
        assert cl["message_cache_size"] == 0

        cons = status["consensus"]
        assert cons["active_deliberations"] == 0
        assert cons["deliberation_engine_stats"]["active_deliberations"] == 0

        mem = status["memory_optimization"]
        assert mem["access_statistics"]["total_accesses"] == 0

    @staticmethod
    def test_learning_mixin_get_learning_status_captures_data() -> None:
        """After recording an access, the stub should reflect it in
        ``get_learning_status()``."""
        access_analyzer = StubAccessAnalyzer()
        access_analyzer.record_access(
            memory_id="test_mem_001",
            access_type="read",
            agent_id="alpha-status",
        )

        actor = AlphaAgent(
            agent_id="alpha-status",
            access_analyzer=access_analyzer,
            pattern_extractor=StubPatternExtractor(),
        )

        status = actor.get_learning_status()
        stats = status["memory_optimization"]["access_statistics"]
        assert stats["total_accesses"] == 1, (
            f"Expected total_accesses=1, got {stats['total_accesses']}"
        )

    @staticmethod
    def test_memory_mixin_track_memory_access_via_stub() -> None:
        """``MemoryMixin._track_memory_access()`` on a host with
        ``access_analyzer`` injected should NOT raise TypeError and
        should record the access on the stub."""
        access_analyzer = StubAccessAnalyzer()
        host = _MemoryMixinHost(access_analyzer=access_analyzer)

        # This should not raise TypeError
        host._track_memory_access(
            item_id="item-001",
            item_type="decision",
            access_type="read",
        )

        # The stub should have recorded the access
        profile = access_analyzer.get_profile("decision_item-001")
        assert profile is not None, "Expected a profile to exist"
        assert profile.access_count == 1, f"Expected access_count=1, got {profile.access_count}"
        assert "read" in profile.access_types

    @staticmethod
    def test_memory_mixin_get_memory_tier_returns_cold() -> None:
        """``MemoryMixin._get_memory_tier()`` on a host with
        ``access_analyzer`` injected returns ``AccessTier.COLD`` for
        an unaccessed item."""
        access_analyzer = StubAccessAnalyzer()
        host = _MemoryMixinHost(access_analyzer=access_analyzer)

        tier = host._get_memory_tier(item_id="new-item", item_type="code")
        # StubAccessAnalyzer has no profiles, so get_profile returns
        # None, and MemoryMixin._get_memory_tier returns AccessTier.COLD
        assert tier == AccessTier.COLD, f"Expected COLD, got {tier}"

    # ------------------------------------------------------------------
    # 3. AlphaAgent without stubs — backward compat
    # ------------------------------------------------------------------

    @staticmethod
    def test_alpha_agent_without_stubs_constructs() -> None:
        """``AlphaAgent()`` (no stub kwargs) constructs without error
        and falls back to module-level stubs."""
        actor = AlphaAgent(agent_id="alpha-no-stubs")
        assert actor.agent_id == "alpha-no-stubs"
        assert actor.access_analyzer is None
        assert actor.pattern_extractor is None

    @staticmethod
    def test_bare_agent_actor_no_stubs_constructs() -> None:
        """``AgentActor()`` without any stub kwargs constructs cleanly."""
        actor = AgentActor(agent_id="bare-no-stubs")
        assert actor.agent_id == "bare-no-stubs"
        assert actor.access_analyzer is None
        assert actor.pattern_extractor is None
        assert actor._llm_provider is not None
