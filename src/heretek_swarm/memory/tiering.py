"""
Memory Tiering System for Heretek Swarm

This module provides multi-tier storage management:
- Multi-tier storage (L1: Redis, L2: PostgreSQL, L3: Compressed Archive)
- Automatic tier migration based on access patterns
- Tier configuration and tuning
- Migration audit logging

Reference: EXPANSION_ROADMAP.md Session 43 - Memory Optimization
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Memory Tier Types and Enums
# =============================================================================

class MemoryTier(str, Enum):
    """Memory storage tiers."""
    L1_HOT = "l1_hot"           # Redis - fastest, most expensive
    L2_WARM = "l2_warm"         # PostgreSQL - balanced
    L3_COLD = "l3_cold"         # Compressed archive - slowest, cheapest
    ARCHIVE = "archive"         # Deep archive - very slow, minimal cost


class TierMigrationStatus(str, Enum):
    """Status of tier migration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationTrigger(str, Enum):
    """Triggers for tier migration."""
    ACCESS_PATTERN = "access_pattern"     # Based on access frequency/recency
    POLICY = "policy"                     # Based on policy rules
    MANUAL = "manual"                     # Manual migration
    SCHEDULED = "scheduled"               # Scheduled maintenance
    CAPACITY = "capacity"                 # Capacity management
    COST_OPTIMIZATION = "cost_optimization"  # Cost-driven migration


@dataclass
class TierConfig:
    """
    Configuration for a memory tier.
    
    Attributes:
        tier: Tier identifier
        name: Human-readable name
        description: Tier description
        max_capacity_bytes: Maximum capacity in bytes
        max_capacity_count: Maximum number of entries
        target_utilization: Target utilization (0-1)
        cost_per_gb_month: Cost per GB per month
        access_latency_ms: Expected access latency
        retention_days: Data retention period
        compression_enabled: Whether compression is enabled
        auto_migrate_enabled: Enable automatic migration
    """
    tier: MemoryTier
    name: str
    description: str
    max_capacity_bytes: int = 0  # 0 = unlimited
    max_capacity_count: int = 0  # 0 = unlimited
    target_utilization: float = 0.8
    cost_per_gb_month: float = 0.0
    access_latency_ms: float = 0.0
    retention_days: int = 0  # 0 = forever
    compression_enabled: bool = False
    auto_migrate_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tier": self.tier.value,
            "name": self.name,
            "description": self.description,
            "capacity": {
                "max_bytes": self.max_capacity_bytes,
                "max_count": self.max_capacity_count,
                "target_utilization": self.target_utilization,
            },
            "performance": {
                "cost_per_gb_month": self.cost_per_gb_month,
                "access_latency_ms": self.access_latency_ms,
            },
            "retention_days": self.retention_days,
            "compression_enabled": self.compression_enabled,
            "auto_migrate_enabled": self.auto_migrate_enabled,
        }


@dataclass
class TieredMemory:
    """
    Memory entry with tier information.
    
    Attributes:
        memory_id: Memory identifier
        current_tier: Current storage tier
        data: Memory data (may be compressed)
        metadata: Memory metadata
        created_at: Creation timestamp
        last_accessed: Last access timestamp
        access_count: Total access count
        tier_history: History of tier migrations
        size_bytes: Data size in bytes
        compressed: Whether data is compressed
        compression_ratio: Compression ratio if compressed
    """
    memory_id: str
    current_tier: MemoryTier
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    access_count: int = 0
    tier_history: List[Dict[str, Any]] = field(default_factory=list)
    size_bytes: int = 0
    compressed: bool = False
    compression_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "current_tier": self.current_tier.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "size_bytes": self.size_bytes,
            "compressed": self.compressed,
            "compression_ratio": self.compression_ratio,
            "tier_history": self.tier_history,
        }


@dataclass
class MigrationRecord:
    """
    Record of a tier migration.
    
    Attributes:
        memory_id: Memory identifier
        from_tier: Source tier
        to_tier: Destination tier
        status: Migration status
        trigger: What triggered the migration
        reason: Migration reason
        started_at: Migration start timestamp
        completed_at: Migration completion timestamp
        latency_ms: Migration latency
        error: Error message if failed
        rolled_back: Whether migration was rolled back
        audit_metadata: Additional audit information
    """
    memory_id: str
    from_tier: MemoryTier
    to_tier: MemoryTier
    status: TierMigrationStatus = TierMigrationStatus.PENDING
    trigger: MigrationTrigger = MigrationTrigger.ACCESS_PATTERN
    reason: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    latency_ms: float = 0.0
    error: Optional[str] = None
    rolled_back: bool = False
    audit_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "from_tier": self.from_tier.value,
            "to_tier": self.to_tier.value,
            "status": self.status.value,
            "trigger": self.trigger.value,
            "reason": self.reason,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "rolled_back": self.rolled_back,
            "audit_metadata": self.audit_metadata,
        }


@dataclass
class MigrationPolicy:
    """
    Policy for automatic tier migration.
    
    Attributes:
        name: Policy name
        description: Policy description
        enabled: Whether policy is enabled
        conditions: Conditions for migration
        actions: Actions to take
        priority: Policy priority (higher = evaluated first)
    """
    name: str
    description: str = ""
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "conditions": self.conditions,
            "actions": self.actions,
            "priority": self.priority,
        }


@dataclass
class TieringStatistics:
    """
    Overall tiering statistics.
    
    Attributes:
        total_memories: Total number of memories
        memories_per_tier: Count per tier
        bytes_per_tier: Bytes stored per tier
        migrations_total: Total migrations
        migrations_successful: Successful migrations
        migrations_failed: Failed migrations
        avg_migration_latency_ms: Average migration latency
        cost_estimate_monthly: Estimated monthly cost
        storage_efficiency: Overall storage efficiency
    """
    total_memories: int = 0
    memories_per_tier: Dict[str, int] = field(default_factory=dict)
    bytes_per_tier: Dict[str, int] = field(default_factory=dict)
    migrations_total: int = 0
    migrations_successful: int = 0
    migrations_failed: int = 0
    avg_migration_latency_ms: float = 0.0
    cost_estimate_monthly: float = 0.0
    storage_efficiency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_memories": self.total_memories,
            "memories_per_tier": self.memories_per_tier,
            "bytes_per_tier": self.bytes_per_tier,
            "migrations": {
                "total": self.migrations_total,
                "successful": self.migrations_successful,
                "failed": self.migrations_failed,
                "avg_latency_ms": self.avg_migration_latency_ms,
            },
            "cost_estimate_monthly": self.cost_estimate_monthly,
            "storage_efficiency": self.storage_efficiency,
        }


# =============================================================================
# Default Tier Configurations
# =============================================================================

DEFAULT_TIER_CONFIGS = {
    MemoryTier.L1_HOT: TierConfig(
        tier=MemoryTier.L1_HOT,
        name="Hot Storage (Redis)",
        description="Fastest tier for frequently accessed memories",
        max_capacity_bytes=10 * 1024 * 1024 * 1024,  # 10GB
        max_capacity_count=100000,
        target_utilization=0.7,
        cost_per_gb_month=0.50,
        access_latency_ms=1.0,
        retention_days=30,
        compression_enabled=False,
        auto_migrate_enabled=True,
    ),
    MemoryTier.L2_WARM: TierConfig(
        tier=MemoryTier.L2_WARM,
        name="Warm Storage (PostgreSQL)",
        description="Balanced tier for moderately accessed memories",
        max_capacity_bytes=100 * 1024 * 1024 * 1024,  # 100GB
        max_capacity_count=1000000,
        target_utilization=0.8,
        cost_per_gb_month=0.10,
        access_latency_ms=10.0,
        retention_days=365,
        compression_enabled=False,
        auto_migrate_enabled=True,
    ),
    MemoryTier.L3_COLD: TierConfig(
        tier=MemoryTier.L3_COLD,
        name="Cold Storage (Compressed Archive)",
        description="Low-cost tier for rarely accessed memories",
        max_capacity_bytes=1000 * 1024 * 1024 * 1024,  # 1TB
        max_capacity_count=10000000,
        target_utilization=0.9,
        cost_per_gb_month=0.02,
        access_latency_ms=100.0,
        retention_days=730,  # 2 years
        compression_enabled=True,
        auto_migrate_enabled=True,
    ),
    MemoryTier.ARCHIVE: TierConfig(
        tier=MemoryTier.ARCHIVE,
        name="Archive Storage",
        description="Deep archive for compliance and long-term retention",
        max_capacity_bytes=0,  # Unlimited
        max_capacity_count=0,
        target_utilization=1.0,
        cost_per_gb_month=0.004,
        access_latency_ms=1000.0,
        retention_days=0,  # Forever
        compression_enabled=True,
        auto_migrate_enabled=False,
    ),
}


# =============================================================================
# Memory Tiering System
# =============================================================================

class MemoryTieringSystem:
    """
    Memory Tiering System for Multi-Tier Storage
    
    Manages automatic tier migration based on access patterns:
    - Multi-tier storage (L1: Redis, L2: PostgreSQL, L3: Compressed Archive)
    - Automatic tier migration based on access patterns
    - Tier configuration and tuning
    - Migration audit logging
    
    Features:
    - Configurable tier policies
    - Automatic migration scheduling
    - Cost optimization
    - Complete audit trail
    """
    
    # Migration thresholds
    HOT_TO_WARM_RECENCY_THRESHOLD = 0.3  # Recency score below this triggers demotion
    WARM_TO_COLD_RECENCY_THRESHOLD = 0.1
    COLD_TO_WARM_FREQUENCY_THRESHOLD = 0.6  # Frequency score above this triggers promotion
    WARM_TO_HOT_FREQUENCY_THRESHOLD = 0.8
    
    def __init__(
        self,
        tier_configs: Optional[Dict[MemoryTier, TierConfig]] = None,
        enable_auto_migration: bool = True,
    ) -> None:
        """
        Initialize the memory tiering system.
        
        Args:
            tier_configs: Tier configurations (uses defaults if None)
            enable_auto_migration: Enable automatic migration
        """
        self.tier_configs = tier_configs or DEFAULT_TIER_CONFIGS.copy()
        self.enable_auto_migration = enable_auto_migration
        
        # Memory storage by tier
        self._memories_by_tier: Dict[MemoryTier, Dict[str, TieredMemory]] = {
            tier: {} for tier in MemoryTier
        }
        
        # Migration tracking
        self._migration_history: List[MigrationRecord] = []
        self._pending_migrations: List[MigrationRecord] = []
        self._max_history_size = 10000
        
        # Migration policies
        self._policies: List[MigrationPolicy] = self._create_default_policies()
        
        # Statistics
        self._total_migrations = 0
        self._successful_migrations = 0
        self._failed_migrations = 0
        self._total_migration_latency_ms = 0.0
        
        # Background migration task
        self._migration_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(
            "memory_tiering_system_initialized",
            tiers=[t.value for t in self.tier_configs.keys()],
            auto_migration=enable_auto_migration,
        )
    
    def _create_default_policies(self) -> List[MigrationPolicy]:
        """Create default migration policies."""
        return [
            MigrationPolicy(
                name="hot_to_warm_demotion",
                description="Demote hot memories with low recency to warm tier",
                enabled=True,
                conditions={
                    "current_tier": MemoryTier.L1_HOT.value,
                    "recency_score_below": self.HOT_TO_WARM_RECENCY_THRESHOLD,
                },
                actions={
                    "target_tier": MemoryTier.L2_WARM.value,
                },
                priority=100,
            ),
            MigrationPolicy(
                name="warm_to_cold_demotion",
                description="Demote warm memories with very low recency to cold tier",
                enabled=True,
                conditions={
                    "current_tier": MemoryTier.L2_WARM.value,
                    "recency_score_below": self.WARM_TO_COLD_RECENCY_THRESHOLD,
                },
                actions={
                    "target_tier": MemoryTier.L3_COLD.value,
                },
                priority=90,
            ),
            MigrationPolicy(
                name="cold_to_warm_promotion",
                description="Promote cold memories with high frequency to warm tier",
                enabled=True,
                conditions={
                    "current_tier": MemoryTier.L3_COLD.value,
                    "frequency_score_above": self.COLD_TO_WARM_FREQUENCY_THRESHOLD,
                },
                actions={
                    "target_tier": MemoryTier.L2_WARM.value,
                },
                priority=80,
            ),
            MigrationPolicy(
                name="warm_to_hot_promotion",
                description="Promote warm memories with very high frequency to hot tier",
                enabled=True,
                conditions={
                    "current_tier": MemoryTier.L2_WARM.value,
                    "frequency_score_above": self.WARM_TO_HOT_FREQUENCY_THRESHOLD,
                },
                actions={
                    "target_tier": MemoryTier.L1_HOT.value,
                },
                priority=70,
            ),
        ]
    
    async def start(self) -> None:
        """Start the tiering system background processes."""
        if self.enable_auto_migration and not self._running:
            self._running = True
            self._migration_task = asyncio.create_task(self._run_migration_loop())
            logger.info("memory_tiering_system_started")
    
    async def stop(self) -> None:
        """Stop the tiering system background processes."""
        self._running = False
        if self._migration_task:
            self._migration_task.cancel()
            try:
                await self._migration_task
            except asyncio.CancelledError:
                pass
        logger.info("memory_tiering_system_stopped")
    
    async def _run_migration_loop(self) -> None:
        """Background migration loop."""
        while self._running:
            try:
                await self._evaluate_and_migrate()
                await asyncio.sleep(60.0)  # Evaluate every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("tiering_migration_loop_error", error=str(e))
                await asyncio.sleep(60.0)
    
    async def _evaluate_and_migrate(self) -> int:
        """Evaluate memories for migration and execute migrations."""
        migrated_count = 0
        
        for policy in self._policies:
            if not policy.enabled:
                continue
            
            candidates = self._find_migration_candidates(policy)
            
            for memory in candidates:
                result = await self._migrate_memory(
                    memory=memory,
                    target_tier=MemoryTier(policy.actions["target_tier"]),
                    trigger=MigrationTrigger.ACCESS_PATTERN,
                    reason=f"Policy: {policy.name}",
                )
                
                if result.status == TierMigrationStatus.COMPLETED:
                    migrated_count += 1
        
        return migrated_count
    
    def _find_migration_candidates(
        self,
        policy: MigrationPolicy,
    ) -> List[TieredMemory]:
        """Find memories matching migration policy conditions."""
        candidates = []
        current_tier = MemoryTier(policy.conditions.get("current_tier", ""))
        
        if current_tier not in self._memories_by_tier:
            return candidates
        
        for memory in self._memories_by_tier[current_tier].values():
            if self._matches_policy(memory, policy):
                candidates.append(memory)
        
        return candidates
    
    def _matches_policy(
        self,
        memory: TieredMemory,
        policy: MigrationPolicy,
    ) -> bool:
        """Check if a memory matches policy conditions."""
        conditions = policy.conditions
        
        # Check recency threshold
        if "recency_score_below" in conditions:
            threshold = conditions["recency_score_below"]
            recency = self._calculate_recency_score(memory)
            if recency >= threshold:
                return False
        
        # Check frequency threshold
        if "frequency_score_above" in conditions:
            threshold = conditions["frequency_score_above"]
            frequency = self._calculate_frequency_score(memory)
            if frequency <= threshold:
                return False
        
        return True
    
    def _calculate_recency_score(self, memory: TieredMemory) -> float:
        """Calculate recency score for a memory."""
        try:
            last_access = datetime.fromisoformat(memory.last_accessed)
            now = datetime.now(timezone.utc)
            age_hours = (now - last_access).total_seconds() / 3600
            
            # Exponential decay with 24-hour half-life
            import math
            return math.exp(-math.log(2) * age_hours / 24)
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_frequency_score(self, memory: TieredMemory) -> float:
        """Calculate frequency score for a memory."""
        try:
            created = datetime.fromisoformat(memory.created_at)
            now = datetime.now(timezone.utc)
            age_hours = max((now - created).total_seconds() / 3600, 1)
            
            # Normalize access count by age
            import math
            accesses_per_hour = memory.access_count / age_hours
            
            # Logarithmic scaling
            return min(1.0, math.log(accesses_per_hour + 1) / math.log(100))
        except (ValueError, TypeError):
            return 0.0
    
    def store(
        self,
        memory_id: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        target_tier: Optional[MemoryTier] = None,
        size_bytes: int = 0,
    ) -> TieredMemory:
        """
        Store a memory in the appropriate tier.
        
        Args:
            memory_id: Memory identifier
            data: Memory data
            metadata: Memory metadata
            target_tier: Explicit target tier (optional)
            size_bytes: Data size in bytes
            
        Returns:
            Stored tiered memory
        """
        # Determine target tier
        if target_tier is None:
            target_tier = self._determine_initial_tier(data, metadata)
        
        # Create tiered memory
        memory = TieredMemory(
            memory_id=memory_id,
            current_tier=target_tier,
            data=data,
            metadata=metadata or {},
            size_bytes=size_bytes or len(str(data)),
            tier_history=[{
                "action": "created",
                "tier": target_tier.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        )
        
        # Store in tier
        self._memories_by_tier[target_tier][memory_id] = memory
        
        logger.debug(
            "memory_stored",
            memory_id=memory_id,
            tier=target_tier.value,
        )
        
        return memory
    
    def _determine_initial_tier(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]],
    ) -> MemoryTier:
        """Determine initial tier for new memory."""
        # Check metadata for explicit tier hint
        if metadata:
            tier_hint = metadata.get("tier_hint")
            if tier_hint:
                try:
                    return MemoryTier(tier_hint)
                except ValueError:
                    pass
            
            # Check importance/priority
            importance = metadata.get("importance", 0)
            if importance >= 0.8:
                return MemoryTier.L1_HOT
            elif importance >= 0.5:
                return MemoryTier.L2_WARM
        
        # Default to warm tier for new memories
        return MemoryTier.L2_WARM
    
    async def _migrate_memory(
        self,
        memory: TieredMemory,
        target_tier: MemoryTier,
        trigger: MigrationTrigger = MigrationTrigger.ACCESS_PATTERN,
        reason: str = "",
    ) -> MigrationRecord:
        """
        Migrate a memory to a different tier.
        
        Args:
            memory: Memory to migrate
            target_tier: Destination tier
            trigger: Migration trigger
            reason: Migration reason
            
        Returns:
            Migration record
        """
        start_time = time.time()
        
        record = MigrationRecord(
            memory_id=memory.memory_id,
            from_tier=memory.current_tier,
            to_tier=target_tier,
            status=TierMigrationStatus.IN_PROGRESS,
            trigger=trigger,
            reason=reason,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        
        try:
            # Remove from source tier
            source_tier = memory.current_tier
            if memory.memory_id in self._memories_by_tier[source_tier]:
                del self._memories_by_tier[source_tier][memory.memory_id]
            
            # Update memory tier
            memory.current_tier = target_tier
            memory.tier_history.append({
                "action": "migrated",
                "from_tier": source_tier.value,
                "to_tier": target_tier.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trigger": trigger.value,
                "reason": reason,
            })
            
            # Add to target tier
            self._memories_by_tier[target_tier][memory.memory_id] = memory
            
            # Complete migration
            latency_ms = (time.time() - start_time) * 1000
            record.status = TierMigrationStatus.COMPLETED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            record.latency_ms = latency_ms
            
            # Update statistics
            self._total_migrations += 1
            self._successful_migrations += 1
            self._total_migration_latency_ms += latency_ms
            
            # Add to history
            self._add_to_history(record)
            
            logger.info(
                "memory_migrated",
                memory_id=memory.memory_id,
                from_tier=source_tier.value,
                to_tier=target_tier.value,
                latency_ms=latency_ms,
            )
            
        except Exception as e:
            record.status = TierMigrationStatus.FAILED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            record.error = str(e)
            
            self._total_migrations += 1
            self._failed_migrations += 1
            
            self._add_to_history(record)
            
            logger.error(
                "memory_migration_failed",
                memory_id=memory.memory_id,
                error=str(e),
            )
        
        return record
    
    def _add_to_history(self, record: MigrationRecord) -> None:
        """Add migration record to history."""
        self._migration_history.append(record)
        
        # Limit history size
        if len(self._migration_history) > self._max_history_size:
            self._migration_history = self._migration_history[-self._max_history_size:]
    
    def get_memory(self, memory_id: str) -> Optional[TieredMemory]:
        """Get a memory by ID from any tier."""
        for tier_memories in self._memories_by_tier.values():
            if memory_id in tier_memories:
                memory = tier_memories[memory_id]
                memory.access_count += 1
                memory.last_accessed = datetime.now(timezone.utc).isoformat()
                return memory
        return None
    
    def get_memories_by_tier(self, tier: MemoryTier) -> List[TieredMemory]:
        """Get all memories in a specific tier."""
        return list(self._memories_by_tier.get(tier, {}).values())
    
    def remove_memory(self, memory_id: str) -> bool:
        """Remove a memory from any tier."""
        for tier_memories in self._memories_by_tier.values():
            if memory_id in tier_memories:
                del tier_memories[memory_id]
                logger.debug("memory_removed", memory_id=memory_id)
                return True
        return False
    
    def get_statistics(self) -> TieringStatistics:
        """Get comprehensive tiering statistics."""
        memories_per_tier = {}
        bytes_per_tier = {}
        
        for tier, memories in self._memories_by_tier.items():
            memories_per_tier[tier.value] = len(memories)
            bytes_per_tier[tier.value] = sum(m.size_bytes for m in memories.values())
        
        total_memories = sum(memories_per_tier.values())
        total_bytes = sum(bytes_per_tier.values())
        
        # Calculate cost estimate
        cost_estimate = 0.0
        for tier, byte_count in bytes_per_tier.items():
            tier_config = self.tier_configs.get(MemoryTier(tier))
            if tier_config:
                gb_count = byte_count / (1024 ** 3)
                cost_estimate += gb_count * tier_config.cost_per_gb_month
        
        # Calculate storage efficiency
        storage_efficiency = 1.0 if total_bytes == 0 else (
            bytes_per_tier.get(MemoryTier.L3_COLD.value, 0) +
            bytes_per_tier.get(MemoryTier.ARCHIVE.value, 0)
        ) / total_bytes
        
        avg_latency = (
            self._total_migration_latency_ms / self._total_migrations
            if self._total_migrations > 0 else 0.0
        )
        
        return TieringStatistics(
            total_memories=total_memories,
            memories_per_tier=memories_per_tier,
            bytes_per_tier=bytes_per_tier,
            migrations_total=self._total_migrations,
            migrations_successful=self._successful_migrations,
            migrations_failed=self._failed_migrations,
            avg_migration_latency_ms=avg_latency,
            cost_estimate_monthly=cost_estimate,
            storage_efficiency=storage_efficiency,
        )
    
    def get_migration_history(
        self,
        limit: int = 100,
        memory_id: Optional[str] = None,
    ) -> List[MigrationRecord]:
        """Get migration history."""
        history = self._migration_history
        
        if memory_id:
            history = [r for r in history if r.memory_id == memory_id]
        
        return history[-limit:]
    
    def get_pending_migrations(self) -> List[MigrationRecord]:
        """Get pending migrations."""
        return self._pending_migrations
    
    def add_policy(self, policy: MigrationPolicy) -> None:
        """Add a migration policy."""
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority, reverse=True)
        logger.info("migration_policy_added", name=policy.name)
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove a migration policy by name."""
        for i, policy in enumerate(self._policies):
            if policy.name == policy_name:
                del self._policies[i]
                logger.info("migration_policy_removed", name=policy_name)
                return True
        return False
    
    def get_policies(self) -> List[MigrationPolicy]:
        """Get all migration policies."""
        return self._policies.copy()
    
    def get_tier_config(self, tier: MemoryTier) -> Optional[TierConfig]:
        """Get configuration for a tier."""
        return self.tier_configs.get(tier)
    
    def update_tier_config(
        self,
        tier: MemoryTier,
        **kwargs: Any,
    ) -> bool:
        """Update configuration for a tier."""
        if tier not in self.tier_configs:
            return False
        
        config = self.tier_configs[tier]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        logger.info("tier_config_updated", tier=tier.value, changes=kwargs)
        return True
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive tiering report."""
        stats = self.get_statistics()
        
        # Tier utilization
        tier_utilization = {}
        for tier, memories in self._memories_by_tier.items():
            config = self.tier_configs.get(tier)
            if config:
                count_util = len(memories) / config.max_capacity_count if config.max_capacity_count > 0 else 0
                tier_utilization[tier.value] = {
                    "count": len(memories),
                    "count_utilization": count_util,
                    "bytes": sum(m.size_bytes for m in memories.values()),
                }
        
        # Recent migrations
        recent_migrations = [
            r.to_dict() for r in self._migration_history[-50:]
        ]
        
        # Policy effectiveness
        policy_stats = []
        for policy in self._policies:
            matching_migrations = sum(
                1 for r in self._migration_history
                if r.trigger == MigrationTrigger.ACCESS_PATTERN and policy.name in r.reason
            )
            policy_stats.append({
                "name": policy.name,
                "enabled": policy.enabled,
                "migrations_triggered": matching_migrations,
            })
        
        return {
            "statistics": stats.to_dict(),
            "tier_utilization": tier_utilization,
            "recent_migrations": recent_migrations,
            "policy_effectiveness": policy_stats,
            "recommendations": self._generate_recommendations(stats),
        }
    
    def _generate_recommendations(
        self,
        stats: TieringStatistics,
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Check L1 hot tier utilization
        l1_count = stats.memories_per_tier.get(MemoryTier.L1_HOT.value, 0)
        l1_config = self.tier_configs.get(MemoryTier.L1_HOT)
        if l1_config and l1_count > l1_config.max_capacity_count * 0.9:
            recommendations.append(
                f"L1 hot tier is at {l1_count / l1_config.max_capacity_count:.1%} capacity. "
                "Consider demoting memories to warm tier."
            )
        
        # Check storage efficiency
        if stats.storage_efficiency < 0.3:
            recommendations.append(
                "Low storage efficiency. Consider more aggressive cold tier migration."
            )
        
        # Check migration failure rate
        if stats.migrations_total > 0:
            failure_rate = stats.migrations_failed / stats.migrations_total
            if failure_rate > 0.1:
                recommendations.append(
                    f"High migration failure rate ({failure_rate:.1%}). "
                    "Review migration policies and system health."
                )
        
        # Check cost
        if stats.cost_estimate_monthly > 100:
            recommendations.append(
                f"Monthly storage cost is ${stats.cost_estimate_monthly:.2f}. "
                "Consider optimizing tier distribution for cost reduction."
            )
        
        return recommendations
    
    def clear(self) -> None:
        """Clear all tiered memories and history."""
        for tier in self._memories_by_tier:
            self._memories_by_tier[tier].clear()
        self._migration_history.clear()
        self._pending_migrations.clear()
        logger.info("memory_tiering_system_cleared")
