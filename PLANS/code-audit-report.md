# Code Audit Report

**Date:** 2026-04-13
**Scope:** Python (src/) and TypeScript (dashboard/frontend/src/)

---

## 1. Unused Imports (Python)

### Fixable with `ruff --fix` (7 issues)

| File | Line | Issue |
|------|------|-------|
| `src/heretek_swarm/api/autonomous.py` | 16 | `fastapi.HTTPException` imported but unused |
| `src/heretek_swarm/api/autonomous.py` | 17 | `pydantic.Field` imported but unused |
| `src/heretek_swarm/config/service.py` | 22 | `.db_models.ConfigAuditLog` imported but unused |
| `src/heretek_swarm/config/service.py` | 23 | `.db_models.ConfigCache` imported but unused |
| `src/heretek_swarm/state/models.py` | 10 | `asyncio` imported but unused |
| `src/heretek_swarm/state/models.py` | 13 | `collections.abc.Callable` imported but unused |
| `tests/mcp/test_client.py` | 10 | `heretek_swarm.mcp.registry.ToolProviderType` imported but unused |

### Require Manual Removal (47 issues)

| File | Line | Description |
|------|------|-------------|
| `src/heretek_swarm/api/websockets.py` | 1152 | Local variable `message` assigned but never used |
| `src/heretek_swarm/collective/society.py` | 29-33 | 5 imports from `.swarm_intelligence` unused (BeeAgent, FlockingAgent, Particle, PheromoneTrail, StigmergicTrace) |
| `src/heretek_swarm/consciousness/__init__.py` | 38-43 | 6 imports from `phi_training` unused (PhiTrainingEnvironment, ScenarioType, TrainingEpisode, TrainingMode, TrainingResult, TrainingScenario) |
| `src/heretek_swarm/infrastructure/otel/tracing.py` | 209 | Local variable `tracer` assigned but never used |
| `src/heretek_swarm/integrations/__init__.py` | 134 | 4 Discord imports unused (DiscordBot, get_discord_bot, start_discord_bot, stop_discord_bot) |
| `src/heretek_swarm/integrations/__init__.py` | 140 | 4 Slack imports unused (SlackBot, get_slack_bot, start_slack_bot, stop_slack_bot) |
| `src/heretek_swarm/integrations/__init__.py` | 146 | 4 Telegram imports unused (TelegramBot, get_telegram_bot, start_telegram_bot, stop_telegram_bot) |
| `src/heretek_swarm/integrations/__init__.py` | 153-157 | 5 Praison handoff imports unused |
| `src/heretek_swarm/memory/__init__.py` | 69 | `MemoryTier` redefined (unused redefinition) |
| `src/heretek_swarm/observability/__init__.py` | 26-37 | 10 imports unused (uuid, dataclasses.field, datetime.timezone, enum.Enum, typing.Dict/List/Optional, prometheus_client.CollectorRegistry, tracing.get_tracer) |
| `src/heretek_swarm/observability/metrics.py` | 24 | `export_cycle_detector_prometheus` imported but unused |
| `src/heretek_swarm/runtime/__init__.py` | 12-17 | 4 typing imports unused + AutonomousRuntime, RuntimeState |
| `src/heretek_swarm/security/ddos_protection.py` | 334 | `redis.asyncio` imported but unused |

---

## 2. Console.log Statements (TypeScript)

**Total: 10 instances** - All should be removed or replaced with proper logging

| File | Line | Code |
|------|------|------|
| `dashboard/frontend/src/components/Dashboard/Dashboard.tsx` | 149 | `console.log('Dashboard WebSocket connected')` |
| `dashboard/frontend/src/components/Dashboard/Dashboard.tsx` | 211 | `console.log('Dashboard WebSocket disconnected')` |
| `dashboard/frontend/src/components/WorkflowBuilder/AgentNode.tsx` | 98 | `console.log('Handle clicked:', handleId)` |
| `dashboard/frontend/src/hooks/useRealTimeAgentUpdates.ts` | 299 | `console.log('Real-time updates connected')` |
| `dashboard/frontend/src/hooks/useRealTimeAgentUpdates.ts` | 314 | `console.log('Real-time updates disconnected')` |
| `dashboard/frontend/src/hooks/useWebSocket.ts` | 58 | `console.log('WebSocket connected to ${channel}')` |
| `dashboard/frontend/src/hooks/useWebSocket.ts` | 64 | `console.log('WebSocket disconnected from ${channel}')` |
| `dashboard/frontend/src/hooks/useWebSocket.ts` | 69 | `console.log('Reconnecting... attempt ${reconnectAttempts.current}')` |
| `dashboard/frontend/src/hooks/useDockerDetection.tsx` | 169 | `console.log('Starting services via Electron...')` |
| `dashboard/frontend/src/hooks/useDockerDetection.tsx` | 171, 178, 180 | Additional console.log statements |

---

## 3. Empty pass Statements

**Total: 21 instances** - These may indicate incomplete code or intentional no-ops

| File | Lines |
|------|-------|
| `src/heretek_swarm/observability/metrics.py` | 682, 687, 692 |
| `src/heretek_swarm/state/event_store.py` | 496 |
| `src/heretek_swarm/state/models.py` | 429, 433, 535, 539 |
| `src/heretek_swarm/api/websockets.py` | 388, 511, 536, 555, 604, 682, 782, 878, 965, 1062, 1137 |
| `src/heretek_swarm/runtime/scaling.py` | 972 |

---

## 4. Logging Style Issues (Python)

**Many instances** - Ruff G004 (f-string in logging) and G201 (.error with exc_info instead of .exception)

### Key Patterns:
- `G004`: Logging statement uses f-string instead of lazy string formatting
- `G201`: Use `.exception(...)` instead of `.error(..., exc_info=True)`

**Files with most issues:**
- `src/heretek_swarm/actors/arbiter.py` - 20+ instances
- `src/heretek_swarm/actors/base.py` - 40+ instances
- `src/heretek_swarm/actors/alpha.py` - 10+ instances

---

## 5. Redundant Code Patterns

### Python

| Pattern | Location | Issue |
|---------|----------|-------|
| Redefinition of unused import | `src/heretek_swarm/memory/__init__.py:69` | `MemoryTier` redefined on line 33 and 69 |
| Conditional imports (importlib.util.find_spec) | `src/heretek_swarm/integrations/__init__.py:134+` | Bot integrations always imported even when optional |
| Nested if statements | `src/heretek_swarm/actors/arbiter.py:1651` | SIM102: Use single if instead of nested |

### TypeScript

| Pattern | Location | Issue |
|---------|----------|-------|
| Multiple Canvas components | `Canvas/Canvas.tsx` (150 lines) vs `FlowCanvas.tsx` (641 lines) vs `EnhancedCanvas.tsx` (706 lines) | Three different canvas implementations - potential consolidation needed |
| Canvas component naming | `App.tsx:25` imports `CollectiveCanvas` from `Canvas.tsx` but index exports `FlowCanvas` from `FlowCanvas.tsx` | Confusing naming and export structure |

---

## 6. TypeScript Type Definitions

### No significant duplicate type definitions found

The type definitions in `WorkflowBuilder/types.ts` and `Consciousness/types.ts` are well-separated by domain. However, both contain large enums that define agent types - verify they stay in sync if agents are added.

---

## 7. Suggested Fixes (Priority Order)

### HIGH Priority (Fix Now)

1. **Remove console.log statements** - Security risk, clutters production logs
   ```bash
   # Interactive search-replace needed
   # Consider using @types/logger or pino for proper logging
   ```

2. **Fix unused imports in `src/heretek_swarm/consciousness/__init__.py`** - Lines 38-43
   - These are substantial unused imports blocking cleanup

3. **Fix unused imports in `src/heretek_swarm/integrations/__init__.py`** - Lines 134-157
   - 13+ unused imports from optional integrations

### MEDIUM Priority (Fix Soon)

4. **Fix unused imports in `src/heretek_swarm/observability/__init__.py`** - Lines 26-37
   - 10 unused imports

5. **Fix `src/heretek_swarm/memory/__init__.py:69`** - Remove duplicate `MemoryTier` definition

6. **Address `pass` statements** - Review each to determine if intentional no-op or incomplete code

### LOW Priority (Nice to Have)

7. **Standardize logging** - Replace f-strings with lazy formatting and .error(..., exc_info=True) with .exception()

8. **Canvas component consolidation** - Consider merging Canvas.tsx, FlowCanvas.tsx, EnhancedCanvas.tsx into a single component with feature flags

---

## Verification Commands

```bash
# Python unused imports
ruff check src tests --select=F401,F811,F841 --output-format=concise

# TypeScript errors
cd dashboard/frontend && npx tsc --noEmit

# Console.log count
grep -rn "console\.log" dashboard/frontend/src/

# pass statement count
grep -rn "pass" src/ | wc -l
```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Unused Python imports | 54 |
| Console.log statements | 10 |
| Empty pass statements | 21 |
| Line-length violations (E501) | 30+ |
| Logging style issues (G004/G201) | 150+ |
