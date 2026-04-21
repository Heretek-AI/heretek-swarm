"""Tests for duplicate class detection.

Uses workflow/strategies.py as a fixture. After S03 cleanup,
strategies.py has exactly one WorkflowExecutionResult class definition
(no duplicate).
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

    def test_strategies_file_has_single_class(self) -> None:
        """Confirm that workflow/strategies.py has exactly one WorkflowExecutionResult class."""
        content = _STRATEGIES_PATH.read_text(encoding="utf-8")
        count = content.count("class WorkflowExecutionResult")
        assert count == 1, (
            f"Expected 1 occurrence of 'class WorkflowExecutionResult' in "
            f"{_STRATEGIES_PATH}, found {count}. "
            "Update this test if the source file changes."
        )

    def test_ast_scan_finds_no_duplicate_class(self) -> None:
        """After S03 cleanup, the AST scanner should find zero DuplicateClassDefinition findings."""
        content = _STRATEGIES_PATH.read_text(encoding="utf-8")
        findings = _scan_ast(content, str(_STRATEGIES_PATH), patterns=None)

        dup_names = [
            f for f in findings if f.pattern_name == "DuplicateClassDefinition"
        ]
        assert len(dup_names) == 0, (
            "Expected zero DuplicateClassDefinition findings for "
            f"{_STRATEGIES_PATH} after cleanup, but got {len(dup_names)}. "
            "The duplicate class has been removed; update this test if needed."
        )

    def test_scan_file_finds_no_duplicate_class(self) -> None:
        """After S03 cleanup, scan_file() must return zero DuplicateClassDefinition findings."""
        findings = scan_file(_STRATEGIES_PATH)
        dup_names = [
            f for f in findings if f.pattern_name == "DuplicateClassDefinition"
        ]
        assert len(dup_names) == 0, (
            f"Expected zero DuplicateClassDefinition findings for {_STRATEGIES_PATH} "
            f"after cleanup, but got {len(dup_names)}."
        )

    def test_single_class_is_workflow_execution_result(self) -> None:
        """Verify strategies.py contains exactly one WorkflowExecutionResult class definition."""
        content = _STRATEGIES_PATH.read_text(encoding="utf-8")
        count = content.count("class WorkflowExecutionResult")
        assert count == 1, (
            f"Expected exactly one WorkflowExecutionResult class in "
            f"{_STRATEGIES_PATH}, found {count}."
        )

    def test_scan_file_returns_findings_for_strategies(self) -> None:
        """Sanity: scan_file on strategies.py returns at least one finding."""
        findings = scan_file(_STRATEGIES_PATH)
        assert len(findings) >= 1, (
            f"Expected at least one finding in {_STRATEGIES_PATH}, got none."
        )
