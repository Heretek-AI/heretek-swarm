#!/usr/bin/env bash
# api_latency.sh — Sample API endpoints and compute latency percentiles
#
# Prerequisites: docker compose up (swarm stack running locally)
# Usage: bash scripts/bench/api_latency.sh [NUM_SAMPLES]
# Output: scripts/bench/results/api_latency_YYYYMMDD_HHMMSS.json

set -euo pipefail

NUM_SAMPLES="${1:-10}"
BASE_URL="${API_BASE_URL:-http://localhost:8000}"
RESULTS_DIR="$(cd "$(dirname "$0")" && pwd)/results"
DATE_TAG="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE_BASENAME="api_latency_${DATE_TAG}.json"

# Preflight: check that the swarm is running
if ! docker compose ps --status running 2>/dev/null | grep -q 'api'; then
    echo "ERROR: Docker swarm is not running or 'api' service not found."
    echo "Run 'docker compose up -d' first."
    exit 1
fi

# Ensure results directory exists
mkdir -p "$RESULTS_DIR"

# Check required tools
for cmd in curl python3 sort; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: Required tool '$cmd' not found on PATH."
        exit 1
    fi
done

# Endpoint list (name, method, URL, optional POST body)
# Use read-only/idempotent endpoints; avoid mutating production data
ENDPOINTS=(
    "health|GET|${BASE_URL}/api/health/live|"
    "health_ready|GET|${BASE_URL}/api/health/ready|"
    "agents_list|GET|${BASE_URL}/api/agents/instances|"
    "agent_types|GET|${BASE_URL}/api/agents/available|"
    "config|GET|${BASE_URL}/api/config|"
)

# ---------------------------------------------------------------------------
# Helper: compute p50/p95/p99 from newline-delimited ms values on stdin
# Delegates to compute_percentiles.py for reliable arithmetic.
# ---------------------------------------------------------------------------
compute_percentiles() {
    python3 "$(cd "$(dirname "$0")" && pwd)/compute_percentiles.py"
}

# ---------------------------------------------------------------------------
# Sample a single endpoint and return latencies as newline-delimited ms
# ---------------------------------------------------------------------------
sample_endpoint() {
    local method="$1" url="$2" body="$3"
    local -a latencies=()
    for ((i=0; i<NUM_SAMPLES; i++)); do
        local start_ms end_ms elapsed
        start_ms=$(python3 -c "import time; print(int(time.time()*1000))" 2>/dev/null || echo 0)

        case "$method" in
            GET)
                curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" > /dev/null
                ;;
            POST)
                curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" \
                    --connect-timeout 5 --max-time 10 -d "${body:-{}}" "$url" > /dev/null
                ;;
            DELETE)
                curl -s -o /dev/null -w "%{http_code}" -X DELETE --connect-timeout 5 --max-time 10 "$url" > /dev/null
                ;;
        esac

        end_ms=$(python3 -c "import time; print(int(time.time()*1000))" 2>/dev/null || echo 0)
        elapsed=$((end_ms - start_ms))
        echo "$elapsed"
    done
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
echo "=== API Latency Benchmark ==="
echo "Samples per endpoint: $NUM_SAMPLES"
echo "Base URL: $BASE_URL"
echo ""

# Build results JSON array
RESULTS_JSON="["
SEPARATOR=""

for entry in "${ENDPOINTS[@]}"; do
    IFS='|' read -r name method url body <<< "$entry"
    echo "→ Sampling $method $url…"

    latencies=$(sample_endpoint "$method" "$url" "$body")
    percentiles=$(echo "$latencies" | compute_percentiles)

    RESULTS_JSON+="${SEPARATOR}{\"endpoint\":\"${name}\",\"method\":\"${method}\",\"url\":\"${url}\",\"percentiles\":${percentiles}}"
    SEPARATOR=","
done

RESULTS_JSON+="]"

# Write output — use python3 for JSON formatting. Convert MSYS path to Windows path for Python.
mkdir -p "$RESULTS_DIR"
export RESULTS_DIR OUTPUT_FILE_BASENAME
echo "$RESULTS_JSON" | python3 -c "
import sys, json, os
data = json.loads(sys.stdin.read())
results_dir = os.environ['RESULTS_DIR']
basename = os.environ['OUTPUT_FILE_BASENAME']
# Convert MSYS /c/... path to Windows C:/... path if needed
if results_dir.startswith('/') and '/' in results_dir[2:]:
    drive = results_dir[1].upper()
    rest = results_dir[3:]
    results_dir = f'{drive}:{rest}'
out = os.path.join(results_dir, basename)
os.makedirs(results_dir, exist_ok=True)
with open(out, 'w') as f:
    json.dump(data, f, indent=2)
print(f'Results written to: {out}')
"
echo ""
echo "Results written to: ${RESULTS_DIR}/${OUTPUT_FILE_BASENAME}"
