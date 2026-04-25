"""
Tests for the wizard CLI command.

Verifies the wizard command opens the correct URL in browser
and handles the headless fallback gracefully.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from heretek_swarm.cli import cli as cli_group


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def cli():
    """Create the CLI group for testing."""
    return cli_group


# =============================================================================
# Wizard Command Tests
# =============================================================================

class TestWizardCommand:
    """Tests for the heretek-swarm wizard command."""

    def test_wizard_command_opens_correct_url(self, cli):
        """Test that wizard command calls webbrowser.open with the correct URL."""
        runner = CliRunner()
        with patch("webbrowser.open") as mock_open:
            result = runner.invoke(
                cli,
                ["wizard"],
            )

            # Should have called webbrowser.open with the wizard URL
            assert mock_open.called, "webbrowser.open was not called"
            call_args = mock_open.call_args
            assert call_args is not None
            args, kwargs = call_args
            # First positional argument should be the wizard URL
            assert len(args) >= 1
            assert args[0] == "http://localhost:3000", (
                f"Expected webbrowser.open to be called with 'http://localhost:3000', "
                f"got '{args[0]}'"
            )

    def test_wizard_command_echoes_url_when_browser_opens(self, cli):
        """Test that wizard command prints the URL when browser opens successfully."""
        runner = CliRunner()
        with patch("webbrowser.open") as mock_open:
            result = runner.invoke(
                cli,
                ["wizard"],
            )

            # Should echo the URL to the user
            assert "http://localhost:3000" in result.output
            assert result.exit_code == 0

    def test_wizard_headless_fallback(self, cli):
        """Test that wizard command echoes URL and exits 0 when browser.open raises."""
        runner = CliRunner()
        with patch("webbrowser.open") as mock_open:
            # Simulate no browser available
            mock_open.side_effect = Exception("No browser found")

            result = runner.invoke(
                cli,
                ["wizard"],
            )

            # Should echo the URL instead
            assert "http://localhost:3000" in result.output
            assert "No browser available" in result.output
            # Should exit cleanly (sys.exit(0) is called)
            assert result.exit_code == 0

    def test_wizard_headless_fallback_calls_sys_exit(self, cli):
        """Test that headless fallback calls sys.exit(0) to terminate."""
        runner = CliRunner()
        with patch("webbrowser.open") as mock_open:
            mock_open.side_effect = Exception("No browser found")

            # Patch sys.exit to capture the call
            with patch("sys.exit") as mock_exit:
                result = runner.invoke(
                    cli,
                    ["wizard"],
                )

                # sys.exit(0) should have been called for headless fallback
                assert mock_exit.called, "sys.exit was not called in headless fallback"
                args, kwargs = mock_exit.call_args
                assert args[0] == 0, "sys.exit was called with non-zero code"

    def test_wizard_command_help(self, cli):
        """Test that wizard command shows help."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["wizard", "--help"],
        )

        assert result.exit_code == 0
        assert "browser" in result.output.lower()
        assert "http://localhost:3000" in result.output

    def test_wizard_command_listed_in_cli_help(self, cli):
        """Test that wizard command appears in CLI help."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--help"],
        )

        assert "wizard" in result.output