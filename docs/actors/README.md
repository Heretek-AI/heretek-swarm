# Actors Guide

**Quick start:** Create a custom agent in under 30 minutes by subclassing , picking mixins, registering with , and exporting from .

---

## Overview

The Heretek Swarm provides **23 specialized agents** implemented as Python classes under . Each agent subclasses  (defined in ) and composes capability from 10 reusable mixins.

Two conventions coexist:

| Convention | Description | Example |
|---|---|---|
| **Flat file** | Single  file exports one agent class |  →  |
| **Subpackage** | Directory with  + supporting modules | ,  |

---

## Architecture

### AgentActor Base Class

All agents inherit from  (defined in ). The base class provides:

- **Lifecycle** — , , ,  hooks
- **Mailbox** — Internal message queue with async dispatch
- **State management** — ActorStatus enum, ActorState tracking
- **Structured logging** — Pre-configured  logger per agent

The base class is split across three modules in the  subpackage:

| Module | Contents |
|---|---|
|  |  init, lifecycle, mailbox, status |
|  | Message dispatch, handler registration |
|  | State persistence, serialization |

### Mixin Capability System

Mixins provide optional, composable capabilities. Each mixin is a standalone class in  that combines with  via multiple inheritance.

**Available mixins (10 total):**

| Mixin | File | Purpose |
|---|---|---|
|  |  | Action logging, audit trails |
|  |  | Multi-step reasoning, internal deliberation |
|  |  | Health check endpoints, diagnostics |
|  |  | Experience replay, pattern learning |
|  |  | Memory read/write, retrieval |
|  |  | Fine-grained memory access control |
|  |  | Pattern extraction, recognition |
|  |  | Consuming emitted patterns |
|  |  | Consensus participation, voting |
|  |  | Input/output validation, security rules |

### MRO (Method Resolution Order) Guidelines

When composing mixins:

1. **Non-AgentActor mixins come first** in the class hierarchy
2. **AgentActor must be last** in the base class list
3. Maintain consistent ordering across similar agents

### Supervisor

 (in ) wraps supervision capabilities around agents: launch, health monitoring, restart on failure. It inherits from , , , , and .

### Factory

 (in ) provides agent registration and instantiation:

-  — Register an agent class
-  — Create an instance
-  — Singleton accessor

---

## Creating an Agent

### Walkthrough: Custom QA Agent

**Step 1: Create the agent file**



**Step 2: Register in **



**Step 3: Register with ActorFactory**



**Step 4: Run (minimal)**



---

## Quick Reference: All 23 Agents

| Agent | Tier | Type | File | Mixins |
|---|---|---|---|---|
| AlphaAgent | 1 (Core Triad) | subpackage |  | Health, Validation, Deliberation, Pattern, Memory, Learning |
| BetaAgent | 1 | subpackage |  | Health, Validation, Deliberation, Pattern, Memory, Learning |
| CharlieAgent | 1 | subpackage |  | Health, Validation, Deliberation, Pattern, Memory |
| StewardAgent | 1 | subpackage |  | Audit, Validation, Health, Pattern |
| HistorianAgent | 2 (Support) | flat |  | Audit, Validation, Pattern, Memory |
| MetisAgent | 2 | flat |  | Validation, Deliberation, Pattern, Memory, Learning |
| EmpathAgent | 2 | flat |  | Health, Validation, Deliberation, Pattern, Memory, Learning |
| PerceiverAgent | 2 | flat |  | Validation, Pattern, Memory |
| EchoAgent | 2 | subpackage | echo/ | Health, Validation |
| ExplorerAgent | 3 (Exploration) | subpackage |  | Validation, Pattern, Memory, Learning |
| ExaminerAgent | 3 | subpackage |  | Validation, Pattern, Memory |
| DreamerAgent | 3 | subpackage |  | Validation, Pattern, Memory |
| CoderAgent | 3 | flat |  | Validation, Pattern, Memory |
| SentinelAgent | 4 (Safety) | subpackage |  | Audit, Validation, Pattern, Memory |
| SentinelPrimeAgent | 4 | subpackage |  | Audit, Validation, Pattern, Memory |
| ArbiterAgent | 4 | subpackage |  | Audit, Validation, Tribunal, Pattern |
| CoordinatorAgent | 5 (Coordination) | subpackage |  | Validation, Deliberation, Pattern, Memory |
| NexusAgent | 5 | subpackage |  | Validation, Pattern, Memory |
| CatalystAgent | 5 | flat |  | Validation, Deliberation, Pattern |
| ChronosAgent | 5 | subpackage |  | Validation, Pattern, Memory |
| PrismAgent | 6 (Enhancement) | subpackage |  | Validation, Pattern, Memory, Learning |
| HabitForgeAgent | 6 | subpackage |  | Validation, Pattern, Memory |
| PerceiverPlusAgent | 6 | subpackage |  | Validation, Pattern, Memory, Learning |

**Mixin key:** Audit=AuditMixin, Health=HealthReportingMixin, Validation=ValidationMixin, Deliberation=DeliberationMixin, Pattern=PatternMixin, Memory=MemoryMixin, Learning=LearningMixin, Tribunal=TribunalMixin.

---

## Running Locally

### No-infrastructure mode (unit tests only)



### Full stack

Requires PostgreSQL, Redis, Qdrant, and NATS (see ):


The command 'docker' could not be found in this WSL 2 distro.
We recommend to activate the WSL integration in Docker Desktop settings.

For details about using Docker Desktop with WSL 2, visit:

https://docs.docker.com/go/wsl2/

---

## Testing Guide

### Test files

| Test | Command |
|---|---|
| Base class tests |  |
| Mixin unit tests |  |
| Factory tests |  |
| Specific agent |  |

### Writing a test


