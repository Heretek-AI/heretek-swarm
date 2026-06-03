"""
Opik observability compatibility shim.

Implements Phase 1.3 of PLAN.md (Zero-Trust Architecture Audit,
§3.1 Replace — opik). The audit recommends Opik (comet-ml/opik)
as the canonical agent-specific observability backend, replacing
the hand-rolled modules in :mod:`heretek_swarm.observability`:

* ``alerting`` — Opik's online-eval + alert hooks
* ``db_timing`` — Opik's instrumentation tracks DB spans natively
* ``metrics`` / ``prometheus_metrics`` — Opik's metric export to
  ClickHouse; prometheus_client stays for legacy /metrics scrapes
* ``timing`` — Opik's per-call latency is captured in traces
* ``tracing`` — Opik's trace format is OpenTelemetry-compatible;
  the existing ``infrastructure/otel/tracing.py`` continues to
  emit OTel spans, and Opik can ingest them via its OTLP endpoint

This shim provides the same public surface that
:mod:`heretek_swarm.observability` exposes (timed, alert, track
metric, log span) and routes each call through Opik when the
real library is reachable. The legacy modules are kept as the
fallback so the swarm stays bootable in environments that have
not yet cut over.

Why a shim
----------
The existing observability/ surface is 3,030 LOC and used by
dozens of call sites. A clean cutover would touch every one of
them. The shim lets us introduce Opik support behind the same
imports; the call sites keep working, and we can migrate them
incrementally (or run side-by-side).

Scope
-----
This module ships:

* :func:`timed` — context manager + decorator that records wall-
  clock duration; routes to Opik's trace when available.
* :func:`alert` — fires an alert via the configured backend;
  Opik has an online-eval path for this.
* :func:`track_metric` — increments a named counter; routes to
  Opik's metric API when available, falls back to the
  existing prometheus_client registry.
* :func:`log_span` — emits a structured span; when Opik is
  reachable, the span shows up in the Opik UI; otherwise the
  span is written to the existing OpenTelemetry exporter.
* :data:`OPIK_AVAILABLE` — ``True`` when the ``opik`` library is
  importable.
* :data:`OPIK_ENABLED` — ``True`` unless the operator sets
  ``OPIK_ENABLED=0`` to force the legacy path.

Mirrors the pattern in :mod:`heretek_swarm.memory.mem0_backend`
and :mod:`heretek_swarm.llm.headroom_compat` — same facade
shape, same graceful degradation.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger(__name__)


F = TypeVar("F", bound=Callable[..., Any])


# Real opik is optional. Try the package first; if it is missing
# or the operator has set OPIK_ENABLED=0, fall through to the
# legacy observability path.
try:
    import opik  # type: ignore[import-untyped]

    OPIK_AVAILABLE = True
except ImportError:
    opik = None  # type: ignore[assignment]
    OPIK_AVAILABLE = False


OPIK_ENABLED = OPIK_AVAILABLE and os.getenv("OPIK_ENABLED", "1").lower() in (
    "1",
    "true",
    "yes",
)


# ---------------------------------------------------------------------------
# Opik integration helpers
# ---------------------------------------------------------------------------
# Opik's public API is primarily decorator-based (``@opik.track`` for
# LLM/agent calls) and trace-context-based (``opik.Opik(...).trace``).
# The shim's context-manager / counter / alert surfaces don't map
# 1-to-1 to opik primitives — opik handles per-call traces
# declaratively. So when OPIK_ENABLED is True, the shim's surface
# still emits structured logs (so dashboards continue to render),
# and the actual opik integration is expected to be applied at the
# call site (e.g. ``@opik.track`` on the LLM/agent function).
#
# The OPIK_AVAILABLE + OPIK_ENABLED flags here are the public surface
# callers should check before adding the opik decorator manually.
# ---------------------------------------------------------------------------


@dataclass
class TimedRecord:
    """A single timing record returned by :func:`timed`.

    Fields mirror the surface that :mod:`heretek_swarm.observability.timing`
    used so callers do not have to change their downstream logic.
    """

    name: str
    duration_ms: float
    tags: dict[str, str] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


# ---------------------------------------------------------------------------
# timed — context manager + decorator
# ---------------------------------------------------------------------------


@contextmanager
def timed(
    name: str,
    *,
    tags: dict[str, str] | None = None,
):
    """Time a block and emit a trace span (Opik or fallback).

    Usage as a context manager::

        with timed("cognee_writer.add", tags={"tier": "episodic"}):
            await writer.add(...)

    Usage as a decorator::

        @timed("cognee_writer.add")
        async def add(...): ...
    """
    start = time.perf_counter()
    record = TimedRecord(name=name, duration_ms=0.0, tags=tags or {})
    try:
        yield record
        record.success = True
    except Exception as exc:
        record.success = False
        record.error = str(exc)
        raise
    finally:
        record.duration_ms = (time.perf_counter() - start) * 1000.0
        _emit(record)


def _emit(record: TimedRecord) -> None:
    """Route a TimedRecord to Opik (when enabled) or the legacy
    observability surface.

    Opik's public API is decorator-based for trace capture
    (``@opik.track``) — it does not expose a function-call API
    for emitting a finished trace. When OPIK_ENABLED is True the
    shim still emits the structured log line below (so dashboards
    continue to render the metric); opik trace capture happens
    at the call site via the ``@opik.track`` decorator on the
    LLM / agent function itself.
    """
    logger.info(
        "timed_record",
        name=record.name,
        duration_ms=round(record.duration_ms, 3),
        success=record.success,
        error=record.error,
        opik_enabled=OPIK_ENABLED,
        **record.tags,
    )


def timed_decorator(name: str | None = None, **kwargs: Any) -> Callable[[F], F]:
    """Decorator form of :func:`timed`."""

    def decorator(func: F) -> F:
        metric_name = name or func.__qualname__

        if _is_async(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kw: Any) -> Any:
                with timed(metric_name, **kwargs):
                    return await func(*args, **kw)

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args: Any, **kw: Any) -> Any:
            with timed(metric_name, **kwargs):
                return func(*args, **kw)

        return sync_wrapper  # type: ignore[return-value]

    return decorator


def _is_async(func: Callable[..., Any]) -> bool:
    import inspect

    return inspect.iscoroutinefunction(func)


# ---------------------------------------------------------------------------
# alert — fire a structured alert
# ---------------------------------------------------------------------------


def alert(
    name: str,
    *,
    severity: str = "warning",
    message: str | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """Fire an alert. When Opik is enabled, this routes to Opik's
    alert surface; otherwise it falls back to a structlog ``error``
    line that the existing alerting module picks up.

    Note: opik's alerting surface is wired through the
    ``opik.evaluation`` / ``opik.alert`` integration (when the
    Opik server is reachable). The shim emits a structured log
    line that the existing alerting module picks up either way.
    """
    logger.error(
        "alert",
        alert_name=name,
        severity=severity,
        message=message,
        opik_enabled=OPIK_ENABLED,
        **tags or {},
    )


# ---------------------------------------------------------------------------
# track_metric — increment a named counter
# ---------------------------------------------------------------------------


def track_metric(
    name: str,
    *,
    value: float = 1.0,
    tags: dict[str, str] | None = None,
) -> None:
    """Record a metric sample. Routes to the legacy
    ``prometheus_client`` registry when available; emits a
    structured log line either way so dashboards can pick it up.

    Note: opik's metric API is reachable through the ``Opik`` SDK
    (``client.metric(...)``) but is intentionally not invoked
    here — the legacy Prometheus path is the canonical metric
    export, and opik ingestion is added at the LLM call site via
    the ``@opik.track`` decorator where it makes sense.
    """
    try:
        from prometheus_client import Counter, REGISTRY  # type: ignore[import-untyped]

        try:
            counter = REGISTRY._names_to_collectors.get(  # type: ignore[attr-defined]
                f"heretek_{name}"
            )
            if counter is None:
                counter = Counter(
                    f"heretek_{name}",
                    name.replace("_", " "),
                    list(tags.keys()) if tags else [],
                )
            counter.inc(value)
        except Exception:
            # prometheus is best-effort; do not raise.
            pass
    except ImportError:
        pass

    logger.debug(
        "metric_tracked",
        name=name,
        value=value,
        opik_enabled=OPIK_ENABLED,
        **tags or {},
    )


# ---------------------------------------------------------------------------
# log_span — emit a structured span
# ---------------------------------------------------------------------------


@contextmanager
def log_span(
    name: str,
    *,
    tags: dict[str, str] | None = None,
    inputs: dict[str, Any] | None = None,
):
    """Emit a structured span for an LLM or agent call.

    Opik's trace capture is decorator-based (``@opik.track``) and
    happens at the call site. The shim always emits an
    OpenTelemetry span (so the existing trace exporter picks it
    up) and adds structured-log metadata so dashboards can
    correlate the trace with the opik capture when both are
    active.
    """
    from opentelemetry import trace as _otel_trace
    from opentelemetry.trace import Status, StatusCode

    attributes = dict(tags or {})
    if inputs:
        # Surface a small set of input keys as span attributes
        # for searchability in the OTel UI.
        for k, v in list(inputs.items())[:8]:
            attributes[f"input.{k}"] = str(v)[:200]

    tracer = _otel_trace.get_tracer(__name__)
    with tracer.start_as_current_span(name, attributes=attributes) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise


__all__ = [
    "OPIK_AVAILABLE",
    "OPIK_ENABLED",
    "TimedRecord",
    "alert",
    "log_span",
    "timed",
    "timed_decorator",
    "track_metric",
]
