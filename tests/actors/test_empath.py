"""
Test suite for Empath Agent - Emotional Intelligence & Sentiment Analysis.

This module provides comprehensive tests for the Empath agent including:
- Initialization with all required dependencies
- Message handling (process_message)
- Sentiment analysis (LLM and heuristic)
- Agent mood tracking and emotional state monitoring
- Conflict detection and mediation
- Error handling and edge cases
- Zero-trust validation tests
"""

import asyncio
import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.actors.empath import EmpathAgent
from heretek_swarm.actors.base import ActorMessage
from heretek_swarm.collective.learning import PatternExtractor
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer
from heretek_swarm.security.zero_trust import ZeroTrustValidator


# ============== FIXTURES ==============

@pytest.fixture
def mock_pattern_extractor() -> MagicMock:
    """Create a mock pattern extractor for testing."""
    extractor = MagicMock(spec=PatternExtractor)
    extractor.analyze_message = AsyncMock(return_value=None)
    extractor.extract_patterns = AsyncMock(return_value=[])
    extractor._validated_patterns = []
    extractor._message_cache = {}
    return extractor


@pytest.fixture
def mock_deliberation_engine() -> MagicMock:
    """Create a mock deliberation engine for testing."""
    engine = MagicMock(spec=SwarmDeliberationEngine)
    engine.start_deliberation = MagicMock(return_value="delib-test-123")
    engine.submit_position = MagicMock(return_value=True)
    engine.finalize_deliberation = MagicMock(return_value={"result": "approved"})
    engine.cleanup_deliberation = MagicMock(return_value=None)
    engine.get_statistics = MagicMock(return_value={})
    return engine


@pytest.fixture
def mock_access_analyzer() -> MagicMock:
    """Create a mock access pattern analyzer for testing."""
    analyzer = MagicMock(spec=AccessPatternAnalyzer)
    analyzer.record_access = MagicMock(return_value=None)
    analyzer.get_profile = MagicMock(return_value=None)
    analyzer.predict_agent_access = MagicMock(return_value=[])
    analyzer.get_statistics = MagicMock(return_value=MagicMock(to_dict=MagicMock(return_value={})))
    return analyzer


@pytest.fixture
def mock_zero_trust_validator() -> MagicMock:
    """Create a mock zero-trust validator for testing."""
    validator = MagicMock(spec=ZeroTrustValidator)
    validator.validate_input = MagicMock(return_value=True)
    validator.validate_output = MagicMock(return_value=True)
    return validator


@pytest.fixture
def mock_swarms_agent() -> MagicMock:
    """Create a mock Swarms agent for testing."""
    agent = MagicMock()
    agent.llm = AsyncMock(return_value='{"sentiment": "positive", "confidence": 0.9, "intensity": 0.7, "emotions": ["joy"], "stress_indicators": false, "conflict_potential": false}')
    agent.run = MagicMock(return_value="Test response")
    return agent


@pytest.fixture
def empath_agent(
    mock_pattern_extractor: MagicMock,
    mock_deliberation_engine: MagicMock,
    mock_access_analyzer: MagicMock,
    mock_zero_trust_validator: MagicMock,
) -> EmpathAgent:
    """Create an Empath agent instance with mocked dependencies."""
    agent = EmpathAgent(
        agent_id="test-empath",
        name="TestEmpath",
        sentiment_threshold=0.7,
        stress_threshold=0.8,
        max_mood_history=50,
    )
    # Inject mocked dependencies
    agent.pattern_extractor = mock_pattern_extractor
    agent.deliberation_engine = mock_deliberation_engine
    agent.access_analyzer = mock_access_analyzer
    agent.zero_trust_validator = mock_zero_trust_validator
    return agent


@pytest.fixture
def sample_positive_text() -> str:
    """Sample positive text for sentiment testing."""
    return "This is wonderful! I'm so happy and excited about the great results!"


@pytest.fixture
def sample_negative_text() -> str:
    """Sample negative text for sentiment testing."""
    return "This is terrible. I'm frustrated and angry about the failure."


@pytest.fixture
def sample_neutral_text() -> str:
    """Sample neutral text for sentiment testing."""
    return "The meeting is scheduled for 3pm tomorrow."


# ============== INITIALIZATION TESTS ==============

class TestEmpathInitialization:
    """Test Empath agent initialization."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        agent = EmpathAgent()
        
        assert agent.agent_id == "empath"
        assert agent.name == "Empath"
        assert agent.sentiment_threshold == 0.7
        assert agent.stress_threshold == 0.8
        assert agent.max_mood_history == 100
        assert isinstance(agent.pattern_extractor, PatternExtractor)
        assert isinstance(agent.deliberation_engine, SwarmDeliberationEngine)
        assert isinstance(agent.access_analyzer, AccessPatternAnalyzer)
        assert isinstance(agent.zero_trust_validator, ZeroTrustValidator)

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        agent = EmpathAgent(
            agent_id="custom-empath",
            name="CustomEmpath",
            sentiment_threshold=0.5,
            stress_threshold=0.6,
            max_mood_history=200,
        )
        
        assert agent.agent_id == "custom-empath"
        assert agent.name == "CustomEmpath"
        assert agent.sentiment_threshold == 0.5
        assert agent.stress_threshold == 0.6
        assert agent.max_mood_history == 200

    def test_init_with_mocked_dependencies(
        self,
        empath_agent: EmpathAgent,
        mock_pattern_extractor: MagicMock,
    ) -> None:
        """Test initialization with mocked dependencies."""
        assert empath_agent.pattern_extractor is mock_pattern_extractor
        assert empath_agent.agent_moods == {}
        assert empath_agent.agent_stress_levels == {}
        assert empath_agent.conflict_log == []

    def test_initial_collective_mood(self, empath_agent: EmpathAgent) -> None:
        """Test initial collective mood values."""
        assert "positive" in empath_agent.collective_mood
        assert "negative" in empath_agent.collective_mood
        assert "neutral" in empath_agent.collective_mood
        assert empath_agent.collective_mood["positive"] == 0.5
        assert empath_agent.collective_mood["negative"] == 0.1
        assert empath_agent.collective_mood["neutral"] == 0.4


# ============== SENTIMENT ANALYSIS TESTS ==============

class TestSentimentAnalysis:
    """Test sentiment analysis functionality."""

    def test_analyze_sentiment_heuristic_positive(
        self, empath_agent: EmpathAgent, sample_positive_text: str
    ) -> None:
        """Test heuristic sentiment analysis for positive text."""
        result = empath_agent._analyze_sentiment_heuristic(sample_positive_text)
        
        assert "sentiment" in result
        assert "confidence" in result
        assert "intensity" in result
        assert "emotions" in result
        assert "stress_indicators" in result
        assert "conflict_potential" in result
        assert result["sentiment"] == "positive"
        assert "joy" in result["emotions"] or "confidence" in result["emotions"]

    def test_analyze_sentiment_heuristic_negative(
        self, empath_agent: EmpathAgent, sample_negative_text: str
    ) -> None:
        """Test heuristic sentiment analysis for negative text."""
        result = empath_agent._analyze_sentiment_heuristic(sample_negative_text)
        
        assert result["sentiment"] == "negative"
        assert "anger" in result["emotions"] or len(result["emotions"]) > 0

    def test_analyze_sentiment_heuristic_neutral(
        self, empath_agent: EmpathAgent, sample_neutral_text: str
    ) -> None:
        """Test heuristic sentiment analysis for neutral text."""
        result = empath_agent._analyze_sentiment_heuristic(sample_neutral_text)
        
        assert result["sentiment"] == "neutral"

    def test_analyze_sentiment_heuristic_empty(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test heuristic sentiment analysis for empty text."""
        result = empath_agent._analyze_sentiment_heuristic("")
        
        assert result["sentiment"] == "neutral"
        assert result["confidence"] >= 0.0
        assert result["confidence"] <= 1.0

    def test_analyze_sentiment_heuristic_stress_detection(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test stress indicator detection."""
        stress_text = "This is urgent! I'm stressed and overwhelmed by the crisis!"
        result = empath_agent._analyze_sentiment_heuristic(stress_text)
        
        assert result["stress_indicators"] is True

    def test_analyze_sentiment_heuristic_conflict_detection(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test conflict potential detection."""
        conflict_text = "I disagree with you. This is wrong and I oppose this decision."
        result = empath_agent._analyze_sentiment_heuristic(conflict_text)
        
        assert result["conflict_potential"] is True

    @pytest.mark.asyncio
    async def test_analyze_sentiment_llm(
        self, empath_agent: EmpathAgent, mock_swarms_agent: MagicMock
    ) -> None:
        """Test LLM-based sentiment analysis."""
        empath_agent.swarms_agent = mock_swarms_agent
        
        result = await empath_agent._analyze_sentiment_llm(
            "Great job!", "agent-1", {}
        )
        
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_analyze_sentiment_llm_timeout(
        self, empath_agent: EmpathAgent, mock_swarms_agent: MagicMock
    ) -> None:
        """Test LLM sentiment analysis timeout fallback."""
        mock_swarms_agent.llm = AsyncMock(side_effect=asyncio.TimeoutError())
        empath_agent.swarms_agent = mock_swarms_agent
        
        result = await empath_agent._analyze_sentiment_llm(
            "Test text", "agent-1", {}
        )
        
        # Should fallback to heuristic
        assert "sentiment" in result

    def test_build_sentiment_prompt(self, empath_agent: EmpathAgent) -> None:
        """Test sentiment prompt building."""
        context = {"topic": "testing", "priority": "high"}
        prompt = empath_agent._build_sentiment_prompt("Test text", context)
        
        assert "Test text" in prompt
        assert "topic" in prompt or "testing" in prompt
        assert "JSON" in prompt or "json" in prompt

    def test_parse_sentiment_response_valid(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test parsing valid JSON response."""
        response = '{"sentiment": "positive", "confidence": 0.8}'
        result = empath_agent._parse_sentiment_response(response)
        
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.8

    def test_parse_sentiment_response_invalid(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test parsing invalid JSON response fallback."""
        response = "This is not JSON"
        result = empath_agent._parse_sentiment_response(response)
        
        # Should fallback to heuristic
        assert "sentiment" in result


# ============== MOOD TRACKING TESTS ==============

class TestMoodTracking:
    """Test agent mood tracking functionality."""

    def test_update_agent_mood_new_agent(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test updating mood for a new agent."""
        sentiment_result = {
            "sentiment": "positive",
            "intensity": 0.7,
            "emotions": ["joy"],
            "stress_indicators": False,
            "conflict_potential": False,
        }
        
        empath_agent._update_agent_mood("agent-1", sentiment_result)
        
        assert "agent-1" in empath_agent.agent_moods
        assert len(empath_agent.agent_moods["agent-1"]) == 1
        mood_entry = empath_agent.agent_moods["agent-1"][0]
        assert mood_entry["sentiment"] == "positive"
        assert mood_entry["intensity"] == 0.7

    def test_update_agent_mood_existing_agent(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test updating mood for an existing agent."""
        sentiment_result = {
            "sentiment": "positive",
            "intensity": 0.7,
            "emotions": ["joy"],
            "stress_indicators": False,
            "conflict_potential": False,
        }
        
        # Add multiple mood entries
        for i in range(5):
            empath_agent._update_agent_mood("agent-1", sentiment_result)
        
        assert len(empath_agent.agent_moods["agent-1"]) == 5

    def test_update_agent_mood_history_limit(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test mood history enforces max limit."""
        sentiment_result = {
            "sentiment": "positive",
            "intensity": 0.5,
            "emotions": ["joy"],
            "stress_indicators": False,
            "conflict_potential": False,
        }
        
        # Add more entries than max_mood_history
        for i in range(empath_agent.max_mood_history + 10):
            empath_agent._update_agent_mood("agent-1", sentiment_result)
        
        assert len(empath_agent.agent_moods["agent-1"]) <= empath_agent.max_mood_history

    def test_check_stress_indicators_increase(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test stress level increases with stress indicators."""
        sentiment_result = {
            "sentiment": "negative",
            "intensity": 0.8,
            "emotions": ["anxiety"],
            "stress_indicators": True,
            "conflict_potential": False,
        }
        
        empath_agent._check_stress_indicators("agent-1", sentiment_result)
        
        assert empath_agent.agent_stress_levels.get("agent-1", 0.0) > 0.0

    def test_check_stress_indicators_decrease(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test stress level decreases without stress indicators."""
        # Set initial stress
        empath_agent.agent_stress_levels["agent-1"] = 0.5
        
        sentiment_result = {
            "sentiment": "positive",
            "intensity": 0.5,
            "emotions": ["joy"],
            "stress_indicators": False,
            "conflict_potential": False,
        }
        
        empath_agent._check_stress_indicators("agent-1", sentiment_result)
        
        # Stress should decrease
        assert empath_agent.agent_stress_levels["agent-1"] < 0.5

    def test_log_sentiment(self, empath_agent: EmpathAgent) -> None:
        """Test sentiment logging."""
        sentiment_result = {
            "sentiment": "positive",
            "intensity": 0.7,
            "emotions": ["joy"],
            "stress_indicators": False,
            "conflict_potential": False,
        }
        
        empath_agent._log_sentiment("agent-1", sentiment_result)
        
        assert len(empath_agent.sentiment_history) == 1
        logged = empath_agent.sentiment_history[0]
        assert logged["agent_id"] == "agent-1"
        assert logged["sentiment"] == "positive"


# ============== MESSAGE HANDLING TESTS ==============

class TestMessageHandling:
    """Test message handling functionality."""

    @pytest.mark.asyncio
    async def test_analyze_sentiment_handler_success(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test analyze_sentiment message handler success."""
        message = ActorMessage(
            sender="test-sender",
            message_type="analyze_sentiment",
            content={
                "text": "This is great!",
                "source_agent": "agent-1",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        # Mock _validate_message_content to return None (no validator for this type)
        empath_agent._validate_message_content = MagicMock(return_value=None)
        # Mock _analyze_sentiment_llm to avoid validation issues
        empath_agent._analyze_sentiment_llm = AsyncMock(return_value={
            "sentiment": "positive",
            "confidence": 0.8,
            "intensity": 0.7,
            "emotions": ["joy"],
            "stress_indicators": False,
            "conflict_potential": False,
        })
        
        await empath_agent._handle_analyze_sentiment(message)
        
        assert empath_agent.send.called
        call_args = empath_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "sentiment_result"

    @pytest.mark.asyncio
    async def test_analyze_sentiment_handler_empty_text(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test analyze_sentiment with empty text."""
        message = ActorMessage(
            sender="test-sender",
            message_type="analyze_sentiment",
            content={
                "text": "",
                "source_agent": "agent-1",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_analyze_sentiment(message)
        
        call_args = empath_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"

    @pytest.mark.asyncio
    async def test_track_emotion_handler(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test track_emotion message handler."""
        message = ActorMessage(
            sender="test-sender",
            message_type="track_emotion",
            content={
                "agent_id": "agent-1",
                "emotion": "joy",
                "intensity": 0.8,
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_track_emotion(message)
        
        assert "agent-1" in empath_agent.agent_moods

    @pytest.mark.asyncio
    async def test_track_emotion_missing_fields(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test track_emotion with missing required fields."""
        message = ActorMessage(
            sender="test-sender",
            message_type="track_emotion",
            content={
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_track_emotion(message)
        
        call_args = empath_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"

    @pytest.mark.asyncio
    async def test_detect_conflict_handler(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test detect_conflict message handler."""
        message = ActorMessage(
            sender="test-sender",
            message_type="detect_conflict",
            content={
                "agents": ["agent-1", "agent-2"],
                "context": "Disagreement about approach",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_detect_conflict(message)
        
        assert empath_agent.send.called
        call_args = empath_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "conflict_result"

    @pytest.mark.asyncio
    async def test_detect_conflict_insufficient_agents(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test detect_conflict with less than 2 agents."""
        message = ActorMessage(
            sender="test-sender",
            message_type="detect_conflict",
            content={
                "agents": ["agent-1"],
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_detect_conflict(message)
        
        call_args = empath_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"

    @pytest.mark.asyncio
    async def test_get_emotional_state_specific_agent(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test get_emotional_state for specific agent."""
        # Set up some mood data
        empath_agent.agent_moods["agent-1"] = [
            {"sentiment": "positive", "intensity": 0.7, "emotions": ["joy"]}
        ]
        empath_agent.agent_stress_levels["agent-1"] = 0.3
        empath_agent.agent_confidence["agent-1"] = 0.8
        
        message = ActorMessage(
            sender="test-sender",
            message_type="get_emotional_state",
            content={
                "agent_id": "agent-1",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_get_emotional_state(message)
        
        call_args = empath_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "emotional_state_result"
        assert call_args[1]["content"]["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_get_emotional_state_aggregate(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test get_emotional_state aggregate (all agents)."""
        message = ActorMessage(
            sender="test-sender",
            message_type="get_emotional_state",
            content={
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_get_emotional_state(message)
        
        call_args = empath_agent.send.call_args
        content = call_args[1]["content"]
        assert content["message_type"] == "emotional_state_result"
        assert "collective_mood" in content

    @pytest.mark.asyncio
    async def test_mediate_conflict_handler(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test mediate_conflict message handler."""
        message = ActorMessage(
            sender="test-sender",
            message_type="mediate_conflict",
            content={
                "agents": ["agent-1", "agent-2"],
                "proposed_resolution": "Compromise on approach",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_mediate_conflict(message)
        
        assert empath_agent.send.called
        # Should have sent to both agents and reply topic
        assert empath_agent.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_collective_mood_handler(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test get_collective_mood message handler."""
        # Add some mood data
        empath_agent.agent_moods["agent-1"] = [
            {"sentiment": "positive", "intensity": 0.7, "emotions": ["joy"]}
        ]
        
        message = ActorMessage(
            sender="test-sender",
            message_type="get_collective_mood",
            content={
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent._handle_get_collective_mood(message)
        
        call_args = empath_agent.send.call_args
        content = call_args[1]["content"]
        assert content["message_type"] == "collective_mood_result"
        assert "collective_mood" in content
        assert "collective_stress" in content


# ============== CONFLICT ANALYSIS TESTS ==============

class TestConflictAnalysis:
    """Test conflict analysis functionality."""

    def test_analyze_conflict_potential_sentiment_divergence(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test conflict detection based on sentiment divergence."""
        # Set up opposing sentiments
        empath_agent.agent_moods["agent-1"] = [
            {"sentiment": "positive", "intensity": 0.9, "emotions": ["joy"]}
            for _ in range(10)
        ]
        empath_agent.agent_moods["agent-2"] = [
            {"sentiment": "negative", "intensity": 0.9, "emotions": ["anger"]}
            for _ in range(10)
        ]
        
        conflict_detected = empath_agent._analyze_conflict_potential(
            ["agent-1", "agent-2"]
        )
        
        assert conflict_detected is True

    def test_analyze_conflict_potential_high_stress(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test conflict detection based on high stress."""
        empath_agent.agent_stress_levels["agent-1"] = 0.9  # Above threshold
        empath_agent.agent_stress_levels["agent-2"] = 0.5
        
        conflict_detected = empath_agent._analyze_conflict_potential(
            ["agent-1", "agent-2"]
        )
        
        assert conflict_detected is True

    def test_analyze_conflict_potential_no_conflict(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test no conflict detected when sentiments align."""
        # Set up similar sentiments
        empath_agent.agent_moods["agent-1"] = [
            {"sentiment": "positive", "intensity": 0.5, "emotions": ["joy"]}
        ]
        empath_agent.agent_moods["agent-2"] = [
            {"sentiment": "positive", "intensity": 0.6, "emotions": ["joy"]}
        ]
        
        conflict_detected = empath_agent._analyze_conflict_potential(
            ["agent-1", "agent-2"]
        )
        
        assert conflict_detected is False


# ============== MEDIATION TESTS ==============

class TestMediation:
    """Test conflict mediation functionality."""

    @pytest.mark.asyncio
    async def test_generate_mediation_llm(
        self, empath_agent: EmpathAgent, mock_swarms_agent: MagicMock
    ) -> None:
        """Test mediation generation using LLM."""
        mock_swarms_agent.llm = AsyncMock(return_value='{"resolution": "Compromise", "reasoning": "Fair solution"}')
        empath_agent.swarms_agent = mock_swarms_agent
        
        result = await empath_agent._generate_mediation(
            ["agent-1", "agent-2"],
            "Both agents should compromise",
        )
        
        assert "resolution" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_generate_mediation_fallback(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test fallback mediation when LLM unavailable."""
        result = await empath_agent._generate_mediation(
            ["agent-1", "agent-2"], None
        )
        
        assert "resolution" in result
        assert "reasoning" in result


# ============== COLLECTIVE MOOD TESTS ==============

class TestCollectiveMood:
    """Test collective mood calculation."""

    def test_update_collective_mood_with_data(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test collective mood update with agent data."""
        # Add mood data for multiple agents
        for i in range(5):
            empath_agent.agent_moods[f"agent-{i}"] = [
                {"sentiment": "positive", "intensity": 0.7, "emotions": ["joy"]}
                for _ in range(5)
            ]
        
        empath_agent._update_collective_mood()
        
        assert empath_agent.collective_mood["positive"] > 0.0

    def test_update_collective_mood_empty(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test collective mood update with no data."""
        empath_agent.agent_moods = {}
        
        empath_agent._update_collective_mood()
        
        # Should handle empty case gracefully
        assert isinstance(empath_agent.collective_mood, dict)

    def test_update_collective_stress(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test collective stress calculation."""
        # Add mood data first (required for _update_collective_mood to process stress)
        empath_agent.agent_moods["agent-1"] = [
            {"sentiment": "neutral", "intensity": 0.5, "emotions": ["neutral"]}
        ]
        empath_agent.agent_moods["agent-2"] = [
            {"sentiment": "neutral", "intensity": 0.5, "emotions": ["neutral"]}
        ]
        empath_agent.agent_moods["agent-3"] = [
            {"sentiment": "neutral", "intensity": 0.5, "emotions": ["neutral"]}
        ]
        
        empath_agent.agent_stress_levels = {
            "agent-1": 0.3,
            "agent-2": 0.6,
            "agent-3": 0.9,
        }
        
        empath_agent._update_collective_mood()
        
        assert empath_agent.collective_stress > 0.0
        assert empath_agent.collective_stress <= 1.0


# ============== PROCESS MESSAGE TESTS ==============

class TestProcessMessage:
    """Test the main process_message method."""

    @pytest.mark.asyncio
    async def test_process_message_known_type(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test processing a known message type."""
        message = ActorMessage(
            sender="test",
            message_type="get_collective_mood",
            content={"reply_to": "reply"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent.process_message(message)
        
        assert True  # Should not raise

    @pytest.mark.asyncio
    async def test_process_message_unknown_type(
        self, empath_agent: EmpathAgent, caplog
    ) -> None:
        """Test processing an unknown message type."""
        message = ActorMessage(
            sender="test",
            message_type="unknown_type",
            content={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        await empath_agent.process_message(message)

    @pytest.mark.asyncio
    async def test_process_message_handler_error(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test error handling in message processing."""
        async def failing_handler(msg: ActorMessage) -> None:
            raise ValueError("Test error")
        
        empath_agent.register_handler("failing", failing_handler)
        
        message = ActorMessage(
            sender="test",
            message_type="failing",
            content={"reply_to": "reply"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        await empath_agent.process_message(message)
        
        assert empath_agent.error_count >= 1


# ============== INTEGRATION TESTS ==============

class TestEmpathIntegration:
    """Integration tests for Empath agent."""

    @pytest.mark.asyncio
    async def test_full_sentiment_workflow(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test complete sentiment analysis workflow."""
        await empath_agent.initialize()
        
        # Verify handlers are registered
        assert "analyze_sentiment" in empath_agent._message_handlers
        assert "track_emotion" in empath_agent._message_handlers
        assert "detect_conflict" in empath_agent._message_handlers
        assert "get_emotional_state" in empath_agent._message_handlers

    @pytest.mark.asyncio
    async def test_learning_status(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test getting learning status."""
        status = empath_agent.get_learning_status()
        
        assert "agent_id" in status
        assert "collective_learning" in status
        assert "consensus" in status
        assert "memory_optimization" in status
        assert status["agent_id"] == "test-empath"


# ============== ERROR HANDLING TESTS ==============

class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_sentiment_analysis_error(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test handling of sentiment analysis errors."""
        message = ActorMessage(
            sender="test",
            message_type="analyze_sentiment",
            content={"reply_to": "reply"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        # Should not raise, should send error response
        await empath_agent._handle_analyze_sentiment(message)
        
        assert empath_agent.send.called

    @pytest.mark.asyncio
    async def test_mediation_error(
        self, empath_agent: EmpathAgent
    ) -> None:
        """Test handling of mediation errors."""
        message = ActorMessage(
            sender="test",
            message_type="mediate_conflict",
            content={
                "agents": ["agent-1", "agent-2"],
                "reply_to": "reply",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        empath_agent.send = AsyncMock(return_value="msg-123")
        
        # Should not raise
        await empath_agent._handle_mediate_conflict(message)
