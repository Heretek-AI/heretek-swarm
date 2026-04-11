# Priority 4: LOW - Insecure HTTP Protocol

## Objective
Fix 6 issues with insecure HTTP URLs.

## Files to Fix
| File | Line | Issue |
|------|------|-------|
| src/heretek_swarm/api/main.py | 324 | HTTP URL |
| src/heretek_swarm/observability/tracing.py | 78 | HTTP URL |
| src/heretek_swarm/runtime/autonomous_runtime.py | 266 | HTTP URL |
| k8s/configmaps.yaml | 19, 20, 41 | HTTP URLs |

## Rules
python:S5332, kubernetes:S5332

## Remediation
- Replace `http://` with `https://` where possible
- For local development, document the security implications
- Use environment variables to configure protocol based on environment

## Verification
1. Production URLs use HTTPS
2. Development URLs documented with security note
3. Environment-based protocol configuration in place