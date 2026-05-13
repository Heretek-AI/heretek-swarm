---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Verify dashboard serves and connects

Verify the swarm dashboard at http://localhost:3000 serves correctly. If it doesn't load, check dashboard container logs and nginx config. Check that VITE_API_URL is correct (api:8000 or host-level URL). Fix any nginx proxy misconfiguration.

## Inputs

- None specified.

## Expected Output

- `Dashboard serves at localhost:3000 and connects to the API`

## Verification

curl -sf http://localhost:3000 | head -5
