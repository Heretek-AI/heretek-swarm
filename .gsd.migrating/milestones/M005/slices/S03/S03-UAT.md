# S03: Convert surviving flat actors to thin re-exports — UAT

**Milestone:** M005
**Written:** 2026-05-12T01:13:15.739Z

# UAT: S03 — Flat actor to subpackage re-export migration

## UAT Type
Structural refactor verification — no behavioral changes, only import chain integrity.

## Preconditions
- Python virtual environment active with all dependencies installed
- Working directory: `heretek-swarm/` (repo root)

## Steps

### Step 1: Verify all agents import from public API
```python
from heretek_swarm.actors import (
    AlphaAgent, BetaAgent, CharlieAgent, StewardAgent,
    ExplorerAgent, HistorianAgent, MetisAgent, EmpathAgent, EchoAgent,
    CoderAgent, CatalystAgent, PerceiverAgent, ArbiterAgent,
    ChronosAgent, CoordinatorAgent, DreamerAgent, ExaminerAgent,
    HabitForgeAgent, NexusAgent, PerceiverPlusAgent, PrismAgent,
    SentinelAgent, SentinelPrimeAgent,
    ActorSupervisor, ActorFactory, AgentActor
)
print("All 26 public symbols import OK")
```
**Expected:** No ImportError or circular import.

### Step 2: Verify EchoActor is removed, EchoAgent is present
```python
from heretek_swarm.actors import EchoAgent  # must succeed
from heretek_swarm.actors import EchoActor  # must raise ImportError
```
**Expected:** First import succeeds, second raises ImportError.

### Step 3: Verify flat files are thin re-exports (no class definitions)
```bash
grep "^class " heretek_swarm/actors/alpha.py heretek_swarm/actors/beta.py \
  heretek_swarm/actors/charlie.py heretek_swarm/actors/steward.py \
  heretek_swarm/actors/explorer.py heretek_swarm/actors/historian.py \
  heretek_swarm/actors/metis.py heretek_swarm/actors/empath.py \
  heretek_swarm/actors/echo.py heretek_swarm/actors/coder.py \
  heretek_swarm/actors/catalyst.py heretek_swarm/actors/perceiver.py \
  heretek_swarm/actors/handoff.py heretek_swarm/actors/handoff_handlers.py
# Should produce no output
```
**Expected:** No lines printed (no class definitions found).

### Step 4: Verify arbiter/core.py is deleted
```bash
test ! -f heretek_swarm/actors/arbiter/core.py && echo "core.py removed OK"
```
**Expected:** "core.py removed OK"

### Step 5: Verify all subpackages exist
```bash
for dir in metis empath historian coder catalyst perceiver echo handoff arbiter; do
  test -d "heretek_swarm/actors/$dir" && echo "$dir: OK"
done
```
**Expected:** All 9 subpackage directories exist.

### Step 6: Run full test suite
```bash
python -m pytest tests/ -x -q
```
**Expected:** All 370 tests pass, exit code 0.

## Edge Cases
- **Legacy flat-file imports:** `from heretek_swarm.actors.historian import _HISTORIAN_FILE` still works via re-export stub for test compatibility.
- **Handoff internals:** Handoff classes remain internal (not in `actors/__init__.py`), but are importable from `heretek_swarm.actors.handoff`.
- **Import chain depth:** Flat stub → subpackage `__init__.py` → subpackage module — 3-hop chain, all using absolute imports, no circular risk.

## Not Proven By This UAT
- Agent behavioral correctness (same code, reorganized only)
- Performance characteristics of import paths
- Runtime behavior under load (pure refactor)
- Integration with external systems

