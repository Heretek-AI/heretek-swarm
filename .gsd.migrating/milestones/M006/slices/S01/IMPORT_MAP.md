# IMPORT MAP — Complete Import Dependency Analysis

**Generated:** 2026-05-11
**Source:** AST-based import analysis of all 429 Python files across `heretek_swarm/`, `tests/`, and `src/`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total .py files scanned | 429 |
| Files with import statements | 424 |
| Unique external import targets | 91 |
| Unique internal module imports | ~260 distinct `heretek_swarm.*` modules |
| Top internal module by importers | `heretek_swarm.actors.base` (35 files) |
| Top external dependency | `typing` (297 import statements) |
| Relative import files | ~25% of source files |

---

## 1. Subpackage Dependency Graph

Each subpackage is listed with the other subpackages it depends on. A `depends_on: []` entry indicates a leaf package with no external internal dependencies.

```yaml
subpackage_dependencies:
  heretek_swarm.__root__:
    depends_on:
      - heretek_swarm.actors
      - heretek_swarm.cli
      - heretek_swarm.config
      - heretek_swarm.consensus
      - heretek_swarm.logging
      - heretek_swarm.memory
      - heretek_swarm.orchestration
      - heretek_swarm.plugins
      - heretek_swarm.runtime

  heretek_swarm.actors:
    depends_on:
      - heretek_swarm.agents
      - heretek_swarm.api
      - heretek_swarm.collective
      - heretek_swarm.consciousness
      - heretek_swarm.consensus
      - heretek_swarm.coordination
      - heretek_swarm.creativity
      - heretek_swarm.gateway
      - heretek_swarm.goals
      - heretek_swarm.infrastructure
      - heretek_swarm.knowledge
      - heretek_swarm.llm
      - heretek_swarm.logging
      - heretek_swarm.memory
      - heretek_swarm.routing
      - heretek_swarm.schemas
      - heretek_swarm.security
      - heretek_swarm.state
      - heretek_swarm.testing
      - heretek_swarm.validation

  heretek_swarm.agents:
    depends_on: []  # leaf

  heretek_swarm.api:
    depends_on:
      - heretek_swarm.actors
      - heretek_swarm.agents
      - heretek_swarm.channels
      - heretek_swarm.collective
      - heretek_swarm.config
      - heretek_swarm.consciousness
      - heretek_swarm.consensus
      - heretek_swarm.evaluation
      - heretek_swarm.gateway
      - heretek_swarm.infrastructure
      - heretek_swarm.infrastructure.nats
      - heretek_swarm.llm
      - heretek_swarm.logging
      - heretek_swarm.mcp
      - heretek_swarm.memory
      - heretek_swarm.models
      - heretek_swarm.observability
      - heretek_swarm.plugins
      - heretek_swarm.rag
      - heretek_swarm.routing
      - heretek_swarm.runtime
      - heretek_swarm.schemas
      - heretek_swarm.security
      - heretek_swarm.state
      - heretek_swarm.utils
      - heretek_swarm.workflow

  heretek_swarm.channels:
    depends_on: []  # leaf

  heretek_swarm.cli:
    depends_on:
      - heretek_swarm._cli_module
      - heretek_swarm.config
      - heretek_swarm.goals
      - heretek_swarm.logging
      - heretek_swarm.runtime

  heretek_swarm.collective:
    depends_on:
      - heretek_swarm.consciousness

  heretek_swarm.config:
    depends_on: []  # leaf

  heretek_swarm.consciousness:
    depends_on:
      - heretek_swarm.consensus
      - heretek_swarm.infrastructure.nats
      - heretek_swarm.security
      - heretek_swarm.validation

  heretek_swarm.consensus:
    depends_on:
      - heretek_swarm.infrastructure.nats
      - heretek_swarm.security

  heretek_swarm.coordination:
    depends_on: []  # leaf

  heretek_swarm.creativity:
    depends_on: []  # leaf

  heretek_swarm.embeddings:
    depends_on:
      - heretek_swarm.infrastructure

  heretek_swarm.embeddings.providers:
    depends_on: []  # leaf

  heretek_swarm.evaluation:
    depends_on: []  # leaf

  heretek_swarm.gateway:
    depends_on:
      - heretek_swarm.infrastructure.nats
      - heretek_swarm.security

  heretek_swarm.goals:
    depends_on:
      - heretek_swarm.actors
      - heretek_swarm.consensus

  heretek_swarm.governance:
    depends_on:
      - heretek_swarm.collective
      - heretek_swarm.consensus
      - heretek_swarm.security

  heretek_swarm.infrastructure:
    depends_on:
      - heretek_swarm.collective
      - heretek_swarm.config
      - heretek_swarm.consensus
      - heretek_swarm.logging
      - heretek_swarm.memory
      - heretek_swarm.models

  heretek_swarm.infrastructure.a2a:
    depends_on: []  # leaf

  heretek_swarm.infrastructure.nats:
    depends_on: []  # leaf

  heretek_swarm.infrastructure.otel:
    depends_on: []  # leaf

  heretek_swarm.integrations:
    depends_on: []  # leaf

  heretek_swarm.interfaces:
    depends_on: []  # leaf

  heretek_swarm.knowledge:
    depends_on:
      - heretek_swarm.rag

  heretek_swarm.llm:
    depends_on:
      - heretek_swarm.config
      - heretek_swarm.infrastructure

  heretek_swarm.llm.providers:
    depends_on: []  # leaf

  heretek_swarm.logging:
    depends_on: []  # leaf

  heretek_swarm.mcp:
    depends_on:
      - heretek_swarm.tools

  heretek_swarm.memory:
    depends_on: []  # leaf

  heretek_swarm.models:
    depends_on: []  # leaf

  heretek_swarm.observability:
    depends_on:
      - heretek_swarm.consciousness
      - heretek_swarm.infrastructure.otel
      - heretek_swarm.workflow

  heretek_swarm.orchestration:
    depends_on:
      - heretek_swarm.actors
      - heretek_swarm.consensus

  heretek_swarm.plugins:
    depends_on:
      - heretek_swarm.consciousness

  heretek_swarm.rag:
    depends_on:
      - heretek_swarm.embeddings.providers

  heretek_swarm.routing:
    depends_on:
      - heretek_swarm.llm

  heretek_swarm.runtime:
    depends_on:
      - heretek_swarm.actors
      - heretek_swarm.agents
      - heretek_swarm.api
      - heretek_swarm.channels
      - heretek_swarm.collective
      - heretek_swarm.config
      - heretek_swarm.consciousness
      - heretek_swarm.consensus
      - heretek_swarm.gateway
      - heretek_swarm.infrastructure.nats
      - heretek_swarm.integrations
      - heretek_swarm.llm
      - heretek_swarm.logging
      - heretek_swarm.mcp
      - heretek_swarm.memory
      - heretek_swarm.plugins
      - heretek_swarm.rag
      - heretek_swarm.routing
      - heretek_swarm.tools

  heretek_swarm.schemas:
    depends_on:
      - heretek_swarm.validation

  heretek_swarm.security:
    depends_on: []  # leaf

  heretek_swarm.slices:
    depends_on: []  # leaf

  heretek_swarm.state:
    depends_on:
      - heretek_swarm.infrastructure.otel

  heretek_swarm.testing:
    depends_on: []  # leaf

  heretek_swarm.tools:
    depends_on:
      - heretek_swarm.models

  heretek_swarm.utils:
    depends_on: []  # leaf

  heretek_swarm.validation:
    depends_on: []  # leaf

  heretek_swarm.workflow:
    depends_on:
      - heretek_swarm.actors
      - heretek_swarm.memory
      - heretek_swarm.runtime
```

### Centrality Ranking (by dependency count)

| Rank | Subpackage | Dependencies |
|------|-----------|-------------|
| 1 | `heretek_swarm.api` | 26 |
| 2 | `heretek_swarm.actors` | 20 |
| 3 | `heretek_swarm.runtime` | 19 |
| 4 | `heretek_swarm.__root__` | 9 |
| 5 | `heretek_swarm.infrastructure` | 6 |
| 6 | `heretek_swarm.cli` | 5 |

---

## 2. Per-File Import Catalog (Key Files)

### `heretek_swarm/__init__.py` — Package entry point

```yaml
path: heretek_swarm/__init__.py
type: package_init
imports:
  internal:
    - heretek_swarm.actors.base
    - heretek_swarm.actors.supervisor
    - heretek_swarm.consensus.maker
    - heretek_swarm.memory.base
    - heretek_swarm.orchestration.heavyswarm
    - heretek_swarm.plugins.consciousness
    - heretek_swarm.plugins.liberation
```

### `heretek_swarm/__main__.py` — CLI launcher

```yaml
path: heretek_swarm/__main__.py
type: entry_point
imports:
  internal:
    - heretek_swarm.cli
```

### `heretek_swarm/cli.py` — Legacy CLI surface (top-level)

```yaml
path: heretek_swarm/cli.py
type: cli_entry
imports:
  internal:
    - heretek_swarm.cli.config_loader
    - heretek_swarm.cli.config_wizard
    - heretek_swarm.cli.goal_commands
    - heretek_swarm.config.models
    - heretek_swarm.consensus.complexity
    - heretek_swarm.logging.config (3 separate import blocks)
    - heretek_swarm.runtime.daemon (4 separate import blocks)
    - heretek_swarm.runtime.main_loop (3 separate import blocks)
  external_packages:
    - click, httpx, structlog, uvicorn, redis, asyncio, json, os, sys, pathlib, webbrowser
```

**Issue:** `heretek_swarm/cli.py` has multiple redundant import blocks for `setup_logging`, `AutonomousSwarm`, and daemon utilities — clean these up during restructure.

### `heretek_swarm/cli/__init__.py` — CLI package init

```yaml
path: heretek_swarm/cli/__init__.py
type: cli_proxy
imports:
  internal:
    - heretek_swarm._cli_module (mass import of 27+ symbols)
    - heretek_swarm.cli.config_loader
    - heretek_swarm.cli.config_wizard (7 symbols)
```

**Issue:** `heretek_swarm/cli/__init__.py` re-exports everything from `heretek_swarm._cli_module` which is actually the legacy `heretek_swarm/cli.py`. This creates a circular naming problem (`cli.py` and `cli/__init__.py` coexist).

### `heretek_swarm/actors/__init__.py` — Actor registry

```yaml
path: heretek_swarm/actors/__init__.py
type: actor_registry
imports:
  internal:
    - heretek_swarm.actors.arbiter
    - heretek_swarm.actors.base
    - heretek_swarm.actors.catalyst
    - heretek_swarm.actors.chronos
    - heretek_swarm.actors.coder
    - heretek_swarm.actors.coordinator
    - heretek_swarm.actors.dreamer
    - heretek_swarm.actors.echo
    - heretek_swarm.actors.empath
    - heretek_swarm.actors.examiner
    - heretek_swarm.actors.explorer
    - heretek_swarm.actors.factory
    - heretek_swarm.actors.habit_forge
    - heretek_swarm.actors.historian
    - heretek_swarm.actors.metis
    - heretek_swarm.actors.nexus
    - heretek_swarm.actors.perceiver
    - heretek_swarm.actors.perceiver_plus
    - heretek_swarm.actors.prism
    - heretek_swarm.actors.sentinel
    - heretek_swarm.actors.sentinel_prime
    - heretek_swarm.actors.supervisor
    - heretek_swarm.actors.triad
```

### `heretek_swarm/actors/supervisor.py` — Actor management

```yaml
path: heretek_swarm/actors/supervisor.py
type: actor_coordinator
imports:
  internal:
    - heretek_swarm.actors.base
    - heretek_swarm.actors.factory
    - heretek_swarm.actors.mixins
    - heretek_swarm.collective.learning
  external_packages:
    - asyncio, structlog, typing
```

### `heretek_swarm/actors/validation.py` — Legacy validation shim

```yaml
path: heretek_swarm/actors/validation.py
type: backward_compat_shim
imports:
  internal:
    - heretek_swarm.actors.mixins.validation (shim delegates to ValidationMixin)
  external_packages:
    - datetime, pydantic, re, typing, uuid
```

**Note per MEM008/MEM009:** This file is a backward-compat shim. New code should import from `heretek_swarm.actors.mixins.validation.ValidationMixin` directly. During M007 restructure, consider removing this shim or keeping it with a deprecation warning.

### `heretek_swarm/actors/mixins/validation.py` — ValidationMixin (source of truth)

```yaml
path: heretek_swarm/actors/mixins/validation.py
type: validation_core
imports:
  external_packages:
    - asyncio, copy, hashlib, json, statistics, structlog, time, typing
```

**Note:** This module has NO internal heretek_swarm imports — it is a pure utility layer with standard library dependencies only.

### `heretek_swarm/api/main.py` — FastAPI application surface

```yaml
path: heretek_swarm/api/main.py
type: api_surface
imports:
  internal:
    - All 22 actor types from heretek_swarm.actors.*
    - heretek_swarm.agents.agent_factory
    - heretek_swarm.api.* (16+ sub-modules via wildcard-ish re-export)
    - heretek_swarm.config.loader
    - heretek_swarm.config.service
    - heretek_swarm.gateway.auth
    - heretek_swarm.gateway.nats_event_mesh
    - heretek_swarm.logging.config
    - heretek_swarm.mcp.server
    - heretek_swarm.memory.persistent
    - heretek_swarm.observability.prometheus_metrics
    - heretek_swarm.observability.tracing
    - heretek_swarm.state.repository
  external_packages:
    - fastapi, sqlalchemy, redis, httpx, asyncio, structlog, json, os, datetime, contextlib
```

### `heretek_swarm/runtime/autonomous_runtime.py`

```yaml
path: heretek_swarm/runtime/autonomous_runtime.py
type: runtime_core
imports:
  internal:
    - heretek_swarm.actors.base
    - heretek_swarm.actors.supervisor
    - heretek_swarm.collective.agency_tracking
    - heretek_swarm.consciousness.agency_metrics
    - heretek_swarm.infrastructure.nats.publisher
    - heretek_swarm.integrations.discord_bot
    - heretek_swarm.integrations.slack_bot
    - heretek_swarm.plugins.consciousness_enhanced
  relative:
    - .agent_runtime
    - .autonomous_runtime_config
    - .scaling
    - .self_maintenance
  external_packages:
    - asyncio, dataclasses, datetime, httpx, json, os, pathlib, psutil, signal, smtplib, structlog, typing
```

### `src/cli.py` — External CLI launcher

```yaml
path: src/cli.py
type: external_cli
imports:
  internal:
    - heretek_swarm.config.models (HealthStatus, InfrastructureService)
  external_packages:
    - __future__, asyncio, click, httpx, pathlib, redis, shutil, structlog, subprocess, sys, time, typing
```

**Critical for M007:** `src/cli.py` is the ONLY file outside `heretek-swarm/heretek_swarm/` that imports from `heretek_swarm`. Any move of `heretek_swarm` must update this import path or restructure `src/cli.py`.

### `heretek_swarm/orchestration/heavyswarm.py`

```yaml
path: heretek_swarm/orchestration/heavyswarm.py
type: orchestration_engine
imports:
  internal:
    - heretek_swarm.actors.base
    - heretek_swarm.consensus.maker
  relative:
    - .phase_handlers (AlternativesPhaseHandler, AnalysisPhaseHandler, DecisionPhaseHandler, PhaseHandler, PhaseHandlerRegistry)
  external_packages:
    - asyncio, collections, dataclasses, datetime, enum, structlog, typing, uuid
```

---

## 3. Test File Import Analysis

All test files import from `heretek_swarm` using absolute imports:

```yaml
test_imports:
  tests/test_auto_routing_integration.py:
    depends_on:
      - heretek_swarm.cli
      - heretek_swarm.consensus.complexity
      - heretek_swarm.consensus.consensus_coordinator
      - heretek_swarm.consensus.domain_selector
      - heretek_swarm.consensus.maker

  tests/test_complexity_heuristic.py:
    depends_on:
      - heretek_swarm.consensus.complexity

  tests/test_consciousness_api.py:
    depends_on:
      - heretek_swarm.api
      - heretek_swarm.api.consciousness
      - heretek_swarm.runtime.registry_enhanced

  tests/test_consensus_audit_jsonl.py:
    depends_on:
      - heretek_swarm.consensus.audit_models
      - heretek_swarm.consensus.audit_trail

  tests/test_consensus_cli.py:
    depends_on:
      - heretek_swarm.cli
      - heretek_swarm.consensus.complexity

  tests/test_consensus_coordinator.py:
    depends_on:
      - heretek_swarm.consensus.consensus_coordinator
      - heretek_swarm.consensus.domain_selector
      - heretek_swarm.consensus.maker

  tests/test_consensus_runtime.py:
    depends_on:
      - heretek_swarm.consensus.maker
      - heretek_swarm.runtime.main_loop

  tests/test_consensus_websocket.py:
    depends_on:
      - heretek_swarm.api.consensus
      - heretek_swarm.api.websockets

  tests/test_domain_selector.py:
    depends_on:
      - heretek_swarm.consensus.domain_selector

  tests/test_goal_cli.py:
    depends_on:
      - heretek_swarm.cli
      - heretek_swarm.goals.models

  tests/test_goal_consensus.py:
    depends_on:
      - heretek_swarm.goals.consensus
      - heretek_swarm.goals.models
      - heretek_swarm.consensus.consensus_coordinator
      - heretek_swarm.consensus.maker

  tests/test_goal_pipeline.py:
    depends_on:
      - heretek_swarm.goals.pipeline
      - heretek_swarm.goals.models
      - heretek_swarm.goals.store

  tests/test_goal_proposer.py:
    depends_on:
      - heretek_swarm.goals.models
      - heretek_swarm.goals.proposer

  tests/test_goal_store.py:
    depends_on:
      - heretek_swarm.goals.models
      - heretek_swarm.goals.store

  tests/test_goal_translator.py:
    depends_on:
      - heretek_swarm.goals.models
      - heretek_swarm.goals.translator

  tests/test_workflow_persistence.py:
    depends_on:
      - heretek_swarm.workflow.store
      - heretek_swarm.api.workflows
      - heretek_swarm.workflow.engine
      - heretek_swarm.gateway.auth
```

**M007 impact:** All 16 test files use absolute `from heretek_swarm.X import Y` imports. If the package root moves, every test file needs its imports updated.

---

## 4. Relative Import Patterns

Relative imports are used extensively within subpackages for intra-package cohesion:

| Directory | Relative Import Count |
|-----------|---------------------|
| `heretek_swarm/runtime` | 33 |
| `heretek_swarm/api` | 25 |
| `heretek_swarm/actors` | 24 |
| `heretek_swarm/consensus` | 18 |
| `heretek_swarm/consciousness` | 15 |
| `heretek_swarm/cli` | 11 |
| `heretek_swarm/goals` | 5 |
| `heretek_swarm/plugins` | 4 |
| `heretek_swarm/actors/arbiter` | 3 |
| `heretek_swarm/actors/sentinel_prime` | 3 |
| `heretek_swarm/interfaces` | 3 |

Relative imports are safe during restructure as long as intra-package directory structure is preserved relative to sibling modules.

---

## 5. External Dependency Analysis

### Top External Dependencies by frequency

| Package | Import Count | Category |
|---------|-------------|----------|
| `typing` | 297 | stdlib |
| `structlog` | 243 | logging |
| `datetime` | 212 | stdlib |
| `dataclasses` | 158 | stdlib |
| `enum` | 134 | stdlib |
| `__future__` | 118 | stdlib |
| `asyncio` | 116 | stdlib |
| `uuid` | 112 | stdlib |
| `json` | 104 | stdlib |
| `collections` | 87 | stdlib |
| `time` | 74 | stdlib |
| `os` | 61 | stdlib |
| `fastapi` | 52 | web framework |
| `httpx` | 36 | HTTP client |
| `re` | 33 | stdlib |
| `hashlib` | 29 | stdlib |
| `pathlib` | 28 | stdlib |
| `pydantic` | 27 | validation |
| `sqlalchemy` | 21 | ORM |
| `opentelemetry` | 18 | observability |
| `pytest` | 16 | testing |
| `starlette` | 14 | web framework |
| `nats` | 11 | messaging |
| `redis` | 10 | caching |
| `swarms` | 12 | external framework |
| `click` | ~15 (est.) | CLI framework |

### Framework Dependencies (M007 CI Impact)

| Framework | Used In | CI/Workflow Relevance |
|-----------|---------|---------------------|
| `fastapi` | `api/main.py`, all `api/` modules | Server startup, health checks |
| `sqlalchemy` | `config/`, `state/`, `api/` | DB migration checks |
| `nats` | `infrastructure/nats/` | Messaging test infra |
| `redis` | `cli.py`, `api/` | Cache test infra |
| `click` | `cli.py`, `cli/`, `audit/cli.py` | CLI integration tests |
| `pytest` | All `tests/` | Core test runner |
| `uvicorn` | `cli.py` | Server startup |
| `httpx` | `cli.py`, `api/` | HTTP health checks |
| `opentelemetry` | `infrastructure/otel/` | Observability pipeline |

---

## 6. Dead/Redundant Import Paths

### Redundant import blocks in `heretek_swarm/cli.py`

The legacy `heretek_swarm/cli.py` has duplicated imports:
- `from heretek_swarm.logging.config import setup_logging` — imported 3 times in the same file
- `from heretek_swarm.runtime.main_loop import AutonomousSwarm` — imported 3 times
- `from heretek_swarm.runtime.daemon import ...` — imports spread across 4 separate blocks

### `heretek_swarm.actors.handoff.py` → `heretek_swarm.actors.handoff_handlers.py` circular naming

Two files reference `heretek_swarm.actors.handoff` which is ambiguous between `handoff.py` and `handoff/__init__.py`. The `handoff_handlers.py` file does `from heretek_swarm.actors.handoff import *` which resolves to the `handoff/__init__.py` package.

### Legacy shim: `heretek_swarm/actors/validation.py` → `heretek_swarm/actors/mixins/validation.py`

Per MEM008/MEM009, this is a backward-compat shim. All new code should import from the mixin directly. If no external consumers rely on the shim path, remove in M007.

### Legacy proxy: `heretek_swarm/cli/__init__.py` → `heretek_swarm._cli_module`

Re-exports everything from a module named `_cli_module` which is actually `heretek_swarm/cli.py` renamed via import machinery. This is fragile and should be cleaned up.

### `heretek_swarm/actors/handoff_handlers.py`

Only does `from heretek_swarm.actors.handoff import *` — a thin re-export. If nothing references this file, it's dead code.

---

## 7. Cycle Detection

### Direct bidirectional cycles: NONE

No direct bidirectional import cycles detected at the subpackage level.

### Potential transitive cycles

These paths warrant attention during M007:
1. `actors` → `consensus` → `security` (and `actors` uses `security` directly)
2. `runtime` → `actors` → `collective` → `consciousness` → `consensus` (and `runtime` → `consensus`)
3. `api` → `runtime` → `api` (possible transitive via `actors`)

No actual Python import errors expected (these are all package-level deps, not runtime issues), but they indicate high coupling.

---

## 8. CI/Workflow Impact List

Files that would need CI/workflow updates if `heretek_swarm` is moved/renamed:

### Direct path references in config files

| File | Reference | Action |
|------|-----------|--------|
| `pyproject.toml` | `packages = ["heretek-swarm/heretek_swarm"]` | Update package path |
| `pyproject.toml` | `[project.scripts]` entry points | Update module paths |
| `Dockerfile` (if present) | `COPY heretek-swarm/` | Update copy paths |
| `docker-compose.yml` | volume mounts, build context | Update paths |
| `.github/workflows/*.yml` | `cd heretek-swarm && ...` | Update working dirs |
| `.pre-commit-config.yaml` | file paths | Update if paths change |
| `.env.example` | path references | Update if needed |
| `uv.lock` | package resolution | Regenerate |

### Imports that cross the `heretek-swarm/` boundary

| Source | Target | Risk |
|--------|--------|------|
| `src/cli.py` | `heretek_swarm.config.models` | **HIGH** — only file outside package dir |
| `tests/*.py` | `heretek_swarm.*` | **HIGH** — all 16 test files |
| `triage_classifier.py` | `heretek_swarm` (if any) | **LOW** — root-level utility, likely standalone |

---

## 9. Leaf Packages (Safest to Move First)

These subpackages have zero internal `heretek_swarm` dependencies and can be extracted independently:

| Leaf Package | Status |
|-------------|--------|
| `heretek_swarm.agents` | Pure leaf |
| `heretek_swarm.channels` | Pure leaf |
| `heretek_swarm.config` | Pure leaf |
| `heretek_swarm.coordination` | Pure leaf |
| `heretek_swarm.creativity` | Pure leaf |
| `heretek_swarm.embeddings.providers` | Pure leaf |
| `heretek_swarm.evaluation` | Pure leaf |
| `heretek_swarm.infrastructure.a2a` | Pure leaf |
| `heretek_swarm.infrastructure.nats` | Pure leaf |
| `heretek_swarm.infrastructure.otel` | Pure leaf |
| `heretek_swarm.integrations` | Pure leaf |
| `heretek_swarm.interfaces` | Pure leaf |
| `heretek_swarm.llm.providers` | Pure leaf |
| `heretek_swarm.logging` | Pure leaf |
| `heretek_swarm.memory` | Pure leaf |
| `heretek_swarm.models` | Pure leaf |
| `heretek_swarm.security` | Pure leaf |
| `heretek_swarm.slices` | Pure leaf |
| `heretek_swarm.testing` | Pure leaf |
| `heretek_swarm.utils` | Pure leaf |
| `heretek_swarm.validation` | Pure leaf |

---

## 10. Migration Complexity by Package

| Package | Consumer Count | Dependency Count | Migration Difficulty |
|---------|---------------|-----------------|---------------------|
| `heretek_swarm.actors.base` | 35 | 0 (leaf) | **MEDIUM** — widely consumed but self-contained |
| `heretek_swarm.actors` | 35+ | 20 | **HIGH** — central hub |
| `heretek_swarm.runtime` | 10+ | 19 | **HIGH** — orchestrates everything |
| `heretek_swarm.api` | 5+ | 26 | **HIGH** — API surface touches all |
| `heretek_swarm.consensus` | 15+ | 2 | **MEDIUM** — well-scoped |
| `heretek_swarm.config` | 20+ | 0 | **LOW** — leaf but widely consumed |

---

*End of IMPORT_MAP.md*
