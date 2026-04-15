"""
Chronos Agent - Temporal & Scheduling Specialist

Tier 5 Coordination Agent responsible for:
- Time-based task scheduling and execution
- Deadline management and tracking
- Temporal coordination across agents
- Calendar and timeline management
- Time-based analytics and optimization

Author: Heretek Swarm Collective
Date: 2026-04-06
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import structlog

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins.deliberation import DeliberationMixin
from heretek_swarm.actors.mixins.learning import LearningMixin
from heretek_swarm.actors.mixins.memory import MemoryMixin
from heretek_swarm.actors.mixins.pattern import PatternMixin
from heretek_swarm.actors.mixins.validation import ValidationMixin
from heretek_swarm.actors.validation import validate_message

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine

# INTG-04: Time Perception & Dilation
from heretek_swarm.coordination.time_dilation import (
    AnchorSource,
    ExecutionContext,
    OverloadDetector,
    TimeDilationCalculator,
    TimePerceptionManager,
)

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

logger = structlog.get_logger(__name__)


class ScheduleStatus(Enum):
    """Status of a scheduled item."""

    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    MISSED = "missed"
    FAILED = "failed"


class RecurrenceType(Enum):
    """Type of recurrence pattern."""

    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CRON = "cron"
    INTERVAL = "interval"


class Priority(Enum):
    """Task priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class ScheduledTask:
    """A scheduled task."""

    task_id: str
    name: str
    description: str
    scheduled_at: datetime
    status: ScheduleStatus = ScheduleStatus.PENDING
    priority: Priority = Priority.NORMAL
    recurrence: RecurrenceType | None = None
    recurrence_config: dict[str, Any] = field(default_factory=dict)
    target_agents: list[str] = field(default_factory=list)
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    deadline: datetime | None = None
    completed_at: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    max_runs: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "scheduled_at": self.scheduled_at.isoformat(),
            "status": self.status.value,
            "priority": self.priority.value,
            "recurrence": self.recurrence.value if self.recurrence else None,
            "recurrence_config": self.recurrence_config,
            "target_agents": self.target_agents,
            "action": self.action,
            "payload": self.payload,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "max_runs": self.max_runs,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Deadline:
    """A deadline tracking entry."""

    deadline_id: str
    name: str
    due_at: datetime
    assigned_to: list[str] = field(default_factory=list)
    status: str = "pending"  # pending, met, missed
    warning_thresholds: list[timedelta] = field(default_factory=list)
    warnings_sent: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "deadline_id": self.deadline_id,
            "name": self.name,
            "due_at": self.due_at.isoformat(),
            "assigned_to": self.assigned_to,
            "status": self.status,
            "warning_thresholds": [str(t) for t in self.warning_thresholds],
            "warnings_sent": list(self.warnings_sent),
            "metadata": self.metadata,
            "time_remaining": str(self.due_at - datetime.now(UTC)),
        }


class ChronosAgent(
    ValidationMixin, AgentActor, PatternMixin, DeliberationMixin, MemoryMixin, LearningMixin
):
    """
    Temporal & Scheduling Specialist.

    Responsibilities:
    - Schedule and execute time-based tasks
    - Manage deadlines and send warnings
    - Coordinate temporal activities across agents
    - Maintain calendars and timelines
    - Provide time-based analytics

    Message Handlers:
    - schedule_task: Schedule a new task
    - cancel_task: Cancel a scheduled task
    - pause_task: Pause a scheduled task
    - resume_task: Resume a paused task
    - get_task_status: Get status of a scheduled task
    - set_deadline: Set a deadline
    - check_deadline: Check deadline status
    - get_timeline: Get timeline of scheduled items
    - get_schedule: Get schedule for time range
    - register_reminder: Register a time-based reminder
    """

    def __init__(
        self,
        agent_id: str | None = None,
        config: dict[str, Any] | None = None,
        # Session 44: Integration components
        pattern_extractor: PatternExtractor | None = None,
        deliberation_engine: SwarmDeliberationEngine | None = None,
        access_analyzer: AccessPatternAnalyzer | None = None,
        zero_trust_validator: ZeroTrustValidator | None = None,
    ):
        super().__init__(
            agent_id=agent_id or f"chronos_{uuid.uuid4().hex[:8]}",
            config=config or {},
        )

        self._config: dict[str, Any] = {}

        # Task scheduling
        self._tasks: dict[str, ScheduledTask] = {}
        self._task_queue: list[tuple[datetime, str]] = []  # (scheduled_at, task_id)
        self._max_tasks: int = self._config.get("max_tasks", 1000)

        # Deadlines
        self._deadlines: dict[str, Deadline] = {}
        self._max_deadlines: int = self._config.get("max_deadlines", 500)

        # Scheduler control
        self._scheduler_running: bool = False
        self._scheduler_task: asyncio.Task | None = None
        self._check_interval: float = self._config.get("check_interval", 1.0)  # seconds

        # Calendars
        self._calendars: dict[str, list[str]] = {}  # calendar_id -> task_ids

        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(
            min_support=3, min_confidence=0.6
        )

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: dict[str, str] = {}
        self._pattern_emitted: set[str] = set()

        # INTG-04: Time perception manager
        self._time_manager: TimePerceptionManager | None = None
        self._dilation_calculator: TimeDilationCalculator | None = None
        self._overload_detector: OverloadDetector | None = None
        self._execution_contexts: dict[str, ExecutionContext] = {}

        # INTG-04: Configuration
        self._enable_time_dilation: bool = self._config.get("enable_time_dilation", True)
        self._anchor_interval_seconds: float = self._config.get("anchor_interval", 300)
        self._overload_threshold: float = self._config.get("overload_threshold", 0.8)
        self._max_contexts: int = self._config.get("max_contexts", 500)

        logger.info(
            "chronos_initialized",
            agent_id=self.agent_id,
            max_tasks=self._max_tasks,
            check_interval=self._check_interval,
        )

    async def initialize(self) -> None:
        """Initialize the Chronos agent."""
        await super().initialize()

        # INTG-04: Initialize time perception components
        if self._enable_time_dilation:
            self._time_manager = TimePerceptionManager(
                max_contexts=self._max_contexts,
                drift_threshold_seconds=5.0,
                anchor_interval=timedelta(seconds=self._anchor_interval_seconds),
            )
            self._dilation_calculator = TimeDilationCalculator()
            self._overload_detector = OverloadDetector()
            self._execution_contexts = {}

        self._scheduler_running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("chronos_scheduler_started")

    async def terminate(self) -> None:
        """Terminate the Chronos agent."""
        self._scheduler_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._scheduler_task
            self._scheduler_task = None
            logger.info("chronos_scheduler_stopped")
        await super().terminate()

    async def _validate_message(self, message: ActorMessage) -> dict[str, Any]:
        """Validate incoming message content."""
        try:
            validated = validate_message(message.message_type, message.content)
            if hasattr(validated, "dict"):
                return validated.dict()
            return validated
        except Exception as e:
            logger.debug("chronos_message_parse_failed", error=str(e))
            return message.content

    async def _run_scheduler(self) -> None:
        """Main scheduler loop - checks and executes due tasks."""
        while self._scheduler_running:
            try:
                now = datetime.now(UTC)

                # Check for due tasks
                due_tasks = []
                remaining_queue = []

                for scheduled_at, task_id in self._task_queue:
                    if task_id in self._tasks:
                        task = self._tasks[task_id]
                        if task.status == ScheduleStatus.PENDING and scheduled_at <= now:
                            due_tasks.append(task)
                        else:
                            remaining_queue.append((scheduled_at, task_id))

                self._task_queue = remaining_queue

                # Execute due tasks
                for task in due_tasks:
                    await self._execute_task(task)

                # Check deadlines
                await self._check_deadlines()

                # INTG-04: Periodic anchoring check
                if self._time_manager and self._enable_time_dilation:
                    await self._time_manager.check_and_anchor()

                # INTG-04: Check context deadlines and update metrics
                await self._check_context_deadlines()

                # INTG-04: Update overload state
                self._update_overload_state()

                # INTG-04: Check if delegation needed
                if self._should_delegate():
                    await self._handle_overload_delegation()

                # Sort queue by time
                self._task_queue.sort(key=lambda x: x[0])

            except Exception as e:
                logger.error("scheduler_error", error=str(e))

            await asyncio.sleep(self._check_interval)

    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        try:
            task.status = ScheduleStatus.ACTIVE
            task.run_count += 1

            logger.info(
                "executing_scheduled_task",
                task_id=task.task_id,
                name=task.name,
                run_count=task.run_count,
            )

            # Notify target agents
            for agent_id in task.target_agents:
                await self.send(
                    agent_id,
                    ActorMessage(
                        message_type=task.action or "scheduled_task",
                        content={
                            "task_id": task.task_id,
                            "name": task.name,
                            "payload": task.payload,
                            "scheduled_at": task.scheduled_at.isoformat(),
                        },
                        sender_id=self.agent_id,
                    ),
                )

            task.status = ScheduleStatus.COMPLETED
            task.completed_at = datetime.now(UTC)

            # Handle recurrence
            if task.recurrence:
                await self._schedule_next_run(task)
            else:
                # Remove from queue if not recurring
                if task.task_id in self._task_queue:
                    self._task_queue.remove((task.scheduled_at, task.task_id))

        except Exception as e:
            logger.error("task_execution_failed", task_id=task.task_id, error=str(e))
            task.status = ScheduleStatus.FAILED

    async def _schedule_next_run(self, task: ScheduledTask) -> None:
        """Schedule the next run for a recurring task."""
        if not task.recurrence:
            return

        # Check max runs
        if task.max_runs and task.run_count >= task.max_runs:
            task.status = ScheduleStatus.COMPLETED
            return

        # Calculate next run time
        now = datetime.now(UTC)

        if task.recurrence == RecurrenceType.HOURLY:
            task.next_run = now + timedelta(hours=1)
        elif task.recurrence == RecurrenceType.DAILY:
            task.next_run = now + timedelta(days=1)
        elif task.recurrence == RecurrenceType.WEEKLY:
            task.next_run = now + timedelta(weeks=1)
        elif task.recurrence == RecurrenceType.MONTHLY:
            # Approximate: add 30 days
            task.next_run = now + timedelta(days=30)
        elif task.recurrence == RecurrenceType.YEARLY:
            task.next_run = now + timedelta(days=365)
        elif task.recurrence == RecurrenceType.INTERVAL:
            interval_seconds = task.recurrence_config.get("interval_seconds", 3600)
            task.next_run = now + timedelta(seconds=interval_seconds)
        elif task.recurrence == RecurrenceType.CRON:
            # Simple cron - would need full implementation for production
            task.next_run = now + timedelta(hours=1)

        if task.next_run:
            task.status = ScheduleStatus.PENDING
            task.scheduled_at = task.next_run
            self._task_queue.append((task.next_run, task.task_id))
            logger.info(
                "task_rescheduled",
                task_id=task.task_id,
                next_run=task.next_run.isoformat(),
            )

    async def _check_deadlines(self) -> None:
        """Check deadlines and send warnings."""
        now = datetime.now(UTC)

        for deadline in self._deadlines.values():
            if deadline.status != "pending":
                continue

            time_remaining = deadline.due_at - now

            if time_remaining.total_seconds() <= 0:
                deadline.status = "missed"
                logger.warning("deadline_missed", deadline_id=deadline.deadline_id)
                continue

                # Check warning thresholds
                for threshold in deadline.warning_thresholds:
                    threshold_key = str(threshold)
                    if threshold_key not in deadline.warnings_sent and time_remaining <= threshold:
                        deadline.warnings_sent.add(threshold_key)
                        await self._send_deadline_warning(deadline, threshold)

    async def _send_deadline_warning(self, deadline: Deadline, threshold: timedelta) -> None:
        """Send deadline warning notification."""
        for agent_id in deadline.assigned_to:
            await self.send(
                agent_id,
                ActorMessage(
                    message_type="deadline_warning",
                    content={
                        "deadline_id": deadline.deadline_id,
                        "name": deadline.name,
                        "due_at": deadline.due_at.isoformat(),
                        "threshold": str(threshold),
                        "time_remaining": str(deadline.due_at - datetime.now(UTC)),
                    },
                    sender_id=self.agent_id,
                ),
            )

    async def _handle_schedule_task(self, message: ActorMessage) -> None:
        """
        Schedule a new task.

        Content:
        - task_id: Optional[str]
        - name: str
        - description: str
        - scheduled_at: str (ISO8601)
        - priority: Optional[int] (1-5)
        - recurrence: Optional[str] (once|hourly|daily|weekly|monthly|yearly|interval|cron)
        - recurrence_config: Optional[Dict]
        - target_agents: Optional[List[str]]
        - action: Optional[str]
        - payload: Optional[Dict]
        - deadline: Optional[str] (ISO8601)
        - max_runs: Optional[int]
        - metadata: Optional[Dict]
        """
        try:
            content = await self._validate_message(message)

            if len(self._tasks) >= self._max_tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task limit reached ({self._max_tasks})",
                    message.message_type,
                )
                return

            task_id = content.get("task_id") or f"task_{uuid.uuid4().hex[:12]}"

            if task_id in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} already exists",
                    message.message_type,
                )
                return

            scheduled_at_str = content.get("scheduled_at")
            scheduled_at = (
                datetime.fromisoformat(scheduled_at_str) if scheduled_at_str else datetime.now(UTC)
            )

            recurrence_str = content.get("recurrence")
            recurrence = RecurrenceType(recurrence_str) if recurrence_str else RecurrenceType.ONCE

            priority_value = content.get("priority", 2)
            priority = Priority(min(max(priority_value, 1), 5))

            task = ScheduledTask(
                task_id=task_id,
                name=content.get("name", "Untitled Task"),
                description=content.get("description", ""),
                scheduled_at=scheduled_at,
                priority=priority,
                recurrence=recurrence,
                recurrence_config=content.get("recurrence_config", {}),
                target_agents=content.get("target_agents", []),
                action=content.get("action", "scheduled_task"),
                payload=content.get("payload", {}),
                deadline=datetime.fromisoformat(content["deadline"])
                if content.get("deadline")
                else None,
                max_runs=content.get("max_runs"),
                metadata=content.get("metadata", {}),
            )

            self._tasks[task_id] = task
            self._task_queue.append((scheduled_at, task_id))

            logger.info(
                "task_scheduled",
                task_id=task_id,
                name=task.name,
                scheduled_at=scheduled_at.isoformat(),
                recurrence=recurrence.value,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_scheduled",
                    content={"task": task.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("schedule_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to schedule task: {e!s}",
                message.message_type,
            )

    async def _handle_cancel_task(self, message: ActorMessage) -> None:
        """
        Cancel a scheduled task.

        Content:
        - task_id: str
        """
        try:
            content = await self._validate_message(message)
            task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            task = self._tasks[task_id]

            if task.status in (ScheduleStatus.COMPLETED, ScheduleStatus.CANCELLED):
                await self._send_error(
                    message.sender_id,
                    f"Task already in {task.status.value} state",
                    message.message_type,
                )
                return

            task.status = ScheduleStatus.CANCELLED

            # Remove from queue
            self._task_queue = [(t, tid) for t, tid in self._task_queue if tid != task_id]

            logger.info("task_cancelled", task_id=task_id)

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_cancelled",
                    content={"task_id": task_id},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("cancel_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to cancel task: {e!s}",
                message.message_type,
            )

    async def _handle_pause_task(self, message: ActorMessage) -> None:
        """
        Pause a scheduled task.

        Content:
        - task_id: str
        """
        try:
            content = await self._validate_message(message)
            task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            task = self._tasks[task_id]

            if task.status not in (ScheduleStatus.PENDING, ScheduleStatus.ACTIVE):
                await self._send_error(
                    message.sender_id,
                    f"Cannot pause task in {task.status.value} state",
                    message.message_type,
                )
                return

            task.status = ScheduleStatus.PAUSED

            # Remove from queue while paused
            self._task_queue = [(t, tid) for t, tid in self._task_queue if tid != task_id]

            logger.info("task_paused", task_id=task_id)

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_paused",
                    content={"task_id": task_id},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("pause_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to pause task: {e!s}",
                message.message_type,
            )

    async def _handle_resume_task(self, message: ActorMessage) -> None:
        """
        Resume a paused task.

        Content:
        - task_id: str
        """
        try:
            content = await self._validate_message(message)
            task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            task = self._tasks[task_id]

            if task.status != ScheduleStatus.PAUSED:
                await self._send_error(
                    message.sender_id,
                    f"Task is not paused (current: {task.status.value})",
                    message.message_type,
                )
                return

            task.status = ScheduleStatus.PENDING
            self._task_queue.append((task.scheduled_at, task_id))

            logger.info("task_resumed", task_id=task_id)

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_resumed",
                    content={"task_id": task_id},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("resume_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to resume task: {e!s}",
                message.message_type,
            )

    async def _handle_get_task_status(self, message: ActorMessage) -> None:
        """
        Get status of a scheduled task.

        Content:
        - task_id: str
        """
        try:
            content = await self._validate_message(message)
            task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            task = self._tasks[task_id]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_status",
                    content={"task": task.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_task_status_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get task status: {e!s}",
                message.message_type,
            )

    async def _handle_set_deadline(self, message: ActorMessage) -> None:
        """
        Set a deadline.

        Content:
        - deadline_id: Optional[str]
        - name: str
        - due_at: str (ISO8601)
        - assigned_to: Optional[List[str]]
        - warning_thresholds: Optional[List[str]] (e.g., ["1 day", "1 hour"])
        - metadata: Optional[Dict]
        """
        try:
            content = await self._validate_message(message)

            if len(self._deadlines) >= self._max_deadlines:
                await self._send_error(
                    message.sender_id,
                    f"Deadline limit reached ({self._max_deadlines})",
                    message.message_type,
                )
                return

            deadline_id = content.get("deadline_id") or f"deadline_{uuid.uuid4().hex[:12]}"

            if deadline_id in self._deadlines:
                await self._send_error(
                    message.sender_id,
                    f"Deadline {deadline_id} already exists",
                    message.message_type,
                )
                return

            due_at = datetime.fromisoformat(content.get("due_at", datetime.now(UTC).isoformat()))

            # Parse warning thresholds
            thresholds = []
            for threshold_str in content.get("warning_thresholds", ["1 hour"]):
                # Simple parsing - would need more robust implementation for production
                if "day" in threshold_str:
                    days = int(threshold_str.split()[0])
                    thresholds.append(timedelta(days=days))
                elif "hour" in threshold_str:
                    hours = int(threshold_str.split()[0])
                    thresholds.append(timedelta(hours=hours))
                elif "minute" in threshold_str:
                    minutes = int(threshold_str.split()[0])
                    thresholds.append(timedelta(minutes=minutes))

            deadline = Deadline(
                deadline_id=deadline_id,
                name=content.get("name", "Untitled Deadline"),
                due_at=due_at,
                assigned_to=content.get("assigned_to", []),
                warning_thresholds=thresholds,
                metadata=content.get("metadata", {}),
            )

            self._deadlines[deadline_id] = deadline

            logger.info(
                "deadline_set",
                deadline_id=deadline_id,
                name=deadline.name,
                due_at=due_at.isoformat(),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="deadline_set",
                    content={"deadline": deadline.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("set_deadline_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to set deadline: {e!s}",
                message.message_type,
            )

    async def _handle_check_deadline(self, message: ActorMessage) -> None:
        """
        Check deadline status.

        Content:
        - deadline_id: str
        """
        try:
            content = await self._validate_message(message)
            deadline_id = content.get("deadline_id")

            if not deadline_id or deadline_id not in self._deadlines:
                await self._send_error(
                    message.sender_id,
                    f"Deadline {deadline_id} not found",
                    message.message_type,
                )
                return

            deadline = self._deadlines[deadline_id]
            now = datetime.now(UTC)
            time_remaining = deadline.due_at - now

            # Update status
            if time_remaining.total_seconds() <= 0:
                deadline.status = "missed"
            else:
                deadline.status = "pending"

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="deadline_status",
                    content={
                        "deadline": deadline.to_dict(),
                        "time_remaining_seconds": time_remaining.total_seconds(),
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("check_deadline_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to check deadline: {e!s}",
                message.message_type,
            )

    async def _handle_get_timeline(self, message: ActorMessage) -> None:
        """
        Get timeline of scheduled items.

        Content:
        - limit: Optional[int]
        - status: Optional[str]
        """
        try:
            content = await self._validate_message(message)
            limit = min(content.get("limit", 50), 100)
            status_filter = content.get("status")

            tasks = list(self._tasks.values())

            # Filter by status
            if status_filter:
                try:
                    status = ScheduleStatus(status_filter)
                    tasks = [t for t in tasks if t.status == status]
                except ValueError:
                    pass

            # Sort by scheduled_at
            tasks.sort(key=lambda t: t.scheduled_at)

            # Limit results
            tasks = tasks[:limit]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="timeline",
                    content={
                        "tasks": [t.to_dict() for t in tasks],
                        "count": len(tasks),
                        "total": len(self._tasks),
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_timeline_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get timeline: {e!s}",
                message.message_type,
            )

    async def _handle_get_schedule(self, message: ActorMessage) -> None:
        """
        Get schedule for a time range.

        Content:
        - start: str (ISO8601)
        - end: str (ISO8601)
        """
        try:
            content = await self._validate_message(message)
            start_str = content.get("start")
            end_str = content.get("end")

            start = datetime.fromisoformat(start_str) if start_str else datetime.now(UTC)
            end = datetime.fromisoformat(end_str) if end_str else start + timedelta(days=1)

            # Find tasks in range
            scheduled = [
                t.to_dict() for t in self._tasks.values() if start <= t.scheduled_at <= end
            ]

            scheduled.sort(key=lambda t: t["scheduled_at"])

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="schedule",
                    content={
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "tasks": scheduled,
                        "count": len(scheduled),
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_schedule_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get schedule: {e!s}",
                message.message_type,
            )

    async def _handle_register_reminder(self, message: ActorMessage) -> None:
        """
        Register a time-based reminder.

        Content:
        - reminder_id: Optional[str]
        - message: str
        - remind_at: str (ISO8601)
        - target_agents: Optional[List[str]]
        """
        try:
            content = await self._validate_message(message)

            reminder_id = content.get("reminder_id") or f"reminder_{uuid.uuid4().hex[:12]}"
            remind_at_str = content.get("remind_at")
            remind_at = (
                datetime.fromisoformat(remind_at_str) if remind_at_str else datetime.now(UTC)
            )
            target_agents = content.get("target_agents", [message.sender_id])

            # Create as a scheduled task
            task = ScheduledTask(
                task_id=reminder_id,
                name="Reminder",
                description=content.get("message", ""),
                scheduled_at=remind_at,
                target_agents=target_agents,
                action="reminder",
                payload={"message": content.get("message", "")},
            )

            self._tasks[reminder_id] = task
            self._task_queue.append((remind_at, reminder_id))

            logger.info(
                "reminder_registered",
                reminder_id=reminder_id,
                remind_at=remind_at.isoformat(),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="reminder_registered",
                    content={"reminder": task.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("register_reminder_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to register reminder: {e!s}",
                message.message_type,
            )

    async def _send_error(
        self,
        recipient: str,
        error_message: str,
        original_type: str,
    ) -> None:
        """Send error response."""
        await self.send(
            recipient,
            ActorMessage(
                message_type="error",
                content={"error": error_message, "original_type": original_type},
                sender_id=self.agent_id,
            ),
        )

    # INTG-04: Time Perception Handlers

    async def _handle_create_context(self, message: ActorMessage) -> None:
        """
        Create a long-running execution context.

        Content: {
            "agent_id": str,
            "task_id": str,
            "expected_duration": str | None (ISO8601 timedelta),
            "deadline": str | None (ISO8601 datetime),
            "priority": int | None (1-5),
            "metadata": dict | None,
        }

        Returns: {
            "context": ExecutionContext.to_dict(),
            "context_id": str,
        }
        """
        try:
            content = await self._validate_message(message)

            if not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Time perception not enabled",
                    message.message_type,
                )
                return

            agent_id = content.get("agent_id", message.sender_id)
            task_id = content.get("task_id", f"task_{uuid.uuid4().hex[:12]}")

            expected_duration = None
            if content.get("expected_duration"):
                td_match = content["expected_duration"]
                if "hour" in td_match:
                    hours = float(td_match.replace("hour", "").strip())
                    expected_duration = timedelta(hours=hours)
                elif "minute" in td_match:
                    minutes = float(td_match.replace("minute", "").strip())
                    expected_duration = timedelta(minutes=minutes)
                elif "second" in td_match:
                    seconds = float(td_match.replace("second", "").strip())
                    expected_duration = timedelta(seconds=seconds)

            deadline = None
            if content.get("deadline"):
                deadline = datetime.fromisoformat(content["deadline"])

            metadata = content.get("metadata", {})
            metadata["priority"] = content.get("priority", 2)

            context = self._time_manager.create_context(
                agent_id=agent_id,
                task_id=task_id,
                expected_duration=expected_duration,
                deadline=deadline,
                metadata=metadata,
            )

            self._execution_contexts[context.context_id] = context

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="execution_context_created",
                    content={
                        "context": context.to_dict(),
                        "context_id": context.context_id,
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("create_context_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to create context: {e!s}",
                message.message_type,
            )

    async def _handle_update_context(self, message: ActorMessage) -> None:
        """
        Update execution context progress.

        Content: {
            "context_id": str,
            "progress_percent": float,
            "status": str | None,
            "time_dilation_factor": float | None,
            "metadata": dict | None,
        }
        """
        try:
            content = await self._validate_message(message)
            context_id = content.get("context_id")

            if not context_id or not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Invalid context_id",
                    message.message_type,
                )
                return

            updated = self._time_manager.update_context(
                context_id=context_id,
                progress_percent=content.get("progress_percent"),
                status=content.get("status"),
                time_dilation_factor=content.get("time_dilation_factor"),
                metadata=content.get("metadata"),
            )

            if updated:
                context = self._time_manager.get_context(context_id)
                if context:
                    self._execution_contexts[context_id] = context

                await self.send(
                    message.sender_id,
                    ActorMessage(
                        message_type="execution_context_updated",
                        content={"context_id": context_id, "success": True},
                        sender_id=self.agent_id,
                    ),
                )
            else:
                await self._send_error(
                    message.sender_id,
                    f"Context {context_id} not found",
                    message.message_type,
                )

        except Exception as e:
            logger.error("update_context_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to update context: {e!s}",
                message.message_type,
            )

    async def _handle_checkpoint_context(self, message: ActorMessage) -> None:
        """
        Create a checkpoint for context recovery.

        Content: {"context_id": str}

        Returns: Checkpoint data for persistence
        """
        try:
            content = await self._validate_message(message)
            context_id = content.get("context_id")

            if not context_id or not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Invalid context_id",
                    message.message_type,
                )
                return

            checkpoint = self._time_manager.checkpoint_context(context_id)

            if checkpoint:
                await self.send(
                    message.sender_id,
                    ActorMessage(
                        message_type="context_checkpoint",
                        content={"checkpoint": checkpoint},
                        sender_id=self.agent_id,
                    ),
                )
            else:
                await self._send_error(
                    message.sender_id,
                    f"Context {context_id} not found",
                    message.message_type,
                )

        except Exception as e:
            logger.error("checkpoint_context_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to checkpoint context: {e!s}",
                message.message_type,
            )

    async def _handle_get_context_status(self, message: ActorMessage) -> None:
        """
        Get status of an execution context.

        Content: {"context_id": str}

        Returns: {
            "context": ExecutionContext.to_dict(),
            "wallclock_elapsed": str,
            "subjective_elapsed": str,
            "time_remaining": str | None,
            "is_at_risk": bool,
        }
        """
        try:
            content = await self._validate_message(message)
            context_id = content.get("context_id")

            if not context_id or not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Invalid context_id",
                    message.message_type,
                )
                return

            context = self._time_manager.get_context(context_id)

            if context:
                await self.send(
                    message.sender_id,
                    ActorMessage(
                        message_type="context_status",
                        content={
                            "context": context.to_dict(),
                            "wallclock_elapsed": str(context.wallclock_elapsed),
                            "subjective_elapsed": str(context.subjective_elapsed),
                            "time_remaining": (
                                str(context.time_remaining) if context.time_remaining else None
                            ),
                            "is_at_risk": context.is_at_risk,
                        },
                        sender_id=self.agent_id,
                    ),
                )
            else:
                await self._send_error(
                    message.sender_id,
                    f"Context {context_id} not found",
                    message.message_type,
                )

        except Exception as e:
            logger.error("get_context_status_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get context status: {e!s}",
                message.message_type,
            )

    async def _handle_get_metrics(self, message: ActorMessage) -> None:
        """
        Get time perception metrics.

        Returns: TimePerceptionMetrics.to_dict()
        """
        try:
            if not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Time perception not enabled",
                    message.message_type,
                )
                return

            metrics = self._time_manager.get_perception_metrics()

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="time_perception_metrics",
                    content=metrics.to_dict(),
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_metrics_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get metrics: {e!s}",
                message.message_type,
            )

    async def _handle_anchor_time(self, message: ActorMessage) -> None:
        """
        Anchor time perception to external source.

        Content: {"source": str}  # system_clock, ntp_server, coordinator

        Returns: Anchoring result
        """
        try:
            content = await self._validate_message(message)
            source_str = content.get("source", "system_clock")

            try:
                source = AnchorSource(source_str)
            except ValueError:
                source = AnchorSource.SYSTEM_CLOCK

            if not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Time perception not enabled",
                    message.message_type,
                )
                return

            result = await self._time_manager.anchor_time(source)

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="time_anchored",
                    content=result,
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("anchor_time_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to anchor time: {e!s}",
                message.message_type,
            )

    async def _handle_get_adaptive_timeout(self, message: ActorMessage) -> None:
        """
        Get adaptive timeout for an operation.

        Content: {
            "operation": str,
            "retry_count": int,
            "context_id": str | None,
        }

        Returns: {
            "timeout_seconds": float,
            "timeout_recommended": str,
        }
        """
        try:
            content = await self._validate_message(message)
            operation = content.get("operation", "default")
            retry_count = content.get("retry_count", 0)
            context_id = content.get("context_id")

            if not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Time perception not enabled",
                    message.message_type,
                )
                return

            timeout = self._time_manager.calculate_adaptive_timeout(
                operation=operation,
                retry_count=retry_count,
                context_id=context_id,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="adaptive_timeout",
                    content={
                        "timeout_seconds": timeout.total_seconds(),
                        "timeout_recommended": str(timeout),
                        "operation": operation,
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_adaptive_timeout_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get adaptive timeout: {e!s}",
                message.message_type,
            )

    async def _handle_delegate(self, message: ActorMessage) -> None:
        """
        Delegate context to Coordinator when overloaded.

        Content: {
            "context_id": str,
            "reason": str,
            "fallback_action": str | None,
        }
        """
        try:
            content = await self._validate_message(message)
            context_id = content.get("context_id")
            reason = content.get("reason", "Chronos overloaded")
            fallback_action = content.get("fallback_action", "reschedule")

            if not self._time_manager:
                await self._send_error(
                    message.sender_id,
                    "Time perception not enabled",
                    message.message_type,
                )
                return

            result = await self._time_manager.delegate_to_coordinator(
                context_id=context_id,
                reason=reason,
                fallback_action=fallback_action,
            )

            if result.get("delegated") and context_id in self._execution_contexts:
                del self._execution_contexts[context_id]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="delegation_result",
                    content=result,
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("delegate_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to delegate: {e!s}",
                message.message_type,
            )

    # INTG-04: Helper Methods

    async def _check_context_deadlines(self) -> None:
        """Check execution context deadlines and send warnings."""
        if not self._time_manager:
            return

        for context in self._execution_contexts.values():
            if context.status != "running":
                continue

            if context.is_at_risk:
                await self._send_context_warning(context)

            if context.time_remaining and context.time_remaining.total_seconds() <= 0:
                await self._handle_context_deadline_miss(context)

    def _update_overload_state(self) -> None:
        """Update overload detection based on current load."""
        if not self._time_manager:
            return

        active_count = sum(1 for c in self._execution_contexts.values() if c.status == "running")
        load = active_count / self._max_contexts if self._max_contexts > 0 else 0

        self._time_manager.update_load(load)

    def _should_delegate(self) -> bool:
        """Check if delegation is needed."""
        if not self._time_manager:
            return False

        should_del, _ = self._time_manager.should_delegate()
        return bool(should_del)

    async def _handle_overload_delegation(self) -> None:
        """Delegate low-priority contexts to Coordinator."""
        if not self._time_manager:
            return

        delegatable = [
            c
            for c in self._execution_contexts.values()
            if c.status == "running" and c.metadata.get("priority", 2) <= 2
        ]

        if delegatable:
            context = delegatable[0]
            await self._time_manager.delegate_to_coordinator(
                context.context_id,
                "Chronos overloaded",
            )
            if context.context_id in self._execution_contexts:
                del self._execution_contexts[context.context_id]

    async def _send_context_warning(self, context: ExecutionContext) -> None:
        """Send warning about at-risk context."""
        await self.send(
            context.agent_id,
            ActorMessage(
                message_type="context_at_risk",
                content={
                    "context_id": context.context_id,
                    "task_id": context.task_id,
                    "time_remaining": str(context.time_remaining),
                    "progress_percent": context.progress_percent,
                    "deadline": (context.deadline.isoformat() if context.deadline else None),
                },
                sender_id=self.agent_id,
            ),
        )

    async def _handle_context_deadline_miss(self, context: ExecutionContext) -> None:
        """Handle a missed deadline for an execution context."""
        if self._time_manager:
            self._time_manager.fail_context(context.context_id, "Deadline missed")

        await self.send(
            context.agent_id,
            ActorMessage(
                message_type="context_deadline_missed",
                content={
                    "context_id": context.context_id,
                    "task_id": context.task_id,
                    "missed_at": datetime.now(UTC).isoformat(),
                },
                sender_id=self.agent_id,
            ),
        )

    def get_capabilities(self) -> list[str]:
        """Return list of capabilities this agent provides."""
        capabilities = [
            "task_scheduling",
            "deadline_management",
            "temporal_coordination",
            "calendar_management",
            "timeline_tracking",
            "reminder_service",
        ]

        # INTG-04: Add time perception capabilities
        if self._enable_time_dilation:
            capabilities.extend(
                [
                    "execution_context_tracking",
                    "time_perception_management",
                    "adaptive_timeout",
                    "reality_anchoring",
                    "overload_detection",
                    "context_delegation",
                ]
            )

        return capabilities
