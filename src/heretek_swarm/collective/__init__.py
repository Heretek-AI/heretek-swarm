"""
Agent Society Module - Collective Intelligence

Provides collective intelligence capabilities for Heretek Swarm including:
- Hierarchical agent coordination
- Collective decision-making
- Emergent behavior detection
- Shared collective memory
- Swarm optimization algorithms
- Cross-agent learning and knowledge transfer
- Pattern extraction and distribution

New in Session 41:
- Pattern Extraction Module (learning.py)
- Knowledge Transformation Module (knowledge_transform.py)
- Distributed Learning Engine (distributed_learning.py)
- Pattern Library (pattern_library.py)
"""

from .society import (
    AgentSociety,
    CollectiveMemory,
    CollectiveTask,
    CollectiveResult,
    CollectiveTaskType,
    SocietyRole,
    EmergentBehavior,
    AgentContribution,
)

from .learning import (
    PatternExtractor,
    CollectiveLearning,
    PatternType,
    PatternSource,
    PatternMetadata,
    ExtractedPattern,
    LearningSignal,
    MessageAnalysis,
)

from .knowledge_transform import (
    KnowledgeTransformer,
    KnowledgeTransformationService,
    TransformedKnowledge,
    TransformationResult,
    TransformationType,
    AgentType,
    AgentCapabilityProfile,
    ValidationResult,
)

from .distributed_learning import (
    DistributedLearningEngine,
    DistributedLearningCoordinator,
    DistributedLearningConfig,
    SyncMessage,
    SyncOperation,
    MergeStrategy,
    MergeResult,
)

from .pattern_library import (
    PatternLibrary,
    PatternLibraryService,
    PatternEntry,
    PatternCategory,
    StorageBackend,
    QueryResult,
    StorageStats,
)

__all__ = [
    # Society classes
    "AgentSociety",
    "CollectiveMemory",
    "CollectiveTask",
    "CollectiveResult",
    "CollectiveTaskType",
    "SocietyRole",
    "EmergentBehavior",
    "AgentContribution",
    # Learning classes
    "PatternExtractor",
    "CollectiveLearning",
    "PatternType",
    "PatternSource",
    "PatternMetadata",
    "ExtractedPattern",
    "LearningSignal",
    "MessageAnalysis",
    # Knowledge transformation
    "KnowledgeTransformer",
    "KnowledgeTransformationService",
    "TransformedKnowledge",
    "TransformationResult",
    "TransformationType",
    "AgentType",
    "AgentCapabilityProfile",
    "ValidationResult",
    # Distributed learning
    "DistributedLearningEngine",
    "DistributedLearningCoordinator",
    "DistributedLearningConfig",
    "SyncMessage",
    "SyncOperation",
    "MergeStrategy",
    "MergeResult",
    # Pattern library
    "PatternLibrary",
    "PatternLibraryService",
    "PatternEntry",
    "PatternCategory",
    "StorageBackend",
    "QueryResult",
    "StorageStats",
]
