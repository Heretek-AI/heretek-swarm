"""
Coordinator Agent - Multi-Agent Coordination Specialist

Tier 5 Coordination Agent responsible for:
- Task synchronization across multiple agents
- Dependency resolution and sequencing
- Parallel execution orchestration
- Resource contention management
- Collective task progress tracking

Author: Heretek Swarm Collective
Date: 2026-04-06
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

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

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    """Status of a coordinated task."""
    PENDING = "pending"
    READY = "ready"  # Dependencies satisfied
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"  # Waiting on external dependency
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DependencyType(Enum):
    """Type of task dependency."""
    SEQUENTIAL = "sequential"  # Must complete before next starts
    PARALLEL = "parallel"  # Can run concurrently
    CONDITIONAL = "conditional"  # Depends on condition being met
    RESOURCE = "resource"  # Competes for shared resource


@dataclass
class CoordinatedTask:
    """A task under coordination."""
    task_id: str
    name: str
    description: str
    assigned_agents: list[str]
    dependencies: list[str] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.SEQUENTIAL
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5  # 1-10 scale
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0  # 0.0 to 1.0
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "assigned_agents": self.assigned_agents,
            "dependencies": self.dependencies,
            "dependency_type": self.dependency_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
            "progress": self.progress,
            "error_message": self.error_message,
        }


@dataclass
class AgentState:
    """Current state of an agent in the coordination system."""
    agent_id: str
    status: str = "idle"  # idle, busy, offline
    current_task: str | None = None
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    load: float = 0.0  # 0.0 to 1.0
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "load": self.load,
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }


class CoordinatorAgent(AgentActor):
    """
    Multi-Agent Coordination Specialist.

    Responsibilities:
    - Manage task dependencies and execution order
    - Synchronize parallel agent activities
    - Resolve resource contention
    - Track collective progress
    - Optimize task assignment based on agent load

    Message Handlers:
    - create_task: Create a new coordinated task
    - update_task: Update task status or metadata
    - get_task_status: Get status of a specific task
    - get_workflow_status: Get status of all tasks in a workflow
    - assign_agent: Assign an agent to the coordination system
    - update_agent_state: Update an agent's state
    - resolve_dependencies: Resolve task dependencies
    - start_workflow: Start execution of a coordinated workflow
    - cancel_workflow: Cancel a running workflow
    - get_coordination_report: Generate coordination status report
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
            agent_id=agent_id or f"coordinator_{uuid.uuid4().hex[:8]}",
            config=config or {},
        )

        # Task tracking
        self._tasks: dict[str, CoordinatedTask] = {}
        self._task_queues: dict[str, list[str]] = {}  # workflow_id -> task_ids
        self._max_tasks: int = self._config.get("max_tasks", 1000)

        # Agent tracking
        self._agents: dict[str, AgentState] = {}
        self._max_agents: int = self._config.get("max_agents", 100)

        # Dependency resolution
        self._dependency_graph: dict[str, set[str]] = {}  # task_id -> dependent task_ids
        self._reverse_deps: dict[str, set[str]] = {}  # task_id -> dependency task_ids

        # Resource pools
        self._resources: dict[str, int] = {}  # resource_name -> available count
        self._resource_locks: dict[str, set[str]] = {}  # resource_name -> locked by task_ids


        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)

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


        logger.info(
            "coordinator_initialized",
            agent_id=self.agent_id,
            max_tasks=self._max_tasks,
            max_agents=self._max_agents,
        )

    async def _validate_message(self, message: ActorMessage) -> dict[str, Any]:
        """Validate incoming message content."""
        try:
            validated = validate_message(message.message_type, message.content)
            if hasattr(validated, "dict"):
                return validated.dict()
            return validated
        except Exception:
            # Fallback: return content as-is for unknown message types
            return message.content

    async def _handle_create_task(self, message: ActorMessage) -> None:
        """
        Create a new coordinated task.

        Content:
        - task_id: Optional[str] - If not provided, generated
        - name: str - Task name
        - description: str - Task description
        - assigned_agents: List[str] - Agents assigned to this task
        - dependencies: Optional[List[str]] - Task IDs this depends on
        - dependency_type: Optional[str] - sequential|parallel|conditional|resource
        - priority: Optional[int] - 1-10 scale, default 5
        - metadata: Optional[Dict] - Additional metadata
        """
        try:
            content = await self._validate_message(message)
            # Create TaskRequest from content - inline construction
            request_data = {
                "task_id": content.get("task_id"),
                "name": content.get("name", "unnamed"),
                "description": content.get("description", ""),
                "assigned_agents": content.get("assigned_agents", []),
            }
            request = CoordinatedTask(**request_data)

            # Check task limit
            if len(self._tasks) >= self._max_tasks:
                await self._send_error(
                    message.sender_id,
                    "Task limit reached",
                    message.message_type,
                )
                return

            task_id = request.task_id or f"task_{uuid.uuid4().hex[:12]}"

            # Check for duplicate
            if task_id in self._tasks:
                await self._send_error(
                    message.sender_id,
                    f"Task {task_id} already exists",
                    message.message_type,
                )
                return

            # Create task
            dep_type = DependencyType(request.dependency_type or "sequential")
            task = CoordinatedTask(
                task_id=task_id,
                name=request.name,
                description=request.description,
                assigned_agents=request.assigned_agents or [],
                dependencies=request.dependencies or [],
                dependency_type=dep_type,
                priority=request.priority or 5,
                metadata=request.metadata or {},
            )

            # Validate dependencies exist
            for dep_id in task.dependencies:
                if dep_id not in self._tasks:
                    await self._send_error(
                        message.sender_id,
                        f"Dependency {dep_id} does not exist",
                        message.message_type,
                    )
                    return

            self._tasks[task_id] = task

            # Update dependency graph
            self._dependency_graph[task_id] = set()
            self._reverse_deps[task_id] = set(task.dependencies)
            for dep_id in task.dependencies:
                if dep_id in self._dependency_graph:
                    self._dependency_graph[dep_id].add(task_id)

            # Determine initial status
            if task.dependencies:
                task.status = TaskStatus.BLOCKED
            else:
                task.status = TaskStatus.READY

            logger.info(
                "task_created",
                task_id=task_id,
                name=request.name,
                dependencies=len(task.dependencies),
                status=task.status.value,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_created",
                    content={"task_id": task_id, "status": task.status.value},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("create_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to create task: {e!s}",
                message.message_type,
            )

    async def _handle_update_task(self, message: ActorMessage) -> None:
        """
        Update task status or metadata.

        Content:
        - task_id: str - Task to update
        - status: Optional[str] - New status
        - progress: Optional[float] - Progress 0.0-1.0
        - metadata: Optional[Dict] - Metadata updates
        - error_message: Optional[str] - Error if failed
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
            updates = []

            # Update status
            if "status" in content:
                old_status = task.status
                task.status = TaskStatus(content["status"])
                updates.append(f"status: {old_status.value} -> {task.status.value}")

                # Track timestamps
                if task.status == TaskStatus.IN_PROGRESS and not task.started_at:
                    task.started_at = datetime.now(UTC)
                elif task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    task.completed_at = datetime.now(UTC)

                    # Unblock dependent tasks
                    if task.status == TaskStatus.COMPLETED:
                        await self._unblock_dependents(task_id)

            # Update progress
            if "progress" in content:
                progress = float(content["progress"])
                if 0.0 <= progress <= 1.0:
                    task.progress = progress
                    updates.append(f"progress: {task.progress}")

            # Update metadata
            if "metadata" in content:
                task.metadata.update(content["metadata"])
                updates.append("metadata updated")

            # Update error message
            if "error_message" in content:
                task.error_message = content["error_message"]
                updates.append("error_message set")

            logger.info(
                "task_updated",
                task_id=task_id,
                updates=updates,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_updated",
                    content={"task_id": task_id, "updates": updates},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("update_task_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to update task: {e!s}",
                message.message_type,
            )

    async def _handle_get_task_status(self, message: ActorMessage) -> None:
        """
        Get status of a specific task.

        Content:
        - task_id: str - Task to query
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
            dependents = list(self._dependency_graph.get(task_id, []))

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="task_status",
                    content={
                        "task": task.to_dict(),
                        "dependents": dependents,
                        "dependency_count": len(task.dependencies),
                    },
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

    async def _handle_get_workflow_status(self, message: ActorMessage) -> None:
        """
        Get status of all tasks in a workflow.

        Content:
        - workflow_id: str - Workflow to query (optional, returns all if not provided)
        """
        try:
            content = await self._validate_message(message)
            workflow_id = content.get("workflow_id")

            if workflow_id:
                task_ids = self._task_queues.get(workflow_id, [])
                tasks = [self._tasks[tid].to_dict() for tid in task_ids if tid in self._tasks]
            else:
                tasks = [task.to_dict() for task in self._tasks.values()]

            # Calculate summary
            status_counts = {}
            total_progress = 0.0
            for task in tasks:
                status = task["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
                total_progress += task.get("progress", 0.0)

            avg_progress = total_progress / len(tasks) if tasks else 0.0

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="workflow_status",
                    content={
                        "workflow_id": workflow_id or "all",
                        "task_count": len(tasks),
                        "status_counts": status_counts,
                        "average_progress": avg_progress,
                        "tasks": tasks,
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_workflow_status_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get workflow status: {e!s}",
                message.message_type,
            )

    async def _handle_assign_agent(self, message: ActorMessage) -> None:
        """
        Assign an agent to the coordination system.

        Content:
        - agent_id: str - Agent to assign
        - metadata: Optional[Dict] - Additional agent metadata
        """
        try:
            content = await self._validate_message(message)
            agent_id = content.get("agent_id")

            if not agent_id:
                await self._send_error(
                    message.sender_id,
                    "agent_id is required",
                    message.message_type,
                )
                return

            if len(self._agents) >= self._max_agents:
                await self._send_error(
                    message.sender_id,
                    f"Agent limit reached ({self._max_agents})",
                    message.message_type,
                )
                return

            if agent_id in self._agents:
                await self._send_error(
                    message.sender_id,
                    f"Agent {agent_id} already assigned",
                    message.message_type,
                )
                return

            self._agents[agent_id] = AgentState(
                agent_id=agent_id,
                metadata=content.get("metadata", {}),
            )

            logger.info(
                "agent_assigned",
                agent_id=agent_id,
                total_agents=len(self._agents),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="agent_assigned",
                    content={"agent_id": agent_id, "status": "assigned"},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("assign_agent_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to assign agent: {e!s}",
                message.message_type,
            )

    async def _handle_update_agent_state(self, message: ActorMessage) -> None:
        """
        Update an agent's state.

        Content:
        - agent_id: str - Agent to update
        - status: Optional[str] - idle|busy|offline
        - current_task: Optional[str] - Current task ID
        - load: Optional[float] - Load 0.0-1.0
        """
        try:
            content = await self._validate_message(message)
            agent_id = content.get("agent_id")

            if not agent_id or agent_id not in self._agents:
                await self._send_error(
                    message.sender_id,
                    f"Agent {agent_id} not found",
                    message.message_type,
                )
                return

            agent = self._agents[agent_id]
            agent.last_heartbeat = datetime.now(UTC)

            if "status" in content:
                agent.status = content["status"]
            if "current_task" in content:
                agent.current_task = content["current_task"]
            if "load" in content:
                agent.load = float(content["load"])

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="agent_state_updated",
                    content={"agent_id": agent_id, "state": agent.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("update_agent_state_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to update agent state: {e!s}",
                message.message_type,
            )

    async def _handle_resolve_dependencies(self, message: ActorMessage) -> None:
        """
        Resolve task dependencies and return execution order.

        Content:
        - task_ids: Optional[List[str]] - Tasks to analyze (all if not provided)
        """
        try:
            content = await self._validate_message(message)
            task_ids = content.get("task_ids", list(self._tasks.keys()))

            # Build subgraph
            subgraph = {tid: self._reverse_deps.get(tid, set()) for tid in task_ids if tid in self._tasks}

            # Topological sort
            sorted_tasks = self._topological_sort(subgraph)

            # Identify parallel groups
            parallel_groups = self._identify_parallel_groups(sorted_tasks, subgraph)

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="dependency_resolution",
                    content={
                        "execution_order": sorted_tasks,
                        "parallel_groups": parallel_groups,
                        "critical_path": self._find_critical_path(sorted_tasks, subgraph),
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("resolve_dependencies_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to resolve dependencies: {e!s}",
                message.message_type,
            )

    async def _handle_start_workflow(self, message: ActorMessage) -> None:
        """
        Start execution of a coordinated workflow.

        Content:
        - workflow_id: str - Workflow to start
        - task_ids: List[str] - Tasks in the workflow
        """
        try:
            content = await self._validate_message(message)
            workflow_id = content.get("workflow_id")
            task_ids = content.get("task_ids", [])

            if not workflow_id:
                await self._send_error(
                    message.sender_id,
                    "workflow_id is required",
                    message.message_type,
                )
                return

            # Register workflow
            self._task_queues[workflow_id] = task_ids

            # Update task statuses
            ready_tasks = []
            for task_id in task_ids:
                if task_id in self._tasks:
                    task = self._tasks[task_id]
                    if not task.dependencies:
                        task.status = TaskStatus.READY
                        ready_tasks.append(task_id)

            logger.info(
                "workflow_started",
                workflow_id=workflow_id,
                task_count=len(task_ids),
                ready_count=len(ready_tasks),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="workflow_started",
                    content={
                        "workflow_id": workflow_id,
                        "ready_tasks": ready_tasks,
                        "blocked_tasks": len(task_ids) - len(ready_tasks),
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("start_workflow_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to start workflow: {e!s}",
                message.message_type,
            )

    async def _handle_cancel_workflow(self, message: ActorMessage) -> None:
        """
        Cancel a running workflow.

        Content:
        - workflow_id: str - Workflow to cancel
        """
        try:
            content = await self._validate_message(message)
            workflow_id = content.get("workflow_id")

            if not workflow_id or workflow_id not in self._task_queues:
                await self._send_error(
                    message.sender_id,
                    f"Workflow {workflow_id} not found",
                    message.message_type,
                )
                return

            task_ids = self._task_queues[workflow_id]
            cancelled = []

            for task_id in task_ids:
                if task_id in self._tasks:
                    task = self._tasks[task_id]
                    if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                        task.status = TaskStatus.CANCELLED
                        task.completed_at = datetime.now(UTC)
                        cancelled.append(task_id)

            # Remove workflow
            del self._task_queues[workflow_id]

            logger.info(
                "workflow_cancelled",
                workflow_id=workflow_id,
                cancelled_count=len(cancelled),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="workflow_cancelled",
                    content={
                        "workflow_id": workflow_id,
                        "cancelled_tasks": cancelled,
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("cancel_workflow_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to cancel workflow: {e!s}",
                message.message_type,
            )

    async def _handle_get_coordination_report(self, message: ActorMessage) -> None:
        """
        Generate coordination status report.

        Content: (none required)
        """
        try:
            # Task statistics
            task_stats = {
                "total": len(self._tasks),
                "by_status": {},
                "by_priority": {},
            }

            for task in self._tasks.values():
                status = task.status.value
                task_stats["by_status"][status] = task_stats["by_status"].get(status, 0) + 1

                priority = task.priority
                task_stats["by_priority"][priority] = task_stats["by_priority"].get(priority, 0) + 1

            # Agent statistics
            agent_stats = {
                "total": len(self._agents),
                "idle": sum(1 for a in self._agents.values() if a.status == "idle"),
                "busy": sum(1 for a in self._agents.values() if a.status == "busy"),
                "offline": sum(1 for a in self._agents.values() if a.status == "offline"),
            }

            # Workflow statistics
            workflow_stats = {
                "total": len(self._task_queues),
                "workflows": {
                    wid: len(tids) for wid, tids in self._task_queues.items()
                },
            }

            report = {
                "timestamp": datetime.now(UTC).isoformat(),
                "task_statistics": task_stats,
                "agent_statistics": agent_stats,
                "workflow_statistics": workflow_stats,
                "resource_pools": self._resources,
            }

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="coordination_report",
                    content=report,
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_coordination_report_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to generate report: {e!s}",
                message.message_type,
            )

    async def _unblock_dependents(self, completed_task_id: str) -> None:
        """Unblock tasks that were waiting on the completed task."""
        dependents = self._dependency_graph.get(completed_task_id, set())

        for dep_id in dependents:
            if dep_id in self._tasks:
                task = self._tasks[dep_id]
                if task.status == TaskStatus.BLOCKED:
                    # Check if all dependencies are satisfied
                    remaining_deps = [
                        d for d in task.dependencies
                        if d in self._tasks and self._tasks[d].status != TaskStatus.COMPLETED
                    ]

                    if not remaining_deps:
                        task.status = TaskStatus.READY
                        logger.info(
                            "task_unblocked",
                            task_id=dep_id,
                        )

    def _topological_sort(self, graph: dict[str, set[str]]) -> list[str]:
        """Perform topological sort on dependency graph."""
        in_degree = {node: len(deps) for node, deps in graph.items()}
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort by priority for deterministic ordering
            queue.sort(key=lambda x: -self._tasks.get(x, CoordinatedTask(x, "", "", [])).priority)
            node = queue.pop(0)
            result.append(node)

            for dependent in self._dependency_graph.get(node, set()):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return result

    def _identify_parallel_groups(self, sorted_tasks: list[str], graph: dict[str, set[str]]) -> list[list[str]]:
        """Identify groups of tasks that can run in parallel."""
        if not sorted_tasks:
            return []

        groups = []
        current_group = []
        completed = set()

        for task_id in sorted_tasks:
            deps = graph.get(task_id, set())

            # If all dependencies are in completed, can add to current group
            if all(d in completed for d in deps):
                current_group.append(task_id)
            else:
                if current_group:
                    groups.append(current_group)
                    completed.update(current_group)
                current_group = [task_id]

        if current_group:
            groups.append(current_group)

        return groups

    def _find_critical_path(self, sorted_tasks: list[str], graph: dict[str, set[str]]) -> list[str]:
        """Find the critical path (longest dependency chain)."""
        if not sorted_tasks:
            return []

        # Calculate longest path to each node
        longest_path: dict[str, list[str]] = {task: [task] for task in sorted_tasks}

        for task_id in sorted_tasks:
            deps = graph.get(task_id, set())
            for dep in deps:
                if dep in longest_path:
                    candidate_path = longest_path[dep] + [task_id]
                    if len(candidate_path) > len(longest_path[task_id]):
                        longest_path[task_id] = candidate_path

        # Find the longest path overall
        if longest_path:
            return max(longest_path.values(), key=len)
        return []


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return

        if item_id in self._pattern_emitted:
            return

        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"{item_type}_{item_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type=f"{item_type}_completion",
                content=content,
                timestamp=datetime.now(UTC).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: list[PatternType] | None = None) -> list[dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []

        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: list[str],
        domain: str = "general",
    ) -> str | None:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None

        try:
            deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=proposal[:200],
                participants=participating_agents,
                domain=domain,
            )
            self._active_deliberations[item_id] = deliberation_id

            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False

        try:
            success = self.deliberation_engine.submit_position(
                deliberation_id=deliberation_id,
                agent_id=agent_id,
                position=position,
                confidence=confidence,
                argument=argument,
            )

            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=f"delib_{deliberation_id}_{agent_id}",
                    access_type="write",
                    agent_id=agent_id,
                )

            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Any | None:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None

        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)

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

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str = "read") -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return

        memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD

        memory_id = f"{item_type}_{item_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> list[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []

        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> dict[str, Any]:
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

    def get_capabilities(self) -> list[str]:
        """Return list of capabilities this agent provides."""
        return [
            "task_coordination",
            "dependency_resolution",
            "workflow_management",
            "agent_synchronization",
            "resource_contention_management",
            "parallel_execution",
            "progress_tracking",
        ]
