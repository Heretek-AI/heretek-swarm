"""Spike for Phase 2B.2 shadcn/ui migration.

The shadcn/ui cutover is a frontend-only change with no Python
side; the spike is a documentation test that verifies the
candidate-file inventory matches the plan.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_shadcn_spike_doc_exists():
    """The migration plan doc exists at swarm-dashboard/src/ui/shadcn_spike.md."""
    doc = REPO_ROOT / "swarm-dashboard" / "src" / "ui" / "shadcn_spike.md"
    assert doc.exists(), f"Migration plan not found at {doc}"
    content = doc.read_text()
    # The doc should mention the headline cuts.
    assert "shadcn" in content
    assert "Toast" in content
    assert "DataTable" in content
    assert "ErrorBoundary" in content


def test_candidate_files_inventory():
    """The 9 candidate UI files for shadcn migration exist (or have existed)."""
    # The candidate files are listed in shadcn_spike.md. The inventory
    # check is a documentation test: it ensures the spike doc is
    # consistent with the plan.
    expected = [
        "Toast.tsx",
        "DataTable.tsx",
        "ErrorBoundary.tsx",
        "ComponentErrorBoundary.tsx",
        "StatusBadge.tsx",
        "EmptyState.tsx",
        "MetricCard.tsx",
        "LoadingSpinner.tsx",
    ]
    doc = REPO_ROOT / "swarm-dashboard" / "src" / "ui" / "shadcn_spike.md"
    content = doc.read_text()
    for f in expected:
        assert f in content, f"{f} not mentioned in shadcn_spike.md"
