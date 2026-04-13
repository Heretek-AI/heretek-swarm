# Canvas Feature Integration Plan

**Date:** 2026-04-13  
**Status:** Planning  
**Priority:** MEDIUM  
**Effort:** 4-8 hours total

---

## Context

EnhancedCanvas.tsx (707 lines) contains features not in Canvas.tsx (150 lines). FlowCanvas.tsx (642 lines) has multi-node type support but no consciousness/swarm metrics overlay. The goal is to consolidate high-value features into a unified canvas experience.

---

## Feature Analysis

| Feature | Source | Effort | Value | Notes |
|---------|--------|--------|-------|-------|
| Consciousness metrics overlay | EnhancedCanvas | LOW | HIGH | Uses /api/consciousness endpoint |
| Swarm health metrics | EnhancedCanvas | LOW | MEDIUM | Displays agent health data |
| Multi-node types | FlowCanvas | MEDIUM | HIGH | Agent, Tool, LLM, Memory, Decision, Connector |
| Workflow execution progress | EnhancedCanvas | MEDIUM | MEDIUM | Requires backend SSE event stream |

---

## Recommended Integration Approach

### Phase 1: Add Consciousness Metrics Overlay to Canvas.tsx

**Effort:** ~1 hour | **Priority:** HIGH

1. Add `ConsciousnessMetrics` interface to Canvas.tsx
2. Create `useConsciousnessMetrics` hook (poll /api/consciousness every 10s)
3. Add metrics overlay panel component
4. Style with dark theme matching existing canvas

```typescript
interface ConsciousnessMetrics {
  phi_score: number;
  phi_avg: number;
  phi_max: number;
  free_energy_avg: number;
  integration_level: number;
}
```

### Phase 2: Add Swarm Health Metrics Panel

**Effort:** ~1 hour | **Priority:** MEDIUM

1. Add `SwarmHealthMetrics` interface to Canvas.tsx
2. Create `useSwarmHealth` hook (reuse existing agent polling)
3. Add health panel below/beside consciousness metrics
4. Include: overall_health_score, active/idle agents, task completion

### Phase 3: Integrate Multi-Node Types from FlowCanvas

**Effort:** ~3 hours | **Priority:** MEDIUM

1. Import node components from FlowCanvas/WorkflowBuilder
2. Add node type registry to Canvas.tsx
3. Update AgentNode to handle different node types
4. Add type-specific icons and colors

**Node types to support:**
- `agentNode` - Agent (existing)
- `toolNode` - Tool execution
- `llmNode` - LLM processing
- `memoryNode` - Memory operations
- `decisionNode` - Conditional branching
- `connectorNode` - Connection/handoff

### Phase 4: Add Workflow Execution Progress

**Effort:** ~3 hours | **Priority:** MEDIUM

1. Add `Workflow` and `ExecutionState` interfaces
2. Create SSE connection to /api/workflow/events (backend needed)
3. Track active execution state
4. Display progress in overlay panel

**Note:** Requires backend endpoint for workflow execution events.

---

## Implementation Order

1. **Canvas.tsx** - Add consciousness metrics (lowest risk, highest visible value)
2. **Canvas.tsx** - Add swarm health panel
3. **FlowCanvas.tsx** - Extract shared node types OR import into Canvas.tsx
4. **Backend** - Add workflow SSE endpoint (can be separate PR)
5. **Canvas.tsx** - Integrate workflow progress when backend ready

---

## Alternative: Progressive Enhancement

Instead of modifying Canvas.tsx directly, create a wrapper:

```tsx
// CanvasWrapper.tsx
<Canvas>
  <MetricsOverlay />
  <SwarmHealthPanel />
</Canvas>
```

This keeps Canvas.tsx unchanged while adding features as overlays/toggles.

---

## Files to Modify

| File | Changes |
|------|---------|
| `Canvas.tsx` | Add consciousness metrics, swarm health |
| `Canvas/index.ts` | Export MetricsOverlay, SwarmHealthPanel |
| `FlowCanvas.tsx` | Import if reusing node types |
| `WorkflowBuilder/*.tsx` | Import node components |
| `hooks/useConsciousnessMetrics.ts` | New hook |
| `hooks/useSwarmHealth.ts` | New hook |

---

## Verification

1. Run `npm run build` - must pass
2. Run `npm run lint` - no new warnings
3. Canvas renders with metrics overlay
4. Node types render correctly
5. No runtime errors in browser console

---

## Notes

- EnhancedCanvas.tsx is 707 lines of prototype code - some features may need refactoring
- FlowCanvas.tsx has good node type patterns we can replicate
- Backend /api/consciousness may need verification that it returns expected shape
- Consider feature flag for metrics overlay to avoid overwhelming users
