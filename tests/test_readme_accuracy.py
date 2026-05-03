"""Tests that README.md accurately reflects the current CLI and package state.

These assertions catch drift between the documentation and the actual
CLI surface area.  If a new command is added or a flag changes, one of
these tests will fail and prompt the developer to update the README.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"


@pytest.fixture(scope="module")
def readme_text() -> str:
    """Return the full text of the repository README."""
    assert README_PATH.exists(), f"README.md not found at {README_PATH}"
    return README_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Command coverage
# ---------------------------------------------------------------------------

EXPECTED_COMMANDS = [
    "run",
    "serve",
    "deploy",
    "wizard",
    "config",
    "init",
    "status",
    "stop",
]


class TestReadmeCommandCoverage:
    """README must document every CLI subcommand."""

    @staticmethod
    @pytest.mark.parametrize("cmd", EXPECTED_COMMANDS)
    def test_command_mentioned(readme_text: str, cmd: str) -> None:
        """The command ``{cmd}`` should appear in the README."""
        # We look for the command name as a word boundary match to avoid
        # false positives from substrings (e.g. "stop" inside "startup").
        assert cmd in readme_text, (
            f"Command '{cmd}' not found in README.md"
        )


# ---------------------------------------------------------------------------
# Flag coverage
# ---------------------------------------------------------------------------


class TestReadmeFlagCoverage:
    """README must mention key CLI flags."""

    @staticmethod
    def test_no_infra_flag_mentioned(readme_text: str) -> None:
        """README should mention the --no-infra flag."""
        assert "--no-infra" in readme_text

    @staticmethod
    def test_prompt_flag_mentioned(readme_text: str) -> None:
        """README should mention the --prompt flag."""
        assert "--prompt" in readme_text


# ---------------------------------------------------------------------------
# Version alignment
# ---------------------------------------------------------------------------


class TestReadmeVersionAlignment:
    """README version string must match the package version."""

    @staticmethod
    def test_version_matches_package(readme_text: str) -> None:
        """The version in the README header should match heretek_swarm.__version__."""
        from heretek_swarm import __version__

        # README uses "**Version:** X.Y.Z" in the header
        assert __version__ in readme_text, (
            f"Package version {__version__!r} not found in README.md"
        )


# ---------------------------------------------------------------------------
# CLI group coverage
# ---------------------------------------------------------------------------

EXPECTED_GROUPS = [
    "Core Operations",
    "Configuration",
    "Monitoring",
]


class TestReadmeCliGroups:
    """README must document all three CLI command groups."""

    @staticmethod
    @pytest.mark.parametrize("group", EXPECTED_GROUPS)
    def test_group_mentioned(readme_text: str, group: str) -> None:
        """The CLI group heading '{group}' should appear in the README."""
        assert group in readme_text, (
            f"CLI group '{group}' not found in README.md"
        )


# ---------------------------------------------------------------------------
# Docker compose naming
# ---------------------------------------------------------------------------


class TestReadmeDockerComposeNaming:
    """Instruction blocks should use 'docker compose' (V2), not the
    deprecated hyphenated 'docker-compose' (V1) as a command."""

    @staticmethod
    def test_no_hyphenated_docker_compose_command(readme_text: str) -> None:
        """README should not use 'docker-compose' as a CLI command (V1).

        References to the *file* ``docker-compose.yml`` are acceptable
        because that is the conventional filename.  Only invocations of
        the command itself (e.g. ``docker-compose up``) are flagged.
        """
        import re

        # Pattern: 'docker-compose' followed by a subcommand word (up, down, etc.)
        # This catches V1 command usage but not filename references.
        v1_command_pattern = re.compile(
            r"docker-compose\s+(up|down|build|pull|push|logs|restart|stop|start|exec|run|ps|config)",
            re.IGNORECASE,
        )
        lines = readme_text.splitlines()
        violations = [
            (i + 1, line)
            for i, line in enumerate(lines)
            if v1_command_pattern.search(line)
        ]
        assert not violations, (
            f"Found 'docker-compose <cmd>' (V1 command) in README on line(s): "
            + ", ".join(str(ln) for ln, _ in violations)
        )
