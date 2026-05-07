# M001: Collapse dual actors/ directory into one canonical location

**Vision:** Single source of truth for all actor implementations. The flat heretek_swarm/actors/*.py files and structured heretek_swarm/heretek_swarm/actors/*/ subpackages currently coexist with overlapping names — every import is a gamble. After this milestone, one location is canonical, all imports resolve predictably, and the flat files that survive become thin re-exports from the subpackages.

## Success Criteria

- All agent classes import from a single canonical location
- No flat-file actor is a duplicate of a subpackage actor
- actors/__init__.py re-exports all public agent classes
- pytest tests/ passes with no ImportError
- No import path in the codebase references a deleted file

## Slices

- [ ] **S01: Audit actor file pairs and determine canonical source** `risk:low` `depends:[]`
  > After this: A complete map of which actor files are authoritative

- [ ] **S02: Delete obsolete actor copies and fix broken imports** `risk:medium` `depends:[S01]`
  > After this: All actor imports resolve from one canonical location

- [ ] **S03: Wire actors/__init__.py as the single re-export surface** `risk:low` `depends:[S02]`
  > After this: from heretek_swarm.actors import AlphaAgent, ArbiterAgent works

## Boundary Map

Not provided.
