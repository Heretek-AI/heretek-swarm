"""
State Snapshot Management.

Provides snapshot creation, management, and rollback capabilities
for the multi-agent system.
"""

import asyncio
import gzip
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

from .base import (
    StateSnapshot,
    StateDiff,
    AgentState,
    ConversationState,
    SystemState,
    StateStatus,
    TransitionType,
    StateTransition
)

logger = structlog.get_logger()


class SnapshotConfig(BaseModel):
    """Configuration for snapshot management"""
    
    # Storage
    storage_path: str = Field(default="/var/lib/heretek/snapshots")
    max_snapshots: int = Field(default=100, ge=1)
    max_snapshot_size_mb: int = Field(default=100, ge=1)
    
    # Retention
    default_retention_days: int = Field(default=30)
    auto_cleanup_enabled: bool = Field(default=True)
    
    # Scheduling
    auto_snapshot_interval_minutes: int = Field(default=60)
    auto_snapshot_enabled: bool = Field(default=True)
    
    # Performance
    compress_snapshots: bool = Field(default=True)
    batch_size: int = Field(default=50)
    
    # Rollback
    max_rollback_depth: int = Field(default=10, ge=1)


class SnapshotStore:
    """
    Storage backend for snapshots.
    
    Supports both file-based and database storage.
    """
    
    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.storage_path = Path(config.storage_path)
        self._ensure_storage()
    
    def _ensure_storage(self) -> None:
        """Ensure storage directory exists"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.storage_path / "full").mkdir(exist_ok=True)
        (self.storage_path / "incremental").mkdir(exist_ok=True)
        (self.storage_path / "temp").mkdir(exist_ok=True)
    
    def _get_snapshot_path(
        self,
        snapshot_id: UUID,
        snapshot_type: str = "full"
    ) -> Path:
        """Get path for snapshot file"""
        filename = f"{snapshot_id}.json"
        if self.config.compress_snapshots:
            filename += ".gz"
        
        return self.storage_path / snapshot_type / filename
    
    async def save(self, snapshot: StateSnapshot) -> int:
        """Save snapshot to storage"""
        path = self._get_snapshot_path(
            snapshot.snapshot_id,
            snapshot.snapshot_type
        )
        
        # Serialize
        data = snapshot.model_dump_json(indent=2)
        bytes_data = data.encode("utf-8")
        
        # Compress if enabled
        if self.config.compress_snapshots:
            bytes_data = gzip.compress(bytes_data)
        
        # Write atomically
        temp_path = self.storage_path / "temp" / f"{snapshot.snapshot_id}.tmp"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: temp_path.write_bytes(bytes_data)
        )
        
        # Atomic move
        await loop.run_in_executor(
            None,
            lambda: temp_path.rename(path)
        )
        
        return len(bytes_data)
    
    async def load(self, snapshot_id: UUID) -> Optional[StateSnapshot]:
        """Load snapshot from storage"""
        # Try full first, then incremental
        for snapshot_type in ["full", "incremental"]:
            path = self._get_snapshot_path(snapshot_id, snapshot_type)
            
            if path.exists():
                loop = asyncio.get_event_loop()
                bytes_data = await loop.run_in_executor(None, path.read_bytes)
                
                # Decompress if needed
                if self.config.compress_snapshots:
                    bytes_data = gzip.decompress(bytes_data)
                
                data = bytes_data.decode("utf-8")
                return StateSnapshot.model_validate_json(data)
        
        return None
    
    async def delete(self, snapshot_id: UUID) -> bool:
        """Delete snapshot from storage"""
        for snapshot_type in ["full", "incremental"]:
            path = self._get_snapshot_path(snapshot_id, snapshot_type)
            
            if path.exists():
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, path.unlink)
                return True
        
        return False
    
    async def list_snapshots(
        self,
        scope: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List available snapshots"""
        snapshots = []
        
        for snapshot_type in ["full", "incremental"]:
            type_path = self.storage_path / snapshot_type
            
            for path in type_path.glob("*.json*" if not self.config.compress_snapshots else "*.gz"):
                try:
                    # Parse snapshot ID from filename
                    snapshot_id_str = path.stem.replace(".json", "")
                    snapshot_id = UUID(snapshot_id_str)
                    
                    # Load just metadata (first few KB)
                    snapshot = await self.load(snapshot_id)
                    if snapshot:
                        if scope is None or snapshot.scope == scope:
                            snapshots.append({
                                "snapshot_id": str(snapshot.snapshot_id),
                                "snapshot_type": snapshot.snapshot_type,
                                "scope": snapshot.scope,
                                "created_at": snapshot.created_at.isoformat(),
                                "trigger": snapshot.trigger,
                                "size_bytes": snapshot.size_bytes,
                            })
                except Exception as e:
                    logger.warning(
                        "snapshot_list_error",
                        path=str(path),
                        error=str(e)
                    )
        
        # Sort by creation time
        snapshots.sort(key=lambda s: s["created_at"], reverse=True)
        
        return snapshots[:limit]


class SnapshotManager:
    """
    Manages state snapshots with creation, rollback, and diff capabilities.
    
    Features:
    - Full and incremental snapshots
    - Automatic snapshot scheduling
    - Rollback to any snapshot
    - Diff between snapshots
    - Compression and retention
    """
    
    def __init__(self, config: Optional[SnapshotConfig] = None):
        self.config = config or SnapshotConfig()
        self.store = SnapshotStore(self.config)
        
        # In-memory cache of recent snapshots
        self._cache: Dict[UUID, StateSnapshot] = {}
        self._cache_order: List[UUID] = []
        self._cache_size = 10
        
        # Index for quick lookups
        self._by_scope: Dict[str, List[UUID]] = {}
        self._by_time: List[Tuple[datetime, UUID]] = []
        
        # Background tasks
        self._auto_snapshot_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Metrics
        self._snapshots_created = 0
        self._snapshots_restored = 0
        self._total_size_bytes = 0
    
    async def initialize(self) -> None:
        """Initialize snapshot manager"""
        # Load existing snapshots into index
        snapshots = await self.store.list_snapshots(limit=1000)
        
        for meta in snapshots:
            snapshot_id = UUID(meta["snapshot_id"])
            
            # Add to time index
            created_at = datetime.fromisoformat(meta["created_at"])
            self._by_time.append((created_at, snapshot_id))
            
            # Add to scope index
            scope = meta["scope"]
            if scope not in self._by_scope:
                self._by_scope[scope] = []
            self._by_scope[scope].append(snapshot_id)
            
            self._total_size_bytes += meta["size_bytes"]
        
        # Sort time index
        self._by_time.sort(key=lambda x: x[0], reverse=True)
        
        # Start background tasks
        self._running = True
        
        if self.config.auto_snapshot_enabled:
            self._auto_snapshot_task = asyncio.create_task(
                self._auto_snapshot_loop()
            )
        
        if self.config.auto_cleanup_enabled:
            self._cleanup_task = asyncio.create_task(
                self._cleanup_loop()
            )
        
        logger.info(
            "snapshot_manager_initialized",
            existing_snapshots=len(snapshots),
            auto_snapshot=self.config.auto_snapshot_enabled,
            auto_cleanup=self.config.auto_cleanup_enabled
        )
    
    async def shutdown(self) -> None:
        """Shutdown snapshot manager"""
        self._running = False
        
        for task in [self._auto_snapshot_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("snapshot_manager_shutdown")
    
    def _cache_get(self, snapshot_id: UUID) -> Optional[StateSnapshot]:
        """Get from cache"""
        if snapshot_id in self._cache:
            # Update access order
            if snapshot_id in self._cache_order:
                self._cache_order.remove(snapshot_id)
            self._cache_order.append(snapshot_id)
            return self._cache[snapshot_id]
        return None
    
    def _cache_set(self, snapshot: StateSnapshot) -> None:
        """Set in cache with LRU eviction"""
        # Evict if at capacity
        while len(self._cache) >= self._cache_size and self._cache_order:
            oldest = self._cache_order.pop(0)
            del self._cache[oldest]
        
        self._cache[snapshot.snapshot_id] = snapshot
        self._cache_order.append(snapshot.snapshot_id)
    
    async def create_snapshot(
        self,
        system_state: Optional[SystemState] = None,
        agent_states: Optional[Dict[str, AgentState]] = None,
        conversation_states: Optional[Dict[str, ConversationState]] = None,
        message_lineage: Optional[Dict[str, Any]] = None,
        scope: str = "system",
        scope_ids: Optional[List[str]] = None,
        trigger: str = "manual",
        description: Optional[str] = None,
        snapshot_type: str = "full"
    ) -> StateSnapshot:
        """
        Create a new state snapshot.
        
        Args:
            system_state: Full system state
            agent_states: Agent states to include
            conversation_states: Conversation states to include
            message_lineage: Message lineage data
            scope: Scope of snapshot (system, agent, conversation)
            scope_ids: IDs within scope
            trigger: What triggered the snapshot
            description: Human-readable description
            snapshot_type: full or incremental
        
        Returns:
            The created snapshot
        """
        snapshot = StateSnapshot(
            snapshot_id=uuid4(),
            snapshot_type=snapshot_type,
            scope=scope,
            scope_ids=scope_ids or [],
            system_state=system_state,
            agent_states=agent_states or {},
            conversation_states=conversation_states or {},
            message_lineage=message_lineage or {},
            trigger=trigger,
            description=description
        )
        
        # Set parent to most recent snapshot of same scope
        if self._by_time:
            for created_at, recent_id in self._by_time:
                recent = await self.get_snapshot(recent_id)
                if recent and recent.scope == scope:
                    snapshot.parent_snapshot_id = recent.snapshot_id
                    break
        
        # Compute hash
        snapshot.state_hash = snapshot.compute_hash()
        
        # Set expiration
        snapshot.expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.config.default_retention_days
        )
        
        # Save to store
        size_bytes = await self.store.save(snapshot)
        snapshot.size_bytes = size_bytes
        self._total_size_bytes += size_bytes
        
        # Update indices
        self._by_time.insert(0, (snapshot.created_at, snapshot.snapshot_id))
        
        if scope not in self._by_scope:
            self._by_scope[scope] = []
        self._by_scope[scope].append(snapshot.snapshot_id)
        
        # Cache
        self._cache_set(snapshot)
        
        self._snapshots_created += 1
        
        logger.info(
            "snapshot_created",
            snapshot_id=str(snapshot.snapshot_id),
            scope=scope,
            trigger=trigger,
            size_bytes=size_bytes
        )
        
        return snapshot
    
    async def get_snapshot(self, snapshot_id: UUID) -> Optional[StateSnapshot]:
        """Get a snapshot by ID"""
        # Check cache
        cached = self._cache_get(snapshot_id)
        if cached:
            return cached
        
        # Load from store
        snapshot = await self.store.load(snapshot_id)
        if snapshot:
            self._cache_set(snapshot)
        
        return snapshot
    
    async def get_latest_snapshot(
        self,
        scope: str = "system"
    ) -> Optional[StateSnapshot]:
        """Get the most recent snapshot for a scope"""
        for created_at, snapshot_id in self._by_time:
            snapshot = await self.get_snapshot(snapshot_id)
            if snapshot and snapshot.scope == scope:
                return snapshot
        
        return None
    
    async def list_snapshots(
        self,
        scope: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List available snapshots"""
        return await self.store.list_snapshots(scope, limit)
    
    async def delete_snapshot(self, snapshot_id: UUID) -> bool:
        """Delete a snapshot"""
        # Remove from indices
        self._by_time = [
            (t, sid) for t, sid in self._by_time
            if sid != snapshot_id
        ]
        
        for scope in self._by_scope:
            self._by_scope[scope] = [
                sid for sid in self._by_scope[scope]
                if sid != snapshot_id
            ]
        
        # Remove from cache
        self._cache.pop(snapshot_id, None)
        if snapshot_id in self._cache_order:
            self._cache_order.remove(snapshot_id)
        
        # Delete from store
        deleted = await self.store.delete(snapshot_id)
        
        if deleted:
            logger.info("snapshot_deleted", snapshot_id=str(snapshot_id))
        
        return deleted
    
    async def compute_diff(
        self,
        from_snapshot_id: UUID,
        to_snapshot_id: UUID
    ) -> Optional[StateDiff]:
        """
        Compute diff between two snapshots.
        
        Returns the changes needed to go from from_snapshot to to_snapshot.
        """
        from_snapshot = await self.get_snapshot(from_snapshot_id)
        to_snapshot = await self.get_snapshot(to_snapshot_id)
        
        if not from_snapshot or not to_snapshot:
            return None
        
        diff = StateDiff(
            from_snapshot_id=from_snapshot_id,
            to_snapshot_id=to_snapshot_id
        )
        
        # Diff agent states
        all_agent_ids = set(from_snapshot.agent_states.keys()) | set(
            to_snapshot.agent_states.keys()
        )
        
        for agent_id in all_agent_ids:
            from_agent = from_snapshot.agent_states.get(agent_id)
            to_agent = to_snapshot.agent_states.get(agent_id)
            
            if from_agent is None and to_agent:
                # Added
                diff.added_agents[agent_id] = to_agent
            elif from_agent and to_agent is None:
                # Removed
                diff.removed_agents.add(agent_id)
            elif from_agent and to_agent:
                # Check if modified
                if from_agent.compute_hash() != to_agent.compute_hash():
                    # Store just the changes
                    diff.modified_agents[agent_id] = {
                        "from": from_agent.model_dump(),
                        "to": to_agent.model_dump()
                    }
        
        # Diff conversation states
        all_conv_ids = set(from_snapshot.conversation_states.keys()) | set(
            to_snapshot.conversation_states.keys()
        )
        
        for conv_id in all_conv_ids:
            from_conv = from_snapshot.conversation_states.get(conv_id)
            to_conv = to_snapshot.conversation_states.get(conv_id)
            
            if from_conv is None and to_conv:
                diff.added_conversations[conv_id] = to_conv
            elif from_conv and to_conv is None:
                diff.removed_conversations.add(conv_id)
            elif from_conv and to_conv:
                if from_conv.version != to_conv.version:
                    diff.modified_conversations[conv_id] = {
                        "from_version": from_conv.version,
                        "to_version": to_conv.version
                    }
        
        # Added messages
        for msg_id, lineage in to_snapshot.message_lineage.items():
            if msg_id not in from_snapshot.message_lineage:
                diff.added_messages[msg_id] = lineage
        
        # Compute size
        diff.size_bytes = len(diff.model_dump_json().encode())
        
        return diff
    
    async def apply_diff(
        self,
        from_snapshot_id: UUID,
        diff: StateDiff
    ) -> Optional[StateSnapshot]:
        """
        Apply a diff to create a new snapshot.
        
        This is used for incremental snapshot restoration.
        """
        from_snapshot = await self.get_snapshot(from_snapshot_id)
        
        if not from_snapshot:
            return None
        
        # Start with from snapshot
        new_agent_states = dict(from_snapshot.agent_states)
        new_conv_states = dict(from_snapshot.conversation_states)
        new_message_lineage = dict(from_snapshot.message_lineage)
        
        # Apply additions
        for agent_id, agent_state in diff.added_agents.items():
            new_agent_states[agent_id] = agent_state
        
        for conv_id, conv_state in diff.added_conversations.items():
            new_conv_states[conv_id] = conv_state
        
        for msg_id, lineage in diff.added_messages.items():
            new_message_lineage[msg_id] = lineage
        
        # Apply modifications
        for agent_id, changes in diff.modified_agents.items():
            new_agent_states[agent_id] = AgentState(**changes["to"])
        
        for conv_id, changes in diff.modified_conversations.items():
            if conv_id in new_conv_states:
                new_conv_states[conv_id].version = changes["to_version"]
        
        # Apply removals
        for agent_id in diff.removed_agents:
            new_agent_states.pop(agent_id, None)
        
        for conv_id in diff.removed_conversations:
            new_conv_states.pop(conv_id, None)
        
        # Create new snapshot
        return await self.create_snapshot(
            system_state=from_snapshot.system_state,
            agent_states=new_agent_states,
            conversation_states=new_conv_states,
            message_lineage=new_message_lineage,
            scope=from_snapshot.scope,
            trigger=f"diff_from_{from_snapshot_id}"
        )
    
    async def _auto_snapshot_loop(self) -> None:
        """Background task for automatic snapshots"""
        while self._running:
            try:
                await asyncio.sleep(
                    self.config.auto_snapshot_interval_minutes * 60
                )
                
                # Create automatic snapshot
                await self.create_snapshot(
                    trigger="auto",
                    description="Automatic scheduled snapshot"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("auto_snapshot_failed", error=str(e))
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up old snapshots"""
        while self._running:
            try:
                # Run cleanup daily
                await asyncio.sleep(86400)
                
                cutoff = datetime.now(timezone.utc) - timedelta(
                    days=self.config.default_retention_days
                )
                
                # Find expired snapshots
                to_delete = []
                for created_at, snapshot_id in self._by_time:
                    if created_at < cutoff:
                        to_delete.append(snapshot_id)
                
                # Delete expired
                for snapshot_id in to_delete:
                    await self.delete_snapshot(snapshot_id)
                
                # Enforce max snapshots limit
                while len(self._by_time) > self.config.max_snapshots:
                    oldest_id = self._by_time[-1][1]
                    await self.delete_snapshot(oldest_id)
                
                logger.info(
                    "snapshot_cleanup_completed",
                    deleted_count=len(to_delete)
                )
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("snapshot_cleanup_failed", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get snapshot statistics"""
        return {
            "snapshots_created": self._snapshots_created,
            "snapshots_restored": self._snapshots_restored,
            "current_snapshots": len(self._by_time),
            "total_size_bytes": self._total_size_bytes,
            "total_size_mb": self._total_size_bytes / (1024 * 1024),
            "cache_size": len(self._cache),
            "by_scope": {
                scope: len(ids)
                for scope, ids in self._by_scope.items()
            }
        }
