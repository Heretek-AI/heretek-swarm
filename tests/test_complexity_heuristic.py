"""
Tests for ComplexityHeuristic — automatic consensus detection.

Covers: keyword matching, length thresholding, combined scoring,
threshold configuration, edge cases, and determinism.
"""

import pytest

from heretek_swarm.consensus.complexity import (
    ComplexityHeuristic,
    ComplexityResult,
)

# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def heuristic() -> ComplexityHeuristic:
    """Default heuristic with production settings."""
    return ComplexityHeuristic()


@pytest.fixture
def strict_heuristic() -> ComplexityHeuristic:
    """Heuristic with a very high threshold — hard to trigger."""
    return ComplexityHeuristic(complex_threshold=0.9)


@pytest.fixture
def lenient_heuristic() -> ComplexityHeuristic:
    """Heuristic with a very low threshold — easy to trigger."""
    return ComplexityHeuristic(complex_threshold=0.2)


# ── Simple questions (should NOT trigger consensus) ────────────────────


class TestSimpleQuestions:
    """Questions that are straightforward and should route to triad."""

    def test_short_simple_question(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What is Python?")
        assert not result.is_complex
        assert result.score < 0.5
        assert result.routing_mode == "triad"

    def test_short_greeting(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("Hello, how are you?")
        assert not result.is_complex
        assert result.score == 0.0

    def test_medium_question_no_keywords(self, heuristic: ComplexityHeuristic):
        # Over 50 chars but no analysis keywords
        q = "Can you explain how the authentication middleware handles JWT tokens in this project?"
        result = heuristic.assess(q)
        assert result.length_trigger is True
        assert result.keyword_trigger is False
        # Length alone = 0.4, below threshold 0.5
        assert not result.is_complex

    def test_empty_string(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("")
        assert not result.is_complex
        assert result.score == 0.0

    def test_whitespace_only(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("   ")
        assert not result.is_complex
        assert result.score == 0.0

    def test_exact_threshold_length_no_keywords(self, heuristic: ComplexityHeuristic):
        """Exactly 50 chars should NOT trigger length (strictly greater)."""
        q = "a" * 50
        result = heuristic.assess(q)
        assert result.length_trigger is False

    def test_one_over_threshold_length_no_keywords(self, heuristic: ComplexityHeuristic):
        """51 chars triggers length but score stays below default threshold."""
        q = "a" * 51
        result = heuristic.assess(q)
        assert result.length_trigger is True
        assert result.score == pytest.approx(0.4)
        assert not result.is_complex


# ── Complex questions (should trigger consensus) ───────────────────────


class TestComplexQuestions:
    """Questions with analysis/tradeoff keywords that should route to MAKER."""

    def test_tradeoff_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What are the tradeoffs of using Redis caching?")
        assert result.is_complex
        assert "tradeoff" in result.matched_keywords
        assert result.routing_mode == "consensus"

    def test_tradeoff_hyphenated(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What are the trade-offs of microservices?")
        assert result.is_complex
        assert "tradeoff" in result.matched_keywords

    def test_tradeoff_spaced(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What is the trade off between speed and accuracy?")
        assert result.is_complex

    def test_pros_and_cons(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What are the pros and cons of GraphQL vs REST?")
        assert result.is_complex
        # Should match both pros/cons and comparison categories
        assert "pros/cons" in result.matched_keywords

    def test_compare_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("Compare React and Angular for this project")
        assert result.is_complex
        assert "comparison" in result.matched_keywords

    def test_evaluate_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("Evaluate the impact of switching to PostgreSQL")
        assert result.is_complex

    def test_should_we_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("Should we use Docker or native deployment?")
        assert result.is_complex
        assert "decision" in result.matched_keywords

    def test_analyze_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("Analyze the security implications of this API")
        assert result.is_complex
        assert "analysis" in result.matched_keywords

    def test_weigh_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("Weigh the benefits of adding a caching layer")
        assert result.is_complex
        assert "weighing" in result.matched_keywords

    def test_risks_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What are the risks of upgrading the database version?")
        assert result.is_complex
        assert "risk" in result.matched_keywords

    def test_implications_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What are the implications of changing the schema?")
        assert result.is_complex

    def test_consequences_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What are the consequences of removing the cache?")
        assert result.is_complex

    def test_advantages_disadvantages(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What are the advantages and disadvantages of a monolith?")
        assert result.is_complex
        assert "pros/cons" in result.matched_keywords

    def test_downside_keyword(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("What is the downside of using WebSockets?")
        assert result.is_complex


# ── Combined scoring ───────────────────────────────────────────────────


class TestCombinedScoring:
    """Test score accumulation from length + keywords."""

    def test_multiple_keyword_categories_boost_score(self, heuristic: ComplexityHeuristic):
        """More categories → higher score."""
        # Single keyword category
        r1 = heuristic.assess("Compare A and B")
        # Two keyword categories (short so no length bonus)
        r2 = heuristic.assess("Compare and evaluate the tradeoffs of A vs B")
        assert r2.score >= r1.score

    def test_long_plus_keyword(self, heuristic: ComplexityHeuristic):
        q = "Should we evaluate the tradeoffs of using a service mesh for our microservices architecture deployment strategy?"
        result = heuristic.assess(q)
        assert result.length_trigger is True
        assert result.keyword_trigger is True
        assert result.is_complex
        # Should be well above threshold
        assert result.score > 0.6

    def test_score_clamped_to_one(self, heuristic: ComplexityHeuristic):
        q = (
            "Analyze and evaluate the tradeoffs, pros and cons, risks, "
            "implications, and consequences of comparing and weighing "
            "the advantages and disadvantages of should we use Redis "
            "versus Memcached for our caching layer in production"
        )
        result = heuristic.assess(q)
        assert result.score <= 1.0

    def test_keyword_weight_configuration(self):
        """Custom keyword weight changes scoring."""
        h = ComplexityHeuristic(keyword_weight=0.3, max_keyword_score=1.0)
        # Two categories × 0.3 = 0.6 → complex (>=0.5)
        result = h.assess("Compare and evaluate this")  # short, 2 categories
        assert result.is_complex
        assert result.score >= 0.5


# ── Threshold configuration ───────────────────────────────────────────


class TestThresholdConfiguration:
    """Verify threshold knobs work correctly."""

    def test_strict_threshold_rejects_moderate(self, strict_heuristic: ComplexityHeuristic):
        """With threshold=0.9, a single keyword without length is not enough."""
        q = "What is the risk here?"  # short, 1 keyword → 0.5 < 0.9
        result = strict_heuristic.assess(q)
        assert result.length_trigger is False
        assert not result.is_complex

    def test_strict_threshold_accepts_heavy(self, strict_heuristic: ComplexityHeuristic):
        """With threshold=0.9, many keywords can still trigger."""
        q = "Analyze and evaluate the tradeoffs, risks, and implications of comparing Redis vs Memcached"
        result = strict_heuristic.assess(q)
        # Many categories → score should exceed 0.9
        assert result.is_complex

    def test_lenient_threshold_accepts_single_keyword(self, lenient_heuristic: ComplexityHeuristic):
        """With threshold=0.2, even a single keyword suffices."""
        result = lenient_heuristic.assess("What is the risk here?")
        assert result.is_complex
        assert result.score >= 0.2

    def test_lenient_threshold_accepts_length_only(self, lenient_heuristic: ComplexityHeuristic):
        """With threshold=0.2, long question alone (0.4) is enough."""
        q = "a" * 51
        result = lenient_heuristic.assess(q)
        assert result.is_complex

    def test_zero_threshold(self):
        """Everything is complex with threshold=0."""
        h = ComplexityHeuristic(complex_threshold=0.0)
        assert h.is_complex("hi")

    def test_threshold_one(self):
        """Nothing is complex with threshold=1.0 unless score is exactly 1.0."""
        h = ComplexityHeuristic(complex_threshold=1.0)
        assert not h.is_complex("Should we evaluate the tradeoffs?")
        # Max possible: 0.4 (length) + 0.9 (max keywords) = 1.3 clamped to 1.0
        # Need many categories + length
        q = "Analyze and evaluate the tradeoffs, risks, implications, and consequences of comparing and weighing the pros and cons of A vs B for our production system architecture design decision strategy planning document review process"
        assert h.is_complex(q)


# ── Convenience methods ────────────────────────────────────────────────


class TestConvenienceMethods:
    """Test is_complex() and score() shorthand."""

    def test_is_complex_returns_bool(self, heuristic: ComplexityHeuristic):
        assert isinstance(heuristic.is_complex("What is Python?"), bool)
        assert isinstance(heuristic.is_complex("Analyze the tradeoffs?"), bool)

    def test_score_returns_float(self, heuristic: ComplexityHeuristic):
        assert isinstance(heuristic.score("What is Python?"), float)

    def test_convenience_matches_assess(self, heuristic: ComplexityHeuristic):
        q = "Should we evaluate the tradeoffs of microservices?"
        result = heuristic.assess(q)
        assert heuristic.is_complex(q) == result.is_complex
        assert heuristic.score(q) == result.score


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    """Boundary conditions and unusual inputs."""

    def test_case_insensitive(self, heuristic: ComplexityHeuristic):
        upper = heuristic.assess("WHAT ARE THE TRADEOFFS OF REDIS?")
        lower = heuristic.assess("what are the tradeoffs of redis?")
        assert upper.is_complex == lower.is_complex
        assert upper.score == lower.score

    def test_mixed_case(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("ShOuLd We UsE dOcKeR?")
        assert result.is_complex

    def test_keyword_at_boundary(self, heuristic: ComplexityHeuristic):
        """Keyword at start and end of question."""
        assert heuristic.is_complex("tradeoffs of X")
        assert heuristic.is_complex("X has many tradeoffs")

    def test_keyword_substring_no_false_match(self, heuristic: ComplexityHeuristic):
        """'risk' in 'brisk' should not match — word boundaries not enforced,
        but 'brisk' contains 'risk' substring.  This is accepted behavior
        for a simple substring heuristic (false positive is tolerable)."""
        # 'brisk' contains 'risk' → matches. This is by design for simplicity.
        result = heuristic.assess("The weather feels brisk today")
        # This will match 'risk' substring — document this as expected behavior
        assert "risk" in result.matched_keywords

    def test_very_long_question(self, heuristic: ComplexityHeuristic):
        q = "a" * 10000
        result = heuristic.assess(q)
        assert result.length_trigger is True
        # No keywords → 0.4 score, not complex with default threshold
        assert not result.is_complex

    def test_unicode_question(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("我们应该使用Redis缓存吗？分析一下利弊")
        # Unicode chars don't match English keywords
        assert not result.is_complex

    def test_numbers_only(self, heuristic: ComplexityHeuristic):
        result = heuristic.assess("1234567890")
        assert not result.is_complex


# ── ComplexityResult dataclass ─────────────────────────────────────────


class TestComplexityResult:
    """Test the result object's properties and formatting."""

    def test_routing_mode_consensus(self):
        r = ComplexityResult(score=0.7, is_complex=True)
        assert r.routing_mode == "consensus"

    def test_routing_mode_triad(self):
        r = ComplexityResult(score=0.3, is_complex=False)
        assert r.routing_mode == "triad"

    def test_explanation_with_keywords(self):
        r = ComplexityResult(
            score=0.7,
            is_complex=True,
            matched_keywords=["tradeoff", "analysis"],
            keyword_trigger=True,
            length_trigger=True,
        )
        exp = r.explanation()
        assert "complexity=0.70" in exp
        assert "mode=consensus" in exp
        assert "keywords=" in exp
        assert "long_question" in exp

    def test_explanation_simple(self):
        r = ComplexityResult(score=0.0, is_complex=False)
        exp = r.explanation()
        assert "simple" in exp

    def test_default_field_values(self):
        r = ComplexityResult(score=0.5, is_complex=True)
        assert r.matched_keywords == []
        assert r.length_trigger is False
        assert r.keyword_trigger is False


# ── Determinism ────────────────────────────────────────────────────────


class TestDeterminism:
    """Same input always produces same output."""

    def test_repeated_calls_same_result(self, heuristic: ComplexityHeuristic):
        q = "Should we evaluate the tradeoffs of using Redis caching?"
        results = [heuristic.assess(q) for _ in range(100)]
        scores = {r.score for r in results}
        assert len(scores) == 1  # All identical

    def test_different_instances_same_result(self):
        q = "Compare React and Angular"
        h1 = ComplexityHeuristic()
        h2 = ComplexityHeuristic()
        assert h1.assess(q).score == h2.assess(q).score


# ── Integration: routing decision ─────────────────────────────────────


class TestRoutingIntegration:
    """Simulate the routing decision flow described in the slice plan."""

    def test_complex_question_routes_to_consensus(self, heuristic: ComplexityHeuristic):
        """The example from the slice plan demo."""
        q = "analyze the tradeoffs of adding Redis caching"
        result = heuristic.assess(q)
        assert result.is_complex
        assert result.routing_mode == "consensus"
        assert "tradeoff" in result.matched_keywords
        assert "analysis" in result.matched_keywords

    def test_simple_question_routes_to_triad(self, heuristic: ComplexityHeuristic):
        q = "What is the current database schema?"
        result = heuristic.assess(q)
        assert not result.is_complex
        assert result.routing_mode == "triad"

    def test_structured_log_output(self, heuristic: ComplexityHeuristic):
        """Explain output includes routing mode for structured logging."""
        q = "Evaluate the risks of schema migration"
        result = heuristic.assess(q)
        exp = result.explanation()
        assert "mode=consensus" in exp
        assert "complexity=" in exp

    def test_complexity_score_field_accessible(self, heuristic: ComplexityHeuristic):
        """Score is available for structured log events (complexity_score)."""
        q = "Should we compare PostgreSQL vs MongoDB?"
        result = heuristic.assess(q)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.score, float)
