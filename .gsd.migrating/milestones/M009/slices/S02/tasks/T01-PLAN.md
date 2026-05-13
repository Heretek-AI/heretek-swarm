---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Fix Dockerfile HEALTHCHECK URL

Fix HEALTHCHECK URL in backend/Dockerfile line 68: change http://localhost:8000/health to http://localhost:8000/api/health

## Inputs

- `backend/Dockerfile`

## Expected Output

- `Dockerfile HEALTHCHECK uses correct /api/health endpoint`

## Verification

grep 'health' backend/Dockerfile | grep 'api/health'
