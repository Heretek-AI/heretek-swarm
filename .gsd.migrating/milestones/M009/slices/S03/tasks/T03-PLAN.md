---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T03: Handle missing embedding server gracefully

Verify the system handles embedding server absence gracefully. Check that non-embedding API flows and agent deliberation complete even when embedding endpoint is unreachable. If embedding failures cause crashes, add graceful fallback handling.

## Inputs

- None specified.

## Expected Output

- `Non-embedding flows succeed when embedding server is unavailable`

## Verification

docker compose logs api | grep -i 'embedding\|embed' | tail -10
