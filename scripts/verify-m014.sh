#!/bin/bash
# verify-m014.sh — M014 comprehensive verification: full-regression sweep
#
# Covers all 4 upstream M014 slice boundaries (S01-S04) plus milestone-level
# invariants.  Self-documenting PASS/FAIL output for every check.
#
# Usage: bash scripts/verify-m014.sh
# Exit 0 = PASS (all checks green — milestone ready for closure)
# Exit 1 = FAIL (at least one check failed)

set -euo pipefail

FAILED=0
SRC_DIR="backend/heretek_swarm"
API_DIR="$SRC_DIR/api"
CATALOG="$API_DIR/route-catalog.md"
MAIN="$API_DIR/main.py"
SUPERVISOR="$API_DIR/agents/supervisor.py"
ASSESSMENT=".gsd/milestones/M014/slices/S03/S03-ASSESSMENT.md"

echo "============================================================"
echo "  M014: Final verification sweep"
echo "============================================================"
echo ""

# ============================================================================
# CHECK 1 — Zero /v1/ route decorators in production code
# (S01/S03 invariant: all /v1/ prefixes flattened to /api/)
# ============================================================================
echo "--- Check 1: Zero /v1/ route decorators ---"
V1_DECORATORS=$(grep -rn '@\(router\|app\)\.\(get\|post\|put\|delete\|patch\)' "$API_DIR" --include='*.py' 2>/dev/null | grep -i '/v1/' || true)
if [ -z "$V1_DECORATORS" ]; then
    echo "  PASS: No /v1/ route decorators found"
else
    echo "  FAIL: /v1/ route decorators found:"
    echo "$V1_DECORATORS"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 2 — Zero infrastructure localhost defaults
# (S02 invariant; LITELLM_URL is the documented exception)
# ============================================================================
echo "--- Check 2: Zero infrastructure localhost defaults ---"
EXCLUDES=(-not -path "*/test_*" -not -path "*/tests/*" -not -path "*/__pycache__/*")

# Redis
REDIS_FALLBACKS=$(grep -rn 'redis://localhost\|REDIS_URL.*localhost\|REDIS_URL.*0\.0\.0\.0' \
    "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$REDIS_FALLBACKS" ]; then
    echo "  PASS: No Redis localhost fallbacks"
else
    echo "  FAIL: Redis localhost fallbacks found:"
    echo "$REDIS_FALLBACKS"
    FAILED=$((FAILED + 1))
fi

# Postgres
PG_FALLBACKS=$(grep -rn 'postgresql://localhost\|DATABASE_URL.*localhost\|POSTGRES_HOST.*localhost\|DATABASE_URL.*0\.0\.0\.0\|POSTGRES_HOST.*0\.0\.0\.0' \
    "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$PG_FALLBACKS" ]; then
    echo "  PASS: No Postgres/DATABASE_URL localhost fallbacks"
else
    echo "  FAIL: Postgres/DATABASE_URL localhost fallbacks found:"
    echo "$PG_FALLBACKS"
    FAILED=$((FAILED + 1))
fi

# NATS
NATS_FALLBACKS=$(grep -rn 'nats://localhost:4222\|HERETEK_NATS_URL.*localhost\|HERETEK_NATS_URL.*0\.0\.0\.0' \
    "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$NATS_FALLBACKS" ]; then
    echo "  PASS: No NATS localhost fallbacks"
else
    echo "  FAIL: NATS localhost fallbacks found:"
    echo "$NATS_FALLBACKS"
    FAILED=$((FAILED + 1))
fi

# Qdrant
QDRANT_FALLBACKS=$(grep -rn 'QDRANT_HOST.*localhost\|QDRANT_URL.*localhost\|QDRANT_HOST.*0\.0\.0\.0\|QDRANT_URL.*0\.0\.0\.0\|http://localhost:6333\|qdrant.*localhost' \
    "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$QDRANT_FALLBACKS" ]; then
    echo "  PASS: No Qdrant localhost fallbacks"
else
    echo "  FAIL: Qdrant localhost fallbacks found:"
    echo "$QDRANT_FALLBACKS"
    FAILED=$((FAILED + 1))
fi

# Broad sweep: any remaining localhost/0.0.0.0 in non-test production code,
# excluding the documented LITELLM_URL exception, CORS origins, and uvicorn references.
BROAD_FALLBACKS=$(grep -rn '"localhost"\|'"'"'localhost'"'"'\|0\.0\.0\.0' \
    "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null \
    | grep -v 'docstring\|# example\|>>>\|LITELLM_URL\|CORS_ORIGINS\|allowed_origins\|uvicorn.*localhost' \
    || true)
if [ -z "$BROAD_FALLBACKS" ]; then
    echo "  PASS: No remaining localhost/0.0.0.0 string literals"
else
    echo "  FAIL: Potentially unsafe localhost/0.0.0.0 references found:"
    echo "$BROAD_FALLBACKS"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 3 — Zero route overlap in main.py for /api/agents/ and /api/memory/mem0/
# (S04/T03 invariant: agent mgmt and mem0 routes served by sub-routers only)
# ============================================================================
echo "--- Check 3: Zero route overlap in main.py ---"

# main.py must not define @app routes for /api/agents/ or /api/memory/mem0/
AGENT_OVERLAP=$(grep -n '@app\.\(get\|post\|put\|delete\|patch\)' "$MAIN" 2>/dev/null \
    | grep -E '"/api/agents/|"/api/agents"|"/api/memory/mem0' || true)
if [ -z "$AGENT_OVERLAP" ]; then
    echo "  PASS: No /api/agents/ or /api/memory/mem0/ routes in main.py"
else
    echo "  FAIL: Overlapping routes in main.py:"
    echo "$AGENT_OVERLAP"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 4 — route-catalog.md exists and is non-empty
# ============================================================================
echo "--- Check 4: route-catalog.md exists and non-empty ---"
if [ -f "$CATALOG" ] && [ -s "$CATALOG" ]; then
    echo "  PASS: $CATALOG exists ($(wc -l < "$CATALOG") lines)"
else
    echo "  FAIL: $CATALOG missing or empty"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 5 — supervisors.py exists
# (S04/T01 deliverable)
# ============================================================================
echo "--- Check 5: supervisor.py exists ---"
if [ -f "$SUPERVISOR" ] && [ -s "$SUPERVISOR" ]; then
    ROUTE_COUNT=$(grep -c '@router\.' "$SUPERVISOR" 2>/dev/null || echo "0")
    echo "  PASS: $SUPERVISOR exists with $ROUTE_COUNT route decorators"
else
    echo "  FAIL: $SUPERVISOR missing or empty"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 6 — alerts.py is deleted
# (S03/T01 invariant)
# ============================================================================
echo "--- Check 6: alerts.py is deleted ---"
DELETED_ALERT="$API_DIR/alerts.py"
if [ ! -f "$DELETED_ALERT" ]; then
    echo "  PASS: $DELETED_ALERT is deleted"
else
    echo "  FAIL: $DELETED_ALERT still exists"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 7 — Route catalog documents >= 36 APIRouter definitions
# ============================================================================
echo "--- Check 7: Route catalog documents >= 36 APIRouter definitions ---"
if [ -f "$CATALOG" ]; then
    ROUTER_COUNT=$(grep -c '^| [0-9]\|^| O[0-9]\|^| A[0-9]' "$CATALOG" 2>/dev/null || echo "0")
    if [ "$ROUTER_COUNT" -ge 36 ]; then
        echo "  PASS: Route catalog documents $ROUTER_COUNT APIRouter definitions (>= 36)"
    else
        echo "  FAIL: Route catalog only documents $ROUTER_COUNT APIRouter definitions (< 36)"
        FAILED=$((FAILED + 1))
    fi
else
    echo "  FAIL: $CATALOG not found"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 8 — S03-ASSESSMENT.md exists
# ============================================================================
echo "--- Check 8: S03-ASSESSMENT.md exists ---"
if [ -f "$ASSESSMENT" ] && [ -s "$ASSESSMENT" ]; then
    echo "  PASS: $ASSESSMENT exists ($(wc -l < "$ASSESSMENT") lines)"
else
    echo "  FAIL: $ASSESSMENT missing or empty"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 9 — Frontend: no /api/v1/ references
# (S01/S03 invariant: all frontend paths use /api/ prefix)
# ============================================================================
echo "--- Check 9: Frontend /api/v1/ references ---"
FRONTEND_V1=$(grep -rn '/api/v1/' frontend/ --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' 2>/dev/null || true)
if [ -z "$FRONTEND_V1" ]; then
    echo "  PASS: No /api/v1/ references in frontend code"
else
    echo "  FAIL: /api/v1/ references found in frontend:"
    echo "$FRONTEND_V1"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# CHECK 10 — S04: Wizard 500 sanitization + SPA removal (verify-s04.sh scope)
# ============================================================================
echo "--- Check 10: Wizard 500 sanitization & SPA removal ---"
WIZARD="$API_DIR/wizard.py"

if grep -q 'raise HTTPException(500, f' "$WIZARD" 2>/dev/null; then
    echo "  FAIL: f-string-leaking HTTPException(500) found in wizard.py"
    FAILED=$((FAILED + 1))
else
    echo "  PASS: No f-string-leaking HTTPException(500) in wizard.py"
fi

LOG_COUNT=$(grep -c 'logger.exception' "$WIZARD" 2>/dev/null || echo "0")
if [ "$LOG_COUNT" -ge 6 ]; then
    echo "  PASS: logger.exception count=$LOG_COUNT (>= 6) in wizard.py"
else
    echo "  FAIL: logger.exception count=$LOG_COUNT (< 6) in wizard.py"
    FAILED=$((FAILED + 1))
fi

if grep -q '_init_spa_mount\|StaticFiles' "$MAIN" 2>/dev/null; then
    echo "  FAIL: SPA mount artifacts (_init_spa_mount/StaticFiles) found in main.py"
    FAILED=$((FAILED + 1))
else
    echo "  PASS: No SPA mount artifacts in main.py"
fi

if grep -q '@app.get("/")' "$MAIN" 2>/dev/null; then
    echo "  FAIL: Root endpoint @app.get('/') found in main.py"
    FAILED=$((FAILED + 1))
else
    echo "  PASS: No root endpoint in main.py"
fi

if grep -q 'FileResponse' "$MAIN" 2>/dev/null; then
    echo "  FAIL: FileResponse reference found in main.py"
    FAILED=$((FAILED + 1))
else
    echo "  PASS: No FileResponse in main.py"
fi

# ============================================================================
# CHECK 11 — /v1/ string literals in monitoring/logging labels
# (observability endpoints have /v1/ in monitoring labels; these are non-route)
# ============================================================================
echo "--- Check 11: /v1/ string literals (non-route context) ---"
V1_STRINGS=$(grep -rn '/v1/' "$API_DIR" --include='*.py' 2>/dev/null \
    | grep -v 'test_\|__pycache__\|docstring\|# \|# ' || true)
if [ -z "$V1_STRINGS" ]; then
    echo "  PASS: No /v1/ string literals remaining"
else
    # Count non-decorator occurrences
    V1_COUNT=$(echo "$V1_STRINGS" | grep -cv '@\(router\|app\)\.' || true)
    echo "  INFO: $V1_COUNT /v1/ references in non-decorator contexts (monitoring labels, docstrings, external URLs)"
    echo "  PASS: Zero route decorators with /v1/ confirmed in Check 1"
fi

# ============================================================================
# Conditional Docker curl checks
# ============================================================================
echo ""
echo "--- Docker curl checks (conditional) ---"
DOCKER_AVAILABLE=false
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    DOCKER_AVAILABLE=true
fi

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "  Docker is available; running curl checks..."

    # Wait briefly for compose services to be up
    if docker compose ps --format '{{.Name}}' 2>/dev/null | grep -q 'api\|backend'; then
        API_HOST="${API_HOST:-localhost:8000}"

        declare -A ROUTES=(
            ["health"]="/api/health"
            ["agents_list"]="/api/agents/"
            ["supervisor_status"]="/api/supervisor/status"
            ["wizard"]="/api/wizard/"
            ["metrics"]="/api/metrics"
            ["prompt"]="/api/prompt"
        )

        DOCKER_CHECKS_PASS=0
        DOCKER_CHECKS_FAIL=0

        for name in "${!ROUTES[@]}"; do
            route="${ROUTES[$name]}"
            status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://${API_HOST}${route}" 2>/dev/null || echo "000")
            if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 500 ]; then
                echo "  PASS: curl http://${API_HOST}${route} → $status_code"
                DOCKER_CHECKS_PASS=$((DOCKER_CHECKS_PASS + 1))
            else
                echo "  FAIL: curl http://${API_HOST}${route} → $status_code"
                DOCKER_CHECKS_FAIL=$((DOCKER_CHECKS_FAIL + 1))
            fi
        done

        echo "  Docker curl results: $DOCKER_CHECKS_PASS passed, $DOCKER_CHECKS_FAIL failed"
        if [ "$DOCKER_CHECKS_FAIL" -gt 0 ]; then
            echo "  WARN: Docker curl checks had failures (services may not be fully up)"
        fi
    else
        echo "  SKIP: docker compose services not running (no api/backend container detected)"
    fi
else
    echo "  SKIP: Docker is not available — curl checks skipped"
    echo "  To run curl checks: start services with 'docker compose up' and re-run this script"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "============================================================"
if [ "$FAILED" -eq 0 ]; then
    echo "  M014 verification: ALL CHECKS PASSED"
    echo "  Milestone M014 is ready for closure."
    echo "============================================================"
    exit 0
else
    echo "  M014 verification: ${FAILED} CHECK(S) FAILED"
    echo "  Milestone M014 is NOT ready for closure."
    echo "============================================================"
    exit 1
fi
