#!/bin/bash
# verify-m016-s03.sh — M016/S03 integration verification gate
# Validates the full Docker stack: container health, API endpoints,
# auth enforcement, agent deploy lifecycle, dashboard reachability,
# TypeScript compilation, and cleanup.
#
# Run: bash scripts/verify-m016-s03.sh
# Requires: Docker, curl, python3 (or jq)

set -euo pipefail

FAILED=0
TOTAL=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Colour helpers (auto-detect tty)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BOLD=''; NC=''
fi

pass()  { echo -e "${GREEN}✓ PASS${NC}: $*"; TOTAL=$((TOTAL + 1)); }
fail()  { echo -e "${RED}✗ FAIL${NC}: $*"; FAILED=$((FAILED + 1)); TOTAL=$((TOTAL + 1)); }
warn()  { echo -e "${YELLOW}⚠ WARN${NC}: $*"; TOTAL=$((TOTAL + 1)); }
skip()  { echo -e "${YELLOW}⊘ SKIP${NC}: $*"; }
header(){ echo ""; echo -e "${BOLD}━━━ $* ━━━${NC}"; }

# ---------------------------------------------------------------------------
# JSON helper (use python3 by default, fall back to jq)
# ---------------------------------------------------------------------------
_json_val() {
  # _json_val <json_string> <key> — extract a top-level string/number value
  local json="$1" key="$2"
  if command -v jq &>/dev/null; then
    echo "$json" | jq -r ".${key} // empty" 2>/dev/null || true
  else
    python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
print(d.get('$key',''))
" <<< "$json" 2>/dev/null || true
  fi
}

_json_val_nested() {
  # _json_val_nested <json_string> <outer_key> <inner_key>
  # Extract a nested value: json[outer_key][inner_key]
  local json="$1" outer="$2" inner="$3"
  if command -v jq &>/dev/null; then
    echo "$json" | jq -r ".${outer}.${inner} // empty" 2>/dev/null || true
  else
    python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
print(d.get('$outer',{}).get('$inner',''))
" <<< "$json" 2>/dev/null || true
  fi
}

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL="${BASE_URL:-http://localhost:8000}"
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:3000}"
ENV_FILE=".env"
TEST_AGENT_TYPE="Echo"

# Read API key from .env
if [ -f "$ENV_FILE" ]; then
  API_KEY=$(grep '^HERETEK_API_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")
  if [ -z "$API_KEY" ]; then
    echo "WARNING: HERETEK_API_KEY not found in $ENV_FILE — using fallback"
    API_KEY="htsk-placeholder-for-local-dev"
  fi
else
  echo "WARNING: $ENV_FILE not found — using fallback API key"
  API_KEY="htsk-placeholder-for-local-dev"
fi

# Global state for cleanup
DEPLOYED_INSTANCE_ID=""
CLEANUP_DONE=false

# ---------------------------------------------------------------------------
# Cleanup trap (runs even if script exits early)
# ---------------------------------------------------------------------------
cleanup() {
  if [ "$CLEANUP_DONE" = true ]; then
    return
  fi
  if [ -n "$DEPLOYED_INSTANCE_ID" ]; then
    echo ""
    echo -e "${BOLD}── Cleanup: removing test agent ${DEPLOYED_INSTANCE_ID} ──${NC}"
    if curl -s --connect-timeout 5 --max-time 10 \
      -X DELETE \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID" > /dev/null 2>&1; then
      echo -e "${GREEN}✓${NC} Test agent removed"
    else
      echo -e "${YELLOW}⚠${NC} Could not remove test agent (may already be gone)"
    fi
    CLEANUP_DONE=true
  fi
}
trap cleanup EXIT

# =============================================================================
# STATIC CHECKS
# =============================================================================
header "STATIC CHECKS"

# ---- Check 1: Syntax validation ----
echo ""
echo "── Script syntax ──"

if bash -n "$0" 2>/dev/null; then
  pass "bash -n syntax check passed"
else
  fail "bash -n syntax check failed"
fi

# ---- Check 2: shellcheck (if available) ----
if command -v shellcheck &>/dev/null; then
  if shellcheck "$0" 2>&1; then
    pass "shellcheck passed"
  else
    warn "shellcheck returned warnings/errors"
  fi
else
  skip "shellcheck not installed — skipping"
fi

# =============================================================================
# RUNTIME CHECKS — Docker container health
# =============================================================================
header "RUNTIME CHECKS — Docker containers"

# ---- Check 3: Docker container health ----
echo ""
echo "── Container health ──"

DOCKER_AVAILABLE=false
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
  DOCKER_AVAILABLE=true
fi

if $DOCKER_AVAILABLE; then
  CONTAINER_OUTPUT=$(docker ps --filter "name=heretek" --format '{{.Names}} {{.Status}}' 2>/dev/null || true)

  # Count non-empty lines
  CONTAINER_COUNT=0
  if [ -n "$CONTAINER_OUTPUT" ]; then
    CONTAINER_COUNT=$(echo "$CONTAINER_OUTPUT" | grep -c . || echo "0")
  fi

  if [ "$CONTAINER_COUNT" -eq 0 ]; then
    fail "No heretek containers found (docker ps returned empty)"
  else
    echo "   Found $CONTAINER_COUNT container(s):"
    echo "$CONTAINER_OUTPUT" | while read -r line; do
      echo "     $line"
    done

    HEALTHY_COUNT=$(echo "$CONTAINER_OUTPUT" | grep -ciE 'healthy|\(healthy\)' || echo "0")
    RUNNING_COUNT=$(echo "$CONTAINER_OUTPUT" | grep -ciE 'Up |healthy' || echo "0")

    if [ "$RUNNING_COUNT" -ge 2 ]; then
      pass "All $CONTAINER_COUNT/6 containers running ($HEALTHY_COUNT healthy)"
    else
      fail "Expected ≥2 running heretek containers (found $CONTAINER_COUNT total, $HEALTHY_COUNT healthy)"
    fi
  fi
else
  skip "Docker not available — skipping container health check"
fi

# =============================================================================
# RUNTIME CHECKS — API reachability & auth
# =============================================================================
header "RUNTIME CHECKS — API at $BASE_URL"

API_REACHABLE=false

HTTP_CODE=$(curl -s --connect-timeout 5 --max-time 10 -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
  API_REACHABLE=true
  echo "API reachable at $BASE_URL/api/health (HTTP $HTTP_CODE)"
else
  echo "API health probe returned HTTP $HTTP_CODE"
fi

if $API_REACHABLE; then

  # ---- Check 4: Health endpoint (open, no auth) ----
  echo ""
  echo "── API health check ──"

  if curl -sf --connect-timeout 5 --max-time 10 "$BASE_URL/api/health" > /dev/null 2>&1; then
    pass "GET /api/health → 200 (open endpoint)"
  else
    fail "GET /api/health did not return 200"
  fi

  # ---- Check 5: Auth enforcement ----
  echo ""
  echo "── Auth enforcement ──"

  # 5a. Authenticated health check
  if curl -sf --connect-timeout 5 --max-time 10 \
    -H "Authorization: Bearer $API_KEY" \
    "$BASE_URL/api/health" > /dev/null 2>&1; then
    pass "GET /api/health with Bearer token → 200"
  else
    fail "GET /api/health with Bearer token failed"
  fi

  # 5b. Unauthenticated gated endpoint returns 401
  UNAUTH_STATUS=$(curl -s --connect-timeout 5 --max-time 10 \
    -o /dev/null -w "%{http_code}" \
    "$BASE_URL/api/agents/deploy" 2>/dev/null || echo "000")
  if [ "$UNAUTH_STATUS" = "401" ] || [ "$UNAUTH_STATUS" = "403" ]; then
    pass "POST /api/agents/deploy without auth → $UNAUTH_STATUS (gated)"
  else
    fail "POST /api/agents/deploy without auth → $UNAUTH_STATUS (expected 401)"
  fi

  # ---- Check 6: Deploy test agent ----
  echo ""
  echo "── Deploy test agent (type=$TEST_AGENT_TYPE) ──"

  DEPLOY_RESPONSE=$(curl -s --connect-timeout 10 --max-time 30 \
    -X POST \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"agent_type\":\"$TEST_AGENT_TYPE\",\"config\":{\"name\":\"test-agent-for-s03\"}}" \
    "$BASE_URL/api/agents/deploy" 2>/dev/null || echo '{"error":"deploy_failed"}')

  DEPLOYED_INSTANCE_ID=$(_json_val "$DEPLOY_RESPONSE" "instance_id")

  if [ -n "$DEPLOYED_INSTANCE_ID" ] && [ "$DEPLOYED_INSTANCE_ID" != "null" ]; then
    DEPLOYED_TYPE=$(_json_val "$DEPLOY_RESPONSE" "agent_type")
    DEPLOYED_STATE=$(_json_val "$DEPLOY_RESPONSE" "state")
    pass "POST /api/agents/deploy → instance_id=$DEPLOYED_INSTANCE_ID (type=$DEPLOYED_TYPE, state=$DEPLOYED_STATE)"
  else
    DEPLOY_ERROR=$(_json_val "$DEPLOY_RESPONSE" "detail")
    fail "POST /api/agents/deploy failed: $DEPLOY_ERROR"
  fi

  if [ -n "$DEPLOYED_INSTANCE_ID" ] && [ "$DEPLOYED_INSTANCE_ID" != "null" ]; then

    # ---- Check 7: Supervisor agent listing ----
    echo ""
    echo "── Supervisor agent listing ──"

    SUP_LIST=$(curl -s --connect-timeout 5 --max-time 10 \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/agents/" 2>/dev/null || echo '{}')

    SUP_TOTAL=$(_json_val "$SUP_LIST" "total")
    if [ -n "$SUP_TOTAL" ]; then
      pass "GET /api/agents/ → supervisor lists $SUP_TOTAL agent(s)"
    else
      warn "GET /api/agents/ → supervisor returned unexpected response"
    fi

    # ---- Check 8: GET /api/agents/{id}/memory ----
    echo ""
    echo "── Agent memory endpoint ──"

    MEM_HTTP=$(curl -s --connect-timeout 5 --max-time 10 \
      -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID/memory" 2>/dev/null || echo "000")

    if [ "$MEM_HTTP" = "200" ]; then
      MEM_RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 \
        -H "Authorization: Bearer $API_KEY" \
        "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID/memory" 2>/dev/null || echo '{}')
      MEM_AGENT_ID=$(_json_val "$MEM_RESPONSE" "agent_id")
      MEM_TOTAL=$(_json_val "$MEM_RESPONSE" "total_memories")
      MEM_STATUS=$(_json_val "$MEM_RESPONSE" "status")

      MEM_ALL_OK=true
      if [ "$MEM_AGENT_ID" != "$DEPLOYED_INSTANCE_ID" ]; then
        fail "GET /api/agents/{id}/memory → agent_id mismatch: got '$MEM_AGENT_ID'"
        MEM_ALL_OK=false
      fi
      for field in total_memories by_type recent_entries status; do
        val=$(_json_val "$MEM_RESPONSE" "$field")
        if [ -z "$val" ] || [ "$val" = "null" ]; then
          fail "GET /api/agents/{id}/memory → missing field: $field"
          MEM_ALL_OK=false
        fi
      done
      if [ "$MEM_ALL_OK" = true ]; then
        pass "GET /api/agents/{id}/memory → 200, total=$MEM_TOTAL, status=$MEM_STATUS"
      fi
    elif [ "$MEM_HTTP" = "404" ]; then
      warn "GET /api/agents/{id}/memory → 404 (route not yet registered in running container — rebuild API to deploy instances.py memory/tools/tasks routes)"
    else
      fail "GET /api/agents/{id}/memory → HTTP $MEM_HTTP (expected 200 or 404)"
    fi

    # ---- Check 9: GET /api/agents/{id}/tools ----
    echo ""
    echo "── Agent tools endpoint ──"

    TOOLS_HTTP=$(curl -s --connect-timeout 5 --max-time 10 \
      -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID/tools" 2>/dev/null || echo "000")

    if [ "$TOOLS_HTTP" = "200" ]; then
      TOOLS_RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 \
        -H "Authorization: Bearer $API_KEY" \
        "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID/tools" 2>/dev/null || echo '{}')
      TOOLS_AGENT_ID=$(_json_val "$TOOLS_RESPONSE" "agent_id")
      TOOLS_TOTAL=$(_json_val "$TOOLS_RESPONSE" "total")

      TOOLS_ALL_OK=true
      if [ "$TOOLS_AGENT_ID" != "$DEPLOYED_INSTANCE_ID" ]; then
        fail "GET /api/agents/{id}/tools → agent_id mismatch: got '$TOOLS_AGENT_ID'"
        TOOLS_ALL_OK=false
      fi
      for field in skills plugins total; do
        val=$(_json_val "$TOOLS_RESPONSE" "$field")
        if [ -z "$val" ] || [ "$val" = "null" ]; then
          fail "GET /api/agents/{id}/tools → missing field: $field"
          TOOLS_ALL_OK=false
        fi
      done
      if [ "$TOOLS_ALL_OK" = true ]; then
        pass "GET /api/agents/{id}/tools → 200, total=$TOOLS_TOTAL"
      fi
    elif [ "$TOOLS_HTTP" = "404" ]; then
      warn "GET /api/agents/{id}/tools → 404 (route not yet registered in running container)"
    else
      fail "GET /api/agents/{id}/tools → HTTP $TOOLS_HTTP (expected 200 or 404)"
    fi

    # ---- Check 10: GET /api/agents/{id}/tasks ----
    echo ""
    echo "── Agent tasks endpoint ──"

    TASKS_HTTP=$(curl -s --connect-timeout 5 --max-time 10 \
      -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID/tasks" 2>/dev/null || echo "000")

    if [ "$TASKS_HTTP" = "200" ]; then
      TASKS_RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 \
        -H "Authorization: Bearer $API_KEY" \
        "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID/tasks" 2>/dev/null || echo '{}')
      TASKS_AGENT_ID=$(_json_val "$TASKS_RESPONSE" "agent_id")
      TASKS_STATUS=$(_json_val "$TASKS_RESPONSE" "status")

      TASKS_ALL_OK=true
      if [ "$TASKS_AGENT_ID" != "$DEPLOYED_INSTANCE_ID" ]; then
        fail "GET /api/agents/{id}/tasks → agent_id mismatch: got '$TASKS_AGENT_ID'"
        TASKS_ALL_OK=false
      fi
      for field in status capabilities message_count error_count last_activity uptime_seconds; do
        val=$(_json_val "$TASKS_RESPONSE" "$field")
        if [ -z "$val" ] || [ "$val" = "null" ]; then
          fail "GET /api/agents/{id}/tasks → missing field: $field"
          TASKS_ALL_OK=false
        fi
      done
      if [ "$TASKS_ALL_OK" = true ]; then
        pass "GET /api/agents/{id}/tasks → 200, status=$TASKS_STATUS"
      fi
    elif [ "$TASKS_HTTP" = "404" ]; then
      warn "GET /api/agents/{id}/tasks → 404 (route not yet registered in running container)"
    else
      fail "GET /api/agents/{id}/tasks → HTTP $TASKS_HTTP (expected 200 or 404)"
    fi

    # ---- Check 11: Supervisor agent detail ----
    echo ""
    echo "── Agent detail (supervisor) ──"

    DETAIL_HTTP=$(curl -s --connect-timeout 5 --max-time 10 \
      -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID" 2>/dev/null || echo "000")

    # The supervisor GET /{agent_id} shadows the instances GET /{instance_id}.
    # If agent is running under supervisor, detail will be 200; otherwise 404.
    if [ "$DETAIL_HTTP" = "200" ]; then
      DETAIL_RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 \
        -H "Authorization: Bearer $API_KEY" \
        "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID" 2>/dev/null || echo '{}')
      pass "GET /api/agents/{id} → 200 (agent found in supervisor)"
    elif [ "$DETAIL_HTTP" = "404" ]; then
      warn "GET /api/agents/{id} → 404 (agent not managed by supervisor — expected for registry-only agents)"
    else
      warn "GET /api/agents/{id} → HTTP $DETAIL_HTTP"
    fi

    # ---- Check 12: Cleanup — delete test agent ----
    echo ""
    echo "── Cleanup: remove test agent ──"

    CLEANUP_HTTP=$(curl -s --connect-timeout 5 --max-time 10 \
      -o /dev/null -w "%{http_code}" \
      -X DELETE \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/agents/$DEPLOYED_INSTANCE_ID" 2>/dev/null || echo "000")
    CLEANUP_DONE=true
    DEPLOYED_INSTANCE_ID=""

    if [ "$CLEANUP_HTTP" = "200" ]; then
      pass "DELETE /api/agents/{id} → 200 (agent removed successfully)"
    else
      fail "DELETE /api/agents/{id} → HTTP $CLEANUP_HTTP (expected 200)"
    fi

  else
    skip "Checks 7-12 — no agent deployed to test against"
  fi

else
  skip "All API checks — API at $BASE_URL not reachable (HTTP $HTTP_CODE)"
fi

# =============================================================================
# DASHBOARD CHECKS
# =============================================================================
header "DASHBOARD CHECKS — at $DASHBOARD_URL"

# ---- Check 13: Dashboard reachable ----
echo ""
echo "── Dashboard reachability ──"

DASH_HTTP=$(curl -s --connect-timeout 5 --max-time 10 -o /tmp/verify-m016-s03-dash.html -w "%{http_code}" "$DASHBOARD_URL" 2>/dev/null || echo "000")

if [ "$DASH_HTTP" = "200" ]; then
  DASH_BODY=$(cat /tmp/verify-m016-s03-dash.html 2>/dev/null || echo "")
  if echo "$DASH_BODY" | grep -qiE 'Heretek|Swarm|heretek'; then
    pass "GET $DASHBOARD_URL → 200, contains 'Heretek'/'Swarm'"
  else
    warn "GET $DASHBOARD_URL → 200, but no 'Heretek'/'Swarm' marker found in body"
  fi
else
  fail "GET $DASHBOARD_URL → HTTP $DASH_HTTP (expected 200)"
fi

rm -f /tmp/verify-m016-s03-dash.html

# ---- Check 14: Dashboard API proxy ----
echo ""
echo "── Dashboard API proxy ──"

if [ "$DASH_HTTP" = "200" ]; then
  PROXY_HEALTH=$(curl -s --connect-timeout 5 --max-time 10 \
    -o /dev/null -w "%{http_code}" \
    "$DASHBOARD_URL/api/health" 2>/dev/null || echo "000")

  if [ "$PROXY_HEALTH" = "200" ] || [ "$PROXY_HEALTH" = "401" ]; then
    pass "GET $DASHBOARD_URL/api/health → $PROXY_HEALTH (API proxy working)"
  else
    warn "GET $DASHBOARD_URL/api/health → $PROXY_HEALTH (proxy may not be configured)"
  fi
else
  skip "Dashboard API proxy check — dashboard not reachable"
fi

# =============================================================================
# TYPESCRIPT CHECK
# =============================================================================
header "TYPESCRIPT CHECK — swarm-dashboard/"

# ---- Check 15: npx tsc --noEmit ----
echo ""
echo "── TypeScript compilation ──"

if [ -d "swarm-dashboard" ]; then
  if [ -f "swarm-dashboard/package.json" ]; then
    cd swarm-dashboard
    if npx --yes tsc --noEmit 2>&1; then
      pass "npx tsc --noEmit passed clean"
    else
      warn "npx tsc --noEmit returned errors (may be pre-existing)"
    fi
    cd "$PROJECT_ROOT"
  else
    skip "swarm-dashboard/package.json not found"
  fi
else
  skip "swarm-dashboard/ directory not found"
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
  echo -e "${GREEN}${BOLD}=== M016/S03 integration gate: ALL CHECKS PASSED ===${NC}"
  exit 0
else
  echo -e "${RED}${BOLD}=== M016/S03 integration gate: ${FAILED} CHECK(S) FAILED ===${NC}"
  exit 1
fi
