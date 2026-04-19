"""Collective algorithms module.

Contains bio-inspired swarm intelligence algorithms:
- ACO: Ant Colony Optimization
- PSO: Particle Swarm Optimization
- ABC: Artificial Bee Colony
"""

from heretek_swarm.collective.algorithms.abc import ABC, BeeAgent, SwarmDecision as ABCSwarmDecision
from heretek_swarm.collective.algorithms.aco import ACO, PheromoneTrail, SwarmDecision as ACOSwarmDecision
from heretek_swarm.collective.algorithms.pso import (
    PSO,
    Particle,
    SwarmDecision as PSOSwarmDecision,
    SwarmPattern,
)

__all__ = [
    "ABC",
    "ACO",
    "PSO",
    "BeeAgent",
    "Particle",
    "PheromoneTrail",
    "SwarmPattern",
    "ABCSwarmDecision",
    "ACOSwarmDecision",
    "PSOSwarmDecision",
]
