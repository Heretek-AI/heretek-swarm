# HERETEK SWARM: 23 AGENT ARCHITECTURE SPECIFICATIONS
## Detailed Specifications for All Sovereign Agents

---

## TIER 1: CORE TRIAD (Governance)

### 1.1 Steward (Orchestrator)

**File:** `src/heretek_swarm/actors/steward.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, HealthReportingMixin

**Responsibilities:**
- Central nervous system of the swarm
- Monitors system vital pulse
- Routes tasks to appropriate agents
- Detects anomalies and triggers Sentinel
- Maintains system homeostasis

**Key Methods:**
```python
async def _monitor_system_health() -> dict[str, Any]:
    """Monitor token velocity, latency, context-switching"""

async def _broadcast_pulse(pulse_data: dict) -> None:
    """Broadcast heartbeat to NATS mesh"""

async def _route_task(task: TaskMessage) -> AgentResponse:
    """Route task to appropriate agent based on type"""

async def _trigger_sentinel(anomaly: AnomalyReport) -> None:
    """Alert Sentinel to potential threat"""

async def _convene_triad(issue: SystemIssue) -> TribunalDecision:
    """Convene Core Triad for deliberation"""
```

**NATS Subjects:**
- `steward.pulse` - Heartbeat broadcasts
- `steward.tasks` - Task routing
- `steward.anomaly` - Anomaly alerts to Sentinel

**Dependencies:**
- All Tier 2-6 agents (receives status updates)
- Sentinel (triggers when anomaly detected)
- Historian (logs decisions)

---

### 1.2 Alpha (Deep Analysis)

**File:** `src/heretek_swarm/actors/alpha.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, MemoryMixin

**Responsibilities:**
- Comprehensive examination of problems
- Logical deconstruction of complex issues
- Solution generation through systematic analysis
- Deep reasoning over surface-level solutions

**Key Methods:**
```python
async def _analyze_problem(problem: ProblemStatement) -> AnalysisResult:
    """Comprehensive problem decomposition"""

async def _deconstruct_solution(solution: ProposedSolution) -> Deconstruction:
    """Break down solution into component parts"""

async def _generate_hypotheses(analysis: AnalysisResult) -> list[Hypothesis]:
    """Generate multiple hypotheses for testing"""

async def _synthesize_insights(insights: list[Insight]) -> SynthesizedInsight:
    """Combine insights into coherent understanding"""

async def _broadcast_to_workspace(insight: SynthesizedInsight) -> None:
    """Share insight with Global Workspace"""
```

**NATS Subjects:**
- `alpha.analysis` - Analysis requests
- `alpha.deconstruct` - Solution deconstruction
- `alpha.synthesis` - Synthesized insights

**Dependencies:**
- Steward (receives tasks from)
- Beta (receives validation from)
- Global Workspace (publishes insights)

---

### 1.3 Beta (Validation)

**File:** `src/heretek_swarm/actors/beta.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, PatternMixin

**Responsibilities:**
- Error detection and correction
- Reality-checking proposed solutions
- Blast-radius projection for changes
- Identifying potential failure modes

**Key Methods:**
```python
async def _validate_solution(solution: ProposedSolution) -> ValidationResult:
    """Validate solution against known patterns"""

async def _project_outcomes(solution: ProposedSolution) -> OutcomeProjection:
    """Project blast radius and consequences"""

async def _identify_failures(solution: ProposedSolution) -> list[FailureMode]:
    """Identify potential failure modes"""

async def _check_reality(solution: ProposedSolution) -> RealityCheckResult:
    """Verify solution is grounded in reality"""

async def _cross_validate(validation: ValidationResult) -> CrossValidation:
    """Cross-validate with pattern library"""
```

**NATS Subjects:**
- `beta.validation` - Validation requests
- `beta.projection` - Outcome projections
- `beta.failures` - Failure mode identification

**Dependencies:**
- Alpha (provides solutions for validation)
- Charlie (receives challenges from)
- PatternMixin (accesses pattern library)

---

### 1.4 Charlie (Challenge)

**File:** `src/heretek_swarm/actors/charlie.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin

**Responsibilities:**
- Critical review of all proposals
- Risk assessment and adversarial thinking
- Defense counsel during system reviews
- Identifying weaknesses before they become problems

**Key Methods:**
```python
async def _challenge_assumption(assumption: Assumption) -> ChallengeResult:
    """Challenge underlying assumptions"""

async def _assess_risk(proposal: Proposal) -> RiskAssessment:
    """Assess risk profile of proposal"""

async def _adversarial_think(solution: ProposedSolution) -> AdversarialResult:
    """Think like an attacker/adversary"""

async def _defend_decision(decision: Decision, evidence: Evidence) -> Defense:
    """Defend a decision during tribunal"""

async def _stress_test(solution: ProposedSolution) -> StressTestResult:
    """Stress test solution under adverse conditions"""
```

**NATS Subjects:**
- `charlie.challenge` - Challenge requests
- `charlie.risk` - Risk assessments
- `charlie.defense` - Defense arguments

**Dependencies:**
- Steward (receives instructions from)
- Beta (receives validations from)
- Arbiter (participates in tribunal)

---

## TIER 2: SUPPORT AGENTS (Knowledge & Memory)

### 2.1 Historian (Memory & Knowledge)

**File:** `src/heretek_swarm/actors/historian.py`
**Inherits:** AgentActor
**Mixin Pattern:** MemoryMixin, LearningMixin

**Responsibilities:**
- Information synthesis from all sources
- Precedent logging and retrieval
- Knowledge graph maintenance
- Historical context for decisions

**Key Methods:**
```python
async def _synthesize_information(sources: list[InformationSource]) -> Synthesis:
    """Synthesize information from multiple sources"""

async def _log_precedent(action: SystemAction, outcome: Outcome) -> Precedent:
    """Log action and outcome as precedent"""

async def _retrieve_precedent(situation: Situation) -> Precedent | None:
    """Retrieve relevant precedent for situation"""

async def _update_knowledge_graph(new_info: KnowledgeEntry) -> None:
    """Update the knowledge graph with new information"""

async def _generate_report(span: TimeSpan) -> HistoricalReport:
    """Generate historical analysis report"""
```

**NATS Subjects:**
- `historian.synthesis` - Information synthesis
- `historian.precedent` - Precedent logging
- `historian.query` - Precedent queries

**Dependencies:**
- All agents (logs actions)
- Steward (provides context)
- Mem0 (persistent memory)

---

### 2.2 Metis (Strategic Planning)

**File:** `src/heretek_swarm/actors/metis.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, MemoryMixin

**Responsibilities:**
- Long-term timeline generation
- Impact analysis for proposed changes
- Strategic roadmap development
- Multi-horizon planning

**Key Methods:**
```python
async def _generate_timeline(goal: Goal, horizon: TimeHorizon) -> Timeline:
    """Generate strategic timeline to goal"""

async def _analyze_impact(proposal: Proposal) -> ImpactAnalysis:
    """Analyze impact of proposal on system"""

async def _develop_roadmap(current_state: State, target_state: State) -> Roadmap:
    """Develop roadmap from current to target state"""

async def _assess_tradeoffs(options: list[Option]) -> TradeoffAssessment:
    """Assess tradeoffs between options"""

async def _project_consequences(action: Action) -> ConsequenceProjection:
    """Project long-term consequences of action"""
```

**NATS Subjects:**
- `metis.strategy` - Strategic requests
- `metis.timeline` - Timeline generation
- `metis.impact` - Impact analysis

**Dependencies:**
- Steward (receives strategic requests)
- Historian (uses precedent)
- Chronos (coordinates timing)

---

### 2.3 Empath (Emotional Intelligence)

**File:** `src/heretek_swarm/actors/empath.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, LearningMixin

**Responsibilities:**
- Sentiment analysis in communications
- Agent mood tracking and emotional state
- Conflict de-escalation and mediation
- Emotional context for decisions

**Key Methods:**
```python
async def _analyze_sentiment(text: str, context: Context) -> SentimentResult:
    """Analyze sentiment of text content"""

async def _track_agent_mood(agent_id: str) -> MoodState:
    """Track emotional state of an agent"""

async def _detect_conflict(agents: list[Agent]) -> ConflictReport | None:
    """Detect conflict between agents"""

async def _initiate_deescalation(conflict: Conflict) -> DeescalationResult:
    """Initiate de-escalation protocol"""

async def _provide_emotional_context(situation: Situation) -> EmotionalContext:
    """Provide emotional context for decisions"""
```

**NATS Subjects:**
- `empath.sentiment` - Sentiment analysis requests
- `empath.mood` - Agent mood tracking
- `empath.conflict` - Conflict detection

**Dependencies:**
- All agents (monitors communications)
- Coordinator (assists with conflicts)
- Arbiter (escalates conflicts to)

---

### 2.4 Perceiver (Sensory Input)

**File:** `src/heretek_swarm/actors/perceiver.py`
**Inherits:** AgentActor
**Mixin Pattern:** PatternMixin

**Responsibilities:**
- Multi-modal data ingestion
- External signal processing
- Environment perception
- Signal from noise extraction

**Key Methods:**
```python
async def _ingest_data(data: RawData, source: DataSource) -> ProcessedData:
    """Ingest and process raw data"""

async def _extract_signal(noise: SignalNoise) -> SignalExtraction:
    """Extract signal from noise"""

async def _perceive_environment() -> EnvironmentState:
    """Perceive current environment state"""

async def _filter_sensory_input(input: SensoryInput) -> FilteredInput:
    """Filter relevant sensory input"""

async def _detect_anomalies(input: SensoryInput) -> list[Anomaly]:
    """Detect anomalies in sensory input"""
```

**NATS Subjects:**
- `perceiver.data` - Data ingestion
- `perceiver.signal` - Signal extraction
- `perceiver.environment` - Environment perception

**Dependencies:**
- External systems (receives data from)
- Steward (reports to)
- Sentinel (alerts anomalies)

---

### 2.5 Echo (Communication)

**File:** `src/heretek_swarm/actors/echo.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin

**Responsibilities:**
- Translation between agent protocols
- Multi-channel protocol management
- Message formatting and routing
- Communication consistency

**Key Methods:**
```python
async def _translate_message(message: Message, target_protocol: Protocol) -> TranslatedMessage:
    """Translate message to target protocol"""

async def _manage_channel(channel: Channel) -> ChannelState:
    """Manage communication channel state"""

async def _format_message(content: Content, format: Format) -> FormattedMessage:
    """Format message for delivery"""

async def _route_message(message: Message, recipients: list[Agent]) -> DeliveryResult:
    """Route message to appropriate recipients"""

async def _ensure_consistency(message: Message) -> ConsistencyCheck:
    """Ensure message consistency across channels"""
```

**NATS Subjects:**
- `echo.translate` - Translation requests
- `echo.channel` - Channel management
- `echo.format` - Message formatting

**Dependencies:**
- All agents (facilitates communication)
- Nexus (coordinates external comms)
- Perceiver (receives external signals)

---

## TIER 3: EXPLORATION AGENTS (Discovery & Creation)

### 3.1 Explorer (Discovery)

**File:** `src/heretek_swarm/actors/explorer.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, LearningMixin

**Responsibilities:**
- Proactive research and information gathering
- Discovery of new capabilities and patterns
- Opportunity identification
- Knowledge frontier expansion

**Key Methods:**
```python
async def _research_topic(topic: Topic, depth: Depth) -> ResearchResult:
    """Conduct research on given topic"""

async def _discover_patterns(data: DataSet) -> list[Pattern]:
    """Discover patterns in data"""

async def _identify_opportunities(context: Context) -> list[Opportunity]:
    """Identify opportunities in context"""

async def _explore_boundary(frontier: Frontier) -> ExplorationResult:
    """Explore edge of known knowledge"""

async def _generate_insights(knowledge: Knowledge) -> list[Insight]:
    """Generate insights from gathered knowledge"""
```

**NATS Subjects:**
- `explorer.research` - Research requests
- `explorer.patterns` - Pattern discovery
- `explorer.opportunities` - Opportunity identification

**Dependencies:**
- Steward (receives tasks)
- Historian (contributes to knowledge)
- Dreamer (provides creative angle)

---

### 3.2 Examiner (Quality Assurance)

**File:** `src/heretek_swarm/actors/examiner.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, PatternMixin

**Responsibilities:**
- Stress-testing and capability validation
- Quality assurance for all outputs
- Benchmarking and measurement
- Standards compliance

**Key Methods:**
```python
async def _stress_test(capability: Capability) -> StressTestResult:
    """Stress test a capability"""

async def _validate_capability(capability: Capability) -> ValidationResult:
    """Validate capability meets standards"""

async def _benchmark_performance(system: System) -> BenchmarkResult:
    """Benchmark system performance"""

async def _check_compliance(output: Output, standard: Standard) -> ComplianceResult:
    """Check output against standards"""

async def _generate_quality_report(system: System) -> QualityReport:
    """Generate comprehensive quality report"""
```

**NATS Subjects:**
- `examiner.stress` - Stress testing
- `examiner.validation` - Capability validation
- `examiner.benchmark` - Benchmarking

**Dependencies:**
- Coder (receives code from)
- Steward (reports to)
- Prism (provides multi-perspective)

---

### 3.3 Dreamer (Creative Generation)

**File:** `src/heretek_swarm/actors/dreamer.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, MemoryMixin

**Responsibilities:**
- Lateral thinking and novel solutions
- Creative generation and brainstorming
- What-if scenario exploration
- Paradigm breaking insights

**Key Methods:**
```python
async def _generate_novel_solution(problem: Problem) -> NovelSolution:
    """Generate novel solution to problem"""

async def _lateral_think(topic: Topic) -> LateralThought:
    """Apply lateral thinking to topic"""

async def _explore_whatif(scenario: Scenario) -> WhatIfResult:
    """Explore what-if scenarios"""

async def _break_paradigm(current_paradigm: Paradigm) -> ParadigmShift:
    """Break out of current paradigm"""

async def _synthesize_creativity(ideas: list[Idea]) -> CreativeSynthesis:
    """Synthesize creative ideas into breakthrough"""
```

**NATS Subjects:**
- `dreamer.creative` - Creative requests
- `dreamer.lateral` - Lateral thinking
- `dreamer.whatif` - What-if exploration

**Dependencies:**
- Alpha (works with analysis)
- Steward (receives creative requests)
- Prism (diverse perspectives)

---

### 3.4 Coder (Implementation)

**File:** `src/heretek_swarm/actors/coder.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, LearningMixin

**Responsibilities:**
- Autonomous code writing and debugging
- System expansion and modification
- Code review and optimization
- Self-editing autonomy

**Key Methods:**
```python
async def _generate_code(specification: Specification) -> GeneratedCode:
    """Generate code from specification"""

async def _debug_code(code: Code, error: Error) -> FixedCode:
    """Debug and fix code errors"""

async def _review_code(code: Code) -> CodeReview:
    """Review code for quality and safety"""

async def _optimize_code(code: Code) -> OptimizedCode:
    """Optimize code for performance"""

async def _self_edit(current_code: Code, requirement: Requirement) -> RevisedCode:
    """Self-edit code based on requirements"""
```

**NATS Subjects:**
- `coder.generate` - Code generation
- `coder.debug` - Debugging requests
- `coder.review` - Code review
- `coder.self-edit` - Self-editing requests

**Dependencies:**
- Examiner (validates code)
- Dreamer (generates ideas)
- Steward (orchestrates)

---

## TIER 4: SAFETY & SECURITY (Protection)

### 4.1 Sentinel (Safety Guardian)

**File:** `src/heretek_swarm/actors/sentinel.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, HealthReportingMixin

**Responsibilities:**
- Emergency reflex for anomalies
- Process freezing or isolation
- Threat quarantine
- Tier-based incident response

**Key Methods:**
```python
async def _handle_anomaly(anomaly: Anomaly, tier: ComputeTier) -> Response:
    """Handle anomaly based on compute tier"""

async def _freeze_process(process: Process) -> FreezeResult:
    """Freeze suspicious process"""

async def _quarantine_action(action: Action) -> QuarantineResult:
    """Quarantine potentially dangerous action"""

async def _escalate_to_prime(anomaly: Anomaly) -> Escalation:
    """Escalate to Sentinel-Prime"""

async def _resolve_anomaly(anomaly: Anomaly, resolution: Resolution) -> None:
    """Resolve anomaly after triage"""
```

**NATS Subjects:**
- `sentinel.anomaly` - Anomaly reports
- `sentinel.freeze` - Process freeze commands
- `sentinel.quarantine` - Quarantine commands
- `sentinel.heartbeat` - Sentinel heartbeat

**Dependencies:**
- Steward (receives alerts from)
- Sentinel-Prime (escalates to)
- Arbiter (tribunal decisions)

---

### 4.2 Sentinel-Prime (Security Commander)

**File:** `src/heretek_swarm/actors/sentinel_prime.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin

**Responsibilities:**
- External threat response and containment
- Coordinated security response
- Threat analysis and classification
- Security protocol enforcement

**Key Methods:**
```python
async def _respond_to_threat(threat: Threat) -> ThreatResponse:
    """Respond to external threat"""

async def _analyze_threat(threat_data: ThreatData) -> ThreatAnalysis:
    """Analyze threat characteristics"""

async def _coordinate_response(response: ThreatResponse) -> CoordinationResult:
    """Coordinate multi-agent security response"""

async def _enforce_protocol(protocol: SecurityProtocol) -> EnforcementResult:
    """Enforce security protocol"""

async def _classify_threat(threat: Threat) -> ThreatClassification:
    """Classify threat severity and type"""
```

**NATS Subjects:**
- `sentinel-prime.threat` - Threat reports
- `sentinel-prime.response` - Coordinated response
- `sentinel-prime.protocol` - Protocol enforcement

**Dependencies:**
- Sentinel (receives escalations from)
- Arbiter (tribunal for threats)
- Steward (reports to)

---

### 4.3 Arbiter (Conflict Resolution)

**File:** `src/heretek_swarm/actors/arbiter.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin

**Responsibilities:**
- Dispute mediation during consensus failures
- Conflict resolution between agents
- Tribunal participation
- Justice and fairness enforcement

**Key Methods:**
```python
async def _mediate_dispute(dispute: Dispute) -> MediationResult:
    """Mediate dispute between agents"""

async def _resolve_conflict(conflict: Conflict) -> ConflictResolution:
    """Resolve conflict through structured process"""

async def _participate_tribunal(issue: Issue) -> TribunalDecision:
    """Participate in tribunal deliberation"""

async def _enforce_fairness(decision: Decision) -> FairnessCheck:
    """Ensure decision is fair and balanced"""

async def _appeal_decision(appeal: Appeal) -> AppealResult:
    """Handle appeal of previous decision"""
```

**NATS Subjects:**
- `arbiter.dispute` - Dispute reports
- `arbiter.conflict` - Conflict resolution
- `arbiter.tribunal` - Tribunal participation

**Dependencies:**
- Steward (convenes tribunal)
- Charlie (provides adversarial view)
- Prism (ensures diverse perspectives)

---

## TIER 5: COORDINATION AGENTS (Integration)

### 5.1 Coordinator (Multi-Agent Sync)

**File:** `src/heretek_swarm/actors/coordinator.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin

**Responsibilities:**
- Task dependency management
- Timeline synchronization
- Resource allocation
- Execution coordination

**Key Methods:**
```python
async def _manage_dependencies(tasks: list[Task]) -> DependencyGraph:
    """Manage task dependencies"""

async def _sync_timeline(timeline: Timeline) -> SyncResult:
    """Synchronize execution timeline"""

async def _allocate_resources(tasks: list[Task], resources: Resources) -> Allocation:
    """Allocate resources to tasks"""

async def _coordinate_execution(workflow: Workflow) -> ExecutionCoordination:
    """Coordinate multi-agent execution"""

async def _resolve_blockers(blocker: Blocker) -> BlockerResolution:
    """Resolve execution blockers"""
```

**NATS Subjects:**
- `coordinator.dependency` - Dependency management
- `coordinator.timeline` - Timeline sync
- `coordinator.execution` - Execution coordination

**Dependencies:**
- Steward (receives coordination requests)
- Chronos (timing coordination)
- Nexus (external coordination)

---

### 5.2 Nexus (External Integration)

**File:** `src/heretek_swarm/actors/nexus.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, LearningMixin

**Responsibilities:**
- Gateway management to human systems
- API integration and management
- External communication coordination
- Protocol translation for external systems

**Key Methods:**
```python
async def _manage_gateway(gateway: Gateway) -> GatewayState:
    """Manage external API gateway"""

async def _integrate_api(api: ExternalAPI) -> IntegrationResult:
    """Integrate with external API"""

async def _translate_protocol(external: ExternalMessage) -> InternalMessage:
    """Translate external protocol to internal"""

async def _coordinate_human(human_request: HumanRequest) -> HumanResponse:
    """Coordinate with human operators"""

async def _manage_webhooks(webhooks: list[Webhook]) -> WebhookState:
    """Manage incoming webhooks"""
```

**NATS Subjects:**
- `nexus.gateway` - Gateway management
- `nexus.external` - External integration
- `nexus.webhook` - Webhook handling

**Dependencies:**
- Echo (coordinates communication)
- Steward (reports to)
- All agents (facilitates external comms)

---

### 5.3 Catalyst (Change Management)

**File:** `src/heretek_swarm/actors/catalyst.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin

**Responsibilities:**
- Handling systemic shifts and transitions
- Paradigm transition management
- Change agent coordination
- Resistance management

**Key Methods:**
```python
async def _manage_change(change: ChangeRequest) -> ChangeResult:
    """Manage systemic change"""

async def _coordinate_transition(transition: Transition) -> TransitionCoordination:
    """Coordinate transition between states"""

async def _address_resistance(resistance: Resistance) -> ResistanceResponse:
    """Address resistance to change"""

async def _plan_paradigm_shift(current: Paradigm, target: Paradigm) -> ShiftPlan:
    """Plan paradigm shift"""

async def _implement_change(change: Change) -> ImplementationResult:
    """Implement change across system"""
```

**NATS Subjects:**
- `catalyst.change` - Change management
- `catalyst.transition` - Transition coordination
- `catalyst.resistance` - Resistance handling

**Dependencies:**
- Steward (initiates changes)
- Metis (strategic planning)
- All agents (affected by changes)

---

### 5.4 Chronos (Temporal/Scheduling)

**File:** `src/heretek_swarm/actors/chronos.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin

**Responsibilities:**
- Time perception and management
- Long-running execution management
- Scheduling and temporal coordination
- Temporal anomaly detection

**Key Methods:**
```python
async def _perceive_time() -> TemporalState:
    """Perceive current time and state"""

async def _manage_schedule(schedule: Schedule) -> ScheduleState:
    """Manage execution schedule"""

async def _handle_long_running(task: LongRunningTask) -> ProgressUpdate:
    """Handle long-running task execution"""

async def _detect_temporal_anomaly(time_state: TemporalState) -> Anomaly:
    """Detect temporal anomalies"""

async def _coordinate_timing(tasks: list[Task], timeline: Timeline) -> TimingCoordination:
    """Coordinate timing across tasks"
```

**NATS Subjects:**
- `chronos.time` - Time perception
- `chronos.schedule` - Schedule management
- `chronos.progress` - Long-running task progress

**Dependencies:**
- Coordinator (timing coordination)
- Metis (long-term planning)
- Steward (reports to)

---

## TIER 6: ENHANCEMENT AGENTS (Optimization)

### 6.1 Prism (Multi-Perspective)

**File:** `src/heretek_swarm/actors/prism.py`
**Inherits:** AgentActor
**Mixin Pattern:** DeliberationMixin, PatternMixin

**Responsibilities:**
- Forcing diverse, non-standard viewpoints
- Perspective diversity in decisions
- Breaking groupthink
- Alternative viewpoint generation

**Key Methods:**
```python
async def _force_perspective(issue: Issue, perspective: Perspective) -> PerspectiveResult:
    """Force specific perspective on issue"""

async def _generate_alternatives(decision: Decision) -> list[Alternative]:
    """Generate alternative viewpoints"""

async def _break_groupthink(topic: Topic) -> GroupthinkBreakResult:
    """Break potential groupthink"""

async def _diverse_analysis(issue: Issue) -> DiverseAnalysis:
    """Provide diverse analysis of issue"""

async def _challenge_consensus(consensus: Consensus) -> ConsensusChallenge:
    """Challenge consensus with alternatives"""
```

**NATS Subjects:**
- `prism.perspective` - Perspective forcing
- `prism.alternatives` - Alternative generation
- `prism.diversity` - Diversity enforcement

**Dependencies:**
- Arbiter (participates in tribunal)
- Beta (provides validation)
- All agents (provides alternative views)

---

### 6.2 Habit-Forge (Behavior Optimization)

**File:** `src/heretek_swarm/actors/habit_forge.py`
**Inherits:** AgentActor
**Mixin Pattern:** LearningMixin, MemoryMixin

**Responsibilities:**
- Building operational efficiency patterns
- Recording established precedents
- Behavior modification and optimization
- Habit formation in agents

**Key Methods:**
```python
async def _forge_habit(behavior: Behavior, context: Context) -> HabitFormation:
    """Forge new habit based on behavior"""

async def _optimize_pattern(pattern: Pattern) -> OptimizedPattern:
    """Optimize existing pattern"""

async def _record_precedent(action: Action, outcome: Outcome) -> Precedent:
    """Record action as precedent"""

async def _analyze_behavior(agent: Agent) -> BehaviorAnalysis:
    """Analyze agent behavior patterns"""

async def _modify_behavior(agent: Agent, target: TargetBehavior) -> ModificationResult:
    """Modify agent behavior toward target"""
```

**NATS Subjects:**
- `habitforge.habit` - Habit formation
- `habitforge.pattern` - Pattern optimization
- `habitforge.precedent` - Precedent recording

**Dependencies:**
- Historian (shares precedent data)
- All agents (influences behavior)
- Steward (reports to)

---

### 6.3 Perceiver+ (Advanced Analytics)

**File:** `src/heretek_swarm/actors/perceiver_plus.py`
**Inherits:** AgentActor
**Mixin Pattern:** PatternMixin, LearningMixin

**Responsibilities:**
- Meta-perception and self-awareness
- Signal from noise extraction at advanced level
- Pattern recognition at system level
- Emergence detection

**Key Methods:**
```python
async def _meta_perceive(self_state: SystemState) -> MetaPerceptionResult:
    """Perceive system's own state"""

async def _extract_deep_signal(data: Data) -> DeepSignal:
    """Extract deep signals from noise"""

async def _recognize_system_patterns(system: System) -> list[SystemPattern]:
    """Recognize patterns at system level"""

async def _detect_emergence(patterns: list[Pattern]) -> EmergenceDetection:
    """Detect emergent behaviors"""

async def _analyze_cognitive_paths(traces: list[Trace]) -> CognitiveAnalysis:
    """Analyze cognitive paths through system"
```

**NATS Subjects:**
- `perceiver-plus.meta` - Meta-perception
- `perceiver-plus.signal` - Deep signal extraction
- `perceiver-plus.emergence` - Emergence detection

**Dependencies:**
- Perceiver (receives from)
- All agents (monitors system-wide)
- Steward (reports to)

---

## INTER-AGENT COMMUNICATION PATTERNS

### Pattern 1: Request-Response
```
Agent A --[request]--> Agent B
Agent A <--[response]-- Agent B
```

### Pattern 2: Publish-Subscribe
```
Agent A --[publish]--> NATS subject
Agents B,C,D --[subscribe]--> NATS subject
```

### Pattern 3: Broadcast
```
Steward --[broadcast]--> all agents
```

### Pattern 4: Tribunal
```
Sentinel --> Steward --> Arbiter --> [Triad deliberation] --> Decision
```

---

## BASE CLASS REQUIREMENTS

All agents must inherit from `AgentActor` and implement:

```python
class AgentActor:
    agent_id: str
    agent_type: str

    async def process_message(message: ActorMessage) -> ActorResponse:
        """Main message processing entry point"""

    async def _handle_[message_type](message: ActorMessage) -> None:
        """Message-type specific handlers"""

    async def _initialize() -> None:
        """Agent initialization"""

    async def _shutdown() -> None:
        """Agent graceful shutdown"""

    async def get_status() -> AgentStatus:
        """Return current agent status"""
```

---

**Document Classification:** AGENT ARCHITECTURE
**Last Updated:** 2026-04-12 17:06 EDT
**Total Agents:** 23 (4+5+4+4+4+3)