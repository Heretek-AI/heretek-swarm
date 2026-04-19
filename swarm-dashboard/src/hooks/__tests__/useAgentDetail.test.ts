/**
 * useAgentDetail Hook Tests
 *
 * Tests for the useAgentDetail polling hook covering:
 * - Skeleton/loading state when agentId is set
 * - Graceful "No metrics" on consciousness 404
 * - Polling stops when agentId becomes null (drawer closed)
 * - Polling restarts when agentId changes to a different agent
 * - Individual section errors don't crash other sections (Promise.allSettled)
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useAgentDetail } from '../../components/Canvas/useAgentDetail';

// ─── Mock the consciousness API module ────────────────────────────────────────
vi.mock('../../api/consciousness', () => ({
  getAgentMetrics: vi.fn(),
  getAgencyMetrics: vi.fn(),
}));

// ─── Mock the agents API module ───────────────────────────────────────────────
vi.mock('../../api/agents', () => ({
  getAgent: vi.fn(),
}));

// ─── Import mocked modules ────────────────────────────────────────────────────
import { getAgentMetrics, getAgencyMetrics } from '../../api/consciousness';
import { getAgent } from '../../api/agents';

const mockedGetAgentMetrics = vi.mocked(getAgentMetrics);
const mockedGetAgencyMetrics = vi.mocked(getAgencyMetrics);
const mockedGetAgent = vi.mocked(getAgent);

// ─── Mock data factories ─────────────────────────────────────────────────────
const mockAgentMetrics = {
  agent_id: 'agent-1',
  phi_score: 0.723,
  fep_metrics: {
    free_energy: 0.142,
    prediction_accuracy: 0.891,
    surprise: 0.033,
    belief_precision: 0.678,
  },
  state: 'coherent' as const,
  timestamp: new Date().toISOString(),
};

const mockAgencyMetrics = {
  agency_score: 0.847,
  autonomy_score: 0.623,
  decision_count: 42,
  last_decision: new Date().toISOString(),
};

const mockAgentInfo = {
  id: 'agent-1',
  type: 'steward',
  status: 'active',
  lastActivity: new Date().toISOString(),
};

// ─── Shared setup ─────────────────────────────────────────────────────────────
beforeEach(() => {
  vi.clearAllMocks();
  // Default: all calls succeed
  mockedGetAgentMetrics.mockResolvedValue(mockAgentMetrics);
  mockedGetAgencyMetrics.mockResolvedValue(mockAgencyMetrics);
  mockedGetAgent.mockResolvedValue(mockAgentInfo);
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('useAgentDetail', () => {
  it('renders with skeleton when agentId is set (loading state)', async () => {
    // Make the call hang so we can observe loading=true before it resolves
    let resolveMetrics: (value: typeof mockAgentMetrics) => void;
    mockedGetAgentMetrics.mockImplementation(
      () => new Promise((r) => { resolveMetrics = r; })
    );

    const { result } = renderHook(() => useAgentDetail('agent-1'));

    // Before any promise resolves, loading should be true (skeleton shown)
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);

    // Resolve and wait for state update
    await act(async () => {
      resolveMetrics!(mockAgentMetrics);
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data?.consciousness?.phi_score).toBeCloseTo(0.723);
  });

  it('shows graceful "no metrics yet" when consciousness endpoint returns 404', async () => {
    // Mock 404 — axios throws an error with the response object attached
    mockedGetAgentMetrics.mockRejectedValue(
      Object.assign(new Error('Request failed with status code 404'), {
        response: { status: 404 },
      })
    );
    mockedGetAgencyMetrics.mockResolvedValue(mockAgencyMetrics);
    mockedGetAgent.mockResolvedValue(mockAgentInfo);

    const { result } = renderHook(() => useAgentDetail('agent-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 404 → consciousness is null (not an error), agency still populated
    expect(result.current.data?.consciousness).toBe(null);
    expect(result.current.data?.agency?.agency_score).toBeCloseTo(0.847);
    // No consciousness error key (404 is graceful null)
    expect(result.current.errors.consciousness).toBeUndefined();
  });

  it('polling stops when agentId becomes null (drawer closed)', async () => {
    const { result, rerender } = renderHook(
      ({ id }: { id: string | null }) => useAgentDetail(id),
      { initialProps: { id: 'agent-1' } }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const callsBefore = mockedGetAgentMetrics.mock.calls.length;

    // Simulate drawer close → agentId becomes null
    rerender({ id: null });

    // State should reset immediately
    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBe(null);

    // Advance time well past the 10s polling interval — no new calls should fire
    await act(async () => {
      await new Promise((r) => setTimeout(r, 200));
    });

    expect(mockedGetAgentMetrics.mock.calls.length).toBe(callsBefore);
  });

  it('polling restarts when agentId changes to a different agent', async () => {
    const { result, rerender } = renderHook(
      ({ id }: { id: string | null }) => useAgentDetail(id),
      { initialProps: { id: 'agent-1' } }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const callsForAgent1 = mockedGetAgentMetrics.mock.calls.length;

    // Switch to a different agent
    rerender({ id: 'agent-2' });

    // Should immediately start fetching (loading resets)
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // New calls should have been made for agent-2
    const newCalls = mockedGetAgentMetrics.mock.calls.slice(callsForAgent1);
    expect(newCalls.length).toBeGreaterThan(0);
  });

  it('individual section errors do not crash other sections (Promise.allSettled)', async () => {
    // consciousness fails hard, agency succeeds, agent succeeds
    mockedGetAgentMetrics.mockRejectedValue(new Error('Network error'));
    mockedGetAgencyMetrics.mockRejectedValue(new Error('Agency network error'));
    mockedGetAgent.mockResolvedValue(mockAgentInfo);

    const { result } = renderHook(() => useAgentDetail('agent-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Both sections should have recorded errors
    expect(result.current.errors.consciousness).toBe('Network error');
    expect(result.current.errors.agency).toBe('Agency network error');
    // Agent succeeded despite the other failures
    expect(result.current.data?.agent?.type).toBe('steward');
    expect(result.current.data?.agency).toBe(null); // agency failed → null
    expect(result.current.data?.consciousness).toBe(null); // consciousness failed → null
  });

  it('gracefully handles partial failures — agency 404, consciousness ok', async () => {
    mockedGetAgentMetrics.mockResolvedValue(mockAgentMetrics);
    mockedGetAgencyMetrics.mockRejectedValue(
      Object.assign(new Error('Request failed with status code 404'), {
        response: { status: 404 },
      })
    );
    mockedGetAgent.mockResolvedValue(mockAgentInfo);

    const { result } = renderHook(() => useAgentDetail('agent-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Consciousness succeeded
    expect(result.current.data?.consciousness?.phi_score).toBeCloseTo(0.723);
    // Agency failed with 404
    expect(result.current.data?.agency).toBe(null);
    expect(result.current.errors.agency).toBe('Request failed with status code 404');
  });
});
