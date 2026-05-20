#!/usr/bin/env python3
"""Verify the final findings.json structure and content validity.

Usage:
    python3 scripts/bench/verify_findings.py

Exits with code 0 if findings.json is valid, code 1 otherwise.
"""

import json
import sys
import os

FINDINGS_PATH = os.path.join(
    os.path.dirname(__file__), "results", "findings.json"
)


def main() -> int:
    if not os.path.exists(FINDINGS_PATH):
        print(f"FAIL: findings.json not found at {FINDINGS_PATH}")
        return 1

    with open(FINDINGS_PATH) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"FAIL: Invalid JSON in findings.json: {e}")
            return 1

    problems = []

    # Top-level fields
    for field in ["task_id", "slice_id", "milestone_id", "findings", "totals", "scan_metadata"]:
        if field not in data:
            problems.append(f"Missing top-level field: {field}")

    # Totals
    totals = data.get("totals", {})
    for sev in ["critical", "moderate", "minor"]:
        if sev not in totals:
            problems.append(f"Missing severity in totals: {sev}")

    # Findings
    findings = data.get("findings", [])
    if not findings:
        problems.append("No findings in findings array")

    modalities_found = set()
    for i, f in enumerate(findings):
        fid = f.get("id", f"[{i}]")
        for field in ["id", "title", "domain", "severity", "description", "source", "evidence"]:
            if field not in f:
                problems.append(f"Finding {fid} missing field: {field}")
        if f.get("domain") != "performance":
            problems.append(f"Finding {fid} domain is '{f.get('domain')}', expected 'performance'")
        sev = f.get("severity", "")
        if sev not in ("critical", "moderate", "minor"):
            problems.append(f"Finding {fid} has invalid severity: {sev}")
        evidence = f.get("evidence", {})
        if "modality" in evidence:
            modalities_found.add(evidence["modality"])

    # Modality coverage
    required_modalities = {"api_latency", "actor_timing", "db_query", "static_analysis"}
    missing = required_modalities - modalities_found
    if missing:
        problems.append(f"Missing modalities: {missing}")

    # Totals consistency
    if totals.get("total", 0) != len(findings):
        problems.append(
            f"Totals mismatch: totals.total={totals.get('total')} != len(findings)={len(findings)}"
        )

    if problems:
        print("FAIL:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(
        f"OK: {len(findings)} findings across {len(modalities_found)} modalities "
        f"({', '.join(sorted(modalities_found))})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
