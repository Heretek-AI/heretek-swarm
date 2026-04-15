"""
Heretek Swarm Consciousness Package

Implements neuroscience-inspired consciousness frameworks:
- IIT (Integrated Information Theory) - Phi calculation
- FEP (Free Energy Principle) - Active inference
- GWT (Global Workspace Theory) - Consciousness broadcast
- Agency/Autonomy Metrics - Self-governance measurement
"""

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
from heretek_swarm.consciousness.gwt import (
    GWTConfig,
    GWTContent,
    GlobalWorkspaceBroadcast,
    GWTSalienceMetrics,
    RateLimitConfig,
    SalienceLevel,
    calculate_salience,
    create_gwt_content,
)
from heretek_swarm.consciousness.gwt_deliberation import (
    DeliberationGWTIntegrator,
    GWTSalienceCalculator,
    GWTDeliberationMixin,
    integrate_gwt_with_agent,
)
from heretek_swarm.consciousness.iit_phi import (
    PhiCalculator,
    PhiResult,
)
from heretek_swarm.consciousness.ast import (
    ASTSelfModel,
    ASTSelfModelTracker,
    ComplexityMetrics,
    EmergenceLevel,
    EmergenceScore,
    ResilienceLevel,
    ResilienceScore,
    SelfOrganizationLevel,
    SelfOrganizationMetrics,
    calculate_complexity_metrics,
    calculate_emergence_score,
    calculate_resilience_score,
    calculate_self_organization,
    create_ast_self_model,
)
from heretek_swarm.consciousness.iit import (
    ConsciousnessLevel,
    CauseEffectStructure,
    IntegrationMetrics,
    IITTracker,
    PhiResult as IITPhiResult,
    calculate_cause_effect_structure,
    calculate_integration_metrics,
    calculate_integrated_information,
    calculate_phi,
    calculate_phi_for_system,
)
from heretek_swarm.consciousness.fep import (
    ActiveInferenceMetrics,
    FEPMetrics,
    FEPTracker,
    FreeEnergyLevel,
    SurpriseLevel,
    SurpriseMetrics,
    ExpectedFreeEnergyMetrics,
    calculate_expected_free_energy,
    calculate_free_energy,
    calculate_surprise,
    create_fep_metrics,
)

__all__ = [
    "ActionOrigin",
    "AgencyLevel",
    "AgencyMetricsCalculator",
    "AgentAgencyMetrics",
    "AutonomyLevel",
    "DecisionPoint",
    "DeliberationGWTIntegrator",
    # Wave 2: Consciousness Frameworks
    # AST Self-Modeling
    "ASTSelfModel",
    "ASTSelfModelTracker",
    "ComplexityMetrics",
    "EmergenceLevel",
    "EmergenceScore",
    "ResilienceLevel",
    "ResilienceScore",
    "SelfOrganizationLevel",
    "SelfOrganizationMetrics",
    "calculate_complexity_metrics",
    "calculate_emergence_score",
    "calculate_resilience_score",
    "calculate_self_organization",
    "create_ast_self_model",
    # FEP
    "FEPResult",
    "FreeEnergyCalculator",
    # IIT Metrics
    "ConsciousnessLevel",
    "CauseEffectStructure",
    "IntegrationMetrics",
    "IITTracker",
    "IITPhiResult",
    "calculate_cause_effect_structure",
    "calculate_integration_metrics",
    "calculate_integrated_information",
    "calculate_phi",
    "calculate_phi_for_system",
    # FEP
    "ActiveInferenceMetrics",
    "FEPMetrics",
    "FEPTracker",
    "FreeEnergyLevel",
    "SurpriseLevel",
    "SurpriseMetrics",
    "ExpectedFreeEnergyMetrics",
    "calculate_expected_free_energy",
    "calculate_free_energy",
    "calculate_surprise",
    "create_fep_metrics",
    # GWT
    "GWTConfig",
    "GWTContent",
    "GlobalWorkspaceBroadcast",
    "GWTSalienceCalculator",
    "GWTSalienceMetrics",
    "GWTDeliberationMixin",
    "integrate_gwt_with_agent",
    # IIT Phi
    "PhiCalculator",
    "PhiResult",
    "PrimeDirectiveComplianceReport",
    "RateLimitConfig",
    "ResourceControl",
    "SalienceLevel",
    "calculate_salience",
    "create_decision_point",
    "create_gwt_content",
    "create_resource_control",
]
