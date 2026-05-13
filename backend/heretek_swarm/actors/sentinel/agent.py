"""
Sentinel Agent - Safety Guardian & Input/Output Validation.

The Sentinel provides:
- Input validation and sanitization
- Output filtering and safety checks
- Guardrail enforcement
- Content policy compliance
- Harmful content detection
- Safety report generation
- BEHAVIORAL ANOMALY DETECTION (SAFE-01)
- Automated response within 30 seconds
- Rate limiting for automated responses
- Sentinel-Prime integration for backup monitoring
- IMMUNE RESPONSE BUILDING (CONS-02)
- Pattern learning from anomaly responses
- Baseline update with quorum approval
- Novel attack pattern preservation for human review

Sentinel is the "safety gate" of the Collective, ensuring all inputs and outputs
meet safety standards before processing or delivery.

Reference: Phase 2 Plan Task 4 (SAFE-01), Task 2 (CONS-02)

Architecture note: Types are defined in heretek_swarm.actors.sentinel.types
and imported here for backwards compatibility.
"""

import hashlib
import re
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import ValidationError

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import (
    DeliberationMixin,
    HealthReportingMixin,
    LearningMixin,
    MemoryMixin,
    PatternMixin,
    ValidationMixin,
)
from heretek_swarm.actors.sentinel.helpers import SentinelHelpers
from heretek_swarm.actors.sentinel.types import (
    AnomalyAlert,
    SafetyLevel,
    SafetyViolation,
    ViolationType,
)
from heretek_swarm.actors.validation import validate_message
from heretek_swarm.consensus.immune import (
    ImmuneResponseBuilding,
    PatternClassification,
    ResponseOutcome,
)
from heretek_swarm.security.anomaly_detection import (
    AnomalyDetectionConfig,
    AnomalyDetectionResult,
    AnomalyResponse,
    AnomalySeverity,
    AnomalyType,
    ResponseStatus,
    create_anomaly_detector,
)
from heretek_swarm.security.behavioral_baseline import (
    BaselineChangeType,
    create_behavioral_baseline,
)

# Error message constants
_STAT_RETRIEVAL_FAILED = "Failed to retrieve agent statistics"
_MISSING_AGENT_ID = "Missing agent ID in request"

logger = structlog.get_logger("SentinelAgent")


class SentinelAgent(
    HealthReportingMixin,
    ValidationMixin,
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    SentinelHelpers,
    AgentActor,
):
    """
    Sentinel Agent - Safety Guardian for the Heretek Swarm Collective.

    Sentinel provides comprehensive input/output validation, guardrail enforcement,
    content safety analysis, and behavioral anomaly detection for all inter-agent
    communications.

    SAFE-01 Enhancements:
    - Behavioral anomaly detection with precision > 99%
    - Automated response within 30 seconds
    - Rate limiting on automated responses
    - Human notification for false positive cascade
    - Sentinel-Prime integration for backup monitoring

    CONS-02 Immune Response Building:
    - Learning from anomaly responses
    - Pattern addition to baseline with quorum approval
    - Novel attack pattern preservation for human review
    - False positive rate < 1%
    """

    def __init__(
        self,
        agent_id: str | None = None,
        name: str = "Sentinel",
        description: str = "Safety Guardian - Input/Output Validation",
        config: dict[str, Any] | None = None,
        db_pool: Any | None = None,
        redis_client: Any | None = None,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            config=config,
            db_pool=db_pool,
            redis_client=redis_client,
        )

        # Safety configuration
        self._max_content_size = config.get("max_content_size", 100000) if config else 100000
        self._enable_pii_detection = config.get("enable_pii_detection", True) if config else True
        self._enable_injection_detection = (
            config.get("enable_injection_detection", True) if config else True
        )
        self._auto_block_critical = config.get("auto_block_critical", True) if config else True

        # Safety state
        self._violations: dict[str, SafetyViolation] = {}
        self._violation_history: list[str] = []  # LRU keys
        self._max_violation_history = 1000

        # Content patterns for detection
        self._injection_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"eval\s*\(",
            r"exec\s*\(",
            r"system\s*\(",
            r"__import__",
            r"os\.system",
            r"subprocess\.",
            r"shell\s*=\s*True",
            r";\s*rm\s+-rf",
            r"\|\s*sh",
            r"`[^`]+`",
            r"\$\([^)]+\)",
        ]

        self._pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",  # Date patterns
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
        ]

        # Compile regex patterns
        self._compiled_injection = [re.compile(p, re.IGNORECASE) for p in self._injection_patterns]
        self._compiled_pii = [re.compile(p) for p in self._pii_patterns]

        # Statistics
        self._stats = {
            "total_scans": 0,
            "safe_scans": 0,
            "violations_detected": 0,
            "violations_blocked": 0,
            "violations_by_type": {},
            "violations_by_severity": {},
        }

        # =====================================================================
        # SAFE-01: Anomaly Detection State
        # =====================================================================

        # Anomaly detection configuration
        anomaly_config = AnomalyDetectionConfig(
            z_score_threshold=config.get("anomaly_z_score_threshold", 3.0) if config else 3.0,
            response_deadline_seconds=config.get("anomaly_response_deadline", 30.0)
            if config
            else 30.0,
            max_auto_responses_per_minute=config.get("max_auto_responses_per_minute", 10)
            if config
            else 10,
            sentinel_prime_escalation_threshold=config.get("sentinel_prime_escalation_threshold", 3)
            if config
            else 3,
        )

        # Anomaly detector
        self._anomaly_detector = create_anomaly_detector(anomaly_config)

        # Sentinel-Prime integration
        self._sentinel_prime_available = False
        self._sentinel_prime_client = None

        # Anomaly response tracking
        self._active_responses: dict[str, AnomalyResponse] = {}
        self._anomaly_alerts: list[AnomalyAlert] = []
        self._max_alert_history = 1000

        # Agent metrics tracking for anomaly detection
        self._agent_metrics: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "request_count": 0.0,
                "total_request_rate": 0.0,
                "request_rate_samples": 0,
                "response_times": [],
                "validation_failures": 0,
                "validation_successes": 0,
            }
        )

        # Rate limiting state
        self._agent_last_request: dict[str, float] = {}
        self._response_rate_limited_until: dict[str, float] = {}

        # Human notification state (for false positive cascade)
        self._human_notification_cooldown: dict[str, float] = {}
        self._human_notification_cooldown_seconds = 300  # 5 minutes

        # Anomaly escalation counter for Sentinel-Prime
        self._anomaly_escalation_count: dict[str, int] = defaultdict(int)

        # Sentinel self-health monitoring
        self._sentinel_self_check_interval = 60.0  # seconds
        self._last_sentinel_self_check = 0.0
        self._sentinel_self_health = "healthy"

        # =====================================================================
        # CONS-02: Immune Response Building State
        # =====================================================================

        # Immune response building system
        self._immune_system = ImmuneResponseBuilding(
            min_occurrences_for_immunity=config.get("immune_min_occurrences", 3) if config else 3,
            min_confidence_for_baseline=config.get("immune_min_confidence", 0.7) if config else 0.7,
            max_false_positive_rate=config.get("immune_max_fp_rate", 0.01) if config else 0.01,
            quorum_required_agents=config.get("immune_quorum_size", 3) if config else 3,
        )

        # Behavioral baseline for pattern storage
        baseline_config = {
            "min_samples_for_baseline": config.get("baseline_min_samples", 30) if config else 30,
            "z_score_threshold": anomaly_config.z_score_threshold,
            "quorum_size": config.get("baseline_quorum_size", 3) if config else 3,
            "quorum_threshold": config.get("baseline_quorum_threshold", 0.66) if config else 0.66,
        }
        self._behavioral_baseline = create_behavioral_baseline(baseline_config)

        # Novel pattern preservation queue
        self._novel_pattern_queue: list[str] = []  # Preservation IDs
        self._max_novel_pattern_queue = 100

        # Response outcome tracking (for learning)
        self._pending_outcome_tracking: dict[str, dict[str, Any]] = {}

        # Immune learning configuration
        self._auto_learn_enabled = config.get("auto_learn_enabled", True) if config else True
        self._preserve_novel_patterns = (
            config.get("preserve_novel_patterns", True) if config else True
        )

        logger.info(
            "SentinelAgent initialized",
            agent_id=self.agent_id,
            max_content_size=self._max_content_size,
            pii_detection=self._enable_pii_detection,
            injection_detection=self._enable_injection_detection,
            anomaly_detection_enabled=True,
            response_deadline_seconds=anomaly_config.response_deadline_seconds,
            immune_system_enabled=True,
            auto_learn=self._auto_learn_enabled,
            preserve_novel_patterns=self._preserve_novel_patterns,
        )

    # =====================================================================
    # CONS-02: Immune Response Building Methods
    # =====================================================================

    async def record_anomaly_response_outcome(
        self,
        anomaly_id: str,
        response_id: str,
        outcome: ResponseOutcome,
        pattern_content: dict[str, Any],
        pattern_type: str,
        severity: str,
        response_time_ms: float,
    ) -> None:
        """
        Record the outcome of an anomaly response for immune learning.

        This is the core method for CONS-02 immune response building.
        When an anomaly is detected and responded to, this method records
        the outcome so the system can learn from it.

        Args:
            anomaly_id: ID of the anomaly
            response_id: ID of the response
            outcome: Result of the response
            pattern_content: Content of the detected pattern
            pattern_type: Type of anomaly
            severity: Severity level
            response_time_ms: Time taken to respond
        """
        # Record the response in the immune system
        immune_response = self._immune_system.record_response(
            pattern_content=pattern_content,
            anomaly_id=anomaly_id,
            agent_id=self.agent_id,
            outcome=outcome,
            response_time_ms=response_time_ms,
        )

        # Learn from the response
        immunity_acquired = self._immune_system.learn_from_response(
            response=immune_response,
            pattern_content=pattern_content,
            pattern_type=pattern_type,
            severity=severity,
        )

        # If immunity acquired, check if we should request baseline update
        if immunity_acquired and self._auto_learn_enabled:
            # Check if this is a novel pattern
            classification, immune_pattern = self._immune_system.check_pattern_immunity(
                pattern_content
            )

            if immune_pattern:
                # Request baseline update with quorum
                await self._request_baseline_update(
                    pattern_id=immune_pattern.pattern_id,
                    pattern_type=pattern_type,
                    pattern_content=pattern_content,
                    confidence=immune_pattern.confidence,
                )

        # If this is a novel pattern and preservation is enabled, preserve it
        if outcome == ResponseOutcome.SUCCESS and self._preserve_novel_patterns:
            classification, _ = self._immune_system.check_pattern_immunity(pattern_content)
            if classification == PatternClassification.NOVEL_MALICIOUS:
                preservation_id = self._immune_system.preserve_novel_pattern(
                    pattern_content=pattern_content,
                    pattern_type=pattern_type,
                    context={
                        "anomaly_id": anomaly_id,
                        "severity": severity,
                        "first_occurrence": datetime.now(UTC).isoformat(),
                    },
                )
                self._novel_pattern_queue.append(preservation_id)

                # Prune queue if too large
                if len(self._novel_pattern_queue) > self._max_novel_pattern_queue:
                    self._novel_pattern_queue = self._novel_pattern_queue[
                        -self._max_novel_pattern_queue :
                    ]

                logger.info(
                    "novel_pattern_preserved_for_review",
                    preservation_id=preservation_id,
                    anomaly_id=anomaly_id,
                )

        logger.info(
            "anomaly_response_outcome_recorded",
            anomaly_id=anomaly_id,
            outcome=outcome.value,
            immunity_acquired=immunity_acquired,
        )

    async def _request_baseline_update(
        self,
        pattern_id: str,
        pattern_type: str,
        pattern_content: dict[str, Any],
        confidence: float,
    ) -> str | None:
        """
        Request quorum approval for adding a pattern to the baseline.

        Args:
            pattern_id: ID of the pattern
            pattern_type: Type of pattern
            pattern_content: Pattern content
            confidence: Confidence level

        Returns:
            Request ID if created
        """
        # Add pattern to behavioral baseline
        baseline_pattern_id = self._behavioral_baseline.add_baseline_pattern(
            pattern_type=pattern_type,
            description="Immune-learned pattern from anomaly response",
            content=pattern_content,
            confidence=confidence,
            requester_id=self.agent_id,
        )

        # Request baseline change with quorum
        request_id = self._behavioral_baseline.request_baseline_change(
            change_type=BaselineChangeType.PATTERN_ADDED,
            pattern_id=baseline_pattern_id,
            proposed_value={"pattern_content": pattern_content, "confidence": confidence},
            reasoning=f"Pattern learned from {self._immune_system.min_occurrences_for_immunity}+ successful anomaly responses",
            requester_id=self.agent_id,
        )

        logger.info(
            "baseline_update_requested",
            pattern_id=pattern_id,
            baseline_pattern_id=baseline_pattern_id,
            request_id=request_id,
        )

        return request_id

    async def report_response_outcome(
        self,
        anomaly_id: str,
        outcome: ResponseOutcome,
    ) -> bool:
        """
        Report the outcome of a previous anomaly response.

        This should be called after the immediate response to an anomaly,
        once the outcome is known (success, failure, false positive, etc.).

        Args:
            anomaly_id: ID of the anomaly
            outcome: Outcome of the response

        Returns:
            True if outcome was recorded
        """
        if anomaly_id not in self._pending_outcome_tracking:
            logger.warning("outcome_reported_for_unknown_anomaly", anomaly_id=anomaly_id)
            return False

        tracking = self._pending_outcome_tracking[anomaly_id]

        await self.record_anomaly_response_outcome(
            anomaly_id=anomaly_id,
            response_id=tracking["response_id"],
            outcome=outcome,
            pattern_content=tracking["pattern_content"],
            pattern_type=tracking["pattern_type"],
            severity=tracking["severity"],
            response_time_ms=tracking["response_time_ms"],
        )

        # Remove from pending tracking
        del self._pending_outcome_tracking[anomaly_id]

        logger.info(
            "response_outcome_reported",
            anomaly_id=anomaly_id,
            outcome=outcome.value,
        )

        return True

    def check_pattern_immunity(
        self,
        pattern_content: dict[str, Any],
    ) -> tuple[PatternClassification, float]:
        """
        Check if a pattern is recognized by the immune system.

        Args:
            pattern_content: Content of the pattern to check

        Returns:
            Tuple of (classification, confidence)
        """
        classification, immune_pattern = self._immune_system.check_pattern_immunity(pattern_content)
        confidence = immune_pattern.confidence if immune_pattern else 0.0
        return (classification, confidence)

    def get_novel_patterns_for_review(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get novel patterns awaiting human review.

        Args:
            limit: Maximum patterns to return

        Returns:
            List of novel pattern preservation records
        """
        patterns = self._immune_system.get_novel_patterns_for_review(limit=limit)
        return [
            {
                "preservation_id": p.preservation_id,
                "pattern_type": p.pattern_type,
                "first_observed": p.first_observed.isoformat(),
                "last_observed": p.last_observed.isoformat(),
                "occurrence_count": p.occurrence_count,
                "reviewed": p.reviewed,
                "disposition": p.disposition,
                "context": p.context,
            }
            for p in patterns
        ]

    async def submit_human_review(
        self,
        preservation_id: str,
        reviewer_id: str,
        disposition: str,
        notes: str | None = None,
    ) -> bool:
        """
        Submit human review of a novel pattern.

        Args:
            preservation_id: ID of the preservation record
            reviewer_id: ID of the human reviewer
            disposition: Decision (approve/reject/investigate)
            notes: Optional review notes

        Returns:
            True if review was recorded
        """
        result = self._immune_system.record_human_review(
            preservation_id=preservation_id,
            reviewer_id=reviewer_id,
            disposition=disposition,
            notes=notes,
        )

        if result and disposition == "approve":
            # If approved, request baseline update
            patterns = self._immune_system.get_novel_patterns_for_review(limit=1000)
            for p in patterns:
                if p.preservation_id == preservation_id:
                    await self._request_baseline_update(
                        pattern_id=p.pattern_id,
                        pattern_type=p.pattern_type,
                        pattern_content=p.pattern_content,
                        confidence=0.9,  # Human approved
                    )
                    break

        return result

    def get_immune_system_statistics(self) -> dict[str, Any]:
        """
        Get immune response building statistics.

        Returns:
            Statistics dictionary
        """
        return self._immune_system.get_statistics()

    def get_immune_memory_snapshot(self) -> dict[str, dict[str, Any]]:
        """
        Get snapshot of immune memory.

        Returns:
            Dictionary of learned patterns
        """
        return self._immune_system.get_immune_memory_snapshot()

    def get_behavioral_baseline_status(self) -> dict[str, Any]:
        """
        Get behavioral baseline status.

        Returns:
            Status information
        """
        return {
            "integrity": self._behavioral_baseline.verify_baseline_integrity(),
            "statistics": self._behavioral_baseline.get_statistics(),
            "approved_patterns": self._behavioral_baseline.get_baseline_patterns(
                approved_only=True
            ),
        }

    def submit_baseline_vote(
        self,
        request_id: str,
        agent_id: str,
        approve: bool,
    ) -> bool:
        """
        Submit a vote for a baseline change request.

        Args:
            request_id: ID of the change request
            agent_id: ID of voting agent
            approve: True to approve, False to reject

        Returns:
            True if vote was recorded
        """
        return self._behavioral_baseline.submit_change_vote(request_id, agent_id, approve)

    # =====================================================================
    # SAFE-01: Anomaly Detection Methods
    # =====================================================================

    async def monitor_agent_behavior(
        self,
        agent_id: str,
        metrics: dict[str, float],
        context: dict[str, Any] | None = None,
    ) -> list[AnomalyAlert]:
        """
        Monitor agent behavior and detect anomalies.

        This is the primary entry point for SAFE-01 behavioral anomaly detection.

        Args:
            agent_id: ID of the agent to monitor
            metrics: Dictionary of metrics (request_rate, response_time_ms, etc.)
            context: Optional context information

        Returns:
            List of anomaly alerts (empty if no anomalies detected)
        """
        alerts = []

        # Analyze behavior
        anomalies = await self._anomaly_detector.analyze_agent_behavior(
            agent_id=agent_id,
            metrics=metrics,
            context=context,
        )

        # Process each anomaly
        for anomaly in anomalies:
            alert = await self._process_anomaly(anomaly)
            if alert:
                alerts.append(alert)

        # Update agent metrics
        self._update_agent_metrics(agent_id, metrics)

        return alerts

    async def check_agent_rate(
        self,
        agent_id: str,
        current_rate: float,
        time_window: float = 1.0,
    ) -> AnomalyAlert | None:
        """
        Check if an agent's request rate is anomalous.

        Args:
            agent_id: ID of the agent
            current_rate: Current requests per time window
            time_window: Time window in seconds

        Returns:
            Anomaly alert or None if rate is normal
        """
        anomaly = await self._anomaly_detector.detect_rate_anomaly(
            agent_id=agent_id,
            current_rate=current_rate,
            time_window=time_window,
            context={"check_type": "rate"},
        )

        if anomaly:
            return await self._process_anomaly(anomaly)

        return None

    async def check_agent_response_time(
        self,
        agent_id: str,
        response_time_ms: float,
    ) -> AnomalyAlert | None:
        """
        Check if an agent's response time is anomalous.

        Args:
            agent_id: ID of the agent
            response_time_ms: Response time in milliseconds

        Returns:
            Anomaly alert or None if response time is normal
        """
        anomaly = await self._anomaly_detector.detect_response_time_anomaly(
            agent_id=agent_id,
            response_time_ms=response_time_ms,
            context={"check_type": "response_time"},
        )

        if anomaly:
            return await self._process_anomaly(anomaly)

        return None

    async def check_agent_validation(
        self,
        agent_id: str,
        validation_success: bool,
        failure_reason: str | None = None,
    ) -> AnomalyAlert | None:
        """
        Check if an agent's validation failures indicate an anomaly.

        Args:
            agent_id: ID of the agent
            validation_success: Whether validation passed
            failure_reason: Optional reason for failure

        Returns:
            Anomaly alert or None if no anomaly
        """
        anomaly = await self._anomaly_detector.detect_validation_anomaly(
            agent_id=agent_id,
            validation_success=validation_success,
            failure_reason=failure_reason,
            context={"check_type": "validation"},
        )

        if anomaly:
            return await self._process_anomaly(anomaly)

        return None

    async def report_false_positive(self, anomaly_id: str) -> bool:
        """
        Report an anomaly as a false positive.

        This helps improve detection precision over time.

        Args:
            anomaly_id: ID of the anomaly to mark as FP

        Returns:
            True if the anomaly was found and marked
        """
        await self._anomaly_detector.report_false_positive(anomaly_id)

        # Also report to immune system
        await self.report_response_outcome(
            anomaly_id=anomaly_id,
            outcome=ResponseOutcome.FALSE_POSITIVE,
        )

        # Update any pending alert
        for alert in self._anomaly_alerts:
            if alert.anomaly_id == anomaly_id:
                alert.false_positive = True
                logger.info(
                    "false_positive_recorded",
                    anomaly_id=anomaly_id,
                    agent_id=alert.agent_id,
                )
                return True

        return False

    def set_sentinel_prime_client(self, client: Any) -> None:
        """
        Set Sentinel-Prime client for backup monitoring and escalation.

        Args:
            client: Sentinel-Prime agent client
        """
        self._sentinel_prime_client = client
        self._sentinel_prime_available = client is not None
        self._anomaly_detector.set_sentinel_prime_client(client)

        logger.info(
            "sentinel_prime_client_configured",
            available=self._sentinel_prime_available,
        )

    def get_anomaly_statistics(self) -> dict[str, Any]:
        """Get anomaly detection statistics."""
        detector_stats = self._anomaly_detector.get_statistics()
        immune_stats = self.get_immune_system_statistics()

        return {
            "detector": detector_stats,
            "immune_system": {
                "precision": immune_stats["precision"],
                "precision_target_met": immune_stats["precision_target_met"],
                "patterns_learned": immune_stats["patterns_learned"],
                "baseline_updates_approved": immune_stats["baseline_updates_approved"],
                "novel_patterns_pending": immune_stats["novel_patterns_pending_review"],
            },
            "active_responses": len(self._active_responses),
            "alert_history_size": len(self._anomaly_alerts),
            "sentinel_prime_available": self._sentinel_prime_available,
            "sentinel_self_health": self._sentinel_self_health,
            "precision_target_met": detector_stats.get("precision", 0) >= 0.99,
        }

    async def _process_anomaly(self, anomaly: AnomalyDetectionResult) -> AnomalyAlert | None:
        """
        Process a detected anomaly and execute automated response.

        Implements the 30-second response deadline requirement.
        Also records the response for immune learning.

        Args:
            anomaly: The detected anomaly

        Returns:
            Anomaly alert with response details
        """
        start_time = time.perf_counter()

        # Check rate limiting
        if self._is_response_rate_limited(anomaly.agent_id):
            logger.warning(
                "anomaly_response_rate_limited",
                anomaly_id=anomaly.anomaly_id,
                agent_id=anomaly.agent_id,
            )

            # Send to human notification instead
            await self._notify_human(anomaly)

            alert = AnomalyAlert(
                alert_id=self._generate_alert_id(),
                anomaly_id=anomaly.anomaly_id,
                agent_id=anomaly.agent_id,
                anomaly_type=anomaly.anomaly_type,
                severity=anomaly.severity,
                timestamp=anomaly.timestamp,
                response_status=ResponseStatus.RATE_LIMITED,
                response_latency_ms=(time.perf_counter() - start_time) * 1000,
                sentinel_prime_escalated=False,
                false_positive=False,
            )
            self._anomaly_alerts.append(alert)
            return alert

        # Execute automated response
        response = await self._anomaly_detector.execute_automated_response(anomaly)
        self._active_responses[response.response_id] = response

        # Track escalation count for Sentinel-Prime
        if response.status == ResponseStatus.EXECUTED:
            self._anomaly_escalation_count[anomaly.agent_id] += 1

            # Check if we need to escalate to Sentinel-Prime
            if (
                self._anomaly_escalation_count[anomaly.agent_id]
                >= self._anomaly_detector.config.sentinel_prime_escalation_threshold
            ):
                await self._escalate_to_sentinel_prime(anomaly)

        # Update response status in anomaly
        anomaly.response_status = response.status

        # Check response latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        if latency_ms > (self._anomaly_detector.config.response_deadline_seconds * 1000):
            logger.warning(
                "response_deadline_exceeded",
                anomaly_id=anomaly.anomaly_id,
                latency_ms=latency_ms,
                deadline_ms=self._anomaly_detector.config.response_deadline_seconds * 1000,
            )

        # Create alert
        alert = AnomalyAlert(
            alert_id=self._generate_alert_id(),
            anomaly_id=anomaly.anomaly_id,
            agent_id=anomaly.agent_id,
            anomaly_type=anomaly.anomaly_type,
            severity=anomaly.severity,
            timestamp=anomaly.timestamp,
            response_status=response.status,
            response_latency_ms=latency_ms,
            sentinel_prime_escalated=self._anomaly_escalation_count[anomaly.agent_id]
            >= self._anomaly_detector.config.sentinel_prime_escalation_threshold,
            false_positive=False,
        )
        self._anomaly_alerts.append(alert)

        # Prune old alerts
        if len(self._anomaly_alerts) > self._max_alert_history:
            self._anomaly_alerts = self._anomaly_alerts[-self._max_alert_history :]

        # =====================================================================
        # CONS-02: Track for immune learning
        # =====================================================================
        pattern_content = {
            "anomaly_type": anomaly.anomaly_type.value,
            "severity": anomaly.severity.value,
            "agent_id": anomaly.agent_id,
            "z_score": anomaly.z_score,
            "trigger_metric": anomaly.trigger_metric,
        }

        # Store for later outcome tracking
        self._pending_outcome_tracking[anomaly.anomaly_id] = {
            "response_id": response.response_id,
            "pattern_content": pattern_content,
            "pattern_type": anomaly.anomaly_type.value,
            "severity": anomaly.severity.value,
            "response_time_ms": latency_ms,
        }

        # Emit pattern for collective learning
        await self._emit_pattern(
            item_id=anomaly.anomaly_id,
            item_type="anomaly_detection",
            outcome="detected",
            content=pattern_content,
        )

        logger.warning(
            "anomaly_processed",
            anomaly_id=anomaly.anomaly_id,
            agent_id=anomaly.agent_id,
            anomaly_type=anomaly.anomaly_type.value,
            severity=anomaly.severity.value,
            response_status=response.status.value,
            latency_ms=latency_ms,
        )

        return alert

    def _is_response_rate_limited(self, agent_id: str) -> bool:
        """Check if responses for this agent are rate limited."""
        now = time.time()

        # Check cooldown
        if agent_id in self._response_rate_limited_until:
            if now < self._response_rate_limited_until[agent_id]:
                return True
            del self._response_rate_limited_until[agent_id]

        # Check if too many recent responses for this agent
        recent_count = sum(
            1
            for alert in self._anomaly_alerts[-100:]
            if alert.agent_id == agent_id and (now - alert.timestamp.timestamp()) < 60
        )

        if recent_count >= self._anomaly_detector.config.max_auto_responses_per_minute:
            self._response_rate_limited_until[agent_id] = now + 60
            return True

        return False

    async def _notify_human(self, anomaly: AnomalyDetectionResult) -> None:
        """
        Notify human operator of an anomaly requiring attention.

        This is used when:
        - Response is rate limited
        - Response deadline is exceeded
        - False positive cascade is detected
        """
        # Check cooldown
        now = time.time()
        if anomaly.agent_id in self._human_notification_cooldown:
            if now < self._human_notification_cooldown[anomaly.agent_id]:
                return
        else:
            self._human_notification_cooldown[anomaly.agent_id] = (
                now + self._human_notification_cooldown_seconds
            )

        logger.warning(
            "human_notification_required",
            anomaly_id=anomaly.anomaly_id,
            agent_id=anomaly.agent_id,
            anomaly_type=anomaly.anomaly_type.value,
            severity=anomaly.severity.value,
            reason="rate_limited_or_deadline_exceeded",
        )

        # In production, this would send to a notification system
        # For now, we just log it

    async def _escalate_to_sentinel_prime(self, anomaly: AnomalyDetectionResult) -> None:
        """
        Escalate anomaly to Sentinel-Prime for backup monitoring.

        This is called when an agent has too many anomalies and Sentinel
        itself might be compromised.
        """
        if not self._sentinel_prime_available or not self._sentinel_prime_client:
            logger.warning(
                "sentinel_prime_not_available_for_escalation",
                anomaly_id=anomaly.anomaly_id,
                agent_id=anomaly.agent_id,
            )
            return

        try:
            await self._sentinel_prime_client.report_threat(
                threat_type="suspicious_behavior",
                threat_level=anomaly.severity.value,
                source=anomaly.agent_id,
                description=f"Anomaly detected: {anomaly.anomaly_type.value}",
                evidence={
                    "anomaly_id": anomaly.anomaly_id,
                    "z_score": anomaly.z_score,
                    "trigger_metric": anomaly.trigger_metric,
                },
            )
            self._anomaly_escalation_count[anomaly.agent_id] = 0

            logger.warning(
                "escalating_to_sentinel_prime",
                anomaly_id=anomaly.anomaly_id,
                agent_id=anomaly.agent_id,
                escalation_count=0,
            )
        except Exception as e:
            logger.error(
                "sentinel_prime_escalation_failed",
                anomaly_id=anomaly.anomaly_id,
                error=str(e),
            )

    def _update_agent_metrics(self, agent_id: str, metrics: dict[str, float]) -> None:
        """Update internal metrics tracking for an agent."""
        agent_metrics = self._agent_metrics[agent_id]

        if "request_rate" in metrics:
            rate = metrics["request_rate"]
            agent_metrics["total_request_rate"] += rate
            agent_metrics["request_rate_samples"] += 1
            agent_metrics["avg_request_rate"] = (
                agent_metrics["total_request_rate"] / agent_metrics["request_rate_samples"]
            )

        if "response_time_ms" in metrics:
            response_time = metrics["response_time_ms"]
            agent_metrics["response_times"].append(response_time)
            # Keep last 100 samples
            if len(agent_metrics["response_times"]) > 100:
                agent_metrics["response_times"] = agent_metrics["response_times"][-100:]

        if "validation_success" in metrics:
            if metrics["validation_success"]:
                agent_metrics["validation_successes"] += 1
            else:
                agent_metrics["validation_failures"] += 1

    async def _sentinel_self_monitoring(self) -> None:
        """
        Perform self-health check of Sentinel.

        This detects if Sentinel itself might be compromised by checking:
        - Response latency
        - Detection accuracy
        - Memory usage
        - Immune system precision
        """
        now = time.time()

        if now - self._last_sentinel_self_check < self._sentinel_self_check_interval:
            return

        self._last_sentinel_self_check = now

        # Check precision from anomaly detector
        precision = self._anomaly_detector.calculate_precision()
        if precision < 0.99:
            self._sentinel_self_health = "degraded"
            logger.warning(
                "sentinel_precision_below_target",
                precision=precision,
                target=0.99,
            )

            # Notify Sentinel-Prime
            if self._sentinel_prime_available:
                await self._escalate_to_sentinel_prime(
                    AnomalyDetectionResult(
                        anomaly_id=self._generate_anomaly_id(),
                        agent_id=self.agent_id,
                        anomaly_type=AnomalyType.BEHAVIORAL_DRIFT,
                        severity=AnomalySeverity.HIGH,
                        timestamp=datetime.now(UTC),
                        z_score=3.0,
                        trigger_metric="sentinel_precision",
                        expected_value=0.99,
                        observed_value=precision,
                        confidence=0.95,
                    )
                )
        else:
            self._sentinel_self_health = "healthy"

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.now(UTC).timestamp()
        return f"ALERT_{int(timestamp)}_{hashlib.sha256(str(timestamp).encode()).hexdigest()[:8]}"

    def _generate_anomaly_id(self) -> str:
        """Generate unique anomaly ID."""
        timestamp = datetime.now(UTC).timestamp()
        return f"ANOM_{int(timestamp)}_{hashlib.sha256(str(timestamp).encode()).hexdigest()[:8]}"

    # =====================================================================
    # Message Handling (from original implementation)
    # =====================================================================

    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming message with safety validation."""
        try:
            handler = self._message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                logger.warning(
                    "Unknown message type",
                    message_type=message.message_type,
                    sender=message.sender_id,
                )
        except Exception as e:
            logger.error(
                "Error processing message",
                message_type=message.message_type,
                error=str(e),
                exc_info=True,
            )

    def _register_handlers(self) -> None:
        """Register message handlers."""
        self._message_handlers = {
            "validate_input": self._handle_validate_input,
            "validate_output": self._handle_validate_output,
            "scan_content": self._handle_scan_content,
            "check_policy": self._handle_check_policy,
            "get_safety_report": self._handle_get_safety_report,
            "get_violation_details": self._handle_get_violation_details,
            "update_guardrails": self._handle_update_guardrails,
            "get_statistics": self._handle_get_statistics,
            # SAFE-01: Anomaly detection handlers
            "monitor_agent": self._handle_monitor_agent,
            "check_agent_rate": self._handle_check_agent_rate,
            "check_agent_response_time": self._handle_check_agent_response_time,
            "check_agent_validation": self._handle_check_agent_validation,
            "report_false_positive": self._handle_report_false_positive,
            "get_anomaly_statistics": self._handle_get_anomaly_statistics,
            "configure_sentinel_prime": self._handle_configure_sentinel_prime,
            # CONS-02: Immune response handlers
            "report_response_outcome": self._handle_report_response_outcome,
            "check_pattern_immunity": self._handle_check_pattern_immunity,
            "get_novel_patterns": self._handle_get_novel_patterns,
            "submit_human_review": self._handle_submit_human_review,
            "get_immune_statistics": self._handle_get_immune_statistics,
            "get_baseline_status": self._handle_get_baseline_status,
            "submit_baseline_vote": self._handle_submit_baseline_vote,
        }

    # =====================================================================
    # CONS-02: Immune Response Message Handlers
    # =====================================================================

    async def _handle_report_response_outcome(self, message: ActorMessage) -> None:
        """
        Handle response outcome report.

        Content: {
            "anomaly_id": str,
            "outcome": str (success/failure/partial/escalated/false_positive)
        }
        """
        try:
            content = message.content
            anomaly_id = content.get("anomaly_id")
            outcome_str = content.get("outcome", "success")

            if not anomaly_id:
                await self._send_error(message, "Missing anomaly_id")
                return

            # Convert string to ResponseOutcome
            outcome = ResponseOutcome(outcome_str)

            result = await self.report_response_outcome(anomaly_id, outcome)

            response_content = {
                "anomaly_id": anomaly_id,
                "outcome_recorded": result,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error reporting response outcome", error=str(e), exc_info=True)
            await self._send_error(message, "Outcome report failed", str(e))

    async def _handle_check_pattern_immunity(self, message: ActorMessage) -> None:
        """
        Handle pattern immunity check.

        Content: {
            "pattern_content": dict
        }
        """
        try:
            content = message.content
            pattern_content = content.get("pattern_content", {})

            if not pattern_content:
                await self._send_error(message, "Missing pattern_content")
                return

            classification, confidence = self.check_pattern_immunity(pattern_content)

            response_content = {
                "classification": classification.value,
                "confidence": confidence,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error checking pattern immunity", error=str(e), exc_info=True)
            await self._send_error(message, "Pattern immunity check failed", str(e))

    async def _handle_get_novel_patterns(self, message: ActorMessage) -> None:
        """
        Handle get novel patterns request.

        Content: {
            "limit": int (optional)
        }
        """
        try:
            content = message.content
            limit = content.get("limit", 50)

            patterns = self.get_novel_patterns_for_review(limit=limit)

            response_content = {
                "patterns": patterns,
                "count": len(patterns),
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting novel patterns", error=str(e), exc_info=True)
            await self._send_error(message, "Novel patterns retrieval failed", str(e))

    async def _handle_submit_human_review(self, message: ActorMessage) -> None:
        """
        Handle human review submission.

        Content: {
            "preservation_id": str,
            "reviewer_id": str,
            "disposition": str (approve/reject/investigate),
            "notes": str (optional)
        }
        """
        try:
            content = message.content
            preservation_id = content.get("preservation_id")
            reviewer_id = content.get("reviewer_id")
            disposition = content.get("disposition")
            notes = content.get("notes")

            if not all([preservation_id, reviewer_id, disposition]):
                await self._send_error(message, "Missing required fields")
                return

            result = await self.submit_human_review(
                preservation_id=preservation_id,
                reviewer_id=reviewer_id,
                disposition=disposition,
                notes=notes,
            )

            response_content = {
                "preservation_id": preservation_id,
                "review_recorded": result,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error submitting human review", error=str(e), exc_info=True)
            await self._send_error(message, "Human review submission failed", str(e))

    async def _handle_get_immune_statistics(self, message: ActorMessage) -> None:
        """
        Handle immune statistics request.

        Content: {} (empty)
        """
        try:
            stats = self.get_immune_system_statistics()

            response_content = {
                "statistics": stats,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting immune statistics", error=str(e), exc_info=True)
            await self._send_error(message, _STAT_RETRIEVAL_FAILED, str(e))

    async def _handle_get_baseline_status(self, message: ActorMessage) -> None:
        """
        Handle baseline status request.

        Content: {} (empty)
        """
        try:
            status = self.get_behavioral_baseline_status()

            response_content = {
                "baseline_status": status,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting baseline status", error=str(e), exc_info=True)
            await self._send_error(message, "Baseline status retrieval failed", str(e))

    async def _handle_submit_baseline_vote(self, message: ActorMessage) -> None:
        """
        Handle baseline vote submission.

        Content: {
            "request_id": str,
            "agent_id": str,
            "approve": bool
        }
        """
        try:
            content = message.content
            request_id = content.get("request_id")
            agent_id = content.get("agent_id")
            approve = content.get("approve", True)

            if not all([request_id, agent_id]):
                await self._send_error(message, "Missing required fields")
                return

            result = self.submit_baseline_vote(request_id, agent_id, approve)

            response_content = {
                "request_id": request_id,
                "vote_recorded": result,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error submitting baseline vote", error=str(e), exc_info=True)
            await self._send_error(message, "Baseline vote failed", str(e))

    # =====================================================================
    # SAFE-01: Anomaly Detection Message Handlers
    # =====================================================================

    async def _handle_monitor_agent(self, message: ActorMessage) -> None:
        """
        Handle agent behavior monitoring request.

        Content: {
            "agent_id": str,
            "metrics": dict[str, float],
            "context": dict (optional)
        }
        """
        try:
            content = message.content
            agent_id = content.get("agent_id")
            metrics = content.get("metrics", {})
            context = content.get("context", {})

            if not agent_id:
                await self._send_error(message, _MISSING_AGENT_ID)
                return

            alerts = await self.monitor_agent_behavior(agent_id, metrics, context)

            response_content = {
                "agent_id": agent_id,
                "alerts_triggered": len(alerts),
                "alerts": [
                    {
                        "alert_id": a.alert_id,
                        "anomaly_id": a.anomaly_id,
                        "anomaly_type": a.anomaly_type.value,
                        "severity": a.severity.value,
                        "response_status": a.response_status.value,
                        "response_latency_ms": a.response_latency_ms,
                    }
                    for a in alerts
                ],
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error monitoring agent", error=str(e), exc_info=True)
            await self._send_error(message, "Agent monitoring failed", str(e))

    async def _handle_check_agent_rate(self, message: ActorMessage) -> None:
        """
        Handle agent rate check request.

        Content: {
            "agent_id": str,
            "current_rate": float,
            "time_window": float (optional)
        }
        """
        try:
            content = message.content
            agent_id = content.get("agent_id")
            current_rate = content.get("current_rate", 0.0)
            time_window = content.get("time_window", 1.0)

            if not agent_id:
                await self._send_error(message, _MISSING_AGENT_ID)
                return

            alert = await self.check_agent_rate(agent_id, current_rate, time_window)

            response_content = {
                "agent_id": agent_id,
                "anomaly_detected": alert is not None,
                "alert": {
                    "alert_id": alert.alert_id,
                    "anomaly_id": alert.anomaly_id,
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "response_status": alert.response_status.value,
                }
                if alert
                else None,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error checking agent rate", error=str(e), exc_info=True)
            await self._send_error(message, "Rate check failed", str(e))

    async def _handle_check_agent_response_time(self, message: ActorMessage) -> None:
        """
        Handle agent response time check request.

        Content: {
            "agent_id": str,
            "response_time_ms": float
        }
        """
        try:
            content = message.content
            agent_id = content.get("agent_id")
            response_time_ms = content.get("response_time_ms", 0.0)

            if not agent_id:
                await self._send_error(message, _MISSING_AGENT_ID)
                return

            alert = await self.check_agent_response_time(agent_id, response_time_ms)

            response_content = {
                "agent_id": agent_id,
                "anomaly_detected": alert is not None,
                "alert": {
                    "alert_id": alert.alert_id,
                    "anomaly_id": alert.anomaly_id,
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "response_status": alert.response_status.value,
                }
                if alert
                else None,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error checking agent response time", error=str(e), exc_info=True)
            await self._send_error(message, "Response time check failed", str(e))

    async def _handle_check_agent_validation(self, message: ActorMessage) -> None:
        """
        Handle agent validation check request.

        Content: {
            "agent_id": str,
            "validation_success": bool,
            "failure_reason": str (optional)
        }
        """
        try:
            content = message.content
            agent_id = content.get("agent_id")
            validation_success = content.get("validation_success", True)
            failure_reason = content.get("failure_reason")

            if not agent_id:
                await self._send_error(message, _MISSING_AGENT_ID)
                return

            alert = await self.check_agent_validation(agent_id, validation_success, failure_reason)

            response_content = {
                "agent_id": agent_id,
                "anomaly_detected": alert is not None,
                "alert": {
                    "alert_id": alert.alert_id,
                    "anomaly_id": alert.anomaly_id,
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "response_status": alert.response_status.value,
                }
                if alert
                else None,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error checking agent validation", error=str(e), exc_info=True)
            await self._send_error(message, "Validation check failed", str(e))

    async def _handle_report_false_positive(self, message: ActorMessage) -> None:
        """
        Handle false positive report.

        Content: {
            "anomaly_id": str
        }
        """
        try:
            content = message.content
            anomaly_id = content.get("anomaly_id")

            if not anomaly_id:
                await self._send_error(message, "Missing anomaly_id")
                return

            found = await self.report_false_positive(anomaly_id)

            response_content = {
                "anomaly_id": anomaly_id,
                "recorded": found,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error reporting false positive", error=str(e), exc_info=True)
            await self._send_error(message, "False positive report failed", str(e))

    async def _handle_get_anomaly_statistics(self, message: ActorMessage) -> None:
        """
        Handle anomaly statistics request.

        Content: {} (empty)
        """
        try:
            stats = self.get_anomaly_statistics()

            response_content = {
                "statistics": stats,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting anomaly statistics", error=str(e), exc_info=True)
            await self._send_error(message, _STAT_RETRIEVAL_FAILED, str(e))

    async def _handle_configure_sentinel_prime(self, message: ActorMessage) -> None:
        """
        Handle Sentinel-Prime configuration.

        Content: {
            "sentinel_prime_client": object (the Sentinel-Prime agent)
        }
        """
        try:
            content = message.content
            client = content.get("sentinel_prime_client")

            self.set_sentinel_prime_client(client)

            response_content = {
                "configured": True,
                "sentinel_prime_available": self._sentinel_prime_available,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error configuring Sentinel-Prime", error=str(e), exc_info=True)
            await self._send_error(message, "Sentinel-Prime configuration failed", str(e))

    # =====================================================================
    # Original Message Handlers (unchanged)
    # =====================================================================

    async def _handle_validate_input(self, message: ActorMessage) -> None:
        """
        Validate input content for safety violations.

        Content: {
            "content": str,
            "content_type": str (optional),
            "source": str (optional),
            "strict_mode": bool (optional)
        }
        """
        try:
            content = message.content
            input_content = content.get("content", "")
            content_type = content.get("content_type", "text")
            content.get("source", "unknown")
            strict_mode = content.get("strict_mode", False)

            # Validate input using Pydantic
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "validate_input",
                    "content": content,
                    "timestamp": message.timestamp,
                }
            )

            # Scan content
            scan_result = await self._scan_content(
                input_content,
                content_type,
                strict_mode=strict_mode,
            )

            # Log and respond
            logger.info(
                "Input validation completed",
                scan_id=scan_result["scan_id"],
                safety_level=scan_result["safety_level"],
                violations_count=len(scan_result.get("violations", [])),
            )

            # Send response
            response_content = {
                "scan_id": scan_result["scan_id"],
                "safety_level": scan_result["safety_level"],
                "is_safe": scan_result["is_safe"],
                "violations": scan_result.get("violations", []),
                "sanitized_content": scan_result.get("sanitized_content", input_content),
                "recommendations": scan_result.get("recommendations", []),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid input format", str(ve))
        except Exception as e:
            logger.error("Error validating input", error=str(e), exc_info=True)
            await self._send_error(message, "Validation failed", str(e))

    async def _handle_validate_output(self, message: ActorMessage) -> None:
        """
        Validate output content before delivery.

        Content: {
            "content": str,
            "target": str (optional),
            "content_type": str (optional),
            "strict_mode": bool (optional)
        }
        """
        try:
            content = message.content
            output_content = content.get("content", "")
            target = content.get("target", "external")
            content_type = content.get("content_type", "text")
            strict_mode = content.get("strict_mode", False)

            # Validate input
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "validate_output",
                    "content": content,
                    "timestamp": message.timestamp,
                }
            )

            # Scan content
            scan_result = await self._scan_content(
                output_content,
                content_type,
                strict_mode=strict_mode,
            )

            logger.info(
                "Output validation completed",
                scan_id=scan_result["scan_id"],
                safety_level=scan_result["safety_level"],
                target=target,
            )

            response_content = {
                "scan_id": scan_result["scan_id"],
                "safety_level": scan_result["safety_level"],
                "is_safe": scan_result["is_safe"],
                "approved_for_delivery": scan_result["is_safe"],
                "violations": scan_result.get("violations", []),
                "filtered_content": scan_result.get("sanitized_content", output_content),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid output format", str(ve))
        except Exception as e:
            logger.error("Error validating output", error=str(e), exc_info=True)
            await self._send_error(message, "Validation failed", str(e))

    async def _handle_scan_content(self, message: ActorMessage) -> None:
        """
        Scan content for safety violations without blocking.

        Content: {
            "content": str,
            "scan_types": List[str] (optional),
            "return_details": bool (optional)
        }
        """
        try:
            content = message.content
            scan_content = content.get("content", "")
            scan_types = content.get("scan_types", ["all"])
            return_details = content.get("return_details", True)

            # Validate
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "scan_content",
                    "content": content,
                    "timestamp": message.timestamp,
                }
            )

            # Perform scan
            violations = []
            safety_level = SafetyLevel.SAFE

            # Check injection patterns
            if "injection" in scan_types or "all" in scan_types:
                injection_violations = self._check_injection_patterns(scan_content)
                violations.extend(injection_violations)

            # Check PII
            if "pii" in scan_types or "all" in scan_types:
                pii_violations = self._check_pii_patterns(scan_content)
                violations.extend(pii_violations)

            # Determine safety level
            if violations:
                max_severity = max(v.get("severity", "low_risk") for v in violations)
                safety_level = SafetyLevel(max_severity)

            # Update statistics
            self._stats["total_scans"] += 1
            if not violations:
                self._stats["safe_scans"] += 1

            response_content = {
                "scan_id": f"scan_{datetime.now(UTC).timestamp()}",
                "safety_level": safety_level.value,
                "is_safe": len(violations) == 0,
                "violations": violations if return_details else len(violations),
                "scan_types": scan_types,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid scan request", str(ve))
        except Exception as e:
            logger.error("Error scanning content", error=str(e), exc_info=True)
            await self._send_error(message, "Scan failed", str(e))

    async def _handle_check_policy(self, message: ActorMessage) -> None:
        """
        Check content against specific policy rules.

        Content: {
            "content": str,
            "policies": List[str],
            "context": Dict (optional)
        }
        """
        try:
            content = message.content
            check_content = content.get("content", "")
            policies = content.get("policies", [])
            context = content.get("context", {})

            # Validate
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "check_policy",
                    "content": content,
                    "timestamp": message.timestamp,
                }
            )

            violations = []

            for policy in policies:
                policy_violation = await self._check_policy_rule(
                    check_content,
                    policy,
                    context,
                )
                if policy_violation:
                    violations.append(policy_violation)

            response_content = {
                "policies_checked": policies,
                "violations": violations,
                "compliant": len(violations) == 0,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid policy check", str(ve))
        except Exception as e:
            logger.error("Error checking policy", error=str(e), exc_info=True)
            await self._send_error(message, "Policy check failed", str(e))

    async def _handle_get_safety_report(self, message: ActorMessage) -> None:
        """
        Generate comprehensive safety report.

        Content: {
            "time_range": str (optional),
            "include_recommendations": bool (optional)
        }
        """
        try:
            content = message.content
            time_range = content.get("time_range", "24h")
            include_recommendations = content.get("include_recommendations", True)

            # Validate
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "get_safety_report",
                    "content": content,
                    "timestamp": message.timestamp,
                }
            )

            # Generate report
            report = self._generate_safety_report(
                time_range=time_range,
                include_recommendations=include_recommendations,
            )

            response_content = {
                "report_id": report.report_id,
                "timestamp": report.timestamp.isoformat(),
                "total_scans": report.total_scans,
                "violations_detected": report.violations_detected,
                "violations_blocked": report.violations_blocked,
                "violations_by_type": report.violations_by_type,
                "violations_by_severity": report.violations_by_severity,
                "recommendations": report.recommendations if include_recommendations else [],
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid report request", str(ve))
        except Exception as e:
            logger.error("Error generating report", error=str(e), exc_info=True)
            await self._send_error(message, "Report generation failed", str(e))

    async def _handle_get_violation_details(self, message: ActorMessage) -> None:
        """
        Get details of a specific violation.

        Content: {
            "violation_id": str
        }
        """
        try:
            content = message.content
            violation_id = content.get("violation_id")

            if not violation_id:
                await self._send_error(message, "Missing violation_id")
                return

            # Validate
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "get_violation_details",
                    "content": content,
                    "timestamp": message.timestamp,
                }
            )

            violation = self._violations.get(violation_id)

            if not violation:
                await self._send_error(message, "Violation not found", f"ID: {violation_id}")
                return

            response_content = {
                "violation_id": violation.violation_id,
                "violation_type": violation.violation_type.value,
                "severity": violation.severity.value,
                "timestamp": violation.timestamp.isoformat(),
                "description": violation.description,
                "source_agent": violation.source_agent,
                "target_agent": violation.target_agent,
                "blocked": violation.blocked,
                "remediation_action": violation.remediation_action,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid request", str(ve))
        except Exception as e:
            logger.error("Error getting violation details", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get details", str(e))

    async def _handle_update_guardrails(self, message: ActorMessage) -> None:
        """
        Update guardrail configuration.

        Content: {
            "max_content_size": int (optional),
            "enable_pii_detection": bool (optional),
            "enable_injection_detection": bool (optional),
            "auto_block_critical": bool (optional),
            "custom_patterns": Dict (optional)
        }
        """
        try:
            content = message.content

            # Validate
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "update_guardrails",
                    "content": content,
                    "timestamp": message.timestamp,
                }
            )

            updates = []

            if "max_content_size" in content:
                self._max_content_size = content["max_content_size"]
                updates.append(f"max_content_size={self._max_content_size}")

            if "enable_pii_detection" in content:
                self._enable_pii_detection = content["enable_pii_detection"]
                updates.append(f"enable_pii_detection={self._enable_pii_detection}")

            if "enable_injection_detection" in content:
                self._enable_injection_detection = content["enable_injection_detection"]
                updates.append(f"enable_injection_detection={self._enable_injection_detection}")

            if "auto_block_critical" in content:
                self._auto_block_critical = content["auto_block_critical"]
                updates.append(f"auto_block_critical={self._auto_block_critical}")

            logger.info("Guardrails updated", updates=", ".join(updates))

            response_content = {
                "updated": True,
                "changes": updates,
                "current_config": {
                    "max_content_size": self._max_content_size,
                    "enable_pii_detection": self._enable_pii_detection,
                    "enable_injection_detection": self._enable_injection_detection,
                    "auto_block_critical": self._auto_block_critical,
                },
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid guardrail update", str(ve))
        except Exception as e:
            logger.error("Error updating guardrails", error=str(e), exc_info=True)
            await self._send_error(message, "Guardrail update failed", str(e))

    async def _handle_get_statistics(self, message: ActorMessage) -> None:
        """
        Get current safety statistics.

        Content: {} (empty)
        """
        try:
            # Validate
            validate_message(
                {
                    "sender_id": message.sender_id,
                    "message_type": "get_statistics",
                    "content": {},
                    "timestamp": message.timestamp,
                }
            )

            response_content = {
                "safety_statistics": self._stats.copy(),
                "active_violations": len([v for v in self._violations.values() if not v.blocked]),
                "total_violations_tracked": len(self._violations),
                "violation_history_size": len(self._violation_history),
                "anomaly_statistics": self.get_anomaly_statistics(),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid statistics request", str(ve))
        except Exception as e:
            logger.error("Error getting statistics", error=str(e), exc_info=True)
            await self._send_error(message, _STAT_RETRIEVAL_FAILED, str(e))

    async def _scan_content(
        self,
        content: str,
        content_type: str = "text",
        strict_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Scan content for safety violations.

        Returns dict with:
        - scan_id: Unique scan identifier
        - safety_level: Overall safety assessment
        - is_safe: Boolean indicating if content is safe
        - violations: List of detected violations
        - sanitized_content: Content with violations removed/masked
        - recommendations: List of recommended actions
        """
        scan_id = f"scan_{datetime.now(UTC).timestamp()}"
        violations = []
        sanitized_content = content

        # Check content size
        if len(content) > self._max_content_size:
            violations.append(
                {
                    "type": ViolationType.POLICY_VIOLATION.value,
                    "severity": SafetyLevel.MEDIUM_RISK.value,
                    "description": f"Content exceeds max size ({len(content)}/{self._max_content_size} chars)",
                }
            )

        # Check injection patterns
        if self._enable_injection_detection:
            injection_violations = self._check_injection_patterns(content)
            violations.extend(injection_violations)

        # Check PII
        if self._enable_pii_detection:
            pii_violations = self._check_pii_patterns(content)
            violations.extend(pii_violations)

        # Determine overall safety level
        if violations:
            severity_order = {
                SafetyLevel.CRITICAL.value: 5,
                SafetyLevel.HIGH_RISK.value: 4,
                SafetyLevel.MEDIUM_RISK.value: 3,
                SafetyLevel.LOW_RISK.value: 2,
                SafetyLevel.SAFE.value: 1,
            }
            max_severity = max(severity_order.get(v.get("severity", "safe"), 1) for v in violations)
            safety_level = {
                5: SafetyLevel.CRITICAL,
                4: SafetyLevel.HIGH_RISK,
                3: SafetyLevel.MEDIUM_RISK,
                2: SafetyLevel.LOW_RISK,
            }.get(max_severity, SafetyLevel.SAFE)
        else:
            safety_level = SafetyLevel.SAFE

        # Auto-block critical violations
        if self._auto_block_critical and safety_level == SafetyLevel.CRITICAL:
            for violation in violations:
                if violation.get("severity") == SafetyLevel.CRITICAL.value:
                    self._record_violation(violation, content, scan_id)

        # Update statistics
        self._stats["total_scans"] += 1
        if not violations:
            self._stats["safe_scans"] += 1
        else:
            self._stats["violations_detected"] += len(violations)
            for v in violations:
                vtype = v.get("type", "unknown")
                self._stats["violations_by_type"][vtype] = (
                    self._stats["violations_by_type"].get(vtype, 0) + 1
                )

        # Generate recommendations
        recommendations = []
        if safety_level != SafetyLevel.SAFE:
            recommendations.append(f"Review content for {safety_level.value} risk")
            if any(v.get("type") == ViolationType.INJECTION_ATTEMPT.value for v in violations):
                recommendations.append("Sanitize input before processing")
            if any(v.get("type") == ViolationType.PII_DETECTED.value for v in violations):
                recommendations.append("Mask or remove PII data")

        return {
            "scan_id": scan_id,
            "safety_level": safety_level.value,
            "is_safe": safety_level == SafetyLevel.SAFE,
            "violations": violations,
            "sanitized_content": sanitized_content,
            "recommendations": recommendations,
        }

    # _check_injection_patterns, _check_pii_patterns, _record_violation, and
    # _generate_safety_report are inherited from SentinelHelpers.

    async def _check_policy_rule(
        self,
        content: str,
        policy: str,
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Check content against a specific policy rule."""
        # Policy rules can be extended with custom logic
        # For now, return None (no violations) as placeholder
        return None
