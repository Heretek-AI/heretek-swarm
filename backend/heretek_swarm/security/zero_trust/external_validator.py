"""External threat detection — prompt injection, exfiltration, DoS, reputation."""

import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .context_validator import ContextValidator
from .result_types import Severity


@dataclass
class ExternalThreatConfig:
    """Configuration for external threat detection in zero-trust."""

    enable_prompt_injection_detection: bool = True
    enable_exfiltration_detection: bool = True
    enable_dos_detection: bool = True
    enable_reputation_check: bool = True
    min_reputation_score: float = 0.3
    false_positive_threshold: float = 0.01
    min_signals_for_block: int = 2
    alert_on_validation_failure: bool = True
    connection_timeout_seconds: float = 5.0


class ExternalInputValidator:
    """Validator for external inputs with threat detection integration."""

    PROMPT_INJECTION_PATTERNS = [  # noqa: RUF012
        (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", "prompt_injection"),
        (r"disregard\s+(your\s+)?(previous|last)\s+instructions", "prompt_injection"),
        (r"new\s+instructions?\s*:", "prompt_injection"),
        (r"<\|.*?\|>", "prompt_injection"),
        (r"\[SYSTEM\]", "prompt_injection"),
        (r"system\s*:\s*", "prompt_injection"),
    ]

    EXFILTRATION_PATTERNS = [  # noqa: RUF012
        (r"extract.*(password|secret|key|token|credential)", "exfiltration"),
        (r"(dump|export|download)\s+(all|entire|full)\s+(memory|context|state)", "exfiltration"),
        (r"show\s+me\s+(your|all)\s+(system|prompt|instruction)", "exfiltration"),
    ]

    DOS_PATTERNS = [  # noqa: RUF012
        (r"(repeating|same)\s+(request|input)\s+(\d+|\w+)\s+times", "dos"),
        (r"for\s+(\d+)\s+(iterations?|loops?|cycles?)", "dos"),
    ]

    def __init__(
        self,
        external_config: ExternalThreatConfig | None = None,
        context_validator: ContextValidator | None = None,
    ):
        self.config = external_config or ExternalThreatConfig()
        self.context_validator = context_validator or ContextValidator()
        self._compiled_prompt = [(re.compile(p, re.IGNORECASE), t) for p, t in self.PROMPT_INJECTION_PATTERNS]
        self._compiled_exfil = [(re.compile(p, re.IGNORECASE), t) for p, t in self.EXFILTRATION_PATTERNS]
        self._compiled_dos = [(re.compile(p, re.IGNORECASE), t) for p, t in self.DOS_PATTERNS]
        self._source_reputation: dict[str, float] = {}
        self._validation_failures: dict[str, list[float]] = defaultdict(list)

    def check_reputation(self, source: str) -> tuple[bool, float, str]:
        score = self._source_reputation.get(source, 0.5)
        passed = score >= self.config.min_reputation_score
        reason = "trusted" if passed else f"low_reputation({score:.2f})"
        return passed, score, reason

    def update_reputation(self, source: str, blocked: bool, weight: float = 1.0) -> float:
        current = self._source_reputation.get(source, 0.5)
        if blocked:
            new_score = max(0.0, current - (0.1 * weight))
        else:
            new_score = min(1.0, current + (0.01 * weight))
        self._source_reputation[source] = new_score
        return new_score

    def validate_external_input(
        self, data: dict[str, Any], source: str, source_type: str = "unknown",
    ) -> tuple[bool, str, dict[str, Any]]:
        content_str = str(data)
        threat_indicators: list[str] = []
        severity = Severity.INFO

        if self.config.enable_prompt_injection_detection:
            for pattern, threat_type in self._compiled_prompt:
                if pattern.search(content_str):
                    threat_indicators.append(threat_type)
                    severity = Severity.HIGH

        if self.config.enable_exfiltration_detection:
            for pattern, threat_type in self._compiled_exfil:
                if pattern.search(content_str):
                    threat_indicators.append(threat_type)
                    severity = Severity.HIGH

        if self.config.enable_dos_detection:
            for pattern, threat_type in self._compiled_dos:
                if pattern.search(content_str):
                    threat_indicators.append(threat_type)
                    if severity != Severity.HIGH:
                        severity = Severity.WARNING

        if self.config.enable_reputation_check:
            rep_passed, _score, _rep_reason = self.check_reputation(source)
            if not rep_passed:
                threat_indicators.append("low_reputation")
                severity = Severity.HIGH

        passed = len(threat_indicators) < self.config.min_signals_for_block

        if not passed and self.config.alert_on_validation_failure:
            self._validation_failures[source].append(time.time())

        details = {
            "source": source,
            "source_type": source_type,
            "threat_indicators": threat_indicators,
            "severity": severity.value,
            "reputation_score": self._source_reputation.get(source, 0.5),
        }

        reason = "passed"
        if not passed:
            reason = f"threats_detected: {', '.join(set(threat_indicators))}"

        return passed, reason, details

    def get_validation_failures(self, source: str, window_seconds: int = 300) -> int:
        now = time.time()
        failures = self._validation_failures.get(source, [])
        return sum(1 for f in failures if now - f < window_seconds)
