---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T01: Create .env from .env.example

Copy .env.example to .env. Fill in required values (OPENAI_API_KEY, etc.) using secure_env_collect for the API key. Verify .env is parseable by docker compose config.

## Inputs

- `.env.example`

## Expected Output

- `.env file exists with all required values filled in`

## Verification

cat .env | grep -v '^#' | grep -v '^$' | wc -l > 10
