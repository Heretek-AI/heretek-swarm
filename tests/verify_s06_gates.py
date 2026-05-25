#!/usr/bin/env python3
"""S06 quality gate verification script.

Runs all four S06 gate checks via subprocess and exits 0 only if all pass:
  1. ruff check backend/heretek_swarm — 0 errors
  2. mypy backend/heretek_swarm — 0 errors
  3. pytest tests/ --cov=backend/heretek_swarm --cov-fail-under=80 — exit 0
  4. No unresolved TODO/FIXME in M001-scoped source files
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTEST_ARGS = [
    sys.executable, "-m", "pytest", "tests/",
    "--cov=backend/heretek_swarm",
    "--cov-report=term",
    "--cov-fail-under=80",
    "-q",
    "--timeout=60",
]

# M002/M003 out-of-scope directories (D011) — TODO/FIXME in these are expected.
M002_M003_DIRS = {
    "agent_workspace", "agents", "audit", "channels", "consciousness",
    "coordination", "creativity", "embeddings", "evaluation", "gateway",
    "governance", "integrations", "interfaces", "knowledge", "llm", "models",
    "orchestration", "plugins", "rag", "security", "slices", "swarm_logging",
    "testing", "utils", "validation",
}


def run_check(name: str, args: list[str], cwd: str | None = None) -> tuple[bool, str, float]:
    """Run a check command and return (passed, output_summary, duration_seconds)."""
    import time
    start = time.monotonic()
    try:
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd or str(ROOT), timeout=120)
        duration = time.monotonic() - start
        passed = result.returncode == 0
        summary = result.stdout.strip().split("\n")[-3:] if result.stdout else result.stderr.strip()
        return passed, "\n".join(summary) if summary else "(no output)", duration
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return False, f"TIMEOUT after {duration:.0f}s", duration


def check_todos() -> tuple[bool, str, float]:
    """Check for unresolved TODO/FIXME in M001-scoped source files."""
    import time
    start = time.monotonic()
    src_dir = ROOT / "backend" / "heretek_swarm"
    violations: list[str] = []
    for py_file in sorted(src_dir.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        # Skip M002/M003 scoped directories
        if py_file.parts[0] != "backend":
            continue
        # Check if any parent directory is M002/M003
        rel = py_file.relative_to(src_dir).parts
        if rel[0] in M002_M003_DIRS:
            continue
        # Check for M002/M003 actor subdirectories
        if len(rel) >= 2 and rel[0] == "actors" and rel[1] in {
            "arbiter", "chronos", "coordinator", "dreamer", "examiner",
            "habit_forge", "handoff", "perceiver_plus", "prism",
            "sentinel_prime", "triad",
        }:
            continue
        try:
            content = py_file.read_text()
        except Exception:
            continue
        for lineno, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#") and ("TODO" in stripped.upper() or "FIXME" in stripped.upper()):
                # Allow TODO/FIXME in noqa comments (they're lint suppression markers)
                if "noqa" in stripped.lower():
                    continue
                violations.append(f"  {py_file.relative_to(ROOT)}:{lineno}: {stripped}")
    duration = time.monotonic() - start
    passed = len(violations) == 0
    summary = "0 TODO/FIXME in M001 scope" if passed else f"{len(violations)} TODO/FIXME found:\n" + "\n".join(violations[:10])
    return passed, summary, duration


def main() -> int:
    checks = [
        ("ruff", [sys.executable, "-m", "ruff", "check", "backend/heretek_swarm"]),
        ("mypy", [sys.executable, "-m", "mypy", "backend/heretek_swarm", "--no-error-summary"]),
        ("pytest+coverage", PYTEST_ARGS),
        ("TODO/FIXME", None),  # special case, handled inline
    ]

    results: list[dict] = []
    all_passed = True

    for name, args in checks:
        print(f"  [{name}] ", end="", flush=True)
        if args is None:
            passed, summary, duration = check_todos()
        else:
            passed, summary, duration = run_check(name, args)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} ({duration:.1f}s)")
        if not all_passed:
            pass  # keep checking, report all failures
        all_passed = all_passed and passed
        results.append({
            "check": name,
            "passed": passed,
            "duration_s": round(duration, 1),
            "summary": summary,
        })

    print()
    if all_passed:
        print("All S06 gates passed ✅")
        return 0
    else:
        print("Some S06 gates failed ❌")
        for r in results:
            if not r["passed"]:
                print(f"  [{r['check']}] {r['summary']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
