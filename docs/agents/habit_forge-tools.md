# Habit Forge Agent - Tool Catalog

## Pattern Tools

### `extract_pattern(sequence, min_support=0.8)`
Extract a pattern from a sequence of interpretations.

**Parameters:**
- `sequence` (list[Interpretation]): Sequence to analyze
- `min_support` (float): Minimum similarity threshold

**Returns:** Pattern or None

### `match_pattern(item, min_similarity=0.8)`
Match an item against existing patterns.

**Parameters:**
- `item` (dict): Item to match
- `min_similarity` (float): Minimum similarity

**Returns:** MatchResult {
    pattern: Pattern,
    similarity: float
} or None

### `list_patterns(domain=None, min_frequency=1)`
List patterns, optionally filtered.

**Parameters:**
- `domain` (str, optional): Filter by domain
- `min_frequency` (int): Minimum frequency

**Returns:** List[Pattern]

### `delete_pattern(pattern_id)`
Delete a pattern.

**Parameters:**
- `pattern_id` (str): Pattern ID

---

## Habit Tools

### `propose_habit(pattern_id)`
Propose a habit based on a pattern.

**Parameters:**
- `pattern_id` (str): Pattern ID

**Returns:** HabitProposal {
    pattern_id: str,
    trigger: str,
    routine: str,
    reward: str,
    confidence: float
}

### `approve_habit(proposal_id)`
Approve a habit proposal (Tribunal only).

**Parameters:**
- `proposal_id` (str): Proposal ID

### `reject_habit(proposal_id, reason)`
Reject a habit proposal.

**Parameters:**
- `proposal_id` (str): Proposal ID
- `reason` (str): Rejection reason

### `execute_habit(habit_id, context)`
Execute a habit in a given context.

**Parameters:**
- `habit_id` (str): Habit ID
- `context` (dict): Execution context

**Returns:** HabitResult {
    success: bool,
    outcome: dict,
    duration_ms: float
}

### `list_habits(domain=None, status="active")`
List habits, optionally filtered.

**Parameters:**
- `domain` (str, optional): Filter by domain
- `status` (str): Status filter (active, pending, rejected)

**Returns:** List[Habit]

---

## Learning Tools

### `record_outcome(habit_id, outcome)`
Record the outcome of a habit execution.

**Parameters:**
- `habit_id` (str): Habit ID
- `outcome` (dict): Outcome data

### `update_habit(habit_id, updates)`
Update a habit based on outcomes.

**Parameters:**
- `habit_id` (str): Habit ID
- `updates` (dict): Updates to apply

### `get_stats()`
Get habit formation statistics.

**Returns:** HabitForgeStats {
    pattern_count: int,
    habit_count: int,
    hit_rate: float,
    success_rate: float
}
