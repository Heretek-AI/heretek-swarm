# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? | Made By |
|---|------|-------|----------|--------|-----------|------------|---------|
| D001 |  | testing | Lifecycle smoke test structure for canonical AgentActor subclasses | Parameterized pytest-asyncio tests organized by constructor pattern (simple kwargs, explicit stubs, config-based, special constructors) | Each agent class has a unique __init__ signature. Grouping by construction pattern (simple **kwargs passthrough, explicit stub params, config-based, or special constructors) ensures each test provides exactly the right args while keeping the test file maintainable at 26 tests. | Yes | agent |
