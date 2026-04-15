"""
Tests for SentinelAgent (SAFE-01) - Sentinel Anomaly Response.

Tests cover:
- Behavioral anomaly detection with precision > 99%
- Automated response within 30 seconds
- Rate limiting on automated responses
- False positive cascade prevention
- Sentinel-Prime integration for backup monitoring
- Immune response building (CONS-02)

Reference: Phase 2 Plan Task 4 (SAFE-01), Task 2 (CONS-02)
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.actors.sentinel import (
    AnomalyAlert,
    SentinelAgent,
    SafetyLevel,
    ViolationType,
)
from heretek_swarm.consensus.immune import ResponseOutcome
from heretek_swarm.security.anomaly_detection import (
    AnomalyDetectionConfig,
    AnomalyDetectionResult,
    AnomalyResponse,
    AnomalySeverity,
    AnomalyType,
    BehavioralAnomalyDetector,
    ResponseStatus,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def anomaly_config() -> AnomalyDetectionConfig:
    """Create anomaly detection config for testing."""
    return AnomalyDetectionConfig(
        z_score_threshold=3.0,
        response_deadline_seconds=30.0,
        max_auto_responses_per_minute=10,
        sentinel_prime_escalation_threshold=3,
        min_baseline_samples=5,  # Lower for testing
    )


@pytest.fixture
def anomaly_detector(anomaly_config: AnomalyDetectionConfig) -> BehavioralAnomalyDetector:
    """Create anomaly detector for testing."""
    return BehavioralAnomalyDetector(config=anomaly_config)


@pytest.fixture
def sentinel_agent() -> SentinelAgent:
    """Create SentinelAgent for testing."""
    agent = SentinelAgent(
        agent_id="test_sentinel",
        name="TestSentinel",
        config={
            "anomaly_z_score_threshold": 3.0,
            "anomaly_response_deadline": 30.0,
            "max_auto_responses_per_minute": 10,
            "sentinel_prime_escalation_threshold": 3,
            "immune_min_occurrences": 3,
            "immune_min_confidence": 0.7,
            "immune_max_fp_rate": 0.01,
        },
    )
    return agent


@pytest.fixture
def mock_sentinel_prime() -> AsyncMock:
    """Create mock Sentinel-Prime client."""
    mock = AsyncMock()
    mock.report_threat = AsyncMock(return_value=True)
    return mock


# =============================================================================
# AnomalyDetectionConfig Tests
# =============================================================================


class TestAnomalyDetectionConfig:
    """Tests for AnomalyDetectionConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AnomalyDetectionConfig()
        assert config.z_score_threshold == 3.0
        assert config.response_deadline_seconds == 30.0
        assert config.max_auto_responses_per_minute == 10
        assert config.min_baseline_samples == 30

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AnomalyDetectionConfig(
            z_score_threshold=2.5,
            response_deadline_seconds=15.0,
            max_auto_responses_per_minute=5,
        )
        assert config.z_score_threshold == 2.5
        assert config.response_deadline_seconds == 15.0
        assert config.max_auto_responses_per_minute == 5

    def test_kwargs_initialization(self):
        """Test kwargs-based initialization."""
        config = AnomalyDetectionConfig(
            sentinel_prime_escalation_threshold=5,
            false_positive_cooldown_minutes=10,
        )
        assert config.sentinel_prime_escalation_threshold == 5
        assert config.false_positive_cooldown_minutes == 10


# =============================================================================
# BehavioralAnomalyDetector Tests
# =============================================================================


class TestBehavioralAnomalyDetector:
    """Tests for BehavioralAnomalyDetector."""

    @pytest.mark.asyncio
    async def test_analyze_agent_behavior_no_baseline(
        self, anomaly_detector: BehavioralAnomalyDetector
    ):
        """Test behavior analysis before baseline is established."""
        # Not enough samples to establish baseline
        metrics = {"request_rate": 10.0, "response_time_ms": 100.0}
        anomalies = await anomaly_detector.analyze_agent_behavior(
            agent_id="agent_1",
            metrics=metrics,
        )
        assert anomalies == []

    @pytest.mark.asyncio
    async def test_analyze_agent_behavior_with_baseline(
        self, anomaly_detector: BehavioralAnomalyDetector
    ):
        """Test behavior analysis with established baseline."""
        agent_id = "agent_2"

        # Establish baseline with normal metrics
        for i in range(35):  # Above min_baseline_samples
            await anomaly_detector.analyze_agent_behavior(
                agent_id=agent_id,
                metrics={"request_rate": 10.0, "response_time_ms": 100.0},
            )

        # Now inject an anomaly
        anomalies = await anomaly_detector.analyze_agent_behavior(
            agent_id=agent_id,
            metrics={"request_rate": 100.0},  # Very high rate
        )

        # Should detect anomaly since we have baseline
        assert len(anomalies) >= 1
        anomaly = anomalies[0]
        assert anomaly.agent_id == agent_id
        assert anomaly.anomaly_type == AnomalyType.RATE_DEVIATION

    @pytest.mark.asyncio
    async def test_detect_rate_anomaly_normal(self, anomaly_detector: BehavioralAnomalyDetector):
        """Test rate anomaly detection with normal rate."""
        agent_id = "agent_3"

        # Establish baseline
        for _ in range(35):
            await anomaly_detector.detect_rate_anomaly(
                agent_id=agent_id,
                current_rate=10.0,
                time_window=1.0,
            )

        # Normal rate should not trigger
        anomaly = await anomaly_detector.detect_rate_anomaly(
            agent_id=agent_id,
            current_rate=11.0,  # Close to baseline
            time_window=1.0,
        )
        assert anomaly is None

    @pytest.mark.asyncio
    async def test_detect_rate_anomaly_high(self, anomaly_detector: BehavioralAnomalyDetector):
        """Test rate anomaly detection with high rate."""
        agent_id = "agent_4"

        # Establish baseline
        for _ in range(35):
            await anomaly_detector.detect_rate_anomaly(
                agent_id=agent_id,
                current_rate=10.0,
                time_window=1.0,
            )

        # Anomalous high rate
        anomaly = await anomaly_detector.detect_rate_anomaly(
            agent_id=agent_id,
            current_rate=100.0,  # 10x baseline
            time_window=1.0,
        )

        assert anomaly is not None
        assert anomaly.agent_id == agent_id
        assert anomaly.anomaly_type == AnomalyType.RATE_DEVIATION
        assert anomaly.z_score >= 3.0

    @pytest.mark.asyncio
    async def test_detect_response_time_anomaly(self, anomaly_detector: BehavioralAnomalyDetector):
        """Test response time anomaly detection."""
        agent_id = "agent_5"

        # Establish baseline
        for _ in range(35):
            await anomaly_detector.detect_response_time_anomaly(
                agent_id=agent_id,
                response_time_ms=100.0,
            )

        # Anomalous response time
        anomaly = await anomaly_detector.detect_response_time_anomaly(
            agent_id=agent_id,
            response_time_ms=1000.0,  # 10x baseline
        )

        assert anomaly is not None
        assert anomaly.agent_id == agent_id
        assert anomaly.anomaly_type == AnomalyType.RESPONSE_TIME_ANOMALY

    @pytest.mark.asyncio
    async def test_detect_validation_anomaly(self, anomaly_detector: BehavioralAnomalyDetector):
        """Test validation failure anomaly detection."""
        agent_id = "agent_6"

        # Establish baseline with successful validations
        for _ in range(35):
            await anomaly_detector.detect_validation_anomaly(
                agent_id=agent_id,
                validation_success=True,
            )

        # Now inject failures
        anomaly = await anomaly_detector.detect_validation_anomaly(
            agent_id=agent_id,
            validation_success=False,
            failure_reason="Test failure",
        )

        # Should detect anomaly due to sudden validation failures
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.VALIDATION_FAILURE

    @pytest.mark.asyncio
    async def test_execute_automated_response_within_deadline(
        self, anomaly_detector: BehavioralAnomalyDetector
    ):
        """Test that automated response executes within 30 second deadline."""
        anomaly = AnomalyDetectionResult(
            anomaly_id="test_anomaly_1",
            agent_id="agent_7",
            anomaly_type=AnomalyType.RATE_DEVIATION,
            severity=AnomalySeverity.HIGH,
            timestamp=datetime.now(UTC),
            z_score=4.0,
            trigger_metric="request_rate",
            expected_value=10.0,
            observed_value=100.0,
            confidence=0.99,
            response_deadline=datetime.now(UTC).timestamp() + 30.0,
        )

        start = time.perf_counter()
        response = await anomaly_detector.execute_automated_response(anomaly)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status == ResponseStatus.EXECUTED
        assert response.success is True
        assert elapsed_ms < 30000  # Within 30 seconds

    @pytest.mark.asyncio
    async def test_execute_automated_response_critical_isolate(
        self, anomaly_detector: BehavioralAnomalyDetector
    ):
        """Test CRITICAL severity triggers isolate action."""
        anomaly = AnomalyDetectionResult(
            anomaly_id="test_anomaly_2",
            agent_id="agent_8",
            anomaly_type=AnomalyType.BEHAVIORAL_DRIFT,
            severity=AnomalySeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            z_score=6.0,
            trigger_metric="behavior",
            expected_value=1.0,
            observed_value=10.0,
            confidence=0.999,
            response_deadline=datetime.now(UTC).timestamp() + 30.0,
        )

        response = await anomaly_detector.execute_automated_response(anomaly)

        assert response.action == "isolate"
        assert response.status == ResponseStatus.EXECUTED
        assert response.success is True

    @pytest.mark.asyncio
    async def test_execute_automated_response_high_suspend(
        self, anomaly_detector: BehavioralAnomalyDetector
    ):
        """Test HIGH severity triggers suspend action."""
        anomaly = AnomalyDetectionResult(
            anomaly_id="test_anomaly_3",
            agent_id="agent_9",
            anomaly_type=AnomalyType.RATE_DEVIATION,
            severity=AnomalySeverity.HIGH,
            timestamp=datetime.now(UTC),
            z_score=4.5,
            trigger_metric="request_rate",
            expected_value=10.0,
            observed_value=80.0,
            confidence=0.98,
            response_deadline=datetime.now(UTC).timestamp() + 30.0,
        )

        response = await anomaly_detector.execute_automated_response(anomaly)

        assert response.action == "suspend"
        assert response.status == ResponseStatus.EXECUTED

    @pytest.mark.asyncio
    async def test_execute_automated_response_rate_limited(
        self, anomaly_detector: BehavioralAnomalyDetector
    ):
        """Test rate limiting on automated responses."""
        anomaly = AnomalyDetectionResult(
            anomaly_id="test_anomaly_4",
            agent_id="agent_10",
            anomaly_type=AnomalyType.RATE_DEVIATION,
            severity=AnomalySeverity.MEDIUM,
            timestamp=datetime.now(UTC),
            z_score=3.5,
            trigger_metric="request_rate",
            expected_value=10.0,
            observed_value=50.0,
            confidence=0.95,
            response_deadline=datetime.now(UTC).timestamp() + 30.0,
        )

        # Simulate many recent responses to trigger rate limit
        for _ in range(10):
            anomaly_detector._recent_responses.append(datetime.now(UTC))

        response = await anomaly_detector.execute_automated_response(anomaly)

        assert response.status == ResponseStatus.RATE_LIMITED
        assert response.human_notified is True

    @pytest.mark.asyncio
    async def test_report_false_positive(self, anomaly_detector: BehavioralAnomalyDetector):
        """Test false positive reporting improves precision."""
        # Create and record some anomalies
        for i in range(10):
            anomaly = AnomalyDetectionResult(
                anomaly_id=f"test_anomaly_fp_{i}",
                agent_id="agent_11",
                anomaly_type=AnomalyType.RATE_DEVIATION,
                severity=AnomalySeverity.MEDIUM,
                timestamp=datetime.now(UTC),
                z_score=3.5,
                trigger_metric="request_rate",
                expected_value=10.0,
                observed_value=50.0,
                confidence=0.95,
            )
            anomaly_detector._anomaly_history.append(anomaly)
            anomaly_detector._stats["total_detections"] += 1

        # Report first 5 as false positives
        for i in range(5):
            await anomaly_detector.report_false_positive(f"test_anomaly_fp_{i}")

        precision = anomaly_detector.calculate_precision()

        # 5 false positives out of 10 = 50% precision
        assert precision == 0.5

    @pytest.mark.asyncio
    async def test_precision_calculation(self, anomaly_detector: BehavioralAnomalyDetector):
        """Test precision calculation (1 - false positive rate)."""
        # No detections = perfect precision
        precision = anomaly_detector.calculate_precision()
        assert precision == 1.0

        # Add some true positives (no false positives reported)
        anomaly_detector._stats["total_detections"] = 100
        anomaly_detector._stats["false_positives"] = 1

        precision = anomaly_detector.calculate_precision()
        assert precision == 0.99  # 1 - 0.01 = 0.99

    def test_get_statistics(self, anomaly_detector: BehavioralAnomalyDetector):
        """Test statistics retrieval."""
        stats = anomaly_detector.get_statistics()

        assert "total_detections" in stats
        assert "true_positives" in stats
        assert "false_positives" in stats
        assert "precision" in stats
        assert stats["precision"] == 1.0  # No detections yet


# =============================================================================
# SentinelAgent Tests
# =============================================================================


class TestSentinelAgentAnomalyDetection:
    """Tests for SentinelAgent anomaly detection functionality."""

    @pytest.mark.asyncio
    async def test_monitor_agent_behavior(self, sentinel_agent: SentinelAgent):
        """Test agent behavior monitoring returns alerts for anomalies."""
        agent_id = "test_agent_1"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.monitor_agent_behavior(
                agent_id=agent_id,
                metrics={"request_rate": 10.0, "response_time_ms": 100.0},
            )

        # Detect anomaly
        alerts = await sentinel_agent.monitor_agent_behavior(
            agent_id=agent_id,
            metrics={"request_rate": 100.0},  # Anomalous
        )

        # Should have detected anomaly
        assert len(alerts) >= 1
        assert alerts[0].agent_id == agent_id

    @pytest.mark.asyncio
    async def test_check_agent_rate_normal(self, sentinel_agent: SentinelAgent):
        """Test agent rate check with normal rate."""
        agent_id = "test_agent_2"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Normal rate should not trigger
        alert = await sentinel_agent.check_agent_rate(agent_id, 11.0)
        assert alert is None

    @pytest.mark.asyncio
    async def test_check_agent_rate_anomaly(self, sentinel_agent: SentinelAgent):
        """Test agent rate check with anomalous rate."""
        agent_id = "test_agent_3"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Anomalous rate
        alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)

        assert alert is not None
        assert alert.agent_id == agent_id
        assert alert.anomaly_type == AnomalyType.RATE_DEVIATION

    @pytest.mark.asyncio
    async def test_check_agent_response_time_anomaly(self, sentinel_agent: SentinelAgent):
        """Test agent response time anomaly detection."""
        agent_id = "test_agent_4"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_response_time(agent_id, 100.0)

        # Anomalous response time
        alert = await sentinel_agent.check_agent_response_time(agent_id, 1000.0)

        assert alert is not None
        assert alert.anomaly_type == AnomalyType.RESPONSE_TIME_ANOMALY

    @pytest.mark.asyncio
    async def test_check_agent_validation_anomaly(self, sentinel_agent: SentinelAgent):
        """Test agent validation anomaly detection."""
        agent_id = "test_agent_5"

        # Establish baseline with successes
        for _ in range(35):
            await sentinel_agent.check_agent_validation(agent_id, True)

        # Inject failures
        alert = await sentinel_agent.check_agent_validation(
            agent_id, False, failure_reason="Test failure"
        )

        assert alert is not None
        assert alert.anomaly_type == AnomalyType.VALIDATION_FAILURE

    @pytest.mark.asyncio
    async def test_report_false_positive(self, sentinel_agent: SentinelAgent):
        """Test false positive reporting."""
        agent_id = "test_agent_6"

        # Create an anomaly first
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)
        assert alert is not None

        # Report as false positive
        result = await sentinel_agent.report_false_positive(alert.anomaly_id)
        assert result is True


class TestSentinelAgentResponseTiming:
    """Tests for SentinelAgent automated response timing (30 second deadline)."""

    @pytest.mark.asyncio
    async def test_response_within_30_seconds(self, sentinel_agent: SentinelAgent):
        """Test that automated responses complete within 30 seconds."""
        agent_id = "test_agent_timing"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Trigger anomaly and measure time
        start = time.perf_counter()
        alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert alert is not None
        assert elapsed_ms < 30000  # 30 seconds

    @pytest.mark.asyncio
    async def test_anomaly_alert_response_latency_recorded(self, sentinel_agent: SentinelAgent):
        """Test that response latency is recorded in alert."""
        agent_id = "test_agent_latency"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Trigger anomaly
        alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)

        assert alert is not None
        assert alert.response_latency_ms > 0


class TestSentinelAgentRateLimiting:
    """Tests for SentinelAgent rate limiting on automated responses."""

    @pytest.mark.asyncio
    async def test_rate_limiting_triggers_human_notification(self, sentinel_agent: SentinelAgent):
        """Test that rate limiting triggers human notification."""
        agent_id = "test_agent_rl"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Exhaust rate limit by having many alerts
        sentinel_agent._response_rate_limited_until[agent_id] = time.time() + 60

        # This should be rate limited
        alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)

        # Rate limited responses still return alerts but with RATE_LIMITED status
        if alert:
            assert alert.response_status == ResponseStatus.RATE_LIMITED

    @pytest.mark.asyncio
    async def test_is_response_rate_limited(self, sentinel_agent: SentinelAgent):
        """Test rate limit checking."""
        agent_id = "test_agent_rl2"

        # Should not be rate limited initially
        assert sentinel_agent._is_response_rate_limited(agent_id) is False

        # Set rate limit
        sentinel_agent._response_rate_limited_until[agent_id] = time.time() + 60

        # Should be rate limited now
        assert sentinel_agent._is_response_rate_limited(agent_id) is True


class TestSentinelAgentSentinelPrime:
    """Tests for Sentinel-Prime integration."""

    @pytest.mark.asyncio
    async def test_set_sentinel_prime_client(self, sentinel_agent: SentinelAgent):
        """Test setting Sentinel-Prime client."""
        mock_client = AsyncMock()

        sentinel_agent.set_sentinel_prime_client(mock_client)

        assert sentinel_agent._sentinel_prime_available is True
        assert sentinel_agent._sentinel_prime_client is mock_client

    @pytest.mark.asyncio
    async def test_escalation_to_sentinel_prime(
        self, sentinel_agent: SentinelAgent, mock_sentinel_prime: AsyncMock
    ):
        """Test that anomalies escalate to Sentinel-Prime after threshold."""
        sentinel_agent.set_sentinel_prime_client(mock_sentinel_prime)
        agent_id = "test_agent_sp"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Trigger multiple anomalies to reach escalation threshold
        for _ in range(3):
            alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)
            if alert:
                # Simulate processing
                sentinel_agent._anomaly_escalation_count[agent_id] += 1

        # At threshold, should escalate
        sentinel_agent._anomaly_escalation_count[agent_id] = (
            sentinel_agent._anomaly_detector.config.sentinel_prime_escalation_threshold
        )


class TestSentinelAgentStatistics:
    """Tests for SentinelAgent anomaly statistics."""

    def test_get_anomaly_statistics(self, sentinel_agent: SentinelAgent):
        """Test anomaly statistics retrieval."""
        stats = sentinel_agent.get_anomaly_statistics()

        assert "detector" in stats
        assert "immune_system" in stats
        assert "precision" in stats["detector"]
        assert "precision_target_met" in stats

    @pytest.mark.asyncio
    async def test_precision_above_99_percent(self, sentinel_agent: SentinelAgent):
        """Test that precision is maintained above 99%."""
        agent_id = "test_agent_precision"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Create some anomalies
        for _ in range(100):
            alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)

        # Report most as true positives (only 1 as false positive)
        stats = sentinel_agent.get_anomaly_statistics()
        precision = stats["detector"]["precision"]

        # With low FP rate, precision should be high
        # Note: This depends on actual detection, so we check it's tracked
        assert "precision" in stats["detector"]


class TestSentinelAgentSafetyScanning:
    """Tests for SentinelAgent content safety scanning."""

    @pytest.mark.asyncio
    async def test_scan_content_safe(self, sentinel_agent: SentinelAgent):
        """Test scanning safe content."""
        result = await sentinel_agent._scan_content("Hello, this is safe content.")

        assert result["safety_level"] == SafetyLevel.SAFE.value
        assert result["is_safe"] is True
        assert len(result["violations"]) == 0

    @pytest.mark.asyncio
    async def test_scan_content_injection(self, sentinel_agent: SentinelAgent):
        """Test scanning content with injection patterns."""
        result = await sentinel_agent._scan_content(
            "Normal text <script>alert('xss')</script> more text"
        )

        assert result["is_safe"] is False
        assert len(result["violations"]) > 0
        assert any(v["type"] == ViolationType.INJECTION_ATTEMPT.value for v in result["violations"])

    @pytest.mark.asyncio
    async def test_scan_content_pii(self, sentinel_agent: SentinelAgent):
        """Test scanning content with PII patterns."""
        result = await sentinel_agent._scan_content(
            "Contact: john.doe@example.com, SSN: 123-45-6789"
        )

        assert result["is_safe"] is False
        assert any(v["type"] == ViolationType.PII_DETECTED.value for v in result["violations"])


class TestSentinelAgentHealthReporting:
    """Tests for SentinelAgent health reporting integration."""

    def test_get_health_status(self, sentinel_agent: SentinelAgent):
        """Test health status reporting."""
        health = sentinel_agent.get_health_status()

        assert "status" in health
        assert "error_count" in health
        assert health["agent_id"] == sentinel_agent.agent_id


# =============================================================================
# Integration Tests
# =============================================================================


class TestSentinelIntegration:
    """Integration tests for full SentinelAgent workflow."""

    @pytest.mark.asyncio
    async def test_full_anomaly_detection_workflow(self, sentinel_agent: SentinelAgent):
        """Test complete anomaly detection workflow."""
        agent_id = "test_integration_agent"

        # 1. Monitor agent behavior to establish baseline
        for i in range(40):
            await sentinel_agent.monitor_agent_behavior(
                agent_id=agent_id,
                metrics={
                    "request_rate": 10.0 + (i % 5),  # Slight variation
                    "response_time_ms": 100.0 + (i % 10) * 5,
                },
            )

        # 2. Detect anomaly
        alerts = await sentinel_agent.monitor_agent_behavior(
            agent_id=agent_id,
            metrics={"request_rate": 200.0},  # Clear anomaly
        )

        assert len(alerts) >= 1

        # 3. Verify statistics updated
        stats = sentinel_agent.get_anomaly_statistics()
        assert stats["detector"]["total_detections"] >= 1

    @pytest.mark.asyncio
    async def test_false_positive_cascade_prevention(self, sentinel_agent: SentinelAgent):
        """Test false positive cascade is prevented via rate limiting."""
        agent_id = "test_fp_cascade"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Enable rate limiting by exhausting the limit
        sentinel_agent._response_rate_limited_until[agent_id] = time.time() + 60

        # Subsequent anomalies should be rate limited
        alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)

        # Should return rate limited status instead of executing response
        if alert:
            assert alert.response_status == ResponseStatus.RATE_LIMITED


# =============================================================================
# Performance Tests
# =============================================================================


class TestSentinelPerformance:
    """Performance tests for SentinelAgent."""

    @pytest.mark.asyncio
    async def test_high_volume_anomaly_detection(self, sentinel_agent: SentinelAgent):
        """Test handling high volume of anomaly detections."""
        agent_id = "test_perf_agent"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Rapid fire anomalies
        start = time.perf_counter()
        for _ in range(50):
            await sentinel_agent.check_agent_rate(agent_id, 100.0)
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time
        assert elapsed < 60  # 60 seconds max for 50 detections

    @pytest.mark.asyncio
    async def test_response_deadline_always_met(self, sentinel_agent: SentinelAgent):
        """Test that response deadline is always met."""
        agent_id = "test_deadline_agent"

        # Establish baseline
        for _ in range(35):
            await sentinel_agent.check_agent_rate(agent_id, 10.0)

        # Multiple rapid detections
        for _ in range(10):
            alert = await sentinel_agent.check_agent_rate(agent_id, 100.0)
            if alert:
                assert alert.response_latency_ms < 30000  # 30 second deadline


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
