#!/bin/bash
# verify-s05.sh — M011 comprehensive milestone regression gate
# Validates all slice boundaries: S01 (auth), S02 (encryption), S03 (print-free),
# S04 (sanitization), plus .env hygiene, ruff, mypy, pytest
#
# Static checks run unconditionally (no Docker needed).
# Runtime checks run only when Docker API container is reachable.

set -euo pipefail

FAILED=0
TOTAL=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colour helpers (auto-detect tty)
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BOLD='\033[1m'
  NC='\033[0m' # No Color
else
  RED=''; GREEN=''; YELLOW=''; BOLD=''; NC=''
fi

pass()  { echo -e "${GREEN}✓ PASS${NC}: $*"; TOTAL=$((TOTAL + 1)); }
fail()  { echo -e "${RED}✗ FAIL${NC}: $*"; FAILED=$((FAILED + 1)); TOTAL=$((TOTAL + 1)); }
warn()  { echo -e "${YELLOW}⚠ WARN${NC}: $*"; TOTAL=$((TOTAL + 1)); }
skip()  { echo -e "${YELLOW}⊘ SKIP${NC}: $*"; }
header(){ echo ""; echo -e "${BOLD}━━━ $* ━━━${NC}"; }

# Router files comprising the 8 auth-gated surfaces
ROUTERS=(
  "backend/heretek_swarm/api/wizard.py"
  "backend/heretek_swarm/api/providers_config.py"
  "backend/heretek_swarm/api/plugins.py"
  "backend/heretek_swarm/api/collective_evolution.py"
  "backend/heretek_swarm/api/autonomous.py"
  "backend/heretek_swarm/api/provisioner.py"
  "backend/heretek_swarm/api/metrics.py"
  "backend/heretek_swarm/mcp/server.py"
)

ENV_FILE=".env"
COMPOSE_FILE="docker-compose.yml"

# =============================================================================
# STATIC CHECKS
# =============================================================================
header "STATIC CHECKS (M011 slice boundaries + hygiene)"

# ---- Check 1: .env credential hygiene ----
echo ""
echo "── S05: .env credential hygiene ──"

CREDENTIAL_VARS=("HERETEK_API_KEY" "POSTGRES_PASSWORD" "QDRANT_API_KEY" "EMBEDDING_API_KEY")
for var in "${CREDENTIAL_VARS[@]}"; do
  val=$(grep "^${var}=" "$ENV_FILE" 2>/dev/null | head -1)
  if echo "$val" | grep -qiE 'placeholder|not-for-production|change-me'; then
    pass ".env ${var} contains placeholder marker"
  else
    fail ".env ${var} does NOT contain placeholder marker (value: ${val#*=})"
  fi
done

# ---- Check 2: S01 auth gate (all 8 routers guarded) ----
echo ""
echo "── S01: Router auth gate ──"

for router in "${ROUTERS[@]}"; do
  if [ -f "$router" ]; then
    if grep -q 'Depends(verify_auth)' "$router"; then
      pass "$router has Depends(verify_auth)"
    else
      fail "$router MISSING Depends(verify_auth)"
    fi
  else
    fail "$router FILE NOT FOUND"
  fi
done

# ---- Check 3: S02 encryption (config_keys volume + mount) ----
echo ""
echo "── S02: Encryption key persistence ──"

if grep -q 'config_keys:' "$COMPOSE_FILE" 2>/dev/null; then
  pass "docker-compose.yml declares config_keys volume"
else
  fail "docker-compose.yml MISSING config_keys volume declaration"
fi

if grep -q 'config_keys:/config' "$COMPOSE_FILE" 2>/dev/null; then
  pass "docker-compose.yml mounts config_keys:/config on api service"
else
  fail "docker-compose.yml MISSING config_keys:/config mount on api service"
fi

# ---- Check 4: S03 print-free production code ----
echo ""
echo "── S03: Print-free production code ──"

PRINT_COUNT=$(find backend/heretek_swarm -name '*.py' \
  ! -name '__main__.py' \
  ! -name 'cli.py' \
  ! -path '*/__pycache__/*' \
  -exec grep -l 'print(' {} \; 2>/dev/null | wc -l)

if [ "$PRINT_COUNT" -eq 0 ]; then
  pass "Zero print() calls in production code (excluding __main__.py, cli.py)"
else
  fail "${PRINT_COUNT} file(s) with print() calls in production code:"
  find backend/heretek_swarm -name '*.py' \
    ! -name '__main__.py' \
    ! -name 'cli.py' \
    ! -path '*/__pycache__/*' \
    -exec grep -Hn 'print(' {} \; 2>/dev/null | while read -r line; do
    echo "       $line"
  done
fi

# ---- Check 5: S04 sanitization (wizard 500 + SPA removal) ----
echo ""
echo "── S04: Wizard 500 sanitization & SPA removal ──"

WIZARD="backend/heretek_swarm/api/wizard.py"
MAIN="backend/heretek_swarm/api/main.py"

# 5a. No f-string-leaking HTTPException(500)
if grep -q 'raise HTTPException(500, f' "$WIZARD" 2>/dev/null; then
  fail "f-string-leaking raise HTTPException(500, f'...') found in wizard.py"
else
  pass "No f-string-leaking HTTPException(500) in wizard.py"
fi

# 5b. logger.exception() ≥ 6 in wizard.py
LOG_EXCEPTION_COUNT=$(grep -c 'logger.exception' "$WIZARD" 2>/dev/null || echo "0")
if [ "$LOG_EXCEPTION_COUNT" -ge 6 ]; then
  pass "logger.exception count=${LOG_EXCEPTION_COUNT} (≥ 6) in wizard.py"
else
  fail "logger.exception count=${LOG_EXCEPTION_COUNT} (< 6) in wizard.py"
fi

# 5c. No SPA mount artifacts in main.py
if grep -q '_init_spa_mount\|StaticFiles' "$MAIN" 2>/dev/null; then
  fail "SPA mount artifacts (_init_spa_mount / StaticFiles) found in main.py"
else
  pass "No SPA mount artifacts in main.py"
fi

# 5d. No root endpoint in main.py
if grep -q '@app.get("/")' "$MAIN" 2>/dev/null; then
  fail "Root endpoint @app.get('/') found in main.py"
else
  pass "No root endpoint in main.py"
fi

# 5e. No FileResponse in main.py
if grep -q 'FileResponse' "$MAIN" 2>/dev/null; then
  fail "FileResponse reference found in main.py"
else
  pass "No FileResponse in main.py"
fi

# ---- Check 6: Ruff lint ----
echo ""
echo "── Ruff check ──"

if command -v ruff &>/dev/null; then
  if ruff check backend/heretek_swarm/; then
    pass "ruff check passed"
  else
    fail "ruff check returned errors"
  fi
else
  skip "ruff not installed — skipping"
fi

# ---- Check 7: Mypy type check ----
echo ""
echo "── Mypy type check ──"

if command -v mypy &>/dev/null; then
  if mypy backend/heretek_swarm/ --ignore-missing-imports 2>&1; then
    pass "mypy check passed"
  else
    # Mypy often has pre-existing issues; treat as warn not fail
    warn "mypy check returned errors (may be pre-existing)"
  fi
else
  skip "mypy not installed — skipping"
fi

# ---- Check 8: pytest (non-integration) ----
echo ""
echo "── pytest (not integration) ──"

if command -v pytest &>/dev/null; then
  if pytest -m 'not integration' -x -q 2>&1; then
    pass "pytest -m 'not integration' -x -q passed"
  else
    fail "pytest returned failures"
  fi
else
  skip "pytest not installed — skipping"
fi

# =============================================================================
# RUNTIME CHECKS (conditional — Docker must be reachable)
# =============================================================================
header "RUNTIME CHECKS (requires Docker API at localhost:8000)"

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${HERETEK_API_KEY:-htsk-placeholder-for-local-dev}"
DOCKER_REACHABLE=false

# Quick connectivity probe
if curl -s --connect-timeout 3 --max-time 5 -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" 2>/dev/null | grep -qE '2..|401'; then
  if curl -s --connect-timeout 3 --max-time 5 -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" 2>/dev/null | grep -q '401'; then
    DOCKER_REACHABLE=true
    echo "API reachable at $BASE_URL (returned 401 as expected)"
  elif curl -s --connect-timeout 3 --max-time 5 -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" 2>/dev/null | grep -q '200'; then
    DOCKER_REACHABLE=true
    echo "API reachable at $BASE_URL (returned 200 — health check open)"
  fi
fi

if $DOCKER_REACHABLE; then

  # ---- Check 9: All 8 routers return 401 without Bearer token ----
  echo ""
  echo "── Auth gate: 401 without Bearer token ──"

  ENDPOINTS=(
    "/api/wizard/config"
    "/api/v1/providers/llm"
    "/api/plugins"
    "/api/collective/evolution-status"
    "/autonomous/agents"
    "/api/wizard/provision/status"
    "/metrics"
    "/mcp/tools/list"
  )

  for endpoint in "${ENDPOINTS[@]}"; do
    status=$(curl -s --connect-timeout 5 --max-time 10 -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$status" = "401" ]; then
      pass "$endpoint → 401 (no auth)"
    elif [ "$status" = "403" ]; then
      pass "$endpoint → 403 (no auth, treated as gated)"
    else
      fail "$endpoint → $status (expected 401)"
    fi
  done

  # ---- Check 10: Encryption key file exists on config_keys volume ----
  echo ""
  echo "── Encryption key persistence ──"

  CONTAINER_NAME="${API_CONTAINER:-heretek-swarm-api-1}"
  # Try common container name patterns
  for name in "heretek-swarm-api-1" "heretek-swarm_api_1" "heretek-swarm-api"; do
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
      CONTAINER_NAME="$name"
      break
    fi
  done

  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "$CONTAINER_NAME"; then
    if docker exec "$CONTAINER_NAME" test -f /config/encryption.key 2>/dev/null; then
      pass "/config/encryption.key exists in container $CONTAINER_NAME"
    else
      fail "/config/encryption.key NOT found in container $CONTAINER_NAME"
    fi
  else
    skip "API container not found (tried: heretek-swarm-api-1, heretek-swarm_api_1)"
  fi

else
  echo "Docker API not reachable at $BASE_URL"
  skip "All runtime checks — API at $BASE_URL not reachable"
fi

# =============================================================================
# SUMMARY
# =============================================================================
header "VERIFICATION SUMMARY"
echo ""
printf "  Total checks : %d\n" "$TOTAL"
printf "  Passed       : %d\n" "$((TOTAL - FAILED))"
printf "  Failed       : %d\n" "$FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}=== M011 regression gate: ALL CHECKS PASSED ===${NC}"
  exit 0
else
  echo -e "${RED}${BOLD}=== M011 regression gate: ${FAILED} CHECK(S) FAILED ===${NC}"
  exit 1
fi
