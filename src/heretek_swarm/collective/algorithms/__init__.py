"""Collective algorithms module.

Contains bio-inspired swarm intelligence algorithms:
- ACO: Ant Colony Optimization
- PSO: Particle Swarm Optimization
- ABC: Artificial Bee Colony
"""

from collective.algorithms.abc import ABC, BeeAgent, SwarmDecision as ABCSwarmDecision
from collective.algorithms.aco import ACO, PheromoneTrail, SwarmDecision as ACOSwarmDecision
from collective.algorithms.pso import (
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
