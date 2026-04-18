/**
 * useA2AMessages Hook Tests
 *
 * Tests for A2A message tracking and active edge state management:
 * - WebSocket message handling for a2a_message type
 * - Edge state Map tracking (count, lastSeen, messageType, animated)
 * - Message tracking for A2ATracker reuse
 * - Throttling behavior for 100ms intervals
 * - Connection and error state propagation
 * - Graceful fallback for heartbeat-only messages
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useA2AMessages } from '../useA2AMessages';

// Mock the useWebSocket hook
jest.mock('../useWebSocket', () => ({
  useWebSocket: jest.fn(() => ({
    connected: false,
    lastMessage: null,
    sendMessage: jest.fn(),
    disconnect: jest.fn(),
    reconnectAttempts: 0,
  })),
}));

const mockUseWebSocket = jest.requireMock('../useWebSocket').useWebSocket;

describe('useA2AMessages', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useA2AMessages());

    expect(result.current.activeEdges.size).toBe(0);
    expect(result.current.messages).toEqual([]);
    expect(result.current.connected).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.disconnect).toBe('function');
  });

  it('should track edge state from a2a_message', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    const a2aMessage = {
      type: 'a2a_message',
      from: 'agent-1',
      to: 'agent-2',
      message_type: 'task' as const,
      timestamp: '2025-01-01T00:00:00Z',
    };

    // Simulate WebSocket message
    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) callback(a2aMessage);
    });

    // Advance timers to flush throttled updates
    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.activeEdges.get('agent-1→agent-2')).toMatchObject({
        count: 1,
        lastSeen: '2025-01-01T00:00:00Z',
        messageType: 'task',
        animated: true,
      });
    });
  });

  it('should increment count for repeated messages on same edge', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    const a2aMessage = {
      type: 'a2a_message',
      from: 'agent-1',
      to: 'agent-2',
      message_type: 'consensus' as const,
      timestamp: '2025-01-01T00:00:00Z',
    };

    // Send two messages on same edge
    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        callback(a2aMessage);
        callback({ ...a2aMessage, timestamp: '2025-01-01T00:00:01Z' });
      }
    });

    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.activeEdges.get('agent-1→agent-2')).toMatchObject({
        count: 2,
        messageType: 'consensus',
      });
    });
  });

  it('should track multiple edges independently', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        callback({ type: 'a2a_message', from: 'agent-1', to: 'agent-2', message_type: 'task' as const });
        callback({ type: 'a2a_message', from: 'agent-2', to: 'agent-3', message_type: 'alert' as const });
        callback({ type: 'a2a_message', from: 'agent-3', to: 'agent-1', message_type: 'default' as const });
      }
    });

    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.activeEdges.size).toBe(3);
      expect(result.current.activeEdges.get('agent-1→agent-2')?.messageType).toBe('task');
      expect(result.current.activeEdges.get('agent-2→agent-3')?.messageType).toBe('alert');
      expect(result.current.activeEdges.get('agent-3→agent-1')?.messageType).toBe('default');
    });
  });

  it('should track messages array for A2ATracker', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        callback({ type: 'a2a_message', from: 'a', to: 'b', message_type: 'task' as const });
        callback({ type: 'a2a_message', from: 'b', to: 'c' });
      }
    });

    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].from).toBe('a');
      expect(result.current.messages[1].from).toBe('b');
    });
  });

  it('should throttle updates to prevent UI flicker', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    // Send 20 rapid messages
    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        for (let i = 0; i < 20; i++) {
          callback({
            type: 'a2a_message',
            from: 'agent-1',
            to: 'agent-2',
            message_type: 'task' as const,
            timestamp: `2025-01-01T00:00:${String(i).padStart(2, '0')}Z`,
          });
        }
      }
    });

    // Only one state update should have occurred (after throttle)
    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.activeEdges.get('agent-1→agent-2')?.count).toBe(20);
    });
  });

  it('should propagate connection state', () => {
    mockUseWebSocket.mockReturnValueOnce({
      connected: true,
      lastMessage: null,
      sendMessage: jest.fn(),
      disconnect: jest.fn(),
      reconnectAttempts: 0,
    });

    const { result } = renderHook(() => useA2AMessages());

    expect(result.current.connected).toBe(true);
  });

  it('should propagate error state', () => {
    const mockError = new Event('error');
    mockUseWebSocket.mockReturnValueOnce({
      connected: false,
      lastMessage: null,
      sendMessage: jest.fn(),
      disconnect: jest.fn(),
      reconnectAttempts: 0,
    });

    // Re-render with error state
    const { result } = renderHook(() => useA2AMessages());

    act(() => {
      const onError = mockUseWebSocket.mock.calls[0][1]?.onError;
      if (onError) onError(mockError);
    });

    expect(result.current.error).toBe(mockError);
  });

  it('should provide disconnect function', () => {
    const mockDisconnect = jest.fn();
    mockUseWebSocket.mockReturnValueOnce({
      connected: true,
      lastMessage: null,
      sendMessage: jest.fn(),
      disconnect: mockDisconnect,
      reconnectAttempts: 0,
    });

    const { result } = renderHook(() => useA2AMessages());

    act(() => {
      result.current.disconnect();
    });

    expect(mockDisconnect).toHaveBeenCalled();
  });

  it('should ignore non-a2a_message types', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        callback({ type: 'agent_status', agentId: 'agent-1' });
        callback({ type: 'metrics', agentId: 'agent-1' });
        callback({ type: 'heartbeat' });
      }
    });

    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.activeEdges.size).toBe(0);
    });
  });

  it('should gracefully handle messages without from/to fields', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        // a2a_message but missing from/to - Redis may be unavailable
        callback({ type: 'a2a_message', timestamp: '2025-01-01T00:00:00Z' });
        callback({ type: 'a2a_message', from: 'agent-1' }); // missing 'to'
        callback({ type: 'a2a_message', to: 'agent-2' }); // missing 'from'
      }
    });

    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      // No edges created but no crash
      expect(result.current.activeEdges.size).toBe(0);
    });
  });

  it('should infer message type from type string when message_type absent', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        callback({ type: 'a2a_message', from: 'a', to: 'b', message: 'task_delegation' });
        callback({ type: 'a2a_message', from: 'c', to: 'd', message: 'consensus_vote' });
        callback({ type: 'a2a_message', from: 'e', to: 'f', message: 'error_alert' });
      }
    });

    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.activeEdges.get('a→b')?.messageType).toBe('task');
      expect(result.current.activeEdges.get('c→d')?.messageType).toBe('consensus');
      expect(result.current.activeEdges.get('e→f')?.messageType).toBe('alert');
    });
  });

  it('should use default message type when type string unrecognizable', async () => {
    const { result } = renderHook(() => useA2AMessages({ throttleInterval: 100 }));

    act(() => {
      const callback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (callback) {
        callback({ type: 'a2a_message', from: 'a', to: 'b', message: 'random_payload' });
      }
    });

    act(() => {
      jest.advanceTimersByTime(150);
    });

    await waitFor(() => {
      expect(result.current.activeEdges.get('a→b')?.messageType).toBe('default');
    });
  });
});
