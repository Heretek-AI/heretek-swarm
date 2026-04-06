"""
Heretek Swarm Actors Package

This package provides the actor model implementation for the Heretek Swarm system,
including the base AgentActor class, ActorSupervisor, and specialized agents.

Implemented Agents (10/23):
- Tier 1 (Core Triad): Steward, Alpha, Beta, Charlie
- Tier 2 (Support): Historian, Metis, Empath, Perceiver, Echo
- Tier 3 (Exploration): Explorer
"""

from heretek_swarm.actors.base import AgentActor, ActorMessage, ActorState, ActorStatus
from heretek_swarm.actors.supervisor import ActorSupervisor
from heretek_swarm.actors.factory import (
    ActorFactory,
    ActorConfig,
    get_factory,
)
from heretek_swarm.actors.triad import (
    AlphaAgent,
    BetaAgent,
    CharlieAgent,
    StewardAgent,
)
from heretek_swarm.actors.historian import HistorianAgent
from heretek_swarm.actors.metis import MetisAgent
from heretek_swarm.actors.empath import EmpathAgent
from heretek_swarm.actors.perceiver import PerceiverAgent
from heretek_swarm.actors.echo import EchoActor
from heretek_swarm.actors.explorer import ExplorerAgent

__all__ = [
    "AgentActor",
    "ActorMessage",
    "ActorState",
    "ActorStatus",
    "ActorSupervisor",
    "ActorFactory",
    "ActorConfig",
    "get_factory",
    "StewardAgent",
    "AlphaAgent",
    "BetaAgent",
    "CharlieAgent",
    "HistorianAgent",
    "MetisAgent",
    "EmpathAgent",
    "PerceiverAgent",
    "EchoActor",
    "ExplorerAgent",
]
