"""
Tests for the research/ tier namespace.

Per M-arch PR #8: verify the research package re-exports the
consciousness and collective modules correctly. New code should
import from heretek_swarm.research; existing imports from the
legacy locations continue to work.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def research():
    return importlib.import_module("heretek_swarm.research")


class TestResearchPackageImports:
    def test_consciousness_modules_reexported(self, research) -> None:
        """All 9 consciousness modules re-exported as attributes."""
        assert hasattr(research, "iit_phi")
        assert hasattr(research, "iit")
        assert hasattr(research, "gwt")
        assert hasattr(research, "gwt_deliberation")
        assert hasattr(research, "fep")
        assert hasattr(research, "fep_active_inference")
        assert hasattr(research, "self_model")
        assert hasattr(research, "introspection")
        assert hasattr(research, "ast")

    def test_collective_modules_reexported(self, research) -> None:
        """All 5 collective modules re-exported as attributes."""
        assert hasattr(research, "emergent_detection")
        assert hasattr(research, "emergent_detection_types")
        assert hasattr(research, "emergence_analyzer")
        assert hasattr(research, "evolution_engine")
        assert hasattr(research, "agency_tracking")

    def test_reexports_are_same_module_objects(self, research) -> None:
        """Re-exports are the same module object as the canonical import."""
        from heretek_swarm.collective import emergent_detection as canon_emergent
        from heretek_swarm.consciousness import iit_phi as canon_iit_phi

        assert research.iit_phi is canon_iit_phi
        assert research.emergent_detection is canon_emergent

    def test_dunder_all_contains_expected_modules(self, research) -> None:
        """__all__ lists all 14 re-exported modules."""
        expected = {
            "agency_tracking",
            "ast",
            "emergence_analyzer",
            "emergent_detection",
            "emergent_detection_types",
            "evolution_engine",
            "fep",
            "fep_active_inference",
            "gwt",
            "gwt_deliberation",
            "iit",
            "iit_phi",
            "introspection",
            "self_model",
        }
        assert set(research.__all__) == expected

    def test_research_module_has_deprecation_marker(self, research) -> None:
        """The research package docstring contains a deprecation marker."""
        assert research.__doc__ is not None
        assert "deprecated" in research.__doc__.lower()

    def test_research_readme_exists(self) -> None:
        """A README.md documents the research tier."""
        import os

        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "backend",
            "heretek_swarm",
            "research",
            "README.md",
        )
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "research-grade" in content.lower()
        assert "Migration status" in content

    def test_legacy_imports_still_work(self) -> None:
        """Legacy imports from heretek_swarm.consciousness still work."""
        from heretek_swarm.collective import emergent_detection, evolution_engine
        from heretek_swarm.consciousness import gwt, iit_phi

        assert iit_phi is not None
        assert gwt is not None
        assert emergent_detection is not None
        assert evolution_engine is not None
