"""
Steward Agent - Overall coordination and governance.

This module implements the Steward agent extracted from triad.py.
The Steward is the primary coordinator for the Triad, responsible for:
- Initiating deliberation processes
- Coordinating between Triad members
- Making final executive decisions
- Managing system governance and policy
- Overseeing resource allocation
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import (
    DeliberationMixin,
    HealthReportingMixin,
    LearningMixin,
    MemoryMixin,
    PatternMixin,
    TribunalMixin,
    ValidationMixin,
)

logger = structlog.get_logger("StewardAgent")


class StewardAgent(
    HealthReportingMixin,
    ValidationMixin,
    DeliberationMixin,
    PatternMixin,
    MemoryMixin,
    LearningMixin,
    TribunalMixin,
    AgentActor,
):
    """
    Steward Agent - Overall coordination and governance.

    The Steward is the primary coordinator for the Triad, responsible for:
    - Initiating deliberation processes
    - Coordinating between Triad members
    - Making final executive decisions
    - Managing system governance and policy
    - Overseeing resource allocation
    """

    def __init__(
        self,
        agent_id: str = "steward",
        name: str = "Steward",
        description: str = "Triad coordinator and governance agent",
        swarms_agent: Agent | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Steward agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=["triad", "coordination", "governance", "decisions"],
            capabilities=[
                "coordination",
                "governance",
                "decision-making",
                "resource-management",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        # Steward-specific state
        self.active_deliberations: dict[str, dict[str, Any]] = {}
        self._deliberations = self.active_deliberations  # alias for test compatibility
        self.governance_policies: dict[str, Any] = {}
        self._policies = self.governance_policies  # alias for test compatibility
        self.resource_allocations: dict[str, float] = {}

        # Initialize mixin-required state
        self._pattern_emitted: set[str] = set()
        self._active_deliberations: dict[str, str] = {}

        self._agent_heartbeats: dict[str, str] = {}  # agent_id -> last heartbeat ISO timestamp
        self._heartbeat_timeout: float = 15.0  # seconds before declaring failure
        self._monitor_task: asyncio.Task | None = None
        self._failed_agents: set[str] = set()
        self._restart_cooldowns: dict[str, float] = {}
        self._restart_base_delay: float = 10.0

        # GOV-01-F: Steward availability tracking
        self._consecutive_missed_heartbeats: int = 0
        self._heartbeat_interval: float = 10.0  # seconds between heartbeats
        self._max_missed_heartbeats: int = 3  # failover threshold

        # GOV-05-Q: Quorum constants
        self.QUORUM_MIN_AGENTS: int = 3  # Minimum for triad + 1
        self.QUORUM_TRIAD_WEIGHT: float = 0.4  # Triad votes = 40% of total
        self.QUORUM_CONSENSUS_THRESHOLD: float = 0.67  # 2/3 required for non-critical
        self.QUORUM_CRITICAL_THRESHOLD: float = 0.75  # 3/4 for critical decisions
        self._quorum_metrics: dict[str, Any] = {}

        logger.info(f"[{self.agent_id}] Steward agent initialized")

    async def initialize(self) -> None:
        """Initialize the Steward agent."""
        # Register message handlers
        self.register_handler("start_deliberation", self._handle_start_deliberation)
        self.register_handler("request_decision", self._handle_request_decision)
        self.register_handler("report_status", self._handle_report_status)
        self.register_handler("policy_update", self._handle_policy_update)
        self.register_handler("heartbeat", self._handle_agent_heartbeat)

        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info(f"[{self.agent_id}] Steward initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming messages.

        Args:
            message: Actor message to process
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    exc_info=True,
                )
                self.error_count += 1
                # Send error response if reply_to is specified
                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        correlation_id=message.correlation_id,
                    )
        else:
            logger.warning(f"[{self.agent_id}] Unhandled message type: {message.message_type}")

    async def _handle_start_deliberation(self, message: ActorMessage) -> None:
        """Handle deliberation start requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("start_deliberation", message.content)
            if validated:
                deliberation_id = validated.deliberation_id
                topic = validated.topic
                triad_members = validated.triad_members
            else:
                # Fallback to unvalidated access
                # Support both deliberation_id/topic and session_id/problem field names
                deliberation_id = message.content.get("deliberation_id") or message.content.get(
                    "session_id"
                )
                topic = message.content.get("topic") or message.content.get("problem")
                triad_members = message.content.get("triad_members", [])

                if not deliberation_id or not topic:
                    # Auto-generate if missing
                    deliberation_id = (
                        deliberation_id or f"del_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
                    )
                    topic = topic or "unspecified"
        except (ValueError, Exception) as e:
            logger.warning(f"[{self.agent_id}] Deliberation validation issue, using fallback: {e}")
            # Fallback: support both deliberation_id/topic and session_id/problem field names
            deliberation_id = (
                message.content.get("deliberation_id")
                or message.content.get("session_id")
                or f"del_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            )
            topic = message.content.get("topic") or message.content.get("problem") or "unspecified"
            triad_members = message.content.get("triad_members", [])

        # Initialize deliberation
        # P2-1 fix: Use timezone-aware datetime
        self.active_deliberations[deliberation_id] = {
            "topic": topic,
            "triad_members": triad_members,
            "status": "initiated",
            "started_at": datetime.now(UTC).isoformat(),
            "votes": {},
        }

        logger.info(f"[{self.agent_id}] Started deliberation {deliberation_id} on topic: {topic}")

        # Notify triad members
        for member_id in triad_members:
            await self.send_to_actor(
                target_actor_id=member_id,
                message_type="deliberation_request",
                content={
                    "deliberation_id": deliberation_id,
                    "topic": topic,
                    "steward_id": self.agent_id,
                },
            )

    async def _handle_request_decision(self, message: ActorMessage) -> None:
        """Handle decision requests."""
        request_id = message.content.get("request_id")
        session_id = message.content.get("session_id")
        decision_context = message.content.get("context", {})

        # Advance deliberation phase when a triad member requests decision
        if session_id and session_id in self._deliberations:
            current_phase = self._deliberations[session_id].get("phase", "alpha")
            phase_progression = {"alpha": "beta", "beta": "charlie", "charlie": "complete"}
            next_phase = phase_progression.get(current_phase, current_phase)
            self._deliberations[session_id]["phase"] = next_phase
            logger.info(
                f"[{self.agent_id}] Deliberation {session_id} phase: {current_phase} -> {next_phase}"
            )

        logger.info(f"[{self.agent_id}] Processing decision request: {request_id}")

        # Make executive decision or delegate to triad
        if self.swarms_agent:
            try:
                decision = await self.run_with_llm(
                    prompt=f"Make an executive decision on: {decision_context}", timeout=60
                )
                await self.send(
                    topic="decisions",
                    content={
                        "message_type": "decision_response",
                        "request_id": request_id,
                        "decision": decision,
                        "source": "steward",
                    },
                    correlation_id=message.correlation_id,
                )
            except Exception as e:
                logger.error(f"[{self.agent_id}] Decision error: {e}")
        else:
            # Fallback logic
            await self.send(
                topic="decisions",
                content={
                    "message_type": "decision_response",
                    "request_id": request_id,
                    "decision": "defer_to_triad",
                    "source": "steward",
                },
                correlation_id=message.correlation_id,
            )

    async def _handle_report_status(self, message: ActorMessage) -> None:
        """Handle status report requests - publish current status."""
        reporter_id = message.content.get("agent_id")
        requester = message.content.get("requester", message.sender)
        status = message.content.get("status", {})

        logger.debug(f"[{self.agent_id}] Status report from {reporter_id or requester}")

        # Update internal tracking
        if reporter_id:
            self.update_state(f"status:{reporter_id}", status)

        # Publish status back to requester
        await self.send(
            topic="status",
            content={
                "message_type": "status_response",
                "agent_id": self.agent_id,
                "state": self.state.value,
                "active_deliberations": len(self._deliberations),
                "policies_count": len(self._policies),
                "requester": requester,
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_policy_update(self, message: ActorMessage) -> None:
        """Handle policy update requests."""
        policy_id = message.content.get("policy_id")
        policy_data = message.content.get("policy_data") or {
            k: v for k, v in message.content.items() if k not in ("policy_id", "reply_to")
        }

        if policy_id:
            # P2-1 fix: Use timezone-aware datetime
            self.governance_policies[policy_id] = {
                **policy_data,
                "updated_at": datetime.now(UTC).isoformat(),
                "updated_by": message.sender,
            }
            logger.info(f"[{self.agent_id}] Updated policy: {policy_id}")

    async def coordinate_triad(
        self,
        topic: str | None = None,
        triad_members: list[str] | None = None,
        problem: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Coordinate a triad deliberation.

        Args:
            topic: Deliberation topic
            triad_members: List of triad member IDs
            problem: Alternative name for topic
            context: Additional context for deliberation

        Returns:
            Deliberation ID
        """
        # P2-1 fix: Use timezone-aware datetime
        deliberation_id = f"del_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        effective_topic = topic or problem

        await self.send(
            topic="triad",
            content={
                "message_type": "start_deliberation",
                "deliberation_id": deliberation_id,
                "topic": effective_topic,
                "triad_members": triad_members or [],
                "context": context or {},
            },
        )

        # Store deliberation for observability
        deliberation_record = {
            "session_id": deliberation_id,
            "topic": effective_topic,
            "phase": "initiated",
            "status": "pending",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.active_deliberations[deliberation_id] = deliberation_record

        return deliberation_record

    def get_deliberation_status(self, deliberation_id: str) -> dict[str, Any] | None:
        """Get status of a deliberation."""
        return self.active_deliberations.get(deliberation_id)

    def get_all_deliberation_statuses(self) -> dict[str, dict[str, Any]]:
        """Get status of all active deliberations."""
        return dict(self.active_deliberations)

    def get_governance_policy(self, policy_id: str) -> dict[str, Any] | None:
        """Get a governance policy."""
        return self.governance_policies.get(policy_id)

    async def _handle_agent_heartbeat(self, message: ActorMessage) -> None:
        """Store heartbeat timestamps from monitored agents."""
        agent_id = message.content.get("agent_id")
        timestamp = message.content.get("timestamp")
        if agent_id and timestamp:
            self._agent_heartbeats[agent_id] = timestamp

    def check_agent_health(self, agent_id: str) -> bool:
        """Check if agent's last heartbeat is within timeout."""
        if agent_id not in self._agent_heartbeats:
            return False
        last_hb = datetime.fromisoformat(self._agent_heartbeats[agent_id])
        cutoff = datetime.now(UTC) - timedelta(seconds=self._heartbeat_timeout)
        return last_hb >= cutoff

    def detect_heartbeat_failure(self) -> list[str]:
        """Return list of agent IDs with stale heartbeats."""
        cutoff = datetime.now(UTC) - timedelta(seconds=self._heartbeat_timeout)
        failed = []
        for agent_id, ts_str in self._agent_heartbeats.items():
            last_hb = datetime.fromisoformat(ts_str)
            if last_hb < cutoff:
                failed.append(agent_id)
        return sorted(failed)

    async def _monitor_loop(self) -> None:
        """Periodically check for heartbeat failures."""
        while self._running:
            await asyncio.sleep(5.0)
            if not self._running:
                break
            failed = self.detect_heartbeat_failure()
            for agent_id in failed:
                await self._handle_agent_failure(agent_id)

    async def _handle_agent_failure(
        self, agent_id: str, supervisor: Optional["ActorSupervisor"] = None
    ) -> None:
        """Record and log an agent heartbeat failure, attempt restart with backoff."""
        if agent_id in self._failed_agents:
            return

        now = datetime.now(UTC).timestamp()
        if agent_id in self._restart_cooldowns and now < self._restart_cooldowns[agent_id]:
            logger.debug(f"[{self.agent_id}] Restart cooldown active for {agent_id}, skipping")
            return
        if agent_id in self._restart_cooldowns:
            del self._restart_cooldowns[agent_id]

        self._failed_agents.add(agent_id)
        self.error_count += 1
        logger.warning(f"[{self.agent_id}] Heartbeat failure detected for agent: {agent_id}")

        await self.send(
            topic="system.recovery",
            content={
                "message_type": "recovery_event",
                "agent_id": agent_id,
                "status": "started",
                "restart_count": len([a for a in self._failed_agents if a == agent_id]),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        if supervisor is not None:
            try:
                restart_count_before = supervisor.restart_counts.get(agent_id, 0)
                await supervisor._attempt_restart(agent_id)
                restart_count_after = supervisor.restart_counts.get(agent_id, 0)

                if restart_count_after > restart_count_before:
                    if agent_id in self._restart_cooldowns:
                        del self._restart_cooldowns[agent_id]
                    self._failed_agents.discard(agent_id)
                    logger.info(
                        f"[{self.agent_id}] Agent {agent_id} recovered successfully",
                        extra={"restart_count": restart_count_after},
                    )

                    await self.send(
                        topic="system.recovery",
                        content={
                            "message_type": "recovery_event",
                            "agent_id": agent_id,
                            "status": "completed",
                            "restart_count": restart_count_after,
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    )
                else:
                    backoff_seconds = min(300, self._restart_base_delay * (2**restart_count_after))
                    self._restart_cooldowns[agent_id] = now + backoff_seconds
                    await self._emit_recovery_failed(agent_id, restart_count_after)

            except Exception as e:
                logger.error(f"[{self.agent_id}] Restart attempt failed for {agent_id}: {e}")
                await self._emit_recovery_failed(agent_id, 0)

    async def _emit_recovery_failed(self, agent_id: str, restart_count: int) -> None:
        await self.send(
            topic="system.recovery",
            content={
                "message_type": "recovery_event",
                "agent_id": agent_id,
                "status": "failed",
                "restart_count": restart_count,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    async def initiate_failover(self, agent_id: str) -> None:
        """Send failover message via event mesh."""
        logger.warning(f"[{self.agent_id}] Initiating failover for agent: {agent_id}")
        await self.send(
            topic="system.failover",
            content={
                "message_type": "failover_request",
                "failed_agent_id": agent_id,
                "steward_id": self.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    def is_available(self) -> bool:
        """
        Check if Steward is available (heartbeat healthy).

        Returns False when heartbeat missed for 3 consecutive intervals
        (>30 seconds with default 10s interval).

        GOV-01-F: Steward failover detection
        """
        if not self._agent_heartbeats:
            return True  # No heartbeats recorded yet, assume available

        cutoff = datetime.now(UTC) - timedelta(
            seconds=self._heartbeat_interval * self._max_missed_heartbeats
        )
        for ts_str in self._agent_heartbeats.values():
            last_hb = datetime.fromisoformat(ts_str)
            if last_hb >= cutoff:
                return True
        return False

    async def publish_heartbeat(self) -> None:
        """Publish heartbeat to NATS for Charlie to monitor."""
        await self.send(
            topic="system.heartbeat",
            content={
                "message_type": "heartbeat",
                "agent_id": self.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "available": True,
            },
        )

    async def publish_recovery(self) -> None:
        """Publish recovery event when Steward resumes after failover."""
        logger.info(f"[{self.agent_id}] Publishing STEWARD_RECOVERY event")
        await self.send(
            topic="system.recovery",
            content={
                "message_type": "steward_recovery",
                "agent_id": self.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "from": "charlie",
                "to": "steward",
            },
        )

    def get_quorum_metrics(self) -> dict[str, Any]:
        """Get quorum attendance metrics."""
        return dict(self._quorum_metrics)

    async def convene_triad(
        self,
        topic: str | None = None,
        triad_members: list[str] | None = None,
        problem: str | None = None,
        context: dict[str, Any] | None = None,
        vote_weights: dict[str, float] | None = None,
    ) -> str | None:
        """
        Coordinate a triad deliberation with quorum check.

        GOV-05-Q: Integrates quorum logic into triad coordination.
        """
        deliberation_id = f"del_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        effective_topic = topic or problem
        participating = triad_members or []

        # GOV-05-Q: Quorum check before proceeding
        if vote_weights:
            weights = vote_weights
        else:
            weights = {m: 1.0 for m in participating}

        quorum_met, quorum_details = self.check_quorum(participating, weights)

        self._quorum_metrics = {
            "quorum_met": quorum_met,
            "participating_agents": participating,
            "triad_weight_ratio": quorum_details.get("triad_weight_ratio", 0.0),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Publish quorum check event to NATS
        await self.send(
            topic="triad.quorum_check",
            content={
                "message_type": "quorum_check",
                "deliberation_id": deliberation_id,
                "quorum_met": quorum_met,
                "participating_agents": participating,
                "triad_weight_ratio": quorum_details.get("triad_weight_ratio", 0.0),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        if not quorum_met:
            logger.error(
                f"[{self.agent_id}] Quorum not met for triad {deliberation_id}, deliberation blocked"
            )
            return None

        await self.send(
            topic="triad",
            content={
                "message_type": "start_deliberation",
                "deliberation_id": deliberation_id,
                "topic": effective_topic,
                "triad_members": participating,
                "context": context or {},
            },
        )

        deliberation_record = {
            "session_id": deliberation_id,
            "topic": effective_topic,
            "phase": "initiated",
            "status": "pending",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.active_deliberations[deliberation_id] = deliberation_record

        return deliberation_id

    def check_quorum(
        self,
        participating_agents: list[str],
        vote_weights: dict[str, float],
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if quorum is met for deliberation to proceed.

        GOV-05-Q: Quorum requires minimum agents AND triad weight threshold.

        Args:
            participating_agents: List of agent IDs participating
            vote_weights: Dict mapping agent_id to vote weight

        Returns:
            Tuple of (quorum_met: bool, details: dict)
        """
        if not participating_agents or not vote_weights:
            return False, {
                "has_min_agents": False,
                "has_triad_weight": False,
                "triad_weight_ratio": 0.0,
            }

        total_weight = sum(vote_weights.values())
        triad_agents = ["alpha", "beta", "charlie"]
        triad_votes = sum(v for a, v in vote_weights.items() if a in triad_agents)

        has_min_agents = len(participating_agents) >= self.QUORUM_MIN_AGENTS
        has_triad_weight = (
            (triad_votes / total_weight) >= self.QUORUM_TRIAD_WEIGHT if total_weight > 0 else False
        )
        triad_weight_ratio = (triad_votes / total_weight) if total_weight > 0 else 0.0

        details = {
            "has_min_agents": has_min_agents,
            "has_triad_weight": has_triad_weight,
            "triad_weight_ratio": triad_weight_ratio,
            "total_weight": total_weight,
            "triad_votes": triad_votes,
            "participating_count": len(participating_agents),
        }

        quorum_met = has_min_agents and has_triad_weight

        logger.info(
            f"[{self.agent_id}] Quorum check: met={quorum_met}, "
            f"min_agents={has_min_agents}, triad_weight={has_triad_weight}, "
            f"ratio={triad_weight_ratio:.2f}"
        )

        return quorum_met, details

    async def _cancel_tasks(self) -> None:
        """Cancel all running tasks including the heartbeat monitor."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        await super()._cancel_tasks()
