"""
Tests for Message Replay & Time Travel Debugging.

Tests cover:
- Replay job creation and management
- Message replay execution
- Progress tracking
- Time travel state reconstruction
- Pause, resume, and cancel operations
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from heretek_swarm.gateway.message_replay import (
    MessageReplayManager,
    ReplayJob,
    ReplayStatus,
    TimeTravelRequest,
    get_replay_manager,
    setup_replay_manager,
)


class TestReplayJob:
    """Test ReplayJob model."""
    
    def test_create_replay_job(self):
        """Test creating a replay job."""
        job = ReplayJob.create(
            stream_name="AGENT_EVENTS",
            start_sequence=1000,
            end_sequence=2000,
            subject_filter="agent.*.status",
            destination_stream="REPLAY_EVENTS",
            replay_speed=10.0,
            metadata={"user_id": "user-123"},
        )
        
        assert job.stream_name == "AGENT_EVENTS"
        assert job.start_sequence == 1000
        assert job.end_sequence == 2000
        assert job.subject_filter == "agent.*.status"
        assert job.destination_stream == "REPLAY_EVENTS"
        assert job.replay_speed == 10.0
        assert job.status == ReplayStatus.PENDING
        assert job.progress == 0
        assert job.total == 0
        assert job.job_id is not None
    
    def test_job_to_dict(self):
        """Test job serialization."""
        job = ReplayJob.create(
            stream_name="TEST_STREAM",
            start_sequence=1,
            end_sequence=100,
        )
        
        data = job.to_dict()
        
        assert data["stream_name"] == "TEST_STREAM"
        assert data["start_sequence"] == 1
        assert data["end_sequence"] == 100
        assert data["status"] == "pending"
        assert "job_id" in data
    
    def test_progress_percent(self):
        """Test progress percentage calculation."""
        job = ReplayJob.create(stream_name="TEST")
        job.progress = 25
        job.total = 100
        
        assert job.progress_percent == 25.0
        
        job.progress = 50
        assert job.progress_percent == 50.0
        
        job.progress = 100
        assert job.progress_percent == 100.0
    
    def test_progress_percent_zero_total(self):
        """Test progress percentage with zero total."""
        job = ReplayJob.create(stream_name="TEST")
        job.progress = 0
        job.total = 0
        
        assert job.progress_percent == 0.0


class TestTimeTravelRequest:
    """Test TimeTravelRequest model."""
    
    def test_create_time_travel_request(self):
        """Test creating a time travel request."""
        target_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        request = TimeTravelRequest.create(
            entity_id="agent-1",
            entity_type="Agent",
            target_time=target_time,
            source_stream="AGENT_EVENTS",
            include_snapshots=True,
            destination="DEBUG_STREAM",
        )
        
        assert request.entity_id == "agent-1"
        assert request.entity_type == "Agent"
        assert request.target_time == target_time
        assert request.source_stream == "AGENT_EVENTS"
        assert request.include_snapshots is True
        assert request.destination == "DEBUG_STREAM"
        assert request.request_id is not None
    
    def test_request_to_dict(self):
        """Test request serialization."""
        target_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        request = TimeTravelRequest.create(
            entity_id="agent-1",
            entity_type="Agent",
            target_time=target_time,
            source_stream="AGENT_EVENTS",
        )
        
        data = request.to_dict()
        
        assert data["entity_id"] == "agent-1"
        assert data["entity_type"] == "Agent"
        assert data["target_time"] == "2024-01-01T12:00:00+00:00"
        assert data["source_stream"] == "AGENT_EVENTS"
        assert "request_id" in data


class TestMessageReplayManager:
    """Test MessageReplayManager functionality."""
    
    @pytest.fixture
    def replay_manager(self):
        """Create a replay manager instance."""
        return MessageReplayManager(
            jetstream_manager=None,
            event_store=None,
            zero_trust_enabled=False,
        )
    
    @pytest.mark.asyncio
    async def test_create_replay_job(self, replay_manager):
        """Test creating a replay job."""
        job = await replay_manager.create_replay_job(
            stream_name="AGENT_EVENTS",
            start_sequence=100,
            end_sequence=200,
            subject_filter="agent.*.status",
        )
        
        assert job is not None
        assert job.stream_name == "AGENT_EVENTS"
        assert job.start_sequence == 100
        assert job.end_sequence == 200
        assert job.subject_filter == "agent.*.status"
        assert job.status == ReplayStatus.PENDING
        
        # Job should be tracked
        assert job.job_id in replay_manager._jobs
    
    @pytest.mark.asyncio
    async def test_create_replay_job_with_time_range(self, replay_manager):
        """Test creating a replay job with time range."""
        start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        
        job = await replay_manager.create_replay_job(
            stream_name="AGENT_EVENTS",
            start_time=start_time,
            end_time=end_time,
            subject_filter="agent.*",
        )
        
        assert job.metadata["start_time"] == "2024-01-01T00:00:00+00:00"
        assert job.metadata["end_time"] == "2024-01-02T00:00:00+00:00"
    
    @pytest.mark.asyncio
    async def test_get_job(self, replay_manager):
        """Test getting a job by ID."""
        job = await replay_manager.create_replay_job(
            stream_name="TEST_STREAM",
        )
        
        retrieved = replay_manager.get_job(job.job_id)
        
        assert retrieved is not None
        assert retrieved.job_id == job.job_id
        assert retrieved.stream_name == "TEST_STREAM"
    
    def test_get_nonexistent_job(self, replay_manager):
        """Test getting a job that doesn't exist."""
        job = replay_manager.get_job("nonexistent-id")
        
        assert job is None
    
    @pytest.mark.asyncio
    async def test_get_all_jobs(self, replay_manager):
        """Test getting all jobs."""
        # Create multiple jobs
        for i in range(5):
            await replay_manager.create_replay_job(
                stream_name=f"STREAM_{i}",
            )
        
        jobs = replay_manager.get_all_jobs()
        
        assert len(jobs) == 5
    
    @pytest.mark.asyncio
    async def test_active_jobs(self, replay_manager):
        """Test getting active jobs."""
        # Create jobs with different statuses
        job1 = await replay_manager.create_replay_job(stream_name="S1")
        job2 = await replay_manager.create_replay_job(stream_name="S2")
        job3 = await replay_manager.create_replay_job(stream_name="S3")
        
        # Set different statuses
        job1.status = ReplayStatus.RUNNING
        job2.status = ReplayStatus.COMPLETED
        job3.status = ReplayStatus.PAUSED
        
        active = replay_manager.active_jobs
        
        assert len(active) == 2  # RUNNING and PAUSED
        active_ids = [j.job_id for j in active]
        assert job1.job_id in active_ids
        assert job3.job_id in active_ids
        assert job2.job_id not in active_ids
    
    @pytest.mark.asyncio
    async def test_pause_replay(self, replay_manager):
        """Test pausing a replay job."""
        job = await replay_manager.create_replay_job(
            stream_name="TEST_STREAM",
        )
        job.status = ReplayStatus.RUNNING
        
        result = await replay_manager.pause_replay(job.job_id)
        
        assert result is True
        assert job.status == ReplayStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_pause_nonexistent_job(self, replay_manager):
        """Test pausing a job that doesn't exist."""
        result = await replay_manager.pause_replay("nonexistent-id")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_resume_replay(self, replay_manager):
        """Test resuming a paused replay job."""
        job = await replay_manager.create_replay_job(
            stream_name="TEST_STREAM",
        )
        job.status = ReplayStatus.PAUSED
        
        result = await replay_manager.resume_replay(job.job_id)
        
        assert result is True
        assert job.status == ReplayStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_resume_non_paused_job(self, replay_manager):
        """Test resuming a job that isn't paused."""
        job = await replay_manager.create_replay_job(
            stream_name="TEST_STREAM",
        )
        job.status = ReplayStatus.COMPLETED
        
        result = await replay_manager.resume_replay(job.job_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cancel_replay(self, replay_manager):
        """Test cancelling a replay job."""
        job = await replay_manager.create_replay_job(
            stream_name="TEST_STREAM",
        )
        job.status = ReplayStatus.RUNNING
        
        result = await replay_manager.cancel_replay(job.job_id)
        
        assert result is True
        assert job.status == ReplayStatus.CANCELLED
        assert job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_completed_job(self, replay_manager):
        """Test cancelling a job that's already completed."""
        job = await replay_manager.create_replay_job(
            stream_name="TEST_STREAM",
        )
        job.status = ReplayStatus.COMPLETED
        
        result = await replay_manager.cancel_replay(job.job_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_stats(self, replay_manager):
        """Test getting replay manager statistics."""
        # Create some jobs
        for i in range(3):
            await replay_manager.create_replay_job(
                stream_name=f"STREAM_{i}",
            )
        
        stats = await replay_manager.get_stats()
        
        assert "jobs_created" in stats
        assert "jobs_completed" in stats
        assert "jobs_failed" in stats
        assert "messages_replayed" in stats
        assert "active_jobs" in stats
        assert "total_jobs" in stats
        assert stats["total_jobs"] == 3
    
    @pytest.mark.asyncio
    async def test_create_time_travel_request(self, replay_manager):
        """Test creating a time travel request."""
        target_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        request = await replay_manager.create_time_travel_request(
            entity_id="agent-1",
            entity_type="Agent",
            target_time=target_time,
            source_stream="AGENT_EVENTS",
            include_snapshots=True,
        )
        
        assert request is not None
        assert request.entity_id == "agent-1"
        assert request.entity_type == "Agent"
        assert request.target_time == target_time
        
        # Request should be tracked
        assert request.request_id in replay_manager._time_travel_requests
    
    @pytest.mark.asyncio
    async def test_execute_time_travel_without_event_store(self, replay_manager):
        """Test time travel execution without event store."""
        target_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        request = await replay_manager.create_time_travel_request(
            entity_id="agent-1",
            entity_type="Agent",
            target_time=target_time,
            source_stream="AGENT_EVENTS",
        )
        
        def applier(state, event):
            return state
        
        # Should return empty dict without event store
        state = await replay_manager.execute_time_travel(request, applier)
        
        assert state == {}


class TestReplayExecution:
    """Test replay execution with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_execute_replay_job(self):
        """Test executing a replay job with mocked JetStream."""
        # Create mock JetStream manager
        mock_js = AsyncMock()
        mock_js.replay_messages = AsyncMock(return_value=[
            {"subject": "agent.1.status", "data": {"state": "running"}},
            {"subject": "agent.2.status", "data": {"state": "stopped"}},
            {"subject": "agent.3.status", "data": {"state": "running"}},
        ])
        mock_js.publish = AsyncMock(return_value=True)
        
        manager = MessageReplayManager(
            jetstream_manager=mock_js,
            event_store=None,
            zero_trust_enabled=False,
        )
        
        job = await manager.create_replay_job(
            stream_name="AGENT_EVENTS",
            start_sequence=1,
            end_sequence=100,
            destination_stream="REPLAY_DEST",
            replay_speed=100.0,  # Fast replay for testing
        )
        
        received_messages = []
        
        async def callback(subject, data):
            received_messages.append((subject, data))
        
        # Execute replay
        result = await manager.execute_replay(job, callback)
        
        assert result is True
        assert job.status == ReplayStatus.COMPLETED
        assert job.progress == 3
        assert job.total == 3
        assert len(received_messages) == 3
        
        # Verify JetStream was called correctly
        mock_js.replay_messages.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_replay_with_cancel(self):
        """Test cancelling a replay during execution."""
        # Create mock JetStream manager with slow replay
        mock_js = AsyncMock()
        
        async def slow_replay(*args, **kwargs):
            messages = []
            for i in range(100):
                messages.append({
                    "subject": f"agent.{i}.status",
                    "data": {"state": "running"},
                })
            return messages
        
        mock_js.replay_messages = AsyncMock(side_effect=slow_replay)
        
        manager = MessageReplayManager(
            jetstream_manager=mock_js,
            event_store=None,
            zero_trust_enabled=False,
        )
        
        job = await manager.create_replay_job(
            stream_name="AGENT_EVENTS",
            replay_speed=1000.0,  # Very fast
        )
        
        # Start replay in background
        async def run_replay():
            await manager.execute_replay(job)
        
        task = asyncio.create_task(run_replay())
        
        # Wait a bit then cancel
        await asyncio.sleep(0.05)
        await manager.cancel_replay(job.job_id)
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        
        # Job should be cancelled or completed
        assert job.status in (ReplayStatus.CANCELLED, ReplayStatus.COMPLETED)
        
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_execute_replay_job_not_found(self):
        """Test executing a job that doesn't exist."""
        manager = MessageReplayManager(
            jetstream_manager=None,
            event_store=None,
            zero_trust_enabled=False,
        )
        
        # Create a job with a fake ID that isn't in the manager
        job = ReplayJob(
            job_id="nonexistent-job-id",
            stream_name="TEST",
            start_sequence=None,
            end_sequence=None,
            subject_filter=None,
            destination_stream=None,
            replay_speed=1.0,
        )
        
        result = await manager.execute_replay(job)
        
        assert result is False


class TestReplayWithMockedEventStore:
    """Test time travel with mocked event store."""
    
    @pytest.mark.asyncio
    async def test_execute_time_travel_with_event_store(self):
        """Test time travel execution with mocked event store."""
        # Create mock event store
        mock_event_store = AsyncMock()
        
        # Mock snapshot
        mock_snapshot = MagicMock()
        mock_snapshot.state = {"initial": "value", "state": "stopped"}
        mock_snapshot.version = 5
        mock_snapshot.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        
        # Mock events after snapshot
        mock_events = [
            MagicMock(
                event_type="agent.state.changed",
                payload={"new_state": "starting"},
                timestamp=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
            ),
            MagicMock(
                event_type="agent.state.changed",
                payload={"new_state": "running"},
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            MagicMock(
                event_type="agent.state.changed",
                payload={"new_state": "processing"},
                timestamp=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            ),
        ]
        
        mock_event_store.get_snapshot = AsyncMock(return_value=mock_snapshot)
        mock_event_store.get_events = AsyncMock(return_value=mock_events)
        mock_event_store.get_last_version = AsyncMock(return_value=10)
        
        manager = MessageReplayManager(
            jetstream_manager=None,
            event_store=mock_event_store,
            zero_trust_enabled=False,
        )
        
        target_time = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        
        request = await manager.create_time_travel_request(
            entity_id="agent-1",
            entity_type="Agent",
            target_time=target_time,
            source_stream="AGENT_EVENTS",
            include_snapshots=True,
        )
        
        def applier(state, event):
            if "new_state" in event.payload:
                state["state"] = event.payload["new_state"]
            return state
        
        state = await manager.execute_time_travel(request, applier)
        
        # Should have snapshot state plus events up to target time
        assert state["initial"] == "value"
        assert state["state"] == "running"  # Last event before target_time
        
        # Verify event store was called
        mock_event_store.get_snapshot.assert_called_once()
        mock_event_store.get_events.assert_called_once()


class TestSingletonFunctions:
    """Test module singleton functions."""
    
    def test_get_replay_manager(self):
        """Test getting the replay manager singleton."""
        manager1 = get_replay_manager()
        manager2 = get_replay_manager()
        
        # Should return same instance
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_setup_replay_manager(self):
        """Test setup_replay_manager function."""
        with patch('heretek_swarm.gateway.message_replay._replay_manager', None):
            mock_js = AsyncMock()
            mock_es = AsyncMock()
            
            manager = await setup_replay_manager(
                jetstream_manager=mock_js,
                event_store=mock_es,
            )
            
            assert manager is not None
            assert manager._js_manager is mock_js
            assert manager._event_store is mock_es
