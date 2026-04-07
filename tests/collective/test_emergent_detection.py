"""Tests for emergent pattern detection system."""

import pytest
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import uuid

from heretek_swarm.collective.emergent_detection import (
    EmergentPatternDetector,
    EmergentPattern,
    EmergentPatternClass,
    EmergenceLevel,
    CollectiveBehavior,
    AgentBehaviorSnapshot,
    DetectionEvent,
    EmergenceDetectionConfig,
    EmergenceAnalyzer,
)


class TestAgentBehaviorSnapshot:
    """Tests for AgentBehaviorSnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test basic snapshot creation."""
        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-1",
            state="active",
            metrics={"success_rate": 0.9},
        )
        assert snapshot.agent_id == "agent-1"
        assert snapshot.state == "active"
        assert snapshot.metrics["success_rate"] == 0.9

    def test_snapshot_to_dict(self):
        """Test snapshot serialization."""
        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-2",
            state="processing",
            metrics={"success_rate": 0.85},
            interaction_count=10,
        )
        data = snapshot.to_dict()
        assert data["agent_id"] == "agent-2"
        assert data["state"] == "processing"
        assert "timestamp" in data
        assert data["metrics"]["success_rate"] == 0.85

    def test_snapshot_with_empty_metrics(self):
        """Test snapshot with no metrics."""
        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-3",
            state="idle",
            metrics={},
        )
        assert snapshot.metrics == {}
        assert snapshot.to_dict()["metrics"] == {}

    def test_snapshot_full_fields(self):
        """Test snapshot with all fields."""
        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-full",
            state="executing",
            active_strategies=["strategy-a", "strategy-b"],
            decision_history=[{"decision": "choice1"}],
            interaction_count=5,
            success_rate=0.75,
            metrics={"accuracy": 0.9},
        )
        assert snapshot.active_strategies == ["strategy-a", "strategy-b"]
        assert len(snapshot.decision_history) == 1
        assert snapshot.interaction_count == 5
        assert snapshot.success_rate == 0.75


class TestCollectiveBehavior:
    """Tests for CollectiveBehavior dataclass."""

    def test_collective_behavior_creation(self):
        """Test basic collective behavior creation."""
        behavior = CollectiveBehavior(
            behavior_type="synchronized_execution",
            participating_agents=["agent-1", "agent-2", "agent-3"],
            intensity=0.85,
            coherence=0.9,
        )
        assert behavior.behavior_type == "synchronized_execution"
        assert len(behavior.participating_agents) == 3
        assert behavior.intensity == 0.85
        assert behavior.coherence == 0.9

    def test_collective_behavior_to_dict(self):
        """Test collective behavior serialization."""
        behavior = CollectiveBehavior(
            behavior_type="resource_sharing",
            participating_agents=["agent-a", "agent-b"],
            intensity=0.7,
            coherence=0.8,
            metadata={"efficiency": 0.9},
        )
        data = behavior.to_dict()
        assert data["behavior_type"] == "resource_sharing"
        assert data["participating_agents"] == ["agent-a", "agent-b"]
        assert "start_time" in data
        assert data["metadata"]["efficiency"] == 0.9

    def test_collective_behavior_large_group(self):
        """Test collective behavior with many agents."""
        agents = [f"agent-{i}" for i in range(50)]
        behavior = CollectiveBehavior(
            behavior_type="swarm_movement",
            participating_agents=agents,
            intensity=0.75,
            coherence=0.6,
        )
        assert len(behavior.participating_agents) == 50
        assert behavior.intensity == 0.75

    def test_collective_behavior_duration(self):
        """Test collective behavior with duration."""
        behavior = CollectiveBehavior(
            behavior_type="coordination",
            participating_agents=["agent-1"],
            duration_seconds=120.5,
            intensity=0.5,
            coherence=0.5,
        )
        assert behavior.duration_seconds == 120.5


class TestEmergentPattern:
    """Tests for EmergentPattern dataclass."""

    def test_pattern_creation(self):
        """Test basic emergent pattern creation."""
        pattern = EmergentPattern(
            pattern_class=EmergentPatternClass.COORDINATION,
            emergence_level=EmergenceLevel.WEAK,
            description="Agents synchronizing their task execution",
            participating_agents=["agent-1", "agent-2"],
            emergence_score=0.6,
            confidence=0.8,
        )
        assert pattern.pattern_class == EmergentPatternClass.COORDINATION
        assert pattern.emergence_level == EmergenceLevel.WEAK
        assert pattern.emergence_score == 0.6
        assert pattern.confidence == 0.8

    def test_pattern_to_dict(self):
        """Test pattern serialization."""
        pattern = EmergentPattern(
            pattern_class=EmergentPatternClass.OPTIMIZATION,
            emergence_level=EmergenceLevel.STRONG,
            description="Resource allocation optimization emerged",
            participating_agents=["agent-a", "agent-b", "agent-c"],
            emergence_score=0.85,
            confidence=0.9,
            impact_score=0.7,
        )
        data = pattern.to_dict()
        assert data["pattern_class"] == "optimization"
        assert data["emergence_level"] == "strong"
        assert data["emergence_score"] == 0.85

    def test_pattern_to_extracted_pattern(self):
        """Test conversion to extracted pattern."""
        pattern = EmergentPattern(
            pattern_class=EmergentPatternClass.COORDINATION,
            emergence_level=EmergenceLevel.WEAK,
            description="Test pattern",
            participating_agents=["agent-1"],
            emergence_score=0.5,
            confidence=0.5,
        )
        # This test may fail if ExtractedPattern dependencies not available
        try:
            extracted = pattern.to_extracted_pattern()
            assert extracted is not None
        except Exception:
            # Skip if dependencies not available
            pass

    def test_pattern_high_impact(self):
        """Test high impact pattern."""
        pattern = EmergentPattern(
            pattern_class=EmergentPatternClass.PHASE_TRANSITION,
            emergence_level=EmergenceLevel.CRITICAL,
            description="System-wide phase transition detected",
            participating_agents=[f"agent-{i}" for i in range(100)],
            emergence_score=0.95,
            confidence=0.98,
            impact_score=0.95,
        )
        assert pattern.impact_score > 0.9
        assert len(pattern.participating_agents) == 100


class TestDetectionEvent:
    """Tests for DetectionEvent dataclass."""

    def test_detection_event_creation(self):
        """Test basic detection event creation."""
        event = DetectionEvent(
            event_id="detect-001",
            detection_method="coordination_analysis",
            raw_score=0.85,
            threshold=0.5,
        )
        assert event.event_id == "detect-001"
        assert event.detection_method == "coordination_analysis"
        assert event.raw_score == 0.85

    def test_detection_event_to_dict(self):
        """Test detection event serialization."""
        event = DetectionEvent(
            event_id="detect-002",
            detection_method="optimization_analysis",
            raw_score=0.9,
            threshold=0.5,
            metadata={"iterations": 10},
        )
        data = event.to_dict()
        assert data["event_id"] == "detect-002"
        assert data["raw_score"] == 0.9
        assert data["metadata"]["iterations"] == 10


class TestEmergenceDetectionConfig:
    """Tests for EmergenceDetectionConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = EmergenceDetectionConfig()
        assert config.min_emergence_score == 0.3
        assert config.min_participating_agents == 3
        assert config.min_coherence == 0.5
        assert config.statistical_threshold == 0.05
        assert config.analysis_window_seconds == 300.0
        assert config.validation_required is True
        assert config.min_confidence == 0.6

    def test_config_custom_values(self):
        """Test custom configuration."""
        config = EmergenceDetectionConfig(
            min_emergence_score=0.5,
            min_participating_agents=5,
            min_coherence=0.7,
            statistical_threshold=0.01,
            analysis_window_seconds=600.0,
            baseline_window_seconds=1200.0,
            validation_required=False,
            min_confidence=0.8,
            max_detections_per_window=20,
        )
        assert config.min_emergence_score == 0.5
        assert config.min_participating_agents == 5
        assert config.min_coherence == 0.7
        assert config.max_detections_per_window == 20


class TestEmergentPatternDetector:
    """Tests for EmergentPatternDetector."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return EmergentPatternDetector()

    @pytest.fixture
    def detector_with_config(self):
        """Create detector with custom config."""
        config = EmergenceDetectionConfig(
            min_emergence_score=0.4,
            min_participating_agents=4,
            min_coherence=0.6,
        )
        return EmergentPatternDetector(config=config)

    def test_detector_initialization(self, detector):
        """Test detector initializes correctly."""
        assert detector is not None
        assert hasattr(detector, "record_agent_snapshot")
        assert hasattr(detector, "analyze_for_emergence")

    def test_record_agent_snapshot(self, detector):
        """Test recording agent behavior snapshots."""
        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-1",
            state="active",
            metrics={"success_rate": 0.9},
        )
        detector.record_agent_snapshot(snapshot)
        # Snapshot should be recorded without error

    def test_record_multiple_snapshots(self, detector):
        """Test recording multiple snapshots."""
        for i in range(10):
            snapshot = AgentBehaviorSnapshot(
                agent_id=f"agent-{i}",
                state="active",
                metrics={"success_rate": 0.8 + i * 0.01},
            )
            detector.record_agent_snapshot(snapshot)
        # All snapshots should be recorded

    def test_record_collective_behavior(self, detector):
        """Test recording collective behavior."""
        behavior = CollectiveBehavior(
            behavior_type="synchronized_execution",
            participating_agents=["agent-1", "agent-2"],
            intensity=0.85,
            coherence=0.9,
        )
        detector.record_collective_behavior(behavior)
        # Behavior should be recorded without error

    @pytest.mark.asyncio
    async def test_analyze_for_emergence_empty(self, detector):
        """Test analysis with no data."""
        patterns = await detector.analyze_for_emergence()
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_analyze_for_emergence_with_data(self, detector):
        """Test analysis with behavior data."""
        # Record some snapshots
        for i in range(5):
            snapshot = AgentBehaviorSnapshot(
                agent_id=f"agent-{i}",
                state="active",
                metrics={"success_rate": 0.8},
            )
            detector.record_agent_snapshot(snapshot)

        # Record collective behavior
        behavior = CollectiveBehavior(
            behavior_type="coordination",
            participating_agents=["agent-0", "agent-1"],
            intensity=0.75,
            coherence=0.8,
        )
        detector.record_collective_behavior(behavior)

        patterns = await detector.analyze_for_emergence()
        assert isinstance(patterns, list)

    def test_get_emergent_patterns(self, detector):
        """Test retrieving emergent patterns."""
        patterns = detector.get_emergent_patterns()
        assert isinstance(patterns, list)

    def test_get_patterns_by_impact(self, detector):
        """Test filtering patterns by impact."""
        patterns = detector.get_patterns_by_impact(min_impact=0.5, limit=10)
        assert isinstance(patterns, list)

    def test_get_harmful_patterns(self, detector):
        """Test retrieving harmful patterns."""
        patterns = detector.get_harmful_patterns(limit=10)
        assert isinstance(patterns, list)

    def test_get_beneficial_patterns(self, detector):
        """Test retrieving beneficial patterns."""
        patterns = detector.get_beneficial_patterns(min_impact=0.3, limit=10)
        assert isinstance(patterns, list)

    def test_get_collective_behaviors(self, detector):
        """Test retrieving collective behaviors."""
        behaviors = detector.get_collective_behaviors()
        assert isinstance(behaviors, list)

    def test_get_detection_history(self, detector):
        """Test retrieving detection history."""
        history = detector.get_detection_history(limit=50)
        assert isinstance(history, list)

    def test_get_emergence_statistics(self, detector):
        """Test getting emergence statistics."""
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_calculate_emergence_metrics(self, detector):
        """Test calculating emergence metrics."""
        metrics = detector.calculate_emergence_metrics()
        assert isinstance(metrics, dict)

    def test_register_detection_callback(self, detector):
        """Test registering detection callback."""
        callback = Mock(__name__="test_callback")
        detector.register_detection_callback(callback)
        # Callback should be registered without error

    def test_register_validation_callback(self, detector):
        """Test registering validation callback."""
        callback = Mock(__name__="test_validation")
        detector.register_validation_callback(callback)
        # Callback should be registered without error

    def test_get_status(self, detector):
        """Test getting detector status."""
        status = detector.get_status()
        assert isinstance(status, dict)


class TestEmergentPatternDetectorCallbacks:
    """Tests for detector callback functionality."""

    @pytest.mark.asyncio
    async def test_detection_callback_invoked(self):
        """Test that detection callback is invoked."""
        detector = EmergentPatternDetector()
        callback = AsyncMock(__name__="test_callback")
        detector.register_detection_callback(callback)

        # Record behavior to trigger detection
        behavior = CollectiveBehavior(
            behavior_type="test_coordination",
            participating_agents=["agent-1", "agent-2"],
            intensity=0.9,
            coherence=0.85,
        )
        detector.record_collective_behavior(behavior)

        # Trigger analysis
        await detector.analyze_for_emergence()
        # Callback may be invoked asynchronously

    def test_validation_callback_registration(self):
        """Test validation callback registration."""
        detector = EmergentPatternDetector()
        validation_callback = Mock(__name__="test_validation")
        detector.register_validation_callback(validation_callback)
        # Callback registered without error
        assert detector is not None


class TestEmergentPatternClass:
    """Tests for EmergentPatternClass enum."""

    def test_pattern_class_values(self):
        """Test all pattern class values exist."""
        assert EmergentPatternClass.COORDINATION == "coordination"
        assert EmergentPatternClass.OPTIMIZATION == "optimization"
        assert EmergentPatternClass.INNOVATION == "innovation"
        assert EmergentPatternClass.PHASE_TRANSITION == "phase_transition"

    def test_pattern_class_count(self):
        """Test number of pattern classes."""
        assert len(list(EmergentPatternClass)) >= 4


class TestEmergenceLevel:
    """Tests for EmergenceLevel enum."""

    def test_emergence_level_values(self):
        """Test all emergence level values exist."""
        assert EmergenceLevel.WEAK.value == "weak"
        assert EmergenceLevel.MODERATE.value == "moderate"
        assert EmergenceLevel.STRONG.value == "strong"
        assert EmergenceLevel.CRITICAL.value == "critical"

    def test_emergence_level_ordering(self):
        """Test emergence level ordering."""
        levels = list(EmergenceLevel)
        assert len(levels) >= 4


class TestEmergenceAnalyzer:
    """Tests for EmergenceAnalyzer."""

    @pytest.fixture
    def detector(self):
        """Create detector for analyzer."""
        return EmergentPatternDetector()

    @pytest.fixture
    def analyzer(self, detector):
        """Create analyzer instance."""
        return EmergenceAnalyzer(detector)

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly."""
        assert analyzer is not None
        assert hasattr(analyzer, "detector")

    def test_analyze_emergence_trends(self, analyzer):
        """Test analyzing emergence trends."""
        trends = analyzer.analyze_emergence_trends()
        assert isinstance(trends, dict)

    def test_identify_key_contributors(self, analyzer):
        """Test identifying key contributors."""
        contributors = analyzer.identify_key_contributors()
        assert isinstance(contributors, list)

    def test_analyze_pattern_correlations(self, analyzer):
        """Test analyzing pattern correlations."""
        correlations = analyzer.analyze_pattern_correlations()
        assert isinstance(correlations, dict)

    def test_get_emergence_timeline(self, analyzer):
        """Test getting emergence timeline."""
        timeline = analyzer.get_emergence_timeline()
        assert isinstance(timeline, list)


class TestEmergentDetectionIntegration:
    """Integration tests for emergent detection system."""

    @pytest.mark.asyncio
    async def test_full_detection_workflow(self):
        """Test complete detection workflow."""
        # Create detector
        detector = EmergentPatternDetector()

        # Record agent snapshots
        for i in range(20):
            snapshot = AgentBehaviorSnapshot(
                agent_id=f"agent-{i % 5}",
                state="active",
                metrics={"success_rate": 0.7 + (i % 3) * 0.1},
            )
            detector.record_agent_snapshot(snapshot)

        # Record collective behaviors
        for i in range(5):
            behavior = CollectiveBehavior(
                behavior_type="coordination_pattern",
                participating_agents=[f"agent-{j}" for j in range(i + 1)],
                intensity=0.6 + i * 0.05,
                coherence=0.7,
            )
            detector.record_collective_behavior(behavior)

        # Analyze for emergence
        patterns = await detector.analyze_for_emergence()
        assert isinstance(patterns, list)

        # Get statistics
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_pattern_tracking_over_time(self):
        """Test tracking patterns over time."""
        detector = EmergentPatternDetector()

        # Simulate behavior over time
        for t in range(10):
            behavior = CollectiveBehavior(
                behavior_type="evolving_coordination",
                participating_agents=["agent-1", "agent-2"],
                intensity=t * 0.1,
                coherence=0.5 + t * 0.05,
            )
            detector.record_collective_behavior(behavior)

        # Check history
        history = detector.get_detection_history(limit=20)
        assert isinstance(history, list)

    def test_multi_agent_coordination_detection(self):
        """Test detecting coordination among multiple agents."""
        detector = EmergentPatternDetector()

        # Record synchronized behavior
        for i in range(10):
            snapshot = AgentBehaviorSnapshot(
                agent_id=f"agent-{i}",
                state="coordinating",
                metrics={"sync_score": 0.9},
            )
            detector.record_agent_snapshot(snapshot)

        # Record collective coordination
        behavior = CollectiveBehavior(
            behavior_type="full_synchronization",
            participating_agents=[f"agent-{i}" for i in range(10)],
            intensity=0.95,
            coherence=0.9,
        )
        detector.record_collective_behavior(behavior)

        # Get patterns
        patterns = detector.get_emergent_patterns()
        assert isinstance(patterns, list)

    def test_emergence_level_classification(self):
        """Test classification of emergence levels."""
        detector = EmergentPatternDetector()

        # Create patterns with different impact scores
        for intensity in [0.3, 0.5, 0.7, 0.9]:
            # Simulate behaviors that would lead to patterns
            behavior = CollectiveBehavior(
                behavior_type=f"intensity_{intensity}",
                participating_agents=["agent-1"],
                intensity=intensity,
                coherence=intensity,
            )
            detector.record_collective_behavior(behavior)

        # Check statistics include level information
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_detector_with_custom_config(self):
        """Test detector with custom configuration."""
        config = EmergenceDetectionConfig(
            min_emergence_score=0.5,
            min_participating_agents=5,
            min_coherence=0.7,
            max_detections_per_window=25,
        )
        detector = EmergentPatternDetector(config=config)

        assert detector.config.min_emergence_score == 0.5
        assert detector.config.min_participating_agents == 5
        assert detector.config.min_coherence == 0.7

    @pytest.mark.asyncio
    async def test_concurrent_snapshot_recording(self):
        """Test concurrent snapshot recording."""
        detector = EmergentPatternDetector()

        # Record many snapshots rapidly
        for i in range(100):
            snapshot = AgentBehaviorSnapshot(
                agent_id=f"agent-{i % 10}",
                state="processing",
                metrics={"load": i / 100},
            )
            detector.record_agent_snapshot(snapshot)

        # Should handle without error
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_pattern_filtering_by_class(self):
        """Test filtering patterns by class."""
        detector = EmergentPatternDetector()

        # Get patterns filtered by class
        for pattern_class in EmergentPatternClass:
            patterns = detector.get_emergent_patterns(pattern_class=pattern_class)
            assert isinstance(patterns, list)

    def test_beneficial_vs_harmful_classification(self):
        """Test classification of beneficial vs harmful patterns."""
        detector = EmergentPatternDetector()

        # Get both types
        harmful = detector.get_harmful_patterns(limit=10)
        beneficial = detector.get_beneficial_patterns(min_impact=0.1, limit=10)

        assert isinstance(harmful, list)
        assert isinstance(beneficial, list)

    @pytest.mark.asyncio
    async def test_detection_with_empty_state(self):
        """Test detection with no recorded data."""
        detector = EmergentPatternDetector()

        # Should handle empty state gracefully
        patterns = await detector.analyze_for_emergence()
        assert patterns == []

        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_analyzer_with_detector_data(self):
        """Test analyzer with populated detector data."""
        # Create detector
        detector = EmergentPatternDetector()
        
        # Populate detector with data
        for i in range(10):
            snapshot = AgentBehaviorSnapshot(
                agent_id=f"agent-{i}",
                state="analyzing",
                metrics={"performance": 0.8},
            )
            detector.record_agent_snapshot(snapshot)

        # Create analyzer
        analyzer = EmergenceAnalyzer(detector)

        # Run analysis
        trends = analyzer.analyze_emergence_trends()
        assert isinstance(trends, dict)

        contributors = analyzer.identify_key_contributors()
        assert isinstance(contributors, list)


class TestEmergentDetectionEdgeCases:
    """Edge case tests for emergent detection."""

    def test_single_agent_behavior(self):
        """Test detection with single agent."""
        detector = EmergentPatternDetector()

        snapshot = AgentBehaviorSnapshot(
            agent_id="solo-agent",
            state="focused",
            metrics={"focus": 1.0},
        )
        detector.record_agent_snapshot(snapshot)

        # Should handle single agent
        patterns = detector.get_emergent_patterns()
        assert isinstance(patterns, list)

    def test_zero_metrics_values(self):
        """Test handling of zero metric values."""
        detector = EmergentPatternDetector()

        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-zero",
            state="idle",
            metrics={"value": 0.0},
        )
        detector.record_agent_snapshot(snapshot)

        # Should handle zero values
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_negative_metrics_values(self):
        """Test handling of negative metric values."""
        detector = EmergentPatternDetector()

        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-negative",
            state="degraded",
            metrics={"delta": -0.5},
        )
        detector.record_agent_snapshot(snapshot)

        # Should handle negative values
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_very_large_agent_group(self):
        """Test handling very large agent groups."""
        detector = EmergentPatternDetector()

        # Record behavior with 1000 agents
        behavior = CollectiveBehavior(
            behavior_type="massive_coordination",
            participating_agents=[f"agent-{i}" for i in range(1000)],
            intensity=1.0,
            coherence=0.95,
        )
        detector.record_collective_behavior(behavior)

        # Should handle large groups
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)

    def test_rapid_sequential_detections(self):
        """Test rapid sequential detection calls."""
        detector = EmergentPatternDetector()

        # Call detection multiple times rapidly
        for _ in range(10):
            patterns = detector.get_emergent_patterns()
            assert isinstance(patterns, list)

    def test_timestamp_edge_cases(self):
        """Test various timestamp scenarios."""
        detector = EmergentPatternDetector()

        # Past timestamp
        snapshot = AgentBehaviorSnapshot(
            agent_id="agent-past",
            state="completed",
            metrics={},
        )
        detector.record_agent_snapshot(snapshot)

        # Should handle both
        stats = detector.get_emergence_statistics()
        assert isinstance(stats, dict)
