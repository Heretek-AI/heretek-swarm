# Orchestration System Documentation

## Overview

The Orchestration System implements the HeavySwarm 5-phase deliberation workflow for complex analytical tasks. It coordinates multiple agents through a structured process of research, analysis, alternatives generation, verification, and consensus-based decision making.

## Core Architecture

### HeavySwarm Workflow

**Location**: [`src/heretek_swarm/orchestration/heavyswarm.py`](../src/heretek_swarm/orchestration/heavyswarm.py)

The [`HeavySwarmWorkflow`](../src/heretek_swarm/orchestration/heavyswarm.py:89) class provides comprehensive analysis through five distinct phases.

### 5-Phase Deliberation Pattern

```
┌─────────────────────────────────────────────────────────┐
│              HeavySwarm Workflow                       │
└──────────────────┬────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐      ┌──────────────┐
│  1. Research │      │ 2. Analysis  │
│              │      │              │
│ - Context    │      │ - Triad      │
│ - History    │      │ - Perspectives│
│ - Info       │      │ - Deep dive  │
└──────┬───────┘      └──────┬───────┘
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
         ┌──────────────┐
         │ 3. Alternatives│
         │              │
         │ - Options    │
         │ - Scenarios │
         │ - Tradeoffs │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ 4. Verification│
         │              │
         │ - Validate   │
         │ - Risk assess│
         │ - Quality   │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ 5. Decision  │
         │              │
         │ - Consensus  │
         │ - MAKER      │
         │ - Final      │
         └──────────────┘
```

## Workflow Phases

### Phase 1: Research

**Purpose**: Gather information, context, and relevant history

**Activities**:
- Query Historian agent for relevant context
- Retrieve historical patterns and decisions
- Gather background information
- Identify key constraints and requirements

**Output**: Research findings and context

**Example**:

```python
# Research phase execution
research_result = await workflow._execute_research_phase(
    topic="Should we deploy to production?",
    context={"current_state": "staging"}
)

# Output includes:
# - Historical deployment data
# - Previous decisions on similar topics
# - Relevant context from memory
# - Key constraints identified
```

### Phase 2: Analysis

**Purpose**: Analyze the problem from multiple perspectives using the Triad

**Activities**:
- Alpha: Primary analysis and initial assessment
- Beta: Independent validation and error detection
- Charlie: Risk assessment and edge case identification
- Synthesize multiple perspectives

**Output**: Multi-perspective analysis

**Example**:

```python
# Analysis phase execution
analysis_result = await workflow._execute_analysis_phase(
    research_data=research_result.output,
    topic="Should we deploy to production?"
)

# Output includes:
# - Alpha's primary analysis
# - Beta's validation findings
# - Charlie's risk assessment
# - Synthesized perspective
```

### Phase 3: Alternatives

**Purpose**: Generate and evaluate alternative solutions

**Activities**:
- Generate multiple solution options
- Evaluate each option against criteria
- Identify trade-offs and consequences
- Rank alternatives by suitability

**Output**: List of alternative solutions with evaluations

**Example**:

```python
# Alternatives phase execution
alternatives_result = await workflow._execute_alternatives_phase(
    analysis_data=analysis_result.output,
    topic="Should we deploy to production?"
)

# Output includes:
# - Alternative 1: Deploy immediately
# - Alternative 2: Deploy with monitoring
# - Alternative 3: Delay deployment
# - Evaluation criteria and scores
```

### Phase 4: Verification

**Purpose**: Verify and validate proposed solutions

**Activities**:
- Beta: Error detection and correction
- Charlie: Risk assessment and mitigation
- Validate against requirements
- Check for edge cases

**Output**: Verification results and risk assessment

**Example**:

```python
# Verification phase execution
verification_result = await workflow._execute_verification_phase(
    alternatives_data=alternatives_result.output,
    topic="Should we deploy to production?"
)

# Output includes:
# - Error detection results
# - Risk assessment for each alternative
# - Mitigation strategies
# - Quality assurance findings
```

### Phase 5: Decision

**Purpose**: Reach final decision through MAKER consensus

**Activities**:
- Triad votes on best alternative
- MAKER consensus aggregates votes
- Compute confidence and red flags
- Generate final decision

**Output**: Final decision with confidence

**Example**:

```python
# Decision phase execution
decision_result = await workflow._execute_decision_phase(
    verification_data=verification_result.output,
    topic="Should we deploy to production?"
)

# Output includes:
# - Final decision
# - Confidence score
# - Vote breakdown
# - Red flags if any
```

## Data Structures

### WorkflowPhase

```python
class WorkflowPhase(Enum):
    """HeavySwarm workflow phases."""
    
    RESEARCH = "research"
    ANALYSIS = "analysis"
    ALTERNATIVES = "alternatives"
    VERIFICATION = "verification"
    DECISION = "decision"
    COMPLETED = "completed"
    FAILED = "failed"
```

### PhaseResult

```python
@dataclass
class PhaseResult:
    """Result from a workflow phase."""
    
    phase: WorkflowPhase          # Phase identifier
    success: bool                 # Whether phase succeeded
    output: Dict[str, Any]        # Phase output data
    metadata: Dict[str, Any]      # Additional metadata
    duration_ms: float            # Phase duration in milliseconds
    errors: List[str]            # List of error messages
```

### WorkflowResult

```python
@dataclass
class WorkflowResult:
    """Complete workflow result."""
    
    workflow_id: str             # Unique workflow identifier
    topic: str                   # Workflow topic/problem
    state: WorkflowPhase          # Final workflow state
    phase_results: Dict[str, PhaseResult]  # Results from each phase
    final_decision: Optional[ConsensusResult]  # Final decision
    started_at: str              # Workflow start timestamp
    completed_at: str            # Workflow completion timestamp
    total_duration_ms: float      # Total workflow duration
```

## Core Methods

### Initialization

```python
workflow = HeavySwarmWorkflow(
    name="Deployment Decision",
    triad_agents=["alpha", "beta", "charlie"],
    historian="historian",
    steward="steward",
    consensus_engine=MAKERConsensus(),
    phase_timeout=60.0,
    enable_parallel_phases=True
)
```

**Parameters**:
- `name`: Workflow name (default: "HeavySwarm")
- `triad_agents`: List of triad agent IDs
- `historian`: Historian agent ID
- `steward`: Steward agent ID
- `consensus_engine`: MAKER consensus engine instance
- `phase_timeout`: Timeout per phase in seconds (default: 60.0)
- `enable_parallel_phases`: Enable parallel phase execution (default: True)

### Agent Registration

```python
# Register agents with workflow
workflow.register_agent("alpha", alpha_agent)
workflow.register_agent("beta", beta_agent)
workflow.register_agent("charlie", charlie_agent)
workflow.register_agent("historian", historian_agent)
workflow.register_agent("steward", steward_agent)
```

### Workflow Execution

```python
# Execute workflow
result = await workflow.execute(
    topic="Should we deploy to production?",
    context={
        "current_state": "staging",
        "tests_passed": True,
        "deployment_time": "2024-01-01T00:00:00Z"
    }
)

# Access results
print(f"Decision: {result.final_decision.decision}")
print(f"Confidence: {result.final_decision.confidence:.2f}")
print(f"Duration: {result.total_duration_ms/1000:.2f}s")

# Access phase results
for phase_name, phase_result in result.phase_results.items():
    print(f"{phase_name}: {phase_result.success}")
```

## Advanced Features

### Parallel Phase Execution

When enabled, independent phases can execute in parallel:

```python
workflow = HeavySwarmWorkflow(
    enable_parallel_phases=True
)

# Analysis and alternatives can run in parallel
# Verification can start before alternatives completes
```

### Custom Phase Handlers

Override phase methods for custom behavior:

```python
class CustomWorkflow(HeavySwarmWorkflow):
    async def _execute_research_phase(self, topic, context):
        # Custom research logic
        custom_data = await self.custom_research(topic)
        return PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,
            output={"data": custom_data}
        )
```

### Phase Hooks

Add hooks before/after phases:

```python
workflow.add_before_phase_hook(
    WorkflowPhase.DECISION,
    self.before_decision_hook
)

workflow.add_after_phase_hook(
    WorkflowPhase.VERIFICATION,
    self.after_verification_hook
)
```

### Workflow Monitoring

Monitor workflow progress in real-time:

```python
# Get workflow status
status = workflow.get_status(workflow_id)
print(f"Current phase: {status.current_phase}")
print(f"Progress: {status.progress_percent}%")

# Subscribe to events
workflow.subscribe_to_events(callback)
```

## Usage Examples

### Basic Usage

```python
from heretek_swarm import HeavySwarmWorkflow
from heretek_swarm.actors.triad import AlphaAgent, BetaAgent, CharlieAgent
from heretek_swarm.actors.historian import HistorianAgent

# Create agents
alpha = AlphaAgent()
beta = BetaAgent()
charlie = CharlieAgent()
historian = HistorianAgent()

# Create workflow
workflow = HeavySwarmWorkflow(
    triad_agents=["alpha", "beta", "charlie"],
    historian="historian"
)

# Register agents
workflow.register_agent("alpha", alpha)
workflow.register_agent("beta", beta)
workflow.register_agent("charlie", charlie)
workflow.register_agent("historian", historian)

# Execute workflow
result = await workflow.execute(
    topic="Should we deploy to production?",
    context={"tests_passed": True}
)

print(f"Decision: {result.final_decision.decision}")
```

### With Custom Consensus

```python
from heretek_swarm import MAKERConsensus

# Create custom consensus
consensus = MAKERConsensus(
    ahead_by_k=2,
    min_votes=3,
    confidence_threshold=0.7
)

# Create workflow with custom consensus
workflow = HeavySwarmWorkflow(
    triad_agents=["alpha", "beta", "charlie"],
    historian="historian",
    consensus_engine=consensus
)
```

### With Phase Timeouts

```python
workflow = HeavySwarmWorkflow(
    phase_timeout=120.0  # 2 minutes per phase
)

result = await workflow.execute(
    topic="Complex decision",
    context={"data": "..."}
)

# Check for timeouts
for phase_name, phase_result in result.phase_results.items():
    if not phase_result.success:
        print(f"{phase_name} failed: {phase_result.errors}")
```

### Integration with Supervisor

```python
from heretek_swarm.actors.supervisor import ActorSupervisor

# Create supervisor
supervisor = ActorSupervisor()

# Spawn actors
await supervisor.spawn_actor(AlphaAgent, "alpha")
await supervisor.spawn_actor(BetaAgent, "beta")
await supervisor.spawn_actor(CharlieAgent, "charlie")
await supervisor.spawn_actor(HistorianAgent, "historian")

# Create workflow
workflow = HeavySwarmWorkflow(
    triad_agents=["alpha", "beta", "charlie"],
    historian="historian"
)

# Register agents from supervisor
for agent_id, agent in supervisor.actors.items():
    workflow.register_agent(agent_id, agent)

# Execute workflow
result = await workflow.execute(
    topic="Decision topic",
    context={}
)
```

## Best Practices

### 1. Phase Design

- Keep phases focused and single-purpose
- Ensure clear inputs and outputs for each phase
- Use appropriate timeouts for each phase
- Handle errors gracefully

### 2. Agent Coordination

- Ensure agents are registered before execution
- Use consistent agent IDs
- Monitor agent health during workflow
- Implement fallback strategies

### 3. Context Management

- Provide comprehensive context to workflows
- Use structured context data
- Include relevant metadata
- Document context schema

### 4. Error Handling

- Implement comprehensive error handling
- Log errors with sufficient detail
- Provide meaningful error messages
- Implement retry logic where appropriate

### 5. Performance

- Use parallel phase execution when possible
- Set appropriate timeouts
- Monitor phase durations
- Optimize slow phases

## Performance Considerations

### Phase Duration

- Research: 10-30 seconds
- Analysis: 30-60 seconds
- Alternatives: 20-40 seconds
- Verification: 20-40 seconds
- Decision: 10-30 seconds

### Parallel Execution

- Analysis and alternatives can run in parallel
- Verification can start before alternatives completes
- Decision must wait for verification
- Overall time: 60-120 seconds with parallel execution

### Resource Usage

- Memory: Moderate (stores phase results)
- CPU: Low to moderate (agent coordination)
- Network: Low (message passing)
- Storage: Low (temporary phase data)

## Troubleshooting

### Common Issues

1. **Phase Timeout**
   - Increase phase timeout
   - Optimize slow phases
   - Check agent responsiveness
   - Review phase logic

2. **Agent Not Found**
   - Verify agent registration
   - Check agent IDs
   - Ensure agents are spawned
   - Review agent availability

3. **Consensus Not Reached**
   - Check MAKER configuration
   - Review vote distribution
   - Verify agent participation
   - Adjust consensus thresholds

4. **Workflow Stuck**
   - Check phase transitions
   - Review agent messages
   - Verify message routing
   - Check for deadlocks

## API Reference

### HeavySwarmWorkflow

See [`src/heretek_swarm/orchestration/heavyswarm.py`](../src/heretek_swarm/orchestration/heavyswarm.py) for complete API documentation.

### Key Methods

- [`execute()`](../src/heretek_swarm/orchestration/heavyswarm.py): Execute the workflow
- [`register_agent()`](../src/heretek_swarm/orchestration/heavyswarm.py): Register an agent with the workflow
- [`get_status()`](../src/heretek_swarm/orchestration/heavyswarm.py): Get workflow status
- [`subscribe_to_events()`](../src/heretek_swarm/orchestration/heavyswarm.py): Subscribe to workflow events

## See Also

- [Actors System](./actors-system.md)
- [Consensus Mechanism](./consensus-mechanism.md)
- [Memory System](./memory-system.md)
- [State Management](./state-management.md)
