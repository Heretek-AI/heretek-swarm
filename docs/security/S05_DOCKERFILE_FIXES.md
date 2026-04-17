# S05: Dockerfile Security Hotspot Fixes

**Date:** 2026-04-16
**Task:** T01 - Fix Dockerfile Security Hotspots (HIGH risk)
**Status:** COMPLETED

## Overview

This document records the security fixes applied to three Dockerfiles to address HIGH and MEDIUM risk SonarQube security hotspots.

## Fixes Applied

### 1. dashboard/frontend/Dockerfile

| Hotspot | Rule | Issue | Fix Applied |
|---------|------|-------|-------------|
| S6472 | ARG Used for Secret | `ARG VITE_API_KEY` could expose secrets | Removed `VITE_API_KEY` ARG - API keys should be injected via environment variables at runtime, not build arguments |
| S6471 | Root User | Container ran as root | Added non-root user (`appuser`) and `USER appuser` instruction before CMD |

**Changes:**
- Removed `ARG VITE_API_KEY` from build stage
- Added user creation: `addgroup -g 1001 -S appgroup && adduser -u 1001 -S appuser -G appgroup`
- Added `USER appuser` before the CMD instruction

### 2. docker/Dockerfile

| Hotspot | Rule | Issue | Fix Applied |
|---------|------|-------|-------------|
| S6471 | Root User | User was created but never used | Added `USER heretek` instruction before CMD/HEALTHCHECK |

**Changes:**
- Added `USER heretek` instruction after ENV variables, before HEALTHCHECK

**Note:** The Dockerfile already had:
- User creation: `RUN useradd -m -s /bin/bash -u heretek`
- Proper `--chown` on COPY instructions: `COPY --chown=heretek:heretek src/ ./src`

### 3. mem0_server/Dockerfile

| Hotspot | Rule | Issue | Status |
|---------|------|-------|--------|
| S6504 | Write Permissions | COPY instructions | Already compliant - `--chown=appuser:appuser` used on all COPY instructions |
| S6471 | Root User | Already handled | Already compliant - `USER appuser` instruction present |

**No changes required** - This Dockerfile was already following best practices.

## Security Improvements Summary

1. **Non-root Execution**: All three containers now run as non-root users, following the principle of least privilege
2. **No Secret ARGs**: Removed hardcoded secret handling via build arguments
3. **Proper Permissions**: COPY instructions use `--chown` to ensure proper ownership

## Verification Commands

```bash
# Verify USER instructions are present
grep -n 'USER' dashboard/frontend/Dockerfile docker/Dockerfile mem0_server/Dockerfile

# Verify no secret ARGs remain
grep -n 'ARG.*SECRET\|ARG.*KEY' dashboard/frontend/Dockerfile

# Build and test (optional)
docker build -t heretek-swarm:latest -f docker/Dockerfile .
docker run --rm heretek-swarm:latest id  # Should show non-root user
```

## Related Documentation

- SonarQube Security Hotspots Report: `audit_findings/security_hotspots.md`
- Docker Security Best Practices: https://docs.docker.com/develop/security-best-practices/

## Future Recommendations

1. **API Key Handling**: Consider using Docker secrets or external secret management for production deployments
2. **Image Scanning**: Run `trivy` or `snyk` container security scans in CI/CD
3. **Minimal Base Images**: Consider using distroless or scratch images for production where possible
