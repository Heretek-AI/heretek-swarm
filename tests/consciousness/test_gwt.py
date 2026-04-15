"""Tests for GWT (Global Workspace Theory) Broadcast."""

import pytest
import time

from heretek_swarm.consciousness.gwt import (
    AgentRateLimiter,
    GWTConfig,
    GWTContent,
    GlobalWorkspaceBroadcast,
    GWTSalienceMetrics,
    RateLimitConfig,
    SalienceLevel,
    calculate_salience,
    create_gwt_content,
)


class TestGWTSalienceMetrics:
    """Test salience metrics calculation."""

    def test_salience_metrics_defaults(self):
        """Test default salience metrics."""
        metrics = GWTSalienceMetrics()
        assert metrics.novelty == 0.0
        assert metrics.relevance == 0.0
        assert metrics.overall_salience == 0.0
        assert metrics.salience_level == SalienceLevel.MINIMAL

    def test_salience_metrics_full(self):
        """Test salience metrics with full values."""
        metrics = GWTSalienceMetrics(
            novelty=0.95,
            relevance=0.95,
            urgency=0.95,
            impact=0.95,
            confidence=0.95,
        )
        assert metrics.overall_salience > 0.9
        assert metrics.salience_level == SalienceLevel.CRITICAL

    def test_salience_level_classification(self):
        """Test salience level thresholds."""
        test_cases = [
            (0.95, SalienceLevel.CRITICAL),
            (0.75, SalienceLevel.HIGH),
            (0.55, SalienceLevel.ELEVATED),
            (0.35, SalienceLevel.NORMAL),
            (0.15, SalienceLevel.LOW),
            (0.05, SalienceLevel.MINIMAL),
        ]
        for score, expected_level in test_cases:
            metrics = GWTSalienceMetrics(
                novelty=score,
                relevance=score,
                urgency=score,
                impact=score,
                confidence=score,
            )
            assert metrics.salience_level == expected_level, f"Failed for score {score}"


class TestCalculateSalience:
    """Test salience calculation function."""

    def test_calculate_salience_basic(self):
        """Test basic salience calculation."""
        salience = calculate_salience(
            novelty=0.5,
            relevance=0.6,
            urgency=0.4,
            impact=0.7,
            confidence=0.8,
        )
        assert isinstance(salience, GWTSalienceMetrics)
        assert salience.novelty == 0.5
        assert salience.overall_salience > 0

    def test_calculate_salience_bounds(self):
        """Test salience values are clamped to 0-1."""
        salience = calculate_salience(
            novelty=1.5,
            relevance=-0.5,
            urgency=0.5,
            impact=0.5,
            confidence=0.5,
        )
        assert salience.novelty == 1.0
        assert salience.relevance == 0.0


class TestCreateGWTContent:
    """Test GWT content creation."""

    def test_create_content_basic(self):
        """Test basic content creation."""
        content = create_gwt_content(
            source_agent="test-agent",
            content_type="test",
            payload={"key": "value"},
        )
        assert content.source_agent == "test-agent"
        assert content.content_type == "test"
        assert content.payload["key"] == "value"
        assert content.content_id.startswith("gwt-")

    def test_create_content_with_salience(self):
        """Test content creation with custom salience."""
        content = create_gwt_content(
            source_agent="test-agent",
            content_type="alert",
            payload={},
            novelty=0.9,
            relevance=0.9,
            urgency=0.9,
            impact=0.9,
            confidence=0.9,
        )
        assert content.salience_metrics.salience_level == SalienceLevel.CRITICAL


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_default_config(self):
        """Test default rate limit config."""
        config = RateLimitConfig()
        assert config.max_broadcasts_per_second == 10.0
        assert config.max_broadcasts_per_minute == 100
        assert config.burst_allowance == 5

    def test_custom_config(self):
        """Test custom rate limit config."""
        config = RateLimitConfig(
            max_broadcasts_per_second=5.0,
            max_broadcasts_per_minute=50,
            burst_allowance=3,
        )
        assert config.max_broadcasts_per_second == 5.0
        assert config.max_broadcasts_per_minute == 50


class TestAgentRateLimiter:
    """Test agent rate limiter."""

    def test_rate_limiter_initial_state(self):
        """Test initial rate limiter state."""
        config = RateLimitConfig(max_broadcasts_per_second=10.0)
        limiter = AgentRateLimiter(agent_id="test", config=config)
        assert limiter.can_broadcast() is True

    def test_rate_limiter_refill(self):
        """Test token refill mechanism."""
        config = RateLimitConfig(max_broadcasts_per_second=10.0)
        limiter = AgentRateLimiter(agent_id="test", config=config)
        limiter.record_broadcast()
        time.sleep(0.15)
        assert limiter.can_broadcast() is True

    def test_rate_limiter_burst(self):
        """Test burst allowance."""
        config = RateLimitConfig(
            max_broadcasts_per_second=0.001,
            burst_allowance=3,
        )
        limiter = AgentRateLimiter(agent_id="test", config=config)
        for _ in range(3):
            limiter.record_broadcast()
        assert limiter.can_broadcast() is False


class TestGWTConfig:
    """Test GWT configuration."""

    def test_default_config(self):
        """Test default GWT config."""
        config = GWTConfig()
        assert config.subject_prefix == "gwt"
        assert config.salience_threshold == 0.3
        assert config.attention_threshold == 0.7
        assert config.broadcast_timeout_ms == 100.0
        assert config.enable_rate_limiting is True

    def test_custom_config(self):
        """Test custom GWT config."""
        config = GWTConfig(
            subject_prefix="custom",
            salience_threshold=0.5,
            attention_threshold=0.8,
            broadcast_timeout_ms=50.0,
        )
        assert config.subject_prefix == "custom"
        assert config.salience_threshold == 0.5
        assert config.attention_threshold == 0.8
        assert config.broadcast_timeout_ms == 50.0


class TestGWTContent:
    """Test GWT content dataclass."""

    def test_content_to_dict(self):
        """Test content serialization."""
        salience = calculate_salience(
            novelty=0.7,
            relevance=0.8,
            urgency=0.6,
            impact=0.75,
            confidence=0.85,
        )
        content = GWTContent(
            content_id="test-123",
            source_agent="agent-1",
            content_type="decision",
            payload={"decision": "approved"},
            salience_metrics=salience,
        )
        data = content.to_dict()
        assert data["content_id"] == "test-123"
        assert data["source_agent"] == "agent-1"
        assert data["content_type"] == "decision"
        assert data["salience_metrics"]["overall_salience"] > 0
        assert data["salience_metrics"]["salience_level"] == "high"


class TestGlobalWorkspaceBroadcast:
    """Test GWT broadcast class."""

    def test_broadcast_initialization(self):
        """Test broadcast initialization."""
        broadcast = GlobalWorkspaceBroadcast()
        assert broadcast._config is not None
        assert broadcast._subscriptions == {}
        assert broadcast._rate_limiters == {}

    def test_get_subject(self):
        """Test subject path generation."""
        broadcast = GlobalWorkspaceBroadcast(config=GWTConfig(subject_prefix="test"))
        subject = broadcast._get_subject("broadcast")
        assert subject == "test.broadcast"

    def test_rate_limiter_creation(self):
        """Test rate limiter creation."""
        broadcast = GlobalWorkspaceBroadcast()
        limiter = broadcast._get_rate_limiter("agent-1")
        assert limiter is not None
        assert limiter.agent_id == "agent-1"

    def test_rate_limit_status(self):
        """Test rate limit status retrieval."""
        broadcast = GlobalWorkspaceBroadcast()
        status = broadcast.get_rate_limit_status("unknown-agent")
        assert status["can_broadcast"] is True
        assert status["reason"] == "no limiter created"

    def test_stats(self):
        """Test statistics retrieval."""
        broadcast = GlobalWorkspaceBroadcast()
        stats = broadcast.get_stats()
        assert "active_subscriptions" in stats
        assert "tracked_agents" in stats
        assert "config" in stats


class TestSalienceFiltering:
    """Test salience-based content filtering."""

    def test_filter_high_salience(self):
        """Test that high salience content passes filter."""
        broadcast = GlobalWorkspaceBroadcast()
        high_salience = calculate_salience(
            novelty=0.9,
            relevance=0.9,
            urgency=0.9,
            impact=0.9,
            confidence=0.9,
        )
        content = GWTContent(
            content_id="test-1",
            source_agent="agent",
            content_type="test",
            payload={},
            salience_metrics=high_salience,
        )
        assert broadcast._filter_by_salience(content) is True

    def test_filter_low_salience(self):
        """Test that low salience content is filtered."""
        broadcast = GlobalWorkspaceBroadcast()
        low_salience = calculate_salience(
            novelty=0.1,
            relevance=0.1,
            urgency=0.1,
            impact=0.1,
            confidence=0.1,
        )
        content = GWTContent(
            content_id="test-2",
            source_agent="agent",
            content_type="test",
            payload={},
            salience_metrics=low_salience,
        )
        assert broadcast._filter_by_salience(content) is False


class TestAttentionSelection:
    """Test attention selection mechanism."""

    def test_select_single_winner(self):
        """Test single attention winner selection."""
        broadcast = GlobalWorkspaceBroadcast()
        contents = []
        for i in range(3):
            salience = calculate_salience(
                novelty=0.5 + (i * 0.15),
                relevance=0.5,
                urgency=0.5,
                impact=0.5,
                confidence=0.5,
            )
            content = GWTContent(
                content_id=f"test-{i}",
                source_agent="agent",
                content_type="test",
                payload={},
                salience_metrics=salience,
            )
            contents.append(content)

        winners = broadcast._select_attention_winners(contents)
        assert len(winners) == 1
        assert winners[0].attention_winner is True
        assert contents[2] == winners[0]

    def test_select_empty_contents(self):
        """Test attention selection with empty contents."""
        broadcast = GlobalWorkspaceBroadcast()
        winners = broadcast._select_attention_winners([])
        assert winners == []


class TestBroadcastIdGeneration:
    """Test broadcast ID generation."""

    def test_unique_ids(self):
        """Test that generated IDs are unique."""
        broadcast = GlobalWorkspaceBroadcast()
        ids = [broadcast._generate_broadcast_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_id_format(self):
        """Test broadcast ID format."""
        broadcast = GlobalWorkspaceBroadcast()
        broadcast_id = broadcast._generate_broadcast_id()
        assert broadcast_id.startswith("gwt-")
        assert len(broadcast_id) == 16


class TestDeserialization:
    """Test content deserialization."""

    def test_deserialize_content(self):
        """Test content deserialization."""
        broadcast = GlobalWorkspaceBroadcast()
        data = {
            "content_id": "test-123",
            "source_agent": "agent-1",
            "content_type": "decision",
            "payload": {"key": "value"},
            "salience_metrics": {
                "novelty": 0.7,
                "relevance": 0.8,
                "urgency": 0.6,
                "impact": 0.75,
                "confidence": 0.85,
            },
            "timestamp": "2026-04-15T00:00:00Z",
            "broadcast_id": "gwt-abc123",
            "attention_winner": False,
        }
        content = broadcast._deserialize_content(data)
        assert content is not None
        assert content.content_id == "test-123"
        assert content.source_agent == "agent-1"
        assert content.salience_metrics.overall_salience > 0

    def test_deserialize_invalid_content(self):
        """Test deserialization with invalid data."""
        broadcast = GlobalWorkspaceBroadcast()
        content = broadcast._deserialize_content({"invalid": "data"})
        assert content is not None
        assert content.content_id != "invalid"
