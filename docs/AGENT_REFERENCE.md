# Agent Reference

**Version:** 2.0.0
**Session:** 44 (2026-04-06)
**Health Score:** 100/100
**Agents:** 23/23 Implemented
**Session 44 Status:** All 18 agents wired with collective learning, consensus, and memory optimization

Complete reference for all 23 agents in the Heretek Swarm system, organized by tier.

---

## Table of Contents

1. [Tier 1: Core Triad](#tier-1-core-triad)
2. [Tier 2: Support Agents](#tier-2-support-agents)
3. [Tier 3: Exploration Agents](#tier-3-exploration-agents)
4. [Tier 4: Safety & Security](#tier-4-safety--security)
5. [Tier 5: Coordination Agents](#tier-5-coordination-agents)
6. [Tier 6: Enhancement Agents](#tier-6-enhancement-agents)

---

## Tier 1: Core Triad

### StewardAgent

**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Governance and orchestration agent that coordinates deliberations.

```python
class StewardAgent(AgentActor):
    """Orchestrates deliberation process between Alpha, Beta, Charlie."""
    
    async def _handle_initiate_deliberation(self, message: ActorMessage) -> None:
        """Start deliberation process."""
        
    async def _handle_collect_decision(self, message: ActorMessage) -> None:
        """Collect final decision from triad."""
```

**Capabilities:**
- Initiates and orchestrates deliberation workflows
- Collects and synthesizes decisions from the triad
- Manages deliberation state and transitions

---

### AlphaAgent

**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Deep analysis and proposal generation.

```python
class AlphaAgent(AgentActor):
    """Generates detailed analysis and initial proposals."""
    
    async def _handle_analyze_proposal(self, message: ActorMessage) -> None:
        """Analyze proposal and generate recommendations."""
```

**Capabilities:**
- Performs deep analysis of problems
- Generates initial proposals and solutions
- Provides detailed recommendations

---

### BetaAgent

**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Validation and verification of proposals.

```python
class BetaAgent(AgentActor):
    """Validates proposals against constraints and requirements."""
    
    async def _handle_validate_proposal(self, message: ActorMessage) -> None:
        """Validate proposal and identify issues."""
```

**Capabilities:**
- Validates proposals against constraints
- Identifies potential issues and edge cases
- Verifies requirements compliance

---

### CharlieAgent

**File:** [`src/heretek_swarm/actors/triad.py`](../src/heretek_swarm/actors/triad.py)

Challenge agent that stress-tests proposals.

```python
class CharlieAgent(AgentActor):
    """Challenges proposals to identify weaknesses."""
    
    async def _handle_challenge_proposal(self, message: ActorMessage) -> None:
        """Challenge proposal with counter-arguments."""
```

**Capabilities:**
- Stress-tests proposals with counter-arguments
- Identifies weaknesses and vulnerabilities
- Provides adversarial analysis

---

## Tier 2: Support Agents

### HistorianAgent

**File:** [`src/heretek_swarm/actors/historian.py`](../src/heretek_swarm/actors/historian.py)

Memory and knowledge management with dual-tier storage.

```python
class HistorianAgent(AgentActor):
    """Manages episodic and semantic memory storage."""
    
    async def _handle_store_memory(self, message: ActorMessage) -> None:
        """Store memory with caching."""
        
    async def _handle_search_memory(self, message: ActorMessage) -> None:
        """Search memory with filters."""
        
    async def _handle_get_lineage(self, message: ActorMessage) -> None:
        """Get decision lineage."""
```

**Capabilities:**
- Dual-tier memory storage (ephemeral + persistent)
- Semantic search with filters
- Decision lineage tracking

---

### MetisAgent

**File:** [`src/heretek_swarm/actors/metis.py`](../src/heretek_swarm/actors/metis.py)

Strategic planning and resource allocation.

```python
class MetisAgent(AgentActor):
    """Generates strategic plans and allocates resources."""
    
    async def _handle_generate_plan(self, message: ActorMessage) -> None:
        """Generate strategic plan with phases."""
        
    async def _handle_allocate_resources(self, message: ActorMessage) -> None:
        """Allocate resources based on priorities."""
```

**Capabilities:**
- Strategic plan generation with phases
- Resource allocation based on priorities
- Timeline and milestone planning

---

### EmpathAgent

**File:** [`src/heretek_swarm/actors/empath.py`](../src/heretek_swarm/actors/empath.py)

Emotional intelligence and conflict mediation.

```python
class EmpathAgent(AgentActor):
    """Monitors emotional state and mediates conflicts."""
    
    async def _handle_analyze_sentiment(self, message: ActorMessage) -> None:
        """Analyze sentiment of content."""
        
    async def _handle_mediate_conflict(self, message: ActorMessage) -> None:
        """Mediate conflict between agents."""
```

**Capabilities:**
- Sentiment analysis of communications
- Conflict mediation between agents
- Emotional state monitoring

---

### PerceiverAgent

**File:** [`src/heretek_swarm/actors/perceiver.py`](../src/heretek_swarm/actors/perceiver.py)

Multi-modal sensory input processing.

```python
class PerceiverAgent(AgentActor):
    """Processes multi-modal sensory input."""
    
    async def _handle_process_input(self, message: ActorMessage) -> None:
        """Process multi-modal input (text, image, audio)."""
        
    async def _handle_extract_features(self, message: ActorMessage) -> None:
        """Extract features from input."""
```

**Capabilities:**
- Multi-modal input processing (text, image, audio)
- Feature extraction from sensory data
- Input normalization and preprocessing

---

### EchoAgent

**File:** [`src/heretek_swarm/actors/echo.py`](../src/heretek_swarm/actors/echo.py)

Communication and protocol translation.

```python
class EchoAgent(AgentActor):
    """Handles multi-channel communication and protocol translation."""
    
    async def _handle_format_message(self, message: ActorMessage) -> None:
        """Format message for specific channel."""
        
    async def _handle_broadcast(self, message: ActorMessage) -> None:
        """Broadcast to multiple channels."""
```

**Capabilities:**
- Multi-channel communication (Slack, Discord, Telegram)
- Protocol translation between formats
- Message formatting and broadcasting

---

## Tier 3: Exploration Agents

### ExplorerAgent

**File:** [`src/heretek_swarm/actors/explorer.py`](../src/heretek_swarm/actors/explorer.py)

Intelligence gathering and opportunity discovery.

```python
class ExplorerAgent(AgentActor):
    """Monitors sources for opportunities and anomalies."""
    
    async def _handle_start_monitoring(self, message: ActorMessage) -> None:
        """Begin monitoring a source."""
        
    async def _handle_generate_report(self, message: ActorMessage) -> None:
        """Generate intelligence report."""
```

**Capabilities:**
- Source monitoring for opportunities
- Anomaly detection
- Intelligence report generation

---

### ExaminerAgent

**File:** [`src/heretek_swarm/actors/examiner.py`](../src/heretek_swarm/actors/examiner.py)

Quality assurance and testing.

```python
class ExaminerAgent(AgentActor):
    """Performs QA testing and code analysis."""
    
    async def _handle_generate_test_plan(self, message: ActorMessage) -> None:
        """Generate test plan for component."""
        
    async def _handle_analyze_quality(self, message: ActorMessage) -> None:
        """Analyze code quality metrics."""
```

**Capabilities:**
- Test plan generation
- Code quality analysis
- QA testing automation

---

### DreamerAgent

**File:** [`src/heretek_swarm/actors/dreamer.py`](../src/heretek_swarm/actors/dreamer.py)

Creative solution generation.

```python
class DreamerAgent(AgentActor):
    """Generates creative solutions and novel ideas."""
    
    async def _handle_generate_ideas(self, message: ActorMessage) -> None:
        """Generate creative ideas using techniques."""
        
    async def _handle_explore_alternatives(self, message: ActorMessage) -> None:
        """Explore alternative solutions."""
```

**Capabilities:**
- Creative idea generation
- Alternative solution exploration
- Divergent thinking techniques

---

### CoderAgent

**File:** [`src/heretek_swarm/actors/coder.py`](../src/heretek_swarm/actors/coder.py)

Code generation and implementation.

```python
class CoderAgent(AgentActor):
    """Generates code and performs code review."""
    
    async def _handle_generate_code(self, message: ActorMessage) -> None:
        """Generate code in specified language."""
        
    async def _handle_review_code(self, message: ActorMessage) -> None:
        """Review code for issues."""
        
    async def _handle_debug_code(self, message: ActorMessage) -> None:
        """Debug and fix code issues."""
```

**Capabilities:**
- Code generation in multiple languages
- Code review and analysis
- Debugging and issue fixing

---

## Tier 4: Safety & Security

### SentinelAgent

**File:** [`src/heretek_swarm/actors/sentinel.py`](../src/heretek_swarm/actors/sentinel.py)

Safety guardian for input/output validation.

```python
class SentinelAgent(AgentActor):
    """Validates inputs and outputs for safety."""
    
    async def _handle_validate_input(self, message: ActorMessage) -> None:
        """Validate input for safety concerns."""
        
    async def _handle_safety_check(self, message: ActorMessage) -> None:
        """Perform comprehensive safety check."""
```

**Capabilities:**
- Input validation for safety
- Output filtering
- Comprehensive safety checks

---

### SentinelPrimeAgent

**File:** [`src/heretek_swarm/actors/sentinel_prime.py`](../src/heretek_swarm/actors/sentinel_prime.py)

Security commander for threat response.

```python
class SentinelPrimeAgent(AgentActor):
    """Commands security response to threats."""
    
    async def _handle_detect_threat(self, message: ActorMessage) -> None:
        """Detect and classify security threats."""
        
    async def _handle_respond_threat(self, message: ActorMessage) -> None:
        """Execute threat response protocol."""
```

**Capabilities:**
- Threat detection and classification
- Security response coordination
- Incident management

---

### ArbiterAgent

**File:** [`src/heretek_swarm/actors/arbiter.py`](../src/heretek_swarm/actors/arbiter.py)

Conflict resolution between agents.

```python
class ArbiterAgent(AgentActor):
    """Resolves conflicts between agents."""
    
    async def _handle_resolve_conflict(self, message: ActorMessage) -> None:
        """Mediate and resolve agent conflict."""
        
    async def _handle_arbitrate_decision(self, message: ActorMessage) -> None:
        """Arbitrate disputed decisions."""
```

**Capabilities:**
- Conflict mediation between agents
- Decision arbitration
- Dispute resolution

---

## Tier 5: Coordination Agents

### CoordinatorAgent

**File:** [`src/heretek_swarm/actors/coordinator.py`](../src/heretek_swarm/actors/coordinator.py)

Multi-agent task synchronization.

```python
class CoordinatorAgent(AgentActor):
    """Coordinates multi-agent workflows."""
    
    async def _handle_start_workflow(self, message: ActorMessage) -> None:
        """Start coordinated workflow."""
        
    async def _handle_resolve_dependencies(self, message: ActorMessage) -> None:
        """Resolve task dependencies."""
```

**Capabilities:**
- Multi-agent workflow coordination
- Task dependency resolution
- Workflow state management

---

### NexusAgent

**File:** [`src/heretek_swarm/actors/nexus.py`](../src/heretek_swarm/actors/nexus.py)

External API integration.

```python
class NexusAgent(AgentActor):
    """Integrates with external APIs and services."""
    
    async def _handle_call_api(self, message: ActorMessage) -> None:
        """Call external API with authentication."""
        
    async def _handle_manage_webhook(self, message: ActorMessage) -> None:
        """Manage webhook subscriptions."""
```

**Capabilities:**
- External API integration
- Webhook management
- Service authentication

---

### CatalystAgent

**File:** [`src/heretek_swarm/actors/catalyst.py`](../src/heretek_swarm/actors/catalyst.py)

Change management.

```python
class CatalystAgent(AgentActor):
    """Manages change requests and rollbacks."""
    
    async def _handle_propose_change(self, message: ActorMessage) -> None:
        """Propose change with impact analysis."""
        
    async def _handle_execute_rollback(self, message: ActorMessage) -> None:
        """Execute rollback procedure."""
```

**Capabilities:**
- Change request management
- Impact analysis
- Rollback execution

---

### ChronosAgent

**File:** [`src/heretek_swarm/actors/chronos.py`](../src/heretek_swarm/actors/chronos.py)

Time-based scheduling.

```python
class ChronosAgent(AgentActor):
    """Manages time-based scheduling and deadlines."""
    
    async def _handle_schedule_task(self, message: ActorMessage) -> None:
        """Schedule task with recurrence."""
        
    async def _handle_set_deadline(self, message: ActorMessage) -> None:
        """Set deadline with warnings."""
```

**Capabilities:**
- Task scheduling with recurrence
- Deadline tracking with warnings
- Timeline management

---

## Tier 6: Enhancement Agents

### PrismAgent

**File:** [`src/heretek_swarm/actors/prism.py`](../src/heretek_swarm/actors/prism.py)

Multi-perspective analysis.

```python
class PrismAgent(AgentActor):
    """Analyzes issues from multiple perspectives."""
    
    async def _handle_generate_perspectives(self, message: ActorMessage) -> None:
        """Generate multiple perspectives on issue."""
        
    async def _handle_detect_biases(self, message: ActorMessage) -> None:
        """Detect cognitive biases in content."""
```

**Capabilities:**
- Multi-perspective analysis
- Cognitive bias detection
- Stakeholder mapping
- Issue reframing

---

### HabitForgeAgent

**File:** [`src/heretek_swarm/actors/habit_forge.py`](../src/heretek_swarm/actors/habit_forge.py)

Behavior optimization.

```python
class HabitForgeAgent(AgentActor):
    """Designs and tracks habit formation."""
    
    async def _handle_create_habit(self, message: ActorMessage) -> None:
        """Create habit with trigger-routine-reward loop."""
        
    async def _handle_analyze_patterns(self, message: ActorMessage) -> None:
        """Analyze behavioral patterns."""
```

**Capabilities:**
- Habit creation and tracking
- Behavioral pattern analysis
- Reinforcement strategy design
- Stage progression monitoring

---

### PerceiverPlusAgent

**File:** [`src/heretek_swarm/actors/perceiver_plus.py`](../src/heretek_swarm/actors/perceiver_plus.py)

Advanced analytics.

```python
class PerceiverPlusAgent(AgentActor):
    """Performs advanced statistical analytics."""
    
    async def _handle_analyze_data(self, message: ActorMessage) -> None:
        """Perform comprehensive data analysis."""
        
    async def _handle_forecast_values(self, message: ActorMessage) -> None:
        """Forecast future values."""
```

**Capabilities:**
- Descriptive, diagnostic, predictive analysis
- Statistical testing
- Correlation analysis
- Trend analysis
- Anomaly detection
- Forecasting

---

## Agent Capabilities Summary

| Tier | Agent | Key Capabilities |
|------|-------|------------------|
| 1 | Steward | Deliberation orchestration |
| 1 | Alpha | Deep analysis, proposals |
| 1 | Beta | Validation, verification |
| 1 | Charlie | Challenge, stress-testing |
| 2 | Historian | Memory storage, search |
| 2 | Metis | Strategic planning |
| 2 | Empath | Sentiment, mediation |
| 2 | Perceiver | Multi-modal processing |
| 2 | Echo | Communication, translation |
| 3 | Explorer | Intelligence gathering |
| 3 | Examiner | QA, testing |
| 3 | Dreamer | Creative solutions |
| 3 | Coder | Code generation, review |
| 4 | Sentinel | Safety validation |
| 4 | Sentinel Prime | Threat response |
| 4 | Arbiter | Conflict resolution |
| 5 | Coordinator | Workflow coordination |
| 5 | Nexus | API integration |
| 5 | Catalyst | Change management |
| 5 | Chronos | Scheduling, deadlines |
| 6 | Prism | Multi-perspective analysis |
| 6 | Habit Forge | Behavior optimization |
| 6 | Perceiver+ | Advanced analytics |

---

## See Also

- [Core Actors System](./CORE_ACTORS.md) - Base classes and validation
- [Gateway & Communication](./GATEWAY_COMMUNICATION.md) - A2A protocol
- [API Endpoints](./API_ENDPOINTS.md) - REST API reference
