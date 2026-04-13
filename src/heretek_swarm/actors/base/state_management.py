"""
State management module for AgentActor.

This module contains:
- State persistence methods (save_state, load_state)
- Checkpoint methods (save_checkpoint, restore_from_checkpoint, get_checkpoints)
- Status and suspension methods (get_status, suspend, resume)
- Internal state accessors (update_state, get_state)
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from heretek_swarm.actors.base.core import AgentActor, ActorState

logger = structlog.get_logger("AgentActor")


class AgentActorStateManagement(AgentActor):
    """Mixin class for state management functionality."""

    async def save_state(self) -> None:
        """
        Persist actor state to PostgreSQL via StateRepository.

        Saves actor state with version tracking for optimistic locking.
        Falls back to legacy file system persistence if repository not available.
        """
        state_data = {
            "internal_state": self.internal_state,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "topics": self.topics,
            "capabilities": self.capabilities,
            "saved_at": datetime.now(UTC).isoformat(),
        }

        # Use state repository if available
        if self._state_repository is not None:
            try:
                # Get current version from stored record
                version = None
                if self._state_record:
                    version = self._state_record.version + 1

                self._state_record = await self._state_repository.save_state(
                    agent_id=self.agent_id,
                    state=state_data,
                    agent_type=self.actor_type,
                    version=version,
                )
                logger.info(
                    f"[{self.agent_id}] State persisted via StateRepository",
                    extra={"state": self.state.value, "version": self._state_record.version},
                )
                return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] StateRepository persistence failed: {e}",
                    exc_info=True,
                )

        # Legacy fallback: try get_db_pool() stub (injectable for testing)
        from heretek_swarm.actors import stubs as _actor_stubs

        db_pool = _actor_stubs.get_db_pool()
        if db_pool is None:
            db_pool = self.get_state("_db_pool")
        if db_pool is not None:
            try:
                # Support mock database (has execute method with SQL parsing)
                if hasattr(db_pool, "execute") and hasattr(db_pool, "_tables"):
                    # Ensure table exists in mock
                    if "agent_states" not in db_pool._tables:
                        db_pool._tables["agent_states"] = []
                    db_pool._tables["agent_states"].append({
                        "id": len(db_pool._tables["agent_states"]) + 1,
                        "agent_id": self.agent_id,
                        "agent_type": self.actor_type,
                        "state": json.dumps(state_data),
                        "created_at": datetime.now(UTC).isoformat(),
                    })
                elif not hasattr(db_pool, "acquire"):
                    # Generic async execute interface
                    await db_pool.execute(
                        "INSERT INTO agent_states (agent_id, agent_type, state) VALUES (%s, %s, %s)",
                        (self.agent_id, self.actor_type, json.dumps(state_data)),
                    )
                else:
                    async with db_pool.acquire() as conn:
                        await conn.execute(
                            """
                            INSERT INTO agent_states (id, agent_id, agent_type, state, version, updated_at, is_active)
                            VALUES (gen_random_uuid(), $1, $2, $3, 1, NOW(), true)
                            ON CONFLICT (agent_id) DO UPDATE
                            SET state = $3, version = agent_states.version + 1, updated_at = NOW()
                            """,
                            self.agent_id,
                            self.actor_type,
                            json.dumps(state_data),
                        )
                logger.info(
                    f"[{self.agent_id}] State persisted to database (legacy)",
                    extra={"state": self.state.value},
                )
                return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Database persistence failed: {e}",
                    exc_info=True,
                )

        # Final fallback: persist to file system
        try:
            import os
            state_dir = os.path.join(os.getcwd(), ".actor_states")
            os.makedirs(state_dir, exist_ok=True)
            state_file = os.path.join(state_dir, f"{self.agent_id}.json")

            with open(state_file, "w") as f:
                json.dump(state_data, f, indent=2)

            logger.info(
                f"[{self.agent_id}] State persisted to file system",
                extra={"path": state_file},
            )
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] File system persistence failed: {e}",
                exc_info=True,
            )

    async def load_state(self) -> None:
        """
        Load actor state from StateRepository.

        Attempts to load from repository first, then falls back to legacy methods.
        """
        # Try StateRepository first
        if self._state_repository is not None:
            try:
                record = await self._state_repository.load_state(self.agent_id)
                if record:
                    self._state_record = record
                    loaded_state = record.state

                    self.internal_state = loaded_state.get("internal_state", {})
                    self.message_count = loaded_state.get("message_count", 0)
                    self.error_count = loaded_state.get("error_count", 0)
                    self.state = ActorState(loaded_state.get("state", "spawning"))
                    self.created_at = loaded_state.get("created_at", self.created_at)
                    self.last_activity = loaded_state.get("last_activity")
                    self.topics = loaded_state.get("topics", self.topics)
                    self.capabilities = loaded_state.get("capabilities", self.capabilities)

                    logger.info(
                        f"[{self.agent_id}] State loaded from StateRepository",
                        extra={"state": self.state.value, "version": record.version},
                    )
                    return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] StateRepository load failed: {e}",
                    exc_info=True,
                )

        # Legacy fallback: try direct db_pool access
        db_pool = self.get_state("_db_pool")
        if db_pool is not None:
            try:
                async with db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT state, version FROM agent_states WHERE agent_id = $1 AND is_active = true",
                        self.agent_id,
                    )
                    if row:
                        loaded_state = json.loads(row["state"])
                        self.internal_state = loaded_state.get("internal_state", {})
                        self.message_count = loaded_state.get("message_count", 0)
                        self.error_count = loaded_state.get("error_count", 0)
                        self.state = ActorState(loaded_state.get("state", "spawning"))
                        self.created_at = loaded_state.get("created_at", self.created_at)
                        self.last_activity = loaded_state.get("last_activity")
                        self.topics = loaded_state.get("topics", self.topics)
                        self.capabilities = loaded_state.get("capabilities", self.capabilities)

                        logger.info(
                            f"[{self.agent_id}] State loaded from PostgreSQL (legacy)",
                            extra={"state": self.state.value},
                        )
                        return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] PostgreSQL load failed: {e}",
                    exc_info=True,
                )

        # Final fallback: load from file system
        try:
            import os
            state_file = os.path.join(os.getcwd(), ".actor_states", f"{self.agent_id}.json")

            if os.path.exists(state_file):
                with open(state_file) as f:
                    loaded_state = json.load(f)

                self.internal_state = loaded_state.get("internal_state", {})
                self.message_count = loaded_state.get("message_count", 0)
                self.error_count = loaded_state.get("error_count", 0)
                self.state = ActorState(loaded_state.get("state", "spawning"))
                self.created_at = loaded_state.get("created_at", self.created_at)
                self.last_activity = loaded_state.get("last_activity")
                self.topics = loaded_state.get("topics", self.topics)
                self.capabilities = loaded_state.get("capabilities", self.capabilities)

                logger.info(
                    f"[{self.agent_id}] State loaded from file system",
                    extra={"path": state_file},
                )
                return
        except Exception as e:
            logger.error(f"[{self.agent_id}] File system load failed: {e}", exc_info=True)

        # No state found - actor is starting fresh
        logger.info(f"[{self.agent_id}] No previous state found, starting fresh")

    async def save_checkpoint(
        self,
        metadata: dict[str, Any] | None = None,
    ) -> Any | None:
        """
        Save a versioned state checkpoint.

        Checkpoints are immutable snapshots that can be used for:
        - Rollback after errors
        - State restoration after restart
        - Audit trail

        Args:
            metadata: Optional metadata (reason, trigger, etc.)

        Returns:
            Created checkpoint, or None if repository not available
        """
        if self._state_repository is None:
            logger.warning(f"[{self.agent_id}] Cannot save checkpoint: no state repository")
            return None

        state_data = {
            "internal_state": self.internal_state,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "topics": self.topics,
            "capabilities": self.capabilities,
        }

        try:
            version = self._state_record.version + 1 if self._state_record else 1
            checkpoint = await self._state_repository.checkpoint(
                agent_id=self.agent_id,
                state=state_data,
                version=version,
                metadata=metadata,
            )
            logger.info(
                f"[{self.agent_id}] Checkpoint saved",
                extra={"version": version, "checkpoint_id": str(checkpoint.checkpoint_id)},
            )
            return checkpoint
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Checkpoint save failed: {e}",
                exc_info=True,
            )
            return None

    async def restore_from_checkpoint(
        self,
        checkpoint_id: uuid.UUID,
    ) -> bool:
        """
        Restore agent state from a checkpoint.

        Args:
            checkpoint_id: UUID of checkpoint to restore from

        Returns:
            True if restored successfully, False otherwise
        """
        if self._state_repository is None:
            logger.warning(f"[{self.agent_id}] Cannot restore checkpoint: no state repository")
            return False

        try:
            success = await self._state_repository.restore_from_checkpoint(
                agent_id=self.agent_id,
                checkpoint_id=checkpoint_id,
            )

            if success:
                # Reload the state
                await self.load_state()
                logger.info(
                    f"[{self.agent_id}] State restored from checkpoint",
                    extra={"checkpoint_id": str(checkpoint_id)},
                )

            return success
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Checkpoint restore failed: {e}",
                exc_info=True,
            )
            return False

    async def get_checkpoints(
        self,
        limit: int = 10,
    ) -> list[Any]:
        """
        Get recent checkpoints for this agent.

        Args:
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoints (newest first)
        """
        if self._state_repository is None:
            return []

        try:
            return await self._state_repository.get_checkpoints(
                agent_id=self.agent_id,
                limit=limit,
            )
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Failed to get checkpoints: {e}",
                exc_info=True,
            )
            return []

    def get_status(self) -> Any:
        """
        Get actor status information.

        Returns:
            Current actor status
        """
        from heretek_swarm.actors.base.core import ActorStatus

        return ActorStatus(
            agent_id=self.agent_id,
            state=self.state,
            message_count=self.message_count,
            created_at=self.created_at,
            topics=self.topics,
            capabilities=self.capabilities,
            mailbox_size=self.mailbox.qsize(),
            last_activity=self.last_activity,
            error_count=self.error_count,
        )

    async def suspend(self) -> None:
        """Suspend the actor temporarily."""
        if self.state == ActorState.ACTIVE:
            self.state = ActorState.SUSPENDED
            logger.info(f"[{self.agent_id}] Agent suspended")

    async def resume(self) -> None:
        """Resume a suspended or errored actor."""
        if self.state == ActorState.SUSPENDED:
            self.state = ActorState.ACTIVE
            logger.info(f"[{self.agent_id}] Agent resumed from suspended state")
        elif self.state == ActorState.ERROR:
            self.state = ActorState.ACTIVE
            logger.info(f"[{self.agent_id}] Agent recovered from error state")

    def update_state(self, key: str, value: Any) -> None:
        """
        Update internal state.

        Args:
            key: State key
            value: State value
        """
        self.internal_state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get internal state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value
        """
        return self.internal_state.get(key, default)


# Bind state management methods to AgentActor
AgentActor.save_state = AgentActorStateManagement.save_state
AgentActor.load_state = AgentActorStateManagement.load_state
AgentActor.save_checkpoint = AgentActorStateManagement.save_checkpoint
AgentActor.restore_from_checkpoint = AgentActorStateManagement.restore_from_checkpoint
AgentActor.get_checkpoints = AgentActorStateManagement.get_checkpoints
AgentActor.get_status = AgentActorStateManagement.get_status
AgentActor.suspend = AgentActorStateManagement.suspend
AgentActor.resume = AgentActorStateManagement.resume
AgentActor.update_state = AgentActorStateManagement.update_state
AgentActor.get_state = AgentActorStateManagement.get_state
