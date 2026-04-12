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
        print(f"❌ Benchmark file not found: {benchmark_file}")
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
    print("\n" + "=" * 60)
    print("LATENCY BASELINE CHECK REPORT")
    print("=" * 60)
    print(f"Baseline threshold: {baseline_ms}ms")
    print(f"Total benchmarks: {len(benchmarks)}")
    print(f"Passed: {len(passes)}")
    print(f"Failed: {len(failures)}")
    print("=" * 60)

    if passes:
        print("\n✅ PASSING BENCHMARKS:")
        for p in passes:
            print(f"  • {p['name']}: {p['mean_ms']:.2f}ms")

    if failures:
        print("\n🚨 FAILING BENCHMARKS - FLAG FOR REFACTORING:")
        for f in failures:
            print(f"  ❌ {f['name']}")
            print(f"     Mean: {f['mean_ms']:.2f}ms")
            print(f"     Overage: +{f['overage_ms']:.2f}ms ({f['overage_pct']:.1f}% over baseline)")

    print("\n" + "=" * 60)

    if failures:
        print("❌ LATENCY BASELINE CHECK FAILED")
        print(f"   {len(failures)} module(s) exceed {baseline_ms}ms baseline")
        print("   FLAG FOR REFACTORING per Phase Directives")
        return 1

    print("✅ ALL BENCHMARKS WITHIN LATENCY BASELINE")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_latency_baseline.py <benchmark-file> [baseline-ms]")
        print("  benchmark-file: Path to pytest-benchmark JSON output")
        print("  baseline-ms: Latency baseline in milliseconds (default: 100)")
        sys.exit(1)

    benchmark_path = Path(sys.argv[1])
    baseline = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0

    sys.exit(check_latency_baseline(benchmark_path, baseline))
