# M001: Collapse Dual `.actor_states` Directories

**Gathered:** 2025-05-07
**Status:** Planning ready

## Project Description

The Heretek Swarm repo has two `.actor_states` directories containing duplicate actor state snapshots:
- `C:/Users/Derek/Desktop/heretek-swarm/.actor_states` — 24 files (outer)
- `C:/Users/Derek/Desktop/heretek-swarm/heretek-swarm/.actor_states` — 23 files (inner)

The duplication arose because `state_management.py` uses `os.getcwd()` to resolve the state directory path. Depending on which directory a process runs from, it writes to a different location.

22 actors have state files in both locations. The outer directory consistently contains the more-recent state (timestamps ~7 hours newer) for alpha, beta, charlie, steward. The remaining 18 actors in the inner directory have no state changes between the two locations.

There is also an orphaned file `steward1.json` in the outer directory only — it has no counterpart in the inner directory and appears to be a test/leftover artifact.

## Why This Milestone

- **Correctness**: Conflicting state between two locations will cause actors to behave unpredictably on restart
- **Maintenance burden**: Developers must manually track which directory is "live"
- **Operational hazard**: Any process that changes CWD at runtime will write to the wrong location silently

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run actors from any directory and have state persist to the same location
- Know unambiguously where actor state lives on disk
- Remove the redundant directory and free ~23 duplicate files worth of storage

### Entry point / environment

- Entry point: Python code that calls `AgentActor.save_state()` / `load_state()`
- Environment: Local development, subprocess spawning
- Live dependencies involved: None — this is purely a file-system reorganization

## Completion Class

- **Contract complete** means: All state files consolidated to one canonical path, code updated to use fixed path, tests confirm persistence/readback works from canonical location
- **Integration complete** means: No other subsystems reference or depend on the dual-location behavior
- **Operational complete** means: State survives `kill -9` and restart across different working directories

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Actors started from any directory can load state persisted from the canonical location
- After consolidation, actors correctly save and load from `~/.heretek-swarm/actor_states/`
- The old duplicate directory is removed (or emptied)
- The orphaned `steward1.json` is deleted
- Running actors from different CWDs produces identical state file location

## Architectural Decisions

### State Directory Path

**Decision:** Replace `os.path.join(os.getcwd(), ".actor_states")` with a fixed absolute path `~/.heretek-swarm/actor_states/`.

**Rationale:** CWD-based paths are inherently unstable — any subprocess or code that changes directory breaks state location. A fixed path makes state location predictable regardless of where Python is invoked from. The user confirmed this approach (fixed home-directory path, not repo-root).

**Alternatives Considered:**

- Keep CWD-based path — rejected because it perpetuates the dual-location problem and makes the system fragile to CWD changes
- Configurable via `HERETEK_STATE_DIR` env var — deferred as a future enhancement; the fixed home-directory path handles 90% of use cases without config overhead
- Repo-root `.actor_states` — rejected because moving the repo would lose state and risks committing state to git

### Orphan Resolution

**Decision:** Delete `steward1.json`.

**Rationale:** It exists in only one location (outer directory) with no counterpart to compare against. It appears to be a test artifact from a process named "steward1" vs the normal "steward". The user confirmed deletion.

### State Merge Strategy

**Decision:** For actors with files in both locations, keep the more-recent timestamped file (outer directory wins for alpha, beta, charlie, steward based on diff analysis — all timestamps are ~7 hours newer in the outer directory).

**Rationale:** The outer directory consistently has newer timestamps, suggesting it was the "live" state at time of last save. Without a version field or explicit merge logic, newer timestamp is the safest heuristic.

**Alternatives Considered:**

- Keep both files with different names — rejected as it doubles storage and confuses which is canonical
- Merge by field-by-field comparison — deferred; would require understanding the schema of each actor's `internal_state`; simple timestamp selection handles the current case

### Old Directory Cleanup

**Decision:** After consolidation, the inner directory (`heretek-swarm/.actor_states`) is removed.

**Rationale:** After files are merged/consolidated, there's no reason to keep two copies. The inner directory is a subdirectory of the repo itself and is the older, stale copy.

### Migration Trigger

**Decision:** Automatic migration on first `save_state()` call (migrate-then-write pattern).

**Rationale:** Least friction for users — no manual management commands needed. On first run, if old directories exist and canonical path doesn't, copy the newer files over, then proceed with normal save.

## Error Handling Strategy

- **Missing state on first run**: If `~/.heretek-swarm/actor_states/` doesn't exist, create it (via `os.makedirs(exist_ok=True)`)
- **Corrupt JSON file**: Log error and continue as if no state found (actor starts fresh); existing code already handles this via try/except
- **Permission denied on home directory**: Fall back to CWD-based path with a warning log — do not crash the actor
- **Collision during consolidation**: If two files have identical content, keep one; if timestamps are identical but content differs, keep the larger file
- **Migration failure**: If migration of old files fails mid-way, log the failure and continue with what succeeded — don't block actor startup

## Risks and Unknowns

- **State loss**: If the user's mental model treats the repo-local copy as authoritative, consolidation could discard state they expected to be "live" — mitigated by keeping the outer (newer) files
- **Migration of in-flight actors**: If an actor process is running when consolidation happens, it may have written state to one directory while consolidation is using the other — mitigated by doing consolidation only when all actor processes are stopped
- **Backward compatibility**: Any tooling (scripts, tests) that hardcodes the old path will break — requires auditing for path references across the codebase before migration
- **Code references to old paths**: There may be other files (not `state_management.py`) that reference the old `.actor_states` path — need a codebase scan for `"actor_states"` string references

## Existing Codebase / Prior Art

- `heretek_swarm/actors/base/state_management.py` — the single file that resolves state paths via `os.getcwd()`; this is the primary code change target
- `heretek-swarm/.actor_states/` — outer directory with 24 files, including the newer state snapshots (canonical source for consolidation)
- `heretek-swarm/heretek-swarm/.actor_states/` — inner directory with 23 files, the older/stale copy to be removed

## Relevant Requirements

- No formal GSD requirements reference actor state persistence yet — this is a first-principles cleanup

## Scope

### In Scope

1. Audit all path references to `.actor_states` in the codebase (grep for `"actor_states"`)
2. Update `state_management.py` to use `~/.heretek-swarm/actor_states/` as the canonical path
3. Add automatic migration: on first `save_state()` call, copy newer files from old locations to canonical path
4. Add a warning log when falling back to CWD-based path
5. Consolidate state files: keep newer files from the outer directory
6. Delete `steward1.json`
7. Remove the inner `.actor_states` directory after consolidation
8. Add a test that verifies actors can load/save state from the canonical path and survive CWD changes

### Out of Scope / Non-Goals

- Implementing `HERETEK_STATE_DIR` env var override
- Database-backed state persistence (StateRepository already in the codebase but not wired to this fix)
- Migrating existing agents in production — this is a development-environment cleanup
- Understanding the schema of each actor's `internal_state` for field-level merging

## Technical Constraints

- The change must be backward-compatible for actors that have already written state — migration must be automatic on first run
- The code path `os.path.join(os.getcwd(), ".actor_states")` must be replaced everywhere it occurs in `state_management.py`
- The migration must not lose state — if a file exists in only one old location, it must be preserved

## Integration Points

- **StateRepository**: Already exists in the codebase with database-backed persistence — not wired as the primary path in `state_management.py`; this milestone doesn't change that but clearing up the filesystem layer is a prerequisite
- **ActorSupervisor**: Spawns actors; worth checking for path references before migration

## Testing Requirements

- Unit test: Verify `save_state()` writes to `~/.heretek-swarm/actor_states/` when called
- Integration test: Start an actor, save state, stop it, restart from a different CWD, verify state is loaded correctly
- File system: Verify the inner duplicate directory is empty (or removed) after migration
- Orphan: Verify `steward1.json` is deleted
- Migration test: Verify migration copies the correct (newer) files and doesn't duplicate data

## Acceptance Criteria

1. `state_management.py` uses `~/.heretek-swarm/actor_states/` as the canonical path
2. Actor state files (alpha, beta, charlie, steward with latest timestamps) are consolidated to the canonical location
3. `steward1.json` is deleted
4. Inner `.actor_states` directory is removed
5. A test confirms actors load state correctly after CWD changes
6. Codebase contains no remaining references to old `.actor_states` path strings
