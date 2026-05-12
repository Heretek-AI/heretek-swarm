# M007: Execute repository restructure

**Vision:** Rename the inner Python package directory from heretek-swarm/ to backend/, update all imports, fix CI paths, and verify everything works cleanly. The swarm-dashboard/ frontend is already correctly separated.

## Success Criteria

- heretek-swarm/ renamed to backend/ via git mv
- All Python imports updated
- All CI workflows updated
- Full test suite passes
- Git history preserved

## Slices

- [x] **S01: S01** `risk:medium` `depends:[]`
  > After this: Repo at new path with no code changes; only directory moves via git mv.

- [x] **S02: S02** `risk:medium` `depends:[]`
  > After this: All Python imports use the new backend/ path; CI passes.

- [ ] **S03: S03** `risk:low` `depends:[]`
  > After this: Fresh clone of the repo works perfectly at new paths.

## Boundary Map

```
heretek-swarm/                        ← repo root (unchanged)
├── backend/                          ← heretek-swarm/ renamed
│   └── heretek_swarm/              ← Python package (unchanged)
├── swarm-dashboard/                  ← already clean
├── docs/                             ← already clean
├── agent_workspace/                  ← already clean
└── .github/workflows/               ← needs path updates for backend/
```
