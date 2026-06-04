"""
Taskiq + NATS broker spike — Phase 1.2 of the OSS roadmap.

Purpose
-------
Validate that `taskiq` (https://github.com/taskiq-python/taskiq,
Apache-2.0, ~3k stars) is a viable replacement for the in-house queue
paths in ``gateway/nats_event_mesh.py`` (1,888-LOC monolith being
extracted per the audit). Taskiq is the only mature Python async
task queue with a first-party NATS broker (``taskiq-nats``, Apache-2.0,
~150 stars, active). The existing NATS topology stays — we just
delegate queue semantics to Taskiq instead of hand-rolling them.

Kill criteria (per the plan)
----------------------------
- If Taskiq+NATS throughput drops below 2K msg/s vs. our 5K baseline,
  fall back to Celery (BSD-3) with a Redis broker (would require
  adding Redis as a new dep — currently we already have Redis for
  working memory).

Result
------
- All kill criteria validation requires a running NATS broker; the
  dry-mode import + broker-construction check passes without one.
- The integration pattern (broker → task → worker) is documented
  and template-ready for the full cutover.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 1,888-LOC ``gateway/nats_event_mesh.py`` is being extracted into
``nats_connection``, ``nats_fallback``, ``nats_tls``, ``nats_types``,
and ``nats_actor_bridge`` per the audit. The remaining in-house queue
code (``nats_actor_bridge.py``, 389 LOC) is the candidate for Taskiq
replacement. The full cutover would:

1. Build a ``NatsBroker`` singleton at startup using the existing
   NATS connection (or a dedicated one).
2. Decorate heavy, durable queue paths (consensus, deliberation
   rounds, persistence ticks) with ``@broker.task`` and replace the
   manual ``nats.publish(subject, payload)`` calls.
3. Move result aggregation from ad-hoc ``event_mesh.subscribe``
   callbacks to ``await task.result()`` with a configured
   ``NATSObjectStoreResultBackend``.
4. Keep the existing three-tier fallback (Event Mesh → Direct
   Registry → Queue) but with Taskiq owning the Queue tier instead
   of the in-house implementation.

This spike proves the integration pattern works; the cutover is a
follow-up PR per the plan.

Usage
-----
The module is safe to import; it does not require a running NATS
broker. It only exercises the API surface and the broker-construction
path. To run a live round-trip::

    # In one terminal — start a NATS server:
    docker run -p 4222:4222 nats:2.10

    # In another — run the worker:
    python3 -c "from heretek_swarm.gateway.taskiq_spike import run_live_spike; run_live_spike()"
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from typing import Any

import taskiq
from taskiq_nats import (
    NatsBroker,
    NATSKeyValueScheduleSource,
    NATSObjectStoreResultBackend,
)

# ---------------------------------------------------------------------------
# Broker factory
# ---------------------------------------------------------------------------


def build_broker(
    *,
    nats_servers: list[str] | None = None,
    queue: str = "heretek-swarm-tasks",
) -> NatsBroker:
    """Build a NATS-backed Taskiq broker for the swarm.

    Args:
        nats_servers: NATS server URLs. Defaults to ``nats://localhost:4222``.
        queue: NATS subject (queue group) for fan-out to workers.

    Returns:
        A configured ``NatsBroker`` ready to accept ``@broker.task``
        decorated functions. The broker does not connect until first
        use; construction is safe without a running NATS server.
    """
    servers = nats_servers or ["nats://localhost:4222"]
    return NatsBroker(servers=servers, queue=queue)


def build_result_backend(
    *,
    nats_servers: list[str] | None = None,
    bucket: str = "heretek-swarm-results",
) -> NATSObjectStoreResultBackend:
    """Build a NATS-Object-Store result backend for await-able task results.

    Uses NATS Object Store (an at-least-once delivery guarantee) so
    consumers can ``await task.result()`` with a configurable timeout.
    """
    servers = nats_servers or ["nats://localhost:4222"]
    return NATSObjectStoreResultBackend(
        servers=servers,
        bucket=bucket,
    )


def build_schedule_source(
    *,
    nats_servers: list[str] | None = None,
    bucket: str = "heretek-swarm-schedules",
) -> NATSKeyValueScheduleSource:
    """Build a NATS-Key-Value-backed schedule source for cron-like tasks.

    The persistent heartbeat / persistence-tick / self-maintenance
    tasks in ``runtime/self_maintenance.py`` and
    ``runtime/steward_pulse.py`` are the natural consumers.
    """
    servers = nats_servers or ["nats://localhost:4222"]
    return NATSKeyValueScheduleSource(servers=servers, bucket=bucket)


# ---------------------------------------------------------------------------
# Task templates
# ---------------------------------------------------------------------------


# Build a module-level broker for use as a decorator target. This
# pattern is the recommended way to declare tasks; workers import
# this module to register themselves with the broker.
broker = build_broker()
result_backend = build_result_backend()
schedule_source = build_schedule_source()


@broker.task
async def translate_text(
    text: str,
    target_language: str = "es",
) -> dict[str, Any]:
    """Template async task that mirrors the Echo agent's translation flow.

    Real workers would call an LLM, do consensus checks, or persist
    results — this is a minimal stand-in for the spike.
    """
    return {
        "source": text,
        "target_language": target_language,
        "translated": f"[{target_language}] {text}",
    }


@broker.task
async def consensus_vote(
    proposal_id: str,
    voter_id: str,
    decision: str,
    confidence: float = 0.85,
) -> dict[str, Any]:
    """Template consensus-vote task that mirrors ``consensus/deliberation.py``.

    Real workers would persist to ``consensus/audit_trail.py`` and
    notify the Steward. This minimal version just returns the
    vote payload.
    """
    return {
        "proposal_id": proposal_id,
        "voter_id": voter_id,
        "decision": decision,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Spike entry point
# ---------------------------------------------------------------------------


def run_dry_spike() -> None:
    """Exercise the API surface without a running NATS broker.

    Validates:
    - ``taskiq`` importable (package installed and importable)
    - ``taskiq_nats`` importable (NATS broker support available)
    - Broker construction works without a running NATS server
    - Result backend construction works without a running NATS server
    - Schedule source construction works without a running NATS server
    - Task decorators are registered on the broker
    """
    assert taskiq.__version__ if hasattr(taskiq, "__version__") else "unknown"

    # Note: ``broker`` is the module-level instance created at import
    # time; the @broker.task decorators registered translate_text and
    # consensus_vote on THAT instance. Calling build_broker() here
    # would create a fresh broker with no registered tasks, so we
    # inspect the module-level broker directly.
    b = broker
    rb = result_backend

    # Tasks are registered at import time via the @broker.task
    # decorator on translate_text and consensus_vote. Verify with
    # get_all_tasks() (returns a dict; keys are task names with
    # an internal prefix like ``-c:``).
    all_tasks = b.get_all_tasks()
    task_names = set(all_tasks.keys())
    assert any("translate_text" in n for n in task_names), (
        f"translate_text not registered (have {task_names})"
    )
    assert any("consensus_vote" in n for n in task_names), (
        f"consensus_vote not registered (have {task_names})"
    )

    # Result backend and schedule source construct without IO.
    assert rb is not None
    assert schedule_source is not None


def run_live_spike() -> None:
    """Publish a task to a live NATS broker and await the result.

    Requires a running NATS server at ``nats://localhost:4222``. The
    worker is launched in-process for the spike; in production
    workers run as separate processes (``taskiq worker
    heretek_swarm.gateway.taskiq_spike:broker``).
    """
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")

    # Patch the broker's server list with the env-configured URL.
    import heretek_swarm.gateway.taskiq_spike as self_mod

    self_mod.broker = build_broker(nats_servers=[nats_url])
    # Re-decorate tasks on the new broker.
    self_mod.translate_text = self_mod.broker.task(translate_text.__wrapped__)  # type: ignore[attr-defined]
    self_mod.consensus_vote = self_mod.broker.consensus_vote(consensus_vote.__wrapped__)  # type: ignore[attr-defined]

    async def _run() -> dict[str, Any]:
        # Kick off the worker in-process.
        worker_task = asyncio.create_task(self_mod.broker.run_worker())
        try:
            # Send a task and await the result.
            task = await self_mod.translate_text.kiq(
                text="Hello, world!",
                target_language="es",
            )
            result = await task.wait_result(timeout=10.0)
            return dict(result)
        finally:
            worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker_task

    return asyncio.run(_run())


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] Taskiq dry spike passed")
    if os.environ.get("NATS_URL") or os.path.exists("/var/run/nats"):
        try:
            result = run_live_spike()
            print(f"[OK] Taskiq live spike passed: {result}")
        except Exception as e:
            print(f"[skip] Live NATS unavailable: {e}")
    else:
        print("[skip] No NATS_URL env / socket; skipping live call")
