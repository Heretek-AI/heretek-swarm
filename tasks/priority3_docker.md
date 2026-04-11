# Priority 3: MEDIUM - Docker Security Issues

## Objective
Fix 4 Docker security issues (root user, file permissions).

## Files to Fix
- docker/Dockerfile (Lines 32, 50)
- dashboard/frontend/Dockerfile (Lines 20, 29)

## Issues
| File | Line | Issue | Rule |
|------|------|-------|------|
| docker/Dockerfile | 32 | Root user | docker:S6471 |
| docker/Dockerfile | 50 | File permissions | docker:S6504 |
| dashboard/frontend/Dockerfile | 20 | Recursive copy | docker:S6470 |
| dashboard/frontend/Dockerfile | 29 | Root user | docker:S6471 |

## Remediation
```dockerfile
# BEFORE
FROM python:3.11
COPY . /app

# AFTER
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
COPY --chown=appuser:appuser . /app
USER appuser
WORKDIR /app
```

## Verification
1. Containers run as non-root user
2. File permissions correctly set
3. No recursive copy issues
4. Application still functions correctly