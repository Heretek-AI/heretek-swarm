# M005: Document architecture and compress flat actor API surface

**Vision:** The system is navigable for new contributors. After this milestone, there is a living ARCHITECTURE.md, a practical actors/README.md showing how to create an agent in under 30min, structlog config is centralized, and all flat actor files that survived M001 are thin re-exports — not implementation copies.

## Success Criteria

- ARCHITECTURE.md exists with all required sections
- actors/README.md exists with a runnable example
- logging/config.py provides the single configure_logging() entry point
- All structlog initialization in base/core.py is removed
- All flat actor files contain only re-exports

## Slices

- [ ] **S01: Write ARCHITECTURE.md and actors/README.md** `risk:low` `depends:[]`
  > After this: A new contributor can understand the system from docs

- [ ] **S02: Consolidate structlog configuration** `risk:low` `depends:[]`
  > After this: from heretek_swarm.logging.config import configure_logging

- [ ] **S03: Convert surviving flat actors to thin re-exports** `risk:low` `depends:[]`
  > After this: actors/alpha.py contains only re-exports, no implementation

## Boundary Map

Not provided.
