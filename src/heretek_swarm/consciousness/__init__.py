"""
Heretek Swarm Consciousness Package

Implements neuroscience-inspired consciousness frameworks:
- IIT (Integrated Information Theory) - Phi calculation
- FEP (Free Energy Principle) - Active inference
- Phi Training - Consciousness metric optimization
"""
from heretek_swarm.consciousness.iit_phi import (
    PhiCalculator,
    PhiResult,
)
from heretek_swarm.consciousness.fep_active_inference import (
    FreeEnergyCalculator,
    FEPResult,
)
from heretek_swarm.consciousness.phi_training import (
    PhiTrainingEnvironment,
    TrainingScenario,
    TrainingResult,
    TrainingEpisode,
    ScenarioType,
    TrainingMode,
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
    ]