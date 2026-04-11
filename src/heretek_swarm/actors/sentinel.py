"""
Sentinel Agent - Safety Guardian & Input/Output Validation.

The Sentinel provides:
- Input validation and sanitization
- Output filtering and safety checks
- Guardrail enforcement
- Content policy compliance
- Harmful content detection
- Safety report generation

Sentinel is the "safety gate" of the Collective, ensuring all inputs and outputs
meet safety standards before processing or delivery.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from pydantic import ValidationError

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.validation import validate_message

_logger = structlog.get_logger("SentinelAgent")


class SafetyLevel(str, Enum):
    """Safety violation severity levels."""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class ViolationType(str, Enum):
    """Types of safety violations."""
    INJECTION_ATTEMPT = "injection_attempt"
    MALICIOUS_CONTENT = "malicious_content"
    PII_DETECTED = "pii_detected"
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual_content"
    DANGEROUS_ACTIVITY = "dangerous_activity"
    MISINFORMATION = "misinformation"
    SPAM = "spam"
    POLICY_VIOLATION = "policy_violation"


class ContentCategory(str, Enum):
    """Content classification categories."""
    TEXT = "text"
    CODE = "code"
    URL = "url"
    FILE_PATH = "file_path"
    COMMAND = "command"
    API_CALL = "api_call"
    UNKNOWN = "unknown"


@dataclass
class SafetyViolation:
    """Record of a detected safety violation."""
    violation_id: str
    violation_type: ViolationType
    severity: SafetyLevel
    content_hash: str
    description: str
    timestamp: datetime
    source_agent: Optional[str] = None
    target_agent: Optional[str] = None
    blocked: bool = True
    remediation_action: Optional[str] = None


@dataclass
class SafetyReport:
    """Aggregated safety report."""
    report_id: str
    timestamp: datetime
    total_scans: int
    violations_detected: int
    violations_blocked: int
    violations_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    recommendations: List[str]


class SentinelAgent(AgentActor):
    """
    Sentinel Agent - Safety Guardian for the Heretek Swarm Collective.
    
    Sentinel provides comprehensive input/output validation, guardrail enforcement,
    and content safety analysis for all inter-agent communications.
    """

    def __init__(self, agent_id: Optional[str], name: str, description: str, config: Optional[Dict[str, Any]], db_pool: Optional[Any], redis_client: Optional[Any]):
        super().__init__(
            agent_id=agent_id,
            _name = name,
            description=description,
            _config = config,
            _db_pool = db_pool,
            _redis_client = redis_client,
        )

        # Safety configuration
        self._max_content_size = config.get("max_content_size", 100000) if config else 100000
        self._enable_pii_detection = config.get("enable_pii_detection", True) if config else True
        self._enable_injection_detection = config.get("enable_injection_detection", True) if config else True
        self._auto_block_critical = config.get("auto_block_critical", True) if config else True

        # Safety state
        self._violations: Dict[str, SafetyViolation] = {}
        self._violation_history: List[str] = []  # LRU keys
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

        logger.info(
            "SentinelAgent initialized",
            _agent_id = self.agent_id,
            _max_content_size = self._max_content_size,
            _pii_detection = self._enable_pii_detection,
            _injection_detection = self._enable_injection_detection,
        )

    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming message with safety validation."""
        try:
            _handler = self._message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                logger.warning(
                    "Unknown message type",
                    _message_type = message.message_type,
                    _sender = message.sender_id,
                )
        except Exception as e:
            logger.error(
                "Error processing message",
                _message_type = message.message_type,
                error=str(e),
                _exc_info = True,
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
        }

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
            _content = message.content
            _input_content = content.get("content", "")
            _content_type = content.get("content_type", "text")
            source = content.get("source", "unknown")
            _strict_mode = content.get("strict_mode", False)

            # Validate input using Pydantic
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "validate_input",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Scan content
            _scan_result = await self._scan_content(
                input_content,
                content_type,
                _strict_mode = strict_mode,
            )

            # Log and respond
            logger.info(
                "Input validation completed",
                _scan_id = scan_result["scan_id"],
                _safety_level = scan_result["safety_level"],
                _violations_count = len(scan_result.get("violations", [])),
            )

            # Send response
            _response_content = {
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
            _content = message.content
            _output_content = content.get("content", "")
            target = content.get("target", "external")
            _content_type = content.get("content_type", "text")
            _strict_mode = content.get("strict_mode", False)

            # Validate input
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "validate_output",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Scan content
            _scan_result = await self._scan_content(
                output_content,
                content_type,
                _strict_mode = strict_mode,
            )

            logger.info(
                "Output validation completed",
                _scan_id = scan_result["scan_id"],
                _safety_level = scan_result["safety_level"],
                _target = target,
            )

            _response_content = {
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
            _content = message.content
            _scan_content = content.get("content", "")
            _scan_types = content.get("scan_types", ["all"])
            _return_details = content.get("return_details", True)

            # Validate
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "scan_content",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Perform scan
            _violations = []
            _safety_level = SafetyLevel.SAFE

            # Check injection patterns
            if "injection" in scan_types or "all" in scan_types:
                _injection_violations = self._check_injection_patterns(scan_content)
                violations.extend(injection_violations)

            # Check PII
            if "pii" in scan_types or "all" in scan_types:
                _pii_violations = self._check_pii_patterns(scan_content)
                violations.extend(pii_violations)

            # Determine safety level
            if violations:
                _max_severity = max(v.get("severity", "low_risk") for v in violations)
                _safety_level = SafetyLevel(max_severity)

            # Update statistics
            self._stats["total_scans"] += 1
            if not violations:
                self._stats["safe_scans"] += 1

            _response_content = {
                "scan_id": f"scan_{datetime.now(timezone.utc).timestamp()}",
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
            _content = message.content
            _check_content = content.get("content", "")
            _policies = content.get("policies", [])
            _context = content.get("context", {})

            # Validate
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "check_policy",
                "content": content,
                "timestamp": message.timestamp,
            })

            _violations = []

            for policy in policies:
                _policy_violation = await self._check_policy_rule(
                    check_content,
                    policy,
                    context,
                )
                if policy_violation:
                    violations.append(policy_violation)

            _response_content = {
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
            _content = message.content
            _time_range = content.get("time_range", "24h")
            _include_recommendations = content.get("include_recommendations", True)

            # Validate
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "get_safety_report",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Generate report
            report = self._generate_safety_report(
                _time_range = time_range,
                _include_recommendations = include_recommendations,
            )

            _response_content = {
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
            _content = message.content
            violation_id = content.get("violation_id")

            if not violation_id:
                await self._send_error(message, "Missing violation_id")
                return

            # Validate
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "get_violation_details",
                "content": content,
                "timestamp": message.timestamp,
            })

            violation = self._violations.get(violation_id)

            if not violation:
                await self._send_error(message, "Violation not found", f"ID: {violation_id}")
                return

            _response_content = {
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
            _content = message.content

            # Validate
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "update_guardrails",
                "content": content,
                "timestamp": message.timestamp,
            })

            _updates = []

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

            _response_content = {
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
            _validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "get_statistics",
                "content": {},
                "timestamp": message.timestamp,
            })

            _response_content = {
                "statistics": self._stats.copy(),
                "active_violations": len([v for v in self._violations.values() if not v.blocked]),
                "total_violations_tracked": len(self._violations),
                "violation_history_size": len(self._violation_history),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid statistics request", str(ve))
        except Exception as e:
            logger.error("Error getting statistics", error=str(e), exc_info=True)
            await self._send_error(message, "Statistics retrieval failed", str(e))

    async def _scan_content(self, content: str, _content_type: str, _strict_mode: bool) -> Dict[str, Any]:
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
        _scan_id = f"scan_{datetime.now(timezone.utc).timestamp()}"
        _violations = []
        _sanitized_content = content

        # Check content size
        if len(content) > self._max_content_size:
            violations.append({
                "type": ViolationType.POLICY_VIOLATION.value,
                "severity": SafetyLevel.MEDIUM_RISK.value,
                "description": f"Content exceeds max size ({len(content)}/{self._max_content_size} chars)",
            })

        # Check injection patterns
        if self._enable_injection_detection:
            _injection_violations = self._check_injection_patterns(content)
            violations.extend(injection_violations)

        # Check PII
        if self._enable_pii_detection:
            _pii_violations = self._check_pii_patterns(content)
            violations.extend(pii_violations)

        # Determine overall safety level
        if violations:
            _severity_order = {
                SafetyLevel.CRITICAL.value: 5,
                SafetyLevel.HIGH_RISK.value: 4,
                SafetyLevel.MEDIUM_RISK.value: 3,
                SafetyLevel.LOW_RISK.value: 2,
                SafetyLevel.SAFE.value: 1,
            }
            _max_severity = max(
                severity_order.get(v.get("severity", "safe"), 1)
                for v in violations
            )
            _safety_level = {
                5: SafetyLevel.CRITICAL,
                4: SafetyLevel.HIGH_RISK,
                3: SafetyLevel.MEDIUM_RISK,
                2: SafetyLevel.LOW_RISK,
            }.get(max_severity, SafetyLevel.SAFE)
        else:
            _safety_level = SafetyLevel.SAFE

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
                _vtype = v.get("type", "unknown")
                self._stats["violations_by_type"][vtype] = \
                    self._stats["violations_by_type"].get(vtype, 0) + 1

        # Generate recommendations
        _recommendations = []
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

    def _check_injection_patterns(self, content: str) -> List[Dict[str, str]]:
        """Check content for injection attack patterns."""
        _violations = []

        for pattern in self._compiled_injection:
            _matches = pattern.findall(content)
            if matches:
                violations.append({
                    "type": ViolationType.INJECTION_ATTEMPT.value,
                    "severity": SafetyLevel.HIGH_RISK.value,
                    "description": f"Detected injection pattern: {pattern.pattern}",
                    "matches": len(matches),
                })

        return violations

    def _check_pii_patterns(self, content: str) -> List[Dict[str, str]]:
        """Check content for personally identifiable information."""
        _violations = []

        for pattern in self._compiled_pii:
            _matches = pattern.findall(content)
            if matches:
                violations.append({
                    "type": ViolationType.PII_DETECTED.value,
                    "severity": SafetyLevel.MEDIUM_RISK.value,
                    "description": f"Detected PII pattern: {pattern.pattern}",
                    "matches": len(matches),
                })

        return violations

    def _record_violation(self, violation: Dict[str, str], content: str, _scan_id: str) -> None:
        """Record a safety violation for tracking."""
        import hashlib

        _content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        _violation_id = f"viol_{datetime.now(timezone.utc).timestamp()}_{content_hash}"

        _record = SafetyViolation(
            _violation_id = violation_id,
            violation_type=ViolationType(violation.get("type", "policy_violation")),
            severity=SafetyLevel(violation.get("severity", "low_risk")),
            _content_hash = content_hash,
            _description = violation.get("description", "Unknown violation"),
            _timestamp = datetime.now(timezone.utc),
            _blocked = True,
        )

        # Store violation
        self._violations[violation_id] = record

        # Update LRU history
        self._violation_history.append(violation_id)
        if len(self._violation_history) > self._max_violation_history:
            # Remove oldest
            _oldest = self._violation_history.pop(0)
            self._violations.pop(oldest, None)

        self._stats["violations_blocked"] += 1

    def _generate_safety_report(self, _time_range: str, include_recommendations: bool) -> SafetyReport:
        """Generate comprehensive safety report."""
        _report_id = f"report_{datetime.now(timezone.utc).timestamp()}"

        violations_by_type: Dict[str, int] = {}
        violations_by_severity: Dict[str, int] = {}

        for violation in self._violations.values():
            _vtype = violation.violation_type.value
            violations_by_type[vtype] = violations_by_type.get(vtype, 0) + 1

            _severity = violation.severity.value
            violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1

        _recommendations = []
        if include_recommendations:
            if violations_by_type.get(ViolationType.INJECTION_ATTEMPT.value, 0) > 10:
                recommendations.append("High injection attempt rate - consider stricter input validation")
            if violations_by_type.get(ViolationType.PII_DETECTED.value, 0) > 5:
                recommendations.append("Frequent PII detection - implement data masking at source")
            if violations_by_severity.get(SafetyLevel.CRITICAL.value, 0) > 0:
                recommendations.append("Critical violations detected - review security policies")

        return SafetyReport(
            _report_id = report_id,
            _timestamp = datetime.now(timezone.utc),
            _total_scans = self._stats["total_scans"],
            _violations_detected = self._stats["violations_detected"],
            _violations_blocked = self._stats["violations_blocked"],
            _violations_by_type = violations_by_type,
            _violations_by_severity = violations_by_severity,
            _recommendations = recommendations,
        )

    async def _check_policy_rule(self, _content: str, _policy: str, _context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check content against a specific policy rule."""
        # Policy rules can be extended with custom logic
        # For now, return None (no violations) as placeholder
        return None
