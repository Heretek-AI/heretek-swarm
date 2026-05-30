# Phase 1.4 — Test Coverage & Quality Audit
**Date:** 2026-05-30
**Project:** Heretek-AI/heretek-swarm
**Status:** COMPLETE (structural analysis)

---

## Test Suite Overview

| Metric | Value |
|--------|-------|
| Total test files | 114 |
| Test framework | pytest |
| Test location | `tests/` |
| Frontend tests | Playwright (`swarm-dashboard/`) |

---

## Test File Inventory (partial — first 50 of 114)

| File | Test Count |
|------|-----------|
| test_auth_endpoints.py | 69 |
| test_certificate_generation.py | 53 |
| test_complexity_heuristic.py | 52 |
| test_compute_tier.py | 51 |
| test_consensus_coordinator.py | 51 |
| test_goal_consensus.py | 52 |
| test_config_cli.py | 49 |
| test_baseline_threshold.py | 44 |
| test_consensus_cli.py | 42 |
| test_full_stack.py | 35 |
| test_immune_loop.py | 33 |
| test_mcp_tool_toggle.py | 30 |
| test_nats_mtls.py | 28 |
| test_actor_lifecycle.py | 26 |
| test_cleanup_hardening.py | 26 |
| test_goal_store.py | 26 |
| test_llm_validation_wiring.py | 25 |
| test_circuit_breaker.py | 24 |
| test_heavyswarm_alternatives_real.py | 24 |
| test_cli_output.py | 23 |
| test_daemon.py | 18 |
| test_goal_proposer.py | 18 |
| test_agent_detail_endpoints.py | 17 |
| test_agent_tools.py | 16 |
| test_cost_calculation.py | 16 |
| test_consensus_runtime.py | 14 |
| test_encryption.py | 14 |
| test_event_mesh_wiring.py | 14 |
| test_auth_bypass.py | 13 |
| test_mixin_guards.py | 12 |
| test_chronos_ticks.py | 11 |
| test_execution_events.py | 11 |
| test_consciousness_metrics_stub.py | 10 |
| test_cli_help.py | 10 |
| test_heartbeat_bus.py | 10 |
| test_agent_factory.py | 9 |
| test_actor_routing.py | 7 |
| test_auth_jwt.py | 7 |
| test_deliberation_e2e.py | 7 |
| test_deliberation_flow.py | 7 |
| test_goal_cli.py | 7 |
| test_heavyswarm_analysis.py | 8 |
| test_mcp_bridge.py | 8 |
| test_auth_unit.py | 5 |
| test_historian_jsonl.py | 5 |
| test_goal_pipeline.py | 3 |
| test_goal_translator.py | 4 |
| test_packaging.py | 4 |

---

## Key Observations

### Strengths
- **Broad coverage**: 114 test files covering actors, auth, consensus, goals, CLI, encryption, NATS, workflows
- **Good test density**: Auth endpoints (69), certificates (53), consensus (51-52), compute tier (51)
- **Integration tests present**: `test_full_stack.py` (35), `test_deliberation_e2e.py` (7)
- **Security tests**: `test_auth_bypass.py`, `test_encryption.py`, `test_nats_mtls.py`

### Gaps
- **No coverage measurement tool configured** — no `.coveragerc` or `[tool.coverage]` in pyproject.toml
- **No CRAP score tracking** — complexity-risk analysis not automated
- **No mutation testing** — test quality not validated
- **Frontend tests unknown** — Playwright config exists but test count unclear
- **No test categorization** — no markers for unit/integration/e2e/slow

### Recommendations
1. Add `[tool.coverage]` to pyproject.toml with `source = ["backend/heretek_swarm"]`
2. Add pytest markers: `unit`, `integration`, `e2e`, `slow`
3. Run `pytest --cov` to establish baseline coverage
4. Add `mutmut` or `mutpy` for mutation testing
5. Add CRAP score tracking via `radon` or SonarQube
