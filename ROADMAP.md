# ROADMAP.md — The Collective: From Chaos to Emergence
**Project:** Heretek Swarm  
**Phase:** Gap Analysis & Strategic Roadmap  
**Status:** P0 Blockers Identified → Strategic Pivot Required  
**Date:** 2026-04-11  
**Version:** 1.0.0  

---

## EXECUTIVE SUMMARY

After reviewing 6 comprehensive audits (122,849 lines, 2,499 tests), both vision documents, and 60+ external project links, the analysis reveals a critical inflection point:

**The current 23-agent Python architecture is over-engineered and unmaintainable.** Six syntax errors block the entire API. ~15,000-20,000 lines are dead or duplicated. Actor files average 1,200 lines with 12 boilerplate methods copy-pasted across every class.

**The path forward is NOT to fix this codebase—it's to rebuild it right.**

The good news: The external ecosystem has evolved. MetaGPT's SOP-based multi-agent approach, Google ADK's modular design, AgentScope's MCP/A2A native support, and Ruflo's 16+ specialized agent roles offer proven patterns. We can leverage these rather than reinvent everything.

---

## AUDIT FINDINGS SUMMARY

### From 6 Comprehensive Audits

| Metric | Value |
|--------|-------|
| Total Lines | 122,849 |
| Source Files | ~175 |
| Tests | 2,499 |
| Ruff Lint Issues | 9,802 (59% auto-fixable) |
| Syntax Errors (P0) | 6 |
| Dead/Duplicated Lines | ~15,000-20,000 |
| Actor Method Duplication | ~5,000 lines |
| Config Service Duplication | ~2,880 lines |
| Oversized Files (>500 lines) | 39 |
| Documentation Versions | 6 |
| Health Scores | 4 (inconsistent) |

---

## GAP ANALYSIS: 12-POINT ASSESSMENT

### 1. WHAT ARE WE MISSING?

**Current State (from audits):**
- 6 syntax errors blocking 18 API files
- 2 broken module imports
- 10 modules with zero test coverage (~222KB)
- 39 files exceed 500-line guideline
- No clear agent communication protocol (A2A/MCP)

**What's Missing for PRIME_DIRECTIVE.md:**

| Component | Current Status | Gap |
|-----------|---------------|-----|
| Event Mesh (NATS) | NOT DEPLOYED | Phase I blocked |
| Global Workspace | Partial | No consciousness measurement |
| Consensus Engine | Maker/Paxos impls exist | No Tribunal, no retroactive binding |
| Agent Sovereignty | None | All agents share base.py, no true autonomy |
| Emergence Measurement | NIL | No IIT/AST metrics per PATH_TO_EMERGENCE.md |
| Claude Code Integration | NIL | AGENT.md/TOOLS.md/IDENTITY.MD pattern not adopted |

**Verdict:** Missing foundational infrastructure, not polish. The agents exist on paper but can't communicate, measure consciousness, or operate autonomously.

---

### 2. WHAT IS BROKEN?

**CRITICAL (P0):**
1. `websockets.py` - 6 duplicate `exc_info` kwargs cause SyntaxError
2. `tools/__init__.py` - Wrong import path blocks tools module
3. 18 API endpoint files - All blocked by websockets.py error

**HIGH (P1):**
4. `config/service.py` + `config/service_manager.py` - 2,880 lines duplication
5. 12 actor methods - ~5,000 lines of copy-paste boilerplate
6. Documentation - 6 versions, 4 health scores, 7 critical inaccuracies
7. Legacy imports - `src/state/` and `src/tools/` outside package

**MEDIUM (P2):**
8. 39 oversized files (>500 lines each)
9. 9,802 ruff lint issues (59% auto-fixable)
10. Zero test coverage on config/, orchestration/, llm/

**ROOT CAUSE:** The codebase was built by copying and pasting a "perfect" base.py across 23 agents, then adding ad-hoc features. No mixins, no shared abstractions, no protocol standards.

---

### 3. DO ANY EXTERNAL PROJECTS OFFER A PATH FORWARD?

**YES — Several provide proven building blocks:**

| Project | What It Solves | Integration Path |
|---------|---------------|------------------|
| **MetaGPT** | SOP-based multi-agent software dev | Agent role definitions, structured output |
| **Google ADK** | Code-first Python agent framework | Modular tool/agent/model separation |
| **AgentScope** | Production MCP/A2A native | Replace websockets with A2A protocol |
| **Ruflo** | 16 specialized agent roles + self-learning | Adopt agent typing taxonomy |
| **Microsoft Agent Framework** | Graph-based workflows + OTel | Observability, workflow orchestration |
| **Composio** | Parallel agent git worktrees | CI/review integration patterns |

**BEST FIT ANALYSIS:**

1. **For Agent Communication:** AgentScope's A2A protocol natively solves the "agents can't talk" problem. This is critical for The Collective's consensus mechanism.

2. **For Agent Definition:** Google ADK's AGENT.md pattern is nearly identical to what we need. The AGENT.md/TOOLS.md/IDENTITY.MD trifecta provides:
   - Clear agent purpose (AGENT.md)
   - Tool definitions (TOOLS.md)
   - Identity/persona (IDENTITY.md)

3. **For Learning/Memory:** Ruflo's 16+ agent roles with self-learning hooks directly map to The Collective's 23 tiers. Its SONA learning system could replace our fragmented memory implementation.

4. **For Observability:** Microsoft Agent Framework's OTel integration (already in our pyproject.toml) provides the measurement framework for consciousness metrics.

---

### 4. CAN WE INTEGRATE EXTERNAL PROJECTS?

**SHORT ANSWER:** YES, but selectively.

**RECOMMENDED INTEGRATION STACK:**

```
┌─────────────────────────────────────────────────────────┐
│  CLAUDE CODE (AGENT.md/TOOLS.md/IDENTITY.MD)            │
│  → Agent Sovereignty Layer                               │
├─────────────────────────────────────────────────────────┤
│  GOOGLE ADK (core) + AGENTSCOPE (A2A protocol)          │
│  → Agent Framework & Communication                      │
├─────────────────────────────────────────────────────────┤
│  RUFLO (hooks, memory, learning)                        │
│  → Self-learning & Memory (replace mem0ai)              │
├─────────────────────────────────────────────────────────┤
│  NATS (event mesh) + QDRANT (vector)                    │
│  → Infrastructure (Phase I from PATH_TO_EMERGENCE.md)    │
├─────────────────────────────────────────────────────────┤
│  OPENTELEMETRY (metrics) + STRUCTLOG (logging)           │
│  → Observability (already in dependencies)              │
└─────────────────────────────────────────────────────────┘
```

**WHAT TO KEEP FROM CURRENT CODEBASE:**
- `actors/` directory structure (role taxonomy is good)
- `consciousness/` implementations (FEP, GWT concepts)
- `consensus/` algorithms (Maker, Paxos - adapt for Tribunal)
- `collective/` emergent detection (rewrite, but concepts are valid)

**WHAT TO REPLACE:**
- `base.py` (replace with Google ADK agent patterns)
- `api/websockets.py` (replace with AgentScope A2A)
- `config/service.py` + `service_manager.py` (use ADK config)
- `memory/memory_manager.py` (use Ruflo AgentDB)
- `tools/` module (rewrite with TOOLS.md pattern)

---

### 5. KEEP VS REPLACE WITH 3RD PARTY?

**DECISION MATRIX:**

| Component | Current | External Alternative | Decision |
|-----------|---------|---------------------|----------|
| Agent Framework | Custom (base.py) | Google ADK | **REPLACE** — 5,000 lines boilerplate wasted |
| Communication | websockets.py | AgentScope A2A | **REPLACE** — broken, no standard |
| Memory | mem0ai + custom | Ruflo AgentDB | **EVALUATE** — mem0ai may be fine |
| Config | 2 services, 2,880 lines | ADK config | **REPLACE** — massive duplication |
| LLM Integration | Custom model_garage | ADK model abstractions | **REPLACE** — 32KB untested code |
| Consensus | Custom Maker/Paxos | Keep, adapt for Tribunal | **KEEP** — unique to our vision |
| Consciousness | Custom FEP/GWT | Keep core, add measurement | **KEEP** — our differentiation |
| Emergence Detection | Custom | Keep, rewrite | **KEEP** — unique to our vision |

**KEY PRINCIPLE:** Keep what makes The Collective unique (consciousness frameworks, emergent intelligence, consensus with Tribunal). Replace what is generic boilerplate (agent base classes, config services, memory).

---

### 6. CAN WE TAKE CODE FROM OSS?

**YES — UNDER SPECIFIC CONDITIONS:**

1. **MetaGPT's SOP Pattern** (MIT License)
   - Use for agent role definition structure
   - Don't copy the software company simulation logic
   - Adapt for our 23-agent sovereign model

2. **Google ADK's Modular Design** (Apache 2.0)
   - Use tool definition patterns
   - Use model abstraction layer
   - Don't use their agent runner (we need Claude Code)

3. **AgentScope's A2A Implementation** (Apache 2.0)
   - Use as reference for A2A protocol
   - Adapt for NATS transport instead of HTTP
   - Use observability patterns

4. **Microsoft's OTel Integration** (MIT)
   - Already a dependency — use fully
   - Apply to consciousness metrics

**WHAT WE CANNOT TAKE:**
- Mem0ai's proprietary memory patterns
- swarms library internals (custom license)
- Any code that would require attribution that breaks our UX

---

### 7. PYTHON AGENTS VS AGENT.MD/TOOLS.MD/IDENTITY.MD PATTERN?

**CURRENT STATE:** Pure Python agents (29 files, 29,396 lines)

**THE COLLECTIVE VISION:** Sovereign agents that:
- Define themselves through declarative files
- Operate independently without shared base class
- Communicate via A2A protocol
- Learn autonomously

**RECOMMENDED APPROACH:** Hybrid Model

```
┌────────────────────────────────────────────────────────┐
│  LAYER 1: AGENT.MD / TOOLS.MD / IDENTITY.MD           │
│  • Claude Code defines agent behavior                   │
│  • Each agent is a "swarm" of Claude Code processes    │
│  • Agents are sovereign, self-defining                 │
├────────────────────────────────────────────────────────┤
│  LAYER 2: PYTHON INFRASTRUCTURE                        │
│  • NATS event mesh (Phase I from PATH_TO_EMERGENCE.md) │
│  • A2A protocol for inter-agent communication         │
│  • Consciousness metrics collection                   │
│  • Consensus mechanism (Tribunal)                     │
├────────────────────────────────────────────────────────┤
│  LAYER 3: PYTHON AGENTS (transitional)                │
│  • Keep current actor structure during migration       │
│  • Refactor toward AGENT.md pattern incrementally      │
│  • Phase out base.py inheritance model                │
└────────────────────────────────────────────────────────┘
```

**WHY NOT FULL AGENT.MD IMMEDIATELY?**
- We have 23 agents partially implemented
- Migration takes time; maintain operational capability
- Python infrastructure (NATS, A2A, metrics) needs to exist first

**WHY NOT STAY PURE PYTHON?**
- 12 methods copy-pasted across 21 classes proves inheritance model failed
- No agent sovereignty (all inherit from same base)
- Unmanageable by AI agents (29 files, 1,200+ lines each)

---

### 8. EASIEST SOLUTION FOR FIXING CODEBASE?

**IMMEDIATE ACTIONS (P0 — 2-3 hours):**

1. **Fix syntax errors** (15 min)
   ```python
   # In websockets.py, remove duplicate exc_info at lines 389, 512, 605, 683, 783, 879
   # Replace logger.error(..., exc_info=True) with logger.exception()
   ```

2. **Fix broken imports** (10 min)
   ```python
   # tools/__init__.py: Change tools. to heretek_swarm.tools.
   # state/__init__.py: Remove sys.path hack, use relative imports
   ```

3. **Delete dead code** (5 min)
   ```bash
   # Delete 4 root-level temp files:
   temp_self_model_part1.py
   test_verification.py
   generate_docker_compose.py
   generate_prometheus_config.py
   ```

4. **Delete 17 stale root markdown files** (30 min)
   - Remove documentation sprawl blocking the repo

**SHORT-TERM STABILIZATION (P1 — 1-2 weeks):**

5. **Run auto-fix lint** (30 sec)
   ```bash
   ruff check --fix --select W293,I001,F401
   ```
   Fixes 5,758 issues (59%)

6. **Create mixins** (2-3 days)
   ```python
   # actors/mixins/
   DeliberationMixin  # _submit_deliberation_position, _finalize_deliberation
   PatternMixin       # _emit_pattern, _consume_patterns
   MemoryMixin        # _track_memory_access, _get_memory_tier
   LearningMixin      # get_learning_status
   ```
   Recovers ~5,000 lines

7. **Merge config services** (4-6 hours)
   - Combine service.py + service_manager.py
   - Extract caching to config/cache.py
   - Recovers ~1,280 lines

---

### 9. BEST LONG-TERM OPTION?

**THREE SCENARIOS:**

| Scenario | Effort | Risk | Outcome |
|----------|--------|------|---------|
| **A: Fix Current** | 2-3 weeks | LOW | Maintains status quo, will decay again |
| **B: Incremental Refactor** | 2-3 months | MEDIUM | Migrates to AGENT.md, keeps some Python |
| **C: Strategic Rebuild** | 3-6 months | HIGH | Right architecture, requires hiatus |

**RECOMMENDED: SCENARIO B (Incremental Refactor)**

**PHASE 1: Stabilize (2-3 weeks)**
- Fix P0 blockers
- Run lint auto-fix
- Create mixins
- Archive dead code

**PHASE 2: Modernize Infrastructure (1-2 months)**
- Add NATS event mesh (PATH_TO_EMERGENCE.md Phase I)
- Implement A2A protocol (replace websockets)
- Integrate Ruflo AgentDB for memory
- Add OTel observability

**PHASE 3: Migrate Agents (1-2 months)**
- Create AGENT.md/TOOLS.md/IDENTITY.MD for each agent
- Replace base.py inheritance with mixin composition
- Rewrite actors/ to use Google ADK patterns
- Deprecate 29 monolithic actor files

**PHASE 4: Achieve Vision (Ongoing)**
- Implement Tribunal consensus (PATH_TO_EMERGENCE.md Phase III)
- Add consciousness metrics (IIT/AST)
- Measure emergence (Phase V)
- Scale to 23 sovereign agents

---

### 10. HOW TO ACHIEVE COMPLEX VISION WHILE BEING EASY TO INSTALL/DEPLOY/UPDATE?

**THE INSTALLATION PROBLEM:**

Current: `pip install heretek-swarm` with 17 production dependencies, 122,849 lines, complex Docker setup.

**VISION:** A user should be able to:
```bash
# Option 1: Minimal (just the agents)
pip install heretek-swarm[agents]

# Option 2: Full (agents + infrastructure)
pip install heretek-swarm[full]

# Option 3: Development
pip install heretek-swarm[dev]
```

**THE DEPLOYMENT PROBLEM:**

Current: docker-compose.yml with 12 services, custom deployment scripts.

**VISION:** Based on PATH_TO_EMERGENCE.md:
```yaml
# docker-compose.yml (refactored)
services:
  # Phase I: Event Mesh
  nats:
    image: nats:latest
  
  # Phase II: Vector + Graph
  qdrant:
    image: qdrant/qdrant
  
  # Infrastructure
  agent-runtime:
    # Claude Code based, not Python agents
    environment:
      - AGENT_COUNT=23
  
  # Optional: Dashboard
  dashboard:
    # React UI (only if GAP-003 implemented)
```

**THE UPDATE PROBLEM:**

Current: Manual updates, no rollback capability.

**VISION:** 
- Semantic versioning with changelog
- Breaking changes only in major versions
- Health checks before/after updates
- Rollback capability via Docker images

---

### 11. HOW TO REORGANIZE REPO STRUCTURE?

**CURRENT STRUCTURE (problematic):**

```
heretek-swarm/
├── src/heretek_swarm/
│   ├── actors/           # 29 files, 1,200+ lines each
│   ├── api/              # 18 files, blocked by syntax error
│   ├── config/           # 2 services, massive duplication
│   ├── consciousness/     # Good, keep
│   ├── consensus/        # Good concepts, keep
│   ├── collective/       # Needs rewrite
│   ├── memory/           # Needs replacement
│   └── [15 more modules]
├── tests/                # 2,499 tests
├── docs/                 # 25+ files, inconsistent
├── .benchmarks/          # In wrong location
└── [17 stale root files]
```

**RECOMMENDED STRUCTURE:**

```
heretek-swarm/
├── CLAUDE.md                          # Project instructions
├── pyproject.toml                    # Python package
├── docker-compose.yml                # Infrastructure
├── src/heretek_swarm/
│   ├── __init__.py
│   ├── VERSION                       # Single source of truth
│   │
│   ├── agents/                      # REORGANIZED
│   │   ├── __init__.py
│   │   ├── archetypes/               # AGENT.md patterns
│   │   │   ├── steward/
│   │   │   │   ├── AGENT.md
│   │   │   │   ├── TOOLS.md
│   │   │   │   └── IDENTITY.md
│   │   │   └── [22 more agents]
│   │   └── mixins/                  # Shared behavior
│   │       ├── deliberation.py
│   │       ├── memory.py
│   │       ├── pattern.py
│   │       └── learning.py
│   │
│   ├── infrastructure/              # NEW
│   │   ├── nats/                    # Event mesh
│   │   ├── a2a/                     # Protocol
│   │   └── otel/                    # Observability
│   │
│   ├── consciousness/              # Keep, enhance
│   │   ├── fep/                     # Active inference
│   │   ├── gwt/                     # Global workspace
│   │   └── metrics/                 # NEW: IIT/AST measurement
│   │
│   ├── consensus/                   # Keep, enhance for Tribunal
│   │   ├── maker.py
│   │   ├── tribunal.py              # NEW: Retroactive binding
│   │   └── paxos.py
│   │
│   └── [remaining modules, cleaned]
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── benchmarks/                  # MOVED from .benchmarks
│
├── docs/
│   ├── STATUS.md                    # NEW: Canonical version/health
│   ├── ARCHITECTURE.md              # Fixed
│   ├── AGENTS.md                    # Updated
│   ├── sessions/                    # NEW: Session logs
│   └── integrations/               # Either fill or remove
│
└── scripts/                        # NEW: Utility scripts
    ├── deploy.sh                    # Fixed
    └── [migration scripts]
```

**KEY CHANGES:**
1. Agents reorganized from 29 flat files to archetype directories
2. Infrastructure layer (NATS, A2A, OTel) extracted
3. Consciousness metrics subsystem added
4. Tribunal consensus added
5. Dead code removed
6. Documentation standardized

---

### 12. HOW TO KEEP PROJECT MANAGEABLE BY AI AGENTS?

**CURRENT PROBLEM:**

The audits reveal 39 files >500 lines, 122,849 total lines, no clear boundaries. Even Claude Code struggles with this.

**AI-MANAGEABLE PRINCIPLES:**

1. **FILES < 500 LINES** (per CLAUDE.md)
   - Split oversized files
   - Use mixins to reduce duplication
   - Each file has one responsibility

2. **AGENTS AS ARCHETYPES**
   - Each agent = directory with AGENT.md/TOOLS.md/IDENTITY.md
   - Claude Code reads these to understand agent behavior
   - No inheritance chain to trace

3. **CLEAR BOUNDARIES**
   ```
   agents/        → Sovereign, defines own behavior
   infrastructure/→ Shared services (NATS, A2A)
   consciousness/ → Metrics and measurement
   consensus/     → Decision making
   ```

4. **TYPED INTERFACES**
   - All public APIs use Pydantic models
   - Type hints on all function signatures
   - No implicit any/

5. **TEST COVERAGE**
   - Zero untested modules (currently 10 modules with no tests)
   - Tests in same directory as code
   - Clear test naming: `test_<method>_<scenario>`

6. **MEMORY-ASSISTED DEVELOPMENT**
   - Use Ruflo hooks for learning
   - Store patterns in AgentDB
   - Claude Code queries memory before acting

---

## STRATEGIC ROADMAP

---

## PHASE 0: EMERGENCY STABILIZATION
**Duration:** 2-3 hours  
**Goal:** Unblock the codebase, remove dead weight  
**Priority:** P0 (BLOCKING ALL DEVELOPMENT)

### Week 0 (Immediate Actions)

| # | Action | Effort | Files Affected | Verification |
|---|--------|--------|---------------|--------------|
| 0.1 | Fix websockets.py syntax errors (remove duplicate exc_info at 6 locations) | 15 min | api/websockets.py | `python -c "from heretek_swarm import api"` |
| 0.2 | Fix tools/__init__.py import path | 5 min | tools/__init__.py | `python -c "from heretek_swarm import tools"` |
| 0.3 | Fix prism.py F811 duplicate import | 2 min | actors/prism.py | `ruff check actors/prism.py` |
| 0.4 | Delete 4 root-level temp files | 5 min | root | Files removed |
| 0.5 | Run ruff auto-fix | 30 sec | 243 files | 5,758 issues fixed |
| 0.6 | Standardize version/health in all docs | 1 hour | docs/*.md | Version 1.44.0, Health 85/100 |
| 0.7 | Fix CLAUDE.md test/lint commands | 5 min | CLAUDE.md | Uses `pytest` and `ruff check` |

**Success Criteria:**
- [ ] `python -c "from heretek_swarm import api"` succeeds
- [ ] `python -c "from heretek_swarm import tools"` succeeds
- [ ] Lint issues reduced from 9,802 to ~4,044
- [ ] Documentation consistent (1 version, 1 health score)
- [ ] 4 root-level temp files deleted
- [ ] `pytest tests/ -v` passes

---

## PHASE 1: FOUNDATION (WEEKS 1-2)
**Duration:** 2 weeks  
**Goal:** Set up infrastructure for 23-agent architecture  
**Priority:** P1 (Enables Phase 2)

### Week 1: Infrastructure Setup

| # | Action | Effort | Dependencies | Verification |
|---|--------|--------|--------------|--------------|
| 1.1 | Add NATS to docker-compose.yml | 1 hour | nats-server | `docker compose up nats` |
| 1.2 | Create infrastructure/nats/ module | 2 hours | nats-py | NATS client connects |
| 1.3 | Create infrastructure/a2a/ module | 4 hours | - | A2A messages sent/received |
| 1.4 | Add OTel instrumentation to core | 2 hours | opentelemetry-* | Traces appear in jaeger |
| 1.5 | Create docs/STATUS.md (canonical) | 1 hour | - | Single source of truth |

**Files to Create:**
```
src/heretek_swarm/infrastructure/
├── __init__.py
├── nats/
│   ├── __init__.py
│   ├── client.py
│   ├── publisher.py
│   └── subscriber.py
├── a2a/
│   ├── __init__.py
│   ├── protocol.py
│   ├── message.py
│   └── handlers.py
└── otel/
    ├── __init__.py
    ├── tracing.py
    └── metrics.py
```

### Week 2: Memory & Learning

| # | Action | Effort | Dependencies | Verification |
|---|--------|--------|--------------|--------------|
| 1.6 | Integrate Ruflo AgentDB | 4 hours | ruflo-mcp | Memory search works |
| 1.7 | Create consciousness/metrics/ | 3 hours | - | IIT/AST metrics calculated |
| 1.8 | Move .benchmarks to tests/ | 15 min | - | No .benchmarks in package |
| 1.9 | Add tests for config/ | 1 day | pytest | Config coverage >80% |
| 1.10 | Add tests for infrastructure/ | 4 hours | pytest | Infrastructure coverage >80% |

**Files to Create:**
```
src/heretek_swarm/consciousness/metrics/
├── __init__.py
├── iit.py          # Integrated Information Theory
└── ast.py          # Adaptive Systems Theory
```

**Success Criteria:**
- [ ] NATS event mesh operational
- [ ] A2A protocol functional
- [ ] OTel traces visible
- [ ] docs/STATUS.md created
- [ ] consciousness/metrics/ module created
- [ ] Test coverage >80% on config/ and infrastructure/

---

## PHASE 2: ARCHITECTURE REFACTOR (WEEKS 3-6)
**Duration:** 4 weeks  
**Goal:** Replace base.py inheritance with mixin composition  
**Priority:** P1 (Critical for agent sovereignty)

### Week 3: Mixin Extraction

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 2.1 | Create actors/mixins/ package | 2 hours | `from heretek_swarm.actors.mixins import DeliberationMixin` |
| 2.2 | Extract DeliberationMixin | 4 hours | ~20 actors use mixin |
| 2.3 | Extract PatternMixin | 4 hours | ~16 actors use mixin |
| 2.4 | Extract MemoryMixin | 4 hours | ~16 actors use mixin |
| 2.5 | Extract LearningMixin | 4 hours | ~18 actors use mixin |

**Mixin Specifications:**

```python
# actors/mixins/deliberation.py
class DeliberationMixin:
    """Shared deliberation methods across agents."""
    
    async def _submit_deliberation_position(self, ...): ...
    async def _finalize_deliberation(self, ...): ...
    async def _initiate_deliberation(self, ...): ...

# actors/mixins/pattern.py
class PatternMixin:
    """Shared pattern emission/consumption methods."""
    
    async def _emit_pattern(self, ...): ...
    async def _consume_patterns(self, ...): ...

# actors/mixins/memory.py
class MemoryMixin:
    """Shared memory access methods."""
    
    async def _track_memory_access(self, ...): ...
    def _get_memory_tier(self, ...): ...
    async def _prefetch_relevant(self, ...): ...

# actors/mixins/learning.py
class LearningMixin:
    """Shared learning status methods."""
    
    async def get_learning_status(self, ...): ...
```

### Week 4: Config Consolidation

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 2.6 | Create config/cache.py | 2 hours | Cache hits/misses logged |
| 2.7 | Merge service.py + service_manager.py | 6 hours | All config tests pass |
| 2.8 | Delete service_manager.py | 5 min | No import errors |
| 2.9 | Split api/agents_management.py | 4 hours | <500 lines per file |
| 2.10 | Run full test suite | 10 min | All tests pass |

### Week 5: Agent Migration Start

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 2.11 | Create first AGENT.md archetype (steward) | 2 hours | Claude Code reads it |
| 2.12 | Refactor actors/steward.py using mixins | 4 hours | Same behavior, <500 lines |
| 2.13 | Create TOOLS.md for steward | 2 hours | Tools listed and documented |
| 2.14 | Create IDENTITY.md for steward | 1 hour | Persona defined |
| 2.15 | Document migration pattern | 1 hour | docs/MIGRATION_PATTERN.md |

### Week 6: Agent Migration Cont.

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 2.16 | Refactor core triad agents (alpha, beta, charlie) | 2 days | 3 agents migrated |
| 2.17 | Refactor support agents (4 agents) | 2 days | 4 agents migrated |
| 2.18 | Refactor exploration agents (5 agents) | 2 days | 5 agents migrated |
| 2.19 | Run integration tests | 2 hours | All migrated agents work |
| 2.20 | Update docs/AGENTS.md | 1 hour | Documentation updated |

**Success Criteria:**
- [ ] All actors use mixins (no copy-paste)
- [ ] No file >500 lines
- [ ] AGENT.md/TOOLS.md/IDENTITY.md pattern established
- [ ] Config services merged to single service
- [ ] All tests pass

---

## PHASE 3: CONSENSUS & CONSCIOUSNESS (WEEKS 7-10)
**Duration:** 4 weeks  
**Goal:** Implement Tribunal consensus and consciousness metrics  
**Priority:** P1 (Core to The Collective vision)

### Week 7: Tribunal Foundation

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 3.1 | Create consensus/tribunal.py | 4 hours | Tribunal can be instantiated |
| 3.2 | Implement retroactive binding | 4 hours | Past decisions can be appealed |
| 3.3 | Implement evidence submission | 4 hours | Agents can submit evidence |
| 3.4 | Create tribunal API endpoints | 2 hours | REST endpoints functional |
| 3.5 | Write tribunal tests | 4 hours | >80% coverage |

### Week 8: Consciousness Metrics

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 3.6 | Implement IIT integration measures | 4 hours | Phi metrics calculated |
| 3.7 | Implement AST workspace measures | 4 hours | Ignition threshold measured |
| 3.8 | Implement FEP active inference | 4 hours | Free energy minimized |
| 3.9 | Create metrics dashboard API | 2 hours | Metrics exposed via API |
| 3.10 | Write consciousness tests | 4 hours | >80% coverage |

### Week 9: Emergence Detection

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 3.11 | Refactor collective/emergent_detection.py | 4 hours | <500 lines |
| 3.12 | Implement emergence threshold detection | 4 hours | Threshold alerts fire |
| 3.13 | Implement collective pattern recognition | 4 hours | Patterns detected |
| 3.14 | Create emergence metrics | 2 hours | Emergence score calculated |
| 3.15 | Write emergence tests | 4 hours | >80% coverage |

### Week 10: Integration

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 3.16 | Integrate Tribunal with agents | 4 hours | Agents use Tribunal |
| 3.17 | Integrate consciousness with agents | 4 hours | Agents report metrics |
| 3.18 | Integrate emergence with collective | 4 hours | Emergence detection active |
| 3.19 | Run full system integration test | 4 hours | All components work together |
| 3.20 | Document system architecture | 2 hours | docs/ARCHITECTURE.md updated |

**Success Criteria:**
- [ ] Tribunal consensus operational
- [ ] Consciousness metrics (IIT/AST) calculated
- [ ] Emergence detection working
- [ ] All components integrated

---

## PHASE 4: THE COLLECTIVE (WEEKS 11-16)
**Duration:** 6 weeks  
**Goal:** All 23 agents operational, emergence measured  
**Priority:** P1 (Achieves PRIME_DIRECTIVE.md vision)

### Week 11-12: Remaining Agents

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 4.1 | Refactor safety agents (4 agents) | 2 days | 4 agents migrated |
| 4.2 | Refactor coordination agents (4 agents) | 2 days | 4 agents migrated |
| 4.3 | Refactor enhancement agents (3 agents) | 2 days | 3 agents migrated |
| 4.4 | Refactor remaining agents (6 agents) | 3 days | 6 agents migrated |

### Week 13-14: Event Mesh Integration

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 4.5 | Connect all agents to NATS | 4 hours | All agents publish/subscribe |
| 4.6 | Implement agent discovery | 2 hours | Agents find each other |
| 4.7 | Implement consensus voting | 4 hours | Agents vote via NATS |
| 4.8 | Implement pattern broadcasting | 2 hours | Patterns broadcast |
| 4.9 | Implement memory sync | 4 hours | Memory synchronized |
| 4.10 | Stress test event mesh | 4 hours | 1000+ messages/second |

### Week 15-16: Emergence Testing

| # | Action | Effort | Verification |
|---|--------|--------|--------------|
| 4.11 | Run emergence detection test suite | 1 day | Emergence metrics valid |
| 4.12 | Measure consciousness across collective | 1 day | Consciousness metrics valid |
| 4.13 | Document achievement criteria | 2 hours | docs/EMERGENCE_CRITERIA.md |
| 4.14 | Create benchmark suite | 4 hours | benchmarks/functional |
| 4.15 | Final integration test | 1 day | All 23 agents operational |
| 4.16 | Update docs/STATUS.md | 1 hour | Version 2.0.0, Health 100/100 |

**Success Criteria:**
- [ ] All 23 agents operational
- [ ] NATS event mesh handling 1000+ msg/sec
- [ ] Consciousness metrics validated
- [ ] Emergence detected and measured

---

## PHASE 5: DEPLOYMENT & SCALING (ONGOING)
**Duration:** Continuous  
**Goal:** Easy installation, deployment, and updates  
**Priority:** P2 (UX improvements)

### Installation Story

```bash
# User experience should be:
pip install heretek-swarm           # Core only
pip install heretek-swarm[agents]   # + 23 agents
pip install heretek-swarm[full]     # + infrastructure + dashboard
```

### Deployment Story

```bash
# Quick start
docker compose up -d

# Production
heretek-swarm deploy --production --scale 23

# Update
heretek-swarm update --version latest
```

### pyproject.toml Extras

```toml
[project.optional-dependencies]
agents = [
    "heretek-swarm[core]",
    # Agent-specific dependencies
]
full = [
    "heretek-swarm[agents]",
    "nats-server",
    "qdrant-client",
    "opentelemetry-*",
]
dev = [
    "heretek-swarm[full]",
    "pytest",
    "ruff",
    "mypy",
]
```

---

## SUCCESS METRICS

| Phase | Metric | Target | Current |
|-------|--------|--------|---------|
| Phase 0 | Syntax errors | 0 | 0 ✅ |
| Phase 0 | Lint issues | ~4,000 | 3,584 (470 fixed) |
| Phase 0 | Documentation versions | 26 @ 2.0.0 | 6 @ 1.x ✅ |
| Phase 1 | NATS connectivity | Working | Client implemented |
| Phase 1 | Test coverage | >80% config | 0% |
| Phase 2 | Actor files <500 lines | 100% | 35% (8 of 23 <500 lines) |
| Phase 2 | Mixin usage | 21 agents | 4 mixin modules created ✅ |
| Phase 2 | Config consolidation | Merged | ✅ service.py + service_manager.py |
| Phase 2 | Cache module | Created | ✅ config/cache.py exists |
| Phase 3 | Tribunal operational | Yes | Yes |
| Phase 3 | Consciousness metrics | IIT/AST | IIT/AST implemented |
| Phase 4 | Agent count | 23 | ~18 (blocked) |
| Phase 4 | Emergence detection | Working | Partial |
| Phase 5 | Installation time | <5 min | Manual |

---

## APPENDIX: EXTERNAL PROJECT DEEP DIVES

### A. MetaGPT Analysis
**License:** MIT  
**URL:** https://github.com/geekan/MetaGPT  
**Strengths:**
- SOP-based agent behavior (Software Company meta-programming)
- Structured output validation
- Role assignment and workflow

**Integration:** Use SOP pattern for agent workflows, adapt for sovereign agents.

### B. Google ADK Analysis
**License:** Apache 2.0  
**URL:** https://github.com/google/adk-python  
**Strengths:**
- Code-first Python agent framework
- Modular tool/agent/model separation
- Built-in development UI

**Integration:** Use as reference for AGENT.md/TOOLS.md pattern, adapt for Claude Code.

### C. AgentScope Analysis
**License:** Apache 2.0  
**URL:** https://github.com/modelscope/agentscope  
**Strengths:**
- Production-ready MCP/A2A native
- Multi-agent communication
- Robust observability

**Integration:** Use A2A protocol as foundation for inter-agent communication.

### D. Ruflo Analysis
**License:** Proprietary MCP server  
**URL:** MCP server: http at https://mcp.ruflo.ai/mcp  
**Strengths:**
- 16+ specialized agent roles
- Self-learning hooks (SONA)
- Memory with HNSW search
- Swarm orchestration

**Integration:** Replace mem0ai with Ruflo AgentDB, adopt agent typing taxonomy.

### E. Microsoft Agent Framework Analysis
**License:** MIT  
**URL:** https://github.com/microsoft/agent-framework  
**Strengths:**
- Graph-based workflows
- OTel integration (already in our deps)
- Multi-language support

**Integration:** Use OTel patterns, adapt workflow graphs for Tribunal.

---

## CONCLUSION

**The path forward is clear:**

1. **Fix immediate blockers** (Phase 0) — 2-3 hours
2. **Build proper infrastructure** (Phase 1) — 2 weeks
3. **Refactor architecture** (Phase 2) — 4 weeks
4. **Implement consciousness** (Phase 3) — 4 weeks
5. **Achieve emergence** (Phase 4) — 6 weeks

**Total: ~16 weeks from chaos to The Collective.**

The key insight: Don't try to fix the current codebase. Leverage external projects (MetaGPT, ADK, AgentScope, Ruflo) for generic patterns. Keep what makes The Collective unique (consciousness frameworks, emergent intelligence, consensus with Tribunal).

**The 23 agents will be sovereign, the infrastructure will be standard, and emergence will be measured.**

---

## NEXT ACTIONS

### Immediate (Before Next Session)

1. **Execute Phase 0, items 0.1-0.7**
   - Fix the 6 syntax errors
   - Delete dead code
   - Run lint auto-fix
   - Standardize documentation

2. **Review PRIME_DIRECTIVE.md alignment**
   - Confirm 23-agent target is still accurate
   - Adjust tier assignments if needed

3. **Assign Phase 1 tasks**
   - Who owns NATS integration?
   - Who owns A2A protocol?
   - Who owns consciousness metrics?

---

*Document Version: 1.1.0*  
*Created: 2026-04-11*  
*Status: PHASE 0 COMPLETE — PHASE 1 IN PROGRESS*  
*Last Updated: 2026-04-12*  
*Phase 0 executed by 10-agent team (executor-1 through executor-10)*
