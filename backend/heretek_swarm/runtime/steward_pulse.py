"""
Steward Pulse Loop — Heartbeat management for the Steward agent.

Extracted from runtime/main_loop.py to keep that module under 800 lines.

Also feeds collected metrics into Sentinel's anomaly monitor on each pulse
(D002 fire-and-forget dispatch).  Anomaly detection is non-blocking — the
pulse never delays its heartbeat interval waiting for Sentinel.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from heretek_swarm.runtime.main_loop import AutonomousSwarm

logger = structlog.get_logger(__name__)

# Per D002: anomaly detection is allowed to run for at most this many
# seconds before we give up and continue the pulse loop.
_ANOMALY_SCAN_TIMEOUT = 5.0  # seconds

# Per D002: rulings older than this many seconds are skipped (fire-and-forget).
_RULING_EXPIRY_SECONDS = 60.0  # seconds


async def _collect_swarm_metrics(supervisor: Any) -> dict[str, float]:
    """Collect swarm-level metrics for anomaly monitoring.

    Returns a lightweight metrics dict suitable for passing to
    `sentinel.monitor_agent_behavior()`.
    """
    stats = supervisor.get_statistics()
    return {
        "active_actors": float(stats.get("active_actors", 0)),
        "total_errors": float(stats.get("total_errors", 0)),
        "total_restarts": float(stats.get("total_restarts", 0)),
    }


async def _run_anomaly_scan(
    sentinel: Any,
    supervisor: Any,
) -> int:
    """Run anomaly detection across swarm + per-actor health.

    Returns the total number of alerts generated (0 if none).
    Never raises — exceptions are caught and logged internally.
    """
    alert_count = 0

    try:
        # Swarm-level health check
        swarm_metrics = await _collect_swarm_metrics(supervisor)
        alerts = await asyncio.wait_for(
            sentinel.monitor_agent_behavior(
                agent_id="steward",
                metrics=swarm_metrics,
            ),
            timeout=_ANOMALY_SCAN_TIMEOUT,
        )
        alert_count += len(alerts)

        # Per-actor health: only actors with non-zero errors
        all_status = await supervisor.get_all_status()
        for actor_id, status in all_status.items():
            if status.error_count > 0 or supervisor.restart_counts.get(actor_id, 0) > 0:
                actor_metrics = {
                    "error_count": float(status.error_count),
                    "restart_count": float(supervisor.restart_counts.get(actor_id, 0)),
                }
                try:
                    alerts = await asyncio.wait_for(
                        sentinel.monitor_agent_behavior(
                            agent_id=actor_id,
                            metrics=actor_metrics,
                        ),
                        timeout=_ANOMALY_SCAN_TIMEOUT,
                    )
                    alert_count += len(alerts)
                except asyncio.TimeoutError:
                    logger.debug(
                        "steward_pulse_anomaly_scan_timeout_per_actor",
                        agent_id=actor_id,
                        timeout_s=_ANOMALY_SCAN_TIMEOUT,
                    )
    except asyncio.TimeoutError:
        logger.debug(
            "steward_pulse_anomaly_scan_timeout",
            timeout_s=_ANOMALY_SCAN_TIMEOUT,
        )

    return alert_count


async def _apply_pending_tribunal_rulings(
    steward: Any,
    sentinel: Any,
) -> None:
    """Apply pending Tribunal rulings to the behavioral baseline.

    Iterates sentinel.tribunal._rulings to find rulings not yet applied.
    Tracks applied rulings in steward.internal_state to avoid re-application.

    Per D002:
    - Rulings older than _RULING_EXPIRY_SECONDS are skipped (expired).
    - Each applied ruling logs ``steward_baseline_updated``.
    - Expired rulings log ``tribunal_ruling_expired`` at WARNING.
    """
    applied: set[str] = steward.internal_state.setdefault(
        "_applied_tribunal_rulings", set()
    )
    now = datetime.now(UTC)

    try:
        rulings = dict(sentinel.tribunal._rulings)
    except Exception:
        return  # Tribunal not yet populated

    for ruling_id, ruling in rulings.items():
        if ruling_id in applied:
            continue

        # Parse timestamp — may be ISO string or datetime object
        ruling_ts = ruling.timestamp
        if isinstance(ruling_ts, str):
            ruling_ts = datetime.fromisoformat(
                ruling_ts.replace("Z", "+00:00")
            )

        # D002: skip expired rulings
        if (now - ruling_ts) > timedelta(seconds=_RULING_EXPIRY_SECONDS):
            logger.warning(
                "tribunal_ruling_expired",
                ruling_id=ruling_id,
                case_id=ruling.case_id,
                ruling_age_seconds=(now - ruling_ts).total_seconds(),
            )
            applied.add(ruling_id)
            continue

        # Apply ruling to behavioral baseline via immune manager
        try:
            if hasattr(sentinel, "_immune_manager"):
                immune_mgr = sentinel._immune_manager
                if hasattr(immune_mgr, "_immune_system"):
                    immune_system = immune_mgr._immune_system
                    # Extract pattern_id from the case/anomaly context if available
                    # The anomaly_id from the case's original_decision_id maps back
                    # to the pattern that triggered this.
                    case = sentinel.tribunal._cases.get(ruling.case_id)
                    anomaly_id = (
                        case.original_decision_id if case else ruling.case_id
                    )

                    # Request a baseline update from the immune system
                    # Use the anomaly_id as the pattern lookup key
                    immune_system.request_baseline_update(
                        pattern_id=anomaly_id,
                        requesting_agent_id="steward",
                    )

                    logger.info(
                        "steward_baseline_updated",
                        ruling_id=ruling_id,
                        case_id=ruling.case_id,
                        ruling_type=(
                            ruling.ruling_type.value
                            if hasattr(ruling.ruling_type, "value")
                            else str(ruling.ruling_type)
                        ),
                        anomaly_id=anomaly_id,
                    )
                    applied.add(ruling_id)
                else:
                    # No immune system, still mark as applied
                    logger.debug(
                        "steward_baseline_update_skipped_no_immune",
                        ruling_id=ruling_id,
                    )
                    applied.add(ruling_id)
            else:
                logger.debug(
                    "steward_baseline_update_skipped_no_manager",
                    ruling_id=ruling_id,
                )
                applied.add(ruling_id)
        except Exception as e:
            logger.error(
                "steward_baseline_update_failed",
                ruling_id=ruling_id,
                error=str(e),
            )
            # Still mark as applied to avoid repeated failures
            applied.add(ruling_id)


async def run_steward_pulse(swarm: AutonomousSwarm) -> None:
    """Steward heartbeat pulse loop.

    Runs at health_check_interval frequency. Sets
    internal_state['_last_heartbeat'] and logs heartbeat/health data
    via the Historian agent.  Uses the None-guard pattern — missing
    steward or historian agents log a warning and skip gracefully.

    Also feeds collected metrics to Sentinel's anomaly monitor on
    each pulse (D002 fire-and-forget).  Anomaly detection is
    non-blocking — the pulse never delays its heartbeat interval
    waiting for Sentinel.
    """
    while swarm._running:
        try:
            steward = swarm.supervisor.actors.get("steward") if swarm.supervisor else None
            if steward is not None:
                # Record heartbeat on steward's internal state
                steward.internal_state["_last_heartbeat"] = datetime.now(UTC).isoformat()

                # Collect heartbeat data
                pulse_data = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "active_actors": len(swarm.supervisor.actors) if swarm.supervisor else 0,
                    "deliberations_active": len(getattr(steward, "active_deliberations", {})),
                    "heartbeat_healthy": True,
                }

                # ── Sentinel anomaly detection (D002 fire-and-forget) ───
                sentinel = (
                    swarm.supervisor.actors.get("sentinel")
                    if swarm.supervisor else None
                )
                if sentinel is not None and hasattr(sentinel, "_anomaly_monitor"):
                    alert_count = await _run_anomaly_scan(
                        sentinel=sentinel,
                        supervisor=swarm.supervisor,
                    )
                    if alert_count > 0:
                        # Signal: anomalies were detected
                        logger.warning(
                            "steward_pulse_anomaly_detected",
                            alert_count=alert_count,
                            timestamp=pulse_data["timestamp"],
                        )
                        pulse_data["heartbeat_healthy"] = False
                elif sentinel is None:
                    logger.warning("steward_pulse_sentinel_skipped_no_sentinel")
                # else: sentinel present but no _anomaly_monitor (unlikely
                # but not an error — monitor may be disabled by config)

                # ── Tribunal ruling application (D002: fire-and-forget) ──
                if sentinel is not None and hasattr(sentinel, "tribunal"):
                    await _apply_pending_tribunal_rulings(
                        steward=steward,
                        sentinel=sentinel,
                    )

                # Log via Historian
                historian = (
                    swarm.supervisor.actors.get("historian") if swarm.supervisor else None
                )
                if historian is not None:
                    await historian.log_event(
                        "steward_pulse",
                        "steward",
                        pulse_data,
                    )
                    logger.info("steward_pulse_logged", pulse_data=pulse_data)
                else:
                    logger.warning("steward_pulse_historian_skipped_no_historian")
            else:
                logger.warning("steward_pulse_skipped_no_steward")

            await asyncio.sleep(swarm._health_check_interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("steward_pulse_error", error=str(e))
            await asyncio.sleep(swarm._health_check_interval)
