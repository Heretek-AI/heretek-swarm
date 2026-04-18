/**
 * A2A Message Tracking Hook
 *
 * Subscribes to the dashboard WebSocket channel and tracks active A2A edges
 * for real-time network graph visualization on the Canvas.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useWebSocket, WebSocketMessage } from './useWebSocket';

/** Message types sent between agents */
export type MessageType = 'task' | 'consensus' | 'alert' | 'default';

/** State for a single edge in the network graph */
export interface A2AEdgeState {
  count: number;
  lastSeen: string;
  messageType: MessageType;
  animated: boolean;
}

/** A2A message as received from the backend */
export interface A2AMessage {
  type: string;
  from: string;
  to: string;
  message_type?: MessageType;
  timestamp?: string;
  payload?: unknown;
}

interface UseA2AMessagesOptions {
  /** Throttle interval in ms to prevent UI flicker (default: 100) */
  throttleInterval?: number;
}

interface UseA2AMessagesReturn {
  /** Active edges keyed by `${from}→${to}` */
  activeEdges: Map<string, A2AEdgeState>;
  /** All received A2A messages for tracker reuse */
  messages: A2AMessage[];
  /** Whether the WebSocket is connected */
  connected: boolean;
  /** Error state for diagnostics */
  error: Event | null;
  /** Manual disconnect function */
  disconnect: () => void;
}

/** Parse message type from A2A message */
function getMessageType(msg: A2AMessage): MessageType {
  if (msg.message_type) return msg.message_type;
  // Infer from message type string if available
  const type = msg.type?.toLowerCase() ?? '';
  if (type.includes('task')) return 'task';
  if (type.includes('consensus') || type.includes('vote')) return 'consensus';
  if (type.includes('alert') || type.includes('error')) return 'alert';
  return 'default';
}

/**
 * Hook to track A2A messages and active edges via dashboard WebSocket channel.
 *
 * Subscribes to the `dashboard` channel which broadcasts `a2a_message` type events.
 * Falls back gracefully when backend sends heartbeat-only (Redis unavailable).
 */
export function useA2AMessages(options: UseA2AMessagesOptions = {}): UseA2AMessagesReturn {
  const { throttleInterval = 100 } = options;

  const [activeEdges, setActiveEdges] = useState<Map<string, A2AEdgeState>>(new Map());
  const [messages, setMessages] = useState<A2AMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);

  // Refs for throttling state
  const pendingUpdates = useRef<Map<string, A2AEdgeState>>(new Map());
  const throttleTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isProcessing = useRef(false);

  /** Flush accumulated edge updates to state */
  const flushUpdates = useCallback(() => {
    if (isProcessing.current || pendingUpdates.current.size === 0) return;
    isProcessing.current = true;

    setActiveEdges((prev) => {
      const next = new Map(prev);
      pendingUpdates.current.forEach((state, key) => {
        next.set(key, state);
      });
      return next;
    });

    pendingUpdates.current.clear();
    isProcessing.current = false;
  }, []);

  /** Handle incoming WebSocket message */
  const handleMessage = useCallback((msg: WebSocketMessage) => {
    // Only process a2a_message type events from dashboard channel
    if (msg.type !== 'a2a_message') return;

    // Validate required fields for edge tracking
    const from = (msg as unknown as A2AMessage).from;
    const to = (msg as unknown as A2AMessage).to;
    if (!from || !to) {
      // Graceful fallback: heartbeat-only or malformed message
      console.debug('[useA2AMessages] Received a2a_message without from/to:', msg);
      return;
    }

    const now = msg.timestamp || new Date().toISOString();
    const messageType = getMessageType(msg as unknown as A2AMessage);

    // Accumulate updates for throttling
    const key = `${from}→${to}`;
    const existing = pendingUpdates.current.get(key) ?? {
      count: 0,
      lastSeen: now,
      messageType,
      animated: true,
    };

    pendingUpdates.current.set(key, {
      count: existing.count + 1,
      lastSeen: now,
      messageType,
      animated: true,
    });

    // Schedule flush if not already scheduled
    if (!throttleTimeout.current) {
      throttleTimeout.current = setTimeout(() => {
        throttleTimeout.current = null;
        flushUpdates();
      }, throttleInterval);
    }

    // Append to messages array (unthrottled for tracker accuracy)
    setMessages((prev) => {
      // Keep last 200 messages to prevent memory bloat
      const next = [...prev, msg as unknown as A2AMessage];
      if (next.length > 200) next.splice(0, next.length - 200);
      return next;
    });
  }, [throttleInterval, flushUpdates]);

  /** WebSocket subscription to dashboard channel */
  const { disconnect } = useWebSocket('dashboard', {
    onMessage: handleMessage,
    onOpen: () => setConnected(true),
    onClose: () => setConnected(false),
    onError: (err) => setError(err),
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
  });

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (throttleTimeout.current) {
        clearTimeout(throttleTimeout.current);
        throttleTimeout.current = null;
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    activeEdges,
    messages,
    connected,
    error,
    disconnect,
  };
}
