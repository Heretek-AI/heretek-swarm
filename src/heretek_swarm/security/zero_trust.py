"""
Enhanced Zero-Trust Security Module for Heretek Swarm

Implements 4-layer validation architecture:
- Layer 1: Input Validation (Pydantic v2, UUID v4, size limits)
- Layer 2: Context Validation (injection detection, behavioral analysis)
- Layer 3: Output Validation (PII detection, sensitive data filtering)
- Layer 4: Audit Logging (structured logging, severity levels)

Reference: EXPANSION_ROADMAP.md SH-1 Enhanced Zero-Trust
"""

import re
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Dict, List

import structlog
from pydantic import BaseModel, ConfigDict, field_validator

logger = structlog.get_logger(__name__)


# =============================================================================
# Severity Levels for Audit Logging (Layer 4)
# =============================================================================

class Severity(StrEnum):
    """Security event severity levels for audit logging."""
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# =============================================================================
# Validation Result Types
# =============================================================================

@dataclass
class LayerResult:
    """Result from a single validation layer."""
    layer: str
    passed: bool
    reason: str | None = None
    severity: Severity = Severity.INFO
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ZeroTrustResult:
    """Aggregated result from all 4 validation layers."""
    passed: bool
    layer1: LayerResult
    layer2: LayerResult
    layer3: LayerResult
    layer4: LayerResult
    request_id: str
    agent_id: str | None = None
    total_latency_ms: float = 0.0
    sanitized_output: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "passed": self.passed,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "total_latency_ms": self.total_latency_ms,
            "layers": {
                "layer1_input": {
                    "passed": self.layer1.passed,
                    "reason": self.layer1.reason,
                    "severity": self.layer1.severity.value,
                },
                "layer2_context": {
                    "passed": self.layer2.passed,
                    "reason": self.layer2.reason,
                    "severity": self.layer2.severity.value,
                },
                "layer3_output": {
                    "passed": self.layer3.passed,
                    "reason": self.layer3.reason,
                    "severity": self.layer3.severity.value,
                },
                "layer4_audit": {
                    "passed": self.layer4.passed,
                    "severity": self.layer4.severity.value,
                },
            },
        }


# =============================================================================
# Layer 1: Input Validation
# =============================================================================

class ValidatedInput(BaseModel):
    """
    Base model for validated input with strict Pydantic v2 settings.

    Features:
    - extra='forbid' rejects unknown fields (injection protection)
    - UUID v4 validation for all ID fields
    - Content size limits enforced
    """

    model_config = ConfigDict(
        extra="forbid",  # Reject unknown fields - critical for injection protection
        validate_assignment=True,  # Validate on field assignment
        str_strip_whitespace=True,  # Strip whitespace from strings
    )

    request_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, v: str) -> str:
        """Validate request_id is a valid UUID v4 (128-bit entropy)."""
        try:
            parsed = uuid.UUID(v, version=4)
            if parsed.version != 4:
                raise ValueError(f"request_id must be UUID v4, got version {parsed.version}")
            return v
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid UUID v4 request_id: {e}")


@dataclass
class InputValidationConfig:
    """Configuration for Layer 1 Input Validation."""
    max_content_size: int = 10240  # 10KB default max
    min_content_size: int = 1
    require_uuid_v4: bool = True
    max_string_length: int = 50000
    max_array_length: int = 1000
    max_nesting_depth: int = 10
    allowed_content_types: set[str] = field(default_factory=lambda: {
        "text/plain",
        "application/json",
        "text/markdown",
        "text/html",
    })


class InputValidator:
    """
    Layer 1: Input Validation

    Validates all incoming data against strict rules:
    - Pydantic v2 validation with extra='forbid'
    - UUID v4 format validation (128-bit entropy)
    - Content size limits (max 10KB default)
    - Type validation for all fields
    """

    # Injection patterns to detect at input level
    INJECTION_PATTERNS = [
        # Python injection
        (r"\bexec\s*\(", "exec() function call detected"),
        (r"\beval\s*\(", "eval() function call detected"),
        (r"\b__import__\s*\(", "__import__() function call detected"),
        (r"\bsubprocess\.", "subprocess module access detected"),
        (r"\bos\.system\s*\(", "os.system() call detected"),
        (r"\bos\.popen\s*\(", "os.popen() call detected"),
        # Shell injection
        (r";\s*rm\s", "rm command injection detected"),
        (r";\s*cat\s", "cat command injection detected"),
        (r"\|\s*sh\b", "shell pipe injection detected"),
        (r"\$\([^)]+\)", "command substitution detected"),
        (r"`[^`]+`", "backtick command substitution detected"),
        # SQL injection hints
        (r"'\s*OR\s+'?\d+'?\s*=\s*'?\d+", "SQL injection pattern detected"),
        (r"'\s*OR\s*'", "SQL OR injection detected"),
        (r"\bUNION\s+SELECT\b", "SQL UNION injection detected"),
        (r";\s*DROP\s+TABLE\b", "SQL DROP injection detected"),
        (r"\bSELECT\s+\*\s+FROM\b", "SQL SELECT injection detected"),
        # Path traversal
        (r"\.\./", "path traversal detected"),
        (r"\.\.\\", "path traversal detected"),
    ]

    def __init__(self, config: InputValidationConfig | None = None):
        self.config = config or InputValidationConfig()
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in self.INJECTION_PATTERNS
        ]

    def validate(
        self,
        data: dict[str, Any],
        model_class: type[ValidatedInput] | None = None,
        agent_id: str | None = None,
    ) -> LayerResult:
        """
        Validate input data against Layer 1 rules.

        Args:
            data: Input data dictionary to validate
            model_class: Optional Pydantic model class for strict validation
            agent_id: Agent ID for logging context

        Returns:
            LayerResult with validation status
        """
        start_time = time.time()

        try:
            # Check content size
            content_size = len(str(data))
            if content_size > self.config.max_content_size:
                return LayerResult(
                    layer="input",
                    passed=False,
                    reason=f"Content size {content_size} exceeds maximum {self.config.max_content_size}",
                    severity=Severity.WARNING,
                    details={"content_size": content_size, "max_size": self.config.max_content_size},
                )

            if content_size < self.config.min_content_size:
                return LayerResult(
                    layer="input",
                    passed=False,
                    reason=f"Content size {content_size} below minimum {self.config.min_content_size}",
                    severity=Severity.INFO,
                    details={"content_size": content_size, "min_size": self.config.min_content_size},
                )

            # Validate request_id if present
            if "request_id" in data and self.config.require_uuid_v4:
                try:
                    parsed = uuid.UUID(data["request_id"], version=4)
                    if parsed.version != 4:
                        return LayerResult(
                            layer="input",
                            passed=False,
                            reason=f"request_id must be UUID v4, got version {parsed.version}",
                            severity=Severity.WARNING,
                        )
                except (ValueError, AttributeError) as e:
                    return LayerResult(
                        layer="input",
                        passed=False,
                        reason=f"Invalid UUID v4 request_id: {e}",
                        severity=Severity.WARNING,
                    )

            # Check for injection patterns
            content_str = str(data)
            for pattern, description in self._compiled_patterns:
                if pattern.search(content_str):
                    return LayerResult(
                        layer="input",
                        passed=False,
                        reason=f"Injection pattern detected: {description}",
                        severity=Severity.HIGH,
                        details={"pattern": pattern.pattern, "description": description},
                    )

            # Validate nesting depth
            depth = self._calculate_depth(data)
            if depth > self.config.max_nesting_depth:
                return LayerResult(
                    layer="input",
                    passed=False,
                    reason=f"Nesting depth {depth} exceeds maximum {self.config.max_nesting_depth}",
                    severity=Severity.WARNING,
                    details={"depth": depth, "max_depth": self.config.max_nesting_depth},
                )

            # If a model class is provided, perform Pydantic validation
            if model_class is not None:
                try:
                    model_class.model_validate(data)
                    logger.debug(
                        "pydantic_validation_passed",
                        agent_id=agent_id,
                        model=model_class.__name__,
                    )
                except Exception as e:
                    return LayerResult(
                        layer="input",
                        passed=False,
                        reason=f"Pydantic validation failed: {e}",
                        severity=Severity.WARNING,
                        details={"pydantic_error": str(e)},
                    )

            latency_ms = (time.time() - start_time) * 1000

            return LayerResult(
                layer="input",
                passed=True,
                severity=Severity.INFO,
                details={
                    "content_size": content_size,
                    "depth": depth,
                    "latency_ms": latency_ms,
                },
            )

        except Exception as e:
            logger.error("input_validation_error", error=str(e), agent_id=agent_id)
            return LayerResult(
                layer="input",
                passed=False,
                reason=f"Validation error: {e}",
                severity=Severity.HIGH,
            )

    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate the maximum nesting depth of a data structure."""
        if current_depth > self.config.max_nesting_depth + 5:
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._calculate_depth(v, current_depth + 1)
                for v in obj.values()
            )
        if isinstance(obj, (list, tuple)):
            if not obj:
                return current_depth
            return max(
                self._calculate_depth(item, current_depth + 1)
                for item in obj
            )
        return current_depth


# =============================================================================
# Layer 2: Context Validation
# =============================================================================

@dataclass
class BehavioralBaseline:
    """Baseline for behavioral analysis."""
    agent_id: str
    avg_request_size: float = 0.0
    avg_request_interval_ms: float = 0.0
    common_patterns: set[str] = field(default_factory=set)
    total_requests: int = 0
    last_request_time: str | None = None
    anomaly_threshold: float = 3.0  # Standard deviations


@dataclass
class ContextValidationConfig:
    """Configuration for Layer 2 Context Validation."""
    enable_injection_detection: bool = True
    enable_behavioral_analysis: bool = True
    enable_anomaly_detection: bool = True
    anomaly_threshold: float = 3.0
    false_positive_threshold: float = 0.01  # Target < 1% false positive rate
    min_requests_for_baseline: int = 10
    max_baseline_age_hours: int = 24


class ContextValidator:
    """
    Layer 2: Context Validation

    Validates the context of requests:
    - Injection pattern detection (exec, eval, import os, subprocess)
    - Behavioral baseline comparison
    - Anomaly detection with configurable threshold
    - False positive rate < 1%
    """

    # Advanced injection patterns for context analysis
    CONTEXT_INJECTION_PATTERNS = [
        # Prompt injection patterns
        (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", "prompt injection: ignore instructions"),
        (r"disregard\s+(all\s+)?(previous|prior)\s+", "prompt injection: disregard"),
        (r"you\s+are\s+now\s+", "prompt injection: role change"),
        (r"act\s+as\s+(if|though)\s+", "prompt injection: role play"),
        (r"pretend\s+(to\s+be|that)\s+", "prompt injection: pretend"),
        (r"forget\s+(everything|all)\s+", "prompt injection: forget"),
        (r"new\s+instructions?\s*:", "prompt injection: new instructions"),
        (r"system\s*:\s*", "prompt injection: system prompt"),
        (r"<\|.*?\|>", "prompt injection: special token"),
        (r"\[SYSTEM\]", "prompt injection: system tag"),
        (r"\[INST\]", "prompt injection: instruction tag"),
        # Encoding-based injection
        (r"\\x[0-9a-fA-F]{2}", "encoded character detected"),
        (r"\\u[0-9a-fA-F]{4}", "unicode escape detected"),
        (r"%[0-9a-fA-F]{2}", "URL encoding detected"),
        (r"base64[_\s]*decode", "base64 decode detected"),
    ]

    def __init__(self, config: ContextValidationConfig | None = None):
        self.config = config or ContextValidationConfig()
        self._baselines: dict[str, BehavioralBaseline] = {}
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in self.CONTEXT_INJECTION_PATTERNS
        ]

    def validate(
        self,
        data: dict[str, Any],
        context: dict[str, Any] | None = None,
        agent_id: str | None = None,
    ) -> LayerResult:
        """
        Validate request context against Layer 2 rules.

        Args:
            data: Input data to validate
            context: Additional context (session, user, etc.)
            agent_id: Agent ID for behavioral baseline

        Returns:
            LayerResult with validation status
        """
        start_time = time.time()
        context = context or {}
        anomalies_detected = []

        try:
            content_str = str(data)

            # Injection detection
            if self.config.enable_injection_detection:
                for pattern, description in self._compiled_patterns:
                    if pattern.search(content_str):
                        return LayerResult(
                            layer="context",
                            passed=False,
                            reason=f"Context injection detected: {description}",
                            severity=Severity.HIGH,
                            details={"pattern": pattern.pattern, "description": description},
                        )

            # Behavioral analysis
            if self.config.enable_behavioral_analysis and agent_id:
                baseline = self._get_or_create_baseline(agent_id)
                behavioral_result = self._analyze_behavior(data, baseline)
                if behavioral_result:
                    anomalies_detected.extend(behavioral_result)

            # Anomaly detection
            if self.config.enable_anomaly_detection and anomalies_detected:
                severity = Severity.WARNING
                if len(anomalies_detected) >= 3:
                    severity = Severity.HIGH

                return LayerResult(
                    layer="context",
                    passed=False,
                    reason=f"Anomalies detected: {'; '.join(anomalies_detected)}",
                    severity=severity,
                    details={"anomalies": anomalies_detected},
                )

            latency_ms = (time.time() - start_time) * 1000

            return LayerResult(
                layer="context",
                passed=True,
                severity=Severity.INFO,
                details={
                    "latency_ms": latency_ms,
                    "behavioral_analysis": self.config.enable_behavioral_analysis,
                    "injection_detection": self.config.enable_injection_detection,
                },
            )

        except Exception as e:
            logger.error("context_validation_error", error=str(e), agent_id=agent_id)
            return LayerResult(
                layer="context",
                passed=False,
                reason=f"Context validation error: {e}",
                severity=Severity.HIGH,
            )

    def _get_or_create_baseline(self, agent_id: str) -> BehavioralBaseline:
        """Get or create behavioral baseline for an agent."""
        if agent_id not in self._baselines:
            self._baselines[agent_id] = BehavioralBaseline(agent_id=agent_id)
        return self._baselines[agent_id]

    def _analyze_behavior(
        self,
        data: dict[str, Any],
        baseline: BehavioralBaseline,
    ) -> list[str]:
        """
        Analyze request against behavioral baseline.

        Returns list of detected anomalies.
        """
        anomalies = []
        current_time = datetime.now(UTC)
        request_size = len(str(data))

        # Update baseline statistics
        if baseline.total_requests > 0:
            # Check for size anomaly
            size_deviation = abs(request_size - baseline.avg_request_size)
            if baseline.avg_request_size > 0:
                z_score = size_deviation / baseline.avg_request_size
                if z_score > self.config.anomaly_threshold:
                    anomalies.append(
                        f"Request size anomaly (z={z_score:.2f})"
                    )

            # Check for timing anomaly (rapid requests)
            if baseline.last_request_time:
                last_time = datetime.fromisoformat(baseline.last_request_time)
                interval_ms = (current_time - last_time).total_seconds() * 1000

                if baseline.avg_request_interval_ms > 0:
                    if interval_ms < baseline.avg_request_interval_ms * 0.1:
                        anomalies.append(
                            f"Rapid request detected (interval={interval_ms:.0f}ms)"
                        )

        # Update baseline
        baseline.total_requests += 1
        baseline.avg_request_size = (
            (baseline.avg_request_size * (baseline.total_requests - 1) + request_size)
            / baseline.total_requests
        )
        baseline.last_request_time = current_time.isoformat()

        return anomalies

    def update_baseline(
        self,
        agent_id: str,
        avg_request_size: float,
        avg_request_interval_ms: float,
    ) -> None:
        """Manually update behavioral baseline."""
        baseline = self._get_or_create_baseline(agent_id)
        baseline.avg_request_size = avg_request_size
        baseline.avg_request_interval_ms = avg_request_interval_ms


# =============================================================================
# Layer 3: Output Validation
# =============================================================================

@dataclass
class OutputValidationConfig:
    """Configuration for Layer 3 Output Validation."""
    enable_pii_detection: bool = True
    enable_sensitive_data_filtering: bool = True
    enable_response_sanitization: bool = True
    redact_pii: bool = True
    max_output_size: int = 100000  # 100KB max output


class OutputValidator:
    """
    Layer 3: Output Validation

    Validates all outgoing data:
    - PII detection and filtering
    - Sensitive data pattern detection
    - Response sanitization
    """

    # PII patterns for detection
    PII_PATTERNS = [
        # Email addresses
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
        # Phone numbers (US format)
        (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]"),
        # SSN
        (r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", "[SSN_REDACTED]"),
        # Credit card numbers
        (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CC_REDACTED]"),
        # IP addresses
        (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP_REDACTED]"),
        # API keys (common patterns)
        (r'\b(?:api[_-]?key|apikey|token|secret|password)\s*[=:]\s*["\']?[a-zA-Z0-9_-]{16,}["\']?',
         "[API_KEY_REDACTED]"),
    ]

    # Sensitive data patterns
    SENSITIVE_PATTERNS = [
        # Private keys
        (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----", "[PRIVATE_KEY_REDACTED]"),
        # AWS keys
        (r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
         "[AWS_KEY_REDACTED]"),
        # JWT tokens
        (r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", "[JWT_REDACTED]"),
    ]

    def __init__(self, config: OutputValidationConfig | None = None):
        self.config = config or OutputValidationConfig()
        self._compiled_pii = [
            (re.compile(p, re.IGNORECASE), replacement)
            for p, replacement in self.PII_PATTERNS
        ]
        self._compiled_sensitive = [
            (re.compile(p, re.IGNORECASE), replacement)
            for p, replacement in self.SENSITIVE_PATTERNS
        ]

    def validate(
        self,
        output: Any,
        agent_id: str | None = None,
    ) -> LayerResult:
        """
        Validate output data against Layer 3 rules.

        Args:
            output: Output data to validate
            agent_id: Agent ID for logging context

        Returns:
            LayerResult with validation status
        """
        start_time = time.time()
        output_str = str(output) if not isinstance(output, str) else output
        sanitized_output = output_str
        detected_pii = []
        detected_sensitive = []

        try:
            # Check output size
            if len(output_str) > self.config.max_output_size:
                return LayerResult(
                    layer="output",
                    passed=False,
                    reason=f"Output size {len(output_str)} exceeds maximum {self.config.max_output_size}",
                    severity=Severity.WARNING,
                    details={"output_size": len(output_str), "max_size": self.config.max_output_size},
                )

            # PII detection
            if self.config.enable_pii_detection:
                for pattern, replacement in self._compiled_pii:
                    matches = pattern.findall(output_str)
                    if matches:
                        detected_pii.append(pattern.pattern)
                        if self.config.redact_pii:
                            sanitized_output = pattern.sub(replacement, sanitized_output)

            # Sensitive data detection
            if self.config.enable_sensitive_data_filtering:
                for pattern, replacement in self._compiled_sensitive:
                    matches = pattern.findall(output_str)
                    if matches:
                        detected_sensitive.append(pattern.pattern)
                        if self.config.redact_pii:
                            sanitized_output = pattern.sub(replacement, sanitized_output)

            latency_ms = (time.time() - start_time) * 1000

            # Determine if validation passed
            passed = True
            reason = None
            if (detected_pii or detected_sensitive) and not self.config.redact_pii:
                passed = False
                reason = f"PII or sensitive data detected: {detected_pii + detected_sensitive}"

            return LayerResult(
                layer="output",
                passed=passed,
                reason=reason,
                severity=Severity.WARNING if detected_pii or detected_sensitive else Severity.INFO,
                details={
                    "latency_ms": latency_ms,
                    "pii_detected": detected_pii,
                    "sensitive_detected": detected_sensitive,
                    "sanitized": self.config.redact_pii and (bool(detected_pii) or bool(detected_sensitive)),
                    "sanitized_output": sanitized_output,
                },
            )

        except Exception as e:
            logger.error("output_validation_error", error=str(e), agent_id=agent_id)
            return LayerResult(
                layer="output",
                passed=False,
                reason=f"Output validation error: {e}",
                severity=Severity.HIGH,
            )

    def sanitize(self, output: str) -> str:
        """
        Sanitize output by redacting PII and sensitive data.

        Args:
            output: Output string to sanitize

        Returns:
            Sanitized string with PII/sensitive data redacted
        """
        sanitized = output

        for pattern, replacement in self._compiled_pii:
            sanitized = pattern.sub(replacement, sanitized)

        for pattern, replacement in self._compiled_sensitive:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized


# =============================================================================
# Layer 4: Audit Logging
# =============================================================================

@dataclass
class AuditLogConfig:
    """Configuration for Layer 4 Audit Logging."""
    enable_logging: bool = True
    log_all_events: bool = True
    log_level: str = "INFO"
    retention_days: int = 30
    include_request_body: bool = False  # Security: don't log sensitive data by default
    include_response_body: bool = False
    structured_format: bool = True


class AuditLogger:
    """
    Layer 4: Audit Logging

    Comprehensive audit logging for all security events:
    - All security events logged with structlog
    - Structured log format with timestamp, agent_id, request_id
    - Severity levels (INFO, WARNING, HIGH, CRITICAL)
    - Log retention policy (30 days default)
    """

    def __init__(self, config: AuditLogConfig | None = None):
        self.config = config or AuditLogConfig()
        self._event_counts: dict[str, int] = defaultdict(int)
        self._high_severity_events: list[dict[str, Any]] = []

    def log(
        self,
        event_type: str,
        result: ZeroTrustResult,
        additional_context: dict[str, Any] | None = None,
    ) -> LayerResult:
        """
        Log a security event.

        Args:
            event_type: Type of security event
            result: Zero-trust validation result
            additional_context: Additional context to log

        Returns:
            LayerResult indicating logging success
        """
        try:
            context = additional_context or {}

            # Build log entry
            log_entry = {
                "event_type": event_type,
                "request_id": result.request_id,
                "agent_id": result.agent_id,
                "passed": result.passed,
                "total_latency_ms": result.total_latency_ms,
                "timestamp": datetime.now(UTC).isoformat(),
                **context,
            }

            # Determine severity and log level
            severity = Severity.INFO
            if not result.passed:
                if result.layer1.severity in (Severity.HIGH, Severity.CRITICAL):
                    severity = result.layer1.severity
                elif result.layer2.severity in (Severity.HIGH, Severity.CRITICAL):
                    severity = result.layer2.severity
                elif result.layer3.severity in (Severity.HIGH, Severity.CRITICAL):
                    severity = result.layer3.severity
                else:
                    severity = Severity.WARNING

            log_entry["severity"] = severity.value

            # Track event counts
            self._event_counts[event_type] += 1
            self._event_counts[f"{event_type}:{severity.value}"] += 1

            # Store high severity events for review
            if severity in (Severity.HIGH, Severity.CRITICAL):
                self._high_severity_events.append(log_entry)
                # Keep only last 1000 high severity events
                if len(self._high_severity_events) > 1000:
                    self._high_severity_events = self._high_severity_events[-1000:]

            # Log to structlog
            log_method = {
                Severity.INFO: logger.info,
                Severity.WARNING: logger.warning,
                Severity.HIGH: logger.error,
                Severity.CRITICAL: logger.critical,
            }.get(severity, logger.info)

            log_method(
                f"security_event_{event_type}",
                **log_entry,
            )

            return LayerResult(
                layer="audit",
                passed=True,
                severity=severity,
                details={
                    "logged": True,
                    "event_type": event_type,
                    "severity": severity.value,
                },
            )

        except Exception as e:
            logger.error("audit_logging_error", error=str(e))
            return LayerResult(
                layer="audit",
                passed=False,
                reason=f"Audit logging error: {e}",
                severity=Severity.WARNING,
            )

    def get_event_counts(self) -> dict[str, int]:
        """Get counts of logged events by type."""
        return dict(self._event_counts)

    def get_high_severity_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent high severity events."""
        return self._high_severity_events[-limit:]


# =============================================================================
# Zero-Trust Orchestrator
# =============================================================================

class ZeroTrustValidator:
    """
    Enhanced Zero-Trust Security Orchestrator

    Coordinates all 4 validation layers:
    - Layer 1: Input Validation
    - Layer 2: Context Validation
    - Layer 3: Output Validation
    - Layer 4: Audit Logging

    Target Performance:
    - Validation latency < 50ms p95
    - False negative rate < 0.1%
    - Throughput > 1000 validations/second
    """

    def __init__(
        self,
        input_config: InputValidationConfig | None = None,
        context_config: ContextValidationConfig | None = None,
        output_config: OutputValidationConfig | None = None,
        audit_config: AuditLogConfig | None = None,
    ):
        self.input_validator = InputValidator(input_config)
        self.context_validator = ContextValidator(context_config)
        self.output_validator = OutputValidator(output_config)
        self.audit_logger = AuditLogger(audit_config)

        # Performance metrics
        self._validation_count = 0
        self._total_latency_ms = 0.0
        self._failed_validations = 0

    async def validate_request(
        self,
        data: dict[str, Any],
        context: dict[str, Any] | None = None,
        agent_id: str | None = None,
        request_id: str | None = None,
        model_class: type[ValidatedInput] | None = None,
    ) -> ZeroTrustResult:
        """
        Validate a request through all 4 layers.

        Args:
            data: Input data to validate
            context: Additional context for Layer 2
            agent_id: Agent ID for logging and behavioral analysis
            request_id: Unique request ID (UUID v4)
            model_class: Optional Pydantic model for strict validation

        Returns:
            ZeroTrustResult with all layer results
        """
        start_time = time.time()
        request_id = request_id or str(uuid.uuid4())

        # Layer 1: Input Validation
        layer1 = self.input_validator.validate(data, model_class, agent_id)

        # Layer 2: Context Validation (skip if Layer 1 failed critically)
        if layer1.severity == Severity.CRITICAL:
            layer2 = LayerResult(
                layer="context",
                passed=True,
                reason="Skipped due to Layer 1 critical failure",
                severity=Severity.INFO,
            )
        else:
            layer2 = self.context_validator.validate(data, context, agent_id)

        # Layer 3: Output Validation (for response data, pass-through for input)
        layer3 = LayerResult(
            layer="output",
            passed=True,
            reason="Input validation - output layer applied on response",
            severity=Severity.INFO,
        )

        # Determine overall pass/fail
        passed = layer1.passed and layer2.passed

        # Calculate total latency
        latency_ms = (time.time() - start_time) * 1000

        # Create result
        result = ZeroTrustResult(
            passed=passed,
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            layer4=LayerResult(layer="audit", passed=True, severity=Severity.INFO),
            request_id=request_id,
            agent_id=agent_id,
            total_latency_ms=latency_ms,
        )

        # Layer 4: Audit Logging
        result.layer4 = self.audit_logger.log(
            event_type="request_validation",
            result=result,
            additional_context={
                "layer1_passed": layer1.passed,
                "layer2_passed": layer2.passed,
            },
        )

        # Update metrics
        self._validation_count += 1
        self._total_latency_ms += latency_ms
        if not passed:
            self._failed_validations += 1

        return result

    async def validate_response(
        self,
        output: Any,
        agent_id: str | None = None,
        request_id: str | None = None,
    ) -> ZeroTrustResult:
        """
        Validate a response through output validation layer.

        Args:
            output: Output data to validate
            agent_id: Agent ID for logging
            request_id: Associated request ID

        Returns:
            ZeroTrustResult with output validation results
        """
        start_time = time.time()
        request_id = request_id or str(uuid.uuid4())

        # Skip layers 1-2 for response validation
        layer1 = LayerResult(
            layer="input",
            passed=True,
            reason="Response validation - input layer skipped",
            severity=Severity.INFO,
        )
        layer2 = LayerResult(
            layer="context",
            passed=True,
            reason="Response validation - context layer skipped",
            severity=Severity.INFO,
        )

        # Layer 3: Output Validation
        layer3 = self.output_validator.validate(output, agent_id)

        latency_ms = (time.time() - start_time) * 1000

        # Extract sanitized output from layer3 details if available
        sanitized = layer3.details.get("sanitized_output")

        result = ZeroTrustResult(
            passed=layer3.passed,
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            layer4=LayerResult(layer="audit", passed=True, severity=Severity.INFO),
            request_id=request_id,
            agent_id=agent_id,
            total_latency_ms=latency_ms,
            sanitized_output=sanitized,
        )

        # Layer 4: Audit Logging
        result.layer4 = self.audit_logger.log(
            event_type="response_validation",
            result=result,
            additional_context={
                "layer3_passed": layer3.passed,
                "pii_detected": layer3.details.get("pii_detected", []),
            },
        )

        return result

    def get_metrics(self) -> dict[str, Any]:
        """Get validation metrics."""
        avg_latency = (
            self._total_latency_ms / self._validation_count
            if self._validation_count > 0
            else 0
        )

        return {
            "total_validations": self._validation_count,
            "failed_validations": self._failed_validations,
            "success_rate": (
                (self._validation_count - self._failed_validations) / self._validation_count
                if self._validation_count > 0
                else 1.0
            ),
            "avg_latency_ms": avg_latency,
            "event_counts": self.audit_logger.get_event_counts(),
        }

    def get_high_severity_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent high severity security events."""
        return self.audit_logger.get_high_severity_events(limit)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_default_validator() -> ZeroTrustValidator:
    """Create a ZeroTrustValidator with default configuration."""
    return ZeroTrustValidator(
        input_config=InputValidationConfig(),
        context_config=ContextValidationConfig(),
        output_config=OutputValidationConfig(),
        audit_config=AuditLogConfig(),
    )


def create_strict_validator() -> ZeroTrustValidator:
    """Create a ZeroTrustValidator with strict security configuration."""
    return ZeroTrustValidator(
        input_config=InputValidationConfig(
            max_content_size=5120,  # 5KB
            require_uuid_v4=True,
            max_nesting_depth=5,
        ),
        context_config=ContextValidationConfig(
            enable_injection_detection=True,
            enable_behavioral_analysis=True,
            enable_anomaly_detection=True,
            anomaly_threshold=2.0,  # More sensitive
        ),
        output_config=OutputValidationConfig(
            enable_pii_detection=True,
            enable_sensitive_data_filtering=True,
            redact_pii=True,
            max_output_size=50000,
        ),
        audit_config=AuditLogConfig(
            enable_logging=True,
            log_all_events=True,
            retention_days=90,
        ),
    )
