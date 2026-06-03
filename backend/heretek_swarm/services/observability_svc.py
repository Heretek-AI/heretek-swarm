"""
Observability service stub — Phase 5.4 of PLAN.md.

In-process skeleton for the future observability sidecar.
The stub exposes the same surface the sidecar would
expose (track_metric, emit_span, fire_alert) but
delegates to the canonical observability stack
(opik_compat, prometheus_client) so behavior matches
the in-process observability exactly.

The exit criterion for activating 5.4 is in
``docs/SOVEREIGN_SERVICES.md``: a load test shows the api
process's per-request latency drops by ≥10% when the
OTel exporter is moved to the sidecar.
"""

from __future__ import annotations

from typing import Any

from heretek_swarm.observability.opik_compat import (
    alert as _alert,
    log_span,
    timed as _timed,
    track_metric as _track_metric,
)


class ObservabilityServiceStub:
    """In-process skeleton for the future observability
    sidecar.
    """

    async def emit_span(
        self,
        name: str,
        *,
        tags: dict[str, str] | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> Any:
        with log_span(name, tags=tags, inputs=inputs) as span:
            yield span

    def fire_alert(
        self,
        name: str,
        *,
        severity: str = "warning",
        message: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        _alert(name, severity=severity, message=message, tags=tags)

    def track_metric(
        self,
        name: str,
        *,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        _track_metric(name, value=value, tags=tags)

    def time_block(self, name: str, *, tags: dict[str, str] | None = None) -> Any:
        return _timed(name, tags=tags)


_singleton: ObservabilityServiceStub | None = None


def get_observability_svc() -> ObservabilityServiceStub:
    """Return the process-wide :class:`ObservabilityServiceStub`."""
    global _singleton
    if _singleton is None:
        _singleton = ObservabilityServiceStub()
    return _singleton


__all__ = [
    "ObservabilityServiceStub",
    "get_observability_svc",
]
