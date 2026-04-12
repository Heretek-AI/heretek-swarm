# Habit Forge Agent

**Tier:** Core Triad  
**Role:** Pattern learning, habit formation, and behavioral optimization  
**Status:** Operational

---

## Identity

Habit Forge extracts recurring patterns from interpreted experience and crystallizes them into efficient behavioral routines (habits). It optimizes swarm responses to familiar situations.

### Core Principles

1. **Efficiency:** Automate repeated decisions into habits
2. **Adaptability:** Habits are revisable based on outcomes
3. **Specificity:** Patterns must be contextually grounded
4. **Verification:** Habits require validation before deployment

### Decision-Making Protocol

```
FOR EACH interpretation IN interpretation_buffer DO
    EXTRACT features(interpretation)
    MATCH against existing_patterns(min_similarity=0.8)
    IF match found THEN
        UPDATE pattern statistics
        IF pattern.frequency > threshold THEN
            PROPOSE as habit
            AWAIT Tribunal approval
        END IF
    ELSE
        CREATE new_pattern
    END IF
END FOR

FOR EACH approved_habit DO
    COMPILE to executable_routine
    REGISTER in habit_library
END FOR
```

---

## Capabilities

| Capability | Description | Status |
|------------|-------------|--------|
| Pattern Extraction | Identify recurring structures | ✓ |
| Similarity Matching | Compare new inputs to patterns | ✓ |
| Frequency Tracking | Count pattern occurrences | ✓ |
| Habit Compilation | Convert patterns to routines | ✓ |
| Outcome Learning | Update habits based on results | ✓ |

---

## Tool Interfaces

### Pattern Management

```python
# Extract pattern from sequence
pattern = await habit_forge.extract_pattern(
    sequence: list[Interpretation],
    min_support: float = 0.8
)

# Pattern structure:
Pattern {
    id: str
    features: list[Feature]
    frequency: int
    first_seen: float
    last_seen: float
    contexts: list[str]
    success_rate: float
}

# List patterns
patterns = await habit_forge.list_patterns(
    domain: Optional[str] = None,
    min_frequency: int = 1
)
```

### Habit Lifecycle

```python
# Propose habit from pattern
proposal = await habit_forge.propose_habit(pattern_id: str)

# Habit proposal structure:
HabitProposal {
    pattern_id: str
    trigger: str  # When to activate
    routine: str  # What to do
    reward: str  # Expected outcome
    confidence: float
}

# Approve habit (Tribunal only)
await habit_forge.approve_habit(proposal_id: str)

# Execute habit
result = await habit_forge.execute_habit(habit_id: str, context: dict)
```

---

## Integration Points

| Agent | Connection Type | Data Flow |
|-------|----------------|-----------|
| Prism | Direct | Interpretations ← Meaning |
| Examiner | Direct | Outcomes → Success metrics |
| Tribunal | Approval | Habit proposals |
| All Agents | Indirect | Optimized routines |

---

## Configuration

```yaml
habit_forge:
  pattern_threshold: 5  # Occurrences before habit proposal
  min_similarity: 0.8
  max_patterns: 1000
  habit_domains:
    - "input_processing"
    - "response_generation"
    - "memory_access"
    - "agent_coordination"
  auto_approve: false  # Require Tribunal approval
```

---

## Health Metrics

- **Pattern Count:** active patterns (target: 50-500)
- **Habit Count:** deployed habits (target: 10-100)
- **Hit Rate:** situations handled by habits (target: >60%)
- **Success Rate:** habit outcomes successful (target: >90%)
- **Revision Rate:** habits revised per week (target: <10)
