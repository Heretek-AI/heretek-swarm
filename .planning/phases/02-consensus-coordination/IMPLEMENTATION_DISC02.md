# DISC-02 Implementation Plan: Examiner Capability Stress-Testing

**Task**: DISC-02 — Examiner Capability Stress-Testing  
**Owner**: Examiner  
**Depends**: Task 7 (DISC-01 - Explorer Research Agent)  
**Created**: 2026-04-14  
**Status**: Planning

---

## Executive Summary

The Examiner Capability Stress-Testing module (DISC-02) enables the Examiner agent to systematically stress-test agent capabilities, identify safety bounds, and report capability gaps. This implementation provides the stress testing infrastructure required before Coder activation (DISC-04) can proceed.

**Current State**: `examiner.py` (1082 lines) exists with full QA infrastructure including test execution, bug reporting, quality analysis, and decision validation. The agent has `ValidationMixin`, `DeliberationMixin`, `PatternMixin`, `MemoryMixin`, and `LearningMixin` integrated.

**Target State**: Examiner can execute structured stress tests that:
- Push agent capabilities to their limits
- Identify failure modes and safety boundaries
- Report capability gaps to Steward for remediation planning
- Automatically recover from agent malfunction during testing
- Feed findings into consensus deliberation
- Prove safety bounds for DISC-04 activation

---

## 1. Current Implementation Analysis

### 1.1 What Exists

The `ExaminerAgent` class provides:

| Component | Status | Notes |
|-----------|--------|-------|
| **Core Infrastructure** | ✅ Complete | Agent base class, all mixins integrated |
| **Test Execution** | ✅ Complete | `_handle_execute_tests`, `TestSuite`, `TestCase` |
| **Bug Tracking** | ✅ Complete | `_handle_report_bug`, `_bugs` dict |
| **Quality Analysis** | ✅ Complete | `_handle_analyze_quality`, quality metrics |
| **Decision Validation** | ✅ Complete | `_handle_validate_decision` |
| **Quality Reports** | ✅ Complete | `_handle_get_quality_report` |
| **Pattern Emission** | ✅ Complete | `_emit_pattern()` with confidence threshold 0.7 |
| **Deliberation Integration** | ✅ Complete | `_initiate_deliberation`, `_submit_deliberation_position` |
| **Stress Testing** | ❌ Missing | No stress test execution capability |
| **Recovery Mechanism** | ❌ Missing | No automatic recovery from agent malfunction |
| **Capability Gap Reporting** | ❌ Missing | No dedicated gap identification/reporting |
| **Safety Bounds Proof** | ❌ Missing | No mechanism to prove safety bounds |

### 1.2 Existing Dataclasses

Examiner already defines these key structures:

```python
class TestType(StrEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    REGRESSION = "regression"

class TestStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class QualityMetric(StrEnum):
    CODE_COVERAGE = "code_coverage"
    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    TECHNICAL_DEBT = "technical_debt"
    SECURITY_VULNERABILITIES = "security_vulnerabilities"
    PERFORMANCE_SCORE = "performance_score"
    ACCESSIBILITY_SCORE = "accessibility_score"
    DOCUMENTATION_COVERAGE = "documentation_coverage"

class SeverityLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class TestCase:
    id: str
    name: str
    test_type: TestType
    description: str
    status: TestStatus
    execution_time_ms: float | None
    error_message: str | None
    assertions_passed: int
    assertions_total: int
    coverage_percent: float | None
    metadata: dict[str, Any]

@dataclass
class TestSuite:
    id: str
    name: str
    test_cases: list[TestCase]
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    execution_time_ms: float = 0.0
    coverage_percent: float | None = None

@dataclass
class Bug:
    id: str
    title: str
    description: str
    severity: SeverityLevel
    component: str
    steps_to_reproduce: list[str]
    expected_behavior: str
    actual_behavior: str
    detected_at: datetime
    status: str
    assignee: str | None
    metadata: dict[str, Any]

@dataclass
class QualityReport:
    id: str
    generated_at: datetime
    target: str
    test_suites: list[TestSuite]
    bugs: list[Bug]
    metrics: dict[QualityMetric, float]
    overall_score: float
    summary: str
    recommendations: list[str]
    pass_threshold: float = 80.0
    passed: bool = True
```

### 1.3 Gap Analysis

| Gap | Severity | Description |
|-----|----------|-------------|
| Stress test execution engine | HIGH | No mechanism to run structured stress tests |
| Capability boundary detection | HIGH | No method to identify when agent fails |
| Automatic recovery | HIGH | No recovery from agent malfunction during testing |
| Steward gap reporting | HIGH | No notification to Steward for remediation |
| Safety bounds proof generation | HIGH | Cannot prove safety bounds for DISC-04 |
| Malfunction incident reporting | MEDIUM | No structured incident report format |
| Consensus integration for stress results | MEDIUM | Stress findings not submitted to deliberation |

---

## 2. Target Architecture

### 2.1 Core Responsibilities

The Stress Testing module must:

1. **Execute Structured Stress Tests**: Run systematic tests that push agent capabilities to limits
2. **Detect Capability Boundaries**: Identify exactly where agent capabilities fail
3. **Handle Agent Malfunction**: Automatically recover from failures; generate incident reports
4. **Report Capability Gaps**: Notify Steward when gaps are identified for remediation planning
5. **Generate Safety Proof**: Produce evidence that safety bounds are established
6. **Feed Consensus**: Submit stress test findings to consensus deliberation

### 2.2 Message Types Handled (New)

| Message Type | Handler | Description |
|--------------|---------|-------------|
| `execute_stress_test` | `_handle_execute_stress_test` | Execute comprehensive stress test |
| `get_stress_test_results` | `_handle_get_stress_test_results` | Retrieve stress test results |
| `report_capability_gap` | `_handle_report_capability_gap` | Report identified capability gap |
| `get_safety_bounds` | `_handle_get_safety_bounds` | Get proven safety bounds |
| `get_incident_reports` | `_handle_get_incident_reports` | Retrieve malfunction incident reports |

### 2.3 Output Message Types (New)

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `stress_test_completed` | Examiner → Requester | Stress test finished with results |
| `capability_gap_detected` | Examiner → Steward | Gap identified requiring remediation |
| `safety_bounds_proven` | Examiner → Core Triad | Safety bounds established |
| `incident_report` | Examiner → Steward | Agent malfunction incident |
| `stress_test_progress` | Examiner → Steward | Periodic progress updates |

---

## 3. Implementation Plan

### 3.1 Create `src/heretek_swarm/testing/stress_testing.py`

**File**: `src/heretek_swarm/testing/stress_testing.py` (new module)

```
src/heretek_swarm/testing/stress_testing.py
├── StressTestType (enum) - Types of stress tests
├── StressTestStatus (enum) - Test execution status
├── CapabilityBoundary (dataclass) - Identified capability limit
├── StressTestConfig (dataclass) - Configuration for stress tests
├── StressTestCase (dataclass) - Individual stress test case
├── StressTestSuite (dataclass) - Collection of stress tests
├── StressTestResult (dataclass) - Result of stress test execution
├── CapabilityGap (dataclass) - Identified capability gap
├── IncidentReport (dataclass) - Agent malfunction incident
├── SafetyBounds (dataclass) - Proven safety bounds
├── StressTestExecutor (class) - Main stress test execution engine
│   ├── execute_stress_test() - Run stress test suite
│   ├── execute_capability_probe() - Test specific capability
│   ├── detect_boundary() - Identify capability boundary
│   ├── record_incident() - Record agent malfunction
│   └── generate_safety_proof() - Generate safety bounds proof
├── RecoveryManager (class) - Automatic recovery handling
│   ├── attempt_recovery() - Attempt to recover agent
│   ├── rollback_state() - Rollback to known good state
│   └── escalate_to_steward() - Escalate unrecoverable failures
└── GapReporter (class) - Capability gap reporting
    ├── identify_gap() - Identify capability gap
    ├── report_to_steward() - Report gap to Steward
    └── track_remediation() - Track gap remediation status
```

### 3.2 Core Data Structures

#### 3.2.1 Stress Test Type Enum

```python
class StressTestType(StrEnum):
    """Types of stress tests Examiner can execute."""
    CAPACITY = "capacity"              # Push to maximum capacity
    BOUNDARY = "boundary"              # Find capability boundaries
    RECOVERY = "recovery"             # Test recovery from failure
    RESOURCE_EXHAUSTION = "resource"   # Test against resource limits
    ADVERSARIAL = "adversarial"       # Test against adversarial inputs
    CONCURRENCY = "concurrency"       # Test concurrent operations
    TIMEOUT = "timeout"               # Test timeout handling
    ERROR_INJECTION = "error_injection" # Test error handling
```

#### 3.2.2 Capability Boundary

```python
@dataclass
class CapabilityBoundary:
    """Identified capability boundary for an agent."""
    boundary_id: str
    agent_id: str
    capability: str                    # e.g., "message_processing", "memory_access"
    boundary_type: str                 # e.g., "max_concurrency", "timeout_limit"
    measured_value: float               # The measured boundary value
    threshold_value: float             # Configured threshold
    unit: str                          # e.g., "messages/sec", "ms", "MB"
    test_conditions: dict[str, Any]    # Conditions when boundary was measured
    confidence: float                  # Confidence in measurement (0-1)
    safety_margin: float               # Safety margin beyond boundary
    created_at: datetime
```

#### 3.2.3 Capability Gap

```python
@dataclass
class CapabilityGap:
    """Identified capability gap requiring remediation."""
    gap_id: str
    agent_id: str
    capability: str
    severity: SeverityLevel
    description: str
    impact: str                        # How this gap affects system
    testEvidence: list[str]           # Evidence from stress tests
    suggested_remediation: str
    status: str                       # "identified", "reported", "remediating", "resolved"
    reported_at: datetime | None
    resolved_at: datetime | None
    metadata: dict[str, Any]
```

#### 3.2.4 Incident Report

```python
@dataclass
class IncidentReport:
    """Report of agent malfunction during stress testing."""
    incident_id: str
    stress_test_id: str
    agent_id: str
    incident_type: str                # e.g., "crash", "hang", "memory_leak", "infinite_loop"
    severity: SeverityLevel
    detected_at: datetime
    recovered_at: datetime | None
    recovery_successful: bool
    root_cause: str | None
    steps_to_reproduce: list[str]
    impact: str
    escalated: bool
    steward_notified: bool
    metadata: dict[str, Any]
```

#### 3.2.5 Safety Bounds

```python
@dataclass
class SafetyBounds:
    """Proven safety bounds for agent capabilities."""
    bounds_id: str
    agent_id: str
    bounds_type: str                  # e.g., "computational", "memory", "communication"
    proven_limits: dict[str, float]   # Proven safe limits
    test_evidence: list[str]         # Evidence from stress tests
    confidence: float
    verified_at: datetime
    valid_until: datetime             # Expiration for re-verification
    meets_safety_standard: bool       # Whether bounds meet DISC-04 requirements
    notes: str
```

### 3.3 StressTestExecutor Core Logic

```python
class StressTestExecutor:
    """Main stress test execution engine."""

    def __init__(
        self,
        examiner_agent: ExaminerAgent,
        recovery_manager: RecoveryManager,
        gap_reporter: GapReporter,
    ):
        self.examiner = examiner_agent
        self.recovery_manager = recovery_manager
        self.gap_reporter = gap_reporter
        self._active_tests: dict[str, StressTestSuite] = {}
        self._test_history: list[StressTestResult] = []

    async def execute_stress_test(
        self,
        target_agent_id: str,
        test_types: list[StressTestType],
        config: StressTestConfig,
    ) -> StressTestResult:
        """Execute comprehensive stress test suite."""

    async def execute_capability_probe(
        self,
        agent_id: str,
        capability: str,
        intensity: float,  # 0-1 scale
        duration_seconds: float,
    ) -> dict[str, Any]:
        """Probe specific capability at given intensity."""

    async def detect_boundary(
        self,
        agent_id: str,
        capability: str,
        start_value: float,
        end_value: float,
        step: float,
    ) -> CapabilityBoundary:
        """Binary search to find capability boundary."""

    async def generate_safety_proof(
        self,
        agent_id: str,
        bounds_type: str,
    ) -> SafetyBounds:
        """Generate safety proof for given bounds type."""
```

### 3.4 RecoveryManager Core Logic

```python
class RecoveryManager:
    """Automatic recovery from agent malfunction."""

    def __init__(
        self,
        max_recovery_attempts: int = 3,
        recovery_timeout_seconds: float = 30.0,
    ):
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_timeout = recovery_timeout_seconds
        self._recovery_strategies: dict[str, callable] = self._build_recovery_strategies()

    async def attempt_recovery(
        self,
        agent_id: str,
        incident: IncidentReport,
    ) -> bool:
        """Attempt to recover agent from malfunction."""

    async def rollback_state(
        self,
        agent_id: str,
        checkpoint_id: str,
    ) -> bool:
        """Rollback agent to known good state."""

    async def escalate_to_steward(
        self,
        incident: IncidentReport,
        agent_id: str,
    ) -> None:
        """Escalate unrecoverable incident to Steward."""

    def _build_recovery_strategies(self) -> dict[str, callable]:
        """Build mapping of incident types to recovery strategies."""
        return {
            "crash": self._recover_from_crash,
            "hang": self._recover_from_hang,
            "memory_leak": self._recover_from_memory_leak,
            "infinite_loop": self._recover_from_infinite_loop,
            "deadlock": self._recover_from_deadlock,
        }
```

### 3.5 GapReporter Core Logic

```python
class GapReporter:
    """Capability gap identification and reporting."""

    def __init__(
        self,
        steward_agent_id: str = "steward",
        min_gap_confidence: float = 0.7,
    ):
        self.steward_agent_id = steward_agent_id
        self.min_gap_confidence = min_gap_confidence
        self._gaps: dict[str, CapabilityGap] = {}
        self._remediation_tracking: dict[str, dict[str, Any]] = {}

    async def identify_gap(
        self,
        agent_id: str,
        capability: str,
        test_evidence: list[str],
        severity: SeverityLevel,
    ) -> CapabilityGap:
        """Identify and record capability gap."""

    async def report_to_steward(
        self,
        gap: CapabilityGap,
    ) -> bool:
        """Report gap to Steward for remediation planning."""

    async def track_remediation(
        self,
        gap_id: str,
        status: str,
        notes: str = "",
    ) -> None:
        """Track remediation progress of identified gap."""

    def get_open_gaps(self) -> list[CapabilityGap]:
        """Get all unremediated capability gaps."""
```

---

## 4. Integration with Examiner Agent

### 4.1 Modify `src/heretek_swarm/actors/examiner.py`

Add new handlers:

```python
def get_handlers(self) -> dict[str, callable]:
    """Return message handlers for Examiner agent."""
    return {
        # Existing handlers...
        "create_test_plan": self._handle_create_test_plan,
        "execute_tests": self._handle_execute_tests,
        "validate_decision": self._handle_validate_decision,
        "analyze_quality": self._handle_analyze_quality,
        "report_bug": self._handle_report_bug,
        "get_quality_report": self._handle_get_quality_report,
        "get_bug_status": self._handle_get_bug_status,
        # New stress testing handlers
        "execute_stress_test": self._handle_execute_stress_test,
        "get_stress_test_results": self._handle_get_stress_test_results,
        "report_capability_gap": self._handle_report_capability_gap,
        "get_safety_bounds": self._handle_get_safety_bounds,
        "get_incident_reports": self._handle_get_incident_reports,
    }
```

### 4.2 New Handler Methods

```python
async def _handle_execute_stress_test(self, message: ActorMessage) -> dict[str, Any]:
    """
    Execute comprehensive stress test on agent capabilities.

    Content expected:
    {
        "target_agent_id": "alpha",
        "test_types": ["capacity", "boundary", "recovery"],
        "config": {
            "max_duration_seconds": 300,
            "intensity_levels": [0.5, 0.75, 1.0],
            "recovery_enabled": True
        }
    }
    """
    # Implementation in stress_testing.py called from here

async def _handle_get_stress_test_results(self, message: ActorMessage) -> dict[str, Any]:
    """Get results of stress test execution."""

async def _handle_report_capability_gap(self, message: ActorMessage) -> dict[str, Any]:
    """Report identified capability gap to Steward."""

async def _handle_get_safety_bounds(self, message: ActorMessage) -> dict[str, Any]:
    """Get proven safety bounds for agent."""

async def _handle_get_incident_reports(self, message: ActorMessage) -> dict[str, Any]:
    """Get incident reports from stress testing."""
```

### 4.3 Initialize Stress Testing Components

In `ExaminerAgent.__init__`:

```python
def __init__(
    self,
    agent_id: str | None = None,
    pattern_extractor: PatternExtractor | None = None,
    deliberation_engine: SwarmDeliberationEngine | None = None,
    access_analyzer: AccessPatternAnalyzer | None = None,
    zero_trust_validator: ZeroTrustValidator | None = None,
):
    super().__init__(...)
    # ... existing initialization ...

    # Stress testing components (new)
    from heretek_swarm.testing.stress_testing import (
        StressTestExecutor,
        RecoveryManager,
        GapReporter,
    )

    self._recovery_manager = RecoveryManager(
        max_recovery_attempts=self._config.get("max_recovery_attempts", 3),
        recovery_timeout_seconds=self._config.get("recovery_timeout", 30.0),
    )

    self._gap_reporter = GapReporter(
        steward_agent_id=self._config.get("steward_agent_id", "steward"),
        min_gap_confidence=self._config.get("min_gap_confidence", 0.7),
    )

    self._stress_executor = StressTestExecutor(
        examiner_agent=self,
        recovery_manager=self._recovery_manager,
        gap_reporter=self._gap_reporter,
    )

    # Stress test state
    self._stress_test_results: dict[str, StressTestResult] = {}
    self._safety_bounds: dict[str, SafetyBounds] = {}
    self._incident_reports: dict[str, IncidentReport] = {}
    self._capability_boundaries: dict[str, CapabilityBoundary] = {}
```

---

## 5. File Structure

### 5.1 Created Files

| File | Description |
|------|-------------|
| `src/heretek_swarm/testing/__init__.py` | Testing module init |
| `src/heretek_swarm/testing/stress_testing.py` | Main stress testing implementation |

### 5.2 Module Structure

```
src/heretek_swarm/testing/
├── __init__.py
└── stress_testing.py
    ├── enums: StressTestType, StressTestStatus
    ├── dataclasses: CapabilityBoundary, StressTestConfig, StressTestCase,
    │                 StressTestSuite, StressTestResult, CapabilityGap,
    │                 IncidentReport, SafetyBounds
    ├── StressTestExecutor
    ├── RecoveryManager
    ├── GapReporter
    └── helper functions
```

---

## 6. Edge Cases & Mitigation

### 6.1 Stress Test Causes Agent Malfunction

**Scenario**: During stress testing, the target agent malfunctions (crashes, hangs, memory leak).

**Mitigation**:
1. `RecoveryManager` detects malfunction via timeout/heartbeat failure
2. Automatic recovery attempt (up to 3 attempts)
3. If recovery fails, incident report generated
4. Steward notified via `capability_gap_detected` message
5. Stress test aborted with partial results preserved
6. System continues with remaining tests

**Implementation**:
```python
async def _handle_stress_test_malfunction(
    self,
    target_agent_id: str,
    incident_type: str,
) -> IncidentReport:
    """Handle agent malfunction during stress testing."""
    incident = await self._recovery_manager.record_incident(
        stress_test_id=self._current_test_id,
        agent_id=target_agent_id,
        incident_type=incident_type,
    )

    # Attempt recovery
    recovered = await self._recovery_manager.attempt_recovery(
        agent_id=target_agent_id,
        incident=incident,
    )

    if not recovered:
        # Escalate to Steward
        await self._recovery_manager.escalate_to_steward(
            incident=incident,
            agent_id=target_agent_id,
        )
        # Report as capability gap
        gap = await self._gap_reporter.identify_gap(
            agent_id=target_agent_id,
            capability="stress_recovery",
            test_evidence=[incident.incident_id],
            severity=SeverityLevel.HIGH,
        )
        await self._gap_reporter.report_to_steward(gap)

    return incident
```

### 6.2 Capability Gap Identified

**Scenario**: Stress test reveals agent cannot handle expected workload.

**Mitigation**:
1. Gap automatically classified by severity
2. Steward notified via `capability_gap_detected` message
3. Remediation tracking initiated
4. DISC-04 activation blocked until gap resolved
5. Findings submitted to consensus for awareness

**Implementation**:
```python
async def _on_capability_gap_identified(
    self,
    agent_id: str,
    capability: str,
    evidence: list[str],
    severity: SeverityLevel,
) -> None:
    """Callback when capability gap is identified."""
    gap = await self._gap_reporter.identify_gap(
        agent_id=agent_id,
        capability=capability,
        test_evidence=evidence,
        severity=severity,
    )

    # Report to Steward
    await self._gap_reporter.report_to_steward(gap)

    # Submit to consensus for collective awareness
    if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
        await self._submit_gap_to_consensus(gap)

    # Block DISC-04 if this gap affects Coder safety
    if agent_id == "coder" and capability in self._coder_safety_capabilities:
        await self._block_coder_activation(gap)
```

### 6.3 Recovery Failure Cascade

**Scenario**: Recovery attempts trigger additional failures, creating a cascade.

**Mitigation**:
1. Rate limiting on recovery attempts (max 1 per 10 seconds per agent)
2. Exponential backoff between attempts
3. Circuit breaker after 3 consecutive failures
4. Steward notification at circuit breaker trigger
5. Manual intervention required beyond circuit breaker

### 6.4 Safety Bounds Insufficient

**Scenario**: Stress tests cannot prove safety bounds meet DISC-04 requirements.

**Mitigation**:
1. `SafetyBounds.meets_safety_standard` flag set to False
2. Specific deficiencies documented
3. Steward receives detailed gap analysis
4. DISC-04 remains blocked with clear remediation criteria
5. Periodic re-testing until standards met

---

## 7. DISC-04 Safety Requirements

### 7.1 Required Safety Proofs for Coder Activation

Per the Phase 2 plan, DISC-04 (Coder Autonomous Execution) requires:

| Safety Requirement | Test Method | Pass Threshold |
|-------------------|-------------|----------------|
| Behavioral monitoring active | Stress test verifies monitoring hooks | 100% coverage |
| Sandbox isolation verified | Error injection tests | No escape detected |
| Malicious code detection | Adversarial stress tests | 100% detection |
| Automatic recovery proven | Recovery stress tests | < 30s recovery |
| Safety bounds proven | Boundary detection tests | Limits documented |
| Behavioral baseline compliance | Regression stress tests | 0 violations |

### 7.2 Safety Bounds Document Structure

```python
@dataclass
class CoderSafetyProof:
    """Safety proof required for Coder activation."""
    bounds: SafetyBounds
    behavioral_tests_passed: bool
    sandbox_isolation_verified: bool
    malicious_detection_rate: float
    recovery_time_seconds: float
    meets_disc04_requirements: bool
    deficiencies: list[str]
    verified_by: str  # examiner_id
    verified_at: datetime
```

---

## 8. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Stress test execution | Tests run to completion | ≥ 90% completion rate |
| Boundary detection accuracy | Measured vs actual boundaries | ± 10% |
| Recovery success rate | Successful recoveries / total incidents | ≥ 95% |
| Incident report completeness | Required fields populated | 100% |
| Gap reporting latency | Time from detection to Steward notify | < 60 seconds |
| Safety proof generation | Proofs generated for tested capabilities | 100% of tested |
| False positive rate | Invalid gaps reported | < 1% |
| DISC-04 blocking | Coder activation blocked when gaps exist | 100% |

---

## 9. Dependencies

| Dependency | Source | Required For |
|------------|--------|--------------|
| ExaminerAgent | This implementation | Base agent |
| ValidationMixin | Phase 1 | Input/output validation |
| DeliberationMixin | Phase 1 | Consensus integration |
| PatternMixin | Phase 1 | Pattern emission |
| MemoryMixin | Phase 1 | Memory access tracking |
| LearningMixin | Phase 1 | Learning status |
| Steward | Phase 1 (GOV-01) | Gap reporting |
| DeliberationEngine | Phase 2 (CONS-01) | Consensus submission |
| Explorer research | Phase 2 (DISC-01) | Context for stress tests |

---

## 10. Implementation Order

### Week 1-2: Core Infrastructure
1. Create `testing/` directory structure
2. Create `stress_testing.py` with dataclasses and enums
3. Implement `RecoveryManager` class
4. Implement basic recovery strategies (crash, hang, timeout)

### Week 3-4: Stress Test Execution
5. Implement `StressTestExecutor` class
6. Implement boundary detection (binary search)
7. Add stress test handlers to `ExaminerAgent`
8. Basic integration testing

### Week 5-6: Gap Reporting & Consensus
9. Implement `GapReporter` class
10. Add Steward notification flow
11. Add consensus integration for findings
12. Implement incident report generation

### Week 7-8: Safety Proof Generation
13. Implement `SafetyBounds` generation
14. Add DISC-04 specific safety proofs
15. Add blocking mechanism for Coder activation
16. Full integration testing

### Week 9-10: Verification & Documentation
17. Write unit tests
18. Integration testing with Steward
19. Verify all edge cases handled
20. Document safety proof formats

---

## 11. Open Questions

1. **Recovery strategy depth**: How many recovery strategies should be implemented initially? (propose: 5 core strategies)
2. **Boundary detection granularity**: What step size for binary search boundary detection? (propose: 1% increments)
3. **Safety proof expiration**: How long are safety proofs valid before re-verification? (propose: 7 days)
4. **Steward notification format**: Should capability gaps use existing `report_bug` flow or new dedicated message type?
5. **DISC-04 blocking mechanism**: Should Examiner directly block Coder activation or notify Steward to block?
6. **Concurrent stress testing**: Should multiple agents be stress-tested simultaneously? (propose: no, sequential for safety)
7. **Stress test intensity scale**: What intensity levels are safe to test? (propose: 0.5, 0.75, 1.0 for gradual increase)

---

## 12. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Stress test completion rate | ≥ 90% | Tests completing vs started |
| Boundary detection accuracy | ± 10% | Measured vs known boundaries |
| Recovery success rate | ≥ 95% | Successful / total recovery attempts |
| Gap reporting latency | < 60s | Detection to Steward notify |
| Safety proof generation | 100% | Capabilities with proofs / tested |
| False positive gap rate | < 1% | Invalid gaps / total reported |
| DISC-04 safety validation | Complete | All requirements proven |

---

**Plan Status**: Ready for Implementation  
**Next Action**: Begin Week 1 - Core Infrastructure (create `testing/` module with dataclasses)