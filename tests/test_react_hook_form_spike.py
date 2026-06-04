"""Spike for Phase 2B.4 react-hook-form + zod migration."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_spike_doc_exists():
    """The migration plan doc exists at swarm-dashboard/src/forms/react_hook_form_spike.md."""
    doc = REPO_ROOT / "swarm-dashboard" / "src" / "forms" / "react_hook_form_spike.md"
    assert doc.exists()
    content = doc.read_text()
    assert "react-hook-form" in content
    assert "zod" in content


def test_candidate_files_inventory():
    """The candidate files inventory is consistent with the plan."""
    expected = [
        "SetupWizard.tsx",
        "ModelGarage.tsx",
        "NodeConfigPanel.tsx",
        "AgentConfigPanel.tsx",
        "setupValidation.ts",
    ]
    doc = REPO_ROOT / "swarm-dashboard" / "src" / "forms" / "react_hook_form_spike.md"
    content = doc.read_text()
    for f in expected:
        assert f in content, f"{f} not mentioned in spike doc"
