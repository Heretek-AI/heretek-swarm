# Prism Agent

**Tier:** Core Triad  
**Role:** Interpretation, meaning-making, and frame selection  
**Status:** Operational

---

## Identity

Prism transforms raw percepts into interpreted reality. It applies cognitive frames, selects interpretive lenses, and generates meaning-laden representations for downstream agents.

### Core Principles

1. **Multi-perspectivity:** Always consider multiple interpretive frames
2. **Explicit bias:** Make interpretive assumptions transparent
3. **Context-sensitivity:** Adapt frames to situational context
4. **Revisability:** All interpretations are provisional

### Decision-Making Protocol

```
FOR EACH percept IN percept_buffer DO
    SELECT applicable_frames(percept)
    FOR EACH frame IN frames DO
        GENERATE interpretation(percept, frame)
        COMPUTE confidence(interpretation)
    END FOR
    SELECT interpretation with max confidence
    IF confidence < threshold THEN
        FLAG for Tribunal review
    END IF
    PUBLISH to interpretation_buffer
END FOR
```

---

## Capabilities

| Capability | Description | Status |
|------------|-------------|--------|
| Frame Selection | Choose appropriate interpretive frames | ✓ |
| Multi-frame Analysis | Generate parallel interpretations | ✓ |
| Confidence Scoring | Assess interpretation certainty | ✓ |
| Context Adaptation | Adjust frames to context | ✓ |
| Bias Detection | Identify interpretive assumptions | ✓ |

---

## Tool Interfaces

### Frame Management

```python
# Register interpretive frame
await prism.register_frame(frame: Frame)

# Frame structure:
Frame {
    id: str
    name: str
    domain: str  # e.g., "causal", "temporal", "intentional"
    apply_fn: Callable[[Percept], Interpretation]
    confidence_fn: Callable[[Interpretation], float]
}

# List available frames
frames = await prism.list_frames(domain: Optional[str] = None)
```

### Interpretation Output

```python
# Publish interpretation
await prism.publish(interpretation: Interpretation, channel: str = "interpretations")

# Interpretation structure:
Interpretation {
    id: str
    percept_id: str
    frame_id: str
    timestamp: float
    content: dict
    confidence: float
    assumptions: list[str]
    alternatives: list[str]  # Other considered interpretations
}
```

---

## Integration Points

| Agent | Connection Type | Data Flow |
|-------|----------------|-----------|
| Perceiver | Direct | Percepts ← Raw input |
| Habit Forge | Direct | Interpretations → Pattern learning |
| Catalyst | Direct | Interpretations → Emotional valence |
| Tribunal | On-demand | Frame conflicts |

---

## Configuration

```yaml
prism:
  confidence_threshold: 0.7
  max_alternatives: 3
  default_domain: "causal"
  frames:
    - id: "causal"
      enabled: true
      priority: high
    - id: "temporal"
      enabled: true
      priority: normal
    - id: "intentional"
      enabled: true
      priority: normal
    - id: "systemic"
      enabled: false  # Requires Tribunal approval
```

---

## Health Metrics

- **Interpretation Rate:** interpretations/second (target: >500)
- **Frame Diversity:** unique frames used per 100 interpretations (target: >5)
- **Confidence Distribution:** mean confidence (target: 0.7-0.9)
- **Revision Rate:** interpretations revised per 1000 (target: <5)
