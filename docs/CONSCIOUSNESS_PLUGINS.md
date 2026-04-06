# Consciousness Plugins

**Version:** 1.11.0  
**Session:** 21 (2026-04-06)

Consciousness framework implementation based on GWT, IIT, AST, and FEP theories.

---

## Table of Contents

1. [ConsciousnessPlugin](#consciousnessplugin)
2. [EnhancedConsciousnessPlugin](#enhancedconsciousnessplugin)
3. [Consciousness Metrics](#consciousness-metrics)
4. [Theoretical Framework](#theoretical-framework)

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
| FEP Free Energy | Free Energy Principle | 0.0-∞ | Prediction error (lower is better) |

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

**Concept:** Agents minimize surprise by reducing prediction error.

**Implementation:**
- `FEPTracker` records predictions and outcomes
- Free energy calculated from prediction error
- Surprise and accuracy metrics
- Adaptive behavior optimization

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
