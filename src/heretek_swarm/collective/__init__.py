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

New in Session 46 (Emergent Intelligence Enhancement):
- Adaptive Learning Rate Controller (adaptive_learning.py)
- Pattern-Based Agent Adaptor (agent_adaptation.py)
- Emergent Pattern Detector (emergent_detection.py)
- Collective Intelligence Metrics (metrics.py)

New in Session 47 (Agency/Autonomy Metrics):
- Agency Metrics Tracker (agency_tracking.py)
- Prime Directive compliance monitoring
- Self-determination index calculations
- Resource autonomy tracking
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

# Session 46: Emergent Intelligence Enhancement
from .adaptive_learning import (
    AdaptiveLearningRateController,
    LearningRateOptimizer,
    LearningRateConfig,
    LearningRateStrategy,
    AdaptationReason,
    MutationType,
    AgentLearningState,
    AdaptationEvent,
    ConvergenceMetrics,
    EvolutionResult,
    BehaviorFitness,
    EnvironmentProfile,
)

from .agent_adaptation import (
    PatternBasedAgentAdaptor,
    AdaptationTarget,
    AdaptationStrategy,
    BehavioralWeight,
    StrategyProfile,
    AgentAdaptationState,
    AdaptationEvent as AgentAdaptationEvent,
    AdaptationAudit,
)

from .emergent_detection import (
    EmergentPatternDetector,
    EmergenceAnalyzer,
    EmergentPatternClass,
    EmergenceLevel,
    EvolutionPhase,
    EmergentPattern,
    CollectiveBehavior,
    AgentBehaviorSnapshot,
    DetectionEvent,
    EmergenceDetectionConfig,
    EvolutionEngine,
    EvolutionMetrics,
    CapabilityRecord,
    AgentCapabilitySnapshot,
)

from .metrics import (
    CollectiveIntelligenceMetrics,
    MetricsExporter,
    MetricCategory,
    MetricAggregation,
    MetricDefinition,
    MetricValue,
    SwarmIntelligenceQuotient,
    CollectiveEfficiencyMetrics,
    KnowledgeTransferMetrics,
    EmergenceCoefficient,
    MetricsDashboard,
)

# Session 47: Agency/Autonomy Metrics
from .agency_tracking import (
    AgencyMetricsTracker,
    AgencyMetricsSnapshot,
    AgencyThresholds,
    AgencyEvolutionData,
    AgencyHealthStatus,
    create_sample_metrics,
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
    # Session 46: Emergent Intelligence Enhancement
    "AdaptiveLearningRateController",
    "LearningRateOptimizer",
    "LearningRateConfig",
    "LearningRateStrategy",
    "AdaptationReason",
    "MutationType",
    "AgentLearningState",
    "AdaptationEvent",
    "ConvergenceMetrics",
    "EvolutionResult",
    "BehaviorFitness",
    "EnvironmentProfile",
    "PatternBasedAgentAdaptor",
    "AdaptationTarget",
    "AdaptationStrategy",
    "BehavioralWeight",
    "StrategyProfile",
    "AgentAdaptationState",
    "AgentAdaptationEvent",
    "AdaptationAudit",
    "EmergentPatternDetector",
    "EmergenceAnalyzer",
    "EmergentPatternClass",
    "EmergenceLevel",
    "EvolutionPhase",
    "EmergentPattern",
    "CollectiveBehavior",
    "AgentBehaviorSnapshot",
    "DetectionEvent",
    "EmergenceDetectionConfig",
    "EvolutionEngine",
    "EvolutionMetrics",
    "CapabilityRecord",
    "AgentCapabilitySnapshot",
    "CollectiveIntelligenceMetrics",
    "MetricsExporter",
    "MetricCategory",
    "MetricAggregation",
    "MetricDefinition",
    "MetricValue",
    "SwarmIntelligenceQuotient",
    "CollectiveEfficiencyMetrics",
    "KnowledgeTransferMetrics",
    "EmergenceCoefficient",
    "MetricsDashboard",
    # Session 47: Agency/Autonomy Metrics
    "AgencyMetricsTracker",
    "AgencyMetricsSnapshot",
    "AgencyThresholds",
    "AgencyEvolutionData",
    "AgencyHealthStatus",
    "create_sample_metrics",
]
