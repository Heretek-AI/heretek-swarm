#!/bin/bash
# verify-sops-encryption.sh — Pre-commit hook: SOPS encryption integrity verification
#
# Checks:
#   1. All files in secrets/ (except *_unencrypted) are valid SOPS-encrypted
#      files — must contain sops version/mac metadata and an age recipient
#   2. .sops.yaml age public key matches the recipient used in each
#      encrypted secrets file
#   3. Staged non-secrets files are free of obvious plaintext credential
#      patterns (API_KEY=, password= with actual values, not templates)
#
# Designed to run as a local pre-commit hook and standalone for verification.

set -euo pipefail

FAILED=0
SOPS_CONFIG=".sops.yaml"
SECRETS_DIR="secrets"
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RESET="\033[0m"

echo "=== SOPS Encryption Verification ==="
echo ""

# ---------------------------------------------------------------------------
# Collect files to check: staged secrets files, or all secrets files if
# running standalone (pre-commit run --all-files / manual invocation).
# ---------------------------------------------------------------------------

IN_GIT=false
git rev-parse --git-dir > /dev/null 2>&1 && IN_GIT=true || true

if $IN_GIT; then
    STAGED_SECRETS=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep "^${SECRETS_DIR}/" || true)
    STAGED_NONSECRETS=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep -v "^${SECRETS_DIR}/" | grep -v "^\.gsd/" | grep -v "^${SECRETS_DIR}" || true)
fi

# If no staged files (manual run or --all-files), scan everything in secrets/
if [ -z "${STAGED_SECRETS:-}" ]; then
    if [ -d "$SECRETS_DIR" ]; then
        STAGED_SECRETS=$(find "$SECRETS_DIR" -type f 2>/dev/null | sort || true)
    else
        STAGED_SECRETS=""
    fi
fi

# ---------------------------------------------------------------------------
# Helper: detect if a file has valid SOPS metadata (without decryption).
# Returns 0 if valid, 1 if not.
#
# SOPS stores metadata differently by format:
#   - YAML/JSON: a `sops:` block with version, mac, and age recipients
#   - dotenv: `sops_*` keys (sops_version=, sops_mac=ENC[...], etc.)
#   - binary: sops metadata at end with version marker
# ---------------------------------------------------------------------------
has_sops_metadata() {
    local file="$1"

    # Dotenv format: inline sops_version= key at end of file
    if grep -q '^sops_version=' "$file" 2>/dev/null; then
        return 0
    fi

    # YAML format: sops: key with version field
    if grep -qE '^(sops:|sops\s*$)' "$file" 2>/dev/null; then
        return 0
    fi

    # JSON format: "sops": { ... }
    if grep -q '"sops"' "$file" 2>/dev/null; then
        return 0
    fi

    # Fallback: check for sops MAC in any format
    if grep -qE '(sops_mac|"mac"):.*(ENC\[|ENC\()' "$file" 2>/dev/null; then
        return 0
    fi

    return 1
}

# ---------------------------------------------------------------------------
# Helper: extract age recipient from a SOPS-encrypted file.
# Works for YAML sops block and dotenv sops_age__list_0__map_recipient format.
# ---------------------------------------------------------------------------
extract_age_recipient() {
    local file="$1"

    # Dotenv format: sops_age__list_0__map_recipient=age1...
    local recipient
    recipient=$(grep -oP '^sops_age__list_\d+__map_recipient=age1[a-z0-9]{58}' "$file" 2>/dev/null | head -1 | cut -d= -f2 || echo "")
    if [ -n "$recipient" ]; then
        echo "$recipient"
        return 0
    fi

    # YAML format: recipient: age1... (under age: list)
    recipient=$(grep -oP 'recipient:\s*age1[a-z0-9]{58}' "$file" 2>/dev/null | head -1 | sed 's/recipient:\s*//' || echo "")
    if [ -n "$recipient" ]; then
        echo "$recipient"
        return 0
    fi

    return 1
}

# ---------------------------------------------------------------------------
# 1. Structural SOPS validation
# ---------------------------------------------------------------------------
echo "--- Check 1: SOPS file structure ---"

SCANNED_COUNT=0
for file in $STAGED_SECRETS; do
    # Skip _unencrypted suffix files (they're templates)
    if [[ "$(basename "$file")" == *_unencrypted ]]; then
        echo "  ⊘ SKIP: $file (unencrypted suffix — template, not a secret)"
        continue
    fi

    if [ ! -f "$file" ]; then
        continue
    fi

    SCANNED_COUNT=$((SCANNED_COUNT + 1))

    if has_sops_metadata "$file"; then
        # Also verify an age recipient is present
        RECIPIENT=$(extract_age_recipient "$file" || echo "")
        if [ -n "$RECIPIENT" ]; then
            echo "  ${GREEN}✓${RESET} PASS: $file (SOPS-encrypted, age recipient present)"
        else
            echo "  ${RED}✗${RESET} FAIL: $file — SOPS metadata found but no age recipient"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "  ${RED}✗${RESET} FAIL: $file — no SOPS metadata; not a valid encrypted file"
        FAILED=$((FAILED + 1))
    fi
done

if [ "$SCANNED_COUNT" -eq 0 ]; then
    echo "  ⊘ SKIP: No secrets files to check"
fi

# ---------------------------------------------------------------------------
# 2. Age key consistency
# ---------------------------------------------------------------------------
echo ""
echo "--- Check 2: Age key consistency ---"

# Extract expected public key from .sops.yaml (age1… format, 62 chars total)
EXPECTED_KEY=$(grep -oP 'age1[a-z0-9]{58}' "$SOPS_CONFIG" 2>/dev/null | sort -u | head -1 || echo "")

if [ -z "$EXPECTED_KEY" ]; then
    echo "  ${YELLOW}⚠${RESET} WARN: Could not extract age public key from $SOPS_CONFIG"
else
    echo "  Expected key: $EXPECTED_KEY"

    for file in $STAGED_SECRETS; do
        if [[ "$(basename "$file")" == *_unencrypted ]]; then
            continue
        fi
        if [ ! -f "$file" ]; then
            continue
        fi

        FILE_KEY=$(extract_age_recipient "$file" || echo "")

        if [ -z "$FILE_KEY" ]; then
            echo "  ${RED}✗${RESET} FAIL: $file — cannot extract age recipient"
            FAILED=$((FAILED + 1))
        elif [ "$FILE_KEY" = "$EXPECTED_KEY" ]; then
            echo "  ${GREEN}✓${RESET} PASS: $file — age key matches .sops.yaml"
        else
            echo "  ${RED}✗${RESET} FAIL: $file — uses key $FILE_KEY, expected $EXPECTED_KEY"
            FAILED=$((FAILED + 1))
        fi
    done
fi

# ---------------------------------------------------------------------------
# 3. Plaintext credential detection in staged non-secrets files.
# ---------------------------------------------------------------------------
echo ""
echo "--- Check 3: Plaintext credential scan (staged non-secrets files) ---"

if [ -z "${STAGED_NONSECRETS:-}" ]; then
    echo "  ⊘ SKIP: No staged non-secrets files to scan"
else
    SCANNED_NONSECRETS=0
    NONSECRET_FAILURES=0

    for file in $STAGED_NONSECRETS; do
        if [ ! -f "$file" ]; then
            continue
        fi

        # Skip binary files
        MIME=$(file -b --mime-type "$file" 2>/dev/null || echo "application/octet-stream")
        if [[ "$MIME" != text/* ]] && [[ "$MIME" != application/json ]] && [[ "$MIME" != application/xml ]]; then
            continue
        fi

        # Skip files that are documentation or example templates
        BASENAME=$(basename "$file")
        if [[ "$BASENAME" == ".env.example" ]] || \
           [[ "$BASENAME" == *".example" ]] || \
           [[ "$file" =~ ^docs/ ]] || \
           [[ "$file" =~ /\.agents/skills/ ]] || \
           [[ "$file" =~ \.md$ ]] || \
           [[ "$file" =~ \.lock$ ]] || \
           [[ "$file" =~ \.json$ ]]; then
            continue
        fi

        SCANNED_NONSECRETS=$((SCANNED_NONSECRETS + 1))

        # Check for API_KEY= with actual-looking values (not placeholder/template words)
        PLACEHOLDER_RE='(your_|change_me|replace_me|example|test_|dummy|xxx|TODO|YOUR_|CHANGE_|REPLACE_|<)'
        if grep -Pn '^\s*(API_KEY|api_key|apikey|API_SECRET|api_secret)\s*=\s*["\x27]?[a-zA-Z0-9_\-\.]{12,}["\x27]?\s*$' "$file" 2>/dev/null | grep -vPi "$PLACEHOLDER_RE" > /tmp/sops-verify-hits.$$ 2>/dev/null; then
            if [ -s /tmp/sops-verify-hits.$$ ]; then
                while IFS= read -r line; do
                    echo "  ${RED}✗${RESET} FAIL: $file: API key pattern — $line"
                    NONSECRET_FAILURES=$((NONSECRET_FAILURES + 1))
                done < /tmp/sops-verify-hits.$$
            fi
        fi

        # Check for password= with actual values (not placeholder)
        if grep -Pn '^\s*(password|PASSWORD|passwd|PASSWD)\s*=\s*["\x27]?[a-zA-Z0-9_\-!@#$%^&*()]{8,}["\x27]?\s*$' "$file" 2>/dev/null | grep -vPi "$PLACEHOLDER_RE" > /tmp/sops-verify-hits.$$ 2>/dev/null; then
            if [ -s /tmp/sops-verify-hits.$$ ]; then
                while IFS= read -r line; do
                    echo "  ${RED}✗${RESET} FAIL: $file: password pattern — $line"
                    NONSECRET_FAILURES=$((NONSECRET_FAILURES + 1))
                done < /tmp/sops-verify-hits.$$
            fi
        fi

        # Check for auth/access token patterns
        if grep -Pn '^\s*(AUTH_TOKEN|auth_token|ACCESS_TOKEN|access_token)\s*=\s*["\x27]?[a-zA-Z0-9_\-\.]{16,}["\x27]?\s*$' "$file" 2>/dev/null | grep -vPi "$PLACEHOLDER_RE" > /tmp/sops-verify-hits.$$ 2>/dev/null; then
            if [ -s /tmp/sops-verify-hits.$$ ]; then
                while IFS= read -r line; do
                    echo "  ${RED}✗${RESET} FAIL: $file: token pattern — $line"
                    NONSECRET_FAILURES=$((NONSECRET_FAILURES + 1))
                done < /tmp/sops-verify-hits.$$
            fi
        fi

        # Check for private keys inlined
        if grep -q '^-----BEGIN.*PRIVATE KEY-----$' "$file" 2>/dev/null; then
            MATCH_LINE=$(grep -n '^-----BEGIN.*PRIVATE KEY-----$' "$file" | head -1)
            echo "  ${RED}✗${RESET} FAIL: $file: private key inlined — $MATCH_LINE"
            NONSECRET_FAILURES=$((NONSECRET_FAILURES + 1))
        fi
    done

    FAILED=$((FAILED + NONSECRET_FAILURES))
    rm -f /tmp/sops-verify-hits.$$

    if [ "$NONSECRET_FAILURES" -eq 0 ]; then
        echo "  ${GREEN}✓${RESET} PASS: Scanned ${SCANNED_NONSECRETS} staged non-secrets file(s); no plaintext credentials found"
    fi
fi

# ---------------------------------------------------------------------------
# Final verdict
# ---------------------------------------------------------------------------
echo ""
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}=== SOPS verification: ALL CHECKS PASSED ===${RESET}"
    exit 0
else
    echo -e "${RED}=== SOPS verification: ${FAILED} CHECK(S) FAILED ===${RESET}"
    echo ""
    echo "Remediation:"
    echo "  • Encrypt plaintext secrets:  sops --encrypt <file> > <file>"
    echo "  • Re-encrypt with correct key: sops --rotate --in-place <file>"
    echo "  • Mark template as unencrypted: rename to *_unencrypted"
    echo "  • Add/update .secrets.baseline: detect-secrets scan --baseline .secrets.baseline .secrets.baseline"
    exit 1
fi
