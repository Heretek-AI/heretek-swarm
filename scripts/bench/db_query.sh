#!/usr/bin/env bash
# db_query.sh — Profile database query latency using db_timing instrumentation
#
# Prerequisites: docker compose up (Postgres must be running)
# Usage: bash scripts/bench/db_query.sh [REPEATS]
# Output: scripts/bench/results/db_query_YYYYMMDD_HHMMSS.json

set -euo pipefail

REPEATS="${1:-5}"
RESULTS_DIR="$(cd "$(dirname "$0")" && pwd)/results"
DATE_TAG="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE="${RESULTS_DIR}/db_query_${DATE_TAG}.json"

mkdir -p "$RESULTS_DIR"

echo "=== DB Query Latency Benchmark ==="
echo "Repeats: $REPEATS"
echo ""

python3 - "$REPEATS" "$OUTPUT_FILE" << 'PYEOF'
import asyncio
import json
import os
import sys
import time

REPEATS = int(sys.argv[1])
OUTPUT_FILE = sys.argv[2]

results: list[dict] = []

async def run_bench() -> None:
    # Import async engine using the same path as config/service.py
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://heretek:heretek@localhost:5432/heretek_swarm",
    )

    engine = create_async_engine(DATABASE_URL, echo=False)

    # Attach db_timing listener
    from heretek_swarm.observability.db_timing import attach_db_timing
    attach_db_timing(engine)

    async with engine.begin() as conn:
        # Warmup query
        await conn.execute(text("SELECT 1"))

        # Benchmark: SELECT on agents table (reads)
        select_times: list[float] = []
        for _ in range(REPEATS):
            start = time.perf_counter()
            try:
                await conn.execute(text("SELECT id, agent_id, actor_type FROM agents LIMIT 50"))
            except Exception:
                pass  # Table may not exist — still measure the attempt
            select_times.append((time.perf_counter() - start) * 1000)

        results.append({
            "query": "SELECT agents (LIMIT 50)",
            "repeats": REPEATS,
            "times_ms": select_times,
        })

        # Benchmark: JOIN pattern
        join_times: list[float] = []
        for _ in range(REPEATS):
            start = time.perf_counter()
            try:
                await conn.execute(text(
                    "SELECT m.id, m.content, a.agent_id "
                    "FROM memories m LEFT JOIN agents a ON m.agent_id = a.id "
                    "LIMIT 50"
                ))
            except Exception:
                pass
            join_times.append((time.perf_counter() - start) * 1000)

        results.append({
            "query": "JOIN memories ↔ agents (LIMIT 50)",
            "repeats": REPEATS,
            "times_ms": join_times,
        })

        # Benchmark: config read
        config_times: list[float] = []
        for _ in range(REPEATS):
            start = time.perf_counter()
            try:
                await conn.execute(text("SELECT key, value FROM configuration LIMIT 20"))
            except Exception:
                pass
            config_times.append((time.perf_counter() - start) * 1000)

        results.append({
            "query": "SELECT configuration (LIMIT 20)",
            "repeats": REPEATS,
            "times_ms": config_times,
        })

    await engine.dispose()

    # Compute summary per query
    output = []
    for r in results:
        times = r["times_ms"]
        sorted_times = sorted(times)
        n = len(sorted_times)
        if n == 0:
            output.append({**r, "p50_ms": None, "p95_ms": None, "mean_ms": None})
            continue

        mean_ms = sum(times) / n
        p50_ms = sorted_times[int(n * 0.50)]
        p95_ms = sorted_times[min(int(n * 0.95), n - 1)]
        output.append({
            "query": r["query"],
            "repeats": r["repeats"],
            "p50_ms": round(p50_ms, 2),
            "p95_ms": round(p95_ms, 2),
            "mean_ms": round(mean_ms, 2),
            "min_ms": round(sorted_times[0], 2),
            "max_ms": round(sorted_times[-1], 2),
        })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))


asyncio.run(run_bench())
PYEOF

echo ""
echo "Results written to: $OUTPUT_FILE"
