# M006: Audit and plan repository restructure

**Vision:** Map every file in the repo, document what belongs where in the new structure, and produce an actionable migration plan so M007 can execute cleanly.

## Success Criteria

- Full file inventory (PLAN.md)
- Import dependency map (PLAN.md)
- CI/workflow impact list (PLAN.md)

## Slices

- [ ] **S01: Audit file inventory and plan** `risk:low` `depends:[]`
  > After this: After this: a written plan with exact file moves, import rewrites, and CI fixes ready to execute.

## Boundary Map

```\ncurrent: heretek-swarm/heretek-swarm/heretek_swarm/{actors,schemas,validation,...}\ntarget: backend/heretek_swarm/{actors,schemas,validation,...}\n```
