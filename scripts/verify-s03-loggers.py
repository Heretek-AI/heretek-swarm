#!/usr/bin/env python3
"""verify-s03-loggers.py — Check that every backend .py file >100 lines has a structlog logger.

Walks ``backend/heretek_swarm/``, counts lines in each ``.py`` file, and
reports any file exceeding 100 lines that lacks ``get_logger``.  Exits 0
when every such file is instrumented, 1 otherwise.

Usage:
    python3 scripts/verify-s03-loggers.py
"""

from __future__ import annotations

import os
import sys

BASE = "backend/heretek_swarm"
MIN_LINES = 100


def _has_logger(path: str) -> bool:
    """Return True if *path* contains a ``get_logger`` call with a logger variable."""
    try:
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return True  # skip unreadable files

    # Must mention get_logger and have a logger = ... assignment
    return "get_logger" in content and ("logger =" in content or "logger=" in content)


def main() -> int:
    missing: list[str] = []
    total_py_files = 0
    checked = 0

    for root, _dirs, files in os.walk(BASE):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            total_py_files += 1
            path = os.path.join(root, fn)

            # Count lines
            try:
                with open(path, encoding="utf-8") as fh:
                    line_count = sum(1 for _ in fh)
            except OSError:
                continue

            if line_count <= MIN_LINES:
                continue

            checked += 1
            if not _has_logger(path):
                rel = os.path.relpath(path)
                missing.append(rel)

    if missing:
        print(f"FAIL: {len(missing)} file(s) > {MIN_LINES} lines lack a structured logger:\n")
        for rel in sorted(missing):
            print(f"   {rel}")
        print(f"\n   Total .py files: {total_py_files}, checked (>100 lines): {checked}")
        return 1

    print(f"PASS: All {checked} files > {MIN_LINES} lines have structured loggers "
          f"(total .py files: {total_py_files})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
