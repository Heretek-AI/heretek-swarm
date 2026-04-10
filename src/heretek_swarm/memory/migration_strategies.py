"""
Memory Migration Strategies for Tiered Memory System

Provides strategy classes for different migration phases.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import structlog

_logger = structlog.get_logger(__name__)


class MigrationPhase(ABC):
    """Abstract base class for migration phases"""
    
    @abstractmethod
    async def execute(self, _memory: Any, _source_tier: Any, _target_tier: Any, _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Execute the phase"""
        pass


class MigrationValidationPhase(MigrationPhase):
    """Phase 1: Validate migration is possible"""
    
    async def execute(self, _memory: Any, _source_tier: Any, _target_tier: Any, _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Validate migration parameters"""
        if target_tier == source_tier:
            return False, f"Cannot migrate to same tier: {source_tier.value}", {}
        
        if source_tier not in memories_by_tier:
            return False, f"Source tier {source_tier.value} not found", {}
        
        if target_tier not in memories_by_tier:
            return False, f"Target tier {target_tier.value} not found", {}
        
        if memory.memory_id not in memories_by_tier.get(source_tier, {}):
            return False, f"Memory {memory.memory_id} not found in source tier", {}
        
        return True, None, {}


class MigrationRemovalPhase(MigrationPhase):
    """Phase 2: Remove from source tier"""
    
    async def execute(self, _memory: Any, _source_tier: Any, _target_tier: Any, _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Remove memory from source tier"""
        if memory.memory_id in memories_by_tier.get(source_tier, {}):
            del memories_by_tier[source_tier][memory.memory_id]
        
        return True, None, {"removed_from_source": True}


class MigrationUpdatePhase(MigrationPhase):
    """Phase 3: Update memory tier and metadata"""
    
    async def execute(self, _memory: Any, _source_tier: Any, _target_tier: Any, _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Update memory with new tier"""
        memory.current_tier = target_tier
        
        _migration_entry = {
            "action": "migrated",
            "from_tier": source_tier.value,
            "to_tier": target_tier.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        memory.tier_history.append(migration_entry)
        
        return True, None, {"tier_updated": True, "history_updated": True}


class MigrationAdditionPhase(MigrationPhase):
    """Phase 4: Add to target tier"""
    
    async def execute(self, _memory: Any, _source_tier: Any, _target_tier: Any, _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Add memory to target tier"""
        memories_by_tier[target_tier][memory.memory_id] = memory
        return True, None, {"added_to_target": True}


class MigrationVerificationPhase(MigrationPhase):
    """Phase 5: Verify migration succeeded"""
    
    def __init__(self, _verify_func):
        self._verify_func = verify_func
    
    async def execute(self, _memory: Any, _source_tier: Any, _target_tier: Any, _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Verify memory is in correct tier"""
        _result = self._verify_func(
            _memory_id = memory.memory_id,
            _expected_tier = target_tier,
            _original_metadata = memory.metadata,
        )
        
        if not result.get("success"):
            return False, f"Migration verification failed: {result.get('error')}", result
        
        return True, None, result


class MigrationRollbackPhase(MigrationPhase):
    """Phase 7: Rollback on failure"""
    
    def __init__(self, _rollback_func):
        self._rollback_func = rollback_func
    
    async def execute(self, _memory: Any, _original_state: Dict[str, _Any], _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Dict[str, Any]:
        """Execute rollback"""
        return self._rollback_func(
            _memory = memory,
            _original_tier = original_state.get("original_tier"),
            _original_tier_history = original_state.get("original_tier_history"),
            _original_metadata = original_state.get("original_metadata"),
            _original_data = original_state.get("original_data"),
            _original_compressed = original_state.get("original_compressed"),
            _original_compression_ratio = original_state.get("original_compression_ratio"),
            _original_size_bytes = original_state.get("original_size_bytes"),
        )


class MigrationStrategy:
    """Main migration strategy that orchestrates all phases"""
    
    def __init__(self, _verify_func, _rollback_func):
        self._validation_phase = MigrationValidationPhase()
        self._removal_phase = MigrationRemovalPhase()
        self._update_phase = MigrationUpdatePhase()
        self._addition_phase = MigrationAdditionPhase()
        self._verification_phase = MigrationVerificationPhase(verify_func)
        self._rollback_phase = MigrationRollbackPhase(rollback_func)
    
    async def execute_migration(self, _memory: Any, _source_tier: Any, _target_tier: Any, _memories_by_tier: Dict[str, _Dict[str, _Any]], _trigger: Any, _reason: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Execute full migration through all phases"""
        # Phase 1: Validation
        success, error, _ = await self._validation_phase.execute(
            memory, source_tier, target_tier, memories_by_tier
        )
        if not success:
            return False, error, {}
        
        # Phase 2: Removal
        success, error, _ = await self._removal_phase.execute(
            memory, source_tier, target_tier, memories_by_tier
        )
        if not success:
            return False, error, {}
        
        # Phase 3: Update
        success, error, _ = await self._update_phase.execute(
            memory, source_tier, target_tier, memories_by_tier
        )
        if not success:
            # Need rollback
            await self._rollback_phase.execute(
                memory, {"original_tier": source_tier}, memories_by_tier
            )
            return False, error, {}
        
        # Phase 4: Addition
        success, error, _ = await self._addition_phase.execute(
            memory, source_tier, target_tier, memories_by_tier
        )
        if not success:
            await self._rollback_phase.execute(
                memory, {"original_tier": source_tier}, memories_by_tier
            )
            return False, error, {}
        
        # Phase 5: Verification
        success, error, verification = await self._verification_phase.execute(
            memory, source_tier, target_tier, memories_by_tier
        )
        if not success:
            await self._rollback_phase.execute(
                memory, {"original_tier": source_tier}, memories_by_tier
            )
            return False, error, {}
        
        return True, None, verification
    
    async def rollback(self, _memory: Any, _original_state: Dict[str, _Any], _memories_by_tier: Dict[str, _Dict[str, _Any]]) -> Dict[str, Any]:
        """Execute rollback"""
        return await self._rollback_phase.execute(memory, original_state, memories_by_tier)