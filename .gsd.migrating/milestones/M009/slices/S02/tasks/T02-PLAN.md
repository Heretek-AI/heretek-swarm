---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Fix docker-compose.yml HEALTHCHECK URL

Fix HEALTHCHECK URL in docker-compose.yml line 111: change http://localhost:8000/health to http://localhost:8000/api/health

## Inputs

- `docker-compose.yml`

## Expected Output

- `docker-compose.yml api healthcheck uses correct /api/health endpoint`

## Verification

grep 'health' docker-compose.yml | grep 'api/health'
