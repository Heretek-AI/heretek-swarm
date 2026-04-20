"""Tests for duplicate class detection.

Uses workflow/strategies.py as a fixture — it contains a duplicate
WorkflowExecutionResult class at lines 29 and 60.
"""

from pathlib import Path

from heretek_swarm.audit import scan_file
from heretek_swarm.audit.stub_patterns import _scan_ast

# Absolute path to the source file containing the duplicate class.
# The repo root contains a "heretek-swarm/" subdirectory.
_STRATEGIES_PATH = (
    Path(__file__).parent.parent.parent
    / "heretek-swarm"
    / "heretek_swarm"
    / "workflow"
    / "strategies.py"
)


class TestDuplicateClassDetection:
    """Tests that duplicate class definitions are detected by AST analysis."""

    def test_strategies_file_exists(self) -> None:
        """Sanity check: the strategies file must exist."""
        assert _STRATEGIES_PATH.exists(), (
            f"strategies.py not found at {_STRATEGIES_PATH}. "
            "Ensure the audit package and test are run from the repo root."
        )

    def test_strategies_file_has_duplicate_class(self) -> None:
        """Confirm that workflow/strategies.py actually has a duplicate class."""
        content = _STRATEGIES_PATH.read_text(encoding="utf-8")
        count = content.count("class WorkflowExecutionResult")
        assert count == 2, (
            f"Expected 2 occurrences of 'class WorkflowExecutionResult' in "
            f"{_STRATEGIES_PATH}, found {count}. "
            "Update this test if the source file changes."
        )

    def test_ast_scan_finds_duplicate_class(self) -> None:
        """The AST scanner must return a DuplicateClassDefinition finding."""
        content = _STRATEGIES_PATH.read_text(encoding="utf-8")
        findings = _scan_ast(content, str(_STRATEGIES_PATH), patterns=None)

        dup_names = [
            f for f in findings if f.pattern_name == "DuplicateClassDefinition"
        ]
        assert len(dup_names) >= 1, (
            "Expected at least one DuplicateClassDefinition finding for "
            f"{_STRATEGIES_PATH}, but got none. "
            "Check that the AST scanner is correctly identifying duplicate class names."
        )

    def test_scan_file_finds_duplicate_class(self) -> None:
        """scan_file() must surface a CRITICAL or INFO finding for the duplicate class."""
        findings = scan_file(_STRATEGIES_PATH)
        dup_names = [
            f for f in findings if f.pattern_name == "DuplicateClassDefinition"
        ]
        assert len(dup_names) >= 1

    def test_duplicate_class_has_workflow_execution_result_name(self) -> None:
        """The finding description must mention WorkflowExecutionResult."""
        findings = scan_file(_STRATEGIES_PATH)
        dup_findings = [
            f for f in findings if f.pattern_name == "DuplicateClassDefinition"
        ]
        assert len(dup_findings) >= 1
        # At least one finding should mention the duplicated class name
        descriptions = [f.description for f in dup_findings]
        assert any("WorkflowExecutionResult" in d for d in descriptions)

    def test_scan_file_returns_findings_for_strategies(self) -> None:
        """Sanity: scan_file on strategies.py returns at least one finding."""
        findings = scan_file(_STRATEGIES_PATH)
        assert len(findings) >= 1, (
            f"Expected at least one finding in {_STRATEGIES_PATH}, got none."
        )
