"""
Steward Pulse Loop — Heartbeat management for the Steward agent.

Extracted from runtime/main_loop.py to keep that module under 800 lines.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from heretek_swarm.runtime.main_loop import AutonomousSwarm

logger = structlog.get_logger(__name__)


async def run_steward_pulse(swarm: AutonomousSwarm) -> None:
    """Steward heartbeat pulse loop.

    Runs at health_check_interval frequency. Sets
    internal_state['_last_heartbeat'] and logs heartbeat/health data
    via the Historian agent.  Uses the None-guard pattern — missing
    steward or historian agents log a warning and skip gracefully.
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
