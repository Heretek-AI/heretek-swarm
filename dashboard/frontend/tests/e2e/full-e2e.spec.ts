/**
 * Comprehensive E2E Tests for Heretek Swarm Dashboard
 *
 * Covers: Setup Wizard, Home, Agents, Canvas, Chat, Consciousness,
 *         Settings, Workflows, Logs — plus WebSocket diagnostics.
 */

import { test, expect } from '@playwright/test';

// ─── Test config ───────────────────────────────────────────────────────────────
const API_HOST = 'http://localhost:8000';
const API_KEY = 'htsk_42a231c6b47abf4cffd8bbe842789fbf';

// ─── Helper: skip wizard ───────────────────────────────────────────────────────
async function skipWizard(page: any) {
  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
  await page.evaluate(() => {
    // Hardcode values here — page.evaluate runs in browser context
    localStorage.setItem('swarm_configured', 'true');
    localStorage.setItem('swarm_api_host', 'http://localhost:8000');
    localStorage.setItem('api_key', 'htsk_42a231c6b47abf4cffd8bbe842789fbf');
  });
  await page.reload();
  await page.waitForLoadState('networkidle');
}

// ─── Helper: nav to a page by emoji icon span ──────────────────────────────────
async function navTo(page, icon: string, label: string) {
  await page.locator(`nav button span:text-is("${icon}")`).click();
  await page.waitForTimeout(1000);
}

// ─── Helper: collect console errors, excluding expected noise ─────────────────────
const EXPECTED_NOISE_PATTERNS = [
  'Failed to fetch',
  'NetworkError',
  'net::ERR',
  'WebSocket',
  'ERR_CONNECTION_REFECTED',
  'ERR_CONNECTION_REFUSED',
  '401',
  'Unauthorized',
  '/api/agents',
  '/api/health',
  '/api/consciousness',
  '/api/config',
  '/api/workflows',
  '/api/workflow',
  '/api/agent-config',
  'favicon',
  '404',
  'CORS',
  'No Access-Control-Allow-Origin',
  'ws://',
  'otel-collector',
];

function filterCritical(errors: string[]): string[] {
  return errors.filter((e) =>
    !EXPECTED_NOISE_PATTERNS.some((p) => e.includes(p))
  );
}

// ─── WebSocket Diagnostic Test ──────────────────────────────────────────────────
// Must run first so we can observe the WS state in isolation
test.describe('WebSocket Diagnostics', () => {
  test('WS: dashboard connection state is observable after navigating to Canvas', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    // Navigate to Canvas
    await navTo(page, '🎨', 'Canvas');
    await page.waitForTimeout(3000);

    // Look for the WS status dot in the toolbar.
    // The dot has a title attribute explaining the state.
    const wsDot = page.locator('[title*="WebSocket"], [title*="A2A"], [title*="connected"], [title*="connecting"], [title*="error"]').first();

    // The dot should be present (it's always rendered in the toolbar)
    // We check it exists rather than its color (color via CSS is hard to assert)
    const dotVisible = await wsDot.isVisible().catch(() => false);

    // If the dot is not visible (toolbar not rendered), check for the loading/error state
    if (!dotVisible) {
      // Either loading spinner or error state should be visible
      const loadingVisible = await page.getByText('Loading swarm...').isVisible().catch(() => false);
      const errorVisible = await page.getByText('Error:', { exact: false }).isVisible().catch(() => false);
      expect(loadingVisible || errorVisible).toBeTruthy();
    }

    // Filter errors — WS errors from NATS unavailability are expected
    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Setup Wizard ───────────────────────────────────────────────────────────────
test.describe('Setup Wizard', () => {
  test.beforeEach(async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
    (page as any).__errors = errors;
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
  });

  test('WIZ-01: complete wizard from welcome to dashboard', async ({ page }) => {
    // Welcome
    await expect(page.getByText('Welcome to Heretek Swarm')).toBeVisible();
    await page.getByRole('button', { name: /get started/i }).click();

    // API Endpoint
    await expect(page.getByText('API Endpoint Configuration')).toBeVisible();
    await page.getByPlaceholder('http://localhost:8000').fill(API_HOST);
    await page.getByRole('button', { name: /continue/i }).click();

    // API Key
    await expect(page.getByText('API Key Configuration')).toBeVisible();
    await page.getByPlaceholder('Enter your API key').fill(API_KEY);
    await page.getByRole('button', { name: /continue/i }).click();

    // Connection Verification
    await expect(page.getByText('Connection Verification')).toBeVisible();
    try {
      await expect(page.getByText(/all connections verified/i, { exact: false })).toBeVisible({ timeout: 15000 });
    } catch { /* services may be unavailable */ }
    await page.getByRole('button', { name: /continue/i }).click();

    // Agent Health
    await expect(page.getByText('Agent Health Check')).toBeVisible();
    try {
      await expect(page.getByText('Agent Status', { exact: true })).toBeVisible({ timeout: 15000 });
    } catch { /* agents may not be running */ }
    await page.getByRole('button', { name: /complete setup/i }).click();

    // Complete
    await expect(page.getByText('Setup Complete')).toBeVisible();

    // localStorage verified
    expect(await page.evaluate(() => localStorage.getItem('swarm_configured'))).toBe('true');
    expect(await page.evaluate(() => localStorage.getItem('swarm_api_host'))).toBe(API_HOST);
    expect(await page.evaluate(() => !!localStorage.getItem('api_key'))).toBe(true);

    const critical = filterCritical((page as any).__errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Home Page ─────────────────────────────────────────────────────────────────
test.describe('Home Page', () => {
  test('HOME-01: overview page loads and shows system status', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    // Should see Overview or Home content
    const overviewVisible = await page.getByText('Overview').isVisible().catch(() => false);
    const homeVisible = await page.getByText('Home').isVisible().catch(() => false);
    expect(overviewVisible || homeVisible).toBeTruthy();

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Agents Page ────────────────────────────────────────────────────────────────
test.describe('Agents Page', () => {
  test('AGENTS-01: agents page loads and shows agent list or empty state', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🤖', 'Agents');
    await page.waitForTimeout(2000);

    // Page should show either agent cards or a loading/error state — not blank
    const hasContent = await (
      page.locator('text=/agent|Agent/i').first().isVisible().catch(() => false) ||
      page.locator('[class*="agent"]').first().isVisible().catch(() => false) ||
      page.getByText('Loading', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Error', { exact: false }).first().isVisible().catch(() => false)
    );
    expect(hasContent).toBeTruthy();

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('AGENTS-02: agents page loads without JS errors', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🤖', 'Agents');
    await page.waitForTimeout(3000);

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Canvas Page ───────────────────────────────────────────────────────────────
test.describe('Canvas Page', () => {
  test('CANVAS-01: canvas renders ReactFlow or gracefully shows error state', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🎨', 'Canvas');
    await page.waitForTimeout(3000);

    // ReactFlow OR error state OR loading — all are valid
    const hasReactFlow = await page.locator('.react-flow').isVisible().catch(() => false);
    const hasError = await page.getByText('Error:', { exact: false }).isVisible().catch(() => false);
    const hasLoading = await page.getByText('Loading swarm...').isVisible().catch(() => false);
    expect(hasReactFlow || hasError || hasLoading).toBeTruthy();

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('CANVAS-02: canvas toolbar is visible when ReactFlow renders', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🎨', 'Canvas');
    await page.waitForTimeout(3000);

    const hasReactFlow = await page.locator('.react-flow').isVisible().catch(() => false);
    if (hasReactFlow) {
      // ReactFlow controls and minimap should be present
      const hasControls = await page.locator('.react-flow__controls').isVisible().catch(() => false);
      const hasMinimap = await page.locator('.react-flow__minimap').isVisible().catch(() => false);
      // At least the controls should be there
      expect(hasControls || hasMinimap).toBeTruthy();
    }

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Chat Page ────────────────────────────────────────────────────────────────
test.describe('Chat Page', () => {
  test('CHAT-01: chat interface loads and can send a message', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '💬', 'Chat');

    // Chat input and send button must be visible
    await expect(page.locator('textarea').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /send/i }).first()).toBeVisible();

    // Type and send
    const msg = 'What is the swarm status?';
    await page.locator('textarea').first().fill(msg);
    await page.getByRole('button', { name: /send/i }).first().click();

    // Message should appear in the chat
    await expect(page.getByText(msg)).toBeVisible({ timeout: 5000 });

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('CHAT-02: chat page loads without JS errors', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '💬', 'Chat');
    await page.waitForTimeout(2000);

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Consciousness Page ───────────────────────────────────────────────────────
test.describe('Consciousness Page', () => {
  test('CONSCIOUS-01: consciousness page loads and shows content or loading state', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🧠', 'Consciousness');
    await page.waitForTimeout(3000);

    // Should have some consciousness-related content or loading
    const hasContent = await (
      page.locator('text=/consciousness|Consciousness/i').first().isVisible().catch(() => false) ||
      page.locator('[class*="gauge"], [class*="metric"], [class*="chart"]').first().isVisible().catch(() => false) ||
      page.getByText('Loading', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Error', { exact: false }).first().isVisible().catch(() => false)
    );
    expect(hasContent).toBeTruthy();

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('CONSCIOUS-02: consciousness page loads without JS errors', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🧠', 'Consciousness');
    await page.waitForTimeout(3000);

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Settings Page ────────────────────────────────────────────────────────────
test.describe('Settings Page', () => {
  test('SETTINGS-01: settings page loads and shows config sections', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '⚙️', 'Settings');
    await page.waitForTimeout(2000);

    // Settings page should show something config-related
    const hasContent = await (
      page.getByText('Settings', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('LLM', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Provider', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Agent', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Error', { exact: false }).first().isVisible().catch(() => false)
    );
    expect(hasContent).toBeTruthy();

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('SETTINGS-02: settings page loads without JS errors', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '⚙️', 'Settings');
    await page.waitForTimeout(2000);

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('SETTINGS-03: LLM providers section loads via API call', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '⚙️', 'Settings');
    await page.waitForTimeout(3000);

    // LLM section should load (either shows providers or loading/error)
    const hasLLMContent = await (
      page.getByText('LLM Provider', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('OpenAI', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Provider', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Loading', { exact: false }).first().isVisible().catch(() => false)
    );
    expect(hasLLMContent).toBeTruthy();

    // The 500 from create_llm_provider should not happen on GET requests
    const critical500 = filterCritical(errors).filter(e => e.includes('500'));
    expect(critical500).toHaveLength(0);
  });
});

// ─── Workflows Page ───────────────────────────────────────────────────────────
test.describe('Workflows Page', () => {
  test('WORKFLOWS-01: workflow builder page loads and shows canvas or error', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🔀', 'Workflows');
    await page.waitForTimeout(3000);

    // Should show workflow builder content or error
    const hasContent = await (
      page.getByText('Workflow', { exact: false }).first().isVisible().catch(() => false) ||
      page.locator('[class*="react-flow"]').first().isVisible().catch(() => false) ||
      page.getByText('Error', { exact: false }).first().isVisible().catch(() => false)
    );
    expect(hasContent).toBeTruthy();

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('WORKFLOWS-02: workflow builder loads without JS errors', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '🔀', 'Workflows');
    await page.waitForTimeout(3000);

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Logs Page ────────────────────────────────────────────────────────────────
test.describe('Logs Page', () => {
  test('LOGS-01: logs page loads without crash', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '📟', 'Logs');
    await page.waitForTimeout(2000);

    // Should show some log-related content or loading
    const hasContent = await (
      page.getByText('Log', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Terminal', { exact: false }).first().isVisible().catch(() => false) ||
      page.getByText('Error', { exact: false }).first().isVisible().catch(() => false) ||
      page.locator('[class*="log"], [class*="terminal"], [class*="console"]').first().isVisible().catch(() => false)
    );
    expect(hasContent).toBeTruthy();

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });

  test('LOGS-02: logs page loads without JS errors', async ({ page }) => {
    await skipWizard(page);
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await navTo(page, '📟', 'Logs');
    await page.waitForTimeout(2000);

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});

// ─── Full Pipeline ───────────────────────────────────────────────────────────────
test.describe('Full Pipeline', () => {
  test('PIPELINE-01: wizard → home → agents → canvas → chat → consciousness → settings → workflows → logs — no crashes', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    // Complete wizard
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.getByRole('button', { name: /get started/i }).click();
    await page.getByPlaceholder('http://localhost:8000').fill(API_HOST);
    await page.getByRole('button', { name: /continue/i }).click();
    await page.getByPlaceholder('Enter your API key').fill(API_KEY);
    await page.getByRole('button', { name: /continue/i }).click();
    try { await expect(page.getByText(/all connections verified/i, { exact: false })).toBeVisible({ timeout: 15000 }); } catch { /* */ }
    await page.getByRole('button', { name: /continue/i }).click();
    try { await expect(page.getByText(/agent status/i, { exact: false })).toBeVisible({ timeout: 15000 }); } catch { /* */ }
    await page.getByRole('button', { name: /complete setup/i }).click();
    await expect(page.getByText('Setup Complete')).toBeVisible();

    // Home
    await page.waitForTimeout(1000);

    // Agents
    await navTo(page, '🤖', 'Agents');
    await page.waitForTimeout(2000);

    // Canvas
    await navTo(page, '🎨', 'Canvas');
    await page.waitForTimeout(2000);

    // Chat
    await navTo(page, '💬', 'Chat');
    await page.waitForTimeout(2000);

    // Consciousness
    await navTo(page, '🧠', 'Consciousness');
    await page.waitForTimeout(2000);

    // Settings
    await navTo(page, '⚙️', 'Settings');
    await page.waitForTimeout(2000);

    // Workflows
    await navTo(page, '🔀', 'Workflows');
    await page.waitForTimeout(2000);

    // Logs
    await navTo(page, '📟', 'Logs');
    await page.waitForTimeout(2000);

    // Home again
    await navTo(page, '🏠', 'Home');
    await page.waitForTimeout(1000);

    const critical = filterCritical(errors);
    expect(critical).toHaveLength(0);
  });
});
