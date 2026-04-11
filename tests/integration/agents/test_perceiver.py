"""
Integration tests for PerceiverAgent.

Tier 2 (Support) - PerceiverAgent handles multi-modal input processing and feature extraction.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.actors.perceiver import PerceiverAgent, ModalityType
from heretek_swarm.actors.base import ActorMessage, ActorState


pytestmark = pytest.mark.integration


class TestPerceiverAgentIntegration:
    """Integration tests for PerceiverAgent."""

    @pytest_asyncio.fixture
    async def perceiver_agent(self, mock_nats, mock_llm, mock_db):
        """Create PerceiverAgent with mock dependencies."""
        with patch('heretek_swarm.actors.stubs.get_nats_event_mesh', return_value=mock_nats):
            with patch('heretek_swarm.actors.stubs.get_llm_provider', return_value=mock_llm):
                with patch('heretek_swarm.actors.stubs.get_db_pool', return_value=mock_db):
                    agent = PerceiverAgent(agent_id="perceiver-test-001")
                    yield agent
                    if agent.state != ActorState.TERMINATED:
                        await agent.terminate()

    @pytest_asyncio.fixture
    async def spawned_perceiver(self, perceiver_agent):
        """Create and spawn PerceiverAgent."""
        await perceiver_agent.spawn()
        yield perceiver_agent

    @pytest.mark.asyncio
    async def test_agent_spawn(self, perceiver_agent):
        """Test agent spawning lifecycle."""
        assert perceiver_agent.state == ActorState.SPAWNING
        await perceiver_agent.spawn()
        assert perceiver_agent.state == ActorState.ACTIVE
        assert perceiver_agent.is_alive

    @pytest.mark.asyncio
    async def test_agent_terminate(self, spawned_perceiver):
        """Test agent termination lifecycle."""
        assert spawned_perceiver.state == ActorState.ACTIVE
        await spawned_perceiver.terminate()
        assert spawned_perceiver.state == ActorState.TERMINATED
        assert not spawned_perceiver.is_alive

    @pytest.mark.asyncio
    async def test_handle_process_input(self, spawned_perceiver, mock_nats):
        """Test handling input processing request."""
        # Create message
        message = ActorMessage(
            message_type="process_input",
            content={
                "input_data": "Sample text input for processing",
                "modality": "text",
                "metadata": {"source": "user_input"},
            },
            sender="echo",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify input processed
        assert len(spawned_perceiver._processed_inputs) > 0

    @pytest.mark.asyncio
    async def test_handle_extract_features(self, spawned_perceiver, mock_nats):
        """Test handling feature extraction request."""
        # Create message
        message = ActorMessage(
            message_type="extract_features",
            content={
                "input_id": "input-001",
                "modality": "text",
            },
            sender="historian",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify features extracted
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_classify_modality(self, spawned_perceiver, mock_nats):
        """Test handling modality classification request."""
        # Create message
        message = ActorMessage(
            message_type="classify_modality",
            content={
                "input_data": "This is clearly text content",
            },
            sender="coordinator",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify modality classified
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_assess_quality(self, spawned_perceiver, mock_nats):
        """Test handling quality assessment request."""
        # Create message
        message = ActorMessage(
            message_type="assess_quality",
            content={
                "input_data": "High quality input data",
                "modality": "text",
            },
            sender="examiner",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify quality assessed
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_get_processing_stats(self, spawned_perceiver, mock_nats):
        """Test handling processing stats request."""
        # Create message
        message = ActorMessage(
            message_type="get_processing_stats",
            content={},
            sender="monitor",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify stats published
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_correlate_modalities(self, spawned_perceiver, mock_llm):
        """Test handling modality correlation request."""
        # Setup mock LLM
        mock_llm.register_response(
            "correlate",
            "Correlation analysis: Text and image inputs show consistent themes."
        )

        # Create message
        message = ActorMessage(
            message_type="correlate_modalities",
            content={
                "modalities": ["text", "image"],
                "input_ids": ["input-text-001", "input-image-001"],
            },
            sender="coordinator",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process message
        await spawned_perceiver.process_message(message)

        # Verify correlation performed
        assert len(mock_nats.published_messages) > 0

    @pytest.mark.asyncio
    async def test_detect_modality(self, spawned_perceiver):
        """Test modality detection."""
        # Detect text modality
        modality = spawned_perceiver._detect_modality("This is text content")
        assert modality == ModalityType.TEXT

        # Detect image modality (base64)
        modality = spawned_perceiver._detect_modality("data:image/png;base64,ABC123")
        assert modality == ModalityType.IMAGE

    @pytest.mark.asyncio
    async def test_extract_text_features(self, spawned_perceiver):
        """Test text feature extraction."""
        features = spawned_perceiver._extract_text_features(
            "This is a sample text with multiple words and sentences."
        )

        assert isinstance(features, dict)
        assert "word_count" in features or "length" in features

    @pytest.mark.asyncio
    async def test_validate_input_size(self, spawned_perceiver):
        """Test input size validation."""
        # Valid size
        assert spawned_perceiver._validate_input_size("small input") is True

        # Too large (assuming max is reasonable)
        large_input = "x" * (spawned_perceiver._max_input_size + 1)
        assert spawned_perceiver._validate_input_size(large_input) is False

    @pytest.mark.asyncio
    async def test_assess_input_quality(self, spawned_perceiver):
        """Test input quality assessment."""
        quality = spawned_perceiver._assess_input_quality(
            input_data="Clear, well-formed text",
            modality="text"
        )

        assert isinstance(quality, dict)
        assert "score" in quality or "quality" in quality

    @pytest.mark.asyncio
    async def test_cache_features(self, spawned_perceiver):
        """Test feature caching."""
        # Cache features
        spawned_perceiver._cache_features(
            input_id="test-input",
            features={"feature1": "value1", "feature2": "value2"}
        )

        # Verify cached
        assert "test-input" in spawned_perceiver._feature_cache

    @pytest.mark.asyncio
    async def test_store_in_historian(self, spawned_perceiver, mock_db):
        """Test storing features in Historian."""
        # Store features
        with patch('heretek_swarm.actors.stubs.get_db_pool', return_value=mock_db):
            await spawned_perceiver._store_in_historian(
                input_id="test-input",
                features={"key": "value"},
                modality="text"
            )

        # Verify stored
        table = mock_db.get_table("memories")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_extract_image_features(self, spawned_perceiver, mock_llm):
        """Test image feature extraction."""
        # Setup mock LLM for image description
        mock_llm.register_response(
            "describe",
            "Image shows a professional setting with modern technology."
        )

        # Extract features (mock base64)
        features = await spawned_perceiver._extract_image_features(
            image_data="base64_encoded_image_data"
        )

        assert isinstance(features, dict)

    @pytest.mark.asyncio
    async def test_extract_audio_features(self, spawned_perceiver):
        """Test audio feature extraction."""
        features = await spawned_perceiver._extract_audio_features(
            audio_data="mock_audio_data"
        )

        assert isinstance(features, dict)

    @pytest.mark.asyncio
    async def test_extract_sensor_features(self, spawned_perceiver):
        """Test sensor data feature extraction."""
        features = spawned_perceiver._extract_sensor_features(
            sensor_data={"temperature": 25.5, "humidity": 60}
        )

        assert isinstance(features, dict)

    @pytest.mark.asyncio
    async def test_concurrent_input_processing(self, spawned_perceiver, mock_nats):
        """Test handling multiple concurrent inputs."""
        # Simulate multiple processed inputs
        for i in range(10):
            spawned_perceiver._processed_inputs[f"input-{i}"] = {
                "modality": "text",
                "features": {"length": 100},
                "quality_score": 0.8,
            }

        # Verify all inputs tracked
        stats = spawned_perceiver.get_processing_stats()
        assert stats["total_processed"] >= 10

    @pytest.mark.asyncio
    async def test_message_validation(self, spawned_perceiver):
        """Test message validation."""
        # Create invalid message
        message = ActorMessage(
            message_type="process_input",
            content={},  # Missing required fields
            sender="test",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        # Process should handle validation error gracefully
        await spawned_perceiver.process_message(message)

        # Verify agent still active
        assert spawned_perceiver.state == ActorState.ACTIVE

    @pytest.mark.asyncio
    async def test_latency_baseline(self, spawned_perceiver, assert_latency_baseline):
        """Test message processing latency meets baseline."""
        import time

        message = ActorMessage(
            message_type="get_processing_stats",
            content={},
            sender="test",
            recipient="perceiver-test-001",
            timestamp=datetime.utcnow().isoformat(),
        )

        start = time.time()
        await spawned_perceiver.process_message(message)
        latency_ms = (time.time() - start) * 1000

        assert_latency_baseline(latency_ms, "perceiver_message_process")

    @pytest.mark.asyncio
    async def test_state_persistence(self, spawned_perceiver, mock_db):
        """Test agent state persistence."""
        # Add processed input
        spawned_perceiver._processed_inputs["persist-input"] = {
            "modality": "text",
            "features": {"test": "persist"},
        }

        # Save state
        with patch('heretek_swarm.actors.stubs.get_db_pool', return_value=mock_db):
            await spawned_perceiver.save_state()

        # Verify state saved
        table = mock_db.get_table("agent_states")
        assert len(table) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, perceiver_agent):
        """Test agent error recovery."""
        await perceiver_agent.spawn()
        perceiver_agent.state = ActorState.ERROR
        await perceiver_agent.resume()
        assert perceiver_agent.state == ActorState.ACTIVE
