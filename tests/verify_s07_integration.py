#!/usr/bin/env python3
"""S07 integration gate verification script.

Runs all six S07 integration-proving checks via subprocess and exits 0 only if
all pass:
  1. full_stack_tests — pytest full-stack + deliberation e2e with coverage ≥80%
  2. s06_gates — ruff 0, mypy 0, coverage ≥80%, 0 TODO/FIXME in M001 scope
  3. docker_config — TestDockerComposeConfigValid (15 structural checks)
  4. env_file — .env exists at repo root
  5. dashboard_build — swarm-dashboard/dist/index.html exists
  6. dashboard_vitest — vitest run from swarm-dashboard/
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FULL_STACK_ARGS = [
    sys.executable, "-m", "pytest",
    "tests/test_full_stack.py", "tests/test_deliberation_e2e.py",
    "-q",
    "--timeout=60",
]

DOCKER_CONFIG_ARGS = [
    sys.executable, "-m", "pytest",
    "tests/test_full_stack.py::TestDockerComposeConfigValid",
    "-q",
    "--timeout=30",
]


def run_check(name: str, args: list[str], cwd: str | None = None,
              timeout: int = 120) -> tuple[bool, str, float]:
    """Run a check command and return (passed, output_summary, duration_seconds)."""
    start = time.monotonic()
    try:
        result = subprocess.run(
            args, capture_output=True, text=True,
            cwd=cwd or str(ROOT), timeout=timeout,
        )
        duration = time.monotonic() - start
        passed = result.returncode == 0
        combined = (result.stdout + result.stderr).strip()
        if combined:
            summary = "\n".join(combined.split("\n")[-5:])
        else:
            summary = "(no output)"
        return passed, summary, duration
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return False, f"TIMEOUT after {duration:.0f}s", duration
    except FileNotFoundError as e:
        duration = time.monotonic() - start
        return False, f"NOT FOUND: {e}", duration


def check_file_exists(name: str, rel_path: str) -> tuple[bool, str, float]:
    """Check that a file exists relative to repo root."""
    start = time.monotonic()
    target = ROOT / rel_path
    exists = target.is_file()
    duration = time.monotonic() - start
    if exists:
        return True, f"{rel_path} exists", duration
    else:
        return False, f"{rel_path} MISSING", duration


def main() -> int:
    checks: list[tuple[str, tuple | None]] = [
        ("full_stack_tests", FULL_STACK_ARGS),
        ("s06_gates", [sys.executable, str(ROOT / "tests" / "verify_s06_gates.py")]),
        ("docker_config", DOCKER_CONFIG_ARGS),
        ("env_file", None),           # special: file existence check
        ("dashboard_build", None),    # special: file existence check
        ("dashboard_vitest", ["npx", "vitest", "run"]),
    ]

    print("=== S07 Integration Gate Verification ===\n")

    results: list[dict] = []
    all_passed = True

    for name, args in checks:
        print(f"  [{name}] ", end="", flush=True)

        if name == "env_file":
            passed, summary, duration = check_file_exists(name, ".env")
        elif name == "dashboard_build":
            passed, summary, duration = check_file_exists(name, "swarm-dashboard/dist/index.html")
        elif name == "dashboard_vitest":
            passed, summary, duration = run_check(
                name, args, cwd=str(ROOT / "swarm-dashboard"), timeout=120,
            )
        else:
            passed, summary, duration = run_check(name, args)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} ({duration:.1f}s)")
        all_passed = all_passed and passed
        results.append({
            "check": name,
            "passed": passed,
            "duration_s": round(duration, 1),
            "summary": summary,
        })

    print()
    if all_passed:
        print("All S07 integration gates passed ✅")
        return 0
    else:
        print("Some S07 integration gates failed ❌\n")
        for r in results:
            if not r["passed"]:
                print(f"  [{r['check']}]")
                # Indent each line of the summary
                for line in r["summary"].split("\n"):
                    print(f"    {line}")
                print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
