"""Tests for constructor-based stub injection into AgentActor.

Verifies that all 6 injectable dependency kwargs can be passed to
AgentActor and its subclasses, and that guarded mixin methods work
without TypeError when a stub is provided.

Also verifies that omitting stubs does NOT raise TypeError at
construction time (the guards only fire when guarded methods are
actually called — S01 covers that path).
"""

from __future__ import annotations

import pytest

from heretek_swarm.actors import AgentActor, AlphaAgent
from heretek_swarm.actors.stubs import (
    StubAccessAnalyzer,
    StubDeliberationEngine,
    StubEventMesh,
    StubLLMProvider,
    StubPatternExtractor,
    StubTribunal,
)

# ===================================================================
# AgentActor direct construction tests
# ===================================================================


class TestAgentActorStubInjection:
    """Exercises stub injection into bare AgentActor instances.

    Note: Mixin methods (_track_memory_access, _emit_pattern, etc.)
    are only available on TriadAgent (and subclasses), not on bare
    AgentActor.  Those tests are in TestTriadAgentStubInjection below.
    """

    # -- access_analyzer injection -----------------------------------

    @staticmethod
    def test_stub_access_analyzer_constructs() -> None:
        """AgentActor(access_analyzer=StubAccessAnalyzer()) constructs
        without TypeError."""
        actor = AgentActor(
            agent_id="test-aa",
            access_analyzer=StubAccessAnalyzer(),
        )
        assert actor.access_analyzer is not None
        assert actor.agent_id == "test-aa"

    # -- llm_provider injection --------------------------------------

    @staticmethod
    def test_stub_llm_provider_assigned() -> None:
        """Constructing AgentActor(llm_provider=StubLLMProvider())
        assigns the stub to self._llm_provider."""
        stub = StubLLMProvider(canned_response="test_response")
        actor = AgentActor(
            agent_id="test-llm",
            llm_provider=stub,
        )
        # Core deps use private names (_llm_provider)
        assert actor._llm_provider is stub

    @staticmethod
    @pytest.mark.asyncio
    async def test_stub_llm_provider_generate() -> None:
        """Calling generate() on an injected stub llm_provider returns
        the canned response."""
        stub = StubLLMProvider(canned_response="hello_test")
        actor = AgentActor(
            agent_id="test-llm-gen",
            llm_provider=stub,
        )
        result = await actor._llm_provider.generate("some prompt")
        assert result == "hello_test"
        assert actor._llm_provider.call_count == 1

    # -- event_mesh injection ----------------------------------------

    @staticmethod
    def test_stub_event_mesh_assigned() -> None:
        """Constructing AgentActor(event_mesh=StubEventMesh())
        assigns the stub to self._event_mesh."""
        stub = StubEventMesh()
        actor = AgentActor(
            agent_id="test-mesh",
            event_mesh=stub,
        )
        assert actor._event_mesh is stub

    # -- multiple stubs together -------------------------------------

    @staticmethod
    def test_multiple_stubs_injected() -> None:
        """Constructing AgentActor with multiple stub kwargs works."""
        actor = AgentActor(
            agent_id="test-multi",
            access_analyzer=StubAccessAnalyzer(),
            pattern_extractor=StubPatternExtractor(),
            tribunal=StubTribunal(),
            deliberation_engine=StubDeliberationEngine(),
            llm_provider=StubLLMProvider(),
            event_mesh=StubEventMesh(),
        )
        assert actor.access_analyzer is not None
        assert actor.pattern_extractor is not None
        assert actor.tribunal is not None
        assert actor.deliberation_engine is not None
        assert actor._llm_provider is not None
        assert actor._event_mesh is not None


# ===================================================================
# TriadAgent stub injection (mixin methods are MRO-resolved)
# ===================================================================


class TestTriadAgentStubInjection:
    """Exercises stub injection into AlphaAgent (a TriadAgent subclass
    that mixes in MemoryMixin, PatternMixin, etc.)."""

    # -- access_analyzer injection -----------------------------------

    @staticmethod
    def test_stub_access_analyzer_track_access() -> None:
        """Calling _track_memory_access with a stub access_analyzer does
        not raise TypeError."""
        agent = AlphaAgent(
            agent_id="test-track",
            access_analyzer=StubAccessAnalyzer(),
        )
        # Should not raise TypeError
        agent._track_memory_access("item-1", "code", "read")
        # Verify the stub recorded it
        profile = agent.access_analyzer.get_profile("code_item-1")
        assert profile is not None
        assert profile.access_count == 1

    @staticmethod
    def test_stub_access_analyzer_get_tier() -> None:
        """Calling _get_memory_tier with a stub access_analyzer does
        not raise TypeError and returns a string tier."""
        agent = AlphaAgent(
            agent_id="test-tier",
            access_analyzer=StubAccessAnalyzer(),
        )
        # Should not raise TypeError
        tier = agent._get_memory_tier("item-2", "code")
        # The stub returns a string "cold" from _StubAccessProfile.tier
        assert tier == "cold"

    # -- pattern_extractor injection ---------------------------------

    @staticmethod
    @pytest.mark.asyncio
    async def test_stub_pattern_extractor_emit() -> None:
        """Calling _emit_pattern with a stub pattern_extractor does
        not raise TypeError."""
        agent = AlphaAgent(
            agent_id="test-pe",
            pattern_extractor=StubPatternExtractor(),
        )
        await agent._emit_pattern("i1", "code", "success", {"key": "val"})

    @staticmethod
    @pytest.mark.asyncio
    async def test_stub_pattern_extractor_consume() -> None:
        """Calling _consume_patterns with a stub pattern_extractor does
        not raise TypeError."""
        agent = AlphaAgent(
            agent_id="test-pc",
            pattern_extractor=StubPatternExtractor(),
        )
        patterns = await agent._consume_patterns()
        assert isinstance(patterns, list)

    # -- tribunal injection (construction-only; TribunalMixin is
    #    not mixed into TriadAgent, so method-call tests use the
    #    _TribunalStub pattern from test_mixin_guards.py) ---------


# ===================================================================
# Default (no stubs) construction — guards should NOT fire at init
# ===================================================================


class TestAgentActorDefaultConstruction:
    """AgentActor() should construct without TypeError when no stub
    kwargs are provided.  The S01 fail-fast guards only fire when the
    guarded methods are *called* with a None dependency."""

    @staticmethod
    def test_agent_without_stubs_constructs() -> None:
        """AgentActor() without any stub kwargs raises no TypeError."""
        actor = AgentActor(agent_id="no-stubs")
        assert actor.agent_id == "no-stubs"
        # Mixin deps are None by default
        assert actor.access_analyzer is None
        assert actor.pattern_extractor is None
        assert actor.deliberation_engine is None
        assert actor.tribunal is None
        # Core deps fall back to module-level stubs
        assert actor._llm_provider is not None
        assert actor._event_mesh is not None

    @staticmethod
    def test_agent_with_explicit_none_constructs() -> None:
        """AgentActor(access_analyzer=None) explicitly is still fine."""
        actor = AgentActor(
            agent_id="explicit-none",
            access_analyzer=None,
            pattern_extractor=None,
            deliberation_engine=None,
            tribunal=None,
        )
        assert actor.agent_id == "explicit-none"
        assert actor.access_analyzer is None


# ===================================================================
# Triad/AlphaAgent subclass stub injection
# ===================================================================


class TestAlphaAgentStubInjection:
    """AlphaAgent (a TriadAgent subclass) should accept stub kwargs
    through its **kwargs passthrough to AgentActor.

    These tests overlap with TestTriadAgentStubInjection but also
    verify construction-specific scenarios.
    """

    @staticmethod
    def test_alpha_agent_with_stubs_constructs() -> None:
        """AlphaAgent(access_analyzer=StubAccessAnalyzer(), ...)
        constructs without error."""
        access_analyzer = StubAccessAnalyzer()
        pattern_extractor = StubPatternExtractor()
        agent = AlphaAgent(
            agent_id="alpha-stubs",
            access_analyzer=access_analyzer,
            pattern_extractor=pattern_extractor,
        )
        assert agent.agent_id == "alpha-stubs"
        assert agent.access_analyzer is access_analyzer
        assert agent.pattern_extractor is pattern_extractor

    @staticmethod
    def test_alpha_agent_with_all_stubs() -> None:
        """AlphaAgent with all 6 stubs injected."""
        agent = AlphaAgent(
            agent_id="alpha-all-stubs",
            access_analyzer=StubAccessAnalyzer(),
            pattern_extractor=StubPatternExtractor(),
            tribunal=StubTribunal(),
            deliberation_engine=StubDeliberationEngine(),
            llm_provider=StubLLMProvider(canned_response="alpha_test"),
            event_mesh=StubEventMesh(),
        )
        assert agent.access_analyzer is not None
        assert agent.pattern_extractor is not None
        assert agent.tribunal is not None
        assert agent.deliberation_engine is not None
        assert agent._llm_provider is not None
        assert agent._event_mesh is not None

    @staticmethod
    def test_alpha_agent_without_stubs_constructs() -> None:
        """AlphaAgent() without any stubs still constructs cleanly."""
        agent = AlphaAgent(agent_id="alpha-no-stubs")
        assert agent.agent_id == "alpha-no-stubs"
        assert agent.access_analyzer is None
