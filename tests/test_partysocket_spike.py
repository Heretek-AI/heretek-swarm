"""Spike for Phase 2B.5 partysocket migration."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_spike_doc_exists():
    doc = REPO_ROOT / "swarm-dashboard" / "src" / "realtime" / "partysocket_spike.md"
    assert doc.exists()
    content = doc.read_text()
    assert "partysocket" in content


def test_candidate_files_inventory():
    expected = [
        "useWebSocket.ts",
        "useConsensusWebSocket.ts",
        "useConsciousnessWebSocket.ts",
        "useA2AMessages.ts",
        "useWorkflowProgress.ts",
    ]
    doc = REPO_ROOT / "swarm-dashboard" / "src" / "realtime" / "partysocket_spike.md"
    content = doc.read_text()
    for f in expected:
        assert f in content
