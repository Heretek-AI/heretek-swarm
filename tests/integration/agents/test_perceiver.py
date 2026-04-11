"""
Integration tests for PerceiverAgent.

Tier 2 (Support) - PerceiverAgent handles multi-modal input processing and feature extraction.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from src.heretek_swarm.actors.base import ActorMessage, ActorState
from src.heretek_swarm.actors.perceiver import ModalityType, PerceiverAgent

_pytestmark = pytest.mark.integration


class TestPerceiverAgentIntegration:
    """Integration tests for PerceiverAgent."""

    @pytest_asyncio.fixture
    async def perceiver_agent(self, _mock_nats, _mock_llm, _mock_db):
        """Create PerceiverAgent with mock dependencies."""
        with patch('src.heretek_swarm.actors.perceiver.get_nats_event_mesh', return_value=mock_nats):
            with patch('src.heretek_swarm.actors.base.get_llm_provider', return_value=mock_llm):
                with patch('src.heretek_swarm.actors.perceiver.get_db_pool', return_value=mock_db):
                    _agent = PerceiverAgent(agent_id="perceiver-test-001")
                    yield agent
                    if agent._state != ActorState.TERMINATED:
                        await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_perceiver(self, _perceiver_agent):
        """Create and spawn PerceiverAgent."""
        await perceiver_agent.spawn()
        yield perceiver_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, _perceiver_agent):
        """Test agent spawning lifecycle."""
        assert perceiver_agent._state == ActorState.SPAWNING
        await perceiver_agent.spawn()
        assert perceiver_agent._state == ActorState.ACTIVE
        assert perceiver_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, _spawned_perceiver):
        """Test agent termination lifecycle."""
        assert spawned_perceiver._state == ActorState.ACTIVE
        await spawned_perceiver.terminate()
        assert spawned_perceiver._state == ActorState.TERMINATED
        assert not spawned_perceiver.is_alive

    @pytest.mark.asyncio
    async def test_handle_process_input(self, _spawned_perceiver, _mock_nats):
        """Test handling input processing request."""
        # Create message
        _message = ActorMessage(
            _message_type = "process_input",
            _content = {
                "input_data": "Sample text input for processing",
                "modality": "text",
                "metadata": {"source": "user_input"},
            },
            _sender = "echo",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify input processed
        assert len(spawned_perceiver._processed_inputs) > 0

    @pytest.mark.asyncio
    async def test_handle_extract_features(self, _spawned_perceiver, _mock_nats):
        """Test handling feature extraction request."""
        # Create message
        _message = ActorMessage(
            _message_type = "extract_features",
            _content = {
                "input_id": "input-001",
                "modality": "text",
            },
            _sender = "historian",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify features extracted
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_classify_modality(self, _spawned_perceiver, _mock_nats):
        """Test handling modality classification request."""
        # Create message
        _message = ActorMessage(
            _message_type = "classify_modality",
            _content = {
                "input_data": "This is clearly text content",
            },
            _sender = "coordinator",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify modality classified
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_assess_quality(self, _spawned_perceiver, _mock_nats):
        """Test handling quality assessment request."""
        # Create message
        _message = ActorMessage(
            _message_type = "assess_quality",
            _content = {
                "input_data": "High quality input data",
                "modality": "text",
            },
            _sender = "examiner",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify quality assessed
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_get_processing_stats(self, _spawned_perceiver, _mock_nats):
        """Test handling processing stats request."""
        # Create message
        _message = ActorMessage(
            _message_type = "get_processing_stats",
            _content = {},
            _sender = "monitor",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify stats published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_correlate_modalities(self, _spawned_perceiver, _mock_llm):
        """Test handling modality correlation request."""
        # Setup mock LLM
        mock_llm.register_response(
            "correlate",
            "Correlation analysis: Text and image inputs show consistent themes."
        )

        # Create message
        _message = ActorMessage(
            _message_type = "correlate_modalities",
            _content = {
                "modalities": ["text", "image"],
                "input_ids": ["input-text-001", "input-image-001"],
            },
            _sender = "coordinator",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify correlation performed
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_detect_modality(self, _spawned_perceiver):
        """Test modality detection."""
        # Detect text modality
        _modality = spawned_perceiver._detect_modality("This is text content")
        assert modality == ModalityType.TEXT

        # Detect image modality (base64)
        _modality = spawned_perceiver._detect_modality("data:image/png;base64,ABC123")
        assert modality == ModalityType.IMAGE

    @pytest.mark.asyncio
    async def test_extract_text_features(self, _spawned_perceiver):
        """Test text feature extraction."""
        _features = spawned_perceiver._extract_text_features(
            "This is a sample text with multiple words and sentences."
        )

        assert isinstance(features, dict)
        assert "word_count" in features or "length" in features

    @pytest.mark.asyncio
    async def test_validate_input_size(self, _spawned_perceiver):
        """Test input size validation."""
        # Valid size
        assert spawned_perceiver._validate_input_size("small input") is True

        # Too large (assuming max is reasonable)
        _large_input = "x" * (spawned_perceiver._max_input_size + 1)
        assert spawned_perceiver._validate_input_size(large_input) is False

    @pytest.mark.asyncio
    async def test_assess_input_quality(self, _spawned_perceiver):
        """Test input quality assessment."""
        _quality = spawned_perceiver._assess_input_quality(
            _input_data = "Clear, well-formed text",
            _modality = "text"
        )

        assert isinstance(quality, dict)
        assert "score" in quality or "quality" in quality

    @pytest.mark.asyncio
    async def test_cache_features(self, _spawned_perceiver):
        """Test feature caching."""
        # Cache features
        spawned_perceiver._cache_features(
            _input_id = "test-input",
            _features = {"feature1": "value1", "feature2": "value2"}
        )

        # Verify cached
        assert "test-input" in spawned_perceiver._feature_cache

    @pytest.mark.asyncio
    async def test_store_in_historian(self, _spawned_perceiver, _mock_db):
        """Test storing features in Historian."""
        # Store features
        with patch('src.heretek_swarm.actors.perceiver.get_db_pool', return_value=mock_db):
            await spawned_perceiver._store_in_historian(
                _input_id = "test-input",
                _features = {"key": "value"},
                _modality = "text"
            )

        # Verify stored
        _table = mock_db.get_table("memories")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_extract_image_features(self, _spawned_perceiver, _mock_llm):
        """Test image feature extraction."""
        # Setup mock LLM for image description
        mock_llm.register_response(
            "describe",
            "Image shows a professional setting with modern technology."
        )

        # Extract features (mock base64)
        _features = await spawned_perceiver._extract_image_features(
            _image_data = "base64_encoded_image_data"
        )

        assert isinstance(features, dict)

    @pytest.mark.asyncio
    async def test_extract_audio_features(self, _spawned_perceiver):
        """Test audio feature extraction."""
        _features = await spawned_perceiver._extract_audio_features(
            _audio_data = "mock_audio_data"
        )

        assert isinstance(features, dict)

    @pytest.mark.asyncio
    async def test_extract_sensor_features(self, _spawned_perceiver):
        """Test sensor data feature extraction."""
        _features = spawned_perceiver._extract_sensor_features(
            _sensor_data = {"temperature": 25.5, "humidity": 60}
        )

        assert isinstance(features, dict)

    @pytest.mark.asyncio
    async def test_concurrent_input_processing(self, _spawned_perceiver, _mock_nats):
        """Test handling multiple concurrent inputs."""
        # Simulate multiple processed inputs
        for i in range(10):
            spawned_perceiver._processed_inputs[f"input-{i}"] = {
                "modality": "text",
                "features": {"length": 100},
                "quality_score": 0.8,
            }

        # Verify all inputs tracked
        _stats = spawned_perceiver.get_processing_stats()
        assert stats["total_processed"] >= 10

    @pytest.mark.asyncio
    async def test_message_validation(self, _spawned_perceiver):
        """Test message validation."""
        # Create invalid message
        _message = ActorMessage(
            _message_type = "process_input",
            _content = {},  # Missing required fields
            _sender = "test",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_perceiver.process_message(message)

        # Verify agent still active
        assert spawned_perceiver._state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, _spawned_perceiver, _assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        _message = ActorMessage(
            _message_type = "get_processing_stats",
            _content = {},
            _sender = "test",
            _recipient = "perceiver-test-001",
            _timestamp = datetime.utcnow().isoformat(),
        )

        _start = time.time()
        await spawned_perceiver.process_message(message)
        _latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "perceiver_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, _spawned_perceiver, _mock_db):
        """Test agent state persistence."""
        # Add processed input
        spawned_perceiver._processed_inputs["persist-input"] = {
            "modality": "text",
            "features": {"test": "persist"},
        }

        # Save state
        with patch('src.heretek_swarm.actors.base.get_db_pool', return_value=mock_db):
            await spawned_perceiver.save_state()

        # Verify state saved
        _table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, _perceiver_agent):
        """Test agent error recovery."""
        await perceiver_agent.spawn()
        perceiver_agent._state = ActorState.ERROR
        await perceiver_agent.resume()
        assert perceiver_agent._state == ActorState.ACTIVE
