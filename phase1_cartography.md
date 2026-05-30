# Phase 1.1 Cartography Findings — Session 2026-05-30

## ARCHITECTURE DISCOVERY

### Actors Package — CRITICAL REALIZATION

**The `actors/` directory is NOT flat files but a NESTED SUBPACKAGE with proper Python package hierarchy.**

- `heretek_swarm/actors/base/core.py` - Contains actual `AgentActor` class, `ActorMessage`, `ActorState`, `ActorStatus`
- `heretek_swarm/actors/base/message_handling.py` - `AgentActorMessageHandling` mixin
- `heretek_swarm/actors/base/state_management.py` - `AgentActorStateManagement` mixin
- `heretek_swarm/actors/supervisor.py` - `ActorSupervisor` class

**Imports use proper absolute package paths** via `heretek_swarm.actors.base.core` etc.

### Mixin-Based Extension Pattern

AgentActor uses Python mixin classes for composition:
- `AgentActorMessageHandling` — send/queue/broadcast
- `AgentAgentStateManagement` — save/load/persist
- `AuditMixin, ValidationMixin, HealthReportingMixin, PatternMixin` from actors.mixins

### Three-Tier Fallback Pattern

Every critical system has 3-tier fallback:
- Messaging: Event mesh → Direct registry → Queue
- Persistence: StateRepository → DB pool → Filesystem
- Routing: NATS → Stub → None

### HeavySwarm Workflow — 5-Phase Pattern

Implements Research → Analysis → Alternatives → Verification → Decision pipeline with phase handlers and consensus engine.

## KEY IMPORTS AND DEPENDENCIES

- `from swarms import Agent` — Swarms framework base class
- `from heretek_swarm.routing import AgentModelRouter` — Multi-provider LLM routing
- `from heretek_swarm.state.repository import StateRepository` — State persistence
- `from heretek_swarm.actors.validation import validate_message`

## VALIDATION ISSUES FOUND

1. **No validation errors** in backend/heretek_swarm/actors/base/core.py
2. **No validation errors** in backend/heretek_swarm/actors/supervisor.py
3. **No validation errors** in backend/heretek_swarm/memory/base.py
4. **No validation errors** in backend/heretek_swarm/orchestration/heavyswarm.py
5. **Traceback issues** in memory.py and phi_training.py need investigation

## FILES RED-FLAGGED FOR FURTHER AUDIT

- backend/heretek_swarm/memory/memory.py — MemoryMixin class hierarchy
- backend/heretek_swarm/collective_learning/phi_training.py — ActorActor (note double-A naming)
- Any file using `__import__()` — legacy pattern replaced with proper imports

## SESSION STATUS

Started: 2026-05-30
Mode: Audit/Cartography
Next: Type checking, pattern analysis, dependency validation
