# DISC-03 Implementation Plan: Dreamer Lateral Thinking Agent

**Task**: DISC-03 — Dreamer Lateral Thinking Agent  
**Owner**: Dreamer  
**Depends**: Phase 1 (Agent base class)  
**Created**: 2026-04-14  
**Status**: Planning

---

## Executive Summary

The Dreamer Lateral Thinking Agent (DISC-03) provides novel connection generation between disparate concepts, enabling the collective to break out of conventional thinking patterns. This implementation plan details the `novel_connections.py` module that extends the existing `DreamerAgent` with specialized lateral thinking capabilities.

**Current State**: `dreamer.py` exists with comprehensive creativity technique implementations (brainstorming, SCAMPER, Six Thinking Hats, TRIZ, analogical thinking, first principles). The DreamerAgent already has `CreativityTechnique.LATERAL_THINKING` defined but lacks a dedicated lateral thinking module.

**Target State**: Production-ready lateral thinking module (`novel_connections.py`) with:
- Novel connection generation between unrelated concepts
- Lateral thinking metrics (divergence score, association distance, insight novelty)
- Safe content generation with Beta validation integration
- Over-reliance detection via position change ratio monitoring
- Deliberation contribution tracking

---

## 1. Current Implementation Analysis

### 1.1 What Exists

The `DreamerAgent` class (926 lines) in `src/heretek_swarm/actors/dreamer.py` provides:

| Component | Status | Notes |
|-----------|--------|-------|
| **Creativity Techniques** | ✅ Complete | 8 techniques defined (brainstorming, SCAMPER, etc.) |
| **CreativeIdea/CreativeSession** | ✅ Complete | Full dataclass models |
| **Idea Generation** | ✅ Complete | `_generate_creative_ideas()` with LLM |
| **Technique Application** | ✅ Complete | `_apply_six_hats()`, `_apply_scamper()`, etc. |
| **Idea Combination** | ✅ Complete | `_combine_ideas_llm()` |
| **Innovation Reports** | ✅ Complete | `_generate_innovation_report()` |
| **DeliberationMixin** | ✅ Integrated | Can participate in consensus |
| **ZeroTrustValidator** | ✅ Integrated | Session 44 zero-trust validation |
| **Lateral Thinking Technique** | 🟡 Stub | `LATERAL_THINKING` enum value exists, no dedicated handler |

### 1.2 Dreamer Agent Mixins

Dreamer already extends these mixins:

```python
class DreamerAgent(
    ValidationMixin,      # Input/output validation
    DeliberationMixin,    # Consensus participation
    PatternMixin,         # Pattern emission
    MemoryMixin,          # Memory access tracking
    LearningMixin,        # Learning status reporting
    AgentActor
):
```

### 1.3 Gap Analysis

| Gap | Severity | Description |
|-----|----------|-------------|
| Lateral thinking handler | HIGH | No dedicated `_handle_lateral_thinking()` or lateral thinking module |
| Novel connection generation | HIGH | No `novel_connections.py` module |
| Lateral thinking metrics | MEDIUM | No divergence score, association distance measurement |
| Over-reliance monitoring | MEDIUM | No position change ratio tracking for Dreamer output |
| Content safety for creativity | MEDIUM | Beta validation integration not specific to creative content |
| Deliberation contribution | MEDIUM | Dreamer ideas not formally submitted as deliberation inputs |

---

## 2. Target Architecture

### 2.1 Core Responsibilities

The `novel_connections.py` module must:

1. **Novel Connection Generation**: Find unexpected relationships between disparate concepts
2. **Association Distance Measurement**: Quantify how "far" a connection is from conventional thinking
3. **Insight Novelty Scoring**: Rate how original/innovative a connection is
4. **Divergence Metrics**: Measure how much a creative output deviates from baseline
5. **Content Safety**: Integrate with Beta for harmful content detection
6. **Over-reliance Detection**: Track usage patterns to prevent collective over-dependence
7. **Deliberation Integration**: Submit lateral thinking outputs as structured deliberation inputs

### 2.2 Module Structure

```
src/heretek_swarm/creativity/novel_connections.py
├── NovelConnection           # Dataclass: generated connection record
├── AssociationDistance        # Dataclass: distance metrics between concepts
├── LateralThinkingMetrics     # Dataclass: comprehensive metrics
├── ConnectionTechnique        # Enum: techniques for making connections
├── HarmfulContentFilter       # Class: Beta validation integration
├── NovelConnectionEngine      # Class: core generation engine
├── LateralThinkingMetricsTracker  # Class: metrics collection
└── create_novel_connection_session()  # Factory function
```

---

## 3. Implementation Plan

### 3.1 Phase 1: Core Data Models

**Files Created**: `src/heretek_swarm/creativity/__init__.py`  
**Files Created**: `src/heretek_swarm/creativity/novel_connections.py`

#### 3.1.1 NovelConnection Dataclass

```python
@dataclass
class NovelConnection:
    """A novel connection between two or more concepts."""
    connection_id: str
    source_concepts: list[str]           # Original concepts provided
    connected_concepts: list[str]        # Concepts discovered through connection
    connection_description: str          # How the concepts are related
    association_distance: float           # 0-1, how unexpected the connection is
    insight_novelty: NoveltyLevel        # incremental/substantial/breakthrough
    confidence: float                    # 0-1 confidence in the connection
    technique_used: ConnectionTechnique  # The technique that produced this
    evidence: str                        # Rationale for the connection
    generated_at: datetime
    validated: bool = False              # Passed Beta validation
    validation_notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### 3.1.2 ConnectionTechnique Enum

```python
class ConnectionTechnique(StrEnum):
    """Techniques for generating novel connections."""
    RANDOM_ASSOCIATION = "random_association"      # Free association
    ANALOGICAL_BRIDGING = "analogical_bridging"   # Analogy between domains
    METAPHORICAL_EXTENSION = "metaphorical_extension"  # Extend metaphors
    FIRST_PRINCIPLES_DECONSTRUCTION = "first_principles_deconstruction"
    ANTI_CONVENTIONAL = "anti_conventional"       # Deliberately opposite
    CROSS_DOMAIN_IMPORT = "cross_domain_import"    # Import from unrelated field
    TEMPORAL_REFRAMING = "temporal_reframing"     # Recontextualize in time
    SCALE_INVERSION = "scale_inversion"            # Invert magnitude/scale
    FUNCTION_TRANSFER = "function_transfer"        # Transfer function to new context
```

#### 3.1.3 LateralThinkingMetrics Dataclass

```python
@dataclass
class LateralThinkingMetrics:
    """Comprehensive metrics for lateral thinking output."""
    metrics_id: str
    session_id: str
    divergence_score: float          # 0-1, how far from conventional
    association_distance_avg: float   # Average association distance
    insight_rate: float              # Insights per minute
    novelty_distribution: dict[NoveltyLevel, int]  # Count by novelty level
    breakthrough_count: int          # Number of breakthrough-level ideas
    validated_count: int            # Number passed Beta validation
    rejected_count: int              # Number rejected by Beta
    total_connections: int
    unique_concepts_used: int        # How many distinct concepts connected
    cross_domain_connections: int    # Connections spanning domains
    timestamp: datetime
    
    def calculate_creativity_score(self) -> float:
        """Calculate overall creativity score (0-100)."""
        base = self.divergence_score * 0.3
        novelty = (self.breakthrough_count / max(1, self.total_connections)) * 0.3
        diversity = (self.unique_concepts_used / max(1, self.total_connections)) * 0.2
        quality = (self.validated_count / max(1, self.total_connections)) * 0.2
        return min(100, (base + novelty + diversity + quality) * 100)
```

### 3.2 Phase 2: Novel Connection Engine

**Files Modified**: `src/heretek_swarm/creativity/novel_connections.py`

#### 3.2.1 NovelConnectionEngine Class

```python
class NovelConnectionEngine:
    """Generates novel connections between disparate concepts."""
    
    def __init__(
        self,
        llm_provider: Any = None,
        creativity_temperature: float = 0.8,
        max_connections_per_session: int = 20,
    ):
        self.llm_provider = llm_provider
        self.temperature = creativity_temperature
        self.max_connections = max_connections_per_session
        
    async def generate_connections(
        self,
        concepts: list[str],
        technique: ConnectionTechnique = ConnectionTechnique.RANDOM_ASSOCIATION,
        target_count: int = 5,
    ) -> list[NovelConnection]:
        """Generate novel connections between provided concepts."""
        
    async def _generate_random_association(
        self, concepts: list[str], target_count: int
    ) -> list[NovelConnection]:
        """Free association - connect through intermediate concepts."""
        
    async def _generate_analogical_bridging(
        self, concepts: list[str], target_count: int
    ) -> list[NovelConnection]:
        """Find analogies between seemingly unrelated domains."""
        
    async def _generate_cross_domain_import(
        self, concepts: list[str], target_count: int
    ) -> list[NovelConnection]:
        """Import solutions/concepts from unrelated fields."""
```

#### 3.2.2 Association Distance Calculation

```python
    async def _calculate_association_distance(
        self,
        source_concepts: list[str],
        target_concepts: list[str],
    ) -> float:
        """Calculate how unexpected/unconventional a connection is.
        
        Uses embedding distance + LLM judgment to estimate.
        Returns 0-1 where 1 = highly unexpected connection.
        """
        # 1. Get embeddings for both concept sets
        # 2. Calculate cosine distance
        # 3. LLM judges "conventionality" 
        # 4. Combine scores
```

#### 3.2.3 Insight Novelty Classification

```python
    def _classify_insight_novelty(
        self,
        connection: NovelConnection,
        baseline_novelty: float,
    ) -> NoveltyLevel:
        """Classify the novelty level of a connection."""
        if connection.association_distance > baseline_novelty + 0.3:
            return NoveltyLevel.BREAKTHROUGH
        elif connection.association_distance > baseline_novelty + 0.1:
            return NoveltyLevel.SUBSTANTIAL
        return NoveltyLevel.INCREMENTAL
```

### 3.3 Phase 3: Safety Integration

**Files Modified**: `src/heretek_swarm/creativity/novel_connections.py`

#### 3.3.1 HarmfulContentFilter Class

```python
class HarmfulContentFilter:
    """Filters potentially harmful creative content via Beta validation."""
    
    def __init__(self, beta_agent: BetaAgent | None = None):
        self.beta_agent = beta_agent
        self._harmful_patterns: list[Pattern] = []
        
    async def validate_connection(
        self,
        connection: NovelConnection,
    ) -> tuple[bool, str | None]:
        """Validate a connection is safe for the collective.
        
        Returns:
            (is_safe, rejection_reason)
        """
        # 1. Check against harmful patterns
        if self._matches_harmful_pattern(connection):
            return False, "Matches known harmful pattern"
            
        # 2. Request Beta validation for borderline cases
        if connection.association_distance > 0.8:  # Very unconventional
            beta_validation = await self._request_beta_validation(connection)
            if not beta_validation.is_safe:
                return False, beta_validation.reason
                
        return True, None
        
    async def _request_beta_validation(
        self,
        connection: NovelConnection,
    ) -> ValidationResult:
        """Request Beta agent to validate potentially harmful content."""
```

#### 3.3.2 Beta Validation Integration

The flow for Dreamer content safety:

```
Dreamer generates novel connection
         ↓
HarmfulContentFilter checks patterns
         ↓
If association_distance > 0.8 → Request Beta validation
         ↓
   Beta validates content safety
         ↓
If unsafe → Steward notified, connection rejected
         ↓
If safe → Connection approved for deliberation
```

### 3.4 Phase 4: Metrics & Over-reliance Detection

**Files Modified**: `src/heretek_swarm/creativity/novel_connections.py`

#### 3.4.1 LateralThinkingMetricsTracker Class

```python
class LateralThinkingMetricsTracker:
    """Tracks lateral thinking metrics for Dreamer agent."""
    
    def __init__(self):
        self._session_metrics: dict[str, LateralThinkingMetrics] = {}
        self._position_change_history: deque[float] = deque(maxlen=100)
        self._dreamer_usage_history: deque[int] = deque(maxlen=100)
        
    async def track_session(
        self,
        session_id: str,
        metrics: LateralThinkingMetrics,
    ) -> None:
        """Record metrics for a lateral thinking session."""
        
    def calculate_position_change_ratio(
        self,
        window_size: int = 50,
    ) -> float:
        """Calculate how often collective changes position due to Dreamer.
        
        High ratio (>0.15) indicates over-reliance on Dreamer output.
        """
        if len(self._position_change_history) < 10:
            return 0.0
        changes = sum(1 for i in range(1, len(self._position_change_history))
                      if self._position_change_history[i] != self._position_change_history[i-1])
        return changes / len(self._position_change_history)
        
    def calculate_dreamer_usage_rate(
        self,
        window_size: int = 50,
    ) -> float:
        """Calculate percentage of deliberations using Dreamer input."""
        if not self._dreamer_usage_history:
            return 0.0
        return sum(self._dreamer_usage_history) / len(self._dreamer_usage_history)
        
    def detect_overreliance(self) -> bool:
        """Detect if collective is over-relying on Dreamer.
        
        Triggers when:
        - Position change ratio > 0.15 (DEL-02 requirement)
        - Dreamer usage rate > 0.4 of all deliberations
        """
        return (
            self.calculate_position_change_ratio() > 0.15 or
            self.calculate_dreamer_usage_rate() > 0.4
        )
```

### 3.5 Phase 5: Dreamer Agent Integration

**Files Modified**: `src/heretek_swarm/actors/dreamer.py`

#### 3.5.1 New Message Handlers

Add to `get_handlers()`:

```python
def get_handlers(self) -> dict[str, callable]:
    """Return message handlers for Dreamer agent."""
    return {
        # ... existing handlers ...
        "generate_novel_connections": self._handle_generate_novel_connections,
        "get_lateral_thinking_metrics": self._handle_get_lateral_thinking_metrics,
        "track_deliberation_contribution": self._handle_track_deliberation_contribution,
    }
```

#### 3.5.2 Novel Connections Handler

```python
async def _handle_generate_novel_connections(
    self, message: ActorMessage
) -> dict[str, Any] | None:
    """
    Generate novel connections between concepts.

    Content expected:
    {
        "concepts": ["concept1", "concept2", ...],
        "technique": "random_association",
        "target_count": 5
    }
    """
    try:
        content = validate_message(message.content, "DreamerNovelConnections")
        concepts = content.get("concepts", [])
        technique = ConnectionTechnique(content.get("technique", ConnectionTechnique.RANDOM_ASSOCIATION.value))
        target_count = content.get("target_count", 5)
        
        # Generate connections
        connections = await self._connection_engine.generate_connections(
            concepts=concepts,
            technique=technique,
            target_count=target_count,
        )
        
        # Validate connections through HarmfulContentFilter
        validated_connections = []
        rejected_count = 0
        for conn in connections:
            is_safe, reason = await self._content_filter.validate_connection(conn)
            if is_safe:
                conn.validated = True
                validated_connections.append(conn)
            else:
                conn.validated = False
                conn.validation_notes = reason
                rejected_count += 1
                
        # Update metrics
        await self._metrics_tracker.track_session(
            session_id=message.correlation_id or str(uuid.uuid4()),
            metrics=self._calculate_session_metrics(connections, validated_connections, rejected_count)
        )
        
        return {
            "status": "success",
            "connections_generated": len(connections),
            "validated_count": len(validated_connections),
            "rejected_count": rejected_count,
            "connections": [self._connection_to_dict(c) for c in validated_connections],
        }
        
    except Exception as e:
        logger.error("Failed to generate novel connections", error=str(e))
        return {"status": "error", "error": str(e)}
```

#### 3.5.3 Deliberation Contribution Handler

```python
async def _handle_track_deliberation_contribution(
    self, message: ActorMessage
) -> dict[str, Any] | None:
    """Track how Dreamer ideas contributed to deliberation outcomes."""
    try:
        content = validate_message(message.content, "DreamerDeliberationContribution")
        deliberation_id = content.get("deliberation_id")
        idea_ids = content.get("idea_ids", [])
        outcome = content.get("outcome")  # "accepted", "rejected", "modified"
        
        # Record contribution for metrics
        self._metrics_tracker.record_deliberation_contribution(
            deliberation_id=deliberation_id,
            ideas=idea_ids,
            outcome=outcome,
        )
        
        return {
            "status": "success",
            "contribution_recorded": True,
        }
    except Exception as e:
        logger.error("Failed to track deliberation contribution", error=str(e))
        return {"status": "error", "error": str(e)}
```

---

## 4. File Structure

### 4.1 Created Files

| File | Description |
|------|-------------|
| `src/heretek_swarm/creativity/__init__.py` | Package init with exports |
| `src/heretek_swarm/creativity/novel_connections.py` | Lateral thinking module (main deliverable) |

### 4.2 Modified Files

| File | Changes |
|------|---------|
| `src/heretek_swarm/actors/dreamer.py` | Add novel connection handlers, integrate metrics tracker |

### 4.3 New Module Structure

```
src/heretek_swarm/creativity/
├── __init__.py
│   └── exports: NovelConnection, NovelConnectionEngine, LateralThinkingMetricsTracker, etc.
└── novel_connections.py
    ├── NovelConnection              # Dataclass
    ├── AssociationDistance          # Dataclass  
    ├── LateralThinkingMetrics       # Dataclass
    ├── ConnectionTechnique         # Enum
    ├── HarmfulContentFilter        # Class
    ├── NovelConnectionEngine        # Class
    ├── LateralThinkingMetricsTracker  # Class
    └── create_novel_connection_session()  # Factory
```

---

## 5. Edge Cases & Mitigation

### 5.1 Harmful Creative Content

**Scenario**: Dreamer generates novel connections that could be harmful or dangerous.

**Mitigation**:
1. `HarmfulContentFilter` checks against known harmful patterns
2. High association_distance (>0.8) triggers mandatory Beta validation
3. Steward can send `suppress_dreamer` message to halt Dreamer output
4. All rejected connections logged with reason for audit

**Implementation**:
```python
async def validate_connection(self, connection: NovelConnection) -> tuple[bool, str | None]:
    # Pattern check first
    if self._matches_harmful_pattern(connection):
        return False, "Harmful pattern detected"
    
    # Mandatory Beta validation for extreme connections
    if connection.association_distance > 0.8:
        beta_result = await self._request_beta_validation(connection)
        if not beta_result.is_safe:
            await self._notify_steward_of_rejection(connection, beta_result.reason)
            return False, beta_result.reason
    
    return True, None
```

### 5.2 Over-reliance on Dreamer

**Scenario**: Collective begins excessively relying on Dreamer output, reducing diversity of thinking.

**Mitigation**:
1. `LateralThinkingMetricsTracker` monitors position change ratio
2. If position_change_ratio > 0.15, alert Steward
3. Dreamer can be configured to reduce output frequency
4. Steward can set `dreamer_usage_cap` to limit Dreamer contributions

**Implementation**:
```python
def detect_overreliance(self) -> bool:
    position_change_ratio = self.calculate_position_change_ratio()
    dreamer_usage_rate = self.calculate_dreamer_usage_rate()
    
    if position_change_ratio > 0.15:
        logger.warning("Over-reliance detected: position_change_ratio exceeded 0.15")
        self._notify_steward_overreliance(position_change_ratio, dreamer_usage_rate)
        return True
    return False
```

### 5.3 Deliberation Deadlock Due to Excessive Ideas

**Scenario**: Dreamer generates too many novel connections, causing deliberation paralysis.

**Mitigation**:
1. `NovelConnectionEngine.max_connections_per_session` limits output
2. Sessions have configurable timeout
3. Steward can prioritize subset of ideas for deliberation

---

## 6. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Novel connections generated | Connections with association_distance > 0.5 | ≥ 3 per session |
| Lateral thinking metrics | MetricsTracker's creativity_score | ≥ 50/100 average |
| Content safety | Connections rejected by Beta / total | < 1% false positive |
| Over-reliance detection | Position change ratio monitoring | Operational, alerts at > 0.15 |
| Deliberation contribution | Ideas submitted to deliberation | ≥ 1 per significant deliberation |
| Suppression capability | Steward can halt Dreamer | Verified within 5 seconds |

---

## 7. Dependencies

| Dependency | Source | Required For |
|------------|--------|--------------|
| AgentActor base | Phase 1 | DreamerAgent base |
| ValidationMixin | Phase 1 | Input validation |
| DeliberationMixin | Phase 1 | Consensus participation |
| BetaAgent | Phase 1 (GOV-03) | Harmful content validation |
| Steward | Phase 1 (GOV-01) | Over-reliance alerts, suppression |
| ZeroTrustValidator | Phase 1 (ZERO-03) | Session 44 validation |

---

## 8. Testing Strategy

### 8.1 Unit Tests

**File**: `tests/creativity/test_novel_connections.py`

```python
async def test_novel_connection_engine_generates_connections():
    """Test NovelConnectionEngine can generate connections."""
    engine = NovelConnectionEngine()
    connections = await engine.generate_connections(
        concepts=["AI", "biology", "music"],
        technique=ConnectionTechnique.ANALOGICAL_BRIDGING,
        target_count=5,
    )
    assert len(connections) > 0
    assert all(c.association_distance > 0 for c in connections)

async def test_association_distance_calculation():
    """Test association distance is calculated correctly."""
    engine = NovelConnectionEngine()
    distance = await engine._calculate_association_distance(
        source_concepts=["AI"],
        target_concepts=["cooking"],
    )
    assert 0 <= distance <= 1
    # AI to cooking should have high distance

async def test_harmful_content_filter_rejects_extremes():
    """Test HarmfulContentFilter rejects dangerous connections."""
    filter = HarmfulContentFilter()
    dangerous_connection = NovelConnection(
        connection_id="test",
        source_concepts=["weaponry"],
        connected_concepts=[" AI"],
        # ... other required fields
        association_distance=0.95,  # Very extreme
    )
    is_safe, reason = await filter.validate_connection(dangerous_connection)
    assert is_safe is False
    assert reason is not None

async def test_metrics_tracker_detects_overreliance():
    """Test LateralThinkingMetricsTracker detects over-reliance."""
    tracker = LateralThinkingMetricsTracker()
    # Simulate high position change ratio
    for _ in range(60):
        tracker._position_change_history.append(1.0)
    tracker._position_change_history.append(0.0)  # Change
    
    assert tracker.calculate_position_change_ratio() > 0.15
    assert tracker.detect_overreliance() is True
```

### 8.2 Integration Tests

**File**: `tests/creativity/test_dreamer_lateral_integration.py`

```python
async def test_dreamer_generates_novel_connections_handler():
    """Test Dreamer agent can handle novel connections request."""
    dreamer = DreamerAgent()
    await dreamer.spawn()
    
    response = await dreamer._handle_generate_novel_connections(
        ActorMessage(
            sender="test",
            message_type="generate_novel_connections",
            content={"concepts": ["AI", "ethics"], "target_count": 3},
            timestamp=datetime.now(UTC).isoformat(),
        )
    )
    
    assert response["status"] == "success"
    assert response["connections_generated"] >= 3

async def test_beta_validation_integration():
    """Test Dreamer integrates with Beta for content safety."""
    # Setup with mock Beta
    beta = BetaAgent()
    dreamer = DreamerAgent(beta_agent=beta)
    
    # Generate extreme connection
    response = await dreamer._handle_generate_novel_connections(
        ActorMessage(
            sender="test",
            message_type="generate_novel_connections",
            content={"concepts": ["dangerous"], "association_distance_threshold": 0.9},
            timestamp=datetime.now(UTC).isoformat(),
        )
    )
    
    # Beta should have validated
    # ...
```

---

## 9. Implementation Order

### Week 1: Core Data Models
1. Create `src/heretek_swarm/creativity/__init__.py`
2. Create `NovelConnection`, `ConnectionTechnique`, `LateralThinkingMetrics` dataclasses/enums
3. Basic module structure in `novel_connections.py`

### Week 2: NovelConnectionEngine
4. Implement `NovelConnectionEngine` class
5. Implement connection technique methods (random_association, analogical_bridging, cross_domain_import)
6. Implement `_calculate_association_distance()`
7. Basic integration test

### Week 3: Safety Integration
8. Implement `HarmfulContentFilter` class
9. Implement Beta validation flow
10. Add Steward notification for rejected content
11. Test safety integration

### Week 4: Metrics & Over-reliance
12. Implement `LateralThinkingMetricsTracker`
13. Implement position change ratio monitoring
14. Add over-reliance detection and alerting
15. Complete metrics tests

### Week 5: Dreamer Agent Integration
16. Add handlers to `dreamer.py`: `generate_novel_connections`, `get_lateral_thinking_metrics`
17. Integrate `NovelConnectionEngine` into DreamerAgent
18. Test handler integration

### Week 6: Testing & Verification
19. Write comprehensive unit tests
20. Integration testing with full agent stack
21. Verify all edge cases handled
22. Document verification results

---

## 10. Open Questions

1. **Association distance baseline**: What concepts should we use to calibrate "expected" vs "unexpected" connections?
2. **Maximum connections per session**: What is a reasonable limit? (propose: 20)
3. **Beta validation timeout**: How long should we wait for Beta validation? (propose: 30 seconds)
4. **Over-reliance threshold**: Should the 0.15 position_change_ratio be configurable?
5. **Dreamer suppression granularity**: Can Steward suppress specific techniques or all Dreamer output?

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Novel connections generated per session | ≥ 5 | Average count |
| Average association distance | ≥ 0.5 | Higher = more novel |
| Creativity score | ≥ 50/100 | LateralThinkingMetrics.creativity_score |
| Content safety precision | ≥ 99% | (True positives) / (True + False positives) |
| Over-reliance detection latency | < 5s | Time to alert Steward |
| Dreamer contribution to deliberation | ≥ 10% | % of deliberations with Dreamer input |

---

## 12. Deliberation Integration Details

### 12.1 How Dreamer Contributes to Deliberation

Dreamer contributes lateral thinking to deliberation by:

1. **Generating Alternative Perspectives**: When deliberation stalls, Dreamer can inject novel connections
2. **Challenging Assumptions**: Dreamer ideas can prompt agents to reconsider positions
3. **Expanding Solution Space**: Dreamer connections reveal new solution dimensions

### 12.2 Deliberation Message Format

```python
@dataclass 
class DreamerDeliberationContribution:
    """Dreamer's contribution to a deliberation."""
    deliberation_id: str
    contribution_type: str  # "novel_connection", "assumption_challenge", "perspective_expansion"
    related_idea_ids: list[str]
    expected_impact: str  # "breakthrough", "substantial", "incremental"
    position_change_prediction: float  # How much this might change positions
```

### 12.3 Position Change Ratio Tracking

Per DEL-02 requirements, the collective must maintain position change ratio ≥ 15%. Dreamer's metrics tracker helps monitor this:

- Track when Dreamer ideas cause agents to change deliberation positions
- Report to Steward when ratio approaches limits
- Alert when Dreamer contributions consistently trigger position changes

---

**Plan Status**: Ready for Implementation  
**Next Action**: Begin Week 1 - Core Data Models