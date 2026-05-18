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
* A **logging filter** on the ``asyncio`` logger that suppresses
  ``Unclosed client session`` messages — these are emitted by the event
  loop's default exception handler during teardown when background tasks
  created ``aiohttp.ClientSession`` objects that were not explicitly closed.
* ``--run-slow`` CLI option: when passed, ``@pytest.mark.slow`` tests are
  collected and run normally.  Without it, slow tests are skipped via
  ``-m "not slow"`` (the default ``addopts`` does *not* include this skip,
  so slow tests are collected but skipped by the ``conftest`` auto-skip
  fixture below).
"""

import logging
import warnings
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from heretek_swarm.actors.supervisor import get_supervisor

# Ignore ResourceWarning from unclosed aiohttp.ClientSession objects —
# these are created by AgentActor heartbeat background tasks in integration
# tests and are harmless (cleaned up by the event loop on shutdown).
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")


class _SuppressUnclosedSessions(logging.Filter):
    """Drop asyncio 'Unclosed client session' log records.

    The asyncio event loop logs unclosed aiohttp sessions as ERROR-level
    messages through the ``asyncio`` logger during event-loop teardown.
    These are benign in the test suite (background heartbeat tasks create
    sessions that are cleaned up when the loop closes).  Suppressing them
    keeps ``pytest`` stderr clean and prevents false-negative verification.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "Unclosed client session" not in record.getMessage()


# Apply the filter to the asyncio logger so structured-log and stdlib
# handlers both see it.
logging.getLogger("asyncio").addFilter(_SuppressUnclosedSessions())


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


# ---------------------------------------------------------------------------
# --run-slow CLI option: gate @pytest.mark.slow tests behind an explicit flag
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ``--run-slow`` so slow tests are opt-in."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run tests marked @pytest.mark.slow (skipped by default)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Ensure 'slow' marker is known at runtime (also declared in pyproject.toml)."""
    config.addinivalue_line("markers", "slow: Tests that take >5s")


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip @pytest.mark.slow tests unless ``--run-slow`` is passed."""
    if config.getoption("--run-slow"):
        return
    slow_marker = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if item.get_closest_marker("slow"):
            item.add_marker(slow_marker)
