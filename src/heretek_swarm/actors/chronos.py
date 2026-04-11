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


import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.validation import validate_message

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import Position, SwarmDeliberationEngine

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

_logger = structlog.get_logger(__name__)


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
    recurrence: Optional[RecurrenceType] = None
    recurrence_config: Dict[str, Any] = field(default_factory=dict)
    target_agents: List[str] = field(default_factory=list)
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
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
    assigned_to: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, met, missed
    warning_thresholds: List[timedelta] = field(default_factory=list)
    warnings_sent: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
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
            "time_remaining": str(self.due_at - datetime.now(timezone.utc)),
        }


class ChronosAgent(AgentActor):
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

    def __init__(self, _agent_id: Optional[str], _config: Optional[Dict[str, Any]], # Session 44: Integration components
        pattern_extractor: Optional[PatternExtractor], _deliberation_engine: Optional[SwarmDeliberationEngine], _access_analyzer: Optional[AccessPatternAnalyzer], _zero_trust_validator: Optional[ZeroTrustValidator]):
        super().__init__(
            agent_id=agent_id or f"chronos_{uuid.uuid4().hex[:8]}",
            _config = config or {},
        )

        # Task scheduling
        self._tasks: Dict[str, ScheduledTask] = {}
        self._task_queue: List[Tuple[datetime, str]] = []  # (scheduled_at, task_id)
        self._max_tasks: int = self._config.get("max_tasks", 1000)

        # Deadlines
        self._deadlines: Dict[str, Deadline] = {}
        self._max_deadlines: int = self._config.get("max_deadlines", 500)

        # Scheduler control
        self._scheduler_running: bool = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._check_interval: float = self._config.get("check_interval", 1.0)  # seconds

        # Calendars
        self._calendars: Dict[str, List[str]] = {}  # calendar_id -> task_ids


        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            _max_rounds = 5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(
            "chronos_initialized",
            agent_id=self.agent_id,
            _max_tasks = self._max_tasks,
            _check_interval = self._check_interval,
        )

    async def initialize(self) -> None:
        """Initialize the Chronos agent."""
        await super().initialize()
        self._scheduler_running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("chronos_scheduler_started")

    async def terminate(self) -> None:
        """Terminate the Chronos agent."""
        self._scheduler_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
            logger.info("chronos_scheduler_stopped")
        await super().terminate()

    async def _validate_message(self, _message: ActorMessage) -> Dict[str, Any]:
        """Validate incoming message content."""
        try:
            _validated = validate_message(message.message_type, message.content)
            if hasattr(validated, 'dict'):
                return validated.dict()
            return validated
        except Exception:
            return message.content

    async def _run_scheduler(self) -> None:
        """Main scheduler loop - checks and executes due tasks."""
        while self._scheduler_running:
            try:
                now = datetime.now(timezone.utc)

                # Check for due tasks
                _due_tasks = []
                _remaining_queue = []

                for scheduled_at, task_id in self._task_queue:
                    if task_id in self._tasks:
                        _task = self._tasks[task_id]
                        if task.status == ScheduleStatus.PENDING and scheduled_at <= now:
                            due_tasks.append(task)
                        else:
                            remaining_queue.append((scheduled_at, task_id))
                    # Remove tasks that no longer exist

                self._task_queue = remaining_queue

                # Execute due tasks
                for task in due_tasks:
                    await self._execute_task(task)

                # Check deadlines
                await self._check_deadlines()

                # Sort queue by time
                self._task_queue.sort(key=lambda x: x[0])

            except Exception as e:
                logger.error("scheduler_error", error=str(e))

            await asyncio.sleep(self._check_interval)

    async def _execute_task(self, _task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        try:
            task.status = ScheduleStatus.ACTIVE
            task.run_count += 1

            logger.info(
                "executing_scheduled_task",
                _task_id = task.task_id,
                name=task.name,
                run_count=task.run_count,
            )

            # Notify target agents
            for agent_id in task.target_agents:
                await self.send(
                    agent_id,
                    ActorMessage(
                        message_type=task.action or "scheduled_task",
                        _content = {
                            "task_id": task.task_id,
                            "name": task.name,
                            "payload": task.payload,
                            "scheduled_at": task.scheduled_at.isoformat(),
                        },
                        _sender_id = self.agent_id,
                    ),
                )

            task.status = ScheduleStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)

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

    async def _schedule_next_run(self, _task: ScheduledTask) -> None:
        """Schedule the next run for a recurring task."""
        if not task.recurrence:
            return

        # Check max runs
        if task.max_runs and task.run_count >= task.max_runs:
            task.status = ScheduleStatus.COMPLETED
            return

        # Calculate next run time
        now = datetime.now(timezone.utc)

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
            _interval_seconds = task.recurrence_config.get("interval_seconds", 3600)
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
                _task_id = task.task_id,
                _next_run = task.next_run.isoformat(),
            )

    async def _check_deadlines(self) -> None:
        """Check deadlines and send warnings."""
        now = datetime.now(timezone.utc)

        for deadline in self._deadlines.values():
            if deadline.status != "pending":
                continue

            _time_remaining = deadline.due_at - now

            if time_remaining.total_seconds() <= 0:
                deadline.status = "missed"
                logger.warning("deadline_missed", deadline_id=deadline.deadline_id)
                continue

            # Check warning thresholds
            for threshold in deadline.warning_thresholds:
                _threshold_key = str(threshold)
                if threshold_key not in deadline.warnings_sent:
                    if time_remaining <= threshold:
                        deadline.warnings_sent.add(threshold_key)
                        await self._send_deadline_warning(deadline, threshold)

    async def _send_deadline_warning(self, _deadline: Deadline, _threshold: timedelta) -> None:
        """Send deadline warning notification."""
        for agent_id in deadline.assigned_to:
            await self.send(
                agent_id,
                ActorMessage(
                    message_type="deadline_warning",
                    _content = {
                        "deadline_id": deadline.deadline_id,
                        "name": deadline.name,
                        "due_at": deadline.due_at.isoformat(),
                        "threshold": str(threshold),
                        "time_remaining": str(deadline.due_at - datetime.now(timezone.utc)),
                    },
                    _sender_id = self.agent_id,
                ),
            )

    async def _handle_schedule_task(self, _message: ActorMessage) -> None:
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
            _content = await self._validate_message(message)

            if len(self._tasks) >= self._max_tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task limit reached ({self._max_tasks})",
                    message.message_type,
                )
                return

            _task_id = content.get("task_id") or f"task_{uuid.uuid4().hex[:12]}"

            if task_id in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} already exists",
                    message.message_type,
                )
                return

            _scheduled_at_str = content.get("scheduled_at")
            scheduled_at = datetime.fromisoformat(scheduled_at_str) if scheduled_at_str else datetime.now(timezone.utc)

            _recurrence_str = content.get("recurrence")
            _recurrence = RecurrenceType(recurrence_str) if recurrence_str else RecurrenceType.ONCE

            _priority_value = content.get("priority", 2)
            _priority = Priority(min(max(priority_value, 1), 5))

            _task = ScheduledTask(
                _task_id = task_id,
                name=content.get("name", "Untitled Task"),
                _description = content.get("description", ""),
                scheduled_at=scheduled_at,
                _priority = priority,
                _recurrence = recurrence,
                _recurrence_config = content.get("recurrence_config", {}),
                _target_agents = content.get("target_agents", []),
                _action = content.get("action", "scheduled_task"),
                _payload = content.get("payload", {}),
                _deadline = datetime.fromisoformat(content["deadline"]) if content.get("deadline") else None,
                _max_runs = content.get("max_runs"),
                metadata=content.get("metadata", {}),
            )

            self._tasks[task_id] = task
            self._task_queue.append((scheduled_at, task_id))

            logger.info(
                "task_scheduled",
                _task_id = task_id,
                name=task.name,
                scheduled_at=scheduled_at.isoformat(),
                _recurrence = recurrence.value,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_scheduled",
                    _content = {"task": task.to_dict()},
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("schedule_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to schedule task: {str(e)}",
                message.message_type,
            )

    async def _handle_cancel_task(self, _message: ActorMessage) -> None:
        """
        Cancel a scheduled task.

        Content:
        - task_id: str
        """
        try:
            _content = await self._validate_message(message)
            _task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            _task = self._tasks[task_id]

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
                    _content = {"task_id": task_id},
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("cancel_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to cancel task: {str(e)}",
                message.message_type,
            )

    async def _handle_pause_task(self, _message: ActorMessage) -> None:
        """
        Pause a scheduled task.

        Content:
        - task_id: str
        """
        try:
            _content = await self._validate_message(message)
            _task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            _task = self._tasks[task_id]

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
                    _content = {"task_id": task_id},
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("pause_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to pause task: {str(e)}",
                message.message_type,
            )

    async def _handle_resume_task(self, _message: ActorMessage) -> None:
        """
        Resume a paused task.

        Content:
        - task_id: str
        """
        try:
            _content = await self._validate_message(message)
            _task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            _task = self._tasks[task_id]

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
                    _content = {"task_id": task_id},
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("resume_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to resume task: {str(e)}",
                message.message_type,
            )

    async def _handle_get_task_status(self, _message: ActorMessage) -> None:
        """
        Get status of a scheduled task.

        Content:
        - task_id: str
        """
        try:
            _content = await self._validate_message(message)
            _task_id = content.get("task_id")

            if not task_id or task_id not in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} not found",
                    message.message_type,
                )
                return

            _task = self._tasks[task_id]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_status",
                    _content = {"task": task.to_dict()},
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_task_status_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get task status: {str(e)}",
                message.message_type,
            )

    async def _handle_set_deadline(self, _message: ActorMessage) -> None:
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
            _content = await self._validate_message(message)

            if len(self._deadlines) >= self._max_deadlines:
                await self._send_error(
                    message.sender_id,
                    f"Deadline limit reached ({self._max_deadlines})",
                    message.message_type,
                )
                return

            _deadline_id = content.get("deadline_id") or f"deadline_{uuid.uuid4().hex[:12]}"

            if deadline_id in self._deadlines:
                await self._send_error(
                    message.sender_id,
                    f"Deadline {deadline_id} already exists",
                    message.message_type,
                )
                return

            due_at = datetime.fromisoformat(content.get("due_at", datetime.now(timezone.utc).isoformat()))

            # Parse warning thresholds
            _thresholds = []
            for threshold_str in content.get("warning_thresholds", ["1 hour"]):
                # Simple parsing - would need more robust implementation for production
                if "day" in threshold_str:
                    _days = int(threshold_str.split()[0])
                    thresholds.append(timedelta(days=days))
                elif "hour" in threshold_str:
                    _hours = int(threshold_str.split()[0])
                    thresholds.append(timedelta(hours=hours))
                elif "minute" in threshold_str:
                    _minutes = int(threshold_str.split()[0])
                    thresholds.append(timedelta(minutes=minutes))

            _deadline = Deadline(
                _deadline_id = deadline_id,
                name=content.get("name", "Untitled Deadline"),
                due_at=due_at,
                _assigned_to = content.get("assigned_to", []),
                _warning_thresholds = thresholds,
                metadata=content.get("metadata", {}),
            )

            self._deadlines[deadline_id] = deadline

            logger.info(
                "deadline_set",
                _deadline_id = deadline_id,
                _name = deadline.name,
                due_at=due_at.isoformat(),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="deadline_set",
                    _content = {"deadline": deadline.to_dict()},
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("set_deadline_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to set deadline: {str(e)}",
                message.message_type,
            )

    async def _handle_check_deadline(self, _message: ActorMessage) -> None:
        """
        Check deadline status.

        Content:
        - deadline_id: str
        """
        try:
            _content = await self._validate_message(message)
            _deadline_id = content.get("deadline_id")

            if not deadline_id or deadline_id not in self._deadlines:
                await self._send_error(
                    message.sender_id,
                    f"Deadline {deadline_id} not found",
                    message.message_type,
                )
                return

            _deadline = self._deadlines[deadline_id]
            now = datetime.now(timezone.utc)
            _time_remaining = deadline.due_at - now

            # Update status
            if time_remaining.total_seconds() <= 0:
                deadline.status = "missed"
            else:
                deadline.status = "pending"

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="deadline_status",
                    _content = {
                        "deadline": deadline.to_dict(),
                        "time_remaining_seconds": time_remaining.total_seconds(),
                    },
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("check_deadline_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to check deadline: {str(e)}",
                message.message_type,
            )

    async def _handle_get_timeline(self, _message: ActorMessage) -> None:
        """
        Get timeline of scheduled items.

        Content:
        - limit: Optional[int]
        - status: Optional[str]
        """
        try:
            _content = await self._validate_message(message)
            _limit = min(content.get("limit", 50), 100)
            _status_filter = content.get("status")

            _tasks = list(self._tasks.values())

            # Filter by status
            if status_filter:
                try:
                    status = ScheduleStatus(status_filter)
                    _tasks = [t for t in tasks if t.status == status]
                except ValueError:
                    pass

            # Sort by scheduled_at
            tasks.sort(key=lambda t: t.scheduled_at)

            # Limit results
            _tasks = tasks[:limit]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="timeline",
                    _content = {
                        "tasks": [t.to_dict() for t in tasks],
                        "count": len(tasks),
                        "total": len(self._tasks),
                    },
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_timeline_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get timeline: {str(e)}",
                message.message_type,
            )

    async def _handle_get_schedule(self, _message: ActorMessage) -> None:
        """
        Get schedule for a time range.

        Content:
        - start: str (ISO8601)
        - end: str (ISO8601)
        """
        try:
            _content = await self._validate_message(message)
            _start_str = content.get("start")
            _end_str = content.get("end")

            start = datetime.fromisoformat(start_str) if start_str else datetime.now(timezone.utc)
            _end = datetime.fromisoformat(end_str) if end_str else start + timedelta(days=1)

            # Find tasks in range
            scheduled = [
                t.to_dict() for t in self._tasks.values()
                if start <= t.scheduled_at <= end
            ]

            scheduled.sort(key=lambda t: t["scheduled_at"])

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="schedule",
                    _content = {
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "tasks": scheduled,
                        "count": len(scheduled),
                    },
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_schedule_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get schedule: {str(e)}",
                message.message_type,
            )

    async def _handle_register_reminder(self, _message: ActorMessage) -> None:
        """
        Register a time-based reminder.

        Content:
        - reminder_id: Optional[str]
        - message: str
        - remind_at: str (ISO8601)
        - target_agents: Optional[List[str]]
        """
        try:
            _content = await self._validate_message(message)

            _reminder_id = content.get("reminder_id") or f"reminder_{uuid.uuid4().hex[:12]}"
            _remind_at_str = content.get("remind_at")
            _remind_at = datetime.fromisoformat(remind_at_str) if remind_at_str else datetime.now(timezone.utc)
            _target_agents = content.get("target_agents", [message.sender_id])

            # Create as a scheduled task
            _task = ScheduledTask(
                _task_id = reminder_id,
                _name = "Reminder",
                _description = content.get("message", ""),
                _scheduled_at = remind_at,
                _target_agents = target_agents,
                _action = "reminder",
                _payload = {"message": content.get("message", "")},
            )

            self._tasks[reminder_id] = task
            self._task_queue.append((remind_at, reminder_id))

            logger.info(
                "reminder_registered",
                _reminder_id = reminder_id,
                _remind_at = remind_at.isoformat(),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="reminder_registered",
                    _content = {"reminder": task.to_dict()},
                    _sender_id = self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("register_reminder_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to register reminder: {str(e)}",
                message.message_type,
            )


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, _item_id: str, _item_type: str, _outcome: str, _content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return

        if item_id in self._pattern_emitted:
            return

        try:
            await self.pattern_extractor.analyze_message(
                _message_id = f"{item_type}_{item_id}",
                _sender = self.agent_id,
                _recipient = "broadcast",
                _message_type = f"{item_type}_completion",
                _content = content,
                _timestamp = datetime.now(timezone.utc).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, _pattern_types: Optional[List[PatternType]]) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []

        try:
            _patterns = await self.pattern_extractor.extract_patterns(
                _time_window_hours = 24,
                _pattern_types = pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(self, _item_id: str, _proposal: str, _participating_agents: List[str], _domain: str) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None

        try:
            _deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                _deliberation_id = deliberation_id,
                _proposal = proposal[:200],
                _participants = participating_agents,
                _domain = domain,
            )
            self._active_deliberations[item_id] = deliberation_id

            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(self, _item_id: str, _agent_id: str, _position: Position, _confidence: float, _argument: str) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False

        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False

        try:
            _success = self.deliberation_engine.submit_position(
                _deliberation_id = deliberation_id,
                agent_id=agent_id,
                _position = position,
                _confidence = confidence,
                _argument = argument,
            )

            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    _memory_id = f"delib_{deliberation_id}_{agent_id}",
                    _access_type = "write",
                    agent_id=agent_id,
                )

            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, _item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None

        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None

        try:
            _result = self.deliberation_engine.finalize_deliberation(deliberation_id)

            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)

            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, _item_id: str, _item_type: str, _access_type: str) -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return

        _memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            _memory_id = memory_id,
            _access_type = access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, _item_id: str, _item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD

        _memory_id = f"{item_type}_{item_id}"
        _profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, _agent_id: str, _item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []

        try:
            _predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
        }


    async def _send_error(self, _recipient: str, _error_message: str, _original_type: str) -> None:
        """Send error response."""
        await self.send(
            recipient,
            ActorMessage(
                _message_type = "error",
                _content = {"error": error_message, "original_type": original_type},
                _sender_id = self.agent_id,
            ),
        )

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "task_scheduling",
            "deadline_management",
            "temporal_coordination",
            "calendar_management",
            "timeline_tracking",
            "reminder_service",
        ]
