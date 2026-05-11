# Heretek Swarm Actors — Practical Guide

> This document explains how the actor system works and how to create a custom agent. It's written for contributors who want to add new functionality to the swarm.

## Overview: Two Actor Conventions

The `heretek_swarm/actors/` directory uses two organizational conventions:

### Flat actor files

Simple, self-contained agents live as single `.py` files directly in `actors/`:

| File | Agent | Lines |
|------|-------|-------|
| `alpha.py` | AlphaAgent | ~300 |
| `beta.py` | BetaAgent | ~300 |
| `steward.py` | StewardAgent | ~900 |
| `charlie.py` | CharlieAgent | ~400 |
| `coder.py` | CoderAgent | ~1000 |
| `echo.py` | EchoActor | ~700 |
| `empath.py` | EmpathAgent | ~1100 |
| `historian.py` | HistorianAgent | ~1300 |
| `metis.py` | MetisAgent | ~1100 |
| `perceiver.py` | PerceiverAgent | ~1000 |
| `catalyst.py` | CatalystAgent | ~1100 |

### Subpackaged actors

Large agents that have been decomposed into smaller modules (per the extraction pattern in `docs/EXTRACTION_PATTERN.md`) live as subpackages:

```
actors/sentinel/           # SentinelAgent — Safety Guardian
    __init__.py            # Re-exports from agent.py, types.py, helpers.py
    agent.py               # Main SentinelAgent class
    types.py               # SafetyLevel, SafetyViolation, ViolationType enums
    helpers.py             # SentinelHelpers mixin + standalone utility functions

actors/sentinel_prime/     # SentinelPrimeAgent — Security Commander
    __init__.py
    agent.py
    handlers.py
    helpers.py
    types.py

actors/triad/              # TriadAgent, StewardAgent, AlphaAgent, BetaAgent, CharlieAgent
    __init__.py
    agent.py               # Shared TriadAgent base + all four agent classes
    balancing.py
    types.py

actors/arbiter/            # ArbiterAgent — Conflict Resolution
actors/chronos/            # ChronosAgent — Temporal Scheduling
actors/coordinator/        # CoordinatorAgent — Multi-Agent Coordination
actors/dreamer/            # DreamerAgent — Creative Generation
actors/examiner/           # ExaminerAgent — QA & Testing
actors/explorer/           # ExplorerAgent — Intelligence Gathering
actors/habit_forge/        # HabitForgeAgent — Behavior Architecture
actors/nexus/              # NexusAgent — External Integration
actors/perceiver_plus/     # PerceiverPlusAgent — Advanced Analytics
actors/prism/              # PrismAgent — Multi-Perspective Analysis
```

Each subpackage has:
- `agent.py` — the main agent class (inherits from AgentActor + mixins)
- `types.py` — enums, dataclasses, type aliases
- Domain-specific helper modules (e.g. `scheduler.py`, `strategies.py`, `pathfinding.py`)
- `__init__.py` — re-exports all public symbols

---

## Architecture: How the Pieces Compose

### AgentActor (base class)

Located at `heretek_swarm/actors/base/core.py`.

Every agent in the system subclasses `AgentActor`. It provides:

- **Mailbox-based message processing** — an `asyncio.Queue` processes messages sequentially via `_process_mailbox()`
- **Lifecycle management** — `spawn()`, `terminate()`, `cleanup()`, heartbeat loop
- **Message routing** — `process_message()` dispatches to registered handlers by message type
- **LLM integration** — optional `swarms_agent` for LLM capabilities; `_model_router` for multi-provider routing
- **State persistence** — optional `StateRepository` + auto-persist at configurable intervals
- **Injectable dependency stubs** — `access_analyzer`, `pattern_extractor`, `tribunal`, etc. (passed via kwargs, defaults to `_actor_stubs` for testability)

Base class import:
```python
from heretek_swarm.actors.base import AgentActor, ActorMessage, ActorState, ActorStatus
```

The message handling and state management are extended via mixin submodules:
- `base/message_handling.py` — `send()`, `broadcast()`, `reply()` methods
- `base/state_management.py` — `update_state()`, `get_state()`, `save_state()`, `load_state()` methods

### The 10 Mixins

Located at `heretek_swarm/actors/mixins/`. Mixins add reusable capabilities to agents via cooperative multiple inheritance:

| Mixin | Purpose | Used By |
|-------|---------|---------|
| `ValidationMixin` | Input validation, behavioral baselines (8 immutable rules) | All agents (core tier + many others) |
| `HealthReportingMixin` | Health check endpoint, status reporting | Steward, Alpha, Beta, Charlie, Echo, Empath, Historian, Metis, Perceiver, Nexus, Sentinel, SentinelPrime |
| `LearningMixin` | Pattern learning, experience accumulation | All Triad agents + Arbiter + most subpackaged agents |
| `MemoryMixin` | Long-term memory storage and retrieval | Triad agents, Arbiter, and most subpackaged agents |
| `PatternMixin` | Pattern extraction and matching | Triad agents, Arbiter, and most subpackaged agents |
| `DeliberationMixin` | Multi-agent deliberation via MAKER consensus | Most agents (not Alpha/Beta/Charlie directly — inherited via TriadAgent) |
| `TribunalMixin` | Dispute resolution, conflict mediation | StewardAgent (only) |
| `AuditMixin` | Audit trail logging | ActorSupervisor (only) |
| `MemoryAccessMixin` | Fine-grained memory access control | Specialist use |
| `PatternConsumerMixin` | Consume extracted patterns from other agents | Specialist use |

**How the MRO works:**

```python
class MyAgent(
    HealthReportingMixin,
    ValidationMixin,
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    AgentActor,  # Must always be last (or at least after all mixins)
):
    ...
```

Python's C3 linearization ensures `super()` calls chain through mixins in declaration order and end at `AgentActor.__init__()`.

### ActorSupervisor

Located at `heretek_swarm/actors/supervisor.py`.

The `ActorSupervisor` (itself a subclass of `AgentActor` + `AuditMixin` + `ValidationMixin` + `HealthReportingMixin` + `PatternMixin`) manages the lifecycle of multiple actors:

- **Spawn/terminate** actors with persistent configuration
- **Health monitoring loop** — periodic checks, auto-restart on failure
- **Configuration storage** — stores `ActorConfig` for each instance to enable resurrection
- **Broadcast** messages to all actors

```python
supervisor = ActorSupervisor()
actor = await supervisor.spawn_actor(MyAgent, "my-agent-1")
await supervisor.start_monitoring()
statuses = await supervisor.get_all_status()
await supervisor.terminate_all()
```

### ActorFactory

Located at `heretek_swarm/actors/factory.py`.

The `ActorFactory` provides a registry for actor classes with default initialization parameters:

```python
factory = ActorFactory()

# Register an actor class with default kwargs
factory.register_actor_class("my-agent", MyAgent, {"name": "My Agent"})

# Create an instance from the registry
actor = factory.create_actor("my-agent", actor_id="instance-1")

# List all registered types
factory.get_registered_types()
```

A global singleton is available via `get_factory()`.

---

## Creating an Agent: Walkthrough

This section walks through adding a `CustomQA` agent that validates output quality.

### Step 1: Create the agent file

Create `heretek_swarm/actors/custom_qa.py`:

```python
"""Custom QA Agent — output quality validation."""

from __future__ import annotations

from typing import Any

import structlog

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.actors.mixins import (
    HealthReportingMixin,
    ValidationMixin,
    LearningMixin,
)

logger = structlog.get_logger("CustomQAAgent")


class CustomQAAgent(
    HealthReportingMixin,
    ValidationMixin,
    LearningMixin,
    AgentActor,
):
    """Validates output quality and reports metrics."""

    actor_type = "CustomQA"

    def __init__(
        self,
        agent_id: str | None = None,
        name: str | None = None,
        topics: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            name=name or "CustomQA",
            topics=topics or ["quality", "validation"],
            capabilities=["quality_validation", "metric_reporting"],
            **kwargs,
        )
        self._quality_scores: dict[str, float] = {}

    async def initialize(self) -> None:
        """Register custom message handlers on spawn."""
        self.register_handler("validate_output", self._handle_validate)
        self.register_handler("get_metrics", self._handle_get_metrics)
        logger.info(f"[{self.agent_id}] CustomQA initialized")

    async def process_message(self, message: ActorMessage) -> None:
        """Route incoming messages to registered handlers."""
        if message.message_type in self._message_handlers:
            await self._message_handlers[message.message_type](message)
        else:
            logger.warning(f"Unknown message type: {message.message_type}")

    async def _handle_validate(self, message: ActorMessage) -> None:
        """Validate output quality from message content."""
        content = message.content.get("output", "")
        score = self._score_quality(content)
        self._quality_scores[message.correlation_id or "unknown"] = score
        logger.info(f"Quality score: {score:.2f}")

    async def _handle_get_metrics(self, message: ActorMessage) -> None:
        """Report accumulated quality metrics."""
        avg = (
            sum(self._quality_scores.values()) / len(self._quality_scores)
            if self._quality_scores
            else 0.0
        )
        await self.send(
            message.reply_to or message.sender,
            {"average_score": avg, "total_validated": len(self._quality_scores)},
        )

    def _score_quality(self, output: str) -> float:
        """Score output quality (0.0–1.0)."""
        if not output:
            return 0.0
        # Simplified heuristic: longer outputs score higher (up to 0.9)
        length_score = min(len(output) / 1000, 0.9)
        return length_score
```

### Step 2: Add `__init__.py` re-exports

In `heretek_swarm/actors/__init__.py`, add:

```python
from heretek_swarm.actors.custom_qa import CustomQAAgent
```

And add `"CustomQAAgent"` to the `__all__` list.

### Step 3: Register with ActorFactory

In your application bootstrap code:

```python
from heretek_swarm.actors.factory import get_factory
from heretek_swarm.actors.custom_qa import CustomQAAgent

factory = get_factory()
factory.register_actor_class(
    "custom-qa",
    CustomQAAgent,
    {"name": "QA Validator", "topics": ["quality"]},
)

# Later, create an instance
qa = factory.create_actor("custom-qa", actor_id="qa-1")
await qa.spawn()
```

Alternatively, for direct usage without the factory:

```python
qa = CustomQAAgent(agent_id="qa-1", topics=["quality"])
await qa.spawn()
```

### Step 4: Minimal working example

```python
import asyncio
from heretek_swarm.actors.custom_qa import CustomQAAgent

async def main():
    agent = CustomQAAgent(agent_id="qa-demo", topics=["validation"])
    await agent.spawn()

    # Send a validation request
    await agent.send(
        "qa-demo",
        {"output": "This is a sample output for quality validation."},
        message_type="validate_output",
    )

    # Check metrics
    metrics = await agent.send_and_receive(
        "qa-demo", {}, message_type="get_metrics"
    )
    print(f"Average quality score: {metrics['average_score']:.2f}")

    await agent.terminate()

asyncio.run(main())
```

---

## Quick Reference: All 23 Agents

| Agent | Tier | Convention | File | Key Mixins |
|-------|------|-----------|------|------------|
| Steward | 1 (Core Triad) | Subpackage (triad/) | `triad/agent.py` | H, V, D, P, M, L, T |
| Alpha | 1 (Core Triad) | Subpackage (triad/) | `triad/agent.py` | H, V, L |
| Beta | 1 (Core Triad) | Subpackage (triad/) | `triad/agent.py` | H, V, L |
| Charlie | 1 (Core Triad) | Subpackage (triad/) | `triad/agent.py` | H, V, L |
| Historian | 2 (Support) | Flat | `historian.py` | H, V, D, P, M, L |
| Metis | 2 (Support) | Flat | `metis.py` | H, V, D, L, M, P |
| Empath | 2 (Support) | Flat | `empath.py` | H, V, D, P, M, L |
| Perceiver | 2 (Support) | Flat | `perceiver.py` | H, V, D, P, M, L |
| Echo | 2 (Support) | Flat | `echo.py` | H, V, P, D, M, L |
| Explorer | 3 (Exploration) | Subpackage | `explorer/agent.py` | EP, V, D, P, M, L |
| Examiner | 3 (Exploration) | Subpackage | `examiner/agent.py` | ET, EV, V, D, P, M, L |
| Dreamer | 3 (Exploration) | Subpackage | `dreamer/agent.py` | V, D, P, M, L, DG |
| Coder | 3 (Exploration) | Flat | `coder.py` | V, D, P, M, L |
| Sentinel | 4 (Safety) | Subpackage | `sentinel/agent.py` | H, V, D, P, M, L, SH |
| Sentinel-Prime | 4 (Safety) | Subpackage | `sentinel_prime/agent.py` | SPH, SPHa, H, V, D, P, M, L |
| Arbiter | 4 (Safety) | Subpackage | `arbiter/core.py` | De, P, Me, L |
| Coordinator | 5 (Coordination) | Subpackage | `coordinator/agent.py` | V, P, D, M, L |
| Nexus | 5 (Coordination) | Subpackage | `nexus/agent.py` | H, V, P, D, M, L, NR |
| Catalyst | 5 (Coordination) | Flat | `catalyst.py` | V, D, P, M, L |
| Chronos | 5 (Coordination) | Subpackage | `chronos/agent.py` | CS, CH, V, P, D, M, L |
| Prism | 6 (Enhancement) | Subpackage | `prism/agent.py` | V, D, P, M, L, PT |
| Habit-Forge | 6 (Enhancement) | Subpackage | `habit_forge/agent.py` | V, D, P, M, L |
| Perceiver+ | 6 (Enhancement) | Subpackage | `perceiver_plus/agent.py` | V, D, P, M, L, PA |

**Mixin key:** H=HealthReportingMixin, V=ValidationMixin, D=DeliberationMixin, P=PatternMixin, M=MemoryMixin, L=LearningMixin, T=TribunalMixin, EP=ExplorerPathfindingMixins, ET=ExaminingTestingMixin, EV=ExaminingValidationMixin, DG=DreamerGeneratorsMixin, SH=SentinelHelpers, SPH=SentinelPrimeHelpers, SPhA=SentinelPrimeHandlers, De=DeliberationMixin, Me=MemoryMixin, CS=ChronosSchedulerMixin, CH=ChronosHandlersMixin, NR=NexusRoutingHelpers, PT=PrismTransforms, PA=PerceiverAnalyticsMixinImpl

---

## Running Agents Locally

### No-infra mode (no Docker, no databases)

The swarm can run entirely in-memory:

```bash
heretek-swarm run --no-infra --prompt "Analyze this text" --target-agent alpha
```

This starts a minimal runtime with all 23 agents in-memory and routes your prompt through the specified agent.

Key flags:
- `--no-infra` — skip external infrastructure (Postgres, Redis, NATS, Qdrant)
- `--prompt "..."` — the input to process
- `--target-agent <name>` — route to a specific agent (e.g. `alpha`, `sentinel`, `arbiter`)
- `--detach` — run as a background daemon

### Full stack

```bash
docker compose up
heretek-swarm run --prompt "Analyze this"
```

This starts all services (Postgres, Redis, Qdrant, NATS, API server, dashboard) and runs the swarm with full persistence.

---

## How Tests Work

Tests live in `heretek-swarm/tests/` and use `pytest`. There are 16 test files covering:

| Test File | Focus |
|-----------|-------|
| `test_consensus_coordinator.py` | MAKER consensus protocol (51 tests) |
| `test_consensus_runtime.py` | Consensus runtime (14 tests) |
| `test_consensus_cli.py` | CLI commands (42 tests) |
| `test_consensus_audit_jsonl.py` | Audit trail (19 tests) |
| `test_consensus_websocket.py` | WebSocket streaming (13 tests) |
| `test_auto_routing_integration.py` | Auto-routing (22 tests) |
| `test_complexity_heuristic.py` | Complexity detection (52 tests) |
| `test_consciousness_api.py` | Consciousness metrics (4 tests) |
| `test_domain_selector.py` | Domain routing (19 tests) |
| `test_goal_*.py` | Goal system (7 files, ~95 tests total) |
| `test_workflow_persistence.py` | Workflow state (24 tests) |

### Running tests

```bash
# All tests
cd heretek-swarm && python3 -m pytest tests/

# Specific test file
python3 -m pytest tests/test_complexity_heuristic.py

# By keyword
python3 -m pytest tests/ -k "consensus"

# With verbose output
python3 -m pytest tests/ -v

# With coverage
python3 -m pytest tests/ --cov=heretek_swarm
```

### Writing tests for a new agent

Tests use pytest fixtures and direct instantiation. Example pattern:

```python
import pytest
from heretek_swarm.actors.custom_qa import CustomQAAgent

@pytest.fixture
def qa_agent():
    agent = CustomQAAgent(agent_id="test-qa")
    return agent

class TestCustomQA:
    @pytest.mark.asyncio
    async def test_spawn_and_terminate(self, qa_agent):
        await qa_agent.spawn()
        assert qa_agent.is_alive
        await qa_agent.terminate()
        assert qa_agent.state == ActorState.TERMINATED

    @pytest.mark.asyncio
    async def test_message_handling(self, qa_agent):
        await qa_agent.spawn()
        # ... send test messages, verify responses
        await qa_agent.terminate()
```

Run agent-specific tests:
```bash
python3 -m pytest tests/ -k "custom_qa"
```
