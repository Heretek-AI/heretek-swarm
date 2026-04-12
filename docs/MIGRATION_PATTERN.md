# Mixin Migration Pattern

This document describes the pattern for extracting shared functionality into mixins and refactoring actors to use them.

## Why Mixins

### Problems Mixins Solve

1. **Code Duplication**: When multiple actors implement the same functionality (e.g., pattern emission, deliberation, memory tracking), mixins eliminate copy-paste duplication.

2. **Actor Sovereignty**: Each actor retains full control over its behavior. Mixins are optional traits, not mandatory inheritance chains.

3. **Consistency**: All actors using `MemoryMixin` track memory access the same way. Changes to the mixin propagate to all consuming actors.

4. **Maintainability**: Bug fixes in a mixin fix all actors at once. New features can be added to mixins without touching actor code.

### When to Create a Mixin

Create a mixin when:
- 3+ actors have identical or near-identical methods
- The shared code is a cross-cutting concern (memory, patterns, deliberation)
- The functionality is optional (actors can exist without it)

### When NOT to Create a Mixin

Do NOT create a mixin when:
- The code is specific to a single actor's domain
- The shared code would be empty for some actors
- The behavior requires different implementations per actor

---

## Available Mixins

| Mixin | Purpose | Files |
|-------|---------|-------|
| `MemoryMixin` | Memory access tracking, tier management, prefetching | `actors/mixins/memory.py` |
| `DeliberationMixin` | Deliberation participation, position submission | `actors/mixins/deliberation.py` |
| `PatternMixin` | Pattern emission and consumption | `actors/mixins/pattern.py` |
| `LearningMixin` | Learning state, adaptation metrics, performance tracking | `actors/mixins/learning.py` |

---

## How to Extract a New Mixin

### Step 1: Identify Shared Behavior

Compare actor methods and find common patterns:

```python
# In MetisAgent
async def _emit_pattern(self, pattern_type, pattern_data, ...):
    pattern_id = f"pattern_{self.agent_id}_{time()}"
    self._emitted_patterns.append(pattern_id)
    ...

# In PerceiverAgent (same method, same signature)
async def _emit_pattern(self, pattern_type, pattern_data, ...):
    pattern_id = f"pattern_{self.agent_id}_{time()}"
    self._emitted_patterns.append(pattern_id)
    ...
```

### Step 2: Create the Mixin File

Create `src/heretek_swarm/actors/mixins/<name>.py`:

```python
"""
<Name>Mixin - <Brief description>.

Methods:
    _<method_name>: <Description>

Version: 1.44.0
"""

import asyncio
from typing import Any
import structlog

logger = structlog.get_logger("<Name>Mixin")


class <Name>Mixin:
    """
    Mixin providing <description>.

    Actors with this mixin can <what actors can do>.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize <name> state."""
        super().__init__(*args, **kwargs)
        self._<state_attr>: <type> = <default>

    async def _<method_name>(
        self,
        param: str,
    ) -> <return_type>:
        """
        <Method description>.

        Args:
            param: <Param description>

        Returns:
            <Return description>
        """
        # Implementation
        return result
```

### Step 3: Export from `__init__.py`

Update `src/heretek_swarm/actors/mixins/__init__.py`:

```python
from heretek_swarm.actors.mixins.memory import MemoryMixin
from heretek_swarm.actors.mixins.deliberation import DeliberationMixin
from heretek_swarm.actors.mixins.pattern import PatternMixin
from heretek_swarm.actors.mixins.learning import LearningMixin

__all__ = [
    "MemoryMixin",
    "DeliberationMixin",
    "PatternMixin",
    "LearningMixin",
]
```

---

## How to Refactor an Actor to Use Mixins

### Step 1: Identify Mixin Methods to Remove

For each mixin method the actor already implements:

1. Remove the method implementation from the actor
2. Remove any state attributes initialized for that method
3. Remove any imports only used by that method

### Step 2: Add Mixin to Inheritance

```python
# Before
class MetisAgent(AgentActor):

# After
class MetisAgent(AgentActor, MemoryMixin, DeliberationMixin, PatternMixin, LearningMixin):
```

### Step 3: Ensure `__init__` Calls Super

The base `AgentActor.__init__` must be called before mixin initialization:

```python
def __init__(self, config: AgentConfig) -> None:
    AgentActor.__init__(self, config)  # Base first
    MemoryMixin.__init__(self)        # Then mixins
    DeliberationMixin.__init__(self)
    PatternMixin.__init__(self)
    LearningMixin.__init__(self)
```

### Step 4: Update Type Annotations

If the actor has type checking enabled, ensure mypy understands the mixin attributes:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from heretek_swarm.actors.mixins import MemoryMixin

class MetisAgent(AgentActor, MemoryMixin, ...):
    _memory_access_count: dict[str, int]  # Remove - now in mixin
```

---

## Size Rules

| Rule | Limit | Reason |
|------|-------|--------|
| **Mixin file** | < 200 lines | Small, focused, single responsibility |
| **Actor file** | < 500 lines | Complex enough to need actors, simple enough to understand |

### Enforcement

- Mixins are checked at 200 lines. If a mixin exceeds this, split it.
- Actors are checked at 500 lines. If an actor exceeds this, extract more methods into mixins or split into smaller actors.

### Line Count Quick Check

```bash
wc -l src/heretek_swarm/actors/mixins/*.py
wc -l src/heretek_swarm/actors/*.py
```

---

## Pattern Examples

### MemoryMixin Usage

```python
# In any actor with MemoryMixin:
await self._track_memory_access("key", "read")
tier = self._get_memory_tier("key")
prefetched = await self._prefetch_relevant(context, limit=5)
stats = self._get_memory_stats()
```

### PatternMixin Usage

```python
# In any actor with PatternMixin:
pattern_id = await self._emit_pattern(
    pattern_type=PatternType.SOLUTION,
    pattern_data={"approach": "recursive"},
    confidence=0.8,
)
patterns = await self._consume_patterns(min_confidence=0.7)
```

### DeliberationMixin Usage

```python
# In any actor with DeliberationMixin:
delib_id = await self._initiate_deliberation("best_approach", timeout=30.0)
await self._submit_deliberation_position(delib_id, {"vote": "option_a"})
result = await self._finalize_deliberation(delib_id, outcome="option_a")
```

### LearningMixin Usage

```python
# In any actor with LearningMixin:
status = await self.get_learning_status()
await self.record_learning_signal("reward", 0.5)
await self.update_adaptation(0.1)
metrics = await self.get_performance_metrics()
```

---

## Actors Currently Using Mixins

| Actor | Mixins Used |
|-------|-------------|
| `MetisAgent` | MemoryMixin, DeliberationMixin, PatternMixin, LearningMixin |
| `PerceiverAgent` | MemoryMixin, DeliberationMixin, PatternMixin, LearningMixin |
| `EmpathAgent` | MemoryMixin, DeliberationMixin, PatternMixin, LearningMixin |
| `HistorianAgent` | MemoryMixin, DeliberationMixin, PatternMixin, LearningMixin |

---

## Migration Checklist

When refactoring an actor to use mixins:

- [ ] Identify methods that exist identically in 3+ actors
- [ ] Create mixin file under 200 lines
- [ ] Export mixin from `mixins/__init__.py`
- [ ] Add mixin to class inheritance
- [ ] Ensure `__init__` calls `super().__init__` before mixin `__init__`
- [ ] Remove duplicated methods from actor
- [ ] Remove orphaned imports from actor
- [ ] Verify actor file is under 500 lines
- [ ] Run tests to verify behavior unchanged
