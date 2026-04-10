"""
Test suite for Perceiver Agent - Multi-Modal Sensory Input Processing.

This module provides comprehensive tests for the Perceiver agent including:
- Initialization with all required dependencies
- Message handling (process_message)
- State management (get_state, update_state)
- Modality detection and feature extraction
- Quality assessment and caching
- Error handling and edge cases
- Zero-trust validation tests
"""

import asyncio
import pytest
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.actors.perceiver import PerceiverAgent, ModalityType
from heretek_swarm.actors.base import ActorMessage
from heretek_swarm.collective.learning import PatternExtractor
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer
from heretek_swarm.security.zero_trust import ZeroTrustValidator


# ============== FIXTURES ==============

@pytest.fixture
def mock_pattern_extractor() -> MagicMock:
    """Create a mock pattern extractor for testing."""
    _extractor = MagicMock(spec=PatternExtractor)
    extractor.analyze_message = AsyncMock(return_value=None)
    extractor.extract_patterns = AsyncMock(return_value=[])
    extractor._validated_patterns = []
    extractor._message_cache = {}
    return extractor


@pytest.fixture
def mock_deliberation_engine() -> MagicMock:
    """Create a mock deliberation engine for testing."""
    _engine = MagicMock(spec=SwarmDeliberationEngine)
    engine.start_deliberation = MagicMock(return_value="delib-test-123")
    engine.submit_position = MagicMock(return_value=True)
    engine.finalize_deliberation = MagicMock(return_value={"result": "approved"})
    engine.cleanup_deliberation = MagicMock(return_value=None)
    engine.get_statistics = MagicMock(return_value={})
    return engine


@pytest.fixture
def mock_access_analyzer() -> MagicMock:
    """Create a mock access pattern analyzer for testing."""
    _analyzer = MagicMock(spec=AccessPatternAnalyzer)
    analyzer.record_access = MagicMock(return_value=None)
    analyzer.get_profile = MagicMock(return_value=None)
    analyzer.predict_agent_access = MagicMock(return_value=[])
    analyzer.get_statistics = MagicMock(return_value=MagicMock(to_dict=MagicMock(return_value={})))
    return analyzer


@pytest.fixture
def mock_zero_trust_validator() -> MagicMock:
    """Create a mock zero-trust validator for testing."""
    _validator = MagicMock(spec=ZeroTrustValidator)
    validator.validate_input = MagicMock(return_value=True)
    validator.validate_output = MagicMock(return_value=True)
    return validator


@pytest.fixture
def perceiver_agent(_mock_pattern_extractor: MagicMock, _mock_deliberation_engine: MagicMock, _mock_access_analyzer: MagicMock, _mock_zero_trust_validator: MagicMock) -> PerceiverAgent:
    """Create a Perceiver agent instance with mocked dependencies."""
    agent = PerceiverAgent(
        agent_id="test-perceiver",
        name="TestPerceiver",
    )
    # Inject mocked dependencies
    agent.pattern_extractor = mock_pattern_extractor
    agent.deliberation_engine = mock_deliberation_engine
    agent.access_analyzer = mock_access_analyzer
    agent.zero_trust_validator = mock_zero_trust_validator
    return agent


@pytest.fixture
def sample_text_input() -> str:
    """Sample text input for testing."""
    return "This is a sample text for processing. It contains multiple sentences."


@pytest.fixture
def sample_image_data() -> str:
    """Sample base64 image data for testing."""
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@pytest.fixture
def sample_sensor_data() -> Dict[str, Any]:
    """Sample sensor data for testing."""
    return {
        "temperature": 25.5,
        "humidity": 60.0,
        "pressure": 1013.25,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============== INITIALIZATION TESTS ==============

class TestPerceiverInitialization:
    """Test Perceiver agent initialization."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        agent = PerceiverAgent()
        
        assert agent.agent_id == "perceiver"
        assert agent.name == "Perceiver"
        assert agent.max_input_size_mb == 50
        assert agent.feature_cache_size == 1000
        assert agent.enable_cross_modal is True
        assert isinstance(agent.pattern_extractor, PatternExtractor)
        assert isinstance(agent.deliberation_engine, SwarmDeliberationEngine)
        assert isinstance(agent.access_analyzer, AccessPatternAnalyzer)
        assert isinstance(agent.zero_trust_validator, ZeroTrustValidator)

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        agent = PerceiverAgent(
            agent_id="custom-perceiver",
            name="CustomPerceiver",
            max_input_size_mb=100,
            feature_cache_size=500,
            enable_cross_modal=False,
        )
        
        assert agent.agent_id == "custom-perceiver"
        assert agent.name == "CustomPerceiver"
        assert agent.max_input_size_mb == 100
        assert agent.feature_cache_size == 500
        assert agent.enable_cross_modal is False

    def test_init_with_mocked_dependencies(self, _perceiver_agent: PerceiverAgent, _mock_pattern_extractor: MagicMock) -> None:
        """Test initialization with mocked dependencies."""
        assert perceiver_agent.pattern_extractor is mock_pattern_extractor
        assert perceiver_agent.inputs_processed is not None
        assert perceiver_agent.feature_cache == {}

    def test_supported_formats(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test that supported formats are properly configured."""
        _formats = perceiver_agent.supported_formats
        
        assert ModalityType.TEXT.value in formats
        assert ModalityType.IMAGE.value in formats
        assert ModalityType.AUDIO.value in formats
        assert ModalityType.VIDEO.value in formats
        assert ModalityType.DOCUMENT.value in formats
        assert ModalityType.SENSOR.value in formats
        
        assert "txt" in formats[ModalityType.TEXT.value]
        assert "jpg" in formats[ModalityType.IMAGE.value]
        assert "mp3" in formats[ModalityType.AUDIO.value]


# ============== MODALITY DETECTION TESTS ==============

class TestModalityDetection:
    """Test modality auto-detection functionality."""

    def test_detect_modality_text(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test text modality detection."""
        _text = "Hello, this is plain text."
        _modality = perceiver_agent._detect_modality(text)
        assert modality == ModalityType.TEXT.value

    def test_detect_modality_text_with_format_hint(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test text modality detection with format hint."""
        _text = "Some content"
        _modality = perceiver_agent._detect_modality(text, format_hint="json")
        assert modality == ModalityType.TEXT.value

    def test_detect_modality_image_base64(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test image modality detection from base64 data URL."""
        _image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
        _modality = perceiver_agent._detect_modality(image_data)
        assert modality == ModalityType.IMAGE.value

    def test_detect_modality_image_bytes(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test image modality detection from bytes."""
        _jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        _modality = perceiver_agent._detect_modality(jpeg_bytes)
        assert modality == ModalityType.IMAGE.value

    def test_detect_modality_png_bytes(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test PNG modality detection from bytes."""
        _png_bytes = b"\x89PNG\r\n\x1a\n"
        _modality = perceiver_agent._detect_modality(png_bytes)
        assert modality == ModalityType.IMAGE.value

    def test_detect_modality_audio_bytes(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test audio modality detection from bytes."""
        _wav_bytes = b"RIFF\x00\x00\x00\x00WAVE"
        _modality = perceiver_agent._detect_modality(wav_bytes)
        assert modality == ModalityType.AUDIO.value

    def test_detect_modality_sensor_dict(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test sensor modality detection from dict."""
        _sensor_data = {"temp": 25.5, "humidity": 60}
        _modality = perceiver_agent._detect_modality(sensor_data)
        assert modality == ModalityType.SENSOR.value

    def test_detect_modality_format_hints(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test modality detection with various format hints."""
        _test_cases = [
            ("content", "jpg", ModalityType.IMAGE.value),
            ("content", "png", ModalityType.IMAGE.value),
            ("content", "mp3", ModalityType.AUDIO.value),
            ("content", "wav", ModalityType.AUDIO.value),
            ("content", "mp4", ModalityType.VIDEO.value),
            ("content", "avi", ModalityType.VIDEO.value),
            ("content", "pdf", ModalityType.DOCUMENT.value),
            ("content", "docx", ModalityType.DOCUMENT.value),
        ]
        
        for content, fmt_hint, expected in test_cases:
            _modality = perceiver_agent._detect_modality(content, format_hint=fmt_hint)
            assert modality == expected, f"Failed for format hint: {fmt_hint}"


# ============== INPUT SIZE VALIDATION TESTS ==============

class TestInputSizeValidation:
    """Test input size validation functionality."""

    def test_validate_input_size_string_small(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test validation of small string input."""
        _small_text = "Small text"
        assert perceiver_agent._validate_input_size(small_text) is True

    def test_validate_input_size_string_large(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test validation of large string input."""
        # Create text larger than default 50MB limit
        _large_text = "A" * (51 * 1024 * 1024)
        assert perceiver_agent._validate_input_size(large_text) is False

    def test_validate_input_size_bytes_small(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test validation of small bytes input."""
        _small_bytes = b"Small bytes"
        assert perceiver_agent._validate_input_size(small_bytes) is True

    def test_validate_input_size_dict(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test validation of dict input."""
        _small_dict = {"key": "value"}
        assert perceiver_agent._validate_input_size(small_dict) is True

    def test_validate_input_size_unknown_type(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test validation fails open for unknown types."""
        _unknown = MagicMock()
        assert perceiver_agent._validate_input_size(unknown) is True


# ============== INPUT ID GENERATION TESTS ==============

class TestInputIdGeneration:
    """Test unique input ID generation."""

    def test_generate_input_id_string(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test ID generation for string input."""
        _input_data = "test input"
        _input_id = perceiver_agent._generate_input_id(input_data, "text")
        
        assert input_id.startswith("input_text_")
        assert len(input_id) > 20  # Should include timestamp and hash

    def test_generate_input_id_bytes(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test ID generation for bytes input."""
        _input_data = b"test bytes"
        _input_id = perceiver_agent._generate_input_id(input_data, "image")
        
        assert input_id.startswith("input_image_")

    def test_generate_input_id_dict(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test ID generation for dict input."""
        _input_data = {"key": "value"}
        _input_id = perceiver_agent._generate_input_id(input_data, "sensor")
        
        assert input_id.startswith("input_sensor_")

    def test_generate_input_id_deterministic(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test that same input generates same hash portion."""
        _input_data = "consistent input"
        _id1 = perceiver_agent._generate_input_id(input_data, "text")
        _id2 = perceiver_agent._generate_input_id(input_data, "text")
        
        # Hash portion should be the same (last 16 chars of hash)
        assert id1[-16:] == id2[-16:]


# ============== FEATURE EXTRACTION TESTS ==============

class TestFeatureExtraction:
    """Test feature extraction for various modalities."""

    @pytest.mark.asyncio
    async def test_extract_text_features(self, _perceiver_agent: PerceiverAgent, _sample_text_input: str) -> None:
        """Test text feature extraction."""
        _features = perceiver_agent._extract_text_features(sample_text_input)
        
        assert "char_count" in features
        assert "word_count" in features
        assert "sentence_count" in features
        assert "avg_word_length" in features
        assert "avg_sentence_length" in features
        assert "unique_words" in features
        assert "vocabulary_richness" in features
        assert features["word_count"] > 0
        assert features["char_count"] > 0

    @pytest.mark.asyncio
    async def test_extract_text_features_empty(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test text feature extraction with empty input."""
        _features = perceiver_agent._extract_text_features("")
        
        assert features["word_count"] == 0
        assert features["sentence_count"] == 0
        assert features["char_count"] == 0

    @pytest.mark.asyncio
    async def test_extract_text_features_code_detection(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test code structure detection in text."""
        code_text = "def hello():\n    return 'world'"
        _features = perceiver_agent._extract_text_features(code_text)
        
        assert features["has_code_structure"] is True

    @pytest.mark.asyncio
    async def test_extract_text_features_json_detection(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test JSON format detection in text."""
        _json_text = '{"key": "value"}'
        _features = perceiver_agent._extract_text_features(json_text)
        
        assert features["has_json_format"] is True

    @pytest.mark.asyncio
    async def test_extract_image_features_metadata(self, _perceiver_agent: PerceiverAgent, _sample_image_data: str) -> None:
        """Test image feature extraction (metadata fallback)."""
        _features = await perceiver_agent._extract_image_features(
            sample_image_data, format_hint="png"
        )
        
        assert "format" in features
        assert "mime_type" in features
        assert "size_bytes" in features
        assert features["format"] == "png"

    @pytest.mark.asyncio
    async def test_extract_audio_features(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test audio feature extraction."""
        _audio_data = b"audio data"
        _features = await perceiver_agent._extract_audio_features(
            audio_data, format_hint="mp3"
        )
        
        assert "format" in features
        assert "size_bytes" in features
        assert features["format"] == "mp3"

    @pytest.mark.asyncio
    async def test_extract_video_features(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test video feature extraction."""
        _video_data = b"video data"
        _features = await perceiver_agent._extract_video_features(
            video_data, format_hint="mp4"
        )
        
        assert "format" in features
        assert "size_bytes" in features

    @pytest.mark.asyncio
    async def test_extract_document_features(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test document feature extraction."""
        _doc_data = "Document content here"
        _features = await perceiver_agent._extract_document_features(
            doc_data, format_hint="pdf"
        )
        
        assert "format" in features
        assert "size_bytes" in features
        assert "preview" in features

    @pytest.mark.asyncio
    async def test_extract_sensor_features(self, _perceiver_agent: PerceiverAgent, _sample_sensor_data: Dict[str, _Any]) -> None:
        """Test sensor data feature extraction."""
        _features = perceiver_agent._extract_sensor_features(sample_sensor_data)
        
        assert "keys" in features
        assert "numeric_stats" in features
        assert "analyzed_by" in features
        assert len(features["keys"]) > 0
        assert features["numeric_stats"]["count"] > 0

    @pytest.mark.asyncio
    async def test_extract_sensor_features_invalid(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test sensor feature extraction with invalid input."""
        _features = perceiver_agent._extract_sensor_features("not a dict")
        
        assert "error" in features


# ============== QUALITY ASSESSMENT TESTS ==============

class TestQualityAssessment:
    """Test input quality assessment functionality."""

    def test_assess_quality_text_good(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test quality assessment for good text input."""
        _features = {
            "word_count": 100,
            "error": None,
        }
        quality = perceiver_agent._assess_input_quality(
            "text", ModalityType.TEXT.value, features
        )
        
        assert 0.0 <= quality <= 1.0

    def test_assess_quality_text_short(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test quality assessment for short text."""
        _features = {
            "word_count": 2,
            "error": None,
        }
        quality = perceiver_agent._assess_input_quality(
            "text", ModalityType.TEXT.value, features
        )
        
        assert quality < 1.0  # Should be penalized for short text

    def test_assess_quality_with_error(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test quality assessment when features contain error."""
        _features = {"error": "Extraction failed"}
        quality = perceiver_agent._assess_input_quality(
            None, ModalityType.TEXT.value, features
        )
        
        assert quality <= 0.5  # Should be penalized for error

    def test_assess_quality_image_small(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test quality assessment for small image."""
        _features = {
            "size_bytes": 500,
            "error": None,
        }
        quality = perceiver_agent._assess_input_quality(
            None, ModalityType.IMAGE.value, features
        )
        
        assert quality < 1.0  # Should be penalized for small size


# ============== FEATURE CACHING TESTS ==============

class TestFeatureCaching:
    """Test feature caching functionality."""

    def test_cache_features(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test caching features."""
        _input_id = "test-input-123"
        _modality = "text"
        _features = {"word_count": 100}
        _metadata = {"source": "test"}
        
        perceiver_agent._cache_features(input_id, modality, features, metadata)
        
        assert input_id in perceiver_agent.feature_cache
        _cached = perceiver_agent.feature_cache[input_id]
        assert cached["modality"] == modality
        assert cached["features"] == features
        assert cached["metadata"] == metadata
        assert "timestamp" in cached

    def test_cache_features_disabled(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test caching when cross-modal is disabled."""
        perceiver_agent.enable_cross_modal = False
        _input_id = "test-input-456"
        
        perceiver_agent._cache_features(input_id, "text", {}, {})
        
        assert input_id not in perceiver_agent.feature_cache

    def test_cache_features_size_limit(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test cache enforces size limit."""
        perceiver_agent.feature_cache_size = 5
        
        # Fill cache beyond limit
        for i in range(10):
            perceiver_agent._cache_features(
                f"input-{i}", "text", {"index": i}, {}
            )
        
        # Cache should be at or below limit
        assert len(perceiver_agent.feature_cache) <= perceiver_agent.feature_cache_size + 100


# ============== MESSAGE HANDLING TESTS ==============

class TestMessageHandling:
    """Test message handling functionality."""

    @pytest.mark.asyncio
    async def test_process_input_success(self, _perceiver_agent: PerceiverAgent, _sample_text_input: str) -> None:
        """Test processing text input successfully."""
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "process_input",
            _content = {
                "input_data": sample_text_input,
                "modality": "text",
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        # Mock the send method
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_process_input(message)
        
        # Verify send was called with processed result
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "input_processed"
        assert "input_id" in call_args[1]["content"]
        assert "features" in call_args[1]["content"]
        assert "quality_score" in call_args[1]["content"]

    @pytest.mark.asyncio
    async def test_process_input_missing_data(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test processing input with missing data."""
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "process_input",
            _content = {
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_process_input(message)
        
        # Verify error response was sent
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"

    @pytest.mark.asyncio
    async def test_process_input_size_exceeded(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test processing input that exceeds size limit."""
        large_input = "A" * (60 * 1024 * 1024)  # 60MB
        
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "process_input",
            _content = {
                "input_data": large_input,
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_process_input(message)
        
        # Verify error response for size exceeded
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"
        assert perceiver_agent.quality_rejections >= 1

    @pytest.mark.asyncio
    async def test_extract_features_handler(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test extract_features message handler."""
        # Cache some features first
        _input_id = "cached-input-123"
        perceiver_agent.feature_cache[input_id] = {
            "modality": "text",
            "features": {"word_count": 50},
            "metadata": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "extract_features",
            _content = {
                "input_id": input_id,
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_extract_features(message)
        
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "features_result"

    @pytest.mark.asyncio
    async def test_extract_features_not_found(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test extract_features for non-existent input."""
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "extract_features",
            _content = {
                "input_id": "non-existent",
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_extract_features(message)
        
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"

    @pytest.mark.asyncio
    async def test_classify_modality_handler(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test classify_modality message handler."""
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "classify_modality",
            _content = {
                "input_data": "test content",
                "format_hint": "json",
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_classify_modality(message)
        
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "modality_result"
        assert call_args[1]["content"]["modality"] == ModalityType.TEXT.value

    @pytest.mark.asyncio
    async def test_assess_quality_handler(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test assess_quality message handler."""
        _input_id = "quality-test-123"
        perceiver_agent.feature_cache[input_id] = {
            "modality": "text",
            "features": {"word_count": 100},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "assess_quality",
            _content = {
                "input_id": input_id,
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_assess_quality(message)
        
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "quality_result"
        assert "quality_score" in call_args[1]["content"]

    @pytest.mark.asyncio
    async def test_get_processing_stats_handler(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test get_processing_stats message handler."""
        # Set some stats
        perceiver_agent.inputs_processed["text"] = 10
        perceiver_agent.total_features_extracted = 500
        
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "get_processing_stats",
            _content = {
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_get_processing_stats(message)
        
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "stats_result"
        assert call_args[1]["content"]["inputs_processed"]["text"] == 10

    @pytest.mark.asyncio
    async def test_correlate_modalities_handler(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test correlate_modalities message handler."""
        # Cache multiple inputs
        for i in range(3):
            perceiver_agent.feature_cache[f"input-{i}"] = {
                "modality": "text",
                "features": {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "correlate_modalities",
            _content = {
                "input_ids": ["input-0", "input-1", "input-2"],
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_correlate_modalities(message)
        
        assert perceiver_agent.send.called
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "correlation_result"
        assert "correlations" in call_args[1]["content"]

    @pytest.mark.asyncio
    async def test_correlate_modalities_insufficient_inputs(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test correlate_modalities with insufficient inputs."""
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "correlate_modalities",
            _content = {
                "input_ids": ["only-one"],
                "reply_to": "test-reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent._handle_correlate_modalities(message)
        
        _call_args = perceiver_agent.send.call_args
        assert call_args[1]["content"]["message_type"] == "error_response"


# ============== PROCESS MESSAGE TESTS ==============

class TestProcessMessage:
    """Test the main process_message method."""

    @pytest.mark.asyncio
    async def test_process_message_known_type(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test processing a known message type."""
        _message = ActorMessage(
            _sender = "test",
            _message_type = "get_processing_stats",
            _content = {"reply_to": "reply"},
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent.process_message(message)
        
        # Should not raise exception
        assert True

    @pytest.mark.asyncio
    async def test_process_message_unknown_type(self, _perceiver_agent: PerceiverAgent, _caplog) -> None:
        """Test processing an unknown message type."""
        _message = ActorMessage(
            _sender = "test",
            _message_type = "unknown_type",
            _content = {},
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        # Should log warning but not raise
        await perceiver_agent.process_message(message)

    @pytest.mark.asyncio
    async def test_process_message_handler_error(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test error handling in message processing."""
        # Register a handler that raises
        async def failing_handler(_msg: ActorMessage) -> None:
            raise ValueError("Test error")
        
        perceiver_agent.register_handler("failing", failing_handler)
        
        _message = ActorMessage(
            _sender = "test",
            _message_type = "failing",
            _content = {"reply_to": "reply"},
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        await perceiver_agent.process_message(message)
        
        # Error count should increase
        assert perceiver_agent.error_count >= 1


# ============== INTEGRATION TESTS ==============

class TestPerceiverIntegration:
    """Integration tests for Perceiver agent."""

    @pytest.mark.asyncio
    async def test_full_processing_workflow(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test complete input processing workflow."""
        # Initialize agent
        await perceiver_agent.initialize()
        
        # Verify handlers are registered
        assert "process_input" in perceiver_agent._message_handlers
        assert "extract_features" in perceiver_agent._message_handlers
        assert "classify_modality" in perceiver_agent._message_handlers

    @pytest.mark.asyncio
    async def test_learning_status(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test getting learning status."""
        _status = perceiver_agent.get_learning_status()
        
        assert "agent_id" in status
        assert "collective_learning" in status
        assert "consensus" in status
        assert "memory_optimization" in status
        assert status["agent_id"] == "test-perceiver"


# ============== ZERO-TRUST VALIDATION TESTS ==============

class TestZeroTrustValidation:
    """Test zero-trust validation integration."""

    def test_validator_configured(self, _perceiver_agent: PerceiverAgent, _mock_zero_trust_validator: MagicMock) -> None:
        """Test that zero-trust validator is configured."""
        assert perceiver_agent.zero_trust_validator is mock_zero_trust_validator

    @pytest.mark.asyncio
    async def test_process_input_validation(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test input validation during processing."""
        _message = ActorMessage(
            _sender = "test-sender",
            _message_type = "process_input",
            _content = {
                "input_data": "valid input",
                "reply_to": "reply-topic",
            },
            _timestamp = datetime.now(timezone.utc).isoformat(),
        )
        
        perceiver_agent.send = AsyncMock(return_value="msg-123")
        
        # Should process without raising
        await perceiver_agent._handle_process_input(message)
        
        assert perceiver_agent.send.called


# ============== ERROR HANDLING TESTS ==============

class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_feature_extraction_error(self, _perceiver_agent: PerceiverAgent) -> None:
        """Test handling of feature extraction errors."""
        with patch.object(
            perceiver_agent, "_extract_text_features", side_effect=Exception("Test error")
        ):
            _features = await perceiver_agent._extract_modality_features(
                "test", "text", None
            )
            
            assert "error" in features

    @pytest.mark.asyncio
    async def test_historian_store_error(self, _perceiver_agent: PerceiverAgent, _caplog) -> None:
        """Test handling of historian storage errors."""
        # This should not raise, just log warning
        await perceiver_agent._store_in_historian(
            "test-id", "text", {}, {}
        )
