"""
Sentinel Module - Safety Guardian for Heretek Swarm.

This module provides the SentinelAgent class and supporting types for:
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

Usage:
    from heretek_swarm.actors.sentinel import SentinelAgent, SafetyLevel, ViolationType
    from heretek_swarm.actors.sentinel.types import SafetyViolation, SafetyReport

Module structure:
    - sentinel/: Main module directory
        - __init__.py: Main exports
        - types.py: Enums and dataclasses (SafetyLevel, ViolationType, etc.)
        - helpers.py: Helper functions for pattern checking and reports
        - agent.py: SentinelAgent class
"""

# Import from agent.py (the main SentinelAgent class)
from heretek_swarm.actors.sentinel.agent import SentinelAgent

# Re-export helpers from sentinel.helpers
from heretek_swarm.actors.sentinel.helpers import (
    SentinelHelpers,
    check_injection_patterns,
    check_pii_patterns,
    generate_safety_report,
)

# Re-export types from sentinel.types
from heretek_swarm.actors.sentinel.types import (
    AnomalyAlert,
    ContentCategory,
    SafetyLevel,
    SafetyReport,
    SafetyViolation,
    ViolationType,
)

__all__ = [
    "AnomalyAlert",
    "ContentCategory",
    # Types
    "SafetyLevel",
    "SafetyReport",
    "SafetyViolation",
    # Main class
    "SentinelAgent",
    # Helpers
    "SentinelHelpers",
    "ViolationType",
    "check_injection_patterns",
    "check_pii_patterns",
    "generate_safety_report",
]
