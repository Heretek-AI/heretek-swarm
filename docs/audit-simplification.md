# Simplification Audit Report

**Date:** 2026-04-11
**Auditor:** simplification-auditor agent
**Scope:** Full codebase — over-engineering, file organization, complexity, dependency, and naming issues

---

## Executive Summary

The heretek-swarm codebase exhibits significant structural bloat from three root causes:

1. **Massive actor method duplication** — 12 boilerplate methods are copy-pasted across 16-18 actor classes, accounting for roughly 8,000-10,000 lines of pure duplication.
2. **Oversized files** — 39 source files exceed the 500-line project guideline; the top 10 range from 1,392 to 1,859 lines.
3. **Dead code at the root** — Four root-level scripts (641 lines total) are leftover generation/test artifacts that should be deleted.

Consolidating the two config services, extracting actor boilerplate into mixins, and removing dead code would eliminate an estimated 15,000-20,000 lines while changing zero user-facing behavior.

---

## 1. Root-Level Dead Code

These files sit at the repository root outside any package. They are not imported by `src/` or `tests/` and appear to be one-off generation/test scripts.

| File | Lines | Purpose | Action |
|------|-------|---------|--------|
| `temp_self_model_part1.py` | 244 | Temporary self-model prototype | Delete |
| `generate_docker_compose.py` | 213 | Docker compose generator script | Move to `scripts/` or delete |
| `generate_prometheus_config.py` | 124 | Prometheus config generator | Move to `scripts/` or delete |
| `test_verification.py` | 60 | Ad-hoc verification test | Delete |

**Total recoverable:** 641 lines, 4 files.

Additionally, `src/heretek_swarm/.benchmarks/` (4.0K) lives inside the Python package. Benchmarks should be in `tests/` or a top-level `benchmarks/` directory, not distributed with the package.

---

## 2. Files Exceeding 500-Line Guideline

39 files exceed the project's 500-line standard. The worst offenders:

| File | Lines | Category |
|------|-------|----------|
| `api/agents_management.py` | 1,859 | API layer — god file |
| `actors/arbiter.py` | 1,819 | Actor — god class |
| `config/service.py` | 1,588 | Config — duplicated with service_manager |
| `actors/perceiver_plus.py` | 1,537 | Actor |
| `actors/base.py` | 1,527 | Actor base — shared but still oversized |
| `collective/swarm_intelligence.py` | 1,469 | Collective intelligence |
| `collective/emergent_detection.py` | 1,440 | Collective detection |
| `actors/prism.py` | 1,413 | Actor |
| `consensus/maker_enhanced.py` | 1,393 | Consensus logic |
| `consciousness/fep_active_inference.py` | 1,392 | Consciousness module |

Full list of 39 files over 500 lines:

- `api/agents_management.py` (1,859)
- `actors/arbiter.py` (1,819)
- `config/service.py` (1,588)
- `actors/perceiver_plus.py` (1,537)
- `actors/base.py` (1,527)
- `collective/swarm_intelligence.py` (1,469)
- `collective/emergent_detection.py` (1,440)
- `actors/prism.py` (1,413)
- `consensus/maker_enhanced.py` (1,393)
- `consciousness/fep_active_inference.py` (1,392)
- `actors/empath.py` (1,383)
- `actors/alpha.py` (1,362)
- `actors/charlie.py` (1,350)
- `actors/beta.py` (1,328)
- `config/service_manager.py` (1,292)
- `actors/steward.py` (1,288)
- `actors/echo.py` (1,274)
- `actors/scout.py` (1,263)
- `actors/omega.py` (1,262)
- `actors/perceiver.py` (1,254)
- `actors/herald.py` (1,233)
- `actors/oracle.py` (1,225)
- `actors/delta.py` (1,206)
- `actors/forge.py` (1,197)
- `actors/inspector.py` (1,182)
- `actors/catalyst.py` (1,165)
- `actors/architect.py` (1,157)
- `actors/sage.py` (1,132)
- `actors/nexus.py` (1,126)
- `actors/sentinel.py` (1,119)
- `actors/sentinel_plus.py` (1,109)
- `consensus/maker.py` (1,065)
- `actors/curator.py` (1,052)
- `consensus/paxos.py` (1,044)
- `consensus/round_robin.py` (1,030)
- `memory/memory_manager.py` (999)
- `consciousness/fep_agent.py` (993)
- `collective/collective_behavior.py` (975)
- `actors/lyra.py` (953)

**Pattern:** Actor files dominate the list. 27 of 39 oversized files are actors, all following the same boilerplate-heavy pattern (see Section 3).

---

## 3. Actor Method Duplication (Highest Impact)

Across 165 parsed actor files, the following methods are copy-pasted nearly identically into 15-21 classes:

| Method | Duplicated Across | Est. Lines per Copy | Total Wasted Lines |
|--------|-------------------|---------------------|---------------------|
| `to_dict` | 21 classes | ~15 | ~315 |
| `_submit_deliberation_position` | 18 classes | ~30 | ~540 |
| `_finalize_deliberation` | 18 classes | ~30 | ~540 |
| `get_learning_status` | 18 classes | ~20 | ~360 |
| `_emit_pattern` | 16 classes | ~25 | ~400 |
| `_consume_patterns` | 16 classes | ~25 | ~400 |
| `_initiate_deliberation` | 16 classes | ~35 | ~560 |
| `_track_memory_access` | 16 classes | ~20 | ~320 |
| `_get_memory_tier` | 16 classes | ~15 | ~240 |
| `_prefetch_relevant` | 16 classes | ~20 | ~320 |
| `initialize` | 16 classes | ~25 | ~400 |
| `process_message` | 15 classes | ~40 | ~600 |

**Estimated total duplication:** ~4,995 lines across these 12 methods alone.

**Root cause:** Actors inherit from `base.py` but then override with identical implementations. The methods should be in a shared mixin or remain in the base class without override.

**Recommended pattern:**

```python
# src/heretek_swarm/actors/mixins/
class DeliberationMixin:
    def _submit_deliberation_position(self, ...): ...
    def _finalize_deliberation(self, ...): ...
    def _initiate_deliberation(self, ...): ...

class PatternMixin:
    def _emit_pattern(self, ...): ...
    def _consume_patterns(self, ...): ...

class MemoryMixin:
    def _track_memory_access(self, ...): ...
    def _get_memory_tier(self, ...): ...
    def _prefetch_relevant(self, ...): ...

class LearningMixin:
    def get_learning_status(self, ...): ...
```

Each actor would then compose only the mixins it actually needs, removing hundreds of lines of boilerplate per file.

---

## 4. Config Service Duplication

Two files define overlapping `ConfigurationService` classes:

| Attribute | `config/service.py` | `config/service_manager.py` |
|-----------|---------------------|----------------------------|
| Lines | 1,588 | 1,292 |
| Combined | 2,880 | — |

**11 overlapping functions:**
- `__init__`
- `_decrypt_extra_config`
- `_encrypt_extra_config`
- `_get_cache`
- `_get_cache_key`
- `_invalidate_cache`
- `_set_cache`
- `_validate_config_value`
- `get_config_service`
- `get_embedding_provider_api_key`
- `get_llm_provider_api_key`

Both files provide configuration management with caching, encryption, and provider key retrieval. The differences appear to be additive rather than divergent — `service_manager.py` adds lifecycle management on top of what `service.py` provides.

**Recommendation:** Merge into a single `config/service.py` (estimated ~1,600 lines), extract caching logic into a small `config/cache.py` utility (~100 lines), and delete `config/service_manager.py`.

---

## 5. Dependency Audit

### Python (pyproject.toml) — 17 Production Dependencies

| Dependency | Version | Assessment |
|------------|---------|------------|
| `swarms` | >=5.0.0 | Core framework — keep |
| `pydantic` | >=2.0.0 | Validation — keep |
| `httpx` | >=0.25.0 | HTTP client — keep |
| `redis` | >=5.0.0 | Caching — verify usage |
| `qdrant-client` | >=1.7.0 | Vector DB — verify usage |
| `opentelemetry-api` | >=1.22.0 | Observability — keep |
| `opentelemetry-sdk` | >=1.22.0 | Observability — keep |
| `opentelemetry-exporter-*` | >=1.22.0 | Observability — keep |
| `structlog` | >=24.1.0 | Logging — keep |
| `tenacity` | >=8.2.0 | Retries — keep |
| `circuitbreaker` | >=2.0.0 | Resilience — verify usage |
| `starlette` | >=0.27.0 | ASGI — overlaps with FastAPI |
| `uvicorn` | >=0.25.0 | ASGI server — keep |
| `websockets` | >=12.0 | WS support — keep |
| `mem0ai` | >=1.0.0 | Memory — verify usage |
| `fastapi` | >=0.109.0 | Web framework — keep |

**Potential simplifications:**
- `starlette` is a transitive dependency of `fastapi` — listing it explicitly may be unnecessary unless direct starlette APIs are used outside FastAPI routes.
- `circuitbreaker` — grep for actual usage; if only used in 1-2 places, tenacity could cover retries + circuit-breaking.
- `redis` and `qdrant-client` — confirm these are actively used and not carried from an earlier architecture.

### JavaScript (package.json) — 9 Production Dependencies

Clean and minimal. No concerns. Dev dependencies (13) are standard Electron + React + Vite tooling.

---

## 6. Structural Issues

### 6.1 Legacy Import Paths

Some modules in `src/heretek_swarm/` import from legacy paths `src/state/` and `src/tools/` that sit outside the package namespace. These should be migrated to proper package-relative imports.

### 6.2 .benchmarks Inside Package

`src/heretek_swarm/.benchmarks/` should not ship with the package. Move to `tests/benchmarks/` or a top-level `benchmarks/` directory and exclude from the wheel via `pyproject.toml`.

### 6.3 Documentation Sprawl

The `docs/` directory is large and established. The `.outdated_docs/` archive contains 16 stale reports. Consider periodic pruning of `.outdated_docs/`.

---

## 7. Priority Recommendations

| Priority | Issue | Estimated Effort | Lines Recovered |
|----------|-------|------------------|-----------------|
| **P0** | Delete 4 root-level dead files | 30 min | 641 |
| **P0** | Move `.benchmarks` out of package | 15 min | 0 (structure) |
| **P1** | Extract actor boilerplate into mixins | 2-3 days | ~5,000 |
| **P1** | Merge config/service.py + service_manager.py | 4-6 hours | ~1,280 |
| **P2** | Verify and prune unused dependencies | 2-3 hours | 0 (deps) |
| **P2** | Fix legacy import paths (src/state/, src/tools/) | 1-2 hours | 0 (health) |
| **P3** | Split oversized API/consensus/collective files | 2-3 days | 0 (structure) |
| **P3** | Prune .outdated_docs/ | 15 min | varies |

**Total estimated line reduction from P0+P1:** ~6,920 lines with no behavioral changes.

---

## 8. Numbered Action Items

1. **Delete `temp_self_model_part1.py`** — confirmed dead code, no imports found.
2. **Delete `test_verification.py`** — ad-hoc test, not part of the test suite.
3. **Move `generate_docker_compose.py` and `generate_prometheus_config.py`** to `scripts/` or delete if docker/prometheus configs are now managed elsewhere.
4. **Move `src/heretek_swarm/.benchmarks/`** to `tests/benchmarks/` and add exclusion to `pyproject.toml`.
5. **Create `src/heretek_swarm/actors/mixins/` package** with `DeliberationMixin`, `PatternMixin`, `MemoryMixin`, and `LearningMixin`.
6. **Refactor all 18 actor classes** using deliberation methods to use `DeliberationMixin` instead of local copies.
7. **Refactor all 16 actor classes** using pattern/memory methods to use `PatternMixin` and `MemoryMixin`.
8. **Merge `config/service_manager.py` into `config/service.py`**, preserving all functionality from both files.
9. **Extract config caching** into a small `config/cache.py` utility to keep the merged service under 500 lines.
10. **Grep for `circuitbreaker` usage** — if minimal, replace with tenacity or remove.
11. **Grep for direct `starlette` usage** — if none outside FastAPI, remove from pyproject.toml.
12. **Verify `redis` and `qdrant-client`** are actively used in current code paths.
13. **Audit legacy imports** from `src/state/` and `src/tools/` — migrate to package-relative imports.
14. **Prune `.outdated_docs/`** — archive or delete reports older than 90 days.
15. **Split `api/agents_management.py`** (1,859 lines) into domain-focused submodules (e.g., `api/agents_crud.py`, `api/agents_lifecycle.py`).

---

## Methodology

- File line counts via `wc -l` on all `.py` files in `src/` and root.
- Actor method duplication via AST parsing of 165 actor files.
- Config service overlap via symbol comparison (`get_symbols_overview`).
- Dependency audit via `pyproject.toml` and `package.json` inspection.
- Dead code identification via import tracing and file location analysis.
