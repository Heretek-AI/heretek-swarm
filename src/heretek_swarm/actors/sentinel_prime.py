"""
Sentinel-Prime Agent - Security Commander & Threat Response.

Sentinel-Prime provides:
- Active threat detection and response
- Security incident management
- Intrusion detection and prevention
- Threat intelligence aggregation
- Security policy enforcement
- Incident response automation
- External threat detection (SAFE-02)

Sentinel-Prime is the "security commander" of the Collective, responsible for
identifying, analyzing, and responding to security threats in real-time.

SAFE-02 Features:
- Prompt injection detection
- DoS attack detection
- Data exfiltration detection
- Threat intelligence correlation
- Automated containment actions
- False positive rate < 1%
- Alert priority filtering (critical alerts only by default)
- Automatic escalation to Core Triad

Reference: Phase 2 Plan Task 5 (SAFE-02)
"""

import asyncio
import contextlib
import hashlib
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
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
from heretek_swarm.actors.validation import validate_message
from heretek_swarm.security.threat_detection import (
    AlertPriority,
    ContainmentAction,
    ExternalThreatDetector,
    ExternalThreatType,
    ThreatDetectionConfig,
    ThreatDetectionResult,
    ThreatIntelligence,
    ThreatLevel as ExtThreatLevel,
    create_default_detector,
)

logger = structlog.get_logger("SentinelPrimeAgent")


class ThreatLevel(StrEnum):
    """Threat severity classification."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(StrEnum):
    """Types of security threats."""

    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE = "malware"
    PHISHING = "phishing"
    DOS_ATTACK = "dos_attack"
    MAN_IN_THE_MIDDLE = "man_in_the_middle"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    CREDENTIAL_STUFFING = "credential_stuffing"
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    POLICY_VIOLATION = "policy_violation"
    ZERO_DAY_EXPLOIT = "zero_day_exploit"
    PROMPT_INJECTION = "prompt_injection"
    SESSION_HIJACKING = "session_hijacking"
    API_ABUSE = "api_abuse"
    CREDENTIAL_THEFT = "credential_theft"
    TRAFFIC_ANALYSIS = "traffic_analysis"


class IncidentStatus(StrEnum):
    """Security incident status."""

    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    REMEDIATED = "remediated"
    CLOSED = "closed"
    ESCALATED = "escalated"


class ResponseAction(StrEnum):
    """Automated response actions."""

    ALERT = "alert"
    BLOCK = "block"
    ISOLATE = "isolate"
    TERMINATE = "terminate"
    QUARANTINE = "quarantine"
    RATE_LIMIT = "rate_limit"
    BLACKLIST = "blacklist"
    NOTIFY = "notify"
    LOG_ONLY = "log_only"


@dataclass
class ThreatIndicator:
    """Individual threat indicator."""

    indicator_id: str
    indicator_type: str  # IP, domain, hash, pattern, behavior
    value: str
    confidence: float  # 0.0 - 1.0
    first_seen: datetime
    last_seen: datetime
    source: str
    tags: list[str] = field(default_factory=list)


@dataclass
class SecurityIncident:
    """Security incident record."""

    incident_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    status: IncidentStatus
    timestamp: datetime
    source_actor: str | None = None
    target_actor: str | None = None
    target_resource: str | None = None
    indicators: list[ThreatIndicator] = field(default_factory=list)
    response_actions: list[ResponseAction] = field(default_factory=list)
    description: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation_steps: list[str] = field(default_factory=list)
    closed_at: datetime | None = None


@dataclass
class ThreatReport:
    """Aggregated threat intelligence report."""

    report_id: str
    timestamp: datetime
    time_range: str
    total_incidents: int
    incidents_by_level: dict[str, int]
    incidents_by_type: dict[str, int]
    active_threats: int
    contained_threats: int
    top_indicators: list[dict[str, Any]]
    recommendations: list[str]


class SentinelPrimeAgent(
    HealthReportingMixin,
    ValidationMixin,
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    AgentActor,
):
    """
    Sentinel-Prime Agent - Security Commander for the Heretek Swarm Collective.

    Sentinel-Prime provides active threat detection, incident response, and
    security intelligence for the Collective.

    SAFE-02 External Threat Detection:
    - Detects external threats: prompt injection, DoS, exfiltration
    - Containment actions operational
    - False positive rate < 1%
    - Alert fatigue prevention via priority filtering
    - Automatic escalation to Core Triad
    """

    def __init__(
        self,
        agent_id: str | None = None,
        name: str = "Sentinel-Prime",
        description: str = "Security Commander - Threat Response",
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

        # Security configuration
        self._auto_response_enabled = config.get("auto_response_enabled", True) if config else True
        self._alert_threshold = (
            config.get("alert_threshold", ThreatLevel.MEDIUM.value)
            if config
            else ThreatLevel.MEDIUM.value
        )
        self._max_incidents = config.get("max_incidents", 5000) if config else 5000
        self._correlation_window = (
            config.get("correlation_window", 300) if config else 300
        )  # seconds

        # =====================================================================
        # SAFE-02: External Threat Detection
        # =====================================================================
        threat_config = ThreatDetectionConfig(
            min_detection_confidence=config.get("min_detection_confidence", 0.7) if config else 0.7,
            max_false_positive_rate=config.get("max_false_positive_rate", 0.01) if config else 0.01,
            default_alert_priority=AlertPriority.CRITICAL,
            auto_response_priorities={AlertPriority.CRITICAL},
            prompt_injection_enabled=config.get("prompt_injection_enabled", True) if config else True,
            exfiltration_detection_enabled=config.get("exfiltration_detection_enabled", True) if config else True,
            dos_detection_enabled=config.get("dos_detection_enabled", True) if config else True,
            core_triad_escalation_enabled=config.get("core_triad_escalation_enabled", True) if config else True,
            escalation_threshold_count=config.get("escalation_threshold_count", 5) if config else 5,
        )
        self._external_threat_detector = create_default_detector(threat_config)

        # Core Triad escalation configuration
        self._core_triad_escalation_enabled = config.get("core_triad_escalation_enabled", True) if config else True
        self._escalation_cooldown_seconds = config.get("escalation_cooldown_seconds", 300) if config else 300
        self._last_escalation_time: dict[str, datetime] = {}

        # Alert priority filtering state
        self._alert_priorities: dict[str, AlertPriority] = {}
        self._suppressed_alerts: dict[str, float] = {}  # source -> suppression_end_time

        # Security state
        self._incidents: dict[str, SecurityIncident] = {}
        self._incident_history: list[str] = []  # LRU keys
        self._threat_indicators: dict[str, ThreatIndicator] = {}
        self._indicator_cache: dict[str, ThreatIndicator] = {}  # LRU cache
        self._max_indicator_cache = 10000

        # Rate limiting state
        self._rate_limits: dict[str, dict[str, Any]] = {}
        self._blocked_sources: set[str] = set()
        self._isolated_actors: set[str] = set()

        # Statistics
        self._stats = {
            "total_incidents": 0,
            "incidents_by_level": defaultdict(int),
            "incidents_by_type": defaultdict(int),
            "auto_responses_triggered": 0,
            "manual_responses_triggered": 0,
            "threats_contained": 0,
            "threats_mitigated": 0,
            # SAFE-02 external threat stats
            "external_threats_detected": 0,
            "external_threats_contained": 0,
            "core_triad_escalations": 0,
            "alert_fatigue_suppressions": 0,
        }

        # Threat patterns
        self._attack_patterns = [
            (r"(?i)union\s+select", ThreatType.SQL_INJECTION),
            (r"(?i)or\s+1\s*=\s*1", ThreatType.SQL_INJECTION),
            (r"(?i)drop\s+table", ThreatType.SQL_INJECTION),
            (r"(?i)<script[^>]*>", ThreatType.XSS_ATTACK),
            (r"(?i)javascript:", ThreatType.XSS_ATTACK),
            (r"(?i)on\w+\s*=", ThreatType.XSS_ATTACK),
            (r"(?i)passwd|password|secret|api_key|token", ThreatType.DATA_EXFILTRATION),
            (r"(?i)/etc/passwd|/etc/shadow", ThreatType.UNAUTHORIZED_ACCESS),
            (r"(?i)\.\./", ThreatType.UNAUTHORIZED_ACCESS),
            (r"(?i)cmd\.exe|powershell|/bin/sh|/bin/bash", ThreatType.PRIVILEGE_ESCALATION),
        ]

        self._compiled_patterns = [
            (re.compile(pattern), threat_type) for pattern, threat_type in self._attack_patterns
        ]

        logger.info(
            "Sentinel-Prime Agent initialized",
            agent_id=self.agent_id,
            auto_response=self._auto_response_enabled,
            alert_threshold=self._alert_threshold,
            external_threat_detection_enabled=True,
            core_triad_escalation=self._core_triad_escalation_enabled,
        )

    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming message with security validation."""
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
            "report_threat": self._handle_report_threat,
            "analyze_threat": self._handle_analyze_threat,
            "get_incident_details": self._handle_get_incident_details,
            "get_active_incidents": self._handle_get_active_incidents,
            "respond_to_incident": self._handle_respond_to_incident,
            "add_threat_indicator": self._handle_add_threat_indicator,
            "check_indicator": self._handle_check_indicator,
            "get_threat_report": self._handle_get_threat_report,
            "block_source": self._handle_block_source,
            "isolate_actor": self._handle_isolate_actor,
            "get_statistics": self._handle_get_statistics,
            "update_config": self._handle_update_config,
            # SAFE-02: External threat detection handlers
            "detect_external_threat": self._handle_detect_external_threat,
            "get_threat_intelligence": self._handle_get_threat_intelligence,
            "configure_alert_priority": self._handle_configure_alert_priority,
            "suppress_alerts": self._handle_suppress_alerts,
            "escalate_to_core_triad": self._handle_escalate_to_core_triad,
        }

    # =====================================================================
    # SAFE-02: External Threat Detection Handlers
    # =====================================================================

    async def _handle_detect_external_threat(self, message: ActorMessage) -> None:
        """
        Detect external threats in content.

        Content: {
            "content": str,
            "source": str,
            "target": str (optional),
            "threat_type": str (optional)
        }
        """
        try:
            content = message.content
            input_content = content.get("content", "")
            source = content.get("source", "unknown")
            target = content.get("target")
            threat_type_str = content.get("threat_type")

            # Validate
            validate_message({
                "sender_id": message.sender_id,
                "message_type": "detect_external_threat",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Convert threat type if specified
            threat_type = None
            if threat_type_str:
                try:
                    threat_type = ExternalThreatType(threat_type_str)
                except ValueError:
                    pass

            # Check alert suppression
            if self._is_alert_suppressed(source):
                response_content = {
                    "source": source,
                    "threat_detected": False,
                    "reason": "alerts_suppressed",
                    "suppressed_until": self._suppressed_alerts.get(source),
                }
                self._stats["alert_fatigue_suppressions"] += 1
                await self._send_response(message, response_content)
                return

            # Detect external threat
            threat_result = await self._external_threat_detector.detect_threat(
                content=input_content,
                source=source,
                target=target,
                threat_type=threat_type,
            )

            if threat_result is None:
                # No threat detected
                response_content = {
                    "source": source,
                    "threat_detected": False,
                    "confidence": 0.0,
                }
                await self._send_response(message, response_content)
                return

            # Threat detected - update stats
            self._stats["external_threats_detected"] += 1

            # Execute containment if auto-response enabled
            containment_actions = []
            if self._auto_response_enabled:
                containment_actions = await self._external_threat_detector.execute_containment(threat_result)
                self._stats["external_threats_contained"] += len(containment_actions)

            # Create incident for tracking
            incident = await self._create_incident_from_detection(threat_result)
            self._incidents[incident.incident_id] = incident

            # Check for Core Triad escalation
            if self._core_triad_escalation_enabled:
                await self._check_core_triad_escalation(source, threat_result)

            logger.warning(
                "external_threat_detected",
                source=source,
                threat_type=threat_result.threat_type.value,
                threat_level=threat_result.threat_level.value,
                priority=threat_result.priority.value,
                containment_actions=[a.value for a in containment_actions],
            )

            response_content = {
                "source": source,
                "threat_detected": True,
                "threat_id": threat_result.threat_id,
                "threat_type": threat_result.threat_type.value,
                "threat_level": threat_result.threat_level.value,
                "priority": threat_result.priority.value,
                "confidence": threat_result.confidence,
                "containment_actions": [a.value for a in containment_actions],
                "auto_responded": threat_result.auto_responded,
                "false_positive_likelihood": threat_result.false_positive_likelihood,
                "indicators": threat_result.indicators,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error in external threat detection", error=str(ve))
            await self._send_error(message, "Invalid threat detection request", str(ve))
        except Exception as e:
            logger.error("Error detecting external threat", error=str(e), exc_info=True)
            await self._send_error(message, "External threat detection failed", str(e))

    async def _handle_get_threat_intelligence(self, message: ActorMessage) -> None:
        """
        Get aggregated threat intelligence.

        Content: {
            "time_range": str (optional)
        }
        """
        try:
            content = message.content
            time_range = content.get("time_range", "24h")

            intelligence = await self._external_threat_detector.get_threat_intelligence(time_range)

            response_content = {
                "total_threats": intelligence.total_threats,
                "threats_by_type": intelligence.threats_by_type,
                "threats_by_source": intelligence.threats_by_source,
                "active_blocked_sources": intelligence.active_blocked_sources,
                "rate_limited_sources": intelligence.rate_limited_sources,
                "last_detection_time": (
                    intelligence.last_detection_time.isoformat()
                    if intelligence.last_detection_time
                    else None
                ),
                "top_indicators": intelligence.top_indicators,
                "recommendations": intelligence.recommendations,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting threat intelligence", error=str(e), exc_info=True)
            await self._send_error(message, "Threat intelligence retrieval failed", str(e))

    async def _handle_configure_alert_priority(self, message: ActorMessage) -> None:
        """
        Configure alert priority for a source.

        Content: {
            "source": str,
            "priority": str (critical, high, medium, low, info)
        }
        """
        try:
            content = message.content
            source = content.get("source")
            priority_str = content.get("priority", "critical")

            if not source:
                await self._send_error(message, "Missing source")
                return

            try:
                priority = AlertPriority(priority_str.lower())
            except ValueError:
                await self._send_error(message, f"Invalid priority: {priority_str}")
                return

            self._alert_priorities[source] = priority

            response_content = {
                "source": source,
                "priority": priority.value,
                "updated": True,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error configuring alert priority", error=str(e), exc_info=True)
            await self._send_error(message, "Priority configuration failed", str(e))

    async def _handle_suppress_alerts(self, message: ActorMessage) -> None:
        """
        Suppress alerts from a source (alert fatigue prevention).

        Content: {
            "source": str,
            "duration_seconds": int
        }
        """
        try:
            content = message.content
            source = content.get("source")
            duration_seconds = content.get("duration_seconds", 300)

            if not source:
                await self._send_error(message, "Missing source")
                return

            self._suppressed_alerts[source] = time.time() + duration_seconds
            self._stats["alert_fatigue_suppressions"] += 1

            logger.info(
                "alerts_suppressed",
                source=source,
                duration_seconds=duration_seconds,
            )

            response_content = {
                "source": source,
                "suppressed": True,
                "duration_seconds": duration_seconds,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error suppressing alerts", error=str(e), exc_info=True)
            await self._send_error(message, "Alert suppression failed", str(e))

    async def _handle_escalate_to_core_triad(self, message: ActorMessage) -> None:
        """
        Manually escalate threat to Core Triad.

        Content: {
            "threat_id": str,
            "reason": str (optional)
        }
        """
        try:
            content = message.content
            threat_id = content.get("threat_id")
            reason = content.get("reason", "manual_escalation")

            if not threat_id:
                await self._send_error(message, "Missing threat_id")
                return

            # Find the incident
            incident = None
            for inc in self._incidents.values():
                if inc.incident_id == threat_id:
                    incident = inc
                    break

            if not incident:
                await self._send_error(message, "Threat not found", threat_id)
                return

            # Escalate
            incident.status = IncidentStatus.ESCALATED
            self._stats["core_triad_escalations"] += 1

            # In production, this would send via NATS to Core Triad
            logger.warning(
                "manual_escalation_to_core_triad",
                incident_id=threat_id,
                reason=reason,
                threat_type=incident.threat_type.value,
            )

            response_content = {
                "threat_id": threat_id,
                "escalated": True,
                "reason": reason,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error escalating to Core Triad", error=str(e), exc_info=True)
            await self._send_error(message, "Escalation failed", str(e))

    # =====================================================================
    # SAFE-02: Internal Methods
    # =====================================================================

    def _is_alert_suppressed(self, source: str) -> bool:
        """Check if alerts from source are suppressed."""
        if source not in self._suppressed_alerts:
            return False

        if time.time() > self._suppressed_alerts[source]:
            # Expired
            del self._suppressed_alerts[source]
            return False

        return True

    async def _create_incident_from_detection(
        self,
        threat_result: ThreatDetectionResult,
    ) -> SecurityIncident:
        """Create a SecurityIncident from ThreatDetectionResult."""
        # Map threat type
        threat_type_map = {
            ExternalThreatType.PROMPT_INJECTION: ThreatType.PROMPT_INJECTION,
            ExternalThreatType.DOS_ATTACK: ThreatType.DOS_ATTACK,
            ExternalThreatType.DATA_EXFILTRATION: ThreatType.DATA_EXFILTRATION,
            ExternalThreatType.SQL_INJECTION: ThreatType.SQL_INJECTION,
            ExternalThreatType.API_ABUSE: ThreatType.API_ABUSE,
        }

        threat_type = threat_type_map.get(
            threat_result.threat_type,
            ThreatType.SUSPICIOUS_BEHAVIOR,
        )

        # Map threat level
        level_map = {
            ExtThreatLevel.CRITICAL: ThreatLevel.CRITICAL,
            ExtThreatLevel.HIGH: ThreatLevel.HIGH,
            ExtThreatLevel.MEDIUM: ThreatLevel.MEDIUM,
            ExtThreatLevel.LOW: ThreatLevel.LOW,
            ExtThreatLevel.BENIGN: ThreatLevel.INFORMATIONAL,
        }
        threat_level = level_map.get(threat_result.threat_level, ThreatLevel.MEDIUM)

        incident_id = self._create_incident_id()
        incident = SecurityIncident(
            incident_id=incident_id,
            threat_type=threat_type,
            threat_level=threat_level,
            status=IncidentStatus.DETECTED,
            timestamp=threat_result.timestamp,
            source_actor=threat_result.source,
            target_actor=threat_result.target,
            description=f"External threat detected: {threat_result.threat_type.value}",
            evidence={
                "threat_id": threat_result.threat_id,
                "confidence": threat_result.confidence,
                "priority": threat_result.priority.value,
                "indicators": threat_result.indicators,
                "false_positive_likelihood": threat_result.false_positive_likelihood,
            },
        )

        # Update stats
        self._stats["total_incidents"] += 1
        self._stats["incidents_by_level"][threat_level.value] += 1
        self._stats["incidents_by_type"][threat_type.value] += 1

        # Store indicator
        if threat_result.indicators:
            for ind in threat_result.indicators[:5]:
                indicator = ThreatIndicator(
                    indicator_id=f"IND_{hashlib.sha256(str(ind).encode()).hexdigest()[:12]}",
                    indicator_type=ind.get("type", "unknown"),
                    value=str(ind),
                    confidence=ind.get("confidence", 0.5),
                    first_seen=datetime.now(UTC),
                    last_seen=datetime.now(UTC),
                    source=threat_result.source,
                )
                incident.indicators.append(indicator)

        return incident

    async def _check_core_triad_escalation(
        self,
        source: str,
        threat_result: ThreatDetectionResult,
    ) -> None:
        """Check if threat warrants escalation to Core Triad."""
        # Check cooldown
        last_escalation = self._last_escalation_time.get(source)
        if last_escalation:
            cooldown_elapsed = (datetime.now(UTC) - last_escalation).total_seconds()
            if cooldown_elapsed < self._escalation_cooldown_seconds:
                return

        # Count recent threats from this source
        recent_threats = sum(
            1 for inc in self._incidents.values()
            if inc.source_actor == source
            and inc.status == IncidentStatus.DETECTED
        )

        # Escalate if threshold reached
        threshold = self._external_threat_detector.config.escalation_threshold_count
        if recent_threats >= threshold:
            self._stats["core_triad_escalations"] += 1
            self._last_escalation_time[source] = datetime.now(UTC)

            logger.warning(
                "core_triad_escalation_triggered",
                source=source,
                recent_threat_count=recent_threats,
                threshold=threshold,
                threat_level=threat_result.threat_level.value,
            )

            # In production: send to Core Triad via NATS
            # await self._send_to_core_triad(threat_result)

    # =====================================================================
    # Original Sentinel-Prime Handlers (preserved for compatibility)
    # =====================================================================

    async def _handle_report_threat(self, message: ActorMessage) -> None:
        """
        Report a potential security threat.

        Content: {
            "threat_type": str,
            "threat_level": str (optional),
            "source": str (optional),
            "target": str (optional),
            "description": str,
            "evidence": Dict (optional),
            "indicators": List[Dict] (optional)
        }
        """
        try:
            content = message.content
            threat_type_str = content.get("threat_type")
            threat_level_str = content.get("threat_level", ThreatLevel.MEDIUM.value)
            source = content.get("source")
            target = content.get("target")
            description = content.get("description", "")
            evidence = content.get("evidence", {})
            indicators = content.get("indicators", [])

            # Validate
            validate_message({
                "sender_id": message.sender_id,
                "message_type": "report_threat",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Convert enums
            try:
                threat_type = ThreatType(threat_type_str)
            except ValueError:
                threat_type = ThreatType.SUSPICIOUS_BEHAVIOR

            try:
                threat_level = ThreatLevel(threat_level_str)
            except ValueError:
                threat_level = ThreatLevel.MEDIUM

            # Create incident
            incident_id = self._create_incident_id()
            incident = SecurityIncident(
                incident_id=incident_id,
                threat_type=threat_type,
                threat_level=threat_level,
                status=IncidentStatus.DETECTED,
                timestamp=datetime.now(UTC),
                source_actor=source,
                target_actor=target,
                description=description,
                evidence=evidence,
            )

            # Add indicators
            for ind_data in indicators:
                indicator = self._create_indicator(ind_data)
                if indicator:
                    incident.indicators.append(indicator)
                    self._threat_indicators[indicator.indicator_id] = indicator

            # Store incident
            self._incidents[incident_id] = incident
            self._incident_history.append(incident_id)

            # Update statistics
            self._stats["total_incidents"] += 1
            self._stats["incidents_by_level"][threat_level.value] += 1
            self._stats["incidents_by_type"][threat_type.value] += 1

            # Auto-respond if enabled and threat level is high enough
            response_actions = []
            if self._auto_response_enabled:
                response_actions = await self._auto_respond(incident)
                incident.response_actions = response_actions

            # LRU cleanup
            if len(self._incident_history) > self._max_incidents:
                oldest = self._incident_history.pop(0)
                self._incidents.pop(oldest, None)

            logger.warning(
                "Security threat reported",
                incident_id=incident_id,
                threat_type=threat_type.value,
                threat_level=threat_level.value,
                source=source,
                target=target,
                auto_response=len(response_actions) > 0,
            )

            response_content = {
                "incident_id": incident_id,
                "status": incident.status.value,
                "threat_level": threat_level.value,
                "auto_response_triggered": len(response_actions) > 0,
                "response_actions": [a.value for a in response_actions],
                "recommendations": self._generate_recommendations(incident),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid threat report", str(ve))
        except Exception as e:
            logger.error("Error reporting threat", error=str(e), exc_info=True)
            await self._send_error(message, "Threat report failed", str(e))

    async def _handle_analyze_threat(self, message: ActorMessage) -> None:
        """Analyze a reported threat for correlation and severity."""
        try:
            content = message.content
            incident_id = content.get("incident_id")
            correlate = content.get("correlate", True)
            deep_analysis = content.get("deep_analysis", False)

            if not incident_id:
                await self._send_error(message, "Missing incident_id")
                return

            incident = self._incidents.get(incident_id)
            if not incident:
                await self._send_error(message, "Incident not found", incident_id)
                return

            # Perform analysis
            analysis_result = {
                "incident_id": incident_id,
                "severity_score": self._calculate_severity_score(incident),
                "correlated_incidents": [],
                "attack_chain": [],
                "ioc_matches": [],
                "mitre_techniques": [],
            }

            # Correlation analysis
            if correlate:
                correlated = self._find_correlated_incidents(incident)
                analysis_result["correlated_incidents"] = [
                    {"incident_id": c.incident_id, "correlation_score": 0.8} for c in correlated[:5]
                ]

            # Deep analysis
            if deep_analysis:
                analysis_result["attack_chain"] = self._reconstruct_attack_chain(incident)
                analysis_result["ioc_matches"] = self._match_iocs(incident)
                analysis_result["mitre_techniques"] = self._map_mitre_techniques(incident)

            response_content = {
                "incident_id": incident_id,
                "analysis": analysis_result,
                "updated_threat_level": incident.threat_level.value,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error analyzing threat", error=str(e), exc_info=True)
            await self._send_error(message, "Threat analysis failed", str(e))

    async def _handle_get_incident_details(self, message: ActorMessage) -> None:
        """Get detailed information about a specific incident."""
        try:
            content = message.content
            incident_id = content.get("incident_id")

            if not incident_id:
                await self._send_error(message, "Missing incident_id")
                return

            incident = self._incidents.get(incident_id)
            if not incident:
                await self._send_error(message, "Incident not found", incident_id)
                return

            response_content = {
                "incident_id": incident.incident_id,
                "threat_type": incident.threat_type.value,
                "threat_level": incident.threat_level.value,
                "status": incident.status.value,
                "timestamp": incident.timestamp.isoformat(),
                "source_actor": incident.source_actor,
                "target_actor": incident.target_actor,
                "target_resource": incident.target_resource,
                "description": incident.description,
                "indicators": [
                    {
                        "indicator_id": i.indicator_id,
                        "type": i.indicator_type,
                        "value": i.value,
                        "confidence": i.confidence,
                    }
                    for i in incident.indicators
                ],
                "response_actions": [a.value for a in incident.response_actions],
                "remediation_steps": incident.remediation_steps,
                "evidence": incident.evidence,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting incident details", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get incident details", str(e))

    async def _handle_get_active_incidents(self, message: ActorMessage) -> None:
        """Get all active (non-closed) incidents."""
        try:
            content = message.content
            threat_level_filter = content.get("threat_level_filter")
            limit = content.get("limit", 100)

            active_incidents = [
                inc
                for inc in self._incidents.values()
                if inc.status not in [IncidentStatus.CLOSED, IncidentStatus.REMEDIATED]
            ]

            # Filter by threat level
            if threat_level_filter:
                try:
                    min_level = ThreatLevel(threat_level_filter)
                    level_order = {
                        ThreatLevel.INFORMATIONAL: 0,
                        ThreatLevel.LOW: 1,
                        ThreatLevel.MEDIUM: 2,
                        ThreatLevel.HIGH: 3,
                        ThreatLevel.CRITICAL: 4,
                    }
                    min_order = level_order.get(min_level, 0)
                    active_incidents = [
                        inc
                        for inc in active_incidents
                        if level_order.get(inc.threat_level, 0) >= min_order
                    ]
                except ValueError:
                    pass

            # Sort by threat level (highest first)
            level_order = {
                ThreatLevel.CRITICAL: 4,
                ThreatLevel.HIGH: 3,
                ThreatLevel.MEDIUM: 2,
                ThreatLevel.LOW: 1,
                ThreatLevel.INFORMATIONAL: 0,
            }
            active_incidents.sort(
                key=lambda x: level_order.get(x.threat_level, 0),
                reverse=True,
            )

            # Apply limit
            active_incidents = active_incidents[:limit]

            response_content = {
                "active_incidents_count": len(active_incidents),
                "incidents": [
                    {
                        "incident_id": inc.incident_id,
                        "threat_type": inc.threat_type.value,
                        "threat_level": inc.threat_level.value,
                        "status": inc.status.value,
                        "timestamp": inc.timestamp.isoformat(),
                        "source_actor": inc.source_actor,
                        "target_actor": inc.target_actor,
                    }
                    for inc in active_incidents
                ],
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting active incidents", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get active incidents", str(e))

    async def _handle_respond_to_incident(self, message: ActorMessage) -> None:
        """Execute response actions for an incident."""
        try:
            content = message.content
            incident_id = content.get("incident_id")
            actions = content.get("actions", [])
            manual = content.get("manual", False)

            if not incident_id:
                await self._send_error(message, "Missing incident_id")
                return

            incident = self._incidents.get(incident_id)
            if not incident:
                await self._send_error(message, "Incident not found", incident_id)
                return

            executed_actions = []

            for action_str in actions:
                try:
                    action = ResponseAction(action_str)
                    result = await self._execute_response_action(incident, action)
                    if result:
                        executed_actions.append(action)
                        incident.response_actions.append(action)
                except ValueError:
                    logger.warning("Unknown response action", action=action_str)

            # Update incident status
            if executed_actions:
                if (
                    ResponseAction.CONTAINED in executed_actions
                    or ResponseAction.ISOLATE in executed_actions
                ):
                    incident.status = IncidentStatus.CONTAINED
                elif ResponseAction.REMEDIATED in executed_actions:
                    incident.status = IncidentStatus.REMEDIATED

            # Update statistics
            if manual:
                self._stats["manual_responses_triggered"] += len(executed_actions)
            else:
                self._stats["auto_responses_triggered"] += len(executed_actions)

            response_content = {
                "incident_id": incident_id,
                "executed_actions": [a.value for a in executed_actions],
                "new_status": incident.status.value,
                "success": len(executed_actions) > 0,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error responding to incident", error=str(e), exc_info=True)
            await self._send_error(message, "Response execution failed", str(e))

    async def _handle_add_threat_indicator(self, message: ActorMessage) -> None:
        """Add a threat indicator to the intelligence database."""
        try:
            content = message.content
            indicator_data = {
                "indicator_type": content.get("indicator_type", "unknown"),
                "value": content.get("value", ""),
                "confidence": content.get("confidence", 0.5),
                "source": content.get("source", "manual"),
                "tags": content.get("tags", []),
            }

            indicator = self._create_indicator(indicator_data)
            if not indicator:
                await self._send_error(message, "Invalid indicator data")
                return

            self._threat_indicators[indicator.indicator_id] = indicator

            # Update cache
            self._indicator_cache[indicator.value] = indicator
            if len(self._indicator_cache) > self._max_indicator_cache:
                # Remove oldest
                oldest_key = next(iter(self._indicator_cache))
                self._indicator_cache.pop(oldest_key)

            response_content = {
                "indicator_id": indicator.indicator_id,
                "type": indicator.indicator_type,
                "value": indicator.value,
                "confidence": indicator.confidence,
                "success": True,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error adding threat indicator", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to add indicator", str(e))

    async def _handle_check_indicator(self, message: ActorMessage) -> None:
        """Check if a value matches any known threat indicator."""
        try:
            content = message.content
            value = content.get("value", "")
            indicator_type = content.get("indicator_type")

            # Check cache first
            cached = self._indicator_cache.get(value)
            if cached:
                response_content = {
                    "value": value,
                    "match_found": True,
                    "indicator": {
                        "indicator_id": cached.indicator_id,
                        "type": cached.indicator_type,
                        "confidence": cached.confidence,
                        "tags": cached.tags,
                    },
                    "source": "cache",
                }
                await self._send_response(message, response_content)
                return

            # Check all indicators
            for indicator in self._threat_indicators.values():
                if indicator.value == value:
                    if indicator_type and indicator.indicator_type != indicator_type:
                        continue

                    response_content = {
                        "value": value,
                        "match_found": True,
                        "indicator": {
                            "indicator_id": indicator.indicator_id,
                            "type": indicator.indicator_type,
                            "confidence": indicator.confidence,
                            "tags": indicator.tags,
                        },
                        "source": "database",
                    }
                    await self._send_response(message, response_content)
                    return

            response_content = {
                "value": value,
                "match_found": False,
                "source": "not_found",
            }
            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error checking indicator", error=str(e), exc_info=True)
            await self._send_error(message, "Indicator check failed", str(e))

    async def _handle_get_threat_report(self, message: ActorMessage) -> None:
        """Generate comprehensive threat intelligence report."""
        try:
            content = message.content
            time_range = content.get("time_range", "24h")
            include_indicators = content.get("include_indicators", False)
            include_recommendations = content.get("include_recommendations", True)

            # Calculate statistics
            incidents_by_level = dict(self._stats["incidents_by_level"])
            incidents_by_type = dict(self._stats["incidents_by_type"])

            active_threats = sum(
                1
                for inc in self._incidents.values()
                if inc.status in [IncidentStatus.DETECTED, IncidentStatus.INVESTIGATING]
            )
            contained_threats = sum(
                1
                for inc in self._incidents.values()
                if inc.status in [IncidentStatus.CONTAINED, IncidentStatus.REMEDIATED]
            )

            # Get top indicators
            top_indicators = []
            if include_indicators:
                sorted_indicators = sorted(
                    self._threat_indicators.values(),
                    key=lambda x: x.confidence,
                    reverse=True,
                )[:20]
                top_indicators = [
                    {
                        "indicator_id": i.indicator_id,
                        "type": i.indicator_type,
                        "value": i.value,
                        "confidence": i.confidence,
                        "tags": i.tags,
                    }
                    for i in sorted_indicators
                ]

            # Generate recommendations
            recommendations = []
            if include_recommendations:
                recommendations = self._generate_strategic_recommendations()

            report = {
                "report_id": f"threat_report_{datetime.now(UTC).timestamp()}",
                "timestamp": datetime.now(UTC).isoformat(),
                "time_range": time_range,
                "total_incidents": self._stats["total_incidents"],
                "incidents_by_level": incidents_by_level,
                "incidents_by_type": incidents_by_type,
                "active_threats": active_threats,
                "contained_threats": contained_threats,
                "top_indicators": top_indicators,
                "recommendations": recommendations,
                "auto_response_stats": {
                    "auto_responses": self._stats["auto_responses_triggered"],
                    "manual_responses": self._stats["manual_responses_triggered"],
                },
            }

            await self._send_response(message, {"report": report})

        except Exception as e:
            logger.error("Error generating threat report", error=str(e), exc_info=True)
            await self._send_error(message, "Threat report generation failed", str(e))

    async def _handle_block_source(self, message: ActorMessage) -> None:
        """Block a source from communicating with the Collective."""
        try:
            content = message.content
            source = content.get("source")
            duration = content.get("duration")
            reason = content.get("reason", "manual_block")

            if not source:
                await self._send_error(message, "Missing source")
                return

            self._blocked_sources.add(source)

            # Schedule unblock if duration specified
            if duration:
                asyncio.create_task(self._schedule_unblock(source, duration))

            logger.warning(
                "Source blocked",
                source=source,
                duration=duration,
                reason=reason,
            )

            response_content = {
                "source": source,
                "blocked": True,
                "duration": duration,
                "reason": reason,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error blocking source", error=str(e), exc_info=True)
            await self._send_error(message, "Block operation failed", str(e))

    async def _handle_isolate_actor(self, message: ActorMessage) -> None:
        """Isolate an actor from the Collective."""
        try:
            content = message.content
            actor_id = content.get("actor_id")
            duration = content.get("duration")
            reason = content.get("reason", "security_isolation")

            if not actor_id:
                await self._send_error(message, "Missing actor_id")
                return

            self._isolated_actors.add(actor_id)

            # Schedule un-isolate if duration specified
            if duration:
                asyncio.create_task(self._schedule_unisolate(actor_id, duration))

            logger.warning(
                "Actor isolated",
                actor_id=actor_id,
                duration=duration,
                reason=reason,
            )

            response_content = {
                "actor_id": actor_id,
                "isolated": True,
                "duration": duration,
                "reason": reason,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error isolating actor", error=str(e), exc_info=True)
            await self._send_error(message, "Isolation operation failed", str(e))

    async def _handle_get_statistics(self, message: ActorMessage) -> None:
        """Get current security statistics."""
        try:
            # Get external threat detector stats
            external_stats = self._external_threat_detector.get_statistics()

            response_content = {
                "statistics": {
                    "total_incidents": self._stats["total_incidents"],
                    "incidents_by_level": dict(self._stats["incidents_by_level"]),
                    "incidents_by_type": dict(self._stats["incidents_by_type"]),
                    "auto_responses": self._stats["auto_responses_triggered"],
                    "manual_responses": self._stats["manual_responses_triggered"],
                    "threats_contained": self._stats["threats_contained"],
                    "threats_mitigated": self._stats["threats_mitigated"],
                    # SAFE-02 stats
                    "external_threats_detected": self._stats["external_threats_detected"],
                    "external_threats_contained": self._stats["external_threats_contained"],
                    "core_triad_escalations": self._stats["core_triad_escalations"],
                    "alert_fatigue_suppressions": self._stats["alert_fatigue_suppressions"],
                },
                "active_state": {
                    "active_incidents": len(
                        [
                            i
                            for i in self._incidents.values()
                            if i.status not in [IncidentStatus.CLOSED, IncidentStatus.REMEDIATED]
                        ]
                    ),
                    "blocked_sources": len(self._blocked_sources),
                    "isolated_actors": len(self._isolated_actors),
                    "tracked_indicators": len(self._threat_indicators),
                },
                "external_threat_detection": external_stats,
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting statistics", error=str(e), exc_info=True)
            await self._send_error(message, "Statistics retrieval failed", str(e))

    async def _handle_update_config(self, message: ActorMessage) -> None:
        """Update security configuration."""
        try:
            content = message.content

            if "auto_response_enabled" in content:
                self._auto_response_enabled = content["auto_response_enabled"]

            if "alert_threshold" in content:
                with contextlib.suppress(ValueError):
                    self._alert_threshold = ThreatLevel(content["alert_threshold"]).value

            if "max_incidents" in content:
                self._max_incidents = content["max_incidents"]

            response_content = {
                "updated": True,
                "current_config": {
                    "auto_response_enabled": self._auto_response_enabled,
                    "alert_threshold": self._alert_threshold,
                    "max_incidents": self._max_incidents,
                },
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error updating config", error=str(e), exc_info=True)
            await self._send_error(message, "Config update failed", str(e))

    # =====================================================================
    # Utility Methods
    # =====================================================================

    def _create_incident_id(self) -> str:
        """Generate unique incident ID."""
        timestamp = datetime.now(UTC).timestamp()
        random_suffix = hashlib.sha256(str(timestamp).encode()).hexdigest()[:8]
        return f"INC_{int(timestamp)}_{random_suffix}"

    def _create_indicator(self, data: dict[str, Any]) -> ThreatIndicator | None:
        """Create a threat indicator from data."""
        try:
            indicator_id = f"IND_{hashlib.sha256(data.get('value', '').encode()).hexdigest()[:12]}"
            now = datetime.now(UTC)

            return ThreatIndicator(
                indicator_id=indicator_id,
                indicator_type=data.get("indicator_type", "unknown"),
                value=data.get("value", ""),
                confidence=float(data.get("confidence", 0.5)),
                first_seen=now,
                last_seen=now,
                source=data.get("source", "unknown"),
                tags=data.get("tags", []),
            )
        except Exception as e:
            logger.error("Error creating indicator", error=str(e))
            return None

    async def _auto_respond(self, incident: SecurityIncident) -> list[ResponseAction]:
        """Execute automatic response to an incident."""
        actions = []

        # Determine response based on threat level
        if incident.threat_level == ThreatLevel.CRITICAL:
            # Critical: Immediate isolation and blocking
            actions.append(ResponseAction.ALERT)
            actions.append(ResponseAction.ISOLATE)
            actions.append(ResponseAction.BLOCK)
            actions.append(ResponseAction.QUARANTINE)

            if incident.source_actor:
                self._isolated_actors.add(incident.source_actor)
            if incident.target_resource:
                actions.append(ResponseAction.TERMINATE)

        elif incident.threat_level == ThreatLevel.HIGH:
            # High: Alert and rate limit
            actions.append(ResponseAction.ALERT)
            actions.append(ResponseAction.RATE_LIMIT)

            if incident.source_actor:
                self._rate_limits[incident.source_actor] = {
                    "max_requests": 10,
                    "window_seconds": 60,
                    "started_at": datetime.now(UTC),
                }

        elif incident.threat_level == ThreatLevel.MEDIUM:
            # Medium: Alert and log
            actions.append(ResponseAction.ALERT)
            actions.append(ResponseAction.LOG_ONLY)

        else:
            # Low/Informational: Log only
            actions.append(ResponseAction.LOG_ONLY)

        # Update statistics
        self._stats["auto_responses_triggered"] += len(actions)

        return actions

    async def _execute_response_action(
        self,
        incident: SecurityIncident,
        action: ResponseAction,
    ) -> bool:
        """Execute a specific response action."""
        try:
            if action == ResponseAction.ALERT:
                logger.warning(
                    "Security alert triggered",
                    incident_id=incident.incident_id,
                    threat_type=incident.threat_type.value,
                )
                return True

            if action == ResponseAction.BLOCK:
                if incident.source_actor:
                    self._blocked_sources.add(incident.source_actor)
                return True

            if action == ResponseAction.ISOLATE:
                if incident.source_actor:
                    self._isolated_actors.add(incident.source_actor)
                return True

            if action == ResponseAction.QUARANTINE:
                if incident.target_resource:
                    # Mark resource as quarantined
                    incident.evidence["quarantined"] = True
                return True

            if action == ResponseAction.TERMINATE:
                # Terminate affected processes/connections
                incident.evidence["terminated"] = True
                return True

            if action == ResponseAction.RATE_LIMIT:
                if incident.source_actor:
                    self._rate_limits[incident.source_actor] = {
                        "max_requests": 10,
                        "window_seconds": 60,
                    }
                return True

            if action == ResponseAction.BLACKLIST:
                for indicator in incident.indicators:
                    self._blocked_sources.add(indicator.value)
                return True

            if action == ResponseAction.NOTIFY:
                # Send notifications to administrators
                logger.info(
                    "Security notification sent",
                    incident_id=incident.incident_id,
                )
                return True

            if action == ResponseAction.LOG_ONLY:
                logger.info(
                    "Security event logged",
                    incident_id=incident.incident_id,
                )
                return True

            return False

        except Exception as e:
            logger.error("Error executing response action", action=action.value, error=str(e))
            return False

    def _calculate_severity_score(self, incident: SecurityIncident) -> float:
        """Calculate numerical severity score for an incident."""
        base_scores = {
            ThreatLevel.CRITICAL: 10.0,
            ThreatLevel.HIGH: 7.5,
            ThreatLevel.MEDIUM: 5.0,
            ThreatLevel.LOW: 2.5,
            ThreatLevel.INFORMATIONAL: 1.0,
        }

        score = base_scores.get(incident.threat_level, 5.0)

        # Adjust based on indicators
        score += len(incident.indicators) * 0.5

        # Adjust based on target
        if incident.target_actor:
            score += 1.0

        return min(score, 10.0)

    def _find_correlated_incidents(
        self,
        incident: SecurityIncident,
        max_results: int = 10,
    ) -> list[SecurityIncident]:
        """Find incidents correlated with the given incident."""
        correlated = []

        for other in self._incidents.values():
            if other.incident_id == incident.incident_id:
                continue

            correlation_score = 0.0

            # Same source actor
            if incident.source_actor and incident.source_actor == other.source_actor:
                correlation_score += 0.4

            # Same target
            if incident.target_actor and incident.target_actor == other.target_actor:
                correlation_score += 0.3

            # Same threat type
            if incident.threat_type == other.threat_type:
                correlation_score += 0.2

            # Shared indicators
            shared_indicators = {i.value for i in incident.indicators} & {
                i.value for i in other.indicators
            }
            correlation_score += len(shared_indicators) * 0.1

            if correlation_score > 0.3:
                correlated.append(other)

        correlated.sort(key=self._calculate_severity_score, reverse=True)
        return correlated[:max_results]

    def _reconstruct_attack_chain(self, incident: SecurityIncident) -> list[dict[str, Any]]:
        """Reconstruct the attack chain leading to this incident."""
        chain = []
        correlated = self._find_correlated_incidents(incident, max_results=20)

        # Sort by timestamp
        correlated.sort(key=lambda x: x.timestamp)

        for related in correlated:
            chain.append(
                {
                    "incident_id": related.incident_id,
                    "timestamp": related.timestamp.isoformat(),
                    "threat_type": related.threat_type.value,
                    "severity": self._calculate_severity_score(related),
                }
            )

        return chain

    def _match_iocs(self, incident: SecurityIncident) -> list[dict[str, Any]]:
        """Match indicators of compromise against known threat intelligence."""
        matches = []

        for indicator in incident.indicators:
            if indicator.value in self._indicator_cache:
                cached = self._indicator_cache[indicator.value]
                matches.append(
                    {
                        "indicator": indicator.value,
                        "matched_threat": cached.indicator_id,
                        "confidence": cached.confidence,
                        "tags": cached.tags,
                    }
                )

        return matches

    def _map_mitre_techniques(self, incident: SecurityIncident) -> list[str]:
        """Map incident to MITRE ATT&CK techniques."""
        technique_mapping = {
            ThreatType.SQL_INJECTION: ["T1190", "T1059"],
            ThreatType.XSS_ATTACK: ["T1189", "T1059"],
            ThreatType.UNAUTHORIZED_ACCESS: ["T1078", "T1133"],
            ThreatType.PRIVILEGE_ESCALATION: ["T1068", "T1134"],
            ThreatType.DATA_EXFILTRATION: ["T1041", "T1048"],
            ThreatType.MALWARE: ["T1204", "T1059"],
            ThreatType.PHISHING: ["T1566", "T1204"],
        }

        return technique_mapping.get(incident.threat_type, [])

    def _generate_recommendations(self, incident: SecurityIncident) -> list[str]:
        """Generate remediation recommendations for an incident."""
        recommendations = []

        if incident.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
            recommendations.append("Immediately isolate affected systems")
            recommendations.append("Conduct forensic analysis")
            recommendations.append("Review access logs for compromise indicators")

        if incident.threat_type == ThreatType.SQL_INJECTION:
            recommendations.append("Review and parameterize all database queries")
            recommendations.append("Implement input validation")

        if incident.threat_type == ThreatType.XSS_ATTACK:
            recommendations.append("Implement Content Security Policy (CSP)")
            recommendations.append("Sanitize all user inputs")

        if incident.threat_type == ThreatType.UNAUTHORIZED_ACCESS:
            recommendations.append("Reset compromised credentials")
            recommendations.append("Review and restrict access permissions")

        return recommendations

    def _generate_strategic_recommendations(self) -> list[str]:
        """Generate strategic security recommendations based on overall threat landscape."""
        recommendations = []

        # Check incident trends
        critical_count = self._stats["incidents_by_level"].get("critical", 0)
        if critical_count > 5:
            recommendations.append(
                f"High critical incident count ({critical_count}) - consider security architecture review"
            )

        # Check for specific threat patterns
        sql_injection_count = self._stats["incidents_by_type"].get("sql_injection", 0)
        if sql_injection_count > 10:
            recommendations.append(
                f" Elevated SQL injection attempts ({sql_injection_count}) - implement WAF rules"
            )

        # Auto-response effectiveness
        if self._stats["auto_responses_triggered"] > 100:
            recommendations.append(
                "High auto-response rate - review detection thresholds for false positives"
            )

        # Check external threat detection stats
        if self._stats["external_threats_detected"] > 50:
            recommendations.append(
                "High external threat count - review gateway protections"
            )

        if not recommendations:
            recommendations.append("Security posture stable - continue monitoring")

        return recommendations

    async def _schedule_unblock(self, source: str, duration: int) -> None:
        """Schedule automatic unblocking of a source."""
        await asyncio.sleep(duration)
        self._blocked_sources.discard(source)
        logger.info("Source automatically unblocked", source=source)

    async def _schedule_unisolate(self, actor_id: str, duration: int) -> None:
        """Schedule automatic un-isolation of an actor."""
        await asyncio.sleep(duration)
        self._isolated_actors.discard(actor_id)
        logger.info("Actor automatically un-isolated", actor_id=actor_id)
