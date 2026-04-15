# DISC-01 Implementation Plan: Explorer Research Agent

**Task**: DISC-01 — Explorer Research Agent  
**Owner**: Explorer  
**Depends**: Phase 1 (Agent base class, health reporting)  
**Created**: 2026-04-14  
**Status**: Planning

---

## Executive Summary

The Explorer Research Agent (DISC-01) provides autonomous topic research, pattern detection, and reporting capabilities for the collective. This implementation plan details the enhancements required to move from the current stub implementation to a production-ready research agent with full consensus integration.

**Current State**: `explorer.py` exists with basic monitoring infrastructure, opportunity/anomaly tracking, and placeholder methods for source checking and pattern analysis.

**Target State**: Full autonomous research capability with:
- Topic-based deep research workflows
- Pattern detection and emission to collective learning
- Contradictory findings resolution via Beta validation and deliberation
- Configurable depth limits with Steward oversight
- Consensus integration for research findings

---

## 1. Current Implementation Analysis

### 1.1 What Exists

The `ExplorerAgent` class (881 lines) in `src/heretek_swarm/actors/explorer.py` provides:

| Component | Status | Notes |
|-----------|--------|-------|
| **Core Infrastructure** | ✅ Complete | Agent base class, mixin integration |
| **Opportunity Tracking** | ✅ Complete | `_opportunities` dict, LRU eviction |
| **Anomaly Detection** | ✅ Complete | `_anomalies` dict, severity-based eviction |
| **Source Monitoring** | 🟡 Stub | `_check_source()` is placeholder |
| **Pattern Analysis** | ❌ Missing | `_analyze_findings()` is placeholder |
| **Research Workflows** | ❌ Missing | No topic-based research handling |
| **Consensus Integration** | 🟡 Partial | Has `_active_deliberations`, `_pattern_emitted` |
| **Depth Limits** | ❌ Missing | No research scope controls |
| **Steward Oversight** | ❌ Missing | No reporting to Steward |

### 1.2 Available Mixins

Explorer already extends these mixins:

```python
class ExplorerAgent(
    ValidationMixin,      # Input/output validation
    DeliberationMixin,   # Consensus participation
    PatternMixin,         # Pattern emission
    MemoryMixin,          # Memory access tracking
    LearningMixin,        # Learning status reporting
    AgentActor
):
```

### 1.3 Gap Analysis

| Gap | Severity | Description |
|-----|----------|-------------|
| Research topic handling | HIGH | No handler for `research_topic` message type |
| Deep research workflow | HIGH | No multi-step research orchestration |
| Pattern emission integration | HIGH | `_emit_pattern()` not called |
| Contradiction resolution | MEDIUM | No Beta validation request flow |
| Depth limits | MEDIUM | No configurable research depth |
| Steward reporting | MEDIUM | No progress/oversight messages to Steward |
| Knowledge access | MEDIUM | No integration with `UnifiedKnowledgeAccess` |
| Research result caching | LOW | No research memoization |

---

## 2. Target Architecture

### 2.1 Core Responsibilities

The Explorer Agent must:

1. **Autonomous Research**: Accept research topics and conduct deep research without human intervention
2. **Pattern Detection**: Identify patterns in research findings and emit them to collective learning
3. **Consensus Integration**: Submit findings to consensus when required, handle contradictory findings
4. **Reporting**: Generate intelligence reports and notify relevant agents of significant findings
5. **Scope Control**: Enforce configurable depth limits; accept Steward oversight

### 2.2 Message Types Handled

| Message Type | Handler | Description |
|--------------|---------|-------------|
| `research_topic` | `_handle_research_topic` | Initiate deep research on a topic |
| `report_opportunity` | existing | Report discovered opportunity |
| `report_anomaly` | existing | Report detected anomaly |
| `get_opportunities` | existing | Query tracked opportunities |
| `get_anomalies` | existing | Query tracked anomalies |
| `generate_report` | existing | Generate intelligence report |
| `get_monitoring_status` | existing | Get Explorer status |
| `start_monitoring` | existing | Start monitoring a source |
| `stop_monitoring` | existing | Stop monitoring a source |

### 2.3 New Message Types Required

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `research_findings` | Explorer → Requester | Deliver completed research |
| `research_progress` | Explorer → Steward | Periodic progress updates |
| `pattern_detected` | Explorer → Collective | Emit detected pattern |
| `contradiction_detected` | Explorer → Beta | Request validation |
| `validation_request` | Explorer → Beta | Request Beta validation |
| `deliberation_request` | Explorer → Steward | Request consensus on findings |

---

## 3. Implementation Plan

### 3.1 Phase 1: Core Research Infrastructure

**Files Modified**: `src/heretek_swarm/actors/explorer.py`  
**Files Created**: `src/heretek_swarm/knowledge/research.py`

#### 3.1.1 Research Query Model

Create `src/heretek_swarm/knowledge/research.py` with:

```python
@dataclass
class ResearchQuery:
    """Research query specification."""
    query_id: str
    topic: str
    depth: ResearchDepth  # shallow, medium, deep
    focus_areas: list[str]
    max_sources: int
    time_limit_seconds: float
    confidence_threshold: float

@dataclass 
class ResearchFinding:
    """Individual research finding."""
    finding_id: str
    claim: str
    evidence: list[Evidence]
    confidence: float
    source: str
    contradicts: list[str]  # IDs of contradictory findings
    metadata: dict[str, Any]

@dataclass
class ResearchResult:
    """Complete research result."""
    query_id: str
    topic: str
    findings: list[ResearchFinding]
    summary: str
    confidence: float
    patterns_detected: list[Pattern]
    research_time_seconds: float
    depth_achieved: ResearchDepth
    contradictions_resolved: bool
```

#### 3.1.2 Research State Machine

Implement research workflow state machine:

```
IDLE → RESEARCHING → ANALYZING → DELIVERING → IDLE
                     ↓
              CONTRADICTION → VALIDATING → DELIVERING
```

States:
- `IDLE`: Waiting for research requests
- `RESEARCHING`: Actively querying sources
- `ANALYZING`: Processing and synthesizing findings
- `CONTRADICTION`: Contradictory findings detected, awaiting resolution
- `VALIDATING`: Beta validation in progress
- `DELIVERING`: Sending results to requester

### 3.2 Phase 2: Pattern Detection Integration

**Files Modified**: `src/heretek_swarm/actors/explorer.py`

#### 3.2.1 Pattern Emission

Implement pattern detection and emission:

```python
async def _detect_and_emit_patterns(
    self, 
    findings: list[ResearchFinding]
) -> list[Pattern]:
    """Detect patterns in findings and emit to collective."""
    patterns = []
    for finding in findings:
        pattern = self._extract_pattern(finding)
        if pattern and pattern.confidence >= 0.7:
            await self._emit_pattern(
                item_id=finding.finding_id,
                item_type="research_finding",
                outcome="success",
                content=pattern.to_dict()
            )
            patterns.append(pattern)
    return patterns
```

#### 3.2.2 Pattern Types for Explorer

| Pattern Type | Trigger | Evidence Required |
|--------------|---------|-------------------|
| `research_trend` | 3+ similar findings across sources | 0.7 confidence |
| `technology_adoption` | New framework/tool mentioned | 0.8 confidence |
| `security_vulnerability` | Vulnerability pattern detected | 0.85 confidence |
| `performance_degradation` | Performance anomaly pattern | 0.8 confidence |
| `capability_gap` | Missing capability identified | 0.75 confidence |

### 3.3 Phase 3: Consensus Integration

**Files Modified**: `src/heretek_swarm/actors/explorer.py`, `src/heretek_swarm/knowledge/research.py`

#### 3.3.1 Contradiction Resolution Flow

```
Explorer detects contradiction
         ↓
Request Beta validation
         ↓
   Beta validates claim
         ↓
If unresolved → Request deliberation via Steward
         ↓
   Steward initiates deliberation
         ↓
Consensus reached → Proceed with winning finding
```

#### 3.3.2 Research Consensus Trigger

Research findings should go to consensus when:
- Finding confidence < threshold but > 0.5
- Multiple contradictory findings with similar confidence
- Finding has high impact (impact_score > 0.8)
- Steward requests validation

### 3.4 Phase 4: Steward Oversight

**Files Modified**: `src/heretek_swarm/actors/explorer.py`

#### 3.4.1 Oversight Messages

Explorer reports to Steward:
- Research started: `research_progress` with status="started"
- Research ongoing: `research_progress` with status="update", percent_complete
- Research completed: `research_progress` with status="completed"
- Scope creep detected: `research_progress` with status="scope_change", proposed_depth
- Deadlock detected: `research_progress` with status="blocked"

#### 3.4.2 Depth Limit Enforcement

```python
@dataclass
class ResearchLimits:
    """Configurable research depth limits."""
    max_depth: ResearchDepth = ResearchDepth.MEDIUM
    max_sources: int = 20
    max_time_seconds: float = 300.0  # 5 minutes
    max_findings: int = 50
    steward_approval_required: bool = True  # For deep research
```

---

## 4. File Structure

### 4.1 Modified Files

| File | Changes |
|------|---------|
| `src/heretek_swarm/actors/explorer.py` | Add research handlers, pattern emission, contradiction resolution |

### 4.2 Created Files

| File | Description |
|------|-------------|
| `src/heretek_swarm/knowledge/research.py` | Research models and utilities |

### 4.3 New Module Structure

```
src/heretek_swarm/knowledge/research.py
├── ResearchQuery        # Research query specification
├── ResearchDepth         # Enum: shallow/medium/deep
├── ResearchFinding       # Individual finding with evidence
├── ResearchResult       # Complete research result
├── ResearchState        # Enum: research workflow states
├── ResearchConfig       # Configuration dataclass
├── KnowledgeSynthesizer # LLM-based synthesis
└── create_research_agent() # Factory function
```

---

## 5. Edge Cases & Mitigation

### 5.1 Contradictory Findings

**Scenario**: Explorer provides contradictory findings to the collective.

**Mitigation**:
1. Beta validates each finding before emission
2. If contradictions persist, request deliberation via Steward
3. Minority report preserved (DEL-02 requirement)
4. All contradictions documented in research result metadata

**Implementation**:
```python
async def _resolve_contradictions(
    self, 
    findings: list[ResearchFinding]
) -> list[ResearchFinding]:
    """Resolve contradictory findings via validation or deliberation."""
    contradictions = self._find_contradictions(findings)
    
    for contradiction in contradictions:
        # Request Beta validation
        validation = await self._request_beta_validation(contradiction)
        
        if not validation.is_resolved:
            # Request deliberation via Steward
            await self._request_deliberation(contradiction)
    
    return [f for f in findings if f.status != "rejected"]
```

### 5.2 Research Scope Creep

**Scenario**: Research expands beyond initial topic, consuming excessive resources.

**Mitigation**:
1. Configurable depth limits (`ResearchConfig.max_depth`)
2. Steward oversight via progress messages
3. Automatic truncation at time limits
4. Steward can send `halt_research` message

**Implementation**:
```python
async def _check_scope_creep(
    self, 
    query: ResearchQuery,
    current_progress: ResearchProgress
) -> bool:
    """Check if research is exceeding scope limits."""
    if current_progress.sources_consulted >= query.max_sources:
        return True
    if current_progress.elapsed_seconds >= query.time_limit_seconds:
        return True
    if current_progress.findings_count >= query.max_findings:
        return True
    return False
```

### 5.3 Deadlock Detection

**Scenario**: Research cannot complete due to unresolved contradictions.

**Mitigation**:
1. Timeout after configurable period
2. Report partial findings with `confidence=0.5`
3. Notify Steward of incomplete research
4. Log for human review

---

## 6. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Explorer autonomously researches topics | Research initiated without human input | 100% of non-critical topics |
| Patterns detected and reported | Patterns emitted to collective learning | ≥ 3 pattern types operational |
| Consensus integration | Findings submitted to consensus when required | Validated via DEL-01 |
| Contradiction resolution | Beta validation operational | < 5% of findings require deliberation |
| Scope control | Depth limits enforced | No research exceeds max_depth |
| Steward oversight | Progress messages sent | Every 60 seconds during research |
| False positive rate | Invalid patterns emitted | < 1% (via Beta validation) |

---

## 7. Dependencies

| Dependency | Source | Required For |
|------------|--------|--------------|
| AgentActor base | Phase 1 | Base class |
| HealthReportingMixin | Phase 1 | Health status |
| ValidationMixin | Phase 1 | Input/output validation |
| DeliberationMixin | Phase 1 | Consensus participation |
| PatternMixin | Phase 1 | Pattern emission |
| Beta validation | Phase 1 (GOV-03) | Contradiction resolution |
| Steward oversight | Phase 1 (GOV-01) | Scope control |
| UnifiedKnowledgeAccess | KNOW-01 | Knowledge queries |

---

## 8. Testing Strategy

### 8.1 Unit Tests

- `test_explorer_research_workflow`: Test research state machine
- `test_contradiction_detection`: Test finding contradiction identification
- `test_depth_limit_enforcement`: Test scope control
- `test_pattern_emission`: Test pattern emission to collective

### 8.2 Integration Tests

- `test_beta_validation_flow`: Test Explorer → Beta validation round-trip
- `test_steward_oversight`: Test progress reporting to Steward
- `test_consensus_integration`: Test findings submission to deliberation

### 8.3 Verification Test

Create `tests/exploration/test_disc01_research.py`:

```python
async def test_explorer_autonomous_research():
    """Test Explorer can research topic autonomously."""
    explorer = ExplorerAgent()
    result = await explorer.research_topic("new AI frameworks")
    
    assert result.findings is not None
    assert result.summary is not None
    assert result.contradictions_resolved is not None

async def test_contradiction_resolution():
    """Test contradictory findings trigger validation."""
    explorer = ExplorerAgent()
    findings = [finding_a, finding_b]  # contradictory
    
    resolved = await explorer._resolve_contradictions(findings)
    
    assert len(resolved) < len(findings)  # Some filtered out
```

---

## 9. Implementation Order

### Week 1-2: Core Research
1. Create `knowledge/research.py` with models
2. Add `_handle_research_topic` handler
3. Implement basic research workflow (IDLE → RESEARCHING → DELIVERING)

### Week 3-4: Pattern Integration
4. Integrate pattern detection in findings
5. Implement `_emit_pattern` calls
6. Add pattern type classification

### Week 5-6: Consensus & Oversight
7. Implement contradiction detection
8. Add Beta validation request flow
9. Add Steward progress reporting
10. Implement depth limit enforcement

### Week 7-8: Testing & Verification
11. Write unit tests
12. Integration testing with Beta
13. Verify all edge cases handled

---

## 10. Open Questions

1. **Research depth default**: What should default `ResearchDepth` be? (propose: MEDIUM)
2. **Timeout threshold**: How long before research times out? (propose: 300s for MEDIUM, 600s for DEEP)
3. **Beta validation latency**: What's acceptable validation turnaround? (propose: 30s)
4. **Pattern confidence threshold**: What minimum confidence for pattern emission? (propose: 0.7)
5. **Steward approval scope**: Which research requires Steward approval? (propose: DEEP only)

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Research completion rate | ≥ 95% | % of research requests completed |
| Pattern emission accuracy | ≥ 99% | Patterns validated by Beta |
| Average research time | ≤ 120s | For MEDIUM depth |
| Contradiction resolution time | ≤ 60s | Via Beta validation |
| Scope creep incidents | 0 | Research exceeding max_depth |

---

**Plan Status**: Ready for Implementation  
**Next Action**: Begin Phase 1 - Core Research Infrastructure
