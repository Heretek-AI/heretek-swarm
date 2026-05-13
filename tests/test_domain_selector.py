"""Tests for DomainSelector — topic-matching agent selection."""

import os
import time

import pytest

from heretek_swarm.consensus.domain_selector import (
    DEFAULT_FALLBACK_AGENTS,
    DomainSelector,
)

# Resolve characters directory relative to the package
_CHARACTERS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "heretek_swarm",
    "runtime",
    "characters",
)


@pytest.fixture
def ds() -> DomainSelector:
    return DomainSelector(characters_dir=_CHARACTERS_DIR)


# ------------------------------------------------------------------
# Core selection tests
# ------------------------------------------------------------------


class TestScoreAgents:
    """Happy-path scoring and selection."""

    def test_security_analysis_selects_relevant_agents(self, ds: DomainSelector):
        """'security analysis' should select alpha, sentinel, and other
        security-relevant agents by keyword overlap."""
        result = ds.score_agents("security analysis")
        assert "alpha" in result, f"Expected alpha in {result}"
        assert "sentinel" in result, f"Expected sentinel in {result}"

    def test_coding_selects_coder(self, ds: DomainSelector):
        """'coding' should rank coder at the top."""
        result = ds.score_agents("coding")
        assert "coder" in result, f"Expected coder in {result}"

    def test_validation_selects_beta(self, ds: DomainSelector):
        """'validation' should select beta (topic: 'validation')."""
        result = ds.score_agents("validation")
        assert "beta" in result, f"Expected beta in {result}"

    def test_empathy_question_selects_empath(self, ds: DomainSelector):
        """'empathy and user emotions' should select empath."""
        result = ds.score_agents("empathy and user emotions")
        assert "empath" in result, f"Expected empath in {result}"

    def test_habits_question_selects_habit_forge(self, ds: DomainSelector):
        """'habits and routines' should select habit-forge."""
        result = ds.score_agents("habits and routines")
        assert "habit-forge" in result, f"Expected habit-forge in {result}"

    def test_safety_question_selects_sentinel_prime(self, ds: DomainSelector):
        """'safety alignment' should select sentinel-prime."""
        result = ds.score_agents("safety alignment protection")
        assert "sentinel-prime" in result, f"Expected sentinel-prime in {result}"


# ------------------------------------------------------------------
# Fallback tests
# ------------------------------------------------------------------


class TestFallback:
    """Fallback to triad + arbiter when few agents match."""

    def test_generic_question_falls_back(self, ds: DomainSelector):
        """A question with no keyword overlap should return fallback agents."""
        result = ds.score_agents("what should we have for lunch")
        for fb in DEFAULT_FALLBACK_AGENTS:
            assert fb in result, f"Expected fallback agent {fb} in {result}"

    def test_empty_question_returns_fallback(self, ds: DomainSelector):
        """An empty question should return fallback agents."""
        result = ds.score_agents("")
        assert result == DEFAULT_FALLBACK_AGENTS

    def test_fallback_pads_to_min_votes(self, ds: DomainSelector):
        """When fewer than min_votes agents match, fallback agents pad the list."""
        # 'coding' only matches coder (1 agent), fallback should pad
        ds.min_votes = 4
        result = ds.score_agents("coding")
        assert len(result) >= 4, f"Expected >=4 agents, got {len(result)}: {result}"

    def test_custom_fallback_agents(self):
        """Custom fallback agents should be used instead of defaults."""
        ds = DomainSelector(
            characters_dir=_CHARACTERS_DIR,
            fallback_agents=["alice", "bob"],
        )
        result = ds.score_agents("no match xyz")
        assert result == ["alice", "bob"]


# ------------------------------------------------------------------
# Top-N parameter
# ------------------------------------------------------------------


class TestTopN:
    """Configurable top-N selection."""

    def test_top_n_limits_results(self, ds: DomainSelector):
        """Requesting top_n=3 should return at most 3 agents."""
        result = ds.score_agents("security analysis", top_n=3)
        assert len(result) <= 3

    def test_default_top_n(self):
        """Default top_n should be 6."""
        ds = DomainSelector(characters_dir=_CHARACTERS_DIR)
        assert ds.default_top_n == 6


# ------------------------------------------------------------------
# Character loading
# ------------------------------------------------------------------


class TestCharacterLoading:
    """Verify character file loading behavior."""

    def test_agents_without_topics_excluded(self, ds: DomainSelector):
        """Agents without topics (catalyst, chronos, coordinator, nexus)
        should not appear in the internal agent dict."""
        for agent in ["catalyst", "chronos", "coordinator", "nexus"]:
            assert agent not in ds._agents, f"{agent} should be excluded"

    def test_agents_with_topics_loaded(self, ds: DomainSelector):
        """All 18 agents with topics should be loaded."""
        assert len(ds._agents) == 18, f"Expected 18, got {len(ds._agents)}"

    def test_nonexistent_directory_returns_empty(self):
        """A missing characters directory should produce an empty agent dict."""
        ds = DomainSelector(characters_dir="/nonexistent/path")
        assert len(ds._agents) == 0


# ------------------------------------------------------------------
# Performance
# ------------------------------------------------------------------


class TestPerformance:
    """Performance: score_agents must complete in <100ms."""

    def test_1000_iterations_under_one_second(self, ds: DomainSelector):
        """1000 iterations of score_agents must complete in <1s total."""
        start = time.perf_counter()
        for _ in range(1000):
            ds.score_agents("security analysis code review")
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"1000 iterations took {elapsed:.3f}s (limit 1s)"


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------


class TestEdgeCases:
    """Boundary conditions and special inputs."""

    def test_case_insensitive(self, ds: DomainSelector):
        """Scoring should be case-insensitive."""
        lower = ds.score_agents("SECURITY ANALYSIS")
        upper = ds.score_agents("security analysis")
        assert set(lower) == set(upper)

    def test_special_characters_in_question(self, ds: DomainSelector):
        """Special characters should not break tokenization."""
        result = ds.score_agents("security!!! @#$ analysis???")
        assert "alpha" in result

    def test_single_word_match(self, ds: DomainSelector):
        """A single matching keyword should still select relevant agents."""
        result = ds.score_agents("refactoring")
        assert "coder" in result
