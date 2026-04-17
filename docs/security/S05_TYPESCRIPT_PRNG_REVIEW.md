# TypeScript PRNG Security Review

## Overview

This document reviews the usage of `Math.random()` in TypeScript/React production code and categorizes each usage as either:
1. **Non-security-critical** - Used for UI/demo purposes only
2. **Replaced with crypto API** - Replaced with `crypto.getRandomValues()` for better randomness

## Audit Results

### Files with Math.random() Usage

| File | Instances | Purpose | Status |
|------|-----------|--------|--------|
| `A2ATracker.tsx` | ~28 | Demo/mock data generation | Documented |
| `ModelGarage.tsx` | 5 | UI mock metrics, simulated health checks | Documented |
| `Toast.tsx` | 1 | Toast ID generation | **Replaced** |
| `WorkflowBuilder.tsx` | 1 | Random node positioning | Documented |
| `useNodeGrouping.ts` | 1 | Group ID generation | **Replaced** |
| `LogsPage.tsx` | 0 | N/A | N/A |

### Detailed Analysis

#### 1. A2ATracker.tsx - Demo Mode Data Generation

**Purpose:** Generates fake agent-to-agent communication messages for the observability dashboard demo mode.

**Usage:** Random agent selection, message type selection, latency simulation, status randomization.

**Security Impact:** NONE - This is purely UI demo/mock data. Real A2A communication uses proper UUIDs and authentication via NATS.

**Action:** Added documentation header explaining non-security-critical usage.

#### 2. ModelGarage.tsx - UI Statistics Simulation

**Purpose:** Simulates provider health checks, latency measurements, and statistics updates for UI demonstration.

**Usage:** `Math.random()` used for:
- Simulated health test delays
- Random latency generation
- Statistics increment values
- Health status random assignment

**Security Impact:** NONE - These are mock values for UI display only. Real provider health checks connect to actual APIs.

**Action:** Added documentation header explaining non-security-critical usage.

#### 3. Toast.tsx - Toast ID Generation (REPLACED)

**Purpose:** Generates unique IDs for toast notifications.

**Action:** REPLACED `Math.random()` with `crypto.getRandomValues()`

**Before:**
```typescript
const id = Math.random().toString(36).substr(2, 9);
```

**After:**
```typescript
const array = new Uint8Array(9);
crypto.getRandomValues(array);
const id = Array.from(array, (b) => b.toString(36).padStart(2, '0')).join('').slice(0, 9);
```

**Rationale:** Toast IDs should have better uniqueness guarantees. While not security-critical, using crypto API provides better randomness for deduplication.

#### 4. WorkflowBuilder.tsx - Node Position Randomization

**Purpose:** Randomizes initial node positions on the canvas for visual variety.

**Security Impact:** NONE - Random positions are purely UI aesthetic, not used for any security decisions.

**Action:** Added documentation header explaining non-security-critical usage.

#### 5. useNodeGrouping.ts - Group ID Generation (REPLACED)

**Purpose:** Generates unique IDs for node groups.

**Action:** REPLACED `Math.random()` with `crypto.getRandomValues()`

**Before:**
```typescript
function generateGroupId(): string {
  return `group-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
```

**After:**
```typescript
function generateGroupId(): string {
  const array = new Uint8Array(9);
  crypto.getRandomValues(array);
  return `group-${Date.now()}-${Array.from(array, (b) => b.toString(36).padStart(2, '0')).join('').slice(0, 9)}`;
}
```

**Rationale:** Group IDs should have better uniqueness guarantees for React key prop optimization.

## Recommendations

1. **Demo/mock code should stay in demo mode** - If A2ATracker or ModelGarage add real API connections, they should use proper UUID generation (`crypto.randomUUID()` or `uuid` package).

2. **Consider using uuid package** - For production UUID generation, consider using `crypto.randomUUID()` (Node.js 19+, modern browsers) or the `uuid` package for broader compatibility.

3. **Audit third-party dependencies** - Check that any npm packages used don't introduce their own insecure random number generation.

## Verification Commands

```bash
# Check that documentation exists
test -f docs/security/S05_TYPESCRIPT_PRNG_REVIEW.md && echo "PASS: Documentation exists"

# Check that crypto replacement is in place
grep -c 'crypto.getRandomValues' \
  dashboard/frontend/src/components/UI/Toast.tsx \
  dashboard/frontend/src/hooks/useNodeGrouping.ts

# Check that demo usage is documented
grep -c 'demo\|mock\|non-security-critical' \
  dashboard/frontend/src/components/Observability/A2ATracker.tsx \
  dashboard/frontend/src/components/Settings/ModelGarage.tsx \
  dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx
```

## Date

Reviewed: April 16, 2026
Reviewed by: T04 (Automated security hotspot review)
