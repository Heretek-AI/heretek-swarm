# Actor File Audit — Heretek Swarm

> **Purpose:** Complete inventory of every actor file in `heretek_swarm/actors/`, classified as canonical (standalone implementation) or shim (thin re-export from a subpackage).

**Audit Date:** 2025-05-07
**Source:** `heretek-swarm/heretek_swarm/actors/`

---

## Markdown Table

| Actor | Classification | Lines | Authoritative Path | Subpackage? | Notes |
|-------|--------------|-------|-------------------|-------------|-------|
| alpha.py | STANDALONE | 283 | `heretek_swarm/actors/alpha.py` | No | Primary decision-maker agent |
| arbiter.py | SHIM | 54 | `heretek_swarm/actors/arbiter/` | Yes | Re-exports from `arbiter/` subpackage |
| base.py | SHIM | 38 | `heretek_swarm/actors/base/` | Yes | Re-exports from `base/` subpackage |
| beta.py | STANDALONE | 300 | `heretek_swarm/actors/beta.py` | No | Secondary analyst agent |
| catalyst.py | STANDALONE | 1136 | `heretek_swarm/actors/catalyst.py` | No | Full implementation |
| charlie.py | STANDALONE | 394 | `heretek_swarm/actors/charlie.py` | No | Full implementation |
| chronos.py | SHIM | 40 | `heretek_swarm/actors/chronos/` | Yes | Re-exports from `chronos/` subpackage |
| coder.py | STANDALONE | 980 | `heretek_swarm/actors/coder.py` | No | Full implementation |
| dreamer.py | SHIM | 50 | `heretek_swarm/actors/dreamer/` | Yes | Re-exports from `dreamer/` subpackage |
| echo.py | STANDALONE | 750 | `heretek_swarm/actors/echo.py` | No | Full implementation |
| empath.py | STANDALONE | 1086 | `heretek_swarm/actors/empath.py` | No | Full implementation |
| examiner.py | SHIM | 61 | `heretek_swarm/actors/examiner/` | Yes | Re-exports from `examiner/` subpackage |
| explorer.py | STANDALONE | 1318 | `heretek_swarm/actors/explorer/` | Yes | Has subpackage but flat file is standalone (~1300 lines) |
| factory.py | STANDALONE | 224 | `heretek_swarm/actors/factory.py` | No | Actor factory |
| habit_forge.py | SHIM | 56 | `heretek_swarm/actors/habit_forge/` | Yes | Re-exports from `habit_forge/` subpackage |
| handoff.py | STANDALONE | 600 | `heretek_swarm/actors/handoff.py` | No | Full implementation |
| handoff_handlers.py | STANDALONE | 244 | `heretek_swarm/actors/handoff_handlers.py` | No | Handler implementations |
| historian.py | STANDALONE | 1354 | `heretek_swarm/actors/historian.py` | No | Full implementation |
| langroid_adapter.py | STANDALONE | 602 | `heretek_swarm/actors/langroid_adapter.py` | No | Langroid integration adapter |
| metis.py | STANDALONE | 1111 | `heretek_swarm/actors/metis.py` | No | Full implementation |
| perceiver.py | STANDALONE | 912 | `heretek_swarm/actors/perceiver.py` | No | Full implementation |
| perceiver_plus.py | SHIM | 54 | `heretek_swarm/actors/perceiver_plus/` | Yes | Re-exports from `perceiver_plus/` subpackage |
| prism.py | SHIM | 50 | `heretek_swarm/actors/prism/` | Yes | Re-exports from `prism/` subpackage |
| profiling.py | STANDALONE | 1095 | `heretek_swarm/actors/profiling.py` | No | Full implementation |
| sentinel_prime.py | SHIM | 44 | `heretek_swarm/actors/sentinel_prime/` | Yes | Re-exports from `sentinel_prime/` subpackage |
| steward.py | STANDALONE | 841 | `heretek_swarm/actors/steward.py` | No | Full implementation |
| stubs.py | STANDALONE | 53 | `heretek_swarm/actors/stubs.py` | No | Type stubs / type definitions |
| supervisor.py | STANDALONE | 557 | `heretek_swarm/actors/supervisor.py` | No | Full implementation |
| triad.py | SHIM | 30 | `heretek_swarm/actors/triad/` | Yes | Re-exports from `triad/` subpackage |
| validation.py | STANDALONE | 476 | `heretek_swarm/actors/validation.py` | No | Validation module (not agent) |

---

## Subpackage Canonical Sources

| Subpackage | Primary Module | Classes Exported |
|------------|---------------|-----------------|
| `arbiter/` | `core.py`, `handlers.py`, `strategies.py` | ArbiterAgent, ArbitrationStrategy |
| `base/` | `core.py`, `message_handling.py`, `state_management.py` | BaseAgent |
| `chronos/` | `agent.py`, `handlers.py`, `scheduler.py`, `types.py` | ChronosAgent, ScheduledTask |
| `coordinator/` | `agent.py`, `strategies.py`, `types.py` | CoordinatorAgent |
| `dreamer/` | `agent.py`, `generators.py`, `types.py` | DreamerAgent |
| `examiner/` | `agent.py`, `testing.py`, `types.py` | ExaminerAgent |
| `explorer/` | `agent.py`, `pathfinding.py`, `types.py` | ExplorerAgent |
| `habit_forge/` | `agent.py`, `streaks.py`, `tracking.py`, `types.py` | HabitForgeAgent |
| `mixins/` | `audit.py`, `deliberation.py`, `health_reporting.py`, `learning.py`, `memory.py`, `memory_access.py`, `pattern.py`, `pattern_consumer.py`, `tribunal.py`, `validation.py` | Various mixin classes |
| `nexus/` | `agent.py`, `routing.py`, `types.py` | NexusAgent |
| `perceiver_plus/` | `agent.py`, `analytics.py`, `types.py` | PerceiverPlusAgent |
| `prism/` | `agent.py`, `transforms.py`, `types.py` | PrismAgent |
| `sentinel/` | `agent.py`, `helpers.py`, `types.py` | SentinelAgent |
| `sentinel_prime/` | `agent.py`, `handlers.py`, `helpers.py`, `types.py` | SentinelPrimeAgent |
| `triad/` | `agent.py`, `balancing.py`, `types.py` | TriadAgent |

---

## JSON Machine-Parseable Block

```json
{
  "audit_date": "2025-05-07",
  "source_directory": "heretek-swarm/heretek_swarm/actors/",
  "summary": {
    "total_flat_files": 30,
    "shims": 11,
    "standalone": 19,
    "subpackages": 16
  },
  "actors": [
    {"name": "alpha", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/alpha.py", "lines": 283},
    {"name": "arbiter", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/arbiter/", "lines": 54},
    {"name": "base", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/base/", "lines": 38},
    {"name": "beta", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/beta.py", "lines": 300},
    {"name": "catalyst", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/catalyst.py", "lines": 1136},
    {"name": "charlie", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/charlie.py", "lines": 394},
    {"name": "chronos", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/chronos/", "lines": 40},
    {"name": "coder", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/coder.py", "lines": 980},
    {"name": "dreamer", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/dreamer/", "lines": 50},
    {"name": "echo", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/echo.py", "lines": 750},
    {"name": "empath", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/empath.py", "lines": 1086},
    {"name": "examiner", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/examiner/", "lines": 61},
    {"name": "explorer", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/explorer/", "lines": 1318},
    {"name": "factory", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/factory.py", "lines": 224},
    {"name": "habit_forge", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/habit_forge/", "lines": 56},
    {"name": "handoff", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/handoff.py", "lines": 600},
    {"name": "handoff_handlers", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/handoff_handlers.py", "lines": 244},
    {"name": "historian", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/historian.py", "lines": 1354},
    {"name": "langroid_adapter", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/langroid_adapter.py", "lines": 602},
    {"name": "metis", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/metis.py", "lines": 1111},
    {"name": "perceiver", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/perceiver.py", "lines": 912},
    {"name": "perceiver_plus", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/perceiver_plus/", "lines": 54},
    {"name": "prism", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/prism/", "lines": 50},
    {"name": "profiling", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/profiling.py", "lines": 1095},
    {"name": "sentinel_prime", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/sentinel_prime/", "lines": 44},
    {"name": "steward", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/steward.py", "lines": 841},
    {"name": "stubs", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/stubs.py", "lines": 53},
    {"name": "supervisor", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/supervisor.py", "lines": 557},
    {"name": "triad", "classification": "SHIM", "authoritative_path": "heretek_swarm/actors/triad/", "lines": 30},
    {"name": "validation", "classification": "STANDALONE", "authoritative_path": "heretek_swarm/actors/validation.py", "lines": 476}
  ]
}
```

---

## Classification Criteria

- **SHIM:** Flat `.py` file that re-exports from a matching subpackage (contains `from .<pkg>` or `from heretek_swarm.actors.<pkg>`) or has explicit "backward compatibility" / "shim" / "re-export" markers.
- **STANDALONE:** Flat `.py` file with full implementation; no re-export from subpackage.
- **CANONICAL_SUBPACKAGE:** When a subpackage exists, its `__init__.py` typically defines the canonical agent class; flat file serves as shim.
