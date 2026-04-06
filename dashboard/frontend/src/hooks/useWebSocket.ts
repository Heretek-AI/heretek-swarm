/**
 * WebSocket Hook - Real-time communication
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  data?: unknown;
  timestamp?: string;
  agent_id?: string;
  [key: string]: unknown;
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(
  channel: string,
  options: UseWebSocketOptions = {}
) {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'localhost:8000';

  const connect = useCallback(() => {
    const wsUrl = `ws://${API_URL.replace('http://', '').replace('https://', '')}/ws/${channel}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setConnected(true);
        reconnectAttempts.current = 0;
        onOpen?.();
        console.log(`WebSocket connected to ${channel}`);
      };

      wsRef.current.onclose = () => {
        setConnected(false);
        onClose?.();
        console.log(`WebSocket disconnected from ${channel}`);

        // Attempt reconnection
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          console.log(`Reconnecting... attempt ${reconnectAttempts.current}`);
          reconnectTimeout.current = setTimeout(connect, reconnectInterval);
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      onError?.(error as Event);
    }
  }, [channel, API_URL, onOpen, onClose, onError, onMessage, reconnectInterval, maxReconnectAttempts]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket not connected, message not sent');
    return false;
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnectAttempts: reconnectAttempts.current,
  };
}

/**
 * Hook for agent events WebSocket
 */
export function useAgentEvents(onMessage?: (message: WebSocketMessage) => void) {
  return useWebSocket('agents', {
    onMessage,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
  });
}

/**
 * Hook for metrics stream WebSocket
 */
export function useMetricsStream(onMessage?: (message: WebSocketMessage) => void) {
  return useWebSocket('metrics', {
    onMessage,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  });
}

/**
 * Hook for execution updates WebSocket
 */
export function useExecutionStream(
  executionId: string,
  onMessage?: (message: WebSocketMessage) => void
) {
  return useWebSocket(`executions/${executionId}`, {
    onMessage,
    reconnectInterval: 2000,
    maxReconnectAttempts: 5,
  });
}
