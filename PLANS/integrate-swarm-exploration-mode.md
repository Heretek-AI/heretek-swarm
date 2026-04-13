# Plan: Integrate Swarm Exploration Layer into society.py

## Context

**Goal:** Add `exploration_mode` flag to `AgentSociety` that activates emergent swarm behavior (BeeAgent, FlockingAgent) as a background exploration layer, without compromising hierarchical TRIAD authority.

**Key insight from code analysis:**
- `society.py` already imports `BeeAgent`, `FlockingAgent`, `Particle`, `PheromoneTrail`, `StigmergicTrace`, `SwarmDecision`, `SwarmIntelligenceEngine`, `SwarmPattern` from `swarm_intelligence.py`
- `AgentSociety.__init__` already accepts `enable_swarm_intelligence: bool = True` and initializes `SwarmIntelligenceEngine()`
- `apply_swarm_pattern` already wires 5 patterns ("pso", "ant_colony", "bee_algorithm", "flocking", "stigmergy") to engine methods
- `run_collective_optimization` already calls `apply_swarm_pattern`
- **Gap:** `coordinated_task` follows the fixed TRIAD flow and never activates swarm intelligence. There is no `exploration_mode`.

---

## Phase 1: Add exploration_mode flag and ExplorationTaskType

**Files:** `society.py`

### 1.1 Add `EXPLORATION = "exploration"` to `CollectiveTaskType` enum (L128)
```python
EXPLORATION = "exploration"
```
Purpose: Enables callers to dispatch tasks explicitly routed to the exploration layer.

### 1.2 Add `exploration_mode: bool = False` parameter to `AgentSociety.__init__` (L298)
```python
def __init__(
    self,
    supervisor=None,
    contribution_cache_ttl: int = 300,
    enable_swarm_intelligence: bool = True,
    exploration_mode: bool = False,   # NEW
):
```
Store and log it:
```python
self.exploration_mode = exploration_mode
if exploration_mode:
    logger.info("exploration_mode_enabled")
```

### 1.3 Add `_exploration_engine: SwarmIntelligenceEngine | None` field (L306)
```python
self._exploration_engine: SwarmIntelligenceEngine | None = None
if exploration_mode and SWARM_INTELLIGENCE_AVAILABLE:
    self._exploration_engine = SwarmIntelligenceEngine()
    logger.info("exploration_engine_initialized")
```

### 1.4 Add `exploration_task_types` set in `__init__`
```python
self._exploration_task_types = {
    CollectiveTaskType.EXPLORATION,
    CollectiveTaskType.OPTIMIZATION,
}
```

---

## Phase 2: Wire exploration_mode into coordinate_task

**Files:** `society.py`

### 2.1 Modify `coordinate_task` to route EXPLORATION tasks to swarm engine (L362)

In `coordinate_task`, after participant selection and before `_execute_coordination`, add:

```python
# Route to swarm exploration layer if exploration_mode and task type matches
if self.exploration_mode and task.type in self._exploration_task_types:
    if self._exploration_engine:
        return await self._execute_swarm_exploration(task, participants)
```

### 2.2 Add `_execute_swarm_exploration` private method (after `_build_hierarchy`)

```python
async def _execute_swarm_exploration(
    self,
    task: CollectiveTask,
    participants: list[str],
) -> CollectiveResult:
    """
    Execute task via swarm exploration layer.

    Activates BeeAgent / FlockingAgent emergent behavior under hierarchy authority.
    The swarm explores but hierarchy retains final decision veto.
    """
    start_time = datetime.now(UTC)

    # Convert task input_data to decision_space
    decision_space = {
        str(k): float(v) if isinstance(v, (int, float)) else 0.0
        for k, v in task.input_data.items()
    }

    # Determine which swarm algorithm to use based on task type
    pattern_map = {
        CollectiveTaskType.EXPLORATION: "bee_algorithm",
        CollectiveTaskType.OPTIMIZATION: "pso",
    }
    pattern = pattern_map.get(task.type, "bee_algorithm")

    logger.info(
        "exploration_layer_invoked",
        task_id=task.id,
        pattern=pattern,
        participants=len(participants),
    )

    try:
        result = await self.apply_swarm_pattern(
            pattern=pattern,
            participants=participants,
            decision_space=decision_space,
            max_iterations=50,
        )

        if result is None:
            # Swarm returned None — fall back to TRIAD hierarchy
            logger.warning("swarm_exploration_fell_back_to_hierarchy")
            return await self._execute_coordination_fallback(task, participants)

        execution_time = (datetime.now(UTC) - start_time).total_seconds()

        return CollectiveResult(
            task_id=task.id,
            success=True,
            result=result,
            participants=participants,
            execution_time=execution_time,
            consensus_score=result.get("confidence", 0.0),
            emergent_behavior=result.get("emergence_detected", False),
        )

    except Exception as e:
        logger.exception("exploration_layer_failed", task_id=task.id)
        return await self._execute_coordination_fallback(task, participants)
```

### 2.3 Add `_execute_coordination_fallback` private method

```python
async def _execute_coordination_fallback(
    self,
    task: CollectiveTask,
    participants: list[str],
) -> CollectiveResult:
    """Fall back to standard TRIAD hierarchy when swarm is unavailable."""
    protocol = self._establish_protocol(participants, task)
    return await self._execute_coordination(participants, protocol, task)
```

---

## Phase 3: Expose exploration mode via public API

**Files:** `society.py`

### 3.1 Add `set_exploration_mode` method

```python
def set_exploration_mode(self, enabled: bool) -> None:
    """
    Enable or disable exploration mode at runtime.

    When enabled, EXPLORATION and OPTIMIZATION tasks are routed to the
    swarm exploration layer while retaining hierarchy authority.
    """
    self.exploration_mode = enabled
    logger.info("exploration_mode_updated", enabled=enabled)
```

### 3.2 Update `get_society_status` to include exploration_mode

In `get_society_status` (L1178), add:
```python
"exploration_mode": self.exploration_mode,
```

### 3.3 Update `get_swarm_status` to expose exploration engine

In `get_swarm_status` (L1066), add:
```python
"exploration_mode_active": self.exploration_mode,
"exploration_engine_available": self._exploration_engine is not None,
```

---

## Phase 4: Validation and testing

### 4.1 Unit tests
- `test_exploration_mode_flag`: verify `exploration_mode` stored correctly
- `test_exploration_task_routed_to_swarm`: dispatch `CollectiveTaskType.EXPLORATION` and verify `apply_swarm_pattern` called
- `test_fallback_when_swarm_unavailable`: with `swarm_engine=None`, verify TRIAD fallback
- `test_set_exploration_mode_runtime`: toggle exploration mode and confirm state change

### 4.2 Integration checks
- `pytest tests/` — verify no regressions in existing swarm intelligence tests
- `ruff check src tests` — lint
- `mypy src` — type check

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/heretek_swarm/collective/society.py` | +3 enum value, +2 `__init__` params, +2 private methods, +1 public method, status method updates |

**No changes needed to:** `swarm_intelligence.py` — BeeAgent and FlockingAgent remain encapsulated behind `SwarmIntelligenceEngine`.

---

## Key Design Decisions

1. **Hierarchy authority preserved**: The swarm explores but `coordinate_task` still calls `_establish_protocol` and `_execute_coordination` on the fallback path. The hierarchy never loses veto power.

2. **Opt-in only**: `exploration_mode=False` by default. Existing behavior is unchanged unless explicitly enabled.

3. **FlockingAgent / BeeAgent stay internal**: They are used internally by `SwarmIntelligenceEngine.run_bee_algorithm` and `run_flocking`. No direct exposure to the caller. This avoids API coupling.

4. **Failure fallback**: If the swarm layer throws or returns None, execution falls back to the TRIAD coordination path — zero disruption to existing flows.

5. **Runtime toggle**: `set_exploration_mode` allows enabling/disabling at runtime without re-initializing the society.

6. **PRIME_DIRECTIVE alignment**: The Lobster Philosophy ("thinks without prompting") is honored by activating background exploration; Zero-Trust and hierarchy authority are honored by the mandatory fallback path.

---

## Estimated Effort

| Phase | Complexity | Notes |
|-------|-----------|-------|
| Phase 1 | Low | Enum value + 2 init params |
| Phase 2 | Medium | Core routing logic + fallback |
| Phase 3 | Low | 3 minor additions |
| Phase 4 | Low | 4 unit tests |
| **Total** | **~3-4 hours** | |
