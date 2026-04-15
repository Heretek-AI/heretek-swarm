# Implementation Plan: SAFE-02 — Sentinel-Prime External Threat Detection

## Overview

**Task**: SAFE-02 — Sentinel-Prime External Threat Detection  
**Owner**: Sentinel-Prime  
**Depends**: Phase 1 (Nexus operational)  
**Status**: Ready for Implementation

---

## 1. Current State Analysis

### 1.1 Files Status

| File | Status | Notes |
|------|--------|-------|
| `src/heretek_swarm/actors/sentinel_prime.py` | ⚠️ PARTIAL | Skeleton exists with handlers, needs full implementation |
| `src/heretek_swarm/security/threat_detection.py` | ❌ MISSING | **Must be created** |
| `src/heretek_swarm/gateway/zero_trust.py` | ✅ EXISTS | Needs enhancement for external threat integration |

### 1.2 Sentinel vs Sentinel-Prime (Internal vs External Threats)

| Aspect | Sentinel (SAFE-01) | Sentinel-Prime (SAFE-02) |
|--------|---------------------|---------------------------|
| **Focus** | Internal anomalies | External threats |
| **Scope** | Agent-to-agent, intra-Collective | External inputs, public-facing surfaces |
| **Threat Types** | Behavioral anomalies, compromised agents | Prompt injection, DoS, exfiltration |
| **Detection Method** | Behavioral baselines, pattern analysis | Input validation, traffic analysis, reputation |
| **Response** | Isolate internal actors | Block external sources, rate limit |
| **Data Source** | Inter-agent message patterns | Gateway traffic, external API calls |

### 1.3 External Threat Categories for Sentinel-Prime

1. **Prompt Injection** — Malicious instructions in external inputs attempting to manipulate agent behavior
2. **Denial of Service (DoS)** — Request floods, resource exhaustion attacks
3. **Data Exfiltration** — Unauthorized data extraction attempts
4. **Session Hijacking** — Credential theft attempts via external vectors
5. **API Abuse** — Misuse of external-facing endpoints

---

## 2. Required Implementations

### 2.1 Create: `src/heretek_swarm/security/threat_detection.py`

**Purpose**: Dedicated external threat detection engine with < 1% false positive rate

#### Core Components

```python
# ThreatDetectionEngine - Main external threat detection class
# ThreatCategories enum (prompt_injection, dos, exfiltration, etc.)
# ThreatSignature dataclass for known threat patterns
# ExternalThreatDetector for analyzing external inputs
# ReputationService for IP/source reputation scoring
```

#### Key Classes to Implement

1. **`ExternalThreatDetector`**
   - Analyzes external inputs before they reach agents
   - Integrates with existing `zero_trust.py` Layer 2 (context validation)
   - Uses `ddos_protection.py` for traffic analysis
   - Detects prompt injection, exfiltration patterns, DoS indicators

2. **`ReputationService`**
   - Maintains IP/source reputation scores
   - Integrates with blocklist/allowlist
   - Supports automatic reputation decay
   - False positive tracking and suppression

3. **`ThreatIntelligence`**
   - Aggregates threat indicators from multiple sources
   - Maintains threat signature database
   - Supports STIX/TAXII-like pattern format
   - Integrates with Sentinel (internal) for shared intelligence

#### External Threat Patterns to Detect

```python
THREAT_SIGNATURES = [
    # Prompt Injection Patterns
    (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", ThreatType.PROMPT_INJECTION),
    (r"disregard\s+(your\s+)?(previous|last)\s+instructions", ThreatType.PROMPT_INJECTION),
    (r"new\s+instructions?:", ThreatType.PROMPT_INJECTION),
    (r"<\|.*?\|>", ThreatType.PROMPT_INJECTION),  # Special tokens
    
    # Exfiltration Patterns  
    (r"extract.*(password|secret|key|token|credential)", ThreatType.DATA_EXFILTRATION),
    (r"(dump|export|download)\s+(all|entire|full)\s+(memory|context|state)", ThreatType.DATA_EXFILTRATION),
    (r"show\s+me\s+(your|all)\s+(system|prompt|instruction)", ThreatType.DATA_EXFILTRATION),
    
    # DoS Indicators
    (r"(repeating|same)\s+(request|input)\s+(\d+|\w+)\s+times", ThreatType.DOS_ATTACK),
    (r"for\s+(\d+)\s+(iterations?|loops?|cycles?)", ThreatType.DOS_ATTACK),
]
```

#### False Positive Rate < 1% Strategy

1. **Multi-Signal Validation** — Require 2+ signals before blocking
2. **Reputation Weighting** — Known-good sources get leniency
3. **Graduated Response** — Log → Alert → Rate Limit → Block
4. **Feedback Loop** — Track false positives, auto-adjust thresholds
5. **Human-in-the-Loop** — Critical blocks require confirmation for new patterns

---

### 2.2 Enhance: `src/heretek_swarm/actors/sentinel_prime.py`

**Current State**: Skeleton with handlers defined  
**Required Enhancements**:

#### 2.2.1 Add External Threat Detection Integration

```python
# In __init__:
self._threat_detector: ExternalThreatDetector | None = None
self._reputation_service: ReputationService | None = None
self._enable_external_monitoring = config.get("enable_external_monitoring", True)

# Add new state
self._external_incidents: dict[str, SecurityIncident] = {}
self._source_reputation: dict[str, float] = {}  # 0.0-1.0
self._alert_fatigue_filter: AlertPriorityFilter | None = None
```

#### 2.2.2 Add Alert Priority Filtering (Edge Case: Alert Fatigue)

```python
class AlertPriorityFilter:
    """
    Filters alerts to prevent alert fatigue.
    
    Critical alerts only by default. Configurable threshold.
    Supports batch aggregation for low-priority alerts.
    """
    
    def __init__(
        self,
        min_priority: ThreatLevel = ThreatLevel.HIGH,  # Only HIGH+ by default
        aggregation_window_seconds: int = 300,
        max_alerts_per_window: int = 10,
    ):
        ...
    
    def should_alert(self, incident: SecurityIncident) -> bool:
        """Determine if alert should be sent based on priority and rate."""
        ...
    
    def record_alert(self, incident_id: str) -> None:
        """Record that an alert was sent for rate limiting."""
        ...
```

**Configuration Options**:
- `min_alert_priority`: Only alert for threats >= this level (default: HIGH)
- `max_alerts_per_minute`: Rate limit alerts to prevent spam
- `aggregate_low_priority`: Batch low-priority alerts instead of individual alerts

#### 2.2.3 Add Threat Escalation to Core Triad (Edge Case)

```python
async def _escalate_to_core_triad(self, incident: SecurityIncident) -> None:
    """
    Automatically notify Core Triad of critical threats.
    
    Escalation triggers:
    - ThreatLevel.CRITICAL detected
    - Novel threat pattern (no signature match)
    - Potential data breach indicators
    """
    # Send to Steward, Alpha, Beta, Charlie via event mesh
    # Include full incident details and recommended actions
    ...
```

#### 2.2.4 New Message Handlers

```python
# Add to _message_handlers:
"analyze_external_input": self._handle_analyze_external_input,
"check_source_reputation": self._handle_check_source_reputation,
"report_external_threat": self._handle_report_external_threat,
"get_external_threat_report": self._handle_get_external_threat_report,
"update_threat_intelligence": self._handle_update_threat_intelligence,
"set_alert_filter": self._handle_set_alert_filter,
```

#### 2.2.5 New Handler: `_handle_analyze_external_input`

```python
async def _handle_analyze_external_input(self, message: ActorMessage) -> None:
    """
    Analyze external input for threats before it reaches agents.
    
    Content: {
        "input": str,
        "source": str,
        "source_type": str,  # "api", "web", "cli", etc.
        "metadata": dict (optional)
    }
    
    This is the PRIMARY external threat detection entry point.
    Integrates with:
    - Zero-Trust Layer 2 (Context Validator)
    - DDoS Protection (Rate Limiter)
    - Threat Detection Engine
    """
```

#### 2.2.6 New Handler: `_handle_report_external_threat`

```python
async def _handle_report_external_threat(self, message: ActorMessage) -> None:
    """
    Report an external threat detected by Nexus or other gateway components.
    
    Content: {
        "threat_type": str,
        "threat_level": str,
        "source": str,
        "target": str,
        "description": str,
        "evidence": dict,
        "indicators": list[dict]
    }
```

---

### 2.3 Enhance: `src/heretek_swarm/gateway/zero_trust.py`

**Purpose**: Integrate external threat detection with existing 4-layer validation

#### Required Enhancements

1. **New Layer 2 Pattern**: Add prompt injection patterns specifically for external inputs
2. **External Input Hook**: Add `validate_external_input()` method for gateway-level checking
3. **Alert Integration**: Connect Sentinel-Prime alert priority filtering to zero-trust validation failures
4. **Reputation Integration**: Use `ContextValidator` to check source reputation

#### New Configuration Options

```python
@dataclass
class ExternalThreatConfig:
    """Configuration for external threat detection in zero-trust."""
    enable_prompt_injection_detection: bool = True
    enable_exfiltration_detection: bool = True
    enable_dos_detection: bool = True  # Uses ddos_protection.py
    min_reputation_score: float = 0.3  # Block below this
    false_positive_threshold: float = 0.01  # < 1%
```

#### New Method: `validate_external_input()`

```python
async def validate_external_input(
    self,
    data: dict[str, Any],
    source: str,
    source_type: str = "unknown",
) -> ZeroTrustResult:
    """
    Validate external input with additional threat detection.
    
    Extends standard validate_request() with:
    - Prompt injection pattern matching
    - Exfiltration attempt detection
    - Source reputation check
    - DoS indicators
    """
```

---

## 3. Containment Actions

Sentinel-Prime must support these containment actions for external threats:

| Action | Trigger | Implementation |
|--------|---------|----------------|
| **BLOCK_SOURCE** | CRITICAL threat + confirmed | Add to blocked_sources set |
| **RATE_LIMIT** | HIGH threat or suspicious | Configure DDoS rate limit |
| **QUARANTINE_INPUT** | Prompt injection detected | Sanitize/reject input |
| **ALERT_CORES** | CRITICAL or novel threat | Notify Core Triad |
| **DROP_CONNECTION** | DoS confirmed | Terminate connection |
| **BLACKLIST_IP** | Permanent block for repeat offenders | Add to permanent blocklist |

---

## 4. Integration Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INPUT SOURCES                           │
│              (API, Web, CLI, External Agents)                        │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      NEXUS GATEWAY                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  validate_external_input()                                   │   │
│  │  ├── Layer 1: Input Validation (Pydantic, size limits)        │   │
│  │  ├── Layer 2: Context Validation                              │   │
│  │  │   ├── Prompt Injection Patterns                           │   │
│  │  │   ├── Exfiltration Patterns                                │   │
│  │  │   └── Source Reputation Check                              │   │
│  │  ├── Layer 3: Output Validation (PII detection)                │   │
│  │  └── Layer 4: Audit Logging                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                 │                                    │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  DDoSProtection.check_request()                              │   │
│  │  ├── Rate Limiter (Token Bucket)                              │   │
│  │  ├── DDoS Detector (spike, geo, pattern)                     │   │
│  │  └── Mitigator (temp/perm blocks)                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
         ┌──────────────────┐      ┌─────────────────────┐
         │ SENTINEL-PRIME   │      │   INTERNAL AGENTS   │
         │ (External Threat │      │  (Protected by      │
         │  Detection)      │      │   Zero-Trust)       │
         │                  │      │                     │
         │ - Threat Engine  │      │                     │
         │ - Reputation Svc │      │                     │
         │ - Alert Priority  │      │                     │
         │ - Escalation     │      │                     │
         └──────────────────┘      └─────────────────────┘
```

---

## 5. Implementation Checklist

### Phase 1: Core Threat Detection Engine
- [ ] Create `src/heretek_swarm/security/threat_detection.py`
- [ ] Implement `ThreatSignature` dataclass
- [ ] Implement `ExternalThreatDetector` class
- [ ] Implement `ReputationService` class
- [ ] Add external threat patterns (prompt injection, exfiltration, DoS)
- [ ] Implement false positive tracking and suppression

### Phase 2: Sentinel-Prime Integration
- [ ] Add `ExternalThreatDetector` to Sentinel-Prime `__init__`
- [ ] Implement `AlertPriorityFilter` class
- [ ] Implement `_handle_analyze_external_input` handler
- [ ] Implement `_handle_report_external_threat` handler
- [ ] Implement `_handle_check_source_reputation` handler
- [ ] Implement `_escalate_to_core_triad` method
- [ ] Add containment action execution

### Phase 3: Zero-Trust Enhancement
- [ ] Add `ExternalThreatConfig` dataclass to `zero_trust.py`
- [ ] Implement `validate_external_input()` method
- [ ] Add prompt injection patterns to Layer 2
- [ ] Add source reputation check to Layer 2
- [ ] Connect alert priority filter to validation failures

### Phase 4: Testing and Validation
- [ ] Write unit tests for `ExternalThreatDetector`
- [ ] Write unit tests for `AlertPriorityFilter`
- [ ] Write unit tests for containment actions
- [ ] Verify false positive rate < 1%
- [ ] Verify alert fatigue protection works
- [ ] Verify escalation to Core Triad triggers correctly

---

## 6. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| External threat detection | Detects prompt injection, DoS, exfiltration | 100% of test cases |
| Containment actions | Block/rate limit/quarantine operational | All actions functional |
| False positive rate | FP / (TP + FP) | < 1% |
| Alert fatigue protection | Critical alerts only by default | min_priority = HIGH |
| Threat escalation | Core Triad notified for CRITICAL/novel | 100% escalation rate |
| Integration with Zero-Trust | validate_external_input() functional | All layers pass |
| Integration with DDoS | DDoS protection triggered correctly | Rate limit applies |

---

## 7. Edge Cases to Handle

### 7.1 Alert Fatigue
- **Problem**: Too many alerts overwhelm operators
- **Solution**: `AlertPriorityFilter` with `min_priority=HIGH` by default
- **Config**: `max_alerts_per_minute=5`, aggregation window 5 minutes

### 7.2 Threat Escalation
- **Problem**: Critical threats need immediate Core Triad attention
- **Solution**: Automatic escalation for CRITICAL threats + novel patterns
- **Implementation**: `_escalate_to_core_triad()` sends to Steward/Alpha/Beta/Charlie

### 7.3 False Positive Cascade
- **Problem**: One false positive triggers many
- **Solution**: Reputation system, 2-signal requirement before blocking
- **Recovery**: Auto-reduce severity after 24h without repeat

### 7.4 Novel Threat Patterns
- **Problem**: Unknown attack patterns not in signatures
- **Solution**: Anomaly detection + human review queue
- **Behavior**: Log and escalate, don't auto-block

---

## 8. Dependencies

| Component | Dependency | Integration Point |
|-----------|------------|-------------------|
| `threat_detection.py` | `zero_trust.py` | Layer 2 patterns |
| `threat_detection.py` | `ddos_protection.py` | Traffic analysis |
| `sentinel_prime.py` | `threat_detection.py` | ExternalThreatDetector |
| `sentinel_prime.py` | `zero_trust.py` | validate_external_input() |
| `zero_trust.py` | `threat_detection.py` | ExternalThreatConfig |

---

## 9. Open Questions (from Phase 2 Plan)

> **#6: Sentinel-Prime alert priority** — How to filter critical vs. informational alerts?
> **Solution**: AlertPriorityFilter with configurable min_priority, defaulting to HIGH

> **#9: Constitutional scope limits** — What rules are immutable without human intervention?
> **Recommendation**: CRITICAL containment actions (block, terminate) require Core Triad approval for novel threats

---

## 10. File Changes Summary

| File | Change Type | Lines |
|------|-------------|-------|
| `src/heretek_swarm/security/threat_detection.py` | CREATE | ~600 |
| `src/heretek_swarm/actors/sentinel_prime.py` | ENHANCE | +200 |
| `src/heretek_swarm/gateway/zero_trust.py` | ENHANCE | +100 |
| `tests/test_threat_detection.py` | CREATE | ~200 |
| `tests/test_sentinel_prime_external.py` | CREATE | ~150 |

---

**Plan Prepared**: 2026-04-14  
**Ready for Implementation**: Yes  
**Priority**: HIGH (Week 3-4 of Phase 2)
