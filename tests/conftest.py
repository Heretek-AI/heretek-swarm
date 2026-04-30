"""Shared pytest fixtures for the heretek-swarm test suite.

Provides:
* ``mock_agent`` — a ``unittest.mock.MagicMock`` pre-configured with the
  ``agent_name`` attribute and a no-op ``run`` method.
* ``mock_agent_dict`` — builds a dict populated with ``analysis_history``,
  ``_analyses``, and ``_challenges`` for test-injectable state on mocked
  agents.
* An **autouse** fixture that clears ``get_supervisor().actors`` after every
  test to prevent singleton state from leaking between tests.
* A **pytest filterwarnings** entry that suppresses ``ResourceWarning`` —
  these are emitted by unclosed ``aiohttp.ClientSession`` objects from
  ``AgentActor`` heartbeat loops in integration tests.
"""

import warnings

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from heretek_swarm.actors.supervisor import get_supervisor


# Ignore ResourceWarning from unclosed aiohttp.ClientSession objects —
# these are created by AgentActor heartbeat background tasks in integration
# tests and are harmless (cleaned up by the event loop on shutdown).
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")


@pytest.fixture
def mock_agent() -> MagicMock:
    """Return a fresh ``MagicMock`` that looks like a ``swarms.Agent``.

    The mock carries an ``agent_name`` attribute (``"test-agent"``) and a
    ``run`` method that returns a preset string so callers get a real return
    value without hitting an LLM.
    """
    agent = MagicMock()
    agent.agent_name = "test-agent"
    agent.run.return_value = "mock response"
    return agent


@pytest.fixture
def mock_agent_dict() -> dict:
    """Return a dict with per-agent attributes for deliberation testing.

    Dict keys mirror what real ``AgentActor`` instances carry so that
    downstream code can inspect ``analysis_history``, ``_analyses``, and
    ``_challenges`` without instantiating real actors.
    """
    return {
        "analysis_history": [],
        "_analyses": {},
        "_challenges": [],
    }


@pytest.fixture(autouse=True)
def _clear_supervisor_actors() -> Generator[None, None, None]:
    """Autouse fixture — clear ``get_supervisor().actors`` after every test.

    ``ActorSupervisor`` is a module-level singleton accessed via
    ``get_supervisor()``.  Without this teardown, tests that spawn or inspect
    actors would leak state into subsequent tests and produce flickering
    failures when run in a different order.
    """
    yield
    supervisor = get_supervisor()
    supervisor.actors.clear()
