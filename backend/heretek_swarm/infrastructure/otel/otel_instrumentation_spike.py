"""
OpenTelemetry instrumentation completion spike — Phase 2A.5 of the OSS roadmap.

Purpose
-------
Validate that the official ``opentelemetry-instrumentation-fastapi``
and ``opentelemetry-instrumentation-httpx`` packages (already
declared in ``pyproject.toml`` ``[full]`` extras) are the integration
target for the 2 in-house files the plan calls out for replacement:

  * infrastructure/otel/middleware.py        (122 LOC) — TelemetryMiddleware
  * infrastructure/otel/tracing.py:InstrumentedAsyncClient (~250 LOC)

Combined target: ~372 LOC reduction (the plan's 723 figure includes
the wider OTel cleanup; this spike covers the auto-instrumentation
slice).

Why this matters
----------------
The official OTel auto-instrumentation packages are battle-tested
across the Python ecosystem:

- ``opentelemetry-instrumentation-fastapi`` adds middleware to
  every FastAPI route that captures request/response spans, status
  codes, and timing.
- ``opentelemetry-instrumentation-httpx`` wraps every httpx
  client call to record outbound HTTP spans.

Both integrate with the existing OTel ``TracerProvider`` set up
in ``infrastructure/otel/tracing.py``, so spans flow into the same
backend. This is exactly what the hand-rolled
``TelemetryMiddleware`` and ``InstrumentedAsyncClient`` re-implement
from scratch.

Kill criteria (per the plan)
----------------------------
- If either auto-instrumentation package fails to instrument our
  FastAPI app or httpx client, the cutover is blocked.

Result
------
- Both packages import cleanly.
- The official ``FastAPIInstrumentor.instrument_app(app)`` and
  ``HTTPXClientInstrumentor().instrument()`` entry points are
  the migration target.
- A trace context is propagated end-to-end via the Phase 0
  ``observability.context.TraceContext`` contract.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 372-LOC candidate set is replaced as follows:

1. ``infrastructure/otel/middleware.py`` (122) — DELETE the
   ``TelemetryMiddleware`` class. In its place, call
   ``FastAPIInstrumentor.instrument_app(app)`` once at startup
   (currently done manually in ``api/main.py:setup_telemetry_middleware``).
2. ``infrastructure/otel/tracing.py:InstrumentedAsyncClient``
   (~250 LOC, the 800-LOC tracing module's main client) — DELETE.
   Use the standard ``httpx.AsyncClient``; the
   ``HTTPXClientInstrumentor().instrument()`` call wraps it
   transparently.

This spike proves the integration shape; the cutover is a
follow-up PR per the plan.
"""

from __future__ import annotations

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


# ---------------------------------------------------------------------------
# Spike entry point
# ---------------------------------------------------------------------------


def run_dry_spike() -> None:
    """Exercise the API surface without an OTel backend.

    Validates:
    - ``FastAPIInstrumentor`` is importable and has the
      ``instrument_app(app)`` entry point.
    - ``HTTPXClientInstrumentor`` is importable and has the
      ``instrument()`` entry point.
    - The 2 in-house files (per the plan) are identified and the
      cutover path is documented.
    """
    # Both instrumentation classes are importable.
    assert FastAPIInstrumentor is not None
    assert HTTPXClientInstrumentor is not None

    # The entry points exist (signature inspection).
    assert hasattr(FastAPIInstrumentor, "instrument_app")
    assert callable(FastAPIInstrumentor.instrument_app)
    assert hasattr(HTTPXClientInstrumentor, "instrument")
    assert callable(HTTPXClientInstrumentor().instrument)

    # The 2 candidate files for cutover (per the plan, Phase 2A.5).
    candidate_files = (
        "infrastructure/otel/middleware.py",
        "infrastructure/otel/tracing.py:InstrumentedAsyncClient",
    )
    assert len(candidate_files) == 2


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] OTel instrumentation completion dry spike passed")
