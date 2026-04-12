# Prism Agent - Tool Catalog

## Frame Management Tools

### `register_frame(frame)`
Register an interpretive frame.

**Parameters:**
- `frame` (Frame): Frame definition

**Frame Structure:**
```python
Frame {
    id: str,
    name: str,
    domain: str,
    apply_fn: Callable,
    confidence_fn: Callable
}
```

### `unregister_frame(frame_id)`
Remove a frame from the registry.

**Parameters:**
- `frame_id` (str): Frame ID

### `list_frames(domain=None)`
List available frames, optionally filtered by domain.

**Parameters:**
- `domain` (str, optional): Filter by domain

**Returns:** List[Frame]

### `get_frame(frame_id)`
Get a specific frame by ID.

**Parameters:**
- `frame_id` (str): Frame ID

**Returns:** Frame or None

---

## Interpretation Tools

### `interpret(percept, frames=None)`
Generate interpretation(s) for a percept.

**Parameters:**
- `percept` (Percept): Input percept
- `frames` (list[str], optional): Specific frames to use

**Returns:** InterpretationResult {
    primary: Interpretation,
    alternatives: list[Interpretation],
    confidence: float
}

### `compare_interpretations(i1, i2)`
Compare two interpretations for consistency.

**Parameters:**
- `i1` (Interpretation): First interpretation
- `i2` (Interpretation): Second interpretation

**Returns:** ComparisonResult {
    consistent: bool,
    divergence: float,
    conflicts: list[str]
}

### `revise(interpretation, new_evidence)`
Revise an interpretation based on new evidence.

**Parameters:**
- `interpretation` (Interpretation): Original interpretation
- `new_evidence` (dict): New evidence to incorporate

**Returns:** Revised interpretation

---

## Analysis Tools

### `get_confidence_distribution()`
Get distribution of confidence scores.

**Returns:** DistributionStats {
    mean: float,
    std: float,
    histogram: dict
}

### `get_frame_usage(domain=None)`
Get frame usage statistics.

**Parameters:**
- `domain` (str, optional): Filter by domain

**Returns:** FrameUsageStats {
    frames: list[FrameStats],
    diversity: float
}
