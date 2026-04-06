"""
Security Module for Heretek Swarm

Provides comprehensive security features:
- Zero-trust 4-layer validation (SH-1)
- Adversarial detection for prompt injection (SH-2)
- Rate limiting and DDoS protection (SH-3)
- Guardrails system for input/output filtering

Reference: EXPANSION_ROADMAP.md Security Hardening (SH-1, SH-2, SH-3)
"""

from heretek_swarm.security.zero_trust import (
    # Core validator
    ZeroTrustValidator,
    ZeroTrustResult,
    LayerResult,
    # Layer 1: Input Validation
    InputValidator,
    InputValidationConfig,
    ValidatedInput,
    # Layer 2: Context Validation
    ContextValidator,
    ContextValidationConfig,
    BehavioralBaseline,
    # Layer 3: Output Validation
    OutputValidator,
    OutputValidationConfig,
    # Layer 4: Audit Logging
    AuditLogger,
    AuditLogConfig,
    # Severity levels
    Severity,
    # Convenience functions
    create_default_validator,
    create_strict_validator,
)

from heretek_swarm.security.adversarial import (
    # Core detector
    AdversarialDetector,
    AdversarialDetectionResult,
    DetectionMatch,
    # Configuration
    PromptInjectionConfig,
    JailbreakDetectionConfig,
    # Enums
    ThreatLevel,
    AttackCategory,
    OWASPCategory,
    # Reporter
    OWASPComplianceReporter,
    # Convenience functions
    create_default_detector,
    create_strict_detector,
)

from heretek_swarm.security.ddos_protection import (
    # Core protection
    DDoSProtection,
    RateLimiter,
    DDoSDetector,
    DDoSMitigator,
    # Results
    RateLimitResult,
    DDoSDetectionResult,
    # Configuration
    RateLimitConfig,
    TierConfig,
    DDoSDetectionConfig,
    MitigationConfig,
    # Enums
    UserTier,
    DDoSSeverity,
    MitigationAction,
    # Token bucket
    TokenBucket,
    # Convenience functions
    create_default_protection,
    create_strict_protection,
)

from heretek_swarm.security.guardrails import (
    GuardrailsSystem,
    GuardrailsConfig,
    GuardrailsAction,
    BlockedPattern,
    ValidationResult,
    FilterResult,
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
