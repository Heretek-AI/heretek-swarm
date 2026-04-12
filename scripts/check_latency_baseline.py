#!/usr/bin/env python3
"""
Latency baseline checker for benchmark results.

Agent Gamma - QA and Validation Lead
Flags any module failing the <100ms message latency baseline for refactoring.

Usage:
    python scripts/check_latency_baseline.py benchmark-results.json 100
"""

import json
import sys
from pathlib import Path


def check_latency_baseline(benchmark_file: Path, baseline_ms: float) -> int:
    """
    Check benchmark results against latency baseline.

    Returns:
        0 if all benchmarks pass
        1 if any benchmark exceeds baseline (flag for refactoring)
    """
    if not benchmark_file.exists():
        return 1

    with open(benchmark_file) as f:
        results = json.load(f)

    failures = []
    passes = []

    benchmarks = results.get("benchmarks", [])

    for bench in benchmarks:
        name = bench.get("name", "unknown")
        # Convert to milliseconds (benchmarks usually in seconds)
        mean_time_s = bench.get("stats", {}).get("mean", 0)
        mean_time_ms = mean_time_s * 1000

        if mean_time_ms > baseline_ms:
            failures.append({
                "name": name,
                "mean_ms": mean_time_ms,
                "baseline_ms": baseline_ms,
                "overage_ms": mean_time_ms - baseline_ms,
                "overage_pct": ((mean_time_ms - baseline_ms) / baseline_ms) * 100,
            })
        else:
            passes.append({
                "name": name,
                "mean_ms": mean_time_ms,
            })

    # Print report

    if passes:
        for _p in passes:
            pass

    if failures:
        for f in failures:
            pass


    if failures:
        return 1

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    benchmark_path = Path(sys.argv[1])
    baseline = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0

    sys.exit(check_latency_baseline(benchmark_path, baseline))
