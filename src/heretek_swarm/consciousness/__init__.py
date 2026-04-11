"""
Heretek Swarm Consciousness Package

Implements neuroscience-inspired consciousness frameworks:
- IIT (Integrated Information Theory) - Phi calculation
- FEP (Free Energy Principle) - Active inference
- Phi Training - Consciousness metric optimization
- Agency/Autonomy Metrics - Self-governance measurement

New in Session 47:
- Agency metrics for Prime Directive compliance
- Self-determination index calculations
- Resource autonomy tracking
- Prime Directive compliance reporting
"""
# Agency/Autonomy Metrics (Session 47)
from heretek_swarm.consciousness.agency_metrics import (
    ActionOrigin,
    AgencyLevel,
    AgencyMetricsCalculator,
    AgentAgencyMetrics,
    AutonomyLevel,
    DecisionPoint,
    PrimeDirectiveComplianceReport,
    ResourceControl,
    create_decision_point,
    create_resource_control,
)
from heretek_swarm.consciousness.fep_active_inference import (
    FEPResult,
    FreeEnergyCalculator,
)
from heretek_swarm.consciousness.iit_phi import (
    PhiCalculator,
    PhiResult,
)
from heretek_swarm.consciousness.phi_training import (
    PhiTrainingEnvironment,
    ScenarioType,
    TrainingEpisode,
    TrainingMode,
    TrainingResult,
    TrainingScenario,
)

__all__ = [
    # IIT Phi
    "PhiCalculator",
    "PhiResult",
    # FEP
    "FreeEnergyCalculator",
    "FEPResult",
    # Phi Training
    # Note: PhiTrainer, ConsciousnessOptimizer, TrainingConfig not implemented
        # Actual classes: PhiTrainingEnvironment, TrainingScenario, TrainingResult,
        # TrainingEpisode, ScenarioType, TrainingMode

    # Agency/Autonomy Metrics (Session 47)
    "AgencyMetricsCalculator",
    "AgentAgencyMetrics",
    "DecisionPoint",
    "ResourceControl",
    "ActionOrigin",
    "AgencyLevel",
    "AutonomyLevel",
    "PrimeDirectiveComplianceReport",
    "create_decision_point",
    "create_resource_control",
]
