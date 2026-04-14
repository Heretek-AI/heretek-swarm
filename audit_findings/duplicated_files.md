# Duplicated Files Audit - Heretek-AI_heretek-swarm

**Generated:** 2026-04-13
**Project:** Heretek-AI_heretek-swarm
**Tool:** SonarQube Duplicated Files Analysis

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Duplicated Lines** | 5,203 |
| **Total Duplicated Blocks** | 166 |
| **Overall Duplication Density** | 2.1% |
| **Total Files with Duplication** | 56 |

---

## Priority 1: Critical Duplication (>80% density)

These files have severe duplication and should be prioritized for refactoring.

| File | Path | Duplicated Lines | Density | Blocks |
|------|------|-----------------|---------|--------|
| **triad.py** | src/heretek_swarm/actors/triad.py | 1,090 | 95.8% | 26 |
| **steward.py** | src/heretek_swarm/actors/steward.py | 285 | 83.3% | 6 |
| **beta.py** | src/heretek_swarm/actors/beta.py | 276 | 91.4% | 7 |
| **charlie.py** | src/heretek_swarm/actors/charlie.py | 271 | 91.2% | 7 |
| **alpha.py** | src/heretek_swarm/actors/alpha.py | 258 | 90.8% | 6 |
| **emergence_analyzer.py** | src/heretek_swarm/collective/emergence_analyzer.py | 80 | 83.3% | 1 |

### Priority 1 Refactoring Suggestions:

**1. triad.py, alpha.py, beta.py, charlie.py, steward.py**
- These actor files likely share a common base class pattern
- **Suggested Action:** Extract common behavior into a base actor class
- Create `src/heretek_swarm/actors/base.py` with shared methods
- Use inheritance or composition to eliminate duplication

**2. emergence_analyzer.py**
- **Suggested Action:** Review if analysis logic can be shared with `emergent_detection.py`

---

## Priority 2: High Duplication (40-80% density)

| File | Path | Duplicated Lines | Density | Blocks |
|------|------|-----------------|---------|--------|
| **LLMProvidersSection.tsx** | dashboard/frontend/src/components/Settings/LLMProvidersSection.tsx | 297 | 63.3% | 8 |
| **EmbeddingProvidersSection.tsx** | dashboard/frontend/src/components/Settings/EmbeddingProvidersSection.tsx | 279 | 56.9% | 7 |
| **ToolNode.tsx** | dashboard/frontend/src/components/WorkflowBuilder/ToolNode.tsx | 48 | 40.7% | 2 |
| **MemoryNode.tsx** | dashboard/frontend/src/components/WorkflowBuilder/MemoryNode.tsx | 48 | 44.0% | 2 |
| **ConnectorNode.tsx** | dashboard/frontend/src/components/WorkflowBuilder/ConnectorNode.tsx | 48 | 44.9% | 2 |
| **LLMNode.tsx** | dashboard/frontend/src/components/WorkflowBuilder/LLMNode.tsx | 48 | 43.6% | 2 |

### Priority 2 Refactoring Suggestions:

**Frontend Settings Components (LLMProvidersSection, EmbeddingProvidersSection)**
- Both settings sections likely share similar provider management UI
- **Suggested Action:** Extract common `ProviderCard` component
- Create shared `ProviderForm`, `ProviderList` components

**Workflow Builder Nodes (ToolNode, MemoryNode, ConnectorNode, LLMNode)**
- These node types share similar visual structure and behavior
- **Suggested Action:** Create a base `WorkflowNode` React component
- Use composition pattern with specialized content slots

---

## Priority 3: Moderate Duplication (10-40% density)

| File | Path | Duplicated Lines | Density | Blocks |
|------|------|-----------------|---------|--------|
| **emergent_detection.py** | src/heretek_swarm/collective/emergent_detection.py | 105 | 21.5% | 2 |
| **wire_agents.py** | scripts/wire_agents.py | 104 | 17.5% | 1 |
| **wire_agents_session44.py** | scripts/wire_agents_session44.py | 104 | 27.1% | 1 |
| **tracing.py** (otel) | src/heretek_swarm/infrastructure/otel/tracing.py | 87 | 20.8% | 1 |
| **tracing.py** (observability) | src/heretek_swarm/observability/tracing.py | 102 | 22.6% | 1 |
| **openai_provider.py** | src/heretek_swarm/llm/providers/openai_provider.py | 56 | 18.7% | 2 |
| **zai_provider.py** | src/heretek_swarm/llm/providers/zai_provider.py | 56 | 19.5% | 2 |
| **observability.py** | src/heretek_swarm/api/observability.py | 119 | 8.8% | 9 |
| **tools.py** | src/heretek_swarm/runtime/tools.py | 54 | 8.5% | 2 |
| **test_empath.py** | tests/actors/test_empath.py | 54 | 5.6% | 2 |
| **test_metis.py** | tests/actors/test_metis.py | 54 | 7.1% | 2 |
| **test_perceiver.py** | tests/actors/test_perceiver.py | 51 | 5.2% | 1 |

### Priority 3 Refactoring Suggestions:

**wire_agents.py vs wire_agents_session44.py**
- Nearly identical scripts with minor session-specific changes
- **Suggested Action:** Merge into single configurable script with session parameter

**tracing.py (duplicate implementations)**
- Two separate tracing implementations
- **Suggested Action:** Consolidate into single tracing module
- Use the `observability/tracing.py` as the canonical implementation

**LLM Providers (openai_provider.py, zai_provider.py)**
- Similar provider patterns
- **Suggested Action:** Ensure both use base provider abstraction correctly

**Test files (test_empath.py, test_metis.py, test_perceiver.py)**
- Similar test patterns across actor tests
- **Suggested Action:** Create test fixtures/base class for actor testing

---

## Priority 4: Low Duplication (<10% density)

| File | Path | Duplicated Lines | Density | Blocks |
|------|------|-----------------|---------|--------|
| **main_loop.py** | src/heretek_swarm/runtime/main_loop.py | 14 | 2.2% | 1 |
| **autonomous_runtime.py** | src/heretek_swarm/runtime/autonomous_runtime.py | 14 | 1.8% | 1 |
| **discord_bot.py** | src/heretek_swarm/integrations/discord_bot.py | 17 | 4.1% | 1 |
| **telegram_bot.py** | src/heretek_swarm/integrations/telegram_bot.py | 16 | 4.0% | 1 |
| **model_garage.py** | src/heretek_swarm/llm/model_garage.py | 19 | 2.1% | 1 |

### Priority 4 Notes:
- These are low priority but should be monitored
- Duplication may be acceptable if it's isolated utility code

---

## Duplicated File Groups (Potential Related Duplication)

### Group 1: Actor Files (alpha, beta, charlie, steward, triad)
- Pattern: High duplication suggests shared base implementation
- **Recommended:** Create actor base class with common lifecycle methods

### Group 2: Workflow Builder Nodes
- Files: ToolNode, MemoryNode, ConnectorNode, LLMNode, DecisionNode
- Pattern: Similar React node components for workflow builder
- **Recommended:** Create shared WorkflowNode base component with slot composition

### Group 3: Provider Settings Sections
- Files: LLMProvidersSection, EmbeddingProvidersSection
- Pattern: Similar settings UI for provider management
- **Recommended:** Extract common ProviderSettings base component

### Group 4: Tracing Implementations
- Files: observability/tracing.py, infrastructure/otel/tracing.py
- Pattern: Duplicate tracing code
- **Recommended:** Consolidate to single tracing module with conditional imports

### Group 5: Test Actor Files
- Files: test_empath.py, test_metis.py, test_perceiver.py
- Pattern: Similar test patterns for actor testing
- **Recommended:** Create shared test fixtures and base test class

### Group 6: Script Files
- Files: wire_agents.py, wire_agents_session44.py
- Pattern: Nearly identical scripts
- **Recommended:** Merge with session-specific configuration

---

## Recommended Refactoring Priority Order

1. **Immediate (P1):** Consolidate actor base class
   - Files: triad.py, steward.py, beta.py, charlie.py, alpha.py
   - Impact: ~2,180 duplicated lines

2. **High (P2):** Create shared frontend node components
   - Files: WorkflowBuilder node components
   - Impact: ~200 duplicated lines

3. **Medium (P3):** Consolidate tracing modules
   - Files: Two tracing.py implementations
   - Impact: ~190 duplicated lines

4. **Low (P4):** Merge script files
   - Files: wire_agents*.py
   - Impact: ~104 duplicated lines

---

## Estimated Total Deduplication Potential

If all recommendations are implemented: **~2,700 lines** could be eliminated through refactoring, representing **52%** of current duplicated lines.