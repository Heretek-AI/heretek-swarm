# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? | Made By |
|---|------|-------|----------|--------|-----------|------------|---------|
| D001 |  | testing | Lifecycle smoke test structure for canonical AgentActor subclasses | Parameterized pytest-asyncio tests organized by constructor pattern (simple kwargs, explicit stubs, config-based, special constructors) | Each agent class has a unique __init__ signature. Grouping by construction pattern (simple **kwargs passthrough, explicit stub params, config-based, or special constructors) ensures each test provides exactly the right args while keeping the test file maintainable at 26 tests. | Yes | agent |
| D002 |  | documentation | Where to place actors/README.md | Create docs/actors/README.md as the practical agent creation guide | The standard docs directory already hosts architecture docs (docs/architecture/). Placing actors/README.md under docs/actors/ keeps all user-facing documentation in one place and makes it discoverable from the README. The milestone's "actors/README.md" name reflects content, not a specific filesystem location requirement. | Yes | agent |
| D003 | M008 | planning | M008 slice ordering and scope | Five-slice sequential decomposition: garbage purge (S01) → root file resolution (S02) → doc refs (S03) → code refs (S04) → validation (S05) | Garbage files are zero-dependency quick wins. Root files need code comparison before deletion (medium risk). Doc and code ref updates are mechanical but broad. Final validation gates the milestone. Risk-first ordering puts the medium-risk S02 early so findings inform S03/S04. No progressive planning needed for 5 well-understood slices. | No | agent |
| D004 | M008 | planning | No REQUIREMENTS.md — validation by convention | Validate all work against project conventions and CI green status instead of a requirements document | The project has no REQUIREMENTS.md. M008 is pure cleanup with clear success criteria (no garbage files, no stale refs, lint/test pass). Creating requirements retroactively for this milestone would be overhead with no benefit. | Yes | agent |
