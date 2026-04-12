"""
Consciousness Metrics Module.

Provides metrics collection and calculation for measuring consciousness,
agency, and emergence in agent swarms using:
- Integrated Information Theory (IIT) for phi calculations
- Adaptive Systems Theory (AST) for complexity and emergence metrics
- Agency metrics for autonomy and self-governance

Usage:
    from heretek_swarm.consciousness.metrics import (
        measure_phi,
        measure_adaptive_metrics,
        ConsciousnessMetrics,
    )

    # Measure phi for an agent
    phi = measure_phi(agent_state)

    # Get full consciousness metrics
    metrics = measure_adaptive_metrics(agent_state)
"""

from heretek_swarm.consciousness.metrics.iit import (
    ConsciousnessMetrics,
    measure_phi,
    measure_phi_for_system,
    PhiResult,
)
from heretek_swarm.consciousness.metrics.ast import (
    AdaptiveMetrics,
    measure_adaptive_metrics,
    EmergenceLevel,
)

__all__ = [
    # IIT (Integrated Information Theory)
    "ConsciousnessMetrics",
    "measure_phi",
    "measure_phi_for_system",
    "PhiResult",
    # AST (Adaptive Systems Theory)
    "AdaptiveMetrics",
    "measure_adaptive_metrics",
    "EmergenceLevel",
]
