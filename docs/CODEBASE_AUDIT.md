# Heretek Swarm Codebase Audit Report

**Date:** 2026-04-13  
**Auditor:** Swarm Analysis Agent  
**Scope:** Full codebase (Backend Python + Frontend React/TypeScript + Docker infrastructure)

---

## Executive Summary

The Heretek Swarm codebase is a sophisticated multi-agent autonomous system with a React dashboard frontend and Python backend. The system has comprehensive architectural foundations but contains several **critical bugs** that render parts non-functional.

### System Health Score: 65/100

| Component | Status |
|----------|--------|
| Backend API | ⚠️ Functional but buggy |
| Frontend Dashboard | ⚠️ Functional with inconsistencies |
| NATS Event Mesh | ✅ Working |
| PostgreSQL | ⚠️ Partial (migration gaps) |
| Redis Cache | ✅ Working |
| Qdrant Vectors | ✅ Working |
| mem0 Memory | ⚠️ Partial (schema mismatches) |

---

## CRITICAL ISSUES

### Backend Critical Issues

#### 1. Workflow Storage Inconsistency (CRITICAL)
**File:** `backend/heretek_swarm/api/workflows.py`

```python
# Line 27: Stores workflows here
_workflows: Dict[str, Workflow] = {}

# Line 86: But list_workflows reads from engine.workflows (DIFFERENT dict)
workflows = list(engine.workflows.values())

# Line 186: delete_workflow deletes from _workflows but NOT engine.workflows
del _workflows[workflow_id]
```

**Impact:** Created workflows don't appear in list. Deleted workflows reappear.

#### 2. Workflow Malformed Execution ID (CRITICAL)
**File:** `backend/heretek_swarm/api/workflows.py`

```python
# Lines 210, 250
execution_id = f"exec_{workflow_id}_{workflow_id}"  # Bug!
```

**Impact:** Two different workflows can have conflicting execution IDs (`exec_abc_abc` vs `exec_xyz_xyz`).

#### 3. Silent Exception Swallowing (CRITICAL)
**File:** `backend/heretek_swarm/api/observability.py:167-168`

```python
except Exception:
    auto_agent_count = 0
```

**Impact:** Any import errors silently fail, making debugging impossible.

#### 4. RAG API Stub with No Fallback (CRITICAL)
**File:** `backend/heretek_swarm/api/rag.py:18-26`

```python
try:
    from rag.document_processor import ProcessingConfig
except ImportError:
    RAG_AVAILABLE = False  # No fallback, runtime will fail
```

**Impact:** API endpoints will crash at runtime if `rag` module not installed.

#### 5. Encryption Silently Disabled (CRITICAL)
**File:** `backend/heretek_swarm/config/encryption.py:48-64`

**Impact:** If `cryptography` package missing or key init fails, API keys stored in plaintext without explicit error.

---

### Frontend Critical Issues

#### 1. API Key Storage Key Inconsistency (CRITICAL - PARTIALLY FIXED)
**Files:** Multiple in `dashboard/frontend/src/`

| Key | Used By | Status |
|-----|---------|--------|
| `api_key` | Most components | ✅ Standard |
| `token` | EnhancedCanvas, ConsciousnessDashboard, AgentMetricsGrid | ❌ Inconsistent |
| `swarm_api_key` | setupStore.ts reset (line 234) | ⚠️ Legacy cleanup |

**Impact:** Token-based auth fails in some components; setupStore cleanup removes wrong key.

**Status:** As of 2026-04-13 4:54pm, setupStore.ts was fixed to use `api_key` consistently.

---

## HIGH PRIORITY ISSUES

### Backend High Issues

#### 1. Consensus Vote Agent ID Mismatch
**File:** `backend/heretek_swarm/api/consensus.py:331-335`

```python
agent_id = x_agent_id or authenticated_agent_id  # Uses one for vote
if not consensus_auth_manager.check_permission(authenticated_agent_id, "vote"):  # Different for permission
```

#### 2. State Repository Silent ImportError
**File:** `backend/heretek_swarm/state/repository.py:28-30`

```python
except ImportError:
    EVENT_SOURCING_AVAILABLE = False  # No alert, runtime will fail later
```

#### 3. Two Conflicting `get_config` Functions
**File:** `backend/heretek_swarm/config/loader.py`
- `ConfigLoader.get()` (line 305) - synchronous
- Module-level `get_config()` (line 490) - async

#### 4. Alerts API Missing Error Handling
**File:** `backend/heretek_swarm/api/alerts.py:86-91`
Returns 200 OK with `success=false` but no error explanation.

---

### Frontend High Issues

#### 1. Excessive `any` Type Usage
**Impact:** 50+ instances of `any` type breaking TypeScript safety.

Critical files:
- `api/configuration.ts:18` - `config_value: any`
- `components/WorkflowBuilder/types.ts` - multiple `config: Record<string, any>`
- `components/Canvas/FlowCanvas.tsx:107` - `React.FC<any>`

#### 2. Missing `api_url` but Never Written
**File:** `dashboard/frontend/src/components/UI/ComponentErrorBoundary.tsx:61-62`
```typescript
const apiKey = localStorage.getItem('api_key');
const apiUrl = localStorage.getItem('api_url') || '';  // api_url is NEVER set anywhere
```

#### 3. Two Overlapping Wizard Implementations
- `SetupWizard.tsx` (1186 lines) - uses setupStore
- `ConfigWizard.tsx` (1288 lines) - uses configWizardStore

---

## MEDIUM PRIORITY ISSUES

### Backend Medium Issues

| File | Issue |
|------|-------|
| `api/consensus.py` | Missing pagination on large collections |
| `api/workflows.py` | Workflow validation checks engine.workflows but creates in `_workflows` |
| `gateway/a2a_server.py` | Unused agent metadata in handshake |

### Frontend Medium Issues

| File | Issue |
|------|-------|
| Multiple Settings components | `catch (error: any)` should narrow error type |
| `api/wizard.ts`, `App.tsx` | API URL from different sources |
| `stores/setupStore.ts` | Still reads `swarm_api_key` on reset |

---

## INCOMPLETE/PLACEHOLDER MODULES

### Backend Placeholders

| File | Placeholder |
|------|-------------|
| `actors/stubs.py` | Explicit stub module returning None |
| `actors/perceiver.py` | Audio/video/document feature extraction marked as needing external libraries |
| `actors/sentinel.py` | Policy rule check returns None (no violations) |
| `actors/profiling.py` | `cleanup_old_data()` marked as placeholder |

### Frontend Placeholders

| File | Placeholder |
|------|-------------|
| `hooks/__tests__/useAgentHandles.test.tsx` | Placeholder tests with TODO comments |
| `components/Canvas/useMetrics.ts` | Only 18 lines, appears minimal/truncated |

---

## HALF-COMPLETED FEATURES REQUIRING DECISION

### 1. RAG Module (`backend/heretek_swarm/api/rag.py`)
**Status:** Stub implementation - imports fail if `rag` package not installed.
**Decision Needed:** Either install `rag` package or remove RAG endpoints entirely.

### 2. Audio/Video Processing (`actors/perceiver.py`)
**Status:** Feature extraction methods note needing `librosa`, `opencv-python`, `PyPDF2`.
**Decision Needed:** Install dependencies or document as future enhancement.

### 3. Dual Wizard Implementation
**Status:** Two overlapping wizards exist.
**Decision Needed:** Merge into single wizard or document why both are needed.

### 4. mem0 Integration
**Status:** Partial implementation with schema mismatches.
**Decision Needed:** Complete integration or use alternative memory system.

---

## FILES REQUIRING IMMEDIATE ATTENTION

### Fix First (Priority 1)

1. `backend/heretek_swarm/api/workflows.py` - Storage inconsistency + malformed execution_id
2. `backend/heretek_swarm/api/observability.py` - Silent exception swallowing
3. `backend/heretek_swarm/api/rag.py` - Add RAG_AVAILABLE check before using imports
4. `dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx` - Change `token` to `api_key`

### Fix Second (Priority 2)

5. `backend/heretek_swarm/config/encryption.py` - Fail explicitly if encryption disabled
6. `backend/heretek_swarm/state/repository.py` - Add warning if EVENT_SOURCING_AVAILABLE=False
7. `backend/heretek_swarm/api/consensus.py` - Fix agent_id mismatch in vote
8. `dashboard/frontend/src/` - Reduce `any` type usage

### Document Later (Priority 3)

9. Merge or document dual wizard purpose
10. Audio/video processing decision (librosa/opencv)
11. RAG module decision

---

## RECOMMENDATIONS

### Immediate Actions

1. **Fix workflow storage** - Unify storage to use `engine.workflows` consistently
2. **Fix execution_id** - Use proper unique ID generation
3. **Add error alerts** - Replace silent exception handling with logging
4. **Standardize API key** - Ensure all frontend components use `api_key` consistently
5. **Add RAG guard** - Check `RAG_AVAILABLE` before using in endpoints

### Medium Term

1. Replace `any` types with proper TypeScript types
2. Add pagination to list endpoints
3. Merge duplicate wizards or document purpose
4. Complete mem0 integration or remove

### Long Term

1. Add event sourcing persistence (currently in-memory only)
2. Complete consciousness metrics (FEP calculation)
3. Add comprehensive error boundaries in frontend

---

## TESTING STATUS

- Backend unit tests: ~385 errors need fixing
- Frontend tests: Placeholder tests exist, not fully implemented
- Integration tests: Partially complete
- E2E tests: Not present

---

## DOCUMENTATION STATUS

| Document | Status |
|----------|--------|
| ARCHITECTURE_REALITY.md | ✅ Current - 2026-04-07 |
| MAIN_PROMPT.md | ⚠️ Needs update |
| API Endpoints | ✅ Documented |
| Deployment guides | ✅ Docker + K8s configs exist |

---

*End of Audit Report*
