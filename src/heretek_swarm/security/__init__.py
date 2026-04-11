"""
Security Module for Heretek Swarm

Provides comprehensive security features:
- Zero-trust 4-layer validation (SH-1)
- Adversarial detection for prompt injection (SH-2)
- Rate limiting and DDoS protection (SH-3)
- Guardrails system for input/output filtering

Reference: EXPANSION_ROADMAP.md Security Hardening (SH-1, SH-2, SH-3)
"""

from heretek_swarm.security.adversarial import (
    AdversarialDetectionResult,
    # Core detector
    AdversarialDetector,
    AttackCategory,
    DetectionMatch,
    JailbreakDetectionConfig,
    OWASPCategory,
    # Reporter
    OWASPComplianceReporter,
    # Configuration
    PromptInjectionConfig,
    # Enums
    ThreatLevel,
    # Convenience functions
    create_default_detector,
    create_strict_detector,
)
from heretek_swarm.security.ddos_protection import (
    DDoSDetectionConfig,
    DDoSDetectionResult,
    DDoSDetector,
    DDoSMitigator,
    # Core protection
    DDoSProtection,
    DDoSSeverity,
    MitigationAction,
    MitigationConfig,
    # Configuration
    RateLimitConfig,
    RateLimiter,
    # Results
    RateLimitResult,
    TierConfig,
    # Token bucket
    TokenBucket,
    # Enums
    UserTier,
    # Convenience functions
    create_default_protection,
    create_strict_protection,
)
from heretek_swarm.security.guardrails import (
    BlockedPattern,
    FilterResult,
    GuardrailsAction,
    GuardrailsConfig,
    GuardrailsSystem,
    ValidationResult,
)
from heretek_swarm.security.zero_trust import (
    AuditLogConfig,
    # Layer 4: Audit Logging
    AuditLogger,
    BehavioralBaseline,
    ContextValidationConfig,
    # Layer 2: Context Validation
    ContextValidator,
    InputValidationConfig,
    # Layer 1: Input Validation
    InputValidator,
    LayerResult,
    OutputValidationConfig,
    # Layer 3: Output Validation
    OutputValidator,
    # Severity levels
    Severity,
    ValidatedInput,
    ZeroTrustResult,
    # Core validator
    ZeroTrustValidator,
    # Convenience functions
    create_default_validator,
    create_strict_validator,
)

__all__ = [
    # Zero-trust (SH-1)
    "ZeroTrustValidator",
    "ZeroTrustResult",
    "LayerResult",
    "InputValidator",
    "InputValidationConfig",
    "ValidatedInput",
    "ContextValidator",
    "ContextValidationConfig",
    "BehavioralBaseline",
    "OutputValidator",
    "OutputValidationConfig",
    "AuditLogger",
    "AuditLogConfig",
    "Severity",
    "create_default_validator",
    "create_strict_validator",
    # Adversarial Detection (SH-2)
    "AdversarialDetector",
    "AdversarialDetectionResult",
    "DetectionMatch",
    "PromptInjectionConfig",
    "JailbreakDetectionConfig",
    "ThreatLevel",
    "AttackCategory",
    "OWASPCategory",
    "OWASPComplianceReporter",
    "create_default_detector",
    "create_strict_detector",
    # DDoS Protection (SH-3)
    "DDoSProtection",
    "RateLimiter",
    "DDoSDetector",
    "DDoSMitigator",
    "RateLimitResult",
    "DDoSDetectionResult",
    "RateLimitConfig",
    "TierConfig",
    "DDoSDetectionConfig",
    "MitigationConfig",
    "UserTier",
    "DDoSSeverity",
    "MitigationAction",
    "TokenBucket",
    "create_default_protection",
    "create_strict_protection",
    # Guardrails
    "GuardrailsSystem",
    "GuardrailsConfig",
    "GuardrailsAction",
    "BlockedPattern",
    "ValidationResult",
    "FilterResult",
]
