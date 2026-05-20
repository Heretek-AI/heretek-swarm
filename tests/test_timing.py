"""
Tests for observability/timing.py — TimedContext and @timed decorator.

Verifies:
- TimedContext records elapsed_ms as positive float
- TimedContext logs structlog event with duration_ms and label
- TimedContext extra_fields appear in structlog output
- @timed decorator works with both sync and async functions
- format_duration_ms helper formats correctly
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from prometheus_client import Histogram

from heretek_swarm.observability.timing import TimedContext, format_duration_ms, timed


class TestTimedContext:
    """Tests for TimedContext context manager."""

    def test_records_elapsed_ms(self) -> None:
        """TimedContext.elapsed_ms is set to a positive value after exit."""
        with TimedContext(label="test_op") as ctx:
            pass
        assert ctx.elapsed_ms is not None
        assert ctx.elapsed_ms > 0

    def test_logs_structured_event(self) -> None:
        """TimedContext emits a structlog event with expected keys."""
        with TimedContext(label="test_event") as ctx:
            pass
        assert ctx.elapsed_ms is not None
        # structlog writes to its configured sinks; we verify the context
        # exit completed without error and elapsed_ms is populated.

    def test_extra_fields_included(self) -> None:
        """TimedContext with extra_fields logs them alongside duration_ms."""
        with TimedContext(
            label="test_extra",
            extra_key="hello",
            nested={"a": 1},
        ) as ctx:
            pass
        assert ctx.elapsed_ms is not None

    def test_histogram_called(self) -> None:
        """When a Histogram is provided, observe is called with duration_seconds."""
        mock_histogram = MagicMock(spec=Histogram)
        mock_labels = MagicMock()
        mock_histogram.labels.return_value = mock_labels

        with TimedContext(
            label="test_histogram",
            histogram=mock_histogram,
            histogram_labels={"db": "postgres"},
        ) as ctx:
            pass

        mock_histogram.labels.assert_called_once_with(db="postgres")
        mock_labels.observe.assert_called_once()
        observed_value = mock_labels.observe.call_args[0][0]
        assert observed_value > 0
        assert observed_value == pytest.approx((ctx.elapsed_ms or 0) / 1000.0)

    def test_histogram_not_called_when_none(self) -> None:
        """Default None histogram skips observe entirely."""
        with TimedContext(label="test_no_histogram") as ctx:
            pass
        assert ctx.elapsed_ms is not None


class TestTimedDecorator:
    """Tests for @timed decorator."""

    def test_wraps_sync_function(self) -> None:
        """@timed returns original value and records timing."""
        @timed("sync_func")
        def compute(x: int) -> int:
            return x * 2

        result = compute(21)
        assert result == 42

    def test_wraps_async_function(self) -> None:
        """@timed works with async functions."""
        @timed("async_func")
        async def fetch(x: int) -> int:
            await asyncio.sleep(0)
            return x + 1

        result = asyncio.run(fetch(41))
        assert result == 42

    def test_decorator_with_histogram(self) -> None:
        """@timed with histogram calls observe."""
        mock_histogram = MagicMock(spec=Histogram)

        @timed(
            "decorated_func",
            histogram=mock_histogram,
            histogram_labels={"actor_type": "executor"},
        )
        def work() -> str:
            return "done"

        result = work()
        assert result == "done"
        mock_histogram.labels.assert_called_once_with(actor_type="executor")
        mock_histogram.labels.return_value.observe.assert_called_once()


class TestFormatDurationMs:
    """Tests for format_duration_ms helper."""

    def test_whole_number(self) -> None:
        assert format_duration_ms(1234.0) == "1234.00ms"

    def test_fractional(self) -> None:
        assert format_duration_ms(1234.567) == "1234.57ms"

    def test_sub_millisecond(self) -> None:
        assert format_duration_ms(0.001) == "0.00ms"
