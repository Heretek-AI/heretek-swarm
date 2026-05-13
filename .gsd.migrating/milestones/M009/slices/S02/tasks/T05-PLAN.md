---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T05: Bring stack up and verify health

Run docker compose up -d. Wait up to 60s for all 6 services to report healthy. Check logs of any unhealthy services. Verify curl http://localhost:8000/api/health returns 200.

## Inputs

- None specified.

## Expected Output

- `All 6 Docker containers healthy; health endpoint responds`

## Verification

curl -sf http://localhost:8000/api/health && docker compose ps --format '{{.Name}} {{.Status}}' | grep healthy
