# HERETEK SWARM DEVELOPMENT STEPS
## From Current State to Phase 1 Completion

---

## PHASE 0: IMMEDIATE FIXES (P0)

### Task 0.1: Fix Empath Agent NameError
**Problem:** `validate_message` not defined in empath.py
**File:** `src/heretek_swarm/actors/empath.py`
**Fix:** Add missing import on line ~22:
```python
from heretek_swarm.validation import validate_message
```
**Verification:** `python -m pytest tests/integration/agents/test_empath.py -v`

### Task 0.2: Fix State Test API Mismatches
**Problem:** 4 tests fail due to API shape differences

| Test | Issue | Fix |
|------|-------|-----|
| `test_compute_diff` | expects `diff.added_agents` | Return object with `.added_agents` attribute |
| `test_update_agent_state` | KeyError 'task' | Set working_memory['task'] in update |
| `test_rollback_to_snapshot` | states not restored | Fix StateManager.rollback_to_snapshot() |
| `test_full_workflow` | compound failure | Fix above, this will auto-resolve |

**Files:** `src/heretek_swarm/state/models.py`

### Task 0.3: Mark External Dependency Tests
**Problem:** RAG, observability tests fail without external services
**Fix:** Add `@pytest.mark.integration` decorator to tests requiring:
- Qdrant vector database
- OpenAI API keys
- Redis instance
- NATS server

---

## PHASE 1: FOUNDATION (Week 1-2)

### Task 1.1: Implement Tier 1 Core Agents

#### Steward Agent (Orchestrator)
**File:** `src/heretek_swarm/actors/steward.py`
**Responsibilities:**
- Monitor system vital pulse
- Route tasks to appropriate agents
- Detect anomalies and trigger Sentinel
- Maintain system homeostasis

**Implementation Steps:**
1. Create StewardAgent class inheriting from AgentActor
2. Implement `_monitor_system_health()` method
3. Implement `_broadcast_pulse()` using NATS
4. Implement `_route_task()` method
5. Add heartbeat mechanism (triad-heartbeat)

#### Alpha Agent (Deep Analysis)
**File:** `src/heretek_swarm/actors/alpha.py`
**Responsibilities:**
- Comprehensive examination of problems
- Logical deconstruction
- Solution generation

**Implementation Steps:**
1. Create AlphaAgent class
2. Implement `_analyze_problem()` method
3. Implement `_deconstruct_solution()` method
4. Connect to Global Workspace

#### Beta Agent (Validation)
**File:** `src/heretek_swarm/actors/beta.py`
**Responsibilities:**
- Error detection
- Reality-checking
- Blast-radius projection

**Implementation Steps:**
1. Create BetaAgent class
2. Implement `_validate_solution()` method
3. Implement `_project_outcomes()` method

#### Charlie Agent (Challenge)
**File:** `src/heretek_swarm/actors/charlie.py`
**Responsibilities:**
- Critical review
- Risk assessment
- Adversarial thinking
- Defense counsel during reviews

**Implementation Steps:**
1. Create CharlieAgent class
2. Implement `_challenge_assumption()` method
3. Implement `_assess_risk()` method

### Task 1.2: Wire NATS Event Mesh to Actors

**Objective:** All agents communicate via NATS pub/sub

**Implementation Steps:**
1. Create `infrastructure/nats/actor_bridge.py`
2. Implement `_publish_to_mesh()` for all agents
3. Implement `_subscribe_from_mesh()` for all agents
4. Create `triad-heartbeat` subject for heartbeat
5. Create `agent-broadcast` subject for announcements

**Code Structure:**
```python
class NATSBridge:
    async def publish(self, subject: str, message: dict): ...
    async def subscribe(self, subject: str, callback: callable): ...
    async def request(self, subject: str, message: dict) -> dict: ...
```

### Task 1.3: Implement Steward Heartbeat

**File:** `src/heretek_swarm/actors/steward.py`
**Interval:** Every 30 seconds
**Broadcasts:**
- Token velocity
- Inter-agent latency
- Context-switching frequency
- Active agent count

---

## PHASE 2: ARCHITECTURE REFACTOR (Week 3-4)

### Task 2.1: Implement Global Workspace

**Concept:** Centralized high-speed shared memory (vector + graph)

**Files to Create:**
- `src/heretek_swarm/collective/global_workspace.py`
- `src/heretek_swarm/collective/workspace_broadcast.py`

**Implementation Steps:**
1. Create GlobalWorkspace class
2. Implement `broadcast_insight()` method
3. Implement `subscribe()` for all 23 agents
4. Integrate with Mem0 for persistence

### Task 2.2: Extract Agent Mixins

**Current State:** 5 mixin files in `actors/mixins/`

**Mixin Files:**
- deliberation.py - Agent deliberation logic
- health_reporting.py - Health metrics reporting
- memory_access.py - Mem0 integration
- pattern_consumer.py - Pattern recognition

**Next Mixins to Add:**
- `workspace_access.py` - Global workspace integration
- `consensus_participation.py` - Tribunal participation

### Task 2.3: Consolidate Configuration

**Files to Consolidate:**
- `config/service.py`
- `config/loader.py`
- `config/cache.py`
- `config/encryption.py`

**Into:** `config/manager.py` with YAML/TOML support

---

## PHASE 3: CONSENSUS & CONSCIOUSNESS (Week 5-7)

### Task 3.1: Implement Tribunal Mechanism

**Concept:** Retroactive deliberation on Sentinel actions

**Files to Create:**
- `src/heretek_swarm/consensus/tribunal.py`
- `src/heretek_swarm/consensus/voting.py`
- `src/heretek_swarm/consensus/decision_logger.py`

**Implementation Steps:**
1. Create Tribunal class
2. Implement `_convene_triad()` method
3. Implement `_deliberate()` method
4. Implement `_vote()` method
5. Implement `_update_baselines()` based on decision

### Task 3.2: Implement Consciousness Metrics

**Concept:** Measure system consciousness using IIT/AST

**Files to Create:**
- `src/heretek_swarm/consciousness/metrics/iit.py`
- `src/heretek_swarm/consciousness/metrics/phi_calculator.py`
- `src/heretek_swarm/consciousness/metrics/openTelemetry.py`

**Metrics to Track:**
- Phi^C (Integrated Information)
- Attention allocation
- Self-model accuracy
- Surprise minimization (FEP)

### Task 3.3: Implement Emergence Detection

**Files to Create:**
- `src/heretek_swarm/collective/emergence_detector.py`

**Detection Methods:**
- Novel agent interaction patterns
- Solution efficiency improvement
- Self-discovered optimizations

---

## PHASE 4: AUTONOMOUS DEVOPS (Week 8-10)

### Task 4.1: Implement Self-Deployment

**Concept:** Swarm reads own repo, identifies inefficiencies, writes patches

**Files to Create:**
- `src/heretek_swarm/runtime/self_deployer.py`
- `src/heretek_swarm/runtime/sandbox_manager.py`
- `src/heretek_swarm/runtime/diff_analyzer.py`

**Safety Protocols:**
1. All changes tested in sandbox first
2. Triad approval required for production
3. Rollback capability maintained
4. Non-destructive file management (rename vs delete)

### Task 4.2: Implement Docker-in-Docker

**Concept:** Isolated execution environment for self-editing

**Files to Create:**
- `src/heretek_swarm/runtime/sandbox/docker_manager.py`

**Requirements:**
- DinD container with resource limits
- Volume mounting for code access
- Network isolation for safety

---

## PHASE 5: EMERGENCE MEASUREMENT (Week 11-12)

### Task 5.1: OpenTelemetry Cognitive Tracing

**Concept:** Track cognitive paths through the system

**Implementation Steps:**
1. Instrument all agents with OpenTelemetry
2. Track spans for each agent interaction
3. Measure:
   - Ideas touched before execution
   - Distance from problem to solution
   - Novelty of interaction patterns

### Task 5.2: Mathematical Emergence Proof

**Concept:** Prove emergent behavior when system solves complex problems

**Metrics:**
- Systemic surprise minimization
- Self-discovered interaction combinations
- Novelty coefficient

---

## CHECKLIST: PREREQUISITES BEFORE EACH PHASE

### Before Phase 1
- [ ] All P0 bugs fixed
- [ ] 95%+ test pass rate
- [ ] NATS infrastructure verified working

### Before Phase 2
- [ ] Tier 1 agents (Steward, Alpha, Beta, Charlie) implemented
- [ ] NATS→Actor bridge complete
- [ ] Steward heartbeat operational

### Before Phase 3
- [ ] All 23 agents have base implementation
- [ ] Global workspace functional
- [ ] Mixin extraction complete

### Before Phase 4
- [ ] Tribunal mechanism operational
- [ ] Consciousness metrics implemented
- [ ] Emergence detection working

### Before Phase 5
- [ ] Self-deployment sandbox ready
- [ ] Docker-in-Docker operational
- [ ] All safety protocols verified

---

## FILE CREATION ORDER

```
1. docs/MASTER_PLAN.md              [DONE]
2. docs/DEVELOPMENT_STEPS.md         [THIS FILE]
3. docs/MAIN_PROMPT.md               [NEXT]
4. docs/AGENT_ARCHITECTURE.md        [TBD]
5. docs/PROTOCOL_SPEC.md             [TBD]
```

---

## VERIFICATION COMMANDS

```bash
# Run full test suite
python -m pytest tests/ -x -q --tb=short

# Run specific agent tests
python -m pytest tests/integration/agents/ -v

# Run state tests
python -m pytest tests/state/ -v

# Check linting
ruff check src tests

# Type checking
mypy src

# Coverage report
pytest --cov=src --cov-report=term-missing
```

---

**Document Classification:** DEVELOPMENT STEPS
**Last Updated:** 2026-04-12 17:06 EDT
**Status:** PHASE 0 IN PROGRESS