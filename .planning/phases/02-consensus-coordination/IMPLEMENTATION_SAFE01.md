# IMPLEMENTATION_SAFE01: Sentinel Anomaly Response

## Phase 2 Task: SAFE01 - Sentinel Anomaly Detection & Response

**Date:** 2026-04-15  
**Status:** IN PROGRESS  
**Atomic Commit:** `ph2-w1-safe01: implement-sentinel-anomaly-response`

---

## 1. Overview

**Purpose:** Implement foundational behavioral anomaly detection that monitors agent behavior and triggers automated responses within 30 seconds.

**Context from Gate 2:**
- Gate 1: PASSED (7/7 criteria met 2026-04-14)
- Gate 2 Target: Sentinel anomaly detection precision with false positive rate < 1%
- Blocks: SAFE02, SAFE03

**Success Criteria:**
- **Sentinel anomaly detection precision**: False positive rate < 1%
- **Anomaly response**: Automated response within 30 seconds deadline

---

## 2. Architecture

### 2.1 Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SENTINEL ANOMALY RESPONSE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐    ┌─────────────────┐    ┌───────────────┐   │
│  │   Sentinel    │───▶│ safe01_anomaly_  │───▶│ Sentinel-Prime│   │
│  │    Agent      │    │    response      │    │   Escalation  │   │
│  └───────────────┘    └─────────────────┘    └───────────────┘   │
│         │                     │                                     │
│         ▼                     ▼                                     │
│  ┌───────────────┐    ┌─────────────────┐                        │
│  │    immune     │◀───│ behavioral_      │                        │
│  │   system      │    │ baseline         │                        │
│  └───────────────┘    └─────────────────┘                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Module Structure

```
src/heretek_swarm/security/
├── __init__.py                    # Exports
├── anomaly_detection.py           # Existing: BehavioralAnomalyDetector
├── behavioral_baseline.py         # Existing: BehavioralBaseline
├── safe01_anomaly_response.py     # NEW: SAFE01 implementation
└── immune.py                      # Existing: ImmuneResponseBuilding
```

---

## 3. Implementation Details

### 3.1 SAFE01AnomalyResponse Class

**Purpose:** Core anomaly response engine that:
- Tracks agent behavioral profiles
- Performs z-score statistical analysis (3.0σ threshold)
- Triggers automated responses (isolate, suspend, alert, log)
- Achieves < 1% false positive rate
- Meets 30-second response deadline
- Escalates to Sentinel-Prime when needed

### 3.2 Key Data Structures

#### AgentBehaviorProfile
```python
@dataclass
class AgentBehaviorProfile:
    agent_id: str
    created_at: datetime
    last_updated: datetime
    
    # Request rate metrics
    avg_request_rate: float = 0.0
    std_request_rate: float = 0.0
    request_rate_samples: int = 0
    
    # Response time metrics  
    avg_response_time: float = 0.0
    std_response_time: float = 0.0
    response_time_samples: int = 0
    
    # Content metrics
    avg_content_length: float = 0.0
    std_content_length: float = 0.0
    content_length_samples: int = 0
    
    # Validation metrics
    validation_success_rate: float = 1.0
    validation_failure_samples: int = 0
```

#### AnomalyDetectionResult
```python
@dataclass
class AnomalyDetectionResult:
    anomaly_id: str
    agent_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    timestamp: datetime
    z_score: float
    trigger_metric: str
    expected_value: float
    observed_value: float
    confidence: float
    p_value: float | None = None
    is_false_positive: bool = False
    response_status: ResponseStatus = ResponseStatus.PENDING
```

### 3.3 Statistical Analysis

**Z-Score Threshold:** 3.0σ (standard deviations)

**Formula:**
```
z_score = |value - mean| / std
```

**Severity Mapping:**
- z ≥ 5.0 → CRITICAL (isolate)
- z ≥ 4.0 → HIGH (suspend)
- z ≥ 3.0 → MEDIUM (alert)

### 3.4 Response Actions

| Severity | Action   | Execution Time Target |
|----------|----------|-----------------------|
| CRITICAL | isolate  | < 100ms               |
| HIGH     | suspend  | < 500ms               |
| MEDIUM   | alert    | < 1s                  |
| LOW      | log      | < 1s                  |

### 3.5 False Positive Rate Control

**Target:** < 1% false positive rate

**Strategies:**
1. **Adaptive thresholds:** After 3+ FPs for an agent, increase threshold
2. **Multi-signal correlation:** Require 2+ metrics to exceed threshold
3. **Confidence weighting:** Only act on high-confidence detections
4. **Rate limiting:** Max 10 automated responses/minute to prevent cascade
5. **Cooldown periods:** 5-minute cooldown after FP reporting

---

## 4. TDD Approach

### 4.1 RED Phase: Test First

**Test:** `test_sentinel_false_positive_rate_below_1_percent()`

```python
@pytest.mark.asyncio
async def test_sentinel_false_positive_rate_below_1_percent():
    """
    Test that false positive rate is maintained below 1%.
    
    Strategy:
    1. Establish baseline with 1000 normal samples
    2. Inject 100 anomalies (50 true, 50 false)
    3. Report FPs
    4. Verify precision >= 0.99
    """
    # Implementation in test file
```

### 4.2 GREEN Phase: Minimal Implementation

Implement behavioral profiling with:
- Welford's online algorithm for running statistics
- Z-score calculation with configurable threshold
- Multi-metric correlation

### 4.3 REFACTOR Phase

Add:
- Adaptive threshold adjustment based on FP history
- Multi-signal correlation for higher precision
- Sentinel-Prime escalation for backup monitoring

---

## 5. Integration with Existing Code

### 5.1 Reuses

- `BehavioralAnomalyDetector` from `anomaly_detection.py`
- `BehavioralBaseline` from `behavioral_baseline.py`
- `ImmuneResponseBuilding` from `immune.py`
- `SentinelAgent` from `sentinel.py`

### 5.2 Extensions

- **`safe01_anomaly_response.py`:** Standalone module for SAFE01-specific logic
- **Enhanced profile tracking:** Multi-dimensional behavioral profiles
- **Precision monitoring:** Real-time FP rate tracking

---

## 6. Files to Create/Modify

### 6.1 New Files

| File | Purpose |
|------|---------|
| `tests/test_security/test_safe01_sentinel_anomaly_response.py` | SAFE01 test suite |
| `src/heretek_swarm/security/safe01_anomaly_response.py` | SAFE01 implementation |

### 6.2 Modified Files

| File | Changes |
|------|---------|
| `src/heretek_swarm/security/__init__.py` | Add exports |
| `src/heretek_swarm/actors/sentinel.py` | Integration with SAFE01 |

---

## 7. Verification

### 7.1 Test Requirements

- `test_sentinel_false_positive_rate_below_1_percent()` - RED/GREEN
- `test_anomaly_response_within_30_seconds()` - Response deadline
- `test_adaptive_threshold_after_fp()` - FP rate control
- `test_multi_signal_correlation()` - Precision enhancement
- `test_sentinel_prime_escalation()` - Backup monitoring

### 7.2 Verification Commands

```bash
# Run SAFE01 tests
pytest tests/test_security/test_safe01_sentinel_anomaly_response.py -v

# Run full security test suite
pytest tests/security/ -v

# Run linting
ruff check src/heretek_swarm/security/

# Run type checking
mypy src/heretek_swarm/security/
```

---

## 8. Dependencies

- **Blocks:** SAFE02, SAFE03
- **Requires:** Gate 1 completion
- **Required by:** Phase 2 Gate 2 verification

---

## 9. Acceptance Criteria

- [ ] False positive rate < 1% (precision > 99%)
- [ ] Automated response within 30 seconds
- [ ] Z-score threshold: 3.0σ
- [ ] Response actions: isolate, suspend, alert, log
- [ ] Sentinel-Prime escalation for backup monitoring
- [ ] Rate limiting to prevent FP cascade
- [ ] Test coverage for all critical paths
