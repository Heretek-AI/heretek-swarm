"""
Tests for observability/db_timing.py — SQLAlchemy async engine query timing.

Verifies:
- attach_db_timing attaches listeners to sync Engine without error
- attach_db_timing attaches listeners to async AsyncEngine via sync_engine
- Listeners fire and emit structured log events on query execution
- db_query_executed DEBUG event emitted for normal queries
- db_slow_query WARNING event emitted for slow queries
- Params summary is type/count only — never actual values
- Statement text is truncated to 200 chars
- Double-attachment guard prevents duplicate listeners
- Does not crash when engine is None is NOT a valid case (must be Engine or AsyncEngine)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from heretek_swarm.observability.db_timing import (
    DB_TIMING_ENGINE_ATTR,
    attach_db_timing,
)

_DB_TIMING_MODULE = "heretek_swarm.observability.db_timing"


class TestAttachDbTiming:
    """Tests for attach_db_timing function."""

    def test_attaches_to_sync_engine(self) -> None:
        """attach_db_timing marks the engine and does not crash."""
        engine = create_engine("sqlite:///:memory:")
        attach_db_timing(engine)
        assert getattr(engine, DB_TIMING_ENGINE_ATTR) is True

    def test_attaches_to_async_engine_sync_engine(self) -> None:
        """attach_db_timing resolves async engine to sync_engine and attaches."""
        async_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        attach_db_timing(async_engine)
        assert getattr(async_engine.sync_engine, DB_TIMING_ENGINE_ATTR) is True

    def test_double_attach_is_idempotent(self) -> None:
        """Calling attach_db_timing twice does not re-register listeners."""
        engine = create_engine("sqlite:///:memory:")
        attach_db_timing(engine)
        attach_db_timing(engine)
        # Still True, no exception raised
        assert getattr(engine, DB_TIMING_ENGINE_ATTR) is True

    @patch(f"{_DB_TIMING_MODULE}.structlog.get_logger")
    def test_emits_db_query_executed_log(self, mock_get_logger: MagicMock) -> None:
        """Normal queries emit DEBUG-level db_query_executed structured log."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        engine = create_engine("sqlite:///:memory:")
        attach_db_timing(engine)

        with engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE test_db_timing (id INTEGER, name VARCHAR)")
            )
            conn.execute(
                text("INSERT INTO test_db_timing (id, name) VALUES (:id, :name)"),
                {"id": 1, "name": "test"},
            )
            conn.commit()

        debug_calls = [
            call
            for call in mock_logger.debug.call_args_list
            if "db_query_executed" in str(call)
        ]
        assert len(debug_calls) >= 2

        # Verify log structure
        first_call = debug_calls[0]
        assert first_call[0][0] == "db_query_executed"
        assert "statement" in first_call[1]
        assert "params_summary" in first_call[1]
        assert "duration_ms" in first_call[1]

    @patch(f"{_DB_TIMING_MODULE}.structlog.get_logger")
    def test_emits_db_slow_query_log(self, mock_get_logger: MagicMock) -> None:
        """Queries exceeding threshold emit WARNING-level db_slow_query."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        engine = create_engine("sqlite:///:memory:")
        # Set threshold to 0 so all queries are "slow"
        attach_db_timing(engine, slow_query_threshold_ms=0)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        mock_logger.warning.assert_called()
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "db_slow_query" in str(call)
        ]
        assert len(warning_calls) >= 1

        call = warning_calls[0]
        assert call[0][0] == "db_slow_query"
        assert "statement" in call[1]
        assert "params_summary" in call[1]
        assert "duration_ms" in call[1]

    @patch(f"{_DB_TIMING_MODULE}.structlog.get_logger")
    def test_params_summary_no_values(self, mock_get_logger: MagicMock) -> None:
        """Params summary records type/count only, never actual values."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        engine = create_engine("sqlite:///:memory:")
        attach_db_timing(engine)

        with engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE test_p (id INTEGER, name VARCHAR, secret VARCHAR)")
            )
            conn.execute(
                text(
                    "INSERT INTO test_p (id, name, secret) "
                    "VALUES (:id, :name, :secret)"
                ),
                {"id": 42, "name": "alice", "secret": "super-secret-key"},
            )
            conn.commit()

        debug_calls = [
            call
            for call in mock_logger.debug.call_args_list
            if "db_query_executed" in str(call)
        ]
        assert len(debug_calls) >= 2

        # SQLite pysqlite driver converts dict params to positional tuple
        params_arg = debug_calls[1][1].get("params_summary")
        assert params_arg == "3 positional"
        # Ensure actual values are NOT present in the params_summary
        assert "super-secret-key" not in params_arg
        assert "alice" not in params_arg

    @patch(f"{_DB_TIMING_MODULE}.structlog.get_logger")
    def test_params_summary_rows(self, mock_get_logger: MagicMock) -> None:
        """executemany with list produces 'N rows' summary."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        engine = create_engine("sqlite:///:memory:")
        attach_db_timing(engine)

        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE t (x INT)"))
            conn.execute(
                text("INSERT INTO t (x) VALUES (:x)"),
                [{"x": 1}, {"x": 2}, {"x": 3}],
            )
            conn.commit()

        debug_calls = [
            call
            for call in mock_logger.debug.call_args_list
            if "db_query_executed" in str(call)
        ]
        insert_call = debug_calls[1]  # second query is the insert
        assert insert_call[1]["params_summary"] == "3 rows"

    @patch(f"{_DB_TIMING_MODULE}.structlog.get_logger")
    def test_params_summary_none(self, mock_get_logger: MagicMock) -> None:
        """Queries with no parameters produce 'none' summary."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        engine = create_engine("sqlite:///:memory:")
        attach_db_timing(engine)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        debug_calls = [
            call
            for call in mock_logger.debug.call_args_list
            if "db_query_executed" in str(call)
        ]
        assert debug_calls[0][1]["params_summary"] == "none"

    @patch(f"{_DB_TIMING_MODULE}.structlog.get_logger")
    def test_statement_truncation(self, mock_get_logger: MagicMock) -> None:
        """Statement text longer than 200 chars is truncated."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        engine = create_engine("sqlite:///:memory:")
        attach_db_timing(engine)

        # Long literal-only SELECT — no table needed
        long_statement = (
            "SELECT "
            + ", ".join([f"{i} AS col{i}" for i in range(1, 31)])
            + " FROM (SELECT 1 AS base)"
        )
        assert len(long_statement) > 200

        with engine.connect() as conn:
            conn.execute(text(long_statement))
            conn.commit()

        debug_calls = [
            call
            for call in mock_logger.debug.call_args_list
            if "db_query_executed" in str(call)
        ]
        logged_statement = debug_calls[0][1]["statement"]
        assert len(logged_statement) == 200
        assert logged_statement == long_statement[:200]

    @patch(f"{_DB_TIMING_MODULE}.structlog.get_logger")
    def test_async_engine_listeners_fire(self, mock_get_logger: MagicMock) -> None:
        """Listeners fire correctly on async engine queries."""
        import asyncio

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        async def _run() -> None:
            async_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            attach_db_timing(async_engine)

            async with async_engine.connect() as conn:
                await conn.execute(
                    text("CREATE TABLE async_test (id INTEGER, name VARCHAR)")
                )
                await conn.execute(
                    text("INSERT INTO async_test (id, name) VALUES (:id, :name)"),
                    {"id": 1, "name": "async_test"},
                )
                await conn.commit()

            # Shut down the async engine to clean up
            await async_engine.dispose()

        asyncio.run(_run())

        debug_calls = [
            call
            for call in mock_logger.debug.call_args_list
            if "db_query_executed" in str(call)
        ]
        assert len(debug_calls) >= 2
        # aiosqlite passes params as positional tuple, not dict
        insert_call = debug_calls[1]
        assert insert_call[1]["params_summary"] == "2 positional"
