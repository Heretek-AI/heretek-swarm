# Heretek Swarm Setup Wizard - E2E Test Plan

## Overview

This test plan covers the Setup Wizard flow for heretek-swarm dashboard, validating all configuration steps, error handling, and integration with backend services.

**Stack under test:**
- Frontend: React/Vite on `localhost:3000`
- Backend API: FastAPI on `localhost:8000`
- Database: PostgreSQL (port 5432)
- Cache: Redis (port 6379)
- Vector DB: Qdrant (port 6333)
- Message Broker: NATS (port 4222)

**Prerequisites:**
```bash
# Docker is accessible without password
# .env file is populated with API keys

# Start core services
docker compose up -d

# Verify services are running
curl http://localhost:8000/api/health
curl http://localhost:3000
```

---

## Test Environment Setup

### 1. Browser & Tools
- Chrome DevTools MCP available for debugging
- Playwright for browser automation
- Network tab for API inspection

### 2. Test Users
- API Key from `.env`: `HERETEK_API_KEY=htsk_42a231c6b47abf4cffd8bbe842789fbf`

### 3. Pre-conditions
- Clear localStorage before each test:
```javascript
localStorage.clear();
```

---

## Wizard Step Flow

```
welcome → api-endpoint → api-key → database-test → agent-health → complete
```

---

## Test Cases

### TC-001: First-Time Setup Flow (Happy Path)

**Objective:** Verify complete wizard flow with valid configuration

**Steps:**
1. Clear browser localStorage
2. Navigate to `http://localhost:3000`
3. Verify Welcome screen appears with "Get Started" button
4. Click "Get Started"
5. Verify API Endpoint step appears
6. Enter: `http://localhost:8000`
7. Click "Continue"
8. Verify API Key step appears
9. Enter API key from `.env`
10. Click "Continue"
11. Verify Database Test step runs automatically
12. Wait for connection success
13. Verify Agent Health step runs automatically
14. Wait for agent status display
15. Verify Completion screen appears
16. Verify dashboard loads

**Expected Results:**
- All steps complete without error
- localStorage contains `swarm_configured=true`
- System health shows green/healthy

**Acceptance Criteria:**
- [ ] Wizard completes in < 60 seconds
- [ ] All status indicators show success
- [ ] No console errors

---

### TC-002: API Endpoint Validation

**Objective:** Validate URL input handling and error states

**Test Data:**
| Input | Expected Behavior |
|-------|------------------|
| `http://localhost:8000` | Valid - continue enabled |
| `http://192.168.1.100:8000` | Valid - continue enabled |
| `https://api.example.com` | Valid - continue enabled |
| `localhost:8000` | Auto-adds http:// - valid |
| `192.168.1.100:8000` | Auto-adds http:// - valid |
| `invalid-url` | Error: "Invalid URL format" |
| `` (empty) | Error: "API host is required" |
| `ftp://localhost:8000` | Valid - continues |

**Steps (for empty input):**
1. Navigate to API Endpoint step
2. Leave field empty
3. Click "Continue"
4. Verify error message appears
5. Verify button is disabled or shows error state

**Acceptance Criteria:**
- [ ] URL normalization works correctly
- [ ] Protocol validation works
- [ ] Empty state handled gracefully

---

### TC-003: API Key Validation

**Objective:** Verify API key format and authentication

**Test Data:**
| Input | Expected Behavior |
|-------|------------------|
| `htsk_42a231c6b47abf4cffd8bbe842789fbf` | Valid - continues |
| `sk-minimal` | Valid - short but accepted |
| `` (empty) | Error: "API key is required" |
| `abc` | Error: "API key is too short" |

**Steps:**
1. Navigate to API Key step with valid endpoint
2. Enter invalid key `invalid-key-123`
3. Verify "Continue" shows error or loading
4. Verify error: "Invalid API key"
5. Clear and enter valid key
6. Verify continuation

**Bug Testing:**
- [ ] Check if error message is user-friendly
- [ ] Check if invalid key is cleared from memory after error

---

### TC-004: Database Connection Failure

**Objective:** Verify behavior when database services are unavailable

**Setup:**
1. Stop postgres container: `docker compose stop postgres`
2. Or block port 5432

**Steps:**
1. Start wizard with valid API endpoint
2. Enter valid API key
3. Reach Database Test step
4. Observe connection attempt

**Expected Results:**
- Timeout after ~10 seconds
- Error message: "Failed to connect" or service-specific error
- Option to retry or go back

**Acceptance Criteria:**
- [ ] Timeout handled gracefully
- [ ] User can retry without refreshing page
- [ ] Clear error message with service name

---

### TC-005: WebSocket Connection Test

**Objective:** Verify WS connectivity check in validation

**Steps:**
1. Complete API endpoint + key steps
2. Observe WebSocket test in Network tab
3. Verify `ws://localhost:8000/ws` connection attempt

**Expected Behavior:**
```javascript
// Derived from HTTP URL
http://localhost:8000 → ws://localhost:8000/ws
```

**Acceptance Criteria:**
- [ ] WS URL is correctly derived
- [ ] Connection failure doesn't block wizard (WS optional?)
- [ ] Console shows WebSocket error if fails

---

### TC-006: Agent Health Check

**Objective:** Verify agent discovery and status display

**Steps:**
1. Complete setup to Agent Health step
2. Wait for `/api/agents/instances` call
3. Verify agents are listed
4. Check for agent types: supervisor, examiner, prism, perceiver

**Expected API Response:**
```json
{
  "instances": [
    {
      "instance_id": "supervisor-001",
      "agent_type": "supervisor",
      "state": "running",
      "actor_status": {
        "message_count": 42,
        "last_activity": "2026-04-13T12:00:00Z"
      }
    }
  ]
}
```

**Acceptance Criteria:**
- [ ] Agent list populates within 15 seconds
- [ ] Status badges show correct colors (green=online, red=offline)
- [ ] Error count displayed if any

---

### TC-007: Network Error Recovery

**Objective:** Verify resilience to network interruptions

**Steps:**
1. Complete first two wizard steps
2. While on Database Test, disconnect network
3. Verify error handling
4. Reconnect network
5. Verify "Retry" works

**Tools:**
- Chrome DevTools → Network → "Offline" checkbox
- Or: `docker compose stop redis` (causes cascading failures)

**Acceptance Criteria:**
- [ ] No white screen of death
- [ ] Error toast appears
- [ ] Retry mechanism works

---

### TC-008: Wizard Reset from Settings

**Objective:** Verify Reset Configuration triggers wizard

**Steps:**
1. Complete wizard successfully
2. Navigate to Settings
3. Click "Reset Configuration"
4. Confirm reset
5. Verify wizard re-appears at Welcome step

**Code Path:**
```javascript
// In SettingsPage
resetSetup() → sets isRerunning=true
// In App.tsx
{showSetup && <SetupWizard onComplete={handleSetupComplete} />}
```

**Acceptance Criteria:**
- [ ] localStorage cleared
- [ ] Wizard shows Welcome step
- [ ] Previous config not pre-populated

---

### TC-009: Browser Refresh Persistence

**Objective:** Verify state persists across refresh

**Steps:**
1. Complete wizard to Agent Health step
2. Refresh browser
3. Verify wizard state preserved
4. OR: Verify redirects to last step

**Expected Behavior:**
- If `swarm_configured=true` in localStorage, skip to dashboard
- OR: Resume at current step

**Acceptance Criteria:**
- [ ] No data loss on refresh
- [ ] No infinite redirect loops
- [ ] Network requests complete

---

### TC-010: Concurrent API Calls

**Objective:** Verify no race conditions in validation

**Steps:**
1. Type rapidly in API endpoint field
2. Debounce should prevent excessive calls
3. Check Network tab for overlapping requests

**Expected:**
- Maximum 1 validation request at a time
- 500ms debounce delay
- Last valid input used

**Acceptance Criteria:**
- [ ] No 401/403 errors from stale requests
- [ ] No "field cleared while typing" bugs
- [ ] Loading spinner shows during validation

---

### TC-011: CORS and Preflight

**Objective:** Verify cross-origin requests work

**Setup:**
1. Change frontend to `localhost:3001`
2. Keep API at `localhost:8000`

**Steps:**
1. Complete wizard
2. Verify OPTIONS preflight requests succeed
3. Check console for CORS errors

**Expected Headers:**
```http
Access-Control-Allow-Origin: http://localhost:3001
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```

**Acceptance Criteria:**
- [ ] No CORS errors in console
- [ ] Preflight completes successfully

---

### TC-012: Latency Display

**Objective:** Verify connection latency is shown

**Steps:**
1. Complete wizard
2. Observe latency on success states

**Expected Format:**
```
✓ Connected (23ms)
✓ Database: postgres: ✓ connected (45ms)
```

**Acceptance Criteria:**
- [ ] Latency shown in milliseconds
- [ ] Timeout shows "Timed out" not infinity

---

### TC-013: Error State Recovery

**Objective:** Verify user can recover from error states

**Steps:**
1. Enter invalid API endpoint
2. Observe error
3. Fix endpoint
4. Verify error clears
5. Verify continue works

**Acceptance Criteria:**
- [ ] Error clears on valid input
- [ ] No stuck error states
- [ ] Clear validation on re-type

---

### TC-014: Wizard Navigation

**Objective:** Verify back/forward navigation works

**Steps:**
1. Complete welcome + api-endpoint
2. Click "Back"
3. Verify api-endpoint is pre-populated
4. Click "Continue"
5. Verify at api-key step

**Edge Cases:**
- [ ] Can't go back from welcome
- [ ] Forward only works if current step valid
- [ ] Step indicators clickable (if implemented)

---

### TC-015: Component Error Boundary

**Objective:** Verify errors don't crash entire app

**Steps:**
1. Introduce artificial error (disable JS, or mock failure)
2. Verify ErrorBoundary catches it
3. Verify "Something went wrong" UI shows
4. Verify retry/exit options

**Acceptance Criteria:**
- [ ] No white screen
- [ ] ErrorBoundary wrapper works
- [ ] User can recover

---

## Bug Scenarios

### BUG-001: Setup Wizard Crash on Type
**Symptom:** Wizard crashes when typing in API Host URL field
**Test:** TC-002 with rapid typing
**Root Cause:** Could be state update during render, or missing null check

### BUG-002: Stale Build Served
**Symptom:** Fixes don't appear after rebuild
**Test:** Rebuild, clear cache, check bundle hash
**Verification:** Network tab shows new `index-*.js` hash

### BUG-003: Health Check Timeout
**Symptom:** /api/health never returns
**Test:** TC-004 with service down
**Expected:** 10 second timeout, then error

### BUG-004: localStorage Corruption
**Symptom:** Setup loops infinitely
**Test:** TC-009, corrupt localStorage manually
**Fix:** Clear localStorage, restart

---

## Playwright Test Template

```typescript
// tests/e2e/setup-wizard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Setup Wizard E2E', () => {

  test.beforeEach(async ({ page }) => {
    // Clear storage and navigate
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
  });

  test('TC-001: Complete happy path setup', async ({ page }) => {
    // Welcome screen
    await expect(page.getByText('Get Started')).toBeVisible();
    await page.getByText('Get Started').click();

    // API Endpoint
    await page.getByLabel(/api.*endpoint/i).fill('http://localhost:8000');
    await page.getByRole('button', { name: 'Continue' }).click();

    // API Key
    await page.getByLabel(/api.*key/i).fill('htsk_42a231c6b47abf4cffd8bbe842789fbf');
    await page.getByRole('button', { name: 'Continue' }).click();

    // Database Test (auto-runs)
    await expect(page.getByText(/database/i)).toBeVisible();

    // Agent Health (auto-runs)
    await expect(page.getByText(/agent.*health/i)).toBeVisible();

    // Complete
    await expect(page.getByText(/success|complete/i)).toBeVisible();
  });

  test('TC-002: Invalid URL shows error', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.getByText('Get Started').click();

    await page.getByLabel(/api.*endpoint/i).fill('invalid-url');
    await expect(page.getByText(/invalid.*url/i)).toBeVisible();
  });
});
```

---

## Execution Commands

```bash
# Start services
docker compose up -d

# Run single test
npx playwright test tests/e2e/setup-wizard.spec.ts --grep "TC-001"

# Run with headed browser
npx playwright test tests/e2e/setup-wizard.spec.ts --headed

# Generate report
npx playwright show-report

# Debug specific test
npx playwright test tests/e2e/setup-wizard.spec.ts --grep "TC-005" --debug
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Test Coverage | All TC-* cases |
| Execution Time | < 5 min for full suite |
| Flakiness Rate | < 5% |
| Browser Support | Chrome, Firefox, Safari |

---

## Troubleshooting

### Services not responding
```bash
docker compose ps
docker compose logs heretek-api
docker compose logs heretek-frontend
```

### Port conflicts
```bash
lsof -i :3000
lsof -i :8000
```

### Clear everything
```bash
docker compose down -v
docker compose up -d
# Clear browser cache and localStorage
```
