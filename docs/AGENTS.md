# Heretek Swarm Agents

**Version:** 2.0.0  
**Date:** 2026-04-10  
**Status:** Production-Ready

Reference documentation for all 23 agents in the Heretek Swarm collective.

---

## Table of Contents

1. [Agent Overview](#agent-overview)
2. [Tier 1: Core Triad](#tier-1-core-triad)
3. [Tier 2: Support Agents](#tier-2-support-agents)
4. [Tier 3: Exploration Agents](#tier-3-exploration-agents)
5. [Tier 4: Safety & Security](#tier-4-safety--security)
6. [Tier 5: Coordination Agents](#tier-5-coordination-agents)
7. [Tier 6: Enhancement Agents](#tier-6-enhancement-agents)
8. [Agent Factory](#agent-factory)

---

## Agent Overview

All 23 agents are implemented in [`src/heretek_swarm/actors/`](../src/heretek_swarm/actors/). Each agent inherits from the [`AgentActor`](../src/heretek_swarm/actors/base.py) base class which provides:

- Async message handling
- State management with PostgreSQL persistence
- Health monitoring
- Zero-Trust input validation
- NATS event mesh integration

### Agent Registry

| Agent | File | Tier | Role |
|-------|------|------|------|
| Steward | [`triad.py`](src/heretek_swarm/actors/triad.py) | 1 | Governance & Orchestration |
| Alpha | [`triad.py`](src/heretek_swarm/actors/triad.py) | 1 | Deep Analysis |
| Beta | [`triad.py`](src/heretek_swarm/actors/triad.py) | 1 | Validation |
| Charlie | [`triad.py`](src/heretek_swarm/actors/triad.py) | 1 | Challenge |
| Historian | [`historian.py`](src/heretek_swarm/actors/historian.py) | 2 | Memory & Knowledge |
| Metis | [`metis.py`](src/heretek_swarm/actors/metis.py) | 2 | Strategic Planning |
| Empath | [`empath.py`](src/heretek_swarm/actors/empath.py) | 2 | Emotional Intelligence |
| Perceiver | [`perceiver.py`](src/heretek_swarm/actors/perceiver.py) | 2 | Multi-Modal Input |
| Echo | [`echo.py`](src/heretek_swarm/actors/echo.py) | 2 | Communication |
| Explorer | [`explorer.py`](src/heretek_swarm/actors/explorer.py) | 3 | Discovery |
| Examiner | [`examiner.py`](src/heretek_swarm/actors/examiner.py) | 3 | Quality Assurance |
| Dreamer | [`dreamer.py`](src/heretek_swarm/actors/dreamer.py) | 3 | Creative Generation |
| Coder | [`coder.py`](src/heretek_swarm/actors/coder.py) | 3 | Implementation |
| Sentinel | [`sentinel.py`](src/heretek_swarm/actors/sentinel.py) | 4 | Safety Guardian |
| Sentinel-Prime | [`sentinel_prime.py`](src/heretek_swarm/actors/sentinel_prime.py) | 4 | Security Commander |
| Arbiter | [`arbiter.py`](src/heretek_swarm/actors/arbiter.py) | 4 | Conflict Resolution |
| Coordinator | [`coordinator.py`](src/heretek_swarm/actors/coordinator.py) | 5 | Multi-Agent Sync |
| Nexus | [`nexus.py`](src/heretek_swarm/actors/nexus.py) | 5 | External Integration |
| Catalyst | [`catalyst.py`](src/heretek_swarm/actors/catalyst.py) | 5 | Change Management |
| Chronos | [`chronos.py`](src/heretek_swarm/actors/chronos.py) | 5 | Scheduling |
| Prism | [`prism.py`](src/heretek_swarm/actors/prism.py) | 6 | Multi-Perspective |
| Habit-Forge | [`habit_forge.py`](src/heretek_swarm/actors/habit_forge.py) | 6 | Behavior Optimization |
| Perceiver+ | [`perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py) | 6 | Advanced Analytics |

---

## Tier 1: Core Triad

The Core Triad consists of 4 agents: Steward, Alpha, Beta, and Charlie. All are implemented in [`triad.py`](src/heretek_swarm/actors/triad.py).

### Steward Agent

**Role:** Orchestrator - The central nervous system of the collective.

**Capabilities:**
- Task routing and delegation
- System health monitoring
- Deliberation orchestration
- Decision collection and finalization

**Key Methods:**
```python
async def route_task(self, task: Task, target_agents: List[str]) -> str
async def monitor_health(self) -> HealthStatus
async def orchestrate_deliberation(self, topic: str) -> DeliberationResult
```

**Prime Directive Alignment:** "The central nervous system that monitors the system's vital pulse and routes tasks."

### Alpha Agent

**Role:** Deep Analysis - Comprehensive examination and logical deconstruction.

**Capabilities:**
- Deep analysis of complex topics
- Proposal generation
- Logical structure decomposition
- Multi-perspective evaluation

**Key Methods:**
```python
async def analyze_deeply(self, topic: str, context: Dict) -> AnalysisResult
async def generate_proposal(self, analysis: AnalysisResult) -> Proposal
async def evaluate_options(self, options: List[Option]) -> Evaluation
```

**Prime Directive Alignment:** "Comprehensive examination and logical deconstruction."

### Beta Agent

**Role:** Validation - Error detection, reality-checking, and blast-radius projection.

**Capabilities:**
- Input validation
- Output verification
- Error detection
Result
async def assess_impact(self, action: Action) -> ImpactAssessment
async def detect_errors(self, content: str) -> List[Error]
```

**Prime Directive Alignment:** "Error detection, reality-checking, and blast-radius projection."

### Charlie Agent

**Role:** Challenge - Critical review, risk assessment, adversarial thinking.

**Capabilities:**
- Critical review of proposals
- Adversarial testing
- Risk assessment
- Defense counsel during system reviews
- Red team analysis

**Key Methods:**
```python
async def challenge_proposal(self, proposal: Proposal) -> ChallengeResult
async def assess_risks(self, action: Action) -> RiskAssessment
async def red_team(self, target: str) -> RedTeamResult
async def provide_counterarguments(self, argument: Argument) -> List[CounterArgument]
```

**Prime Directive Alignment:** "Critical review, risk assessment, adversarial thinking, and defense counsel."

---

## Tier 2: Support Agents

### Historian Agent

**File:** [`historian.py`](src/heretek_swarm/actors/historian.py)

**Role:** Memory & Knowledge - Information synthesis and precedent logging.

**Capabilities:**
- Memory storage and retrieval
- Knowledge graph maintenance
- Precedent logging
- Lineage tracking
- Temporal queries

**Key Methods:**
```python
async def store_memory(self, memory: MemoryEntry) -> str
async def retrieve_memories(self, query: str) -> List[MemoryEntry]
async def log_precedent(self, event: Event, outcome: Outcome) -> str
async def get_lineage(self, entity_id: str) -> Lineage
```

**Prime Directive Alignment:** "Information synthesis and precedent logging."

### Metis Agent

**File:** [`metis.py`](src/heretek_swarm/actors/metis.py)

**Role:** Strategic Planning - Long-term timeline generation and impact analysis.

**Capabilities:**
- Strategic planning
- Resource allocation
- Timeline generation
- Impact analysis
- Scenario planning

**Key Methods:**
```python
async def create_strategy(self, objective: Objective) -> Strategy
async def allocate_resources(self, strategy: Strategy) -> ResourceAllocation
async def generate_timeline(self, project: Project) -> Timeline
async def analyze_impact(self, action: Action) -> ImpactAnalysis
```

**Prime Directive Alignment:** "Long-term timeline generation and impact analysis."

### Empath Agent

**File:** [`empath.py`](src/heretek_swarm/actors/empath.py)

**Role:** Emotional Intelligence - Sentiment analysis and human-AI resonance.

**Capabilities:**
- Sentiment analysis
- Emotional state tracking
- Conflict mediation
- Human-AI resonance
- Tone adaptation

**Key Methods:**
```python
async def analyze_sentiment(self, text: str) -> SentimentAnalysis
async def track_emotional_state(self, user_id: str) -> EmotionalState
async def mediate_conflict(self, parties: List[Party]) -> MediationResult
async def adapt_tone(self, context: Context) -> AdaptedResponse
```

**Prime Directive Alignment:** "Sentiment analysis and human-AI resonance."

### Perceiver Agent

**File:** [`perceiver.py`](src/heretek_swarm/actors/perceiver.py)

**Role:** Sensory Input - Multi-modal data ingestion.

**Capabilities:**
- Multi-modal input processing
- Signal normalization
- Noise filtering
- Context extraction
- Data validation Directive Alignment:** "Multi-modal data ingestion."

### Echo Agent

**File:** [`echo.py`](src/heretek_swarm/actors/echo.py)

**Role:** Communication - Translation and multi-channel protocol management.

**Capabilities:**
- Multi-channel communication
- Protocol translation
- Message formatting
- Response templating
- Cross-channel synchronization

**Key Methods:**
```python
async def translate_message(self, message: Message, target_protocol: Protocol) -> Translated: Format) -> FormattedResponse
async def sync_channels(self, message_id: str) -> SyncResult
```

**Prime Directive Alignment:** "Translation and multi-channel protocol management."

---

## Tier 3: Exploration Agents

### Explorer Agent

**File:** [`explorer.py`](src/heretek_swarm/actors/explorer.py)

**Role:** Discovery - Proactive research and information gathering.

**Capabilities:**
- Source monitoring
- Anomaly detection
- Proactive research
- Trend identification
- Intelligence gathering

**Key Methods:**
```python
async def explore_topic(self, topic: str) -> ExplorationResult
async def monitor_sources(self, sources: List[Source]) -> List[Discovery]
async def detect_anomalies(self) -> List[Anomaly]
async def gather_intelligence(self, query: str) -> IntelligenceReport
```

**Prime Directive Alignment:** "Proactive research and information gathering."

### Examiner Agent

**File:** [`examiner.py`](src/heretek_swarm/actors/examiner.py)

**Role:** Quality Assurance - Stress-testing and capability validation.

**Capabilities:**
- Test plan generation
- Code analysis
- Stress testing
- Capability validation
- Quality assessment

**Key Methods:**
```python
async def generate_test_plan(self, code: str) -> TestPlan
async def analyze_code(self, code: str) -> CodeAnalysis
async def stress_test(self, target: str, parameters: TestParameters) -> StressTestResult
async def validate_capabilities(self, agent: Agent) -> CapabilityValidation
```

**Prime Directive Alignment:** "Stress-testing and capability validation."

### Dreamer Agent

**File:** [`dreamer.py`](src/heretek_swarm/actors/dreamer.py)

**Role:** Creative Generation - Lateral thinking and novel solution synthesis.

**Capabilities:**
- Creative solution generation
- Novel approach synthesis
- Lateral thinking
- Idea combination
- Innovation facilitation

**Key Methods:**
```python
async def generate_ideas(self, context: Context) -> List[Idea]
async def combine_concepts(self, concepts: List[Concept]) -> NovelConcept
async def explore_alternatives(self, solution: Solution) -> List[Alternative]
async def synthesize_novel(self, inputs: List[Any]) -> Synthesis
```

**Prime Directive Alignment:** "Lateral thinking and novel solution synthesis."

### Coder Agent

**File:** [`coder.py`](src/heretek_swarm/actors/coder.py)

**Role:** Implementation - Autonomous code writing, debugging, and system expansion.

**Capabilities:**
- Code generation
- Code review
- Safe execution (no eval/exec)
- Debugging assistance
- System expansion

**Key Methods:**
```python
async def generate_code(self, specification: Specification) -> GeneratedCode
async def review_code(self, code: str) -> CodeReview
async def debug_issue(self, error: Error) -> DebugResult
async def execute_safely(self, code: str, context: ExecutionContext) -> ExecutionResult
```

**Prime Directive Alignment:** "Autonomous code writing, debugging, and system expansion."

---

## Tier 4: Safety & Security

### Sentinel Agent

**File:** [`sentinel.py`](src/heretek_swarm/actors/sentinel.py)

**Role:** Safety Guardian - Emergency reflex and anomaly response.

**Capabilities:**
- Input validation
- Safety checks
- Anomaly detection
- Threat response: Action) -> SafetyCheckResult
async def respond_to_anomaly(self, anomaly: Anomaly) -> ResponseAction
async def quarantine(self, target: str, reason: str) -> QuarantineResult
async def clear_anomaly(self, anomaly_id: str) -> ClearResult
```

**Prime Directive Alignment:** "The emergency reflex that responds to anomalies to freeze or isolate threats."

### Sentinel-Prime Agent

**File:** [`sentinel_prime.py`](src/heretek_swarm/actors/sentinel_prime.py)

**Role:** Security Commander - External threat response and containment.

**Capabilities:**
- External threat detection
- Threat analysis
- Containment strategies
- Security response coordination
- Incident management

**Key Methods:**
```python
async def detect_external_threat(self, signal: Signal) -> ThreatDetection
async def analyze_threat(self, threat: Threat) -> ThreatAnalysis
async def contain_threat(self, threat: Threat) -> ContainmentResult
async def coordinate_response(self, incident: Incident) -> CoordinatedResponse
async def manage_incident(self, incident: Incident) -> IncidentManagement
```

**Prime Directive Alignment:** "External threat response and containment."

### Arbiter Agent

**File:** [`arbiter.py`](src/heretek_swarm/actors/arbiter.py)

**Role:** Conflict Resolution - Dispute mediation during systemic consensus failures.

**Capabilities:**
- Conflict detection
- Dispute mediation
- Decision arbitration
- Fair resolution
- Consensus facilitation

**Key Methods:**
```python
async def detect_conflict(self) -> ConflictDetection
async def mediate_dispute(self, parties: List[Party], issue: Issue) -> MediationResult
async def arbitrate(self, case: Case) -> ArbitrationResult
async def resolve_fairly(self, dispute: Dispute) -> FairResolution
async def facilitate_consensus(self, deadlocked_parties: List[Party]) -> ConsensusResult
```

**Prime Directive Alignment:** "Dispute mediation during systemic consensus failures."

---

## Tier 5: Coordination Agents

### Coordinator Agent

**File:** [`coordinator.py`](src/heretek_swarm/actors/coordinator.py)

**Role:** Multi-Agent Sync - Task dependency and timeline synchronization.

**Capabilities:**
- Task coordination
- Dependency resolution
- Timeline synchronization
- Resource scheduling
- Progress tracking

**Key Methods:**
```python
async def coordinate_tasks(self, tasks: List[Task]) -> CoordinationResult
async def resolve_dependencies(self, task_graph: TaskGraph) -> DependencyResolution
async def sync_timelines(self, timelines: List[Timeline]) -> SyncResult
async def schedule_resources(self, tasks: List[Task]) -> Schedule
async def track_progress(self, workflow_id: str) -> ProgressReport
```

**Prime Directive Alignment:** "Task dependency and timeline synchronization."

### Nexus Agent

**File:** [`nexus.py`](src/heretek_swarm/actors/nexus.py)

**Role:** External Integration - Gateway management to human systems and APIs.

**Capabilities:**
- API integration
- Webhook management
- External system connection
- Data transformation
- Protocol adaptation

**Key Methods:**
```python
async def connect_api(self, api_config: APIConfig) -> ConnectionResult
async def manage_webhooks(self, webhooks: List[Webhook]) -> WebhookManagement
async def transform_protocol: Protocol) -> AdaptedMessage
```

**Prime Directive Alignment:** "Gateway management to human systems and APIs."

### Catalyst Agent

**File:** [`catalyst.py`](src/heretek_swarm/actors/catalyst.py)

**Role:** Change Management - Handling systemic shifts and paradigm transitions.

**Capabilities:**
- Change request processing
- Impact analysis
- Transition management
- Rollback coordination
- Paradigm shift handling

**Key Methods:**
```python
async def process_change_request(self, request: ChangeRequest) -> ChangeResult
async def analyze_impact(self, change: Change) -> ImpactAnalysis
async def manage_transition(self, transition: Transition) -> TransitionResult
async def coordinate_rollback(self, rollback: Rollback) -> RollbackResult
async def handle_paradigm_shift(self, shift: ParadigmShift) -> ShiftResult
```

**Prime Directive Alignment:** "Handling systemic shifts and paradigm transitions."

### Chronos Agent

**File:** [`chronos.py`](src/heretek_swarm/actors/chronos.py)

**Role:** Temporal/Scheduling - Time perception and long-running execution management.

**Capabilities:**
- Task scheduling
- Deadline tracking
- Time perception
- Long-running execution management
- Temporal reasoning

**Key Methods:**
```python
async def schedule_task(self, task: Task, schedule: Schedule) -> SchedulingResult
async def track_deadlines(self) -> DeadlineReport
async def manage_long_running(self, execution: Execution) -> LongRunningResult
async def reason_temporally(self, context: TemporalContext) -> TemporalReasoning
```

**Prime Directive Alignment:** "Time perception and long-running execution management."

---

## Tier 6: Enhancement Agents

### Prism Agent

**File:** [`prism.py`](src/heretek_swarm/actors/prism.py)

**Role:** Multi-Perspective - Forcing diverse, non-standard viewpoints into consensus.

**Capabilities:**
- Multi-perspective analysis
- Bias detection
- Diverse viewpoint generation
- Perspective synthesis
- Opinion diversity assessment

**Key Methods:**
```python
async def analyze_perspectives(self, topic: str) -> List[Perspective]
async def detect_bias(self, content: Content) -> BiasDetection
async def generate_diverse_views(self, topic: str) -> List[DiverseView]
async def synthesize_perspectives(self, perspectives: List[Perspective]) -> Synthesis
async def assess_diversity(self, opinions: List[Opinion]) -> DiversityAssessment
```

**Prime Directive Alignment:** "Forcing diverse, non-standard viewpoints into consensus."

### Habit-Forge Agent

**File:** [`habit_forge.py`](src/heretek_swarm/actors/habit_forge.py)

**Role:** Behavior Optimization - Building operational efficiency patterns and recording established precedents.

**Capabilities:**
- Habit creation
- Pattern analysis
- Efficiency optimization
- Precedent recording
- Behavioral adaptation

**Key Methods:**
```python
async def create_habit(self, behavior: Behavior) -> HabitResult
async def analyze_patterns(self) -> PatternAnalysis
async def optimize_efficiency(self, process: Process) -> OptimizationResult
async def record_precedent(self, event: Event) -> PrecedentRecord
async def adapt_behavior(self, feedback: Feedback) -> BehavioralAdaptation
```

**Prime Directive Alignment:** "Building operational efficiency patterns and recording established precedents."

### Perceiver+ Agent

**File:** [`perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py)

**Role:** Advanced Analytics - Meta-perception and signal-from-noise extraction.

**Capabilities:**
- Statistical analysis
- Forecasting
- Trend analysis
- Signal extraction
- Meta-perception

**Key Methods:**
```python DataSeries) -> List[Trend]
```

**Prime Directive Alignment:** "Meta-perception and signal-from-noise extraction."

---

## Agent Factory

**File:** [`factory.py`](src/heretek_swarm/actors/factory.py)

The Agent Factory provides centralized agent instantiation:

```python
from heretek_swarm.actors.factory import AgentFactory

factory = AgentFactory()

# Create agents
steward = await factory.create_agent("steward")
alpha = await factory.create_agent("alpha")
beta = await factory.create_agent("beta")

# Create by type
core_triad = await factory.create_tier1_agents()
support_agents = await factory.create_tier2_agents()
exploration_agents = await factory.create_tier3_agents()

# Create entire collective
all_agents = await factory.create_all_agents()
```

### Factory Methods

| Method | Description |
|--------|-------------|
| `create_agent(name)` | Create single agent by name |
| `create_tier1_agents()` | Create Core Triad (Steward, Alpha, Beta, Charlie) |
| `create_tier2_agents()` | Create Support Agents (Historian, Metis, Empath, Perceiver, Echo) |
| `create_tier3_agents()` | Create Exploration Agents (Explorer, Examiner, Dreamer, Coder) |
| `create_tier4_agents()` | Create Safety Agents (Sentinel, Sentinel-Prime, Arbiter) |
| `create_tier5_agents()` | Create Coordination Agents (Coordinator, Nexus, Catalyst, Chronos) |
| `create_tier6_agents()` | Create Enhancement Agents (Prism, Habit-Forge, Perceiver+) |
| `create_all_agents()` | Create entire 23-agent collective |

---

## Handoff System

**Files:** [`handoff.py`](src/heretek_swarm/actors/handoff.py), [`handoff_handlers.py`](src/heretek_swarm/actors/handoff_handlers.py)

Agents communicate via a structured handoff system:

```python
from heretek_swarm.actors.handoff import Handoff, HandoffHandler

# Create handoff
handoff = Handoff(
    source_agent="steward",
    target_agent="alpha",
    task_id="task-123",
    priority="high",
    context={"topic": "analysis request"}
)

# Send handoff
handler = HandoffHandler()
await handler.send_handoff(handoff)

# Receive handoff
received = await handler.receive_handoff("alpha")
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [PRIME_DIRECTIVE.md](../PRIME_DIRECTIVE.md) - 23-agent vision and philosophy
- [CONSCIOUSNESS_PLUGINS.md](CONSCIOUSNESS_PLUGINS.md) - Consciousness framework

---

**License:** Apache 2.0
