"""
State Persistence Repository for Heretek Swarm.

Provides PostgreSQL-backed persistence for agent states with:
- Save/load agent state
- Versioned checkpoints for schema compatibility
- State restoration after restart
- Concurrent update handling with optimistic locking
- Event sourcing integration for audit trail and state reconstruction
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID, uuid4

import structlog

_logger = structlog.get_logger("state.repository")

# Import event sourcing types
try:
    from heretek_swarm.state.event_store import DomainEvent
    EVENT_SOURCING_AVAILABLE = True
except ImportError:
    EVENT_SOURCING_AVAILABLE = False
    _DomainEvent = None


@dataclass
class AgentStateRecord:
    """
    Represents a persisted agent state record.
    
    Attributes:
        id: Unique record identifier (UUID)
        agent_id: Agent identifier
        agent_type: Type/class of the agent
        state: JSONB state data
        version: Version number for optimistic locking
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_active: Whether this state is active
    """
    agent_id: str
    agent_type: str
    state: Dict[str, Any]
    version: int = 1
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self.state,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, _data: Dict[str, _Any]) -> "AgentStateRecord":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            state=data["state"],
            version=data.get("version", 1),
            created_at=(
                datetime.fromisoformat(data["created_at"]) 
                if isinstance(data["created_at"], str) 
                else data["created_at"]
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"]) 
                if isinstance(data["updated_at"], str) 
                else data["updated_at"]
            ),
            is_active=data.get("is_active", True),
        )


@dataclass
class StateCheckpoint:
    """
    Represents a versioned state checkpoint.
    
    Used for state versioning and rollback capabilities.
    
    Attributes:
        checkpoint_id: Unique checkpoint identifier
        agent_id: Agent identifier
        state: State data at checkpoint
        version: Checkpoint version
        created_at: Creation timestamp
        metadata: Optional metadata about the checkpoint
    """
    checkpoint_id: UUID
    agent_id: str
    state: Dict[str, Any]
    version: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": str(self.checkpoint_id),
            "agent_id": self.agent_id,
            "state": self.state,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class StateRepository:
    """
    PostgreSQL-backed state persistence repository.
    
    Provides CRUD operations for agent states with:
    - Optimistic locking via version numbers
    - Checkpoint management for rollback
    - Automatic retry on concurrency conflicts
    - Graceful fallback to in-memory storage
    
    Database Schema (agent_states table):
        CREATE TABLE agent_states (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id VARCHAR(255) NOT NULL,
            agent_type VARCHAR(255) NOT NULL,
            state JSONB NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT true
        );
        
        CREATE INDEX idx_agent_states_agent_id ON agent_states(agent_id);
        CREATE INDEX idx_agent_states_active ON agent_states(is_active) WHERE is_active = true;
    
    Example:
        ```python
        # Initialize repository
        _repo = StateRepository(db_pool)
        await repo.initialize()
        
        # Save state
        await repo.save_state("agent-1", {"key": "value"})
        
        # Load state
        state = await repo.load_state("agent-1")
        
        # Create checkpoint
        await repo.checkpoint("agent-1", {"key": "value"}, version=2)
        
        # Restore from checkpoint
        await repo.restore_from_checkpoint("agent-1", checkpoint_id)
        ```
    """
    
    # SQL queries
    SAVE_STATE_QUERY = """
        INSERT INTO agent_states (id, agent_id, agent_type, state, version, created_at, updated_at, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (agent_id) DO UPDATE
        SET state = $4, version = $5, updated_at = $7, is_active = $8
        WHERE agent_states.version = $5 - 1
        RETURNING *
    """
    
    LOAD_STATE_QUERY = """
        SELECT id, agent_id, agent_type, state, version, created_at, updated_at, is_active
        FROM agent_states
        WHERE agent_id = $1 AND is_active = true
    """
    
    DELETE_STATE_QUERY = """
        UPDATE agent_states
        SET is_active = false, updated_at = NOW()
        WHERE agent_id = $1
    """
    
    LIST_ACTIVE_STATES_QUERY = """
        SELECT id, agent_id, agent_type, state, version, created_at, updated_at, is_active
        FROM agent_states
        WHERE is_active = true
        ORDER BY updated_at DESC
    """
    
    CHECKPOINT_QUERY = """
        INSERT INTO agent_state_checkpoints (checkpoint_id, agent_id, state, version, created_at, metadata)
        VALUES ($1, $2, $3, $4, $5, $6)
    """
    
    GET_CHECKPOINT_QUERY = """
        SELECT checkpoint_id, agent_id, state, version, created_at, metadata
        FROM agent_state_checkpoints
        WHERE checkpoint_id = $1
    """
    
    GET_CHECKPOINTS_QUERY = """
        SELECT checkpoint_id, agent_id, state, version, created_at, metadata
        FROM agent_state_checkpoints
        WHERE agent_id = $1
        ORDER BY version DESC
        LIMIT $2
    """
    
    def __init__(self, _db_pool: Optional[Any], _max_retries: int, _retry_delay: float):
        """
        Initialize state repository.
        
        Args:
            db_pool: asyncpg connection pool
            max_retries: Maximum retries for concurrent updates
            retry_delay: Base delay between retries (seconds)
        """
        self._db_pool = db_pool
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        
        # In-memory fallback storage
        self._memory_store: Dict[str, AgentStateRecord] = {}
        self._checkpoints: Dict[str, List[StateCheckpoint]] = {}
        
        # Statistics
        self._stats = {
            "db_saves": 0,
            "db_loads": 0,
            "memory_saves": 0,
            "memory_loads": 0,
            "concurrency_retries": 0,
            "checkpoints_created": 0,
            "checkpoints_restored": 0,
        }
        
        self._initialized = False
    
    async def initialize(self, _db_pool: Optional[Any]) -> None:
        """
        Initialize the repository.
        
        Args:
            db_pool: Optional asyncpg connection pool
        """
        if db_pool:
            self._db_pool = db_pool
        
        # Create checkpoint table if using database
        if self._db_pool:
            try:
                await self._create_checkpoint_table()
                self._initialized = True
                logger.info("State repository initialized with PostgreSQL")
            except Exception as e:
                logger.warning(f"PostgreSQL initialization failed, using in-memory: {e}")
                self._db_pool = None
                self._initialized = True
        else:
            self._initialized = True
            logger.info("State repository initialized with in-memory storage")
    
    async def _create_checkpoint_table(self) -> None:
        """Create the agent_state_checkpoints table if it doesn't exist."""
        if not self._db_pool:
            return
        
        async with self._db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_state_checkpoints (
                    checkpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(255) NOT NULL,
                    state JSONB NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    FOREIGN KEY (agent_id) REFERENCES agent_states(agent_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_checkpoints_agent_id ON agent_state_checkpoints(agent_id);
                CREATE INDEX IF NOT EXISTS idx_checkpoints_version ON agent_state_checkpoints(agent_id, version DESC);
            """)
    
    async def save_state(self, _agent_id: str, _state: Dict[str, _Any], _agent_type: str, _version: Optional[int]) -> AgentStateRecord:
        """
        Save agent state to database.
        
        Uses optimistic locking with version numbers to handle
        concurrent updates. Retries on version conflicts.
        
        Args:
            agent_id: Unique agent identifier
            state: State data to persist
            agent_type: Type/class of agent
            version: Expected current version (for optimistic locking)
            
        Returns:
            Saved state record
            
        Raises:
            ConcurrencyError: If max retries exceeded due to concurrent updates
        """
        _record = AgentStateRecord(
            _agent_id = agent_id,
            _agent_type = agent_type,
            state=state,
            version=version or 1,
        )
        
        if self._db_pool:
            return await self._save_to_db(record)
        else:
            return self._save_to_memory(record)
    
    async def _save_to_db(self, _record: AgentStateRecord) -> AgentStateRecord:
        """Save record to database with retry logic."""
        _attempt = 0
        _last_error = None
        
        while attempt < self._max_retries:
            try:
                async with self._db_pool.acquire() as conn:
                    now = datetime.now(timezone.utc)
                    record.updated_at = now
                    
                    _row = await conn.fetchrow(
                        self.SAVE_STATE_QUERY,
                        record.id,
                        record.agent_id,
                        record.agent_type,
                        json.dumps(record.state),
                        record.version,
                        record.created_at,
                        now,
                        record.is_active,
                    )
                    
                    if row:
                        self._stats["db_saves"] += 1
                        logger.debug(
                            f"State saved for {record.agent_id}",
                            _extra = {"version": record.version},
                        )
                        return record
                    else:
                        # Version conflict - retry with incremented version
                        attempt += 1
                        self._stats["concurrency_retries"] += 1
                        
                        if attempt < self._max_retries:
                            # Fetch current version and retry
                            _current = await self._load_from_db(record.agent_id)
                            if current:
                                record.version = current.version + 1
                            await asyncio.sleep(self._retry_delay * (2 ** (attempt - 1)))
                        else:
                            raise ConcurrencyError(
                                f"Max retries ({self._max_retries}) exceeded for agent {record.agent_id}"
                            )
                            
            except Exception as e:
                _last_error = e
                attempt += 1
                if attempt < self._max_retries:
                    await asyncio.sleep(self._retry_delay * (2 ** (attempt - 1)))
                else:
                    break
        
        # All retries failed, fall back to memory
        logger.warning(
            f"Database save failed after {attempt} attempts, using memory: {last_error}"
        )
        return self._save_to_memory(record)
    
    def _save_to_memory(self, _record: AgentStateRecord) -> AgentStateRecord:
        """Save record to in-memory storage."""
        self._memory_store[record.agent_id] = record
        self._stats["memory_saves"] += 1
        logger.debug(f"State saved to memory for {record.agent_id}")
        return record
    
    async def load_state(self, _agent_id: str) -> Optional[AgentStateRecord]:
        """
        Load agent state from database.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            State record or None if not found
        """
        if self._db_pool:
            _record = await self._load_from_db(agent_id)
        else:
            _record = self._load_from_memory(agent_id)
        
        if record:
            logger.debug(f"State loaded for {agent_id}")
        
        return record
    
    async def _load_from_db(self, _agent_id: str) -> Optional[AgentStateRecord]:
        """Load record from database."""
        try:
            async with self._db_pool.acquire() as conn:
                _row = await conn.fetchrow(
                    self.LOAD_STATE_QUERY,
                    agent_id,
                )
                
                if row:
                    self._stats["db_loads"] += 1
                    return AgentStateRecord(
                        _id = row["id"],
                        _agent_id = row["agent_id"],
                        _agent_type = row["agent_type"],
                        state=json.loads(row["state"]),
                        version=row["version"],
                        created_at=row["created_at"],
                        _updated_at = row["updated_at"],
                        _is_active = row["is_active"],
                    )
        except Exception as e:
            logger.error(f"Database load failed: {e}")
        
        return None
    
    def _load_from_memory(self, _agent_id: str) -> Optional[AgentStateRecord]:
        """Load record from memory."""
        _record = self._memory_store.get(agent_id)
        if record:
            self._stats["memory_loads"] += 1
        return record
    
    async def delete_state(self, _agent_id: str) -> bool:
        """
        Delete (deactivate) agent state.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if deleted, False if not found
        """
        if self._db_pool:
            try:
                async with self._db_pool.acquire() as conn:
                    _result = await conn.execute(
                        self.DELETE_STATE_QUERY,
                        agent_id,
                    )
                    self._stats["db_saves"] += 1
                    _deleted = result != "DELETE 0"
                    logger.debug(f"State {'deleted' if deleted else 'not found'} for {agent_id}")
                    return deleted
            except Exception as e:
                logger.error(f"Database delete failed: {e}")
        
        # Memory fallback
        if agent_id in self._memory_store:
            del self._memory_store[agent_id]
            logger.debug(f"Memory state deleted for {agent_id}")
            return True
        
        return False
    
    async def list_active_states(self) -> List[AgentStateRecord]:
        """
        List all active agent states.
        
        Returns:
            List of active state records
        """
        if self._db_pool:
            try:
                async with self._db_pool.acquire() as conn:
                    _rows = await conn.fetch(self.LIST_ACTIVE_STATES_QUERY)
                    self._stats["db_loads"] += len(rows)
                    return [
                        AgentStateRecord(
                            _id = row["id"],
                            _agent_id = row["agent_id"],
                            _agent_type = row["agent_type"],
                            state=json.loads(row["state"]),
                            version=row["version"],
                            _created_at = row["created_at"],
                            _updated_at = row["updated_at"],
                            _is_active = row["is_active"],
                        )
                        for row in rows
                    ]
            except Exception as e:
                logger.error(f"Database list failed: {e}")
        
        # Memory fallback
        self._stats["memory_loads"] += len(self._memory_store)
        return list(self._memory_store.values())
    
    async def checkpoint(self, _agent_id: str, _state: Dict[str, _Any], _version: int, _metadata: Optional[Dict[str, _Any]]) -> StateCheckpoint:
        """
        Create a versioned state checkpoint.
        
        Checkpoints are immutable snapshots that can be used for:
        - Rollback after errors
        - State restoration after restart
        - Audit trail
        
        Args:
            agent_id: Agent identifier
            state: State data to checkpoint
            version: Checkpoint version number
            metadata: Optional metadata (reason, trigger, etc.)
            
        Returns:
            Created checkpoint
        """
        checkpoint = StateCheckpoint(
            checkpoint_id=uuid4(),
            _agent_id = agent_id,
            state=state,
            _version = version,
            created_at=datetime.now(timezone.utc),
            _metadata = metadata,
        )
        
        if self._db_pool:
            try:
                async with self._db_pool.acquire() as conn:
                    await conn.execute(
                        self.CHECKPOINT_QUERY,
                        checkpoint.checkpoint_id,
                        agent_id,
                        json.dumps(state),
                        version,
                        checkpoint.created_at,
                        json.dumps(metadata) if metadata else None,
                    )
                    self._stats["checkpoints_created"] += 1
                    logger.debug(
                        f"Checkpoint created for {agent_id}",
                        _extra = {"version": version},
                    )
                    return checkpoint
            except Exception as e:
                logger.error(f"Database checkpoint failed: {e}")
        
        # Memory fallback
        if agent_id not in self._checkpoints:
            self._checkpoints[agent_id] = []
        self._checkpoints[agent_id].append(checkpoint)
        self._stats["checkpoints_created"] += 1
        return checkpoint
    
    async def get_checkpoint(self, _checkpoint_id: UUID) -> Optional[StateCheckpoint]:
        """
        Get a specific checkpoint by ID.
        
        Args:
            checkpoint_id: Checkpoint identifier
            
        Returns:
            Checkpoint or None if not found
        """
        if self._db_pool:
            try:
                async with self._db_pool.acquire() as conn:
                    _row = await conn.fetchrow(
                        self.GET_CHECKPOINT_QUERY,
                        checkpoint_id,
                    )
                    if row:
                        return StateCheckpoint(
                            _checkpoint_id = row["checkpoint_id"],
                            _agent_id = row["agent_id"],
                            state=json.loads(row["state"]),
                            version=row["version"],
                            _created_at = row["created_at"],
                            _metadata = row["metadata"],
                        )
            except Exception as e:
                logger.error(f"Database checkpoint get failed: {e}")
        
        # Memory fallback
        for checkpoints in self._checkpoints.values():
            for cp in checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    return cp
        
        return None
    
    async def get_checkpoints(self, _agent_id: str, _limit: int) -> List[StateCheckpoint]:
        """
        Get checkpoints for an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of checkpoints (newest first)
        """
        if self._db_pool:
            try:
                async with self._db_pool.acquire() as conn:
                    _rows = await conn.fetch(
                        self.GET_CHECKPOINTS_QUERY,
                        agent_id,
                        limit,
                    )
                    return [
                        StateCheckpoint(
                            _checkpoint_id = row["checkpoint_id"],
                            _agent_id = row["agent_id"],
                            state=json.loads(row["state"]),
                            version=row["version"],
                            _created_at = row["created_at"],
                            _metadata = row["metadata"],
                        )
                        for row in rows
                    ]
            except Exception as e:
                logger.error(f"Database checkpoints list failed: {e}")
        
        # Memory fallback
        _checkpoints = self._checkpoints.get(agent_id, [])
        return sorted(checkpoints, key=lambda c: c.version, reverse=True)[:limit]
    
    async def restore_from_checkpoint(self, _agent_id: str, _checkpoint_id: UUID) -> bool:
        """
        Restore agent state from a checkpoint.
        
        Args:
            agent_id: Agent identifier
            checkpoint_id: Checkpoint to restore from
            
        Returns:
            True if restored, False if checkpoint not found
        """
        _checkpoint = await self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return False
        
        # Save the checkpoint state as current state
        await self.save_state(
            _agent_id = agent_id,
            state=checkpoint.state,
            _version = checkpoint.version + 1,
        )
        
        self._stats["checkpoints_restored"] += 1
        logger.info(
            f"State restored from checkpoint for {agent_id}",
            _extra = {"checkpoint_id": str(checkpoint_id)},
        )
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        return {
            **self._stats,
            "memory_records": len(self._memory_store),
            "agents_with_checkpoints": len(self._checkpoints),
            "initialized": self._initialized,
            "using_database": self._db_pool is not None,
        }


class ConcurrencyError(Exception):
    """Raised when concurrent update conflicts exceed max retries."""
    pass


# =============================================================================
# Event Sourcing Integration
# =============================================================================

class EventSourcedRepository(StateRepository):
    """
    Event-sourced state repository extending StateRepository.
    
    Combines traditional state persistence with event sourcing:
    - All state changes are stored as immutable events
    - Current state is stored for performance (CQRS pattern)
    - State can be reconstructed from events at any time
    - Supports snapshotting for large event streams
    
    Example:
        ```python
        _repo = EventSourcedRepository(db_pool)
        await repo.initialize()
        
        # Save state with event
        await repo.save_state_with_event(
            _agent_id = "agent-1",
            state={"status": "running"},
            event_type="agent.state.changed",
            _event_payload = {"old_state": "stopped", "new_state": "running"},
        )
        
        # Reconstruct state from events
        state = await repo.reconstruct_state("agent-1")
        ```
    """
    
    def __init__(self, _db_pool: Optional[Any], _max_retries: int, _retry_delay: float, _snapshot_interval: int):
        """
        Initialize event-sourced repository.
        
        Args:
            db_pool: asyncpg connection pool
            max_retries: Maximum retries for concurrent updates
            retry_delay: Base delay between retries
            snapshot_interval: Create snapshot every N events
        """
        super().__init__(db_pool, max_retries, retry_delay)
        
        # Event store reference
        self._event_store = None
        self._snapshot_interval = snapshot_interval
        
        # Event appliers
        self._event_appliers: Dict[str, Callable[[Dict[str, Any], DomainEvent], Dict[str, Any]]] = {
            "agent.state.changed": self._apply_agent_state_changed,
            "agent.config.updated": self._apply_agent_config_updated,
            "agent.created": self._apply_agent_created,
        }
        
        logger.info(
            "EventSourcedRepository initialized",
            _snapshot_interval = snapshot_interval,
        )
    
    async def initialize(self, _db_pool: Optional[Any]) -> None:
        """Initialize repository and event store."""
        await super().initialize(db_pool)
        
        # Initialize event store
        from heretek_swarm.state.event_store import get_event_store
        
        self._event_store = get_event_store()
        await self._event_store.initialize(db_pool)
        
        logger.info("EventSourcedRepository fully initialized")
    
    async def save_state_with_event(self, _agent_id: str, _state: Dict[str, _Any], _event_type: str, _event_payload: Dict[str, _Any], _agent_type: str, _version: Optional[int], _event_metadata: Optional[Dict[str, _Any]]) -> AgentStateRecord:
        """
        Save state and append corresponding event.
        
        Args:
            agent_id: Agent identifier
            state: State data to persist
            event_type: Type of event
            event_payload: Event payload
            agent_type: Type of agent
            version: Expected current version
            event_metadata: Event metadata (correlation_id, causation_id, user_id)
            
        Returns:
            Saved state record
        """
        # Get current version
        _current_version = await self._event_store.get_last_version(agent_id) if self._event_store else 0
        _new_version = current_version + 1
        
        # Create event
        event = DomainEvent.create(
            event_type=event_type,
            _aggregate_id = agent_id,
            _aggregate_type = agent_type,
            payload=event_payload,
            _version = new_version,
            _metadata = event_metadata,
        )
        
        # Append event first (event sourcing)
        if self._event_store:
            await self._event_store.append(event)
        
        # Save current state (for performance)
        _record = await self.save_state(
            _agent_id = agent_id,
            state=state,
            _agent_type = agent_type,
            _version = new_version,
        )
        
        logger.info(
            "State saved with event",
            _agent_id = agent_id,
            event_type=event_type,
            _version = new_version,
        )
        
        return record
    
    async def reconstruct_state(self, _agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Reconstruct state from events.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Reconstructed state or None if no events found
        """
        if not self._event_store:
            logger.warning("Event store not available")
            return None
        
        # Get current state as base
        _current_record = await self.load_state(agent_id)
        _initial_state = current_record.state if current_record else {}
        
        # Reconstruct from events
        state = await self._event_store.reconstruct_state(
            _aggregate_id = agent_id,
            _applier = self._apply_event,
            _initial_state = initial_state,
        )
        
        logger.info(f"State reconstructed for {agent_id}")
        return state
    
    def _apply_event(self, _state: Dict[str, _Any], _event: DomainEvent) -> Dict[str, Any]:
        """Apply event to state."""
        _applier = self._event_appliers.get(event.event_type)
        
        if applier:
            return applier(state, event)
        else:
            # Default: merge payload into state
            state.update(event.payload)
            return state
    
    def _apply_agent_state_changed(self, _state: Dict[str, _Any], _event: DomainEvent) -> Dict[str, Any]:
        """Apply agent.state.changed event."""
        if "new_state" in event.payload:
            state["state"] = event.payload["new_state"]
        if "status" in event.payload:
            state["status"] = event.payload["status"]
        state["last_state_change"] = event.timestamp.isoformat()
        return state
    
    def _apply_agent_config_updated(self, _state: Dict[str, _Any], _event: DomainEvent) -> Dict[str, Any]:
        """Apply agent.config.updated event."""
        if "config" in event.payload:
            state["config"] = event.payload["config"]
        state["last_config_update"] = event.timestamp.isoformat()
        return state
    
    def _apply_agent_created(self, _state: Dict[str, _Any], _event: DomainEvent) -> Dict[str, Any]:
        """Apply agent.created event."""
        state.update(event.payload)
        state["created_at"] = event.timestamp.isoformat()
        return state
    
    async def get_event_history(self, _agent_id: str, _from_version: int) -> List[DomainEvent]:
        """
        Get event history for an agent.
        
        Args:
            agent_id: Agent identifier
            from_version: Start version (exclusive)
            
        Returns:
            List of events
        """
        if not self._event_store:
            return []
        
        return await self._event_store.get_events(agent_id, from_version=from_version)
    
    async def create_state_snapshot(self, _agent_id: str, _agent_type: str) -> bool:
        """
        Create a state snapshot.
        
        Args:
            agent_id: Agent identifier
            agent_type: Agent type
            
        Returns:
            True if snapshot created
        """
        if not self._event_store:
            return False
        
        # Get current state
        _record = await self.load_state(agent_id)
        if not record:
            return False
        
        # Get current version
        _version = await self._event_store.get_last_version(agent_id)
        
        # Create snapshot
        return await self._event_store.create_snapshot(
            _aggregate_id = agent_id,
            _aggregate_type = agent_type,
            _state = record.state,
            _version = version,
        )
    
    def register_event_applier(self, _event_type: str, _applier: Callable[[Dict[str, _Any], _DomainEvent], _Dict[str, _Any]]) -> None:
        """
        Register a custom event applier.
        
        Args:
            event_type: Type of event
            applier: Function to apply event to state
        """
        self._event_appliers[event_type] = applier
        logger.debug(f"Event applier registered for {event_type}")


# Override get_event_store for event_sourced compatibility
def get_event_sourced_repository() -> EventSourcedRepository:
    """Get or create the event-sourced repository singleton."""
    # This would typically be a singleton, but for now create new instance
    return EventSourcedRepository()
