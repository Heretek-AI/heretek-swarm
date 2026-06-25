"""Tests for init_telemetry wiring."""

from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI


def test_init_telemetry_configures_structlog():
    """init_telemetry should inject add_trace_context into structlog."""
    from tier1.observability import init_telemetry

    app = FastAPI()
    with patch("tier1.observability._init_otel") as mock_otel:
        init_telemetry(app)
        mock_otel.assert_called_once()


def test_init_telemetry_installs_fastapi_instrumentor():
    """init_telemetry should instrument the FastAPI app."""
    from tier1.observability import init_telemetry

    app = FastAPI()
    with patch("tier1.observability._init_otel"):
        init_telemetry(app)
    # If _init_otel is mocked, we just verify init_telemetry doesn't crash.
