#!/bin/bash
# verify-auth-s01.sh - Verify all 8 routers return 401 without auth, 200 with auth

API_KEY="${HERETEK_API_KEY:-htsk_dev_key}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
FAILED=0

# Define test endpoints for each router (one representative endpoint per router)
ENDPOINTS=(
  "/api/wizard/status"
  "/api/v1/providers/llm"
  "/api/plugins"
  "/api/collective/evolution-status"
  "/autonomous/agents"
  "/api/wizard/provision/status"
  "/metrics"
  "/mcp/tools/list"
)

for endpoint in "${ENDPOINTS[@]}"; do
  # Without auth: expect 401
  status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
  if [ "$status" = "401" ]; then
    echo "✓ $endpoint → 401 (no auth)"
  else
    echo "✗ $endpoint → $status (expected 401)"
    FAILED=$((FAILED + 1))
  fi

  # With auth: expect 200 or 422 (validation) or 404, but NOT 401
  status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $API_KEY" "$BASE_URL$endpoint")
  if [ "$status" != "401" ]; then
    echo "✓ $endpoint → $status (with auth, not 401)"
  else
    echo "✗ $endpoint → 401 (expected non-401 with valid key)"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
if [ "$FAILED" -eq 0 ]; then
  echo "All checks passed!"
  exit 0
else
  echo "$FAILED checks failed"
  exit 1
fi
