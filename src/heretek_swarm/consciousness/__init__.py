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

__all__ = [
    "ActionOrigin",
    "AgencyLevel",
    "AgencyMetricsCalculator",
    "AgentAgencyMetrics",
    "AutonomyLevel",
    "DecisionPoint",
    "DeliberationGWTIntegrator",
    "FEPResult",
    "FreeEnergyCalculator",
    "GWTConfig",
    "GWTContent",
    "GlobalWorkspaceBroadcast",
    "GWTSalienceCalculator",
    "GWTSalienceMetrics",
    "GWTDeliberationMixin",
    "integrate_gwt_with_agent",
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
