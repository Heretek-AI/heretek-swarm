"""
ActorSupervisor - Supervisor for managing multiple actors.

This module provides:
- Spawn and manage multiple actors
- Monitor actor health
- Restart failed actors
- Coordinate actors
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import structlog

from heretek_swarm.actors.base import AgentActor, ActorState, ActorStatus

logger = structlog.get_logger("ActorSupervisor")


# Global supervisor instance
_global_supervisor: Optional[ActorSupervisor] = None


def get_supervisor() -> "ActorSupervisor":
    """
    Get global supervisor instance.

    Returns:
        ActorSupervisor instance
    """
    global _global_supervisor

    if _global_supervisor is None:
        _global_supervisor = ActorSupervisor()

    return _global_supervisor


class ActorSupervisor:
    """
    Supervisor for managing multiple actors.

    The supervisor provides centralized management for a collection of actors,
    including lifecycle management, health monitoring, and coordination.

    Example:
        ```python
        supervisor = ActorSupervisor()

        # Spawn actors
        await supervisor.spawn_actor(MyActor, "actor-1", topics=["topic1"])
        await supervisor.spawn_actor(MyActor, "actor-2", topics=["topic2"])

        # Monitor health
        await supervisor.start_monitoring()

        # Get status
        status = await supervisor.get_actor_status("actor-1")

        # Terminate all
        await supervisor.terminate_all()
        ```
    """

    def __init__(
        self,
        name: Optional[str] = None,
        health_check_interval: float = 5.0,
        auto_restart: bool = True,
        max_restarts: int = 3,
    ) -> None:
        """
        Initialize the supervisor.

        Args:
            name: Supervisor name
            health_check_interval: Interval between health checks in seconds
            auto_restart: Automatically restart failed actors
            max_restarts: Maximum restart attempts per actor
        """
        self.name = name or "ActorSupervisor"
        self.health_check_interval = health_check_interval
        self.auto_restart = auto_restart
        self.max_restarts = max_restarts

        self.actors: Dict[str, AgentActor] = {}
        self.restart_counts: Dict[str, int] = {}
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info(
            f"[{self.name}] Supervisor initialized",
            extra={
                "health_check_interval": health_check_interval,
                "auto_restart": auto_restart,
                "max_restarts": max_restarts,
            },
        )

    async def spawn_actor(
        self,
        actor_class: Type[AgentActor],
        actor_id: str,
        **kwargs: Any,
    ) -> AgentActor:
        """
        Spawn a new actor.

        Args:
            actor_class: Actor class to instantiate
            actor_id: Unique identifier for the actor
            **kwargs: Additional arguments for actor initialization

        Returns:
            Spawned actor instance

        Raises:
            ValueError: If actor_id already exists
        """
        if actor_id in self.actors:
            raise ValueError(f"Actor {actor_id} already exists")

        # Create actor instance
        actor = actor_class(agent_id=actor_id, **kwargs)

        # Spawn the actor
        await actor.spawn()

        # Register
        self.actors[actor_id] = actor
        self.restart_counts[actor_id] = 0

        logger.info(
            f"[{self.name}] Actor {actor_id} spawned",
            extra={"actor_class": actor_class.__name__},
        )

        return actor

    async def terminate_actor(self, actor_id: str) -> None:
        """
        Terminate an actor.

        Args:
            actor_id: Actor identifier
        """
        if actor_id not in self.actors:
            logger.warning(f"[{self.name}] Actor {actor_id} not found")
            return

        actor = self.actors[actor_id]
        await actor.terminate()

        del self.actors[actor_id]
        if actor_id in self.restart_counts:
            del self.restart_counts[actor_id]

        logger.info(f"[{self.name}] Actor {actor_id} terminated")

    async def terminate_all(self) -> None:
        """Terminate all actors."""
        logger.info(f"[{self.name}] Terminating all actors...")

        actor_ids = list(self.actors.keys())
        tasks = [self.terminate_actor(actor_id) for actor_id in actor_ids]

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"[{self.name}] All actors terminated")

    async def get_actor_status(self, actor_id: str) -> Optional[ActorStatus]:
        """
        Get status of an actor.

        Args:
            actor_id: Actor identifier

        Returns:
            Actor status or None if not found
        """
        if actor_id not in self.actors:
            return None

        return self.actors[actor_id].get_status()

    async def get_all_status(self) -> Dict[str, ActorStatus]:
        """
        Get status of all actors.

        Returns:
            Dictionary of actor statuses
        """
        return {
            actor_id: actor.get_status()
            for actor_id, actor in self.actors.items()
        }

    async def start_monitoring(self) -> None:
        """Start monitoring actors."""
        if self._running:
            logger.warning(f"[{self.name}] Monitoring already running")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info(f"[{self.name}] Actor monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop monitoring actors."""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info(f"[{self.name}] Actor monitoring stopped")

    async def _monitor_loop(self) -> None:
        """Monitor actor health."""
        logger.info(f"[{self.name}] Starting monitor loop")

        while self._running:
            try:
                for actor_id, actor in list(self.actors.items()):
                    status = actor.get_status()

                    # Check for terminated actors
                    if status.state == ActorState.TERMINATED:
                        logger.warning(
                            f"[{self.name}] Actor {actor_id} is terminated",
                        )
                        continue

                    # Check for error state
                    if status.state == ActorState.ERROR:
                        logger.error(
                            f"[{self.name}] Actor {actor_id} in error state",
                        )
                        if self.auto_restart:
                            await self._attempt_restart(actor_id)

                    # Check for high error count
                    if status.error_count > 10:
                        logger.warning(
                            f"[{self.name}] Actor {actor_id} has high error count: {status.error_count}",
                        )

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.name}] Monitor error: {e}", exc_info=True)
                await asyncio.sleep(5.0)

    async def _attempt_restart(self, actor_id: str) -> None:
        """
        Attempt to restart a failed actor.

        Args:
            actor_id: Actor identifier
        """
        if actor_id not in self.actors:
            return

        restart_count = self.restart_counts.get(actor_id, 0)

        if restart_count >= self.max_restarts:
            logger.error(
                f"[{self.name}] Actor {actor_id} exceeded max restarts ({self.max_restarts})",
            )
            await self.terminate_actor(actor_id)
            return

        logger.info(
            f"[{self.name}] Attempting restart {restart_count + 1}/{self.max_restarts} for {actor_id}",
        )

        try:
            # Terminate current actor
            await self.actors[actor_id].terminate()

            # Re-spawn (this would require storing actor class and kwargs)
            # For now, just log the attempt
            logger.warning(
                f"[{self.name}] Restart requires actor class info - manual intervention needed",
            )

            self.restart_counts[actor_id] = restart_count + 1

        except Exception as e:
            logger.error(f"[{self.name}] Restart failed for {actor_id}: {e}")

    async def save_all_states(self) -> None:
        """Save states of all actors."""
        logger.info(f"[{self.name}] Saving all actor states...")

        tasks = [actor.save_state() for actor in self.actors.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"[{self.name}] All states saved")

    async def load_all_states(self) -> None:
        """Load states for all actors."""
        logger.info(f"[{self.name}] Loading all actor states...")

        tasks = [actor.load_state() for actor in self.actors.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"[{self.name}] All states loaded")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get supervisor statistics.

        Returns:
            Statistics dictionary
        """
        statuses = [actor.get_status() for actor in self.actors.values()]

        return {
            "total_actors": len(self.actors),
            "active_actors": sum(
                1 for s in statuses if s.state == ActorState.ACTIVE
            ),
            "suspended_actors": sum(
                1 for s in statuses if s.state == ActorState.SUSPENDED
            ),
            "terminated_actors": sum(
                1 for s in statuses if s.state == ActorState.TERMINATED
            ),
            "error_actors": sum(
                1 for s in statuses if s.state == ActorState.ERROR
            ),
            "total_messages": sum(s.message_count for s in statuses),
            "total_errors": sum(s.error_count for s in statuses),
            "monitoring_active": self._running,
        }

    async def broadcast_to_all(
        self,
        content: Dict[str, Any],
        message_type: str = "broadcast",
    ) -> None:
        """
        Broadcast a message to all actors.

        Args:
            content: Message content
            message_type: Message type identifier
        """
        logger.info(
            f"[{self.name}] Broadcasting to {len(self.actors)} actors",
        )

        tasks = [
            actor.broadcast(content, message_type)
            for actor in self.actors.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    def find_actors_by_capability(self, capability: str) -> List[str]:
        """
        Find actors with a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of actor IDs
        """
        return [
            actor_id
            for actor_id, actor in self.actors.items()
            if capability in actor.capabilities
        ]

    def find_actors_by_topic(self, topic: str) -> List[str]:
        """
        Find actors subscribed to a specific topic.

        Args:
            topic: Topic to search for

        Returns:
            List of actor IDs
        """
        return [
            actor_id
            for actor_id, actor in self.actors.items()
            if topic in actor.topics
        ]
