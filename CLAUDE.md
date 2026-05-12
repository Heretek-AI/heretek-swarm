# CLAUDE.md

This file provides guidance to Claw Code (clawcode.dev) when working with code in this repository.

## Detected stack
- Languages: Python, TypeScript.
- Frameworks/tooling markers: React, Vite.

## Verification
- Run the Python project checks from `pyproject.toml`: `cd backend && pytest` for tests, `ruff check heretek_swarm tests` for linting, and `mypy heretek_swarm` for type checking.
- Run the JavaScript/TypeScript checks from `package.json` before shipping changes (`npm test`, `npm run lint`, `npm run build`, or the repo equivalent).
- `backend/heretek_swarm/` contains source files; `tests/` contains validation surfaces; update both together when behavior changes.

## Repository shape
- `backend/heretek_swarm/` contains source files that should stay consistent with generated guidance and tests.
- `tests/` contains validation surfaces that should be reviewed alongside code changes.

## Framework notes
- React detected: keep component behavior covered with focused tests and avoid unnecessary prop/API churn.
- Vite detected: validate the production bundle after changing build-sensitive configuration or imports.

## Working agreement
- Prefer small, reviewable changes and keep generated bootstrap files aligned with actual repo workflows.
- Keep shared defaults in `.claw.json`; reserve `.claw/settings.local.json` for machine-local overrides.
- Do not overwrite existing `CLAUDE.md` content automatically; update it intentionally when repo workflows change.
