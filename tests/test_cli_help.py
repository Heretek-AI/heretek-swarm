"""Tests for CLI help text polish and 'did you mean?' error suggestions.

Verifies that per-command help text renders examples in a clean block
(not inline prose) and that misspelled commands produce actionable
suggestions using difflib.get_close_matches().
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from heretek_swarm.cli import cli

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner() -> CliRunner:
    """Return a Click CliRunner for invoking CLI commands."""
    return CliRunner()


# ---------------------------------------------------------------------------
# Per-command help: examples rendered cleanly
# ---------------------------------------------------------------------------


class TestCommandHelpExamples:
    """Each command that has examples should render them as a clean block
    in the epilog, not as inline prose in the docstring body."""

    @staticmethod
    def test_run_help_shows_examples_block(runner: CliRunner) -> None:
        """``heretek-swarm run --help`` should include an Examples section."""
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Examples:" in result.output

    @staticmethod
    def test_serve_help_shows_examples_block(runner: CliRunner) -> None:
        """``heretek-swarm serve --help`` should include an Examples section."""
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "Examples:" in result.output

    @staticmethod
    def test_deploy_help_shows_examples_block(runner: CliRunner) -> None:
        """``heretek-swarm deploy --help`` should include an Examples section."""
        result = runner.invoke(cli, ["deploy", "--help"])
        assert result.exit_code == 0
        assert "Examples:" in result.output

    @staticmethod
    def test_run_help_examples_are_not_in_docstring_body(runner: CliRunner) -> None:
        """The Examples block should appear after the option list (in the
        epilog), not mixed into the command description."""
        result = runner.invoke(cli, ["run", "--help"])
        output = result.output
        # Find the last occurrence of "Examples:" — it should be in the epilog
        # after the option list.
        examples_idx = output.rfind("Examples:")
        assert examples_idx > 0, "Examples block not found in help output"
        # The epilog comes after the options, so it should be near the end
        assert examples_idx > len(output) * 0.4, (
            "Examples block appears too early — likely inline in docstring body"
        )

    @staticmethod
    def test_serve_help_examples_include_all_variants(runner: CliRunner) -> None:
        """The serve help epilog should include usage variants."""
        result = runner.invoke(cli, ["serve", "--help"])
        assert "--host" in result.output
        assert "--port" in result.output


# ---------------------------------------------------------------------------
# 'Did you mean?' suggestions on misspelled commands
# ---------------------------------------------------------------------------


class TestDidYouMean:
    """Misspelled commands should suggest the closest valid command name."""

    @staticmethod
    def test_misspelled_run_suggests_run(runner: CliRunner) -> None:
        """``heretek-swarm rnu`` should suggest 'run'."""
        result = runner.invoke(cli, ["rnu"])
        assert result.exit_code != 0
        assert "Did you mean" in result.output or "did you mean" in result.output.lower()
        assert "'run'" in result.output

    @staticmethod
    def test_misspelled_status_suggests_status(runner: CliRunner) -> None:
        """``heretek-swarm statu`` should suggest 'status'."""
        result = runner.invoke(cli, ["statu"])
        assert result.exit_code != 0
        assert "Did you mean" in result.output or "did you mean" in result.output.lower()
        assert "'status'" in result.output

    @staticmethod
    def test_misspelled_serve_suggests_serve(runner: CliRunner) -> None:
        """``heretek-swarm serb`` should suggest 'serve'."""
        result = runner.invoke(cli, ["serb"])
        assert result.exit_code != 0
        assert "Did you mean" in result.output or "did you mean" in result.output.lower()
        assert "'serve'" in result.output

    @staticmethod
    def test_totally_unknown_command_shows_error(runner: CliRunner) -> None:
        """``heretek-swarm xyzabc`` should show an error, not crash."""
        result = runner.invoke(cli, ["xyzabc"])
        assert result.exit_code != 0
        assert "No such command" in result.output

    @staticmethod
    def test_valid_commands_still_work(runner: CliRunner) -> None:
        """Known commands should not trigger the 'did you mean' path."""
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Start the Heretek Swarm autonomous runtime" in result.output
