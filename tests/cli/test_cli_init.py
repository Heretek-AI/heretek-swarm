"""
Tests for the init CLI command.

Verifies the init command bootstraps ~/.heretek-swarm/.env from .env.example
and handles edge cases (existing file, missing .env.example, etc.).
"""

from __future__ import annotations

from pathlib import Path
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
# Init Command Tests
# =============================================================================

class TestInitCommand:
    """Tests for the heretek-swarm init command."""

    def test_init_command_creates_env_file(self, cli, tmp_path):
        """Test that init command creates ~/.heretek-swarm/.env from .env.example."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a fake .env.example in the isolated filesystem (CWD)
            env_example = Path(".env.example")
            env_example.write_text("DATABASE_URL=postgresql://localhost/heretek\nAPI_KEY=secret123\n")

            # Mock Path.home() to return our temp directory
            fake_home = tmp_path / "home"
            fake_home.mkdir()

            with patch("heretek_swarm.cli.Path.home", return_value=fake_home):
                result = runner.invoke(cli, ["init"])

        # Verify exit code
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify the config file was created
        config_file = fake_home / ".heretek-swarm" / ".env"
        assert config_file.exists(), f"Config file not created. Output: {result.output}"

        # Verify content was copied
        content = config_file.read_text()
        assert "DATABASE_URL" in content
        assert "API_KEY" in content

    def test_init_command_skips_existing_env(self, cli, tmp_path):
        """Test that init command skips when ~/.heretek-swarm/.env already exists."""
        runner = CliRunner()

        # Mock Path.home() to return our temp directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        # Pre-create the config file
        config_dir = fake_home / ".heretek-swarm"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / ".env"
        config_file.write_text("ALREADY_SET=existing\n")

        with runner.isolated_filesystem():
            # Create .env.example in CWD
            env_example = Path(".env.example")
            env_example.write_text("DATABASE_URL=original\n")

            with patch("heretek_swarm.cli.Path.home", return_value=fake_home):
                result = runner.invoke(cli, ["init"])

        # Should exit with 0 and print "Already initialized"
        assert result.exit_code == 0
        assert "Already initialized" in result.output

        # Content should NOT be overwritten
        content = config_file.read_text()
        assert "ALREADY_SET" in content
        assert "original" not in content

    def test_init_command_creates_directory(self, cli, tmp_path):
        """Test that init command creates the config directory when missing."""
        runner = CliRunner()

        # Mock Path.home() to return our temp directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with runner.isolated_filesystem():
            # Create .env.example in CWD
            env_example = Path(".env.example")
            env_example.write_text("NEW_VAR=value\n")

            with patch("heretek_swarm.cli.Path.home", return_value=fake_home):
                result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify directory was created
        config_dir = fake_home / ".heretek-swarm"
        assert config_dir.exists() and config_dir.is_dir(), (
            f"Config directory not created. Output: {result.output}"
        )

    def test_init_command_help(self, cli):
        """Test that init command shows help with --help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--help"])

        assert result.exit_code == 0
        assert "initialize" in result.output.lower() or "heretek-swarm" in result.output.lower()

    def test_init_command_no_browser_needed(self, cli, tmp_path):
        """Test that init command has no webbrowser dependency."""
        runner = CliRunner()

        # Mock Path.home()
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with runner.isolated_filesystem():
            # Create .env.example
            env_example = Path(".env.example")
            env_example.write_text("VAR=value\n")

            with patch("heretek_swarm.cli.Path.home", return_value=fake_home):
                with patch("webbrowser.open") as mock_browser:
                    result = runner.invoke(cli, ["init"])

        # webbrowser.open should NOT have been called
        assert not mock_browser.called, (
            "webbrowser.open should not be called by init command"
        )
        assert result.exit_code == 0

    def test_init_command_listed_in_cli_help(self, cli):
        """Test that init command appears in CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert "init" in result.output
