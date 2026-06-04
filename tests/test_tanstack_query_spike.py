"""Spike for Phase 2B.3 TanStack Query + openapi-typescript migration.

The TanStack Query cutover is a frontend-only change; the spike
is a documentation test that verifies the migration plan.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_tanstack_spike_doc_exists():
    """The migration plan doc exists at swarm-dashboard/src/data/tanstack_query_spike.md."""
    doc = REPO_ROOT / "swarm-dashboard" / "src" / "data" / "tanstack_query_spike.md"
    assert doc.exists(), f"Migration plan not found at {doc}"
    content = doc.read_text()
    assert "TanStack Query" in content
    assert "openapi-typescript" in content


def test_candidate_files_inventory():
    """The candidate files inventory is consistent with the plan."""
    expected_api = [
        "agents.ts",
        "deliberation.ts",
        "configuration.ts",
        "wizard.ts",
        "consensus.ts",
        "client.ts",
        "consciousness.ts",
        "autonomous.ts",
        "metrics.ts",
        "mcp.ts",
        "events.ts",
        "observability.ts",
    ]
    doc = (
        REPO_ROOT / "swarm-dashboard" / "src" / "data" / "tanstack_query_spike.md"
    )
    content = doc.read_text()
    for f in expected_api:
        assert f in content, f"{f} not mentioned in tanstack_query_spike.md"
