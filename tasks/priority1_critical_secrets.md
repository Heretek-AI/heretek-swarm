# Priority 1: CRITICAL - Exposed Secrets Remediation

## Objective
Fix all 6 BLOCKER issues related to hardcoded credentials/secrets.

## Files to Fix

### 1. src/heretek_swarm/api/main.py (Line 285)
- PostgreSQL password exposed
- Replace hardcoded password with environment variable retrieval

### 2. src/memory/persistent.py (Line 87)
- PostgreSQL password exposed
- Use environment variables or secrets management

### 3. docker-compose.yml (Line 14)
- PostgreSQL password exposed
- Use environment variables with .env file pattern

### 4. scripts/run_migration.py (Line 24)
- PostgreSQL password exposed
- Use environment variables

### 5. scripts/run_migrations.py (Line 27)
- PostgreSQL password exposed
- Use environment variables

### 6. .github/workflows/ci-cd.yml (Line 133)
- PostgreSQL password exposed
- Use GitHub Secrets

## Remediation Pattern
All secrets should be retrieved from environment variables:
```python
import os
password = os.environ.get("POSTGRES_PASSWORD")
```

For Docker, use:
```yaml
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

## Verification
After fixing:
1. No hardcoded passwords should remain in source
2. All credential access should go through os.environ.get() or similar
3. Document required environment variables in .env.example