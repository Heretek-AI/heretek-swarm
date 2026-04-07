/**
 * Real-Time Agent Updates Hook Tests
 * 
 * Tests for useRealTimeAgentUpdates hook covering:
 * - WebSocket message handling
 * - Agent status updates
 * - Workflow progress updates
 * - Metrics updates
 * - Connection status
 * - Throttling behavior
 * - Reconnection logic
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useRealTimeAgentUpdates, useAgentStatus, useWorkflowProgress, useAgentMetrics } from '../useRealTimeAgentUpdates';

// Mock the useWebSocket hook
jest.mock('../useWebSocket', () => ({
  useWebSocket: jest.fn(() => ({
    connected: true,
    lastMessage: null,
    sendMessage: jest.fn(),
    disconnect: jest.fn(),
    reconnectAttempts: 0,
  })),
}));

const mockUseWebSocket = jest.requireMock('../useWebSocket').useWebSocket;

describe('useRealTimeAgentUpdates', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useRealTimeAgentUpdates());

    expect(result.current.agentStatuses).toEqual({});
    expect(result.current.workflowProgress).toEqual({});
    expect(result.current.agentMetrics).toEqual({});
    expect(result.current.connected).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should process agent status updates', () => {
    const { result } = renderHook(() => useRealTimeAgentUpdates());

    const agentStatusMessage = {
      type: 'agent_status',
      agentId: 'agent-1',
      status: 'active' as const,
      currentTask: 'Processing data',
      lastHeartbeat: new Date().toISOString(),
    };

    act(() => {
      // Simulate receiving message through useWebSocket
      const mockCallback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (mockCallback) {
        mockCallback(agentStatusMessage);
      }
    });

    expect(result.current.agentStatuses['agent-1']).toEqual({
      type: 'agent_status',
      agentId: 'agent-1',
      status: 'active',
      currentTask: 'Processing data',
      lastHeartbeat: expect.any(String),
    });
  });

  it('should process workflow progress updates', () => {
    const { result } = renderHook(() => useRealTimeAgentUpdates());

    const progressMessage = {
      type: 'workflow_progress',
      workflowId: 'workflow-1',
      currentNode: 'node-1',
      phase: 'execute' as const,
      progress: 75,
    };

    act(() => {
      const mockCallback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (mockCallback) {
        mockCallback(progressMessage);
      }
    });

    expect(result.current.workflowProgress['workflow-1']).toEqual({
      type: 'workflow_progress',
      workflowId: 'workflow-1',
      currentNode: 'node-1',
      phase: 'execute',
      progress: 75,
    });
  });

  it('should process metrics updates', () => {
    const { result } = renderHook(() => useRealTimeAgentUpdates());

    const metricsMessage = {
      type: 'metrics',
      agentId: 'agent-1',
      metrics: {
        phi: 0.85,
        coherence: 0.92,
        load: 0.45,
        queueSize: 3,
      },
    };

    act(() => {
      const mockCallback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (mockCallback) {
        mockCallback(metricsMessage);
      }
    });

    expect(result.current.agentMetrics['agent-1']).toEqual({
      type: 'metrics',
      agentId: 'agent-1',
      metrics: {
        phi: 0.85,
        coherence: 0.92,
        load: 0.45,
        queueSize: 3,
      },
    });
  });

  it('should throttle updates to prevent UI flicker', async () => {
    const { result } = renderHook(() =>
      useRealTimeAgentUpdates({ throttleInterval: 100 })
    );

    const agentStatusMessage = {
      type: 'agent_status',
      agentId: 'agent-1',
      status: 'active' as const,
      lastHeartbeat: new Date().toISOString(),
    };

    // Send multiple messages rapidly
    act(() => {
      const mockCallback = mockUseWebSocket.mock.calls[0][1]?.onMessage;
      if (mockCallback) {
        mockCallback(agentStatusMessage);
        mockCallback({ ...agentStatusMessage, status: 'idle' });
        mockCallback({ ...agentStatusMessage, status: 'processing' });
      }
    });

    // Should have processed at least one update
    expect(result.current.agentStatuses['agent-1']).toBeDefined();
  });

  it('should track connection status', () => {
    mockUseWebSocket.mockReturnValueOnce({
      connected: false,
      lastMessage: null,
      sendMessage: jest.fn(),
      disconnect: jest.fn(),
      reconnectAttempts: 2,
    });

    const { result } = renderHook(() => useRealTimeAgentUpdates());

    expect(result.current.connected).toBe(false);
    expect(result.current.reconnectAttempts).toBe(2);
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

    const { result } = renderHook(() => useRealTimeAgentUpdates());

    act(() => {
      result.current.disconnect();
    });

    expect(mockDisconnect).toHaveBeenCalled();
  });

  it('should provide sendMessage function', () => {
    const mockSendMessage = jest.fn().mockReturnValue(true);
    mockUseWebSocket.mockReturnValueOnce({
      connected: true,
      lastMessage: null,
      sendMessage: mockSendMessage,
      disconnect: jest.fn(),
      reconnectAttempts: 0,
    });

    const { result } = renderHook(() => useRealTimeAgentUpdates());

    act(() => {
      result.current.sendMessage({ type: 'subscribe', channel: 'agent_status' });
    });

    expect(mockSendMessage).toHaveBeenCalledWith({
      type: 'subscribe',
      channel: 'agent_status',
    });
  });
});

describe('useAgentStatus', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return only agent statuses', () => {
    const { result } = renderHook(() => useAgentStatus());

    expect(result.current.agentStatuses).toEqual({});
    expect(result.current.workflowProgress).toBeUndefined();
    expect(result.current.agentMetrics).toBeUndefined();
  });
});

describe('useWorkflowProgress', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return only workflow progress', () => {
    const { result } = renderHook(() => useWorkflowProgress());

    expect(result.current.workflowProgress).toEqual({});
    expect(result.current.agentStatuses).toBeUndefined();
    expect(result.current.agentMetrics).toBeUndefined();
  });
});

describe('useAgentMetrics', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return only agent metrics', () => {
    const { result } = renderHook(() => useAgentMetrics());

    expect(result.current.agentMetrics).toEqual({});
    expect(result.current.agentStatuses).toBeUndefined();
    expect(result.current.workflowProgress).toBeUndefined();
  });
});
