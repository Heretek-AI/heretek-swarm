#!/bin/bash
# verify-s04.sh — S04 verification: sanitized 500s, SPA artifacts removed
# Verify:
#   1. No f-string-leaking HTTPException(500) in wizard.py
#   2. logger.exception() used in all 6 wizard infrastructure except blocks
#   3. No SPA-serving artifacts (_init_spa_mount, StaticFiles, root endpoint, FileResponse) in main.py

set -euo pipefail

FAILED=0
WIZARD="backend/heretek_swarm/api/wizard.py"
MAIN="backend/heretek_swarm/api/main.py"

echo "=== S04: Wizard 500 sanitization & SPA removal verification ==="
echo ""

# 1. No f-string-leaking 500s
if grep -q 'raise HTTPException(500, f' "$WIZARD" 2>/dev/null; then
    echo "✗ FAIL: f-string-leaking HTTPException(500) found in wizard.py"
    FAILED=$((FAILED + 1))
else
    echo "✓ PASS: No f-string-leaking HTTPException(500) in wizard.py"
fi

# 2. logger.exception count >= 6
COUNT=$(grep -c 'logger.exception' "$WIZARD" 2>/dev/null || echo "0")
if [ "$COUNT" -ge 6 ]; then
    echo "✓ PASS: logger.exception count=${COUNT} (>= 6) in wizard.py"
else
    echo "✗ FAIL: logger.exception count=${COUNT} (< 6) in wizard.py"
    FAILED=$((FAILED + 1))
fi

# 3. No SPA mount artifacts
if grep -q '_init_spa_mount\|StaticFiles' "$MAIN" 2>/dev/null; then
    echo "✗ FAIL: SPA mount artifacts (_init_spa_mount/StaticFiles) found in main.py"
    FAILED=$((FAILED + 1))
else
    echo "✓ PASS: No SPA mount artifacts in main.py"
fi

# 4. No root endpoint
if grep -q '@app.get("/")' "$MAIN" 2>/dev/null; then
    echo "✗ FAIL: Root endpoint @app.get('/') found in main.py"
    FAILED=$((FAILED + 1))
else
    echo "✓ PASS: No root endpoint in main.py"
fi

# 5. No FileResponse import
if grep -q 'FileResponse' "$MAIN" 2>/dev/null; then
    echo "✗ FAIL: FileResponse reference found in main.py"
    FAILED=$((FAILED + 1))
else
    echo "✓ PASS: No FileResponse in main.py"
fi

echo ""
if [ "$FAILED" -eq 0 ]; then
    echo "=== S04 verification: ALL CHECKS PASSED ==="
    exit 0
else
    echo "=== S04 verification: ${FAILED} CHECK(S) FAILED ==="
    exit 1
fi
