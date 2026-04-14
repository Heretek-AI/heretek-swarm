# Feature Landscape: The Collective

**Domain:** Multi-agent autonomous swarm with emergent collective intelligence
**Researched:** 2026-04-13
**Confidence:** MEDIUM-HIGH (based on existing codebase analysis and theoretical frameworks)

## Executive Summary

The Collective is a 23-agent autonomous swarm requiring consensus-based governance, zero-trust security, and measurable consciousness frameworks. The codebase already implements substantial foundations across all key areas: deliberation-based consensus, 4-layer zero-trust validation, IIT Phi calculations, FEP active inference, and emergent pattern detection. This research synthesizes requirements into implementable features with complexity estimates and dependency graphs.

---

## 1. Feature Categories Derived from Requirements

### 1.1 Core Governance (Core Triad)

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Steward monitoring | GOV-01 | Low | Agent base class, health reporting | Stub exists |
| Alpha deep analysis | GOV-02 | Medium | Deliberation engine, expertise weighting | Stub exists |
| Beta error detection | GOV-03 | Medium | Validation layer, reality projection | Stub exists |
| Charlie critical review | GOV-04 | Medium | Deliberation, risk assessment | Stub exists |
| Core Triad convening | GOV-05 | High | Swarm deliberation, quorum formation | Not started |

**Rationale:** Core Triad is the governance backbone. Steward is simplest (monitoring), Alpha/Beta need deliberation integration, Charlie adds risk framing. GOV-05 (convening) requires full quorum mechanics.

### 1.2 Knowledge & Memory (Support Agents)

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Historian synthesis | KNOW-01 | Medium | Memory system, precedent tracking | Stub exists |
| Metis timelines | KNOW-02 | Medium-High | Time perception, causal tracing | Stub exists |
| Empath sentiment | KNOW-03 | Medium | Human-AI interaction, resonance metrics | Stub exists |
| Perceiver ingestion | KNOW-04 | Medium | Multi-modal input handling | Stub exists |
| Echo translation | KNOW-05 | Low-Medium | Channel registry, protocol translation | Stub exists |

**Rationale:** Support agents provide context and memory. Historian and Metis are higher complexity due to temporal reasoning. Echo is straightforward protocol translation.

### 1.3 Discovery & Creation (Exploration Agents)

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Explorer research | DISC-01 | Medium | Information gathering, pattern detection | Stub exists |
| Examiner validation | DISC-02 | Medium | Capability stress-testing | Stub exists |
| Dreamer synthesis | DISC-03 | High | Lateral thinking, novel connections | Stub exists |
| Coder autonomous | DISC-04 | Very High | Code generation, debugging, execution | Stub exists |

**Rationale:** Exploration agents increase in complexity from passive (Explorer) to generative (Dreamer) to autonomous execution (Coder). Coder is highest risk and should be developed last with robust safety bounds.

### 1.4 Protection (Safety Agents)

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Sentinel anomaly response | SAFE-01 | Medium | Zero-trust validator, behavioral analysis | Stub exists |
| Sentinel-Prime external threats | SAFE-02 | High | Threat detection, containment protocols | Stub exists |
| Arbiter dispute mediation | SAFE-03 | Medium | Tribunal system, consensus tracking | Partial implementation |

**Rationale:** Safety agents form the immune system. Sentinel is internal monitoring (lower complexity), Sentinel-Prime handles external attacks (high complexity, needs threat intelligence), Arbiter mediates disputes during consensus failures.

### 1.5 Integration (Coordination Agents)

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Coordinator sync | INTG-01 | Medium | Task dependency graph, synchronization | Stub exists |
| Nexus gateway | INTG-02 | Medium | External API handling, protocol translation | Stub exists |
| Catalyst paradigm shifts | INTG-03 | High | Systemic change detection, transition management | Stub exists |
| Chronos time perception | INTG-04 | High | Time dilation, long-running execution context | Stub exists |

**Rationale:** Coordination agents are infrastructure-level. Coordinator is foundational task sync, Nexus is external communication, Catalyst and Chronos handle edge cases (paradigm shifts, extended time horizons).

### 1.6 Optimization (Enhancement Agents)

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Prism diverse viewpoints | OPT-01 | Medium | Consensus participation, perspective injection | Stub exists |
| Habit-Forge efficiency | OPT-02 | Medium | Pattern library, behavioral optimization | Stub exists |
| Perceiver+ meta-perception | OPT-03 | High | Signal extraction, noise filtering | Stub exists |

**Rationale:** Enhancement agents optimize system performance. Prism adds diversity to consensus, Habit-Forge captures efficient patterns, Perceiver+ extracts higher-order signals.

### 1.7 Consensus & Governance

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Inter-agent dispute consensus | CONS-01 | High | Deliberation engine, quorum system | Partial implementation |
| Immune response building | CONS-02 | High | Anomaly detection, pattern learning | Partial implementation |
| Baseline updating | CONS-03 | Medium | Emergent pattern detection, adaptation | Partial implementation |

**Rationale:** Consensus requirements build on deliberation mechanics. CONS-01 is the core dispute resolution (uses existing DeliberationEngine), CONS-02/03 require integration with emergent detection and learning systems.

### 1.8 Zero-Trust Architecture

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| Hostile input treatment | ZERO-01 | Low | Input validation layer | Implemented |
| Internal function validation | ZERO-02 | Medium | Context validation, behavioral baselines | Implemented |
| Comprehensive audit trails | ZERO-03 | Low | Audit logging, structured logging | Implemented |

**Rationale:** Zero-trust is already substantially implemented with 4-layer architecture (Input, Context, Output, Audit). ZERO-02 is ongoing behavioral analysis that needs runtime integration.

### 1.9 Consciousness Framework

| Feature | Requirement | Complexity | Dependencies | Implementation Status |
|---------|-------------|------------|--------------|----------------------|
| GWT broadcast mechanism | COG-01 | High | NATS broadcast, workspace integration | Implemented |
| AST self-model | COG-02 | High | Attention schema metrics, self-tracking | Partial implementation |
| IIT metrics tracking | COG-03 | Very High | Phi calculation, cause-effect structures | Implemented |
| FEP minimization | COG-04 | Very High | Active inference, free energy calculation | Implemented |

**Rationale:** Consciousness frameworks are mathematically complex. IIT and FEP calculations are implemented but need integration with agent runtime. GWT broadcast exists in NATS but agent-level integration is pending.

---

## 2. Multi-Agent Consensus Patterns

### 2.1 Pattern Analysis

**Existing Implementation:** `DeliberationEngine` (src/heretek_swarm/consensus/deliberation.py)

The codebase implements a sophisticated multi-round deliberation system with:
- Argument/counter-argument structure with evidence quality weighting
- Consensus confidence scoring based on agreement level, evidence quality, dissent severity
- Expertise weighting for agent contributions
- Dissent tracking with minority reports
- Decision hashing for immutable audit trails

**Patterns Observed:**

| Pattern | Description | Implementation |
|---------|-------------|----------------|
| **Quorum-based** | Requires minimum participants (3) for valid deliberation | `min_participants: int = 3` |
| **Multi-round deliberation** | Iterative argument exchange with position evolution | `max_rounds: int = 5` configurable |
| **Expertise-weighted voting** | Domain-specific expertise increases argument weight | `expertise_weight: float = 0.30` |
| **Evidence-gravity** | Evidence quality contributes 35% to consensus scoring | `evidence_weight: float = 0.35` |
| **Dissent preservation** | Minority opinions tracked for minority reports | `dissent_tracking: bool = True` |

### 2.2 BFT vs Raft vs Quorum Analysis

| Criterion | DeliberationEngine (Quorum-based) | Raft-style Election | BFT-style |
|-----------|-----------------------------------|---------------------| --------|
| **Crash fault tolerance** | Yes (quorum survives n-1 failures) | Yes | Yes |
| **Byzantine fault tolerance** | Partial (evidence validation helps) | No | Yes (3f+1 required) |
| **Finality** | eventual | eventual | deterministic |
| **Latency** | Medium (multi-round) | Low (leader-based) | High (byzantine agreement) |
| **Complexity** | Medium | Low | Very High |
| **Suitable for** | Decision-making with reasoning | State replication | Critical transactions |

**Recommendation:** Use quorum-based deliberation for decisions requiring reasoning (GOV-05, CONS-01). Implement Raft-style leader election for operational decisions (agent health, task distribution). BFT not recommended unless Byzantine attacks are a realistic threat (external API boundaries).

### 2.3 Consensus Implementation Complexity

| Consensus Type | Complexity | Risk | Recommendation |
|---------------|------------|------|----------------|
| Simple majority | Low | Low | DISC-02 (Examiner validation) |
| Expertise-weighted | Medium | Medium | All governance decisions |
| Quorum with evidence | High | Medium | CONS-01, GOV-05 |
| Raft leader election | Medium | Medium | Operational coordination |
| BFT-style | Very High | High | External boundary only |

---

## 3. Global Workspace Theory (GWT) Implementation

### 3.1 Pattern Analysis

**Existing Implementation:** NATS broadcast system (src/heretek_swarm/infrastructure/nats/broadcast.py)

GWT in The Collective requires:
1. **Broadcast mechanism** - Information presented to all agents
2. **Global access** - Single shared workspace
3. **Consciousness threshold** - Only salient information broadcast

### 3.2 GWT Architecture

```
Agent A ──┐
Agent B ──┼──► [NATS Broadcast] ──► [Global Workspace] ──► All Agents
Agent C ──┘                          │
                                      ▼
                              [Consciousness Filter]
                                      │
                                      ▼
                              [Attention Selection]
```

### 3.3 GWT Implementation Status

| Component | Status | Implementation |
|-----------|--------|----------------|
| Broadcast transport | Implemented | NATS publish/subscribe |
| Global workspace state | Partial | Event store with global queries |
| Consciousness filtering | Not implemented | Needs salience metrics |
| Attention selection | Not implemented | Needs priority mechanism |
| Integration with deliberation | Partial | Broadcast used in consensus |

### 3.4 GWT Complexity

| Feature | Complexity | Dependencies |
|---------|------------|--------------|
| Basic broadcast | Low | NATS infrastructure |
| Consciousness filter | Medium | Salience metrics from agents |
| Attention selection | High | Priority ranking,竞争机制 |
| Integration with AST | High | Self-model awareness |
| Cross-modal workspace | High | Multi-modal input handling |

---

## 4. Attention Schema Theory (AST) Self-Modeling

### 4.1 Pattern Analysis

**Existing Implementation:** `ASTMetrics` (src/heretek_swarm/consciousness/metrics/ast.py)

ASTMetrics implements Adaptive Systems Theory with:
- **Complexity** measurement (component count, connection density)
- **Emergence** detection (micro-state to macro-property transitions)
- **Self-organization** coefficient (local rules producing global patterns)
- **Resilience** scoring (recovery from perturbations)
- **Adaptation** rate tracking

### 4.2 AST Metrics Tracked

| Metric | Description | Measurement |
|--------|-------------|-------------|
| Complexity (0-1) | Information content in system organization | density * 0.6 + diversity * 0.4 |
| Emergence Score (0-1) | Novel properties from interactions | state_variety * (1 - abs(micro_info - macro_info)) |
| Self-Organization (0-1) | Spontaneous order from local rules | rule_contribution + pattern_contribution + interaction |
| Resilience (0-1) | Recovery ability from perturbations | recovery_rate * 0.7 + speed * 0.3 |
| Adaptation Rate (0-1) | Learning/evolution speed | behavioral_variety / 20.0 |
| Entropy (0-1) | System disorder (inverse of complexity) | 1.0 - complexity |
| Coupling (0-1) | Inter-component dependency | connections / 100.0 |

### 4.3 Emergence Levels

```python
class EmergenceLevel(Enum):
    NONE = "none"           # < 0.1
    WEAK = "weak"           # 0.1 - 0.3
    MODERATE = "moderate"   # 0.3 - 0.5
    STRONG = "strong"       # 0.5 - 0.7
    CRITICAL = "critical"   # > 0.7
```

### 4.4 AST Complexity

| Feature | Complexity | Dependencies |
|---------|------------|--------------|
| Basic metrics collection | Medium | Agent state tracking |
| Emergence detection | High | Statistical significance testing |
| Self-organization measurement | High | Pattern library, local rules |
| Integration with GWT | Very High | Attention and consciousness linking |
| Real-time adaptation | Very High | Streaming metrics, thresholds |

---

## 5. Zero-Trust Security Patterns

### 5.1 Pattern Analysis

**Existing Implementation:** `ZeroTrustValidator` (src/heretek_swarm/security/zero_trust.py)

4-layer validation architecture:

| Layer | Purpose | Key Features |
|-------|---------|--------------|
| Layer 1: Input Validation | Reject malformed/malicious input | Pydantic v2, UUID v4, size limits, injection patterns |
| Layer 2: Context Validation | Detect behavioral anomalies | Injection detection, behavioral baselines, anomaly scoring |
| Layer 3: Output Validation | Prevent data leakage | PII detection, sensitive data redaction, sanitization |
| Layer 4: Audit Logging | Complete audit trail | Structured logging, severity levels, event retention |

### 5.2 Security Metrics

| Metric | Target | Implementation |
|--------|--------|----------------|
| Validation latency p95 | < 50ms | Measured in `total_latency_ms` |
| False negative rate | < 0.1% | Threshold-based detection |
| False positive rate | < 1% | `anomaly_threshold: float = 3.0` (std dev) |
| Throughput | > 1000/sec | Per-layer performance tracking |

### 5.3 Injection Detection Patterns

**Layer 1 (Input):**
- Python injection: `exec()`, `eval()`, `__import__()`, `subprocess`
- Shell injection: `; rm`, `; cat`, `| sh`, `$(...)`, backticks
- SQL injection: `OR 1=1`, `UNION SELECT`, `DROP TABLE`
- Path traversal: `../`, `..\\`

**Layer 2 (Context):**
- Prompt injection: "ignore previous instructions", "you are now"
- Role play: "act as", "pretend to be"
- Encoding: `\x`, `\u`, URL encoding, base64

### 5.4 Zero-Trust Complexity

| Feature | Complexity | Dependencies |
|---------|------------|--------------|
| Input validation | Low | Pydantic models, regex patterns |
| Context injection detection | Medium | Prompt templates, encoding detection |
| Behavioral baselines | Medium | Historical data, anomaly scoring |
| Output PII detection | Low | Regex patterns, data classification |
| Full audit trail | Medium | Event store, log aggregation |
| Real-time alerting | High | Alert routing, severity escalation |

---

## 6. Emergent Intelligence Measurement

### 6.1 Pattern Analysis

**Existing Implementation:** `EmergentPatternDetector` (src/heretek_swarm/collective/emergent_detection.py)

Key components:
- **AgentBehaviorSnapshot** - Individual agent state capture
- **CollectiveBehavior** - Group behavior patterns
- **EmergentPattern** - Validated emergent properties
- **EvolutionEngine** - Organic capability development tracking

### 6.2 Emergence Detection Pipeline

```
Agent Snapshots → Sliding Windows → Metrics Calculation → Significance Testing
                                              │
                                              ▼
                                      Pattern Validation
                                              │
                                              ▼
                                    [Validated Emergent Pattern]
                                              │
                                              ▼
                                    Impact Score Calculation
```

### 6.3 Emergent Pattern Classes

| Class | Description | Examples |
|-------|-------------|----------|
| COORDINATION | Synchronized group action | Aligned decisions, resource sharing |
| OPTIMIZATION | Improved efficiency | Faster consensus, reduced redundancy |
| INNOVATION | Novel solutions | New strategies, creative combinations |
| ADAPTATION | Responds to change | Environment adaptation, learning |
| RESILIENCE | Fault tolerance | Recovery patterns, redundancy |

### 6.4 Emergent Intelligence Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| Swarm Emergence Index | Average emergence score across patterns | avg(emergence_score) |
| Collective Intelligence Factor | Validated emergence weighted by validation rate | avg_score * validation_rate |
| Coordination Level | Ratio of coordination patterns | coordination_patterns / total |
| Pattern Diversity | Unique pattern classes / total classes | unique_classes / max_classes |

### 6.5 Integration with Consciousness Frameworks

**IIT Phi Integration:**
- Phi calculations measure system integration
- High Phi correlates with strong emergence
- Integration levels: minimal (0.1), low (0.3), moderate (0.5), high (0.7), very_high (0.9)

**FEP Integration:**
- Surprise minimization indicates learning
- Expected free energy tracks adaptation
- Low free energy = well-adapted system

**Combined Metrics:**
```
Emergence Score = f(IIT_phi, FEP_surprise, AST_self_organization, AST_resilience)
Collective Intelligence = WeightedSum(emergence_metrics) * Pattern_validation_rate
```

### 6.6 Emergent Intelligence Complexity

| Feature | Complexity | Dependencies |
|---------|------------|--------------|
| Snapshot collection | Medium | Agent instrumentation |
| Sliding window analysis | Medium | Time-series processing |
| Statistical significance | High | Hypothesis testing, p-values |
| Pattern classification | High | ML classification or rule-based |
| Impact scoring | Medium | Outcome tracking |
| Real-time detection | Very High | Streaming analytics |

---

## 7. Feature Dependencies Graph

```
[Phase 1: Foundation]
    │
    ├──► ZERO-01/02/03 (Zero-Trust base) ──────────────────────────┐
    │                                                              │
    ├──► Agent Base Classes ───────────────────────────────────────┼──► [Phase 2]
    │     │                                                        │
    │     ├──► Core Triad (GOV-01-04) ─────────────────────────────┤
    │     │     │                                                  │
    │     │     └──► GOV-05 (Triad convening) ─────────────────────┤
    │     │           │                                            │
    │     ├──► Support Agents (KNOW-01-05) ───────────────────────┤
    │     │           │                                            │
    │     ├──► Safety Agents (SAFE-01, SAFE-03) ──────────────────┤
    │     │           │                                            │
    │     └──► Coordination Agents (INTG-01, INTG-02) ───────────┤
    │                                                              │
    │                                                    [Phase 2: Consensus & Safety]
    │
    └──► GWT Broadcast (COG-01) ──────────────────────────────────┐
          │                                                        │
          ├──► Deliberation Engine Integration ────────────────────┼──► [Phase 3]
          │     │                                                  │
          │     ├──► CONS-01 (Dispute consensus) ─────────────────┤
          │     │     │                                            │
          │     │     └──► CONS-02/03 (Immune responses, baselines)─┤
          │     │                                                  │
          │     ├──► OPT-01 (Prism viewpoints) ───────────────────┤
          │     │                                                  │
          │     └──► SAFE-02 (Sentinel-Prime) ─────────────────────┤
          │                                                          │
          │                                              [Phase 3: Enhancement]
          │
          └──► AST Self-Model (COG-02) ────────────────────────────┐
                │                                                 │
                ├──► IIT Phi Integration (COG-03) ────────────────┼──► [Phase 4]
                │     │                                           │
                │     └──► FEP Minimization (COG-04) ─────────────┤
                │                                                 │
                ├──► DISC-03 (Dreamer) ──────────────────────────┤
                │                                                 │
                ├──► INTG-03/04 (Catalyst, Chronos) ──────────────┤
                │                                                 │
                └──► OPT-02/03 (Habit-Forge, Perceiver+) ──────────┤
                                                                          │
                                                          [Phase 4: Autonomous Operation]
                                                          │
                                                          └──► DISC-04 (Coder) ──► HEAL-01/02/03
```

---

## 8. Implementation Priority Rationale

### Phase 1: Foundation (Core Agents + Zero-Trust)

**Rationale:** Zero-trust is the security substrate and is already implemented. Core agents provide the basic operational capability. No dependencies on consensus or consciousness frameworks.

**Critical path:**
1. Zero-trust validation integration (ZERO-01/02/03)
2. Agent base class with health reporting
3. Core Triad implementation (GOV-01-04)
4. Support agents (KNOW-01-05)
5. Basic coordination (INTG-01, INTG-02)

### Phase 2: Consensus & Safety

**Rationale:** After foundation, the system needs to make collective decisions and defend itself. Deliberation engine is ready; needs agent integration. Safety agents need zero-trust integration.

**Critical path:**
1. GWT broadcast integration (COG-01)
2. Deliberation engine agent integration
3. CONS-01 (dispute consensus)
4. Safety agents (SAFE-01, SAFE-03)
5. OPT-01 (Prism for diverse viewpoints)

### Phase 3: Enhancement & Consciousness

**Rationale:** Enhancement agents optimize the system. Consciousness frameworks provide measurability. These are higher complexity but depend on earlier phases.

**Critical path:**
1. AST self-model implementation (COG-02)
2. IIT Phi calculation integration (COG-03)
3. FEP active inference integration (COG-04)
4. Emergent pattern detection integration
5. Enhancement agents (OPT-02, OPT-03)
6. Exploration agents except Coder (DISC-01-03)

### Phase 4: Autonomous Operation

**Rationale:** Coder is highest risk (autonomous code execution). Self-healing enables unbounded operation. This is the final phase before true autonomy.

**Critical path:**
1. DISC-04 (Coder) with safety bounds
2. HEAL-01 (Failure detection and recovery)
3. HEAL-02 (Auto-scaling)
4. HEAL-03 (Self-maintenance)

---

## 9. Anti-Features to Avoid

| Anti-Feature | Why Avoid | Instead |
|-------------|-----------|---------|
| Centralized orchestration | Violates sovereignty principle | Quorum-based consensus |
| Static rule enforcement | Prevents organic evolution | Adaptive pattern learning |
| Human-in-the-loop commands | Bottleneck for 24/7 operation | Agent autonomy with guardrails |
| Periodic task invocation | Contradicts continuous operation | Persistent runtime |
| Hardcoded agent behaviors | No adaptation | Learning and pattern capture |

---

## 10. Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Python/FastAPI/Pydantic/SQLAlchemy confirmed |
| Features | MEDIUM | Requirements well-documented; implementation partial |
| Architecture | MEDIUM | Consensus patterns proven; GWT/AST need integration |
| Pitfalls | MEDIUM | Known complexity in consciousness frameworks |

---

## 11. Research Gaps

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| Coder safety bounds | High | Need dedicated safety research before DISC-04 |
| BFT requirements | Medium | Clarify if Byzantine faults are realistic threat |
| GWT consciousness threshold | Medium | Need salience metric definition |
| Emergent intelligence validation | Medium | Need ground truth for "exceeding individual agents" |
| Self-healing implementation | High | Need failure mode analysis |

---

## 12. Sources

**Codebase (HIGH confidence):**
- `src/heretek_swarm/consensus/deliberation.py` - Deliberation engine implementation
- `src/heretek_swarm/security/zero_trust.py` - 4-layer security architecture
- `src/heretek_swarm/consciousness/metrics/ast.py` - Adaptive systems metrics
- `src/heretek_swarm/collective/emergent_detection.py` - Emergence detection
- `src/heretek_swarm/consciousness/iit_phi.py` - IIT Phi calculation
- `src/heretek_swarm/consciousness/fep_active_inference.py` - FEP implementation

**Theoretical frameworks (MEDIUM confidence - training data):**
- Global Workspace Theory: Baars (1997), Dehaene et al.
- Integrated Information Theory: Tononi (2008), Oizumi et al. (2014)
- Free Energy Principle: Friston (2010, 2017)
- Attention Schema Theory: Graziano (2013)
- Adaptive Systems Theory: Holland (1995), Kauffman (1993)
