"""Spike for Phase 3C pyphi + pymdp IIT/FEP migration.

The spike is a documentation test that records the Python 3.14
incompatibility of pyphi 1.x — this finding is the primary
output of the spike.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_spike_doc_exists():
    """The IIT/FEP spike doc exists at consciousness/iit_fep_spike.md."""
    doc = REPO_ROOT / "backend" / "heretek_swarm" / "consciousness" / "iit_fep_spike.md"
    assert doc.exists()
    content = doc.read_text()
    # The doc should call out the Python 3.14 incompatibility.
    assert "Python 3.14" in content or "Python 3.10" in content
    assert "pyphi" in content
    assert "pymdp" in content


def test_pyphi_python_3_14_incompatibility_documented():
    """The doc documents the pyphi 1.x Python 3.14 incompatibility."""
    doc = REPO_ROOT / "backend" / "heretek_swarm" / "consciousness" / "iit_fep_spike.md"
    content = doc.read_text()
    # The doc should explicitly call out the ImportError
    assert "Iterable" in content or "collections" in content
    # The doc should recommend deferring
    assert "DEFER" in content or "blocked" in content.lower()
