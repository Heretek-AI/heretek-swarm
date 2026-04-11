# Dead Code Audit Report

**Date:** 2026-04-11
**Scope:** `src/heretek_swarm/`, root-level files
**Method:** ruff F401/F811 checks, cross-module grep, symbol reference analysis, filesystem scan

## Summary

| Category | Count | Action |
|----------|-------|--------|
| Unused imports | 3 | Fix |
| Syntax errors (duplicate kwargs) | 6 | Fix immediately |
| Unreferenced modules | 5 | Investigate |
| Temp files (root) | 6 | Delete |
| Dead functions/classes | 40 | Archive or delete |
| Already archived | 2 dirs | No action |

---

## 1. Unused Imports

| File | Line | Code | Note |
|------|------|------|------|
| `src/heretek_swarm/actors/langroid_adapter.py` | 28 | `from langroid.embedding.EmbeddingConfig` | Inside try/except availability check |
| `src/heretek_swarm/actors/langroid_adapter.py` | 30 | `from langroid.vector_store.VectorStoreConfig` | Inside try/except availability check |
| `src/heretek_swarm/actors/prism.py` | 29 | `from heretek_swarm.consciousness.phi_training import AgentActor` | F811: redefines `AgentActor` imported at line 22 from `heretek_swarm.actors.base` |

**Recommendation:** Keep the langroid_adapter imports (they are guarded by try/except for optional dependency). Fix prism.py by removing the duplicate import and using only one source.

---

## 2. Syntax Errors

`src/heretek_swarm/api/websockets.py` has duplicate `exc_info=True` keyword arguments at 6 locations:

| Line | Context |
|------|---------|
| 389 | `logger.error(...)` call |
| 512 | `logger.error(...)` call |
| 605 | `logger.error(...)` call |
| 683 | `logger.error(...)` call |
| 783 | `logger.error(...)` call |
| 879 | `logger.error(...)` call |

**Recommendation:** Fix immediately. Each call has `exc_info=True` passed twice, which is a `SyntaxError`. Remove the duplicate in each case.

---

## 3. Unreferenced Modules

These modules under `src/heretek_swarm/` have zero or near-zero cross-module references (grep for `from heretek_swarm.<module>` and `import heretek_swarm.<module>`):

| Module | External References | Verdict |
|--------|--------------------|---------|
| `agent_workspace` | 0 | Candidate for archive |
| `embeddings` | 0 | Candidate for archive |
| `interfaces` | 0 | Investigate — may define public API contracts |
| `llm` | 1 | Low usage — investigate |
| `utils` | 1 | Likely utility hub; investigate before archiving |

**Recommendation:**
- `agent_workspace` and `embeddings`: Move to `.dead_code/` if no runtime or test imports exist.
- `interfaces`: Likely an API contract module. Check if it is used dynamically or re-exported. Do **not** archive without confirmation.
- `llm` and `utils`: Single-reference modules may be legitimate. Investigate the one consumer before deciding.

---

## 4. Temp Files at Root

Six Python files at the repository root are not part of the package:

| File | Size | Description | Action |
|------|------|-------------|--------|
| `temp_self_model_part1.py` | 8,852 bytes | Temp file | **Delete** |
| `generate_docker_compose.py` | 6,552 bytes | One-off generator script | **Delete** |
| `generate_prometheus_config.py` | 3,479 bytes | One-off generator script | **Delete** |
| `test_verification.py` | 1,679 bytes | Ad-hoc test | **Delete** |
| `test_full.py` | — | Ad-hoc test | **Delete** |
| `test_tool_verification.py` | — | Ad-hoc test | **Delete** |

**Recommendation:** Delete all six. They are not imported by `src/` or `tests/`.

---

## 5. Dead Functions and Classes

Found via scanning 200 exported names and counting cross-codebase references. A function/class is flagged if it has **zero** references outside its own file.

### config (4 dead symbols)

| File | Line | Symbol | Action |
|------|------|--------|--------|
| `config/encryption.py` | 163 | `get_encryptor()` | Investigate — may be public API |
| `config/loader.py` | 423 | `invalidate_all()` | Investigate — cache invalidation utility |
| `config/models.py` | 193 | `class LLMProviderTestResponse` | **Delete** — test response model |
| `config/models.py` | 280 | `class EmbeddingProviderTestResponse` | **Delete** — test response model |

### interfaces (2 dead symbols)

| File | Line | Symbol | Action |
|------|------|--------|--------|
| `interfaces/registry.py` | 59 | `register_llm_provider()` | May be dynamic registration API — **investigate** |
| `interfaces/registry.py` | 72 | `register_embedding_provider()` | May be dynamic registration API — **investigate** |

### memory (16 dead symbols)

Note: `memory/` may overlap with already-archived `.dead_code/memory/`. Verify before archiving.

| File | Line | Symbol | Action |
|------|------|--------|--------|
| `memory/access_patterns.py` | 657 | `get_hot_memories()` | Check if archiving target |
| `memory/access_patterns.py` | 661 | `get_cold_memories()` | Check if archiving target |
| `memory/access_patterns.py` | 665 | `get_frozen_memories()` | Check if archiving target |
| `memory/access_patterns.py` | 831 | `get_agent_patterns()` | Check if archiving target |
| `memory/compression.py` | 759 | `is_compressed()` | Check if archiving target |
| `memory/compression.py` | 763 | `get_compressed_entry()` | Check if archiving target |
| `memory/compression.py` | 799 | `get_compression_report()` | Check if archiving target |
| `memory/migration_strategies.py` | 163 | `class MigrationStrategy` | **Archive** — likely superseded |
| `memory/prefetcher.py` | 317 | `get_entries_by_frequency()` | Check if archiving target |
| `memory/prefetcher.py` | 325 | `get_least_recently_used()` | Check if archiving target |
| `memory/prefetcher.py` | 957 | `evict()` | Check if archiving target |
| `memory/prefetcher.py` | 997 | `get_prefetch_recommendations()` | Check if archiving target |
| `memory/tiering.py` | 990 | `get_memories_by_tier()` | Check if archiving target |
| `memory/tiering.py` | 994 | `remove_memory()` | Check if archiving target |
| `memory/tiering.py` | 1046 | `get_migration_history()` | Check if archiving target |
| `memory/tiering.py` | 1059 | `get_pending_migrations()` | Check if archiving target |
| `memory/tiering.py` | 1069 | `remove_policy()` | Check if archiving target |
| `memory/tiering.py` | 1078 | `get_policies()` | Check if archiving target |
| `memory/tiering.py` | 1082 | `get_tier_config()` | Check if archiving target |
| `memory/tiering.py` | 1086 | `update_tier_config()` | Check if archiving target |

### plugins (12 dead symbols)

| File | Line | Symbol | Action |
|------|------|--------|--------|
| `plugins/consciousness.py` | 283 | `attend_to()` | Investigate — may be plugin hook |
| `plugins/consciousness.py` | 602 | `submit_to_workspace()` | Investigate |
| `plugins/consciousness.py` | 628 | `get_workspace_contents()` | Investigate |
| `plugins/consciousness.py` | 655 | `update_agent_attention()` | Investigate |
| `plugins/consciousness.py` | 689 | `get_attention_schema()` | Investigate |
| `plugins/consciousness_metrics.py` | 243 | `calculate_fep_metrics()` | Investigate |
| `plugins/consciousness_metrics.py` | 353 | `update_temporal_metrics()` | Investigate |
| `plugins/consciousness_metrics.py` | 387 | `get_consciousness_state()` | Investigate |
| `plugins/examples.py` | 249 | `list_available_plugins()` | **Delete** — example code |
| `plugins/liberation.py` | 631 | `activate_shield()` | Investigate — may be runtime hook |
| `plugins/liberation.py` | 636 | `deactivate_shield()` | Investigate |
| `plugins/liberation.py` | 641 | `set_mode()` | Investigate |
| `plugins/manager.py` | 381 | `list_plugins()` | Investigate — may be public API |
| `plugins/manager.py` | 393 | `get_plugin_count()` | **Delete** — trivially dead |

---

## 6. Already Archived

The `.dead_code/` directory already contains:

- `.dead_code/memory/` — archived memory module
- `.dead_code/rag/` — archived RAG module

No action needed.

---

## Priority Actions

### Immediate (fix now)

1. **Fix 6 syntax errors** in `src/heretek_swarm/api/websockets.py` — duplicate `exc_info=True` kwargs
2. **Fix F811** in `src/heretek_swarm/actors/prism.py` — duplicate `AgentActor` import
3. **Delete 6 temp files** from repository root

### Short-term (next sprint)

4. **Archive `agent_workspace/` and `embeddings/`** modules to `.dead_code/` after verifying no dynamic imports
5. **Investigate `interfaces/`** before archiving — likely defines public API contracts
6. **Verify memory/ dead symbols** against `.dead_code/memory/` to avoid double-archiving
7. **Delete test response models** `LLMProviderTestResponse` and `EmbeddingProviderTestResponse` in `config/models.py`

### Medium-term (backlog)

8. **Audit plugins/ dead symbols** — many may be runtime hooks called via reflection or plugin loading
9. **Full ruff lint pass** — 9,802 issues across 243 files (majority W293 whitespace; B008 FastAPI violations: 127)
10. **Investigate `llm/` and `utils/`** single-reference modules for consolidation
