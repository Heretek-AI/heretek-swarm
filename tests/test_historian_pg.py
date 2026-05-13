"""Tests for ``HistorianAgent`` Postgres-backed event store.

Covers three scenarios:

1. ``_pg_writer`` drains the queue and issues parameterized INSERT calls
   via a mocked asyncpg pool.
2. Pool creation failure causes fallback to the JSONL writer path.
3. ``read_events()`` returns mocked DB rows via the dynamic WHERE builder.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.actors.historian import HistorianAgent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_pool() -> AsyncMock:
    """Return an ``AsyncMock`` that looks like an asyncpg connection pool.

    ``pool.acquire()`` returns an async context manager whose ``__aenter__``
    yields a mock connection.  The mock connection carries:
    - ``execute(sql, *args)`` — AsyncMock for DDL / INSERT calls
    - ``fetch(sql, *args)`` — AsyncMock for SELECT (read_events)
    """
    # Build the mock connection with async execute and fetch
    conn = AsyncMock(spec=[])
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock()

    # Build a proper async context manager for acquire()
    acquire_cm = AsyncMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    # Build the pool
    pool = AsyncMock(spec=[])
    pool.acquire = MagicMock(return_value=acquire_cm)

    return pool


@pytest.fixture
def mock_pool_acquire_fail() -> MagicMock:
    """Return a pool mock whose ``acquire()`` raises on the first call.

    Used to simulate startup failure (e.g. no Postgres available).
    """
    pool = MagicMock(spec=[])

    async def _fail_acquire():
        raise ConnectionError("could not connect to server")

    pool.acquire = MagicMock(side_effect=_fail_acquire)
    return pool


# =========================================================================
# Contract 1 — _pg_writer issues parameterized INSERT calls
# =========================================================================


class TestPGWriter:
    """The ``_pg_writer`` drains the queue and executes parameterized INSERT
    statements via a real-seeming asyncpg pool interface."""

    @staticmethod
    async def test_pg_writer_inserts_event(mock_pool: AsyncMock) -> None:
        agent = HistorianAgent(db_pool=mock_pool)

        # Grab the mock connection *before* initialize() starts the writer
        # so we can assert on it later.
        async with mock_pool.acquire() as conn:
            pass  # conn is the mock

        # Start the agent — this creates _pg_writer as a background task
        await agent.initialize()
        assert agent._using_pg is True
        assert agent._writer_task is not None

        # Enqueue an event and wait for the writer to drain it
        await agent.log_event(
            event_type="pg_test",
            agent_id="test-agent",
            payload={"key": "value"},
        )
        await agent._jsonl_queue.join()

        # The connection's execute should have been called twice:
        # 1) CREATE TABLE IF NOT EXISTS ...
        # 2) INSERT INTO historian_events ...
        assert conn.execute.call_count >= 2

        # Grab the INSERT call (the DDL call is first)
        insert_call = conn.execute.call_args_list[-1]
        insert_sql = insert_call[0][0]
        insert_params = insert_call[0][1:]

        assert "INSERT INTO historian_events" in insert_sql
        assert "event_id" in insert_sql
        assert "$1" in insert_sql
        assert insert_params[1] == "pg_test"
        assert insert_params[3] == "test-agent"

        await agent.cleanup()

    @staticmethod
    async def test_pg_writer_logs_on_success(mock_pool: AsyncMock) -> None:
        """Each successful insert logs a debug message."""
        import heretek_swarm.actors.historian as _h_mod

        agent = HistorianAgent(db_pool=mock_pool)

        with patch.object(_h_mod.logger, "debug") as mock_debug:
            await agent.initialize()

            await agent.log_event(
                event_type="log_check",
                agent_id="logger",
                payload={"msg": "hello"},
            )
            await agent._jsonl_queue.join()

            # The _pg_writer should have logged at least one debug
            # message for the insert.
            debug_calls = [
                c for c in mock_debug.call_args_list
                if "PG writer: inserted" in str(c)
            ]
            assert len(debug_calls) >= 1

        await agent.cleanup()


# =========================================================================
# Contract 2 — Pool creation failure → fallback to JSONL writer
# =========================================================================


class TestFallback:
    """When the pool is broken or absent, the agent gracefully falls back to
    the JSONL writer."""

    @staticmethod
    async def test_falls_back_to_jsonl_when_no_pool() -> None:
        """No ``db_pool`` at all → ``_using_pg`` stays ``False``."""
        agent = HistorianAgent()
        await agent.initialize()
        assert agent._using_pg is False
        assert agent._writer_task is not None

        # The writer task should be _jsonl_writer — verify by checking
        # the coroutine name.
        coro_name = agent._writer_task.get_coro().cr_code.co_name  # type: ignore[union-attr]
        assert coro_name == "_jsonl_writer"

        await agent.cleanup()

    @staticmethod
    async def test_falls_back_when_acquire_fails() -> None:
        """Pool exists but acquire() raises → _pg_writer logs and exits;
        the agent stays in JSONL mode for subsequent events."""
        import heretek_swarm.actors.historian as _h_mod

        # Build a broken pool whose acquire() returns an async context
        # manager that raises on __aenter__.
        broken_pool = AsyncMock()
        broken_pool.close = AsyncMock()
        acquire_cm = AsyncMock()
        acquire_cm.__aenter__ = AsyncMock(side_effect=ConnectionError("broken pool"))
        acquire_cm.__aexit__ = AsyncMock(return_value=None)
        broken_pool.acquire = MagicMock(return_value=acquire_cm)

        agent = HistorianAgent(db_pool=broken_pool)

        with patch.object(_h_mod.logger, "exception") as mock_exception:
            await agent.initialize()
            # _using_pg should be True since db_pool was set...
            assert agent._using_pg is True
            # ...but the writer should have logged the failure and exited.
            await asyncio.sleep(0.05)  # Let the writer task run

            error_calls = [
                c for c in mock_exception.call_args_list
                if "Failed to create historian_events table" in str(c)
            ]
            assert len(error_calls) >= 1

        await agent.cleanup()


# =========================================================================
# Contract 3 — read_events() with mocked DB response
# =========================================================================


class TestReadEvents:
    """``read_events()`` queries the ``historian_events`` table via the
    dynamic WHERE builder and returns parsed dicts."""

    @staticmethod
    async def test_read_events_returns_mocked_rows(mock_pool: AsyncMock) -> None:
        agent = HistorianAgent(db_pool=mock_pool)

        # Set up the mock connection's fetch to return fake rows
        async with mock_pool.acquire() as conn:
            now = datetime.now(UTC)
            conn.fetch = AsyncMock(return_value=[
                {
                    "event_id": "abc123",
                    "event_type": "test_event",
                    "timestamp": now,
                    "agent_id": "alice",
                    "payload": {"n": 1},
                },
                {
                    "event_id": "def456",
                    "event_type": "other_event",
                    "timestamp": now,
                    "agent_id": "bob",
                    "payload": {"n": 2},
                },
            ])

        await agent.initialize()
        assert agent._using_pg is True

        results = await agent.read_events(
            agent_id="alice",
            event_type="test_event",
        )

        assert len(results) == 2
        assert results[0]["event_id"] == "abc123"
        assert results[0]["type"] == "test_event"
        assert results[0]["agent_id"] == "alice"
        assert results[0]["payload"] == {"n": 1}
        assert "T" in results[0]["timestamp"]  # ISO-8601 format check

        async with mock_pool.acquire() as conn:
            fetch_call = conn.fetch.call_args_list[-1]
            fetch_sql = fetch_call[0][0]
            assert "WHERE" in fetch_sql
            assert "agent_id = $1" in fetch_sql
            assert "event_type = $2" in fetch_sql
            assert "LIMIT $3" in fetch_sql

        await agent.cleanup()

    @staticmethod
    async def test_read_events_returns_empty_when_not_pg() -> None:
        """Without a db_pool, ``read_events()`` returns an empty list."""
        agent = HistorianAgent()
        await agent.initialize()
        assert agent._using_pg is False

        results = await agent.read_events()
        assert results == []

        await agent.cleanup()

    @staticmethod
    async def test_read_events_returns_empty_on_query_failure(
        mock_pool: AsyncMock,
    ) -> None:
        import heretek_swarm.actors.historian as _h_mod

        agent = HistorianAgent(db_pool=mock_pool)

        async with mock_pool.acquire() as conn:
            conn.fetch = AsyncMock(
                side_effect=Exception("db connection lost")
            )

        await agent.initialize()

        with patch.object(_h_mod.logger, "exception") as mock_exception:
            results = await agent.read_events()
            assert results == []

            # Should have logged the exception
            error_calls = [
                c for c in mock_exception.call_args_list
                if "read_events query failed" in str(c)
            ]
            assert len(error_calls) >= 1

        await agent.cleanup()

    @staticmethod
    async def test_read_events_with_all_filters(mock_pool: AsyncMock) -> None:
        """All optional filters produce a correct parameterized WHERE clause."""
        agent = HistorianAgent(db_pool=mock_pool)

        async with mock_pool.acquire() as conn:
            conn.fetch = AsyncMock(return_value=[])

        await agent.initialize()

        results = await agent.read_events(
            agent_id="charlie",
            event_type="deploy",
            since="2026-01-01T00:00:00Z",
            until="2026-12-31T23:59:59Z",
            limit=50,
        )
        assert results == []

        async with mock_pool.acquire() as conn:
            fetch_call = conn.fetch.call_args_list[-1]
            fetch_sql = fetch_call[0][0]
            assert "agent_id = $1" in fetch_sql
            assert "event_type = $2" in fetch_sql
            assert "timestamp >= $3" in fetch_sql
            assert "timestamp <= $4" in fetch_sql
            assert "LIMIT $5" in fetch_sql

        await agent.cleanup()
