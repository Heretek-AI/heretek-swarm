---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Verify live prompt → swarm response

Verify the prompt endpoint works. Send a POST to localhost:8000/v1/prompt with a test prompt. Check that the response is structured JSON containing agent deliberation output (opinions, votes, synthesis). If the LLM endpoint is unreachable, diagnose and fix (check .env OPENAI_API_KEY value, check MiniMax provider config).

## Inputs

- None specified.

## Expected Output

- `POST /v1/prompt returns 200 with JSON containing agent deliberation`

## Verification

curl -sf -X POST http://localhost:8000/v1/prompt -H 'Content-Type: application/json' -d '{"prompt":"Hello swarm"}' | python -m json.tool | head -20
