"""Tests for OTel auto-enable wiring in AutonomousSwarm.

Verifies that init_tracing() is called during startup when
OTEL_EXPORTER_OTLP_ENDPOINT is set.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_otel_globals():
    """Reset OTel global state between tests to avoid cross-contamination."""
    import heretek_swarm.infrastructure.otel.tracing as tracing_mod

    old_config = tracing_mod._tracer_config
    old_instance = tracing_mod._tracer_instance
    tracing_mod._tracer_config = None
    tracing_mod._tracer_instance = None
    yield
    tracing_mod._tracer_config = old_config
    tracing_mod._tracer_instance = old_instance


class TestOtelAutoEnable:
    """Verify OTel tracing is auto-enabled when the env var is present."""

    @patch("heretek_swarm.infrastructure.otel.tracing.init_tracing")
    def test_auto_enable_when_endpoint_set(self, mock_init_tracing):
        """init_tracing should be called with exporter='otlp' when OTEL_EXPORTER_OTLP_ENDPOINT is set."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = AutonomousSwarm(no_infra=True)

        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"}):
            import asyncio

            asyncio.run(swarm.initialize())

        mock_init_tracing.assert_called_once()
        call_args = mock_init_tracing.call_args
        config = call_args[0][0] if call_args[0] else call_args[1].get("config")
        assert config is not None
        assert config.exporter == "otlp"

    @patch("heretek_swarm.infrastructure.otel.tracing.init_tracing")
    def test_no_auto_enable_when_endpoint_unset(self, mock_init_tracing):
        """init_tracing should NOT be called when OTEL_EXPORTER_OTLP_ENDPOINT is absent."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = AutonomousSwarm(no_infra=True)

        # Ensure env var is not set
        env = {k: v for k, v in os.environ.items() if k != "OTEL_EXPORTER_OTLP_ENDPOINT"}
        with patch.dict(os.environ, env, clear=True):
            import asyncio

            asyncio.run(swarm.initialize())

        mock_init_tracing.assert_not_called()

    @patch("heretek_swarm.infrastructure.otel.tracing.init_tracing", side_effect=RuntimeError("boom"))
    def test_auto_enable_failure_is_swallowed(self, mock_init_tracing):
        """A failure in init_tracing should not crash the swarm init."""
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        swarm = AutonomousSwarm(no_infra=True)

        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"}):
            import asyncio

            # Should not raise — the warning is logged and init continues
            asyncio.run(swarm.initialize())

        mock_init_tracing.assert_called_once()
