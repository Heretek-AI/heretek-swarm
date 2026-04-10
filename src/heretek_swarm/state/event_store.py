"""
Event Store for Heretek Swarm - Event Sourcing Implementation.

This module provides event sourcing capabilities:
- Store all state changes as immutable events
- Support event replay for state reconstruction
- Implement snapshotting for performance
- Event versioning for schema evolution
- Query events by agent, workflow, time range

Event Structure:
    - event_id: Unique event identifier
    - event_type: Type of event (e.g., "agent.state.changed")
    - aggregate_id: Entity identifier (agent_id, workflow_id)
    - aggregate_type: Entity type (e.g., "Agent", "Workflow")
    - timestamp: Event timestamp
    - version: Event version for optimistic concurrency
    - payload: Event data
    - metadata: Correlation ID, causation ID, user_id, etc.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum

import structlog

_logger = structlog.get_logger(__name__)


class EventType(str, Enum):
    """Standard event types for the swarm."""
    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_SUSPENDED = "agent.suspended"
    AGENT_RESUMED = "agent.resumed"
    AGENT_STATE_CHANGED = "agent.state.changed"
    AGENT_CONFIG_UPDATED = "agent.config.updated"
    AGENT_MESSAGE_RECEIVED = "agent.message.received"
    AGENT_MESSAGE_SENT = "agent.message.sent"
    AGENT_ERROR = "agent.error"
    
    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_STEP_EXECUTED = "workflow.step.executed"
    WORKFLOW_STATE_CHANGED = "workflow.state.changed"
    
    # Consciousness events
    PHI_CALCULATED = "consciousness.phi.calculated"
    COHERENCE_UPDATED = "consciousness.coherence.updated"
    EMERGENCE_DETECTED = "consciousness.emergence.detected"
    
    # System events
    SYSTEM_HEALTH_CHECK = "system.health.check"
    SYSTEM_RESOURCE_UPDATED = "system.resource.updated"
    SYSTEM_CONFIG_CHANGED = "system.config.changed"


@dataclass
class DomainEvent:
    """
    Domain event for event sourcing.
    
    Attributes:
        event_id: Unique event identifier (UUID)
        event_type: Type of event
        aggregate_id: Entity identifier
        aggregate_type: Entity type
        timestamp: Event timestamp (UTC)
        version: Event version for optimistic concurrency
        payload: Event data
        metadata: Additional context (correlation_id, causation_id, user_id)
    """
    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    timestamp: datetime
    version: int
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "payload": self.payload,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, _data: Dict[str, _Any]) -> "DomainEvent":
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if isinstance(data["timestamp"], str)
                else data["timestamp"]
            ),
            version=data["version"],
            payload=data["payload"],
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def create(cls, _event_type: str, _aggregate_id: str, _aggregate_type: str, _payload: Dict[str, _Any], _version: int, _metadata: Optional[Dict[str, _Any]]) -> "DomainEvent":
        """
        Create a new domain event.
        
        Args:
            event_type: Type of event
            aggregate_id: Entity identifier
            aggregate_type: Entity type
            payload: Event data
            version: Event version
            metadata: Additional context
            
        Returns:
            New DomainEvent instance
        """
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            timestamp=datetime.now(timezone.utc),
            version=version,
            payload=payload,
            metadata=metadata or {},
        )


@dataclass
class Snapshot:
    """
    State snapshot for performance optimization.
    
    Attributes:
        snapshot_id: Unique snapshot identifier
        aggregate_id: Entity identifier
        aggregate_type: Entity type
        state: Snapshot state data
        version: Version at snapshot time
        created_at: Snapshot creation timestamp
        metadata: Optional metadata
    """
    snapshot_id: str
    aggregate_id: str
    aggregate_type: str
    state: Dict[str, Any]
    version: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "state": self.state,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, _data: Dict[str, _Any]) -> "Snapshot":
        """Create from dictionary."""
        return cls(
            snapshot_id=data["snapshot_id"],
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            state=data["state"],
            version=data["version"],
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if isinstance(data["created_at"], str)
                else data["created_at"]
            ),
            metadata=data.get("metadata"),
        )


class EventStore:
    """
    Event store for domain events.
    
    Provides:
    - Append-only event storage
    - Event replay for state reconstruction
    - Snapshot management
    - Event querying by various criteria
    - Zero-trust security integration
    
    Example:
        ```python
        _store = EventStore(db_pool)
        await store.initialize()
        
        # Append event
        event = DomainEvent.create(
            event_type="agent.state.changed",
            aggregate_id="agent-1",
            aggregate_type="Agent",
            payload={"old_state": "stopped", "new_state": "running"},
        )
        await store.append(event)
        
        # Get events for aggregate
        _events = await store.get_events("agent-1")
        
        # Reconstruct state
        state = await store.reconstruct_state("agent-1", apply_event)
        ```
    """
    
    # SQL queries
    APPEND_EVENT_QUERY = """
        INSERT INTO domain_events (
            event_id, event_type, aggregate_id, aggregate_type,
            timestamp, version, payload, metadata, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    """
    
    GET_EVENTS_QUERY = """
        SELECT event_id, event_type, aggregate_id, aggregate_type,
               timestamp, version, payload, metadata
        FROM domain_events
        WHERE aggregate_id = $1
        ORDER BY version ASC
    """
    
    GET_EVENTS_BY_TYPE_QUERY = """
        SELECT event_id, event_type, aggregate_id, aggregate_type,
               timestamp, version, payload, metadata
        FROM domain_events
        WHERE event_type = $1
        ORDER BY timestamp DESC
        LIMIT $2
    """
    
    GET_EVENTS_BY_TIME_RANGE_QUERY = """
        SELECT event_id, event_type, aggregate_id, aggregate_type,
               timestamp, version, payload, metadata
        FROM domain_events
        WHERE timestamp >= $1 AND timestamp <= $2
        ORDER BY timestamp ASC
        LIMIT $3
    """
    
    GET_EVENTS_BY_AGGREGATE_TYPE_QUERY = """
        SELECT event_id, event_type, aggregate_id, aggregate_type,
               timestamp, version, payload, metadata
        FROM domain_events
        WHERE aggregate_type = $1
        ORDER BY timestamp DESC
        LIMIT $2
    """
    
    GET_LAST_VERSION_QUERY = """
        SELECT MAX(version) as version
        FROM domain_events
        WHERE aggregate_id = $1
    """
    
    APPEND_SNAPSHOT_QUERY = """
        INSERT INTO event_snapshots (
            snapshot_id, aggregate_id, aggregate_type,
            state, version, created_at, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (aggregate_id) DO UPDATE
        SET state = $4, version = $5, created_at = $6, metadata = $7
    """
    
    GET_SNAPSHOT_QUERY = """
        SELECT snapshot_id, aggregate_id, aggregate_type,
               state, version, created_at, metadata
        FROM event_snapshots
        WHERE aggregate_id = $1
    """
    
    def __init__(self, _db_pool: Optional[Any], _snapshot_interval: int, _zero_trust_enabled: bool):
        """
        Initialize event store.
        
        Args:
            db_pool: asyncpg connection pool
            snapshot_interval: Create snapshot every N events
            zero_trust_enabled: Enable zero-trust security
        """
        self._db_pool = db_pool
        self._snapshot_interval = snapshot_interval
        self._zero_trust_enabled = zero_trust_enabled
        
        # In-memory storage
        self._memory_events: List[DomainEvent] = []
        self._memory_snapshots: Dict[str, Snapshot] = {}
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Statistics
        self._stats = {
            "events_appended": 0,
            "events_replayed": 0,
            "snapshots_created": 0,
            "snapshots_restored": 0,
        }
        
        self._initialized = False
        
        logger.info(
            "EventStore initialized",
            _db_enabled = db_pool is not None,
            _snapshot_interval = snapshot_interval,
        )
    
    async def initialize(self, _db_pool: Optional[Any]) -> None:
        """
        Initialize the event store.
        
        Args:
            db_pool: Optional asyncpg connection pool
        """
        if db_pool:
            self._db_pool = db_pool
        
        if self._db_pool:
            try:
                await self._create_tables()
                self._initialized = True
                logger.info("EventStore initialized with PostgreSQL")
            except Exception as e:
                logger.warning(f"PostgreSQL initialization failed, using in-memory: {e}")
                self._db_pool = None
                self._initialized = True
        else:
            self._initialized = True
            logger.info("EventStore initialized with in-memory storage")
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self._db_pool:
            return
        
        async with self._db_pool.acquire() as conn:
            # Domain events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_events (
                    event_id UUID PRIMARY KEY,
                    event_type VARCHAR(255) NOT NULL,
                    aggregate_id VARCHAR(255) NOT NULL,
                    aggregate_type VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    version INTEGER NOT NULL,
                    payload JSONB NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_events_aggregate ON domain_events(aggregate_id);
                CREATE INDEX IF NOT EXISTS idx_events_type ON domain_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON domain_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_aggregate_type ON domain_events(aggregate_type);
                CREATE INDEX IF NOT EXISTS idx_events_version ON domain_events(aggregate_id, version);
            """)
            
            # Snapshots table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS event_snapshots (
                    snapshot_id UUID PRIMARY KEY,
                    aggregate_id VARCHAR(255) NOT NULL UNIQUE,
                    aggregate_type VARCHAR(255) NOT NULL,
                    state JSONB NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
                CREATE INDEX IF NOT EXISTS idx_snapshots_aggregate ON event_snapshots(aggregate_id);
            """)
    
    async def append(self, _event: DomainEvent) -> bool:
        """
        Append an event to the store.
        
        Args:
            event: Event to append
            
        Returns:
            True if appended successfully
        """
        if self._db_pool:
            return await self._append_to_db(event)
        else:
            return self._append_to_memory(event)
    
    async def _append_to_db(self, _event: DomainEvent) -> bool:
        """Append event to database."""
        try:
            async with self._db_pool.acquire() as conn:
                await conn.execute(
                    self.APPEND_EVENT_QUERY,
                    event.event_id,
                    event.event_type,
                    event.aggregate_id,
                    event.aggregate_type,
                    event.timestamp,
                    event.version,
                    json.dumps(event.payload),
                    json.dumps(event.metadata),
                    datetime.now(timezone.utc),
                )
                
                self._stats["events_appended"] += 1
                
                # Check if snapshot needed
                await self._check_snapshot(event.aggregate_id, event.aggregate_type)
                
                # Notify handlers
                await self._notify_handlers(event)
                
                logger.debug(f"Event appended: {event.event_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            return False
    
    def _append_to_memory(self, _event: DomainEvent) -> bool:
        """Append event to in-memory storage."""
        self._memory_events.append(event)
        self._stats["events_appended"] += 1
        
        # Check if snapshot needed
        self._check_snapshot_memory(event.aggregate_id, event.aggregate_type)
        
        # Notify handlers
        asyncio.create_task(self._notify_handlers(event))
        
        logger.debug(f"Event appended to memory: {event.event_id}")
        return True
    
    async def _check_snapshot(self, _aggregate_id: str, _aggregate_type: str) -> None:
        """Check if snapshot should be created."""
        # Get event count for aggregate
        async with self._db_pool.acquire() as conn:
            _row = await conn.fetchval(
                "SELECT COUNT(*) FROM domain_events WHERE aggregate_id = $1",
                aggregate_id,
            )
            
            if row and row % self._snapshot_interval == 0:
                # Create snapshot
                state = await self.reconstruct_state(aggregate_id, self._default_applier)
                await self.create_snapshot(aggregate_id, aggregate_type, state, row)
    
    def _check_snapshot_memory(self, _aggregate_id: str, _aggregate_type: str) -> None:
        """Check if snapshot should be created in memory."""
        _count = sum(
            1 for e in self._memory_events if e.aggregate_id == aggregate_id
        )
        
        if count > 0 and count % self._snapshot_interval == 0:
            # Skip snapshot reconstruction during event append to avoid recursion
            pass
    
    async def get_events(self, _aggregate_id: str, _from_version: int, _to_version: Optional[int]) -> List[DomainEvent]:
        """
        Get events for an aggregate.
        
        Args:
            aggregate_id: Entity identifier
            from_version: Start version (exclusive)
            to_version: End version (inclusive)
            
        Returns:
            List of events
        """
        if self._db_pool:
            return await self._get_events_from_db(aggregate_id, from_version, to_version)
        else:
            return self._get_events_from_memory(aggregate_id, from_version, to_version)
    
    async def _get_events_from_db(self, _aggregate_id: str, _from_version: int, _to_version: Optional[int]) -> List[DomainEvent]:
        """Get events from database."""
        async with self._db_pool.acquire() as conn:
            if to_version:
                _rows = await conn.fetch(
                    f"""
                        SELECT event_id, event_type, aggregate_id, aggregate_type,
                               timestamp, version, payload, metadata
                        FROM domain_events
                        WHERE aggregate_id = $1 AND version > $2 AND version <= $3
                        ORDER BY version ASC
                    """,
                    aggregate_id, from_version, to_version,
                )
            else:
                _rows = await conn.fetch(
                    f"""
                        SELECT event_id, event_type, aggregate_id, aggregate_type,
                               timestamp, version, payload, metadata
                        FROM domain_events
                        WHERE aggregate_id = $1 AND version > $2
                        ORDER BY version ASC
                    """,
                    aggregate_id, from_version,
                )
            
            return [
                DomainEvent(
                    _event_id = row["event_id"],
                    event_type=row["event_type"],
                    aggregate_id=row["aggregate_id"],
                    aggregate_type=row["aggregate_type"],
                    _timestamp = row["timestamp"],
                    version=row["version"],
                    payload=json.loads(row["payload"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]
    
    def _get_events_from_memory(self, _aggregate_id: str, _from_version: int, _to_version: Optional[int]) -> List[DomainEvent]:
        """Get events from memory."""
        _events = [
            e for e in self._memory_events
            if e.aggregate_id == aggregate_id and e.version > from_version
        ]
        
        if to_version:
            _events = [e for e in events if e.version <= to_version]
        
        return sorted(events, key=lambda e: e.version)
    
    async def get_events_by_type(self, _event_type: str, _limit: int) -> List[DomainEvent]:
        """Get events by type."""
        if self._db_pool:
            async with self._db_pool.acquire() as conn:
                _rows = await conn.fetch(
                    self.GET_EVENTS_BY_TYPE_QUERY,
                    event_type, limit,
                )
                return [self._row_to_event(row) for row in rows]
        else:
            return [
                e for e in self._memory_events if e.event_type == event_type
            ][-limit:]
    
    async def get_events_by_time_range(self, _start_time: datetime, _end_time: datetime, _limit: int) -> List[DomainEvent]:
        """Get events within a time range."""
        if self._db_pool:
            async with self._db_pool.acquire() as conn:
                _rows = await conn.fetch(
                    self.GET_EVENTS_BY_TIME_RANGE_QUERY,
                    start_time, end_time, limit,
                )
                return [self._row_to_event(row) for row in rows]
        else:
            return [
                e for e in self._memory_events
                if start_time <= e.timestamp <= end_time
            ][-limit:]
    
    async def get_events_by_aggregate_type(self, _aggregate_type: str, _limit: int) -> List[DomainEvent]:
        """Get events by aggregate type."""
        if self._db_pool:
            async with self._db_pool.acquire() as conn:
                _rows = await conn.fetch(
                    self.GET_EVENTS_BY_AGGREGATE_TYPE_QUERY,
                    aggregate_type, limit,
                )
                return [self._row_to_event(row) for row in rows]
        else:
            return [
                e for e in self._memory_events if e.aggregate_type == aggregate_type
            ][-limit:]
    
    def _row_to_event(self, _row) -> DomainEvent:
        """Convert database row to DomainEvent."""
        return DomainEvent(
            _event_id = row["event_id"],
            event_type=row["event_type"],
            aggregate_id=row["aggregate_id"],
            aggregate_type=row["aggregate_type"],
            _timestamp = row["timestamp"],
            version=row["version"],
            payload=json.loads(row["payload"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
    
    async def get_last_version(self, _aggregate_id: str) -> int:
        """Get the last version number for an aggregate."""
        if self._db_pool:
            async with self._db_pool.acquire() as conn:
                _row = await conn.fetchrow(
                    self.GET_LAST_VERSION_QUERY,
                    aggregate_id,
                )
                return row["version"] or 0
        else:
            _versions = [
                e.version for e in self._memory_events
                if e.aggregate_id == aggregate_id
            ]
            return max(versions) if versions else 0
    
    async def reconstruct_state(self, _aggregate_id: str, _applier: Callable[[Dict[str, _Any], _DomainEvent], _Dict[str, _Any]], _initial_state: Optional[Dict[str, _Any]]) -> Dict[str, Any]:
        """
        Reconstruct state by replaying events.
        
        Args:
            aggregate_id: Entity identifier
            applier: Function to apply event to state (state, event) -> new_state
            initial_state: Initial state to start from
            
        Returns:
            Reconstructed state
        """
        # Get snapshot if available
        snapshot = await self.get_snapshot(aggregate_id)
        
        if snapshot:
            state = snapshot.state.copy()
            _from_version = snapshot.version
            self._stats["snapshots_restored"] += 1
            logger.debug(f"Restored from snapshot: {aggregate_id} v{from_version}")
        else:
            state = initial_state or {}
            _from_version = 0
        
        # Get events after snapshot
        _events = await self.get_events(aggregate_id, from_version=from_version)
        
        # Apply events
        for event in events:
            state = applier(state, event)
            self._stats["events_replayed"] += 1
        
        logger.debug(f"Reconstructed state for {aggregate_id} with {len(events)} events")
        return state
    
    def _default_applier(self, _state: Dict[str, _Any], _event: DomainEvent) -> Dict[str, Any]:
        """Default state applier that merges payload."""
        state.update(event.payload)
        return state
    
    def _reconstruct_from_memory(self, _aggregate_id: str, _applier: Callable[[Dict[str, _Any], _DomainEvent], _Dict[str, _Any]], _initial_state: Optional[Dict[str, _Any]]) -> Dict[str, Any]:
        """Reconstruct state from memory."""
        # Check for snapshot
        snapshot = self._memory_snapshots.get(aggregate_id)
        
        if snapshot:
            state = snapshot.state.copy()
            _from_version = snapshot.version
        else:
            state = initial_state or {}
            _from_version = 0
        
        # Get and apply events
        _events = self._get_events_from_memory(aggregate_id, from_version=from_version)
        for event in events:
            state = applier(state, event)
        
        return state
    
    async def create_snapshot(self, _aggregate_id: str, _aggregate_type: str, _state: Dict[str, _Any], _version: int, _metadata: Optional[Dict[str, _Any]]) -> bool:
        """
        Create a state snapshot.
        
        Args:
            aggregate_id: Entity identifier
            aggregate_type: Entity type
            state: State to snapshot
            version: Version at snapshot time
            metadata: Optional metadata
            
        Returns:
            True if created successfully
        """
        snapshot = Snapshot(
            snapshot_id=str(uuid4()),
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            state=state,
            version=version,
            created_at=datetime.now(timezone.utc),
            metadata=metadata,
        )
        
        if self._db_pool:
            return await self._create_snapshot_db(snapshot)
        else:
            return self._create_snapshot_memory(snapshot)
    
    async def _create_snapshot_db(self, _snapshot: Snapshot) -> bool:
        """Create snapshot in database."""
        try:
            async with self._db_pool.acquire() as conn:
                await conn.execute(
                    self.APPEND_SNAPSHOT_QUERY,
                    snapshot.snapshot_id,
                    snapshot.aggregate_id,
                    snapshot.aggregate_type,
                    json.dumps(snapshot.state),
                    snapshot.version,
                    snapshot.created_at,
                    json.dumps(snapshot.metadata) if snapshot.metadata else None,
                )
                
                self._stats["snapshots_created"] += 1
                logger.debug(f"Snapshot created: {snapshot.aggregate_id} v{snapshot.version}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return False
    
    def _create_snapshot_memory(self, _snapshot: Snapshot) -> bool:
        """Create snapshot in memory."""
        self._memory_snapshots[snapshot.aggregate_id] = snapshot
        self._stats["snapshots_created"] += 1
        logger.debug(f"Memory snapshot created: {snapshot.aggregate_id}")
        return True
    
    async def get_snapshot(self, _aggregate_id: str) -> Optional[Snapshot]:
        """Get snapshot for an aggregate."""
        if self._db_pool:
            async with self._db_pool.acquire() as conn:
                _row = await conn.fetchrow(
                    self.GET_SNAPSHOT_QUERY,
                    aggregate_id,
                )
                if row:
                    return Snapshot(
                        _snapshot_id = row["snapshot_id"],
                        _aggregate_id = row["aggregate_id"],
                        _aggregate_type = row["aggregate_type"],
                        _state = json.loads(row["state"]),
                        _version = row["version"],
                        _created_at = row["created_at"],
                        _metadata = json.loads(row["metadata"]) if row["metadata"] else None,
                    )
        else:
            return self._memory_snapshots.get(aggregate_id)
        
        return None
    
    def register_handler(self, _event_type: str, _handler: Callable[[DomainEvent], _None]) -> None:
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Callback function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Event handler registered for {event_type}")
    
    async def _notify_handlers(self, _event: DomainEvent) -> None:
        """Notify registered handlers."""
        _handlers = self._event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get event store statistics."""
        return {
            **self._stats,
            "initialized": self._initialized,
            "using_database": self._db_pool is not None,
            "memory_events": len(self._memory_events),
            "memory_snapshots": len(self._memory_snapshots),
        }


# Event sourcing helper functions

def create_event_applier(_state_field: str, _value_field: str) -> Callable[[Dict[str, Any], DomainEvent], Dict[str, Any]]:
    """
    Create a simple event applier function.
    
    Args:
        state_field: Field in state to update
        value_field: Field in event payload containing new value
        
    Returns:
        Applier function
    """
    def applier(_state: Dict[str, _Any], _event: DomainEvent) -> Dict[str, Any]:
        state[state_field] = event.payload.get(value_field)
        return state
    
    return applier


# Module singleton
_store: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """Get or create the event store singleton."""
    global _store
    if _store is None:
        _store = EventStore()
    return _store


async def setup_event_store(_db_pool: Optional[Any], _snapshot_interval: int) -> EventStore:
    """
    Setup and initialize event store.
    
    Args:
        db_pool: Optional asyncpg connection pool
        snapshot_interval: Create snapshot every N events
        
    Returns:
        Initialized EventStore
    """
    global _store
    _store = EventStore(db_pool=db_pool, snapshot_interval=snapshot_interval)
    await _store.initialize(db_pool)
    return _store
