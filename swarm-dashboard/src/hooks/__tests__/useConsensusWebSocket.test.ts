/**
 * useConsensusWebSocket Hook Tests
 *
 * Tests for consensus/deliberation event tracking via WebSocket:
 * - WebSocket message handling for consensus_vote, consensus_state_change,
 *   consensus_complete, deliberation_round, deliberation_position,
 *   deliberation_argument, and deliberation_finalized types
 * - Live consensus round tracking (votes, state, decision, red_flags)
 * - Live deliberation tracking (rounds, positions, consensus_score, finalization)
 * - Chronological event feed with capping
 * - Throttling behavior for 100ms intervals to prevent UI flicker
 * - Connection and error state propagation
 * - Non-consensus event types are ignored
 * - Events without required IDs are ignored
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import React from 'react';
import { useConsensusWebSocket } from '../useConsensusWebSocket';

// Mock the useWebSocket hook using Vitest
const mockUseWebSocket = vi.fn(() => ({
  connected: false,
  lastMessage: null,
  sendMessage: vi.fn(),
  disconnect: vi.fn(),
  reconnectAttempts: 0,
}));

vi.mock('../useWebSocket', () => ({
  useWebSocket: (...args: unknown[]) => mockUseWebSocket(...args),
}));

// Helper to get the onMessage callback registered by the hook
function getOnMessage(): (msg: Record<string, unknown>) => void {
  return mockUseWebSocket.mock.calls[0][1]?.onMessage;
}

describe('useConsensusWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ─── Initialization ──────────────────────────────────────────────────────

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useConsensusWebSocket());

    expect(result.current.consensusRounds.size).toBe(0);
    expect(result.current.deliberations.size).toBe(0);
    expect(result.current.eventFeed).toEqual([]);
    expect(result.current.connected).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.disconnect).toBe('function');
  });

  // ─── Consensus Vote Events ──────────────────────────────────────────────

  it('should track a consensus_vote event', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      getOnMessage()({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.9,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T00:00:00Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const round = result.current.consensusRounds.get('c-1');
      expect(round).toBeDefined();
      expect(round?.vote_count).toBe(1);
      expect(round?.state).toBe('gathering');
      expect(round?.votes).toHaveLength(1);
      expect(round?.votes[0].agent_id).toBe('agent-alpha');
      expect(round?.votes[0].decision).toBe('approve');
    });
  });

  it('should accumulate multiple votes for the same round', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.9,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T00:00:00Z',
      });
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-beta',
        decision: 'reject',
        confidence: 0.7,
        vote_count: 2,
        current_state: 'voting',
        timestamp: '2025-01-01T00:00:01Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const round = result.current.consensusRounds.get('c-1');
      expect(round?.votes).toHaveLength(2);
      expect(round?.vote_count).toBe(2);
      expect(round?.state).toBe('voting');
    });
  });

  it('should deduplicate votes from the same agent', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.9,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T00:00:00Z',
      });
      // Same agent votes again (should be ignored for votes array)
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-alpha',
        decision: 'reject',
        confidence: 0.5,
        vote_count: 2,
        current_state: 'voting',
        timestamp: '2025-01-01T00:00:01Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const round = result.current.consensusRounds.get('c-1');
      // Only 1 unique agent in the votes array
      expect(round?.votes).toHaveLength(1);
      // But vote_count reflects the server-side count
      expect(round?.vote_count).toBe(2);
    });
  });

  // ─── Consensus State Change Events ──────────────────────────────────────

  it('should apply consensus_state_change to an existing round', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      // First create a round with a vote
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.9,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T00:00:00Z',
      });
      // Then a state change
      cb({
        type: 'consensus_state_change',
        consensus_id: 'c-1',
        old_state: 'gathering',
        new_state: 'aggregating',
        timestamp: '2025-01-01T00:00:02Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const round = result.current.consensusRounds.get('c-1');
      expect(round?.state).toBe('aggregating');
    });
  });

  it('should ignore consensus_state_change for unknown rounds', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      getOnMessage()({
        type: 'consensus_state_change',
        consensus_id: 'unknown',
        old_state: 'gathering',
        new_state: 'voting',
        timestamp: '2025-01-01T00:00:00Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.consensusRounds.size).toBe(0);
    });
  });

  // ─── Consensus Complete Events ──────────────────────────────────────────

  it('should apply consensus_complete event', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      getOnMessage()({
        type: 'consensus_complete',
        consensus_id: 'c-1',
        decision: 'deploy-approved',
        confidence: 0.92,
        vote_count: 5,
        red_flags: ['low-sample'],
        timestamp: '2025-01-01T00:01:00Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const round = result.current.consensusRounds.get('c-1');
      expect(round?.state).toBe('completed');
      expect(round?.decision).toBe('deploy-approved');
      expect(round?.confidence).toBe(0.92);
      expect(round?.vote_count).toBe(5);
      expect(round?.red_flags).toEqual(['low-sample']);
    });
  });

  // ─── Deliberation Events ────────────────────────────────────────────────

  it('should track deliberation_round events', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      getOnMessage()({
        type: 'deliberation_round',
        deliberation_id: 'd-1',
        round_number: 1,
        consensus_score: 0.65,
        positions: { support: 3, oppose: 1, neutral: 0, modify: 0 },
        summary: 'Most agents support the proposal',
        timestamp: '2025-01-01T00:00:00Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const delib = result.current.deliberations.get('d-1');
      expect(delib).toBeDefined();
      expect(delib?.current_round).toBe(1);
      expect(delib?.consensus_score).toBe(0.65);
      expect(delib?.positions.support).toBe(3);
      expect(delib?.last_round_summary).toBe('Most agents support the proposal');
      expect(delib?.finalized).toBe(false);
    });
  });

  it('should track deliberation_position events and increment counts', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      // First create a deliberation via round
      cb({
        type: 'deliberation_round',
        deliberation_id: 'd-1',
        round_number: 1,
        consensus_score: 0.5,
        positions: { support: 0, oppose: 0, neutral: 0, modify: 0 },
        summary: 'Starting',
        timestamp: '2025-01-01T00:00:00Z',
      });
      // Then submit positions
      cb({
        type: 'deliberation_position',
        deliberation_id: 'd-1',
        agent_id: 'agent-alpha',
        position: 'support',
        confidence: 0.8,
        timestamp: '2025-01-01T00:00:01Z',
      });
      cb({
        type: 'deliberation_position',
        deliberation_id: 'd-1',
        agent_id: 'agent-beta',
        position: 'oppose',
        confidence: 0.6,
        timestamp: '2025-01-01T00:00:02Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const delib = result.current.deliberations.get('d-1');
      expect(delib?.positions.support).toBe(1);
      expect(delib?.positions.oppose).toBe(1);
    });
  });

  it('should track deliberation_finalized event', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      getOnMessage()({
        type: 'deliberation_finalized',
        deliberation_id: 'd-1',
        final_position: 'support',
        consensus_score: 0.85,
        total_rounds: 3,
        timestamp: '2025-01-01T00:05:00Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      const delib = result.current.deliberations.get('d-1');
      expect(delib?.finalized).toBe(true);
      expect(delib?.final_position).toBe('support');
      expect(delib?.consensus_score).toBe(0.85);
      expect(delib?.current_round).toBe(3);
    });
  });

  // ─── Event Feed ─────────────────────────────────────────────────────────

  it('should populate eventFeed from all event types', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.9,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T00:00:00Z',
      });
      cb({
        type: 'deliberation_round',
        deliberation_id: 'd-1',
        round_number: 1,
        consensus_score: 0.5,
        positions: { support: 2, oppose: 0, neutral: 0, modify: 0 },
        summary: 'Initial round',
        timestamp: '2025-01-01T00:00:01Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.eventFeed).toHaveLength(2);
      const types = result.current.eventFeed.map((e) => e.event_type);
      expect(types).toContain('consensus_vote');
      expect(types).toContain('deliberation_round');
    });
  });

  it('should cap eventFeed at 100 entries', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    // Send 120 events
    act(() => {
      const cb = getOnMessage();
      for (let i = 0; i < 120; i++) {
        cb({
          type: 'consensus_vote',
          consensus_id: `c-${i}`,
          agent_id: `agent-${i}`,
          decision: 'approve',
          confidence: 0.9,
          vote_count: 1,
          current_state: 'gathering',
          timestamp: `2025-01-01T00:${String(i).padStart(2, '0')}:00Z`,
        });
      }
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.eventFeed.length).toBeLessThanOrEqual(100);
    });
  });

  // ─── Throttling ─────────────────────────────────────────────────────────

  it('should throttle rapid events into a single state update', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      // 20 rapid events
      for (let i = 0; i < 20; i++) {
        cb({
          type: 'consensus_vote',
          consensus_id: 'c-1',
          agent_id: `agent-${i}`,
          decision: 'approve',
          confidence: 0.9,
          vote_count: i + 1,
          current_state: 'gathering',
          timestamp: `2025-01-01T00:00:${String(i).padStart(2, '0')}Z`,
        });
      }
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.consensusRounds.size).toBe(1);
      const round = result.current.consensusRounds.get('c-1');
      // All 20 unique agents should be in votes
      expect(round?.votes).toHaveLength(20);
      // vote_count should be the last value
      expect(round?.vote_count).toBe(20);
    });
  });

  // ─── Ignoring Non-Consensus Events ──────────────────────────────────────

  it('should ignore non-consensus event types', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      cb({ type: 'agent_status', agent_id: 'a-1', status: 'active' });
      cb({ type: 'heartbeat', timestamp: '2025-01-01T00:00:00Z' });
      cb({ type: 'phi_update', agent_id: 'a-1', phi_score: 0.8 });
      cb({ type: 'memory_update', agent_id: 'a-1' });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.consensusRounds.size).toBe(0);
      expect(result.current.deliberations.size).toBe(0);
      expect(result.current.eventFeed).toEqual([]);
    });
  });

  // ─── Connection and Error State ─────────────────────────────────────────

  it('should propagate connected state from WebSocket', () => {
    const { result } = renderHook(() => useConsensusWebSocket());

    act(() => {
      const onOpen = mockUseWebSocket.mock.calls[0][1]?.onOpen;
      if (onOpen) onOpen();
    });

    expect(result.current.connected).toBe(true);
  });

  it('should propagate error state from WebSocket', () => {
    const mockError = new Event('error');
    mockUseWebSocket.mockReturnValueOnce({
      connected: false,
      lastMessage: null,
      sendMessage: vi.fn(),
      disconnect: vi.fn(),
      reconnectAttempts: 0,
    });

    const { result } = renderHook(() => useConsensusWebSocket());

    act(() => {
      const onError = mockUseWebSocket.mock.calls[0][1]?.onError;
      if (onError) onError(mockError);
    });

    expect(result.current.error).toBe(mockError);
  });

  it('should provide callable disconnect function', () => {
    const mockDisconnect = vi.fn();
    mockUseWebSocket.mockReturnValueOnce({
      connected: true,
      lastMessage: null,
      sendMessage: vi.fn(),
      disconnect: mockDisconnect,
      reconnectAttempts: 0,
    });

    const { result } = renderHook(() => useConsensusWebSocket());

    act(() => {
      result.current.disconnect();
    });

    expect(mockDisconnect).toHaveBeenCalled();
  });

  // ─── Multiple Independent Rounds and Deliberations ──────────────────────

  it('should track multiple independent consensus rounds', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-1',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.9,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T00:00:00Z',
      });
      cb({
        type: 'consensus_vote',
        consensus_id: 'c-2',
        agent_id: 'agent-beta',
        decision: 'reject',
        confidence: 0.6,
        vote_count: 1,
        current_state: 'voting',
        timestamp: '2025-01-01T00:00:01Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.consensusRounds.size).toBe(2);
      expect(result.current.consensusRounds.get('c-1')?.state).toBe('gathering');
      expect(result.current.consensusRounds.get('c-2')?.state).toBe('voting');
    });
  });

  it('should track multiple independent deliberations', async () => {
    const { result } = renderHook(() => useConsensusWebSocket({ throttleInterval: 100 }));

    act(() => {
      const cb = getOnMessage();
      cb({
        type: 'deliberation_round',
        deliberation_id: 'd-1',
        round_number: 1,
        consensus_score: 0.7,
        positions: { support: 3, oppose: 1, neutral: 0, modify: 0 },
        summary: 'Round 1 of first deliberation',
        timestamp: '2025-01-01T00:00:00Z',
      });
      cb({
        type: 'deliberation_round',
        deliberation_id: 'd-2',
        round_number: 2,
        consensus_score: 0.4,
        positions: { support: 1, oppose: 2, neutral: 1, modify: 0 },
        summary: 'Round 2 of second deliberation',
        timestamp: '2025-01-01T00:00:01Z',
      });
    });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.deliberations.size).toBe(2);
      expect(result.current.deliberations.get('d-1')?.consensus_score).toBe(0.7);
      expect(result.current.deliberations.get('d-2')?.consensus_score).toBe(0.4);
    });
  });
});
