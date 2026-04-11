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

# Session 46: Emergent Intelligence Enhancement
from .adaptive_learning import (
    AdaptationEvent,
    AdaptationReason,
    AdaptiveLearningRateController,
    AgentLearningState,
    BehaviorFitness,
    ConvergenceMetrics,
    EnvironmentProfile,
    EvolutionResult,
    LearningRateConfig,
    LearningRateOptimizer,
    LearningRateStrategy,
    MutationType,
)

# Session 47: Agency/Autonomy Metrics
from .agency_tracking import (
    AgencyEvolutionData,
    AgencyHealthStatus,
    AgencyMetricsSnapshot,
    AgencyMetricsTracker,
    AgencyThresholds,
    create_sample_metrics,
)
from .agent_adaptation import (
    AdaptationAudit,
    AdaptationStrategy,
    AdaptationTarget,
    AgentAdaptationState,
    BehavioralWeight,
    PatternBasedAgentAdaptor,
    StrategyProfile,
)
from .agent_adaptation import (
    AdaptationEvent as AgentAdaptationEvent,
)
from .distributed_learning import (
    DistributedLearningConfig,
    DistributedLearningCoordinator,
    DistributedLearningEngine,
    MergeResult,
    MergeStrategy,
    SyncMessage,
    SyncOperation,
)
from .emergent_detection import (
    AgentBehaviorSnapshot,
    AgentCapabilitySnapshot,
    CapabilityRecord,
    CollectiveBehavior,
    DetectionEvent,
    EmergenceAnalyzer,
    EmergenceDetectionConfig,
    EmergenceLevel,
    EmergentPattern,
    EmergentPatternClass,
    EmergentPatternDetector,
    EvolutionEngine,
    EvolutionMetrics,
    EvolutionPhase,
)
from .knowledge_transform import (
    AgentCapabilityProfile,
    AgentType,
    KnowledgeTransformationService,
    KnowledgeTransformer,
    TransformationResult,
    TransformationType,
    TransformedKnowledge,
    ValidationResult,
)
from .learning import (
    CollectiveLearning,
    ExtractedPattern,
    LearningSignal,
    MessageAnalysis,
    PatternExtractor,
    PatternMetadata,
    PatternSource,
    PatternType,
)
from .metrics import (
    CollectiveEfficiencyMetrics,
    CollectiveIntelligenceMetrics,
    EmergenceCoefficient,
    KnowledgeTransferMetrics,
    MetricAggregation,
    MetricCategory,
    MetricDefinition,
    MetricsDashboard,
    MetricsExporter,
    MetricValue,
    SwarmIntelligenceQuotient,
)
from .pattern_library import (
    PatternCategory,
    PatternEntry,
    PatternLibrary,
    PatternLibraryService,
    QueryResult,
    StorageBackend,
    StorageStats,
)
from .society import (
    AgentContribution,
    AgentSociety,
    CollectiveMemory,
    CollectiveResult,
    CollectiveTask,
    CollectiveTaskType,
    EmergentBehavior,
    SocietyRole,
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
