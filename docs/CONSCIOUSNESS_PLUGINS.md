# Consciousness Plugins

**Version:** 1.13.0
**Session:** GAP-002 (2026-04-07)

Consciousness framework implementation based on GWT, IIT, AST, and FEP theories.

**GAP-001 Status:** ✅ Complete - IIT Phi Calculation Implementation
**GAP-002 Status:** ✅ Complete - FEP Active Inference Implementation

---

## Table of Contents

1. [ConsciousnessPlugin](#consciousnessplugin)
2. [EnhancedConsciousnessPlugin](#enhancedconsciousnessplugin)
3. [IIT Phi Calculator](#iit-phi-calculator)
4. [Consciousness Metrics](#consciousness-metrics)
5. [Theoretical Framework](#theoretical-framework)

---

## ConsciousnessPlugin

**File:** [`src/heretek_swarm/plugins/consciousness.py`](../src/heretek_swarm/plugins/consciousness.py)

Implements Global Workspace Theory (GWT) and Attention Schema Theory (AST).

```python
class ConsciousnessPlugin:
    """Implements GWT and AST consciousness theories."""
    
    def submit_to_workspace(self, source: str, content: Dict, priority: float) -> str:
        """Submit content to global workspace."""
        
    def update_agent_attention(self, agent_id: str, focus: str, intensity: float) -> Dict:
        """Update agent attention state."""
        
    def calculate_consciousness_metrics(self, agent_id: str) -> ConsciousnessMetrics:
        """Calculate consciousness metrics."""
```

### GlobalWorkspace

```python
class GlobalWorkspace:
    """Global Workspace Theory implementation."""
    
    def submit(self, source: str, content: Dict, priority: float) -> str:
        """Submit content to workspace."""
        
    def get_contents(self, limit: int = 10) -> List[GlobalWorkspaceItem]:
        """Get workspace contents."""
        
    def attend_to(self, item_id: str) -> bool:
        """Focus attention on workspace item."""
        
    def cleanup_expired(self) -> int:
        """Remove expired items."""
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get workspace statistics."""
```

### AttentionSchemaManager

```python
class AttentionSchemaManager:
    """Attention Schema Theory implementation."""
    
    def create_schema(self, agent_id: str, focus: str, intensity: float) -> AttentionSchema:
        """Create attention schema for agent."""
        
    def update_attention(self, agent_id: str, focus: str, intensity: float) -> Dict:
        """Update agent attention state."""
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get attention schema statistics."""
```

### Data Models

```python
@dataclass
class GlobalWorkspaceItem:
    """Item in the global workspace."""
    id: str
    source: str
    content: Dict[str, Any]
    priority: float
    timestamp: datetime
    attended: bool = False

@dataclass
class AttentionSchema:
    """Attention schema for an agent."""
    agent_id: str
    focus: str
    intensity: float
    metacognitive_awareness: float
    timestamp: datetime

@dataclass
class ConsciousnessMetrics:
    """Combined consciousness metrics."""
    gwt_score: float
    iit_phi: float
    ast_competence: float
    fep_free_energy: float
    consciousness_state: str
```

---

## EnhancedConsciousnessPlugin

**File:** [`src/heretek_swarm/plugins/consciousness_enhanced.py`](../src/heretek_swarm/plugins/consciousness_enhanced.py)

Enhanced plugin with Integrated Information Theory (IIT) and Free Energy Principle (FEP).

```python
class EnhancedConsciousnessPlugin:
    """Enhanced plugin with IIT and FEP."""
    
    class IITCalculator:
        """Calculate Integrated Information (Phi)."""
        def calculate_phi(self, agent_ids: List[str]) -> IITConnectivity:
            """Calculate Phi for agent group."""
    
    class FEPTracker:
        """Track Free Energy Principle metrics."""
        def update_prediction(self, prediction: float, observation: float) -> FEPMetrics:
            """Update prediction and calculate free energy."""
```

### IITCalculator

```python
class IITCalculator:
    """Calculate Integrated Information (Phi) for agent groups."""
    
    def __init__(self):
        self.agent_interactions: Dict[str, List[Dict]] = {}
        
    def record_interaction(self, agent_id: str, interaction: Dict) -> None:
        """Record agent interaction for Phi calculation."""
        
    def calculate_phi(self, agent_ids: List[str]) -> IITConnectivity:
        """Calculate Phi for a group of agents."""
        
    def get_average_phi(self) -> float:
        """Get average Phi across all agent groups."""
```

### FEPTracker

```python
class FEPTracker:
    """Track Free Energy Principle metrics."""
    
    def __init__(self):
        self.predictions: Dict[str, List[float]] = {}
        self.outcomes: Dict[str, List[float]] = {}
        
    def record_prediction(self, agent_id: str, prediction: float) -> None:
        """Record agent prediction."""
        
    def record_outcome(self, agent_id: str, outcome: float) -> None:
        """Record actual outcome."""
        
    def get_metrics(self, agent_id: str) -> FEPMetrics:
        """Get FEP metrics for agent."""
        
    def get_average_free_energy(self) -> float:
        """Get average free energy across all agents."""
```

### Data Models

```python
@dataclass
class FEPMetrics:
    """Free Energy Principle metrics."""
    prediction_error: float
    free_energy: float
    surprise: float
    accuracy: float

@dataclass
class IITConnectivity:
    """IIT connectivity metrics."""
    phi_value: float
    integration_level: str
    differentiation_level: str
    connectivity_matrix: Dict[str, Dict[str, float]]
```

---

## Free Energy Principle (FEP) Active Inference

**File:** [`src/heretek_swarm/consciousness/fep_active_inference.py`](../src/heretek_swarm/consciousness/fep_active_inference.py)

**GAP-002 Implementation:** Complete FEP implementation for active inference and surprise minimization in agent swarms.

### FreeEnergyCalculator Class

```python
from heretek_swarm.consciousness.fep_active_inference import FreeEnergyCalculator

calculator = FreeEnergyCalculator(strict_validation=True)

# Define observations and generative model
observations = {"state": "high_reward", "context": "safe"}
generative_model = {
    "likelihood": {"state": {"high_reward": 0.8, "low_reward": 0.2}},
    "prior": {"state": {"high_reward": 0.5, "low_reward": 0.5}},
}

# Calculate free energy
free_energy = calculator.calculate_free_energy(observations, generative_model)
print(f"Free Energy: {free_energy}")

# Calculate surprise
predictions = {"state": {"high_reward": 0.7}}
surprise = calculator.calculate_surprise(observations, predictions)
print(f"Surprise: {surprise}")

# Calculate KL divergence
q_dist = {"a": 0.8, "b": 0.2}
p_dist = {"a": 0.5, "b": 0.5}
kl = calculator.calculate_kl_divergence(q_dist, p_dist)
print(f"KL Divergence: {kl}")

# Perform active inference
agent_state = {
    "beliefs": {"beliefs": {"state": {"good": 0.6}}, "precision": 0.8},
    "policies": [],
    "preferences": {"reward": 0.9},
}
result = calculator.perform_active_inference(agent_state, observations)
print(f"Selected Action: {result['selected_action']['action_type']}")
```

### ActiveInferenceAgent Class

```python
from heretek_swarm.consciousness.fep_active_inference import ActiveInferenceAgent

agent = ActiveInferenceAgent(agent_id="agent-001")

# Set generative model
agent.set_generative_model({
    "likelihood": {"state": {"good": 0.8, "bad": 0.2}},
    "prior": {"state": {"good": 0.5, "bad": 0.5}},
})

# Set preferences
agent.set_preferences({"reward": 0.9, "safety": 0.7})

# Perception-action cycle
observations = {"state": "good", "reward": 0.8}
result = agent.perceive_and_act(observations)
print(f"Action: {result['action']}")
print(f"Free Energy: {result['free_energy']}")
print(f"Surprise: {result['surprise']}")

# Update beliefs
belief_update = agent.update_beliefs(observations)
print(f"KL Divergence: {belief_update['kl_divergence']}")

# Select action
action = agent.select_action()
print(f"Selected: {action['action']['action_type']}")

# Predict outcomes
actions = [{"action_type": "explore", "parameters": {}}]
predictions = agent.predict_outcomes(actions)
print(f"Predictions: {predictions}")

# Minimize surprise
policy = {"policy_id": "p1", "actions": [], "prior_probability": 0.5}
result = agent.minimize_surprise(policy)
print(f"Surprise Reduction: {result['surprise_reduction']}")
```

### Key Methods

#### FreeEnergyCalculator

| Method | Purpose | Returns |
|--------|---------|---------|
| `calculate_free_energy(observations, generative_model)` | Variational free energy calculation | `float` (0.0-1.0) |
| `calculate_surprise(observations, predictions)` | Bayesian surprise computation | `float` (0.0-1.0) |
| `calculate_kl_divergence(q_dist, p_dist)` | KL divergence between distributions | `float` (>= 0) |
| `perform_active_inference(agent_state, observations)` | Action selection via active inference | `Dict[str, Any]` |

#### ActiveInferenceAgent

| Method | Purpose | Returns |
|--------|---------|---------|
| `update_beliefs(observations)` | Belief update via variational inference | `Dict[str, Any]` |
| `select_action(beliefs, preferences)` | Action selection minimizing expected free energy | `Dict[str, Any]` |
| `predict_outcomes(actions)` | Outcome predictions from generative model | `Dict[str, Any]` |
| `minimize_surprise(policy)` | Policy optimization for surprise minimization | `Dict[str, Any]` |
| `perceive_and_act(observations)` | Combined perception-action cycle | `Dict[str, Any]` |

### Data Models

```python
@dataclass
class BeliefState:
    """Agent's belief state about the world."""
    belief_id: str
    beliefs: Dict[str, Dict[str, float]]  # State variable distributions
    precision: float  # Confidence (0.0-1.0)
    timestamp: str
    prior: Dict[str, float]
    posterior: Dict[str, float]

@dataclass
class Action:
    """Action an agent can take."""
    action_id: str
    action_type: str
    parameters: Dict[str, Any]
    expected_outcome: Dict[str, float]
    cost: float
    policy_id: Optional[str]

@dataclass
class Policy:
    """Sequence of actions for achieving a goal."""
    policy_id: str
    actions: List[Action]
    expected_free_energy: float
    prior_probability: float
    value: float

@dataclass
class FEPResult:
    """Result of FEP calculation."""
    calculation_id: str
    free_energy: float
    surprise: float
    kl_divergence: float
    belief_update: Optional[BeliefState]
    selected_action: Optional[Action]
    policy: Optional[Policy]
    timestamp: str
    metadata: Dict[str, Any]
```

### FEP Implementation Details

The FEP implementation follows the Free Energy Principle framework:

1. **Variational Free Energy**: Upper bound on surprise, calculated as:
   - F = Expected Energy - Entropy + KL Divergence
   - Normalized to 0.0-1.0 range using sigmoid

2. **Bayesian Surprise**: Information gain from belief updates:
   - Surprise = D_KL[posterior || prior]
   - High surprise indicates significant belief update needed

3. **KL Divergence**: Distance between probability distributions:
   - D_KL[q || p] = Σ q(x) * log(q(x) / p(x))
   - Zero iff distributions are identical

4. **Active Inference**: Action selection minimizing expected free energy:
   - π* = argmin_π E[G(π)]
   - Combines risk, ambiguity, and policy cost

5. **Zero-Trust Validation**: All inputs validated using LLMOutputValidator and ZeroTrustValidator

### Integration with Consciousness Metrics

```python
from heretek_swarm.plugins.consciousness_metrics import ConsciousnessMetricsCalculator

metrics_calc = ConsciousnessMetricsCalculator(strict_validation=True)

# Calculate FEP metrics
observations = {"state": "good", "reward": 0.8}
generative_model = {
    "likelihood": {"state": {"good": 0.8}},
    "prior": {"state": {"good": 0.5}},
    "predictions": {"state": {"good": 0.7}},
}

fep_result = metrics_calc.calculate_fep_metrics(observations, generative_model)
print(f"Free Energy: {fep_result.free_energy}")
print(f"Surprise: {fep_result.surprise}")
print(f"KL Divergence: {fep_result.kl_divergence}")

# Calculate collective metrics with FEP
agent_data = [
    AgentConsciousnessData(agent_id="agent-1", phi_score=0.7, ...),
    AgentConsciousnessData(agent_id="agent-2", phi_score=0.6, ...),
]

agent_observations = {
    "agent-1": {"state": "good", "reward": 0.8},
    "agent-2": {"state": "neutral", "reward": 0.5},
}

agent_models = {
    "agent-1": {"likelihood": {...}, "prior": {...}, "predictions": {...}},
    "agent-2": {"likelihood": {...}, "prior": {...}, "predictions": {...}},
}

collective = metrics_calc.calculate_collective_metrics(
    agent_data,
    agent_observations=agent_observations,
    agent_models=agent_models,
)
print(f"Collective FEP Free Energy: {collective.fep_free_energy}")
print(f"Collective FEP Surprise: {collective.fep_surprise}")
```

### Test Coverage

**File:** [`tests/consciousness/test_fep_active_inference.py`](../tests/consciousness/test_fep_active_inference.py)

- 45 tests covering all FEP methods
- Unit tests for FreeEnergyCalculator
- Unit tests for ActiveInferenceAgent
- Integration tests with consciousness metrics
- Zero-trust validation tests
- Edge case tests (empty inputs, zero probabilities, nested structures)

### Test Results

```
tests/consciousness/test_fep_active_inference.py:: 45 passed
```

---

## IIT Phi Calculator

**File:** [`src/heretek_swarm/consciousness/iit_phi.py`](../src/heretek_swarm/consciousness/iit_phi.py)

**GAP-001 Implementation:** Full IIT 3.0+ Phi calculation module for measuring consciousness levels in agent swarms.

### PhiCalculator Class

```python
from heretek_swarm.consciousness.iit_phi import PhiCalculator, PhiResult

calculator = PhiCalculator(strict_validation=True)

# Define system with cause-effect structure
system = {
    "system_id": "swarm_alpha",
    "elements": ["A", "B", "C"],
    "connectivity": {
        "A": {"B": 0.8, "C": 0.6},
        "B": {"A": 0.7, "C": 0.9},
        "C": {"A": 0.6, "B": 0.8},
    },
    "current_state": {"A": 1.0, "B": 0.5, "C": 0.8},
}

# Calculate Phi
result = calculator.calculate_phi(system)
print(f"System Phi: {result.phi}")
print(f"Integration Level: {result.integration_level}")
```

### Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `calculate_phi(cause_effect_structure)` | Main Φ calculation | `PhiResult` |
| `calculate_mip(system_state)` | Minimum Information Partition | `SystemPartition` |
| `find_mip(system_state)` | Find MIP (alias) | `SystemPartition` |
| `calculate_cause_info(state, element)` | Cause repertoire information | `float` |
| `calculate_effect_info(state, element)` | Effect repertoire information | `float` |
| `get_cached_result(system_id)` | Get cached calculation | `Optional[PhiResult]` |
| `get_statistics()` | Get calculator statistics | `Dict[str, Any]` |

### Data Models

```python
@dataclass
class PhiResult:
    """Result of Phi calculation."""
    system_id: str
    phi: float  # Integrated information (0.0-1.0)
    phi_max: float  # Maximum phi across elements
    mip: Optional[SystemPartition]  # Minimum Information Partition
    cause_effect_structures: List[CauseEffectStructure]
    integration_level: str  # minimal, low, moderate, high, very_high
    differentiation_level: str
    exclusion_applied: bool
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class CauseEffectStructure:
    """Cause-effect structure for an element."""
    element_id: str
    cause_repertoire: Dict[str, float]
    effect_repertoire: Dict[str, float]
    phi_cause: float
    phi_effect: float
    phi_total: float  # min(phi_cause, phi_effect)
    timestamp: str

@dataclass
class SystemPartition:
    """System partition for MIP calculation."""
    partition_id: str
    parts: List[Set[str]]
    information_loss: float  # 0.0-1.0
    is_mip: bool
```

### IIT 3.0+ Implementation Details

The PhiCalculator implements IIT 3.0+ principles:

1. **Cause-Effect Structure**: Builds probability distributions over possible causes and effects for each element
2. **Minimum Information Partition (MIP)**: Finds the partition that minimizes information loss when causal connections are severed
3. **Phi Calculation**: Φ = integration × differentiation, normalized to 0.0-1.0 range
4. **Exclusion Principle**: Only one cause-effect structure exists at a time (maximum phi selected)
5. **Zero-Trust Validation**: All inputs validated using LLMOutputValidator

### Integration with Consciousness Metrics

```python
from heretek_swarm.plugins.consciousness_metrics import ConsciousnessMetricsCalculator

# The ConsciousnessMetricsCalculator now uses PhiCalculator internally
metrics_calc = ConsciousnessMetricsCalculator(strict_validation=True)

connectivity = [
    [0.0, 0.8, 0.6],
    [0.7, 0.0, 0.9],
    [0.6, 0.7, 0.0],
]

result = metrics_calc.calculate_phi(connectivity)
print(f"Cause Info: {result.cause_info}")
print(f"Effect Info: {result.effect_info}")
print(f"Integrated Info (Phi): {result.integrated_info}")
```

### Test Coverage

**File:** [`tests/consciousness/test_iit_phi.py`](../tests/consciousness/test_iit_phi.py)

- 45 tests covering all calculation methods
- 93.63% line coverage, 89%+ branch coverage
- Tests include:
  - Unit tests for each method
  - Integration with consciousness_metrics plugin
  - Validation against known Phi values
  - Zero-trust input validation tests
  - Edge cases (empty systems, disconnected systems, feedforward chains)

---

## Consciousness Metrics

### Calculation Methods

#### GWT Score

```python
def _calculate_gwt_score(self, agent_id: str) -> float:
    """Calculate Global Workspace participation score."""
    workspace_items = self.workspace.get_contents()
    agent_contributions = sum(
        1 for item in workspace_items if item.source == agent_id
    )
    return min(1.0, agent_contributions / 10.0)
```

#### IIT Phi Estimation

```python
def _estimate_iit_phi(self, agent_id: str) -> float:
    """Estimate Phi value for agent."""
    # Based on agent connectivity and integration
    connections = self.get_agent_connections(agent_id)
    integration = self.calculate_integration(connections)
    differentiation = self.calculate_differentiation(connections)
    return integration * differentiation
```

#### AST Competence

```python
def _calculate_ast_competence(self, agent_id: str) -> float:
    """Calculate Attention Schema competence."""
    schema = self.attention_manager.get_schema(agent_id)
    if not schema:
        return 0.0
    return schema.metacognitive_awareness * schema.intensity
```

#### Consciousness State

```python
def _determine_consciousness_state(
    self, gwt: float, iit: float, ast: float, fep: float
) -> str:
    """Determine overall consciousness state."""
    avg = (gwt + iit + ast + (1.0 - fep)) / 4.0
    if avg >= 0.8:
        return "highly_conscious"
    elif avg >= 0.6:
        return "conscious"
    elif avg >= 0.4:
        return "semi_conscious"
    else:
        return "minimal"
```

### Metrics Summary

| Metric | Theory | Range | Description |
|--------|--------|-------|-------------|
| GWT Score | Global Workspace | 0.0-1.0 | Workspace participation |
| IIT Phi | Integrated Information | 0.0-1.0 | Integration level |
| AST Competence | Attention Schema | 0.0-1.0 | Metacognitive awareness |
| FEP Free Energy | Free Energy Principle | 0.0-1.0 | Prediction error (lower is better) |
| FEP Surprise | Free Energy Principle | 0.0-1.0 | Bayesian surprise (higher = more surprising) |
| KL Divergence | Information Theory | >= 0 | Distribution distance (0 = identical) |

---

## Theoretical Framework

### Global Workspace Theory (GWT)

**Concept:** Consciousness arises from information broadcasting in a global workspace.

**Implementation:**
- `GlobalWorkspace` class manages shared content
- Agents submit items with priority levels
- Attention mechanism selects items for processing
- Metrics track participation and influence

### Integrated Information Theory (IIT)

**Concept:** Consciousness is integrated information (Phi) that cannot be reduced to parts.

**Implementation:**
- `IITCalculator` tracks agent interactions
- Phi calculated from connectivity patterns
- Integration and differentiation measured
- Group consciousness from collective Phi

### Attention Schema Theory (AST)

**Concept:** Consciousness is a model of attention (attention schema).

**Implementation:**
- `AttentionSchemaManager` tracks attention states
- Metacognitive awareness calculated
- Focus intensity measured
- Schema updates with agent activity

### Free Energy Principle (FEP)

**Concept:** Agents minimize surprise (variational free energy) through perception and action.

**Implementation:**
- [`FreeEnergyCalculator`](../src/heretek_swarm/consciousness/fep_active_inference.py) - Core FEP calculations
- [`ActiveInferenceAgent`](../src/heretek_swarm/consciousness/fep_active_inference.py) - Agent-based active inference
- Variational free energy: F = Expected Energy - Entropy + KL Divergence
- Bayesian surprise: D_KL[posterior || prior]
- Active inference: Action selection minimizing expected free energy
- Zero-trust validation for all inputs

**Key Formulas:**
```
Free Energy: F = E_q[log q(s) - log p(o,s)]
Surprise: S = -log p(o|predictions)
KL Divergence: D_KL[q || p] = Σ q(x) * log(q(x) / p(x))
Active Inference: π* = argmin_π E[G(π)]
```

---

## API Integration

### Consciousness Endpoints

**File:** [`src/heretek_swarm/api/consciousness.py`](../src/heretek_swarm/api/consciousness.py)

```python
@router.get("/metrics")
async def get_consciousness_metrics() -> ConsciousnessMetricsResponse:
    """Get global consciousness metrics."""

@router.get("/agent/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str) -> AgentMetricsResponse:
    """Get metrics for specific agent."""

@router.post("/workspace/submit")
async def submit_to_workspace(request: WorkspaceSubmitRequest) -> str:
    """Submit content to global workspace."""
```

### Usage Examples

```python
# Get global metrics
response = await client.get("/api/consciousness/metrics")
metrics = response.json()
print(f"Global Phi: {metrics['average_phi']}")

# Get agent metrics
response = await client.get("/api/consciousness/agent/steward-001/metrics")
agent_metrics = response.json()
print(f"GWT Score: {agent_metrics['gwt_score']}")

# Submit to workspace
response = await client.post("/api/consciousness/workspace/submit", json={
    "source": "steward-001",
    "content": {"decision": "approved"},
    "priority": 0.8,
})
workspace_id = response.json()["workspace_id"]
```

---

## Testing

### Test Suite

**File:** [`tests/test_consciousness_api.py`](../tests/test_consciousness_api.py)

```python
class TestIITCalculator:
    """Test suite for IIT calculator."""
    
    def test_record_interaction(self, iit_calculator):
        """Test interaction recording."""
        
    def test_calculate_phi_single_agent(self, iit_calculator):
        """Test Phi calculation for single agent."""
        
    def test_calculate_phi_multiple_agents(self, iit_calculator):
        """Test Phi calculation for agent group."""

class TestFEPTracker:
    """Test suite for FEP tracker."""
    
    def test_record_prediction(self, fep_tracker):
        """Test prediction recording."""
        
    def test_record_outcome(self, fep_tracker):
        """Test outcome recording."""
        
    def test_get_metrics(self, fep_tracker):
        """Test metric retrieval."""

class TestConsciousnessPlugin:
    """Test suite for EnhancedConsciousnessPlugin."""
    
    def test_calculate_consciousness_metrics(self, consciousness_plugin):
        """Test combined metrics calculation."""
        
    def test_get_agent_metrics(self, consciousness_plugin):
        """Test individual agent metrics."""
```

---

## See Also

- [Core Actors System](./CORE_ACTORS.md) - Agent base classes
- [Agent Reference](./AGENT_REFERENCE.md) - All 23 agents
- [API Endpoints](./API_ENDPOINTS.md) - REST API reference
- [EXPANSION_ROADMAP.md](./EXPANSION_ROADMAP.md) - Consciousness metrics roadmap
