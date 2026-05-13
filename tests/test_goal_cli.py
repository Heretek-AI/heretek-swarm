"""
Tests for the ``goal`` CLI command group (T04).

Verifies that ``heretek-swarm goal list`` and ``heretek-swarm goal propose``
are wired into the Click CLI and that the CLI runner can invoke them.
"""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from heretek_swarm.cli import cli
from heretek_swarm.goals.models import Goal


class TestGoalCLIGroup:
    """Verify the ``goal`` command group is registered and invocable."""

    def test_goal_group_registered(self) -> None:
        assert "goal" in cli.commands

    def test_goal_group_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["goal", "--help"])
        assert result.exit_code == 0
        assert "propose" in result.output
        assert "list" in result.output


class TestGoalList:
    """Tests for ``heretek-swarm goal list``."""

    def test_goal_list_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["goal", "list", "--help"])
        assert result.exit_code == 0

    def test_goal_list_empty_store(self) -> None:
        with patch(
            "heretek_swarm.goals.store.FileGoalStore.load_all",
            return_value=[],
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["goal", "list"])
            assert result.exit_code == 0
            assert "No goals persisted yet" in result.output

    def test_goal_list_with_goals(self) -> None:
        goals = [
            Goal(
                id="goal_aaa111", title="Example goal", description="A test goal", status="proposed"
            ),
            Goal(
                id="goal_bbb222",
                title="Accepted goal",
                description="Already voted in",
                status="accepted",
                votes=[{"agent_id": "steward", "decision": "approve", "confidence": 0.9}],
            ),
        ]
        with patch(
            "heretek_swarm.goals.store.FileGoalStore.load_all",
            return_value=goals,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["goal", "list"])
            assert result.exit_code == 0
            assert "goal_aaa111" in result.output
            assert "goal_bbb222" in result.output
            assert "proposed" in result.output
            assert "accepted" in result.output

    def test_goal_list_status_filter(self) -> None:
        goals = [
            Goal(id="g1", title="A", description="...", status="proposed"),
            Goal(id="g2", title="B", description="...", status="accepted"),
        ]
        with patch(
            "heretek_swarm.goals.store.FileGoalStore.load_all",
            return_value=goals,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["goal", "list", "--status", "accepted"])
            assert result.exit_code == 0
            assert "g2" in result.output
            assert "g1" not in result.output


class TestGoalPropose:
    """Tests for ``heretek-swarm goal propose``."""

    def test_goal_propose_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["goal", "propose", "--help"])
        assert result.exit_code == 0
