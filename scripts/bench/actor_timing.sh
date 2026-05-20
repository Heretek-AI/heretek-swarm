#!/usr/bin/env bash
# actor_timing.sh — Run pytest-benchmark suite for actor message processing throughput
#
# Prerequisites: pip install pytest-benchmark (in dev deps)
# Usage: bash scripts/bench/actor_timing.sh
# Output: scripts/bench/results/actor_timing_YYYYMMDD_HHMMSS.json

set -euo pipefail

RESULTS_DIR="$(cd "$(dirname "$0")" && pwd)/results"
DATE_TAG="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE="${RESULTS_DIR}/actor_timing_${DATE_TAG}.json"

mkdir -p "$RESULTS_DIR"

echo "=== Actor Message Processing Benchmark ==="
echo ""

# Run benchmarks
python3 -m pytest tests/test_bench_actor_throughput.py \
    -k bench_actor_throughput \
    --benchmark-only \
    --benchmark-json="$OUTPUT_FILE" \
    -v \
    --no-header \
    -p no:warnings

echo ""
echo "Results written to: $OUTPUT_FILE"
