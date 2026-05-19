#!/bin/bash
# verify-s02.sh — S02 verification: zero infrastructure URL localhost fallbacks
# Checks for remaining localhost/0.0.0.0 defaults in Redis, Postgres/Database,
# NATS, and Qdrant connection URLs across backend/heretek_swarm/ production code.
#
# Usage: bash scripts/verify-s02.sh
# Exit 0 = PASS (zero remaining fallbacks)
# Exit 1 = FAIL (at least one fallback found)

set -euo pipefail

FAILED=0
SRC_DIR="backend/heretek_swarm"
EXCLUDES=(-not -path "*/test_*" -not -path "*/tests/*" -not -path "*/__pycache__/*")

echo "=== S02: Infrastructure URL localhost fallback verification ==="
echo ""

# ---------------------------------------------------------------------------
# 1. REDIS_URL — redis://localhost, REDIS_URL.*localhost, REDIS_URL.*0.0.0.0
# ---------------------------------------------------------------------------
echo "--- Redis ---"
REDIS_HITS=$(grep -rn "redis://localhost\|REDIS_URL.*localhost\|REDIS_URL.*0\.0\.0\.0" "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$REDIS_HITS" ]; then
    echo "✓ PASS: No Redis localhost fallbacks"
else
    echo "✗ FAIL: Redis localhost fallbacks found:"
    echo "$REDIS_HITS"
    FAILED=$((FAILED + 1))
fi

# ---------------------------------------------------------------------------
# 2. DATABASE_URL / POSTGRES_HOST — postgresql://localhost, DATABASE_URL.*localhost
# ---------------------------------------------------------------------------
echo "--- Postgres / Database ---"
PG_HITS=$(grep -rn "postgresql://localhost\|DATABASE_URL.*localhost\|POSTGRES_HOST.*localhost\|DATABASE_URL.*0\.0\.0\.0\|POSTGRES_HOST.*0\.0\.0\.0" "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$PG_HITS" ]; then
    echo "✓ PASS: No Postgres/DATABASE_URL localhost fallbacks"
else
    echo "✗ FAIL: Postgres/DATABASE_URL localhost fallbacks found:"
    echo "$PG_HITS"
    FAILED=$((FAILED + 1))
fi

# ---------------------------------------------------------------------------
# 3. NATS — nats://localhost:4222, HERETEK_NATS_URL.*localhost
# ---------------------------------------------------------------------------
echo "--- NATS ---"
NATS_HITS=$(grep -rn "nats://localhost:4222\|HERETEK_NATS_URL.*localhost\|HERETEK_NATS_URL.*0\.0\.0\.0" "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$NATS_HITS" ]; then
    echo "✓ PASS: No NATS localhost fallbacks"
else
    echo "✗ FAIL: NATS localhost fallbacks found:"
    echo "$NATS_HITS"
    FAILED=$((FAILED + 1))
fi

# ---------------------------------------------------------------------------
# 4. Qdrant — QDRANT_HOST.*localhost, QDRANT_URL.*localhost,
#           http://localhost:6333 in Qdrant context
# ---------------------------------------------------------------------------
echo "--- Qdrant ---"
QDRANT_HITS=$(grep -rn "QDRANT_HOST.*localhost\|QDRANT_URL.*localhost\|QDRANT_HOST.*0\.0\.0\.0\|QDRANT_URL.*0\.0\.0\.0\|http://localhost:6333\|qdrant.*localhost" "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>' || true)
if [ -z "$QDRANT_HITS" ]; then
    echo "✓ PASS: No Qdrant localhost fallbacks"
else
    echo "✗ FAIL: Qdrant localhost fallbacks found:"
    echo "$QDRANT_HITS"
    FAILED=$((FAILED + 1))
fi

# ---------------------------------------------------------------------------
# 5. Broad sweep: any remaining localhost/0.0.0.0 used as a URL/connection
#    default in non-test production code.
#    Catches patterns like: "localhost" or 'localhost' or "0.0.0.0" used as
#    default values in .py files outside tests.
# ---------------------------------------------------------------------------
echo "--- Broad localhost sweep ---"
BROAD_HITS=$(grep -rn "\"localhost\"\|'localhost'\|0\.0\.0\.0" "$SRC_DIR" --include='*.py' "${EXCLUDES[@]}" 2>/dev/null | grep -v 'docstring\|# example\|>>>\|\"localhost:8080\"\|\"localhost:8000\"\|test_' || true)
if [ -z "$BROAD_HITS" ]; then
    echo "✓ PASS: No remaining localhost/0.0.0.0 string literals"
else
    # Further filter: exclude known-safe patterns (dev server refs, docs)
    FILTERED=$(echo "$BROAD_HITS" | grep -v 'uvicorn.*localhost\|#.*localhost\|\.md.*localhost\|localhost:8080\|localhost:8000' || true)
    if [ -z "$FILTERED" ]; then
        echo "✓ PASS: Remaining localhost references are benign (uvicorn, docs, dev server URLs)"
    else
        echo "✗ FAIL: Potentially unsafe localhost/0.0.0.0 references found:"
        echo "$FILTERED"
        FAILED=$((FAILED + 1))
    fi
fi

echo ""
if [ "$FAILED" -eq 0 ]; then
    echo "=== S02 verification: ALL CHECKS PASSED ==="
    exit 0
else
    echo "=== S02 verification: ${FAILED} CHECK(S) FAILED ==="
    exit 1
fi
