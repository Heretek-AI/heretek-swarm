---
id: T01
parent: S02
milestone: M003
key_files:
  - (none)
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-08T00:16:37.289Z
blocker_discovered: false
---

# T01: Add 6 protocol stub classes (StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh) to stubs.py with minimal in-memory implementations, plus legacy backward-compat functions.

**Add 6 protocol stub classes (StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh) to stubs.py with minimal in-memory implementations, plus legacy backward-compat functions.**

## What Happened

Implemented the 6 protocol stub classes in `heretek_swarm/actors/stubs.py` that the injectable dependency system will use:

- **StubAccessAnalyzer** — records accesses in-memory dict, returns `_StubAccessProfile` and `_StubAccessStatistics` stand-ins. Implements `record_access`, `get_profile`, `predict_agent_access`, `get_statistics`.
- **StubPatternExtractor** — caches `_StubMessageAnalysis` objects, stores validated `_StubExtractedPattern`s. Async `analyze_message` and `extract_patterns` methods. Exposes `_message_cache` and `_validated_patterns` dicts expected by LearningMixin/PatternMixin.
- **StubTribunal** — in-memory case/evidence/ruling store. Implements `create_case`, `submit_evidence`, `get_case`, `issue_ruling`, `get_precedents`, `find_similar_precedents` with `_StubTribunalCase`/`_StubTribunalEvidence`/`_StubTribunalRuling` data containers.
- **StubDeliberationEngine** — in-memory deliberation state with `start_deliberation`, `submit_position`, `submit_argument`, `run_deliberation_round`, `get_statistics`. Uses `_StubDeliberationRound` data container.
- **StubLLMProvider** — canned-response provider that returns a pre-configured string for `generate`, `generate_stream`, or synchronous `__call__`. Tracks `call_count`.
- **StubEventMesh** — in-memory event bus with `connect`, `disconnect`, `publish`, `subscribe`, `request`. Stores published messages and subscriptions for test inspection.

Also preserved and updated legacy module-level functions `get_nats_event_mesh()` and `get_llm_provider()` for backward compatibility with existing code that imports them from this module.

## Verification

Import verification passed: all 6 stub classes import successfully from `heretek_swarm.actors.stubs`. Each class was also instantiated and its key methods exercised in prior session verification runs.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -c "from heretek_swarm.actors.stubs import StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh; print('OK')"` | 0 | ✅ pass | 1500ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

None.
