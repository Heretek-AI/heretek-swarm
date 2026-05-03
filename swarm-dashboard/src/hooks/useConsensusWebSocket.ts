/**
 * Consensus & Deliberation WebSocket Hook
 *
 * Subscribes to the dashboard WebSocket channel and tracks live
 * consensus/deliberation events — votes, round completions, state
 * transitions, and deliberation argument submissions.
 *
 * Supplements REST polling — when WebSocket is unavailable, the dashboard
 * falls back to periodic fetches.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useWebSocket, WebSocketMessage } from './useWebSocket';
import type { ConsensusVote, ConsensusState } from '../api/consensus';
import type { DeliberationPosition, DeliberationRoundResult } from '../api/deliberation';

// =============================================================================
// WebSocket Event Types
// =============================================================================

/** A vote was submitted to a consensus round */
export interface ConsensusVoteEvent {
  type: 'consensus_vote';
  consensus_id: string;
  agent_id: string;
  decision: string;
  confidence: number;
  vote_count: number;
  current_state: ConsensusState;
  timestamp: string;
}

/** A consensus round changed state (gathering → voting → aggregating → completed) */
export interface ConsensusStateChangeEvent {
  type: 'consensus_state_change';
  consensus_id: string;
  old_state: ConsensusState;
  new_state: ConsensusState;
  timestamp: string;
}

/** Consensus aggregation completed */
export interface ConsensusCompleteEvent {
  type: 'consensus_complete';
  consensus_id: string;
  decision: string;
  confidence: number;
  vote_count: number;
  red_flags: string[];
  timestamp: string;
}

/** A deliberation round was executed */
export interface DeliberationRoundEvent {
  type: 'deliberation_round';
  deliberation_id: string;
  round_number: number;
  consensus_score: number;
  positions: Record<DeliberationPosition, number>;
  summary: string;
  timestamp: string;
}

/** An agent submitted a position during deliberation */
export interface DeliberationPositionEvent {
  type: 'deliberation_position';
  deliberation_id: string;
  agent_id: string;
  position: DeliberationPosition;
  confidence: number;
  timestamp: string;
}

/** An agent submitted an argument during deliberation */
export interface DeliberationArgumentEvent {
  type: 'deliberation_argument';
  deliberation_id: string;
  argument_id: string;
  agent_id: string;
  position: DeliberationPosition;
  reasoning: string;
  timestamp: string;
}

/** A deliberation was finalized */
export interface DeliberationFinalizedEvent {
  type: 'deliberation_finalized';
  deliberation_id: string;
  final_position: DeliberationPosition;
  consensus_score: number;
  total_rounds: number;
  timestamp: string;
}

/** Union of all consensus/deliberation WebSocket events */
export type ConsensusWebSocketEvent =
  | ConsensusVoteEvent
  | ConsensusStateChangeEvent
  | ConsensusCompleteEvent
  | DeliberationRoundEvent
  | DeliberationPositionEvent
  | DeliberationArgumentEvent
  | DeliberationFinalizedEvent;

// =============================================================================
// Hook State Types
// =============================================================================

/** Live consensus round state tracked from WebSocket events */
export interface LiveConsensusRound {
  consensus_id: string;
  topic?: string;
  state: ConsensusState;
  votes: ConsensusVote[];
  vote_count: number;
  decision: string | null;
  confidence: number | null;
  red_flags: string[];
  last_updated: string;
}

/** Live deliberation state tracked from WebSocket events */
export interface LiveDeliberation {
  deliberation_id: string;
  current_round: number;
  consensus_score: number;
  positions: Record<DeliberationPosition, number>;
  last_round_summary: string | null;
  finalized: boolean;
  final_position: DeliberationPosition | null;
  last_updated: string;
}

/** Recent event for the audit trail feed */
export interface ConsensusEventEntry {
  event_type: ConsensusWebSocketEvent['type'];
  id: string; // consensus_id or deliberation_id
  agent_id?: string;
  summary: string;
  timestamp: string;
}

interface UseConsensusWebSocketOptions {
  /** Throttle interval in ms to prevent UI flicker (default: 100) */
  throttleInterval?: number;
}

interface UseConsensusWebSocketReturn {
  /** Live consensus rounds keyed by consensus_id */
  consensusRounds: Map<string, LiveConsensusRound>;
  /** Live deliberations keyed by deliberation_id */
  deliberations: Map<string, LiveDeliberation>;
  /** Chronological event feed (most recent first, capped at 100) */
  eventFeed: ConsensusEventEntry[];
  /** Whether the WebSocket is connected */
  connected: boolean;
  /** Error state for diagnostics */
  error: Event | null;
  /** Manual disconnect function */
  disconnect: () => void;
}

// =============================================================================
// Event Type Guard
// =============================================================================

const CONSENSUS_EVENT_TYPES = new Set([
  'consensus_vote',
  'consensus_state_change',
  'consensus_complete',
  'deliberation_round',
  'deliberation_position',
  'deliberation_argument',
  'deliberation_finalized',
]);

function isConsensusEvent(msg: WebSocketMessage): msg is WebSocketMessage & ConsensusWebSocketEvent {
  return CONSENSUS_EVENT_TYPES.has(msg.type);
}

// =============================================================================
// Event-to-State Reducers
// =============================================================================

function applyVoteEvent(
  existing: LiveConsensusRound | undefined,
  event: ConsensusVoteEvent
): LiveConsensusRound {
  const round: LiveConsensusRound = existing ?? {
    consensus_id: event.consensus_id,
    state: event.current_state,
    votes: [],
    vote_count: 0,
    decision: null,
    confidence: null,
    red_flags: [],
    last_updated: event.timestamp,
  };

  // Avoid duplicate votes from the same agent
  const hasVote = round.votes.some((v) => v.agent_id === event.agent_id);
  const votes = hasVote
    ? round.votes
    : [
        ...round.votes,
        {
          agent_id: event.agent_id,
          decision: event.decision,
          confidence: event.confidence,
          timestamp: event.timestamp,
          metadata: {},
        },
      ];

  return {
    ...round,
    votes,
    vote_count: event.vote_count,
    state: event.current_state,
    last_updated: event.timestamp,
  };
}

function applyStateChangeEvent(
  existing: LiveConsensusRound | undefined,
  event: ConsensusStateChangeEvent
): LiveConsensusRound | undefined {
  if (!existing) return undefined;
  return {
    ...existing,
    state: event.new_state,
    last_updated: event.timestamp,
  };
}

function applyCompleteEvent(
  existing: LiveConsensusRound | undefined,
  event: ConsensusCompleteEvent
): LiveConsensusRound {
  const round: LiveConsensusRound = existing ?? {
    consensus_id: event.consensus_id,
    state: 'completed',
    votes: [],
    vote_count: event.vote_count,
    decision: null,
    confidence: null,
    red_flags: [],
    last_updated: event.timestamp,
  };

  return {
    ...round,
    state: 'completed',
    decision: event.decision,
    confidence: event.confidence,
    vote_count: event.vote_count,
    red_flags: event.red_flags,
    last_updated: event.timestamp,
  };
}

function applyDeliberationRoundEvent(
  existing: LiveDeliberation | undefined,
  event: DeliberationRoundEvent
): LiveDeliberation {
  return {
    ...(existing ?? {
      deliberation_id: event.deliberation_id,
      current_round: 0,
      consensus_score: 0,
      positions: {} as Record<DeliberationPosition, number>,
      last_round_summary: null,
      finalized: false,
      final_position: null,
      last_updated: event.timestamp,
    }),
    current_round: event.round_number,
    consensus_score: event.consensus_score,
    positions: event.positions,
    last_round_summary: event.summary,
    last_updated: event.timestamp,
  };
}

function applyDeliberationPositionEvent(
  existing: LiveDeliberation | undefined,
  event: DeliberationPositionEvent
): LiveDeliberation | undefined {
  if (!existing) return undefined;
  // Increment position count
  const positions = { ...existing.positions };
  positions[event.position] = (positions[event.position] ?? 0) + 1;
  return {
    ...existing,
    positions,
    last_updated: event.timestamp,
  };
}

function applyDeliberationFinalizedEvent(
  existing: LiveDeliberation | undefined,
  event: DeliberationFinalizedEvent
): LiveDeliberation {
  return {
    ...(existing ?? {
      deliberation_id: event.deliberation_id,
      current_round: 0,
      consensus_score: 0,
      positions: {} as Record<DeliberationPosition, number>,
      last_round_summary: null,
      finalized: false,
      final_position: null,
      last_updated: event.timestamp,
    }),
    finalized: true,
    final_position: event.final_position,
    consensus_score: event.consensus_score,
    current_round: event.total_rounds,
    last_updated: event.timestamp,
  };
}

// =============================================================================
// Event Feed Builder
// =============================================================================

const MAX_FEED_SIZE = 100;

function buildFeedEntry(event: ConsensusWebSocketEvent): ConsensusEventEntry {
  const id = 'consensus_id' in event ? event.consensus_id : event.deliberation_id;

  switch (event.type) {
    case 'consensus_vote':
      return {
        event_type: event.type,
        id,
        agent_id: event.agent_id,
        summary: `Vote: "${event.decision}" (confidence: ${(event.confidence * 100).toFixed(0)}%)`,
        timestamp: event.timestamp,
      };
    case 'consensus_state_change':
      return {
        event_type: event.type,
        id,
        summary: `State: ${event.old_state} → ${event.new_state}`,
        timestamp: event.timestamp,
      };
    case 'consensus_complete':
      return {
        event_type: event.type,
        id,
        summary: `Consensus: "${event.decision}" (confidence: ${(event.confidence * 100).toFixed(0)}%)`,
        timestamp: event.timestamp,
      };
    case 'deliberation_round':
      return {
        event_type: event.type,
        id,
        summary: `Round ${event.round_number}: consensus ${(event.consensus_score * 100).toFixed(0)}% — ${event.summary}`,
        timestamp: event.timestamp,
      };
    case 'deliberation_position':
      return {
        event_type: event.type,
        id,
        agent_id: event.agent_id,
        summary: `Position: ${event.position} (confidence: ${(event.confidence * 100).toFixed(0)}%)`,
        timestamp: event.timestamp,
      };
    case 'deliberation_argument':
      return {
        event_type: event.type,
        id,
        agent_id: event.agent_id,
        summary: `Argument (${event.position}): ${event.reasoning.slice(0, 80)}${event.reasoning.length > 80 ? '…' : ''}`,
        timestamp: event.timestamp,
      };
    case 'deliberation_finalized':
      return {
        event_type: event.type,
        id,
        summary: `Finalized: ${event.final_position} (consensus: ${(event.consensus_score * 100).toFixed(0)}%)`,
        timestamp: event.timestamp,
      };
  }
}

// =============================================================================
// Hook
// =============================================================================

/**
 * Track live consensus rounds and deliberations via dashboard WebSocket channel.
 *
 * Subscribes to the `dashboard` channel which broadcasts consensus_vote,
 * consensus_state_change, consensus_complete, deliberation_round,
 * deliberation_position, deliberation_argument, and deliberation_finalized
 * events from the backend consensus/deliberation endpoints.
 */
export function useConsensusWebSocket(
  options: UseConsensusWebSocketOptions = {}
): UseConsensusWebSocketReturn {
  const { throttleInterval = 100 } = options;

  const [consensusRounds, setConsensusRounds] = useState<Map<string, LiveConsensusRound>>(new Map());
  const [deliberations, setDeliberations] = useState<Map<string, LiveDeliberation>>(new Map());
  const [eventFeed, setEventFeed] = useState<ConsensusEventEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);

  // Refs for throttled state batching
  const pendingConsensus = useRef<Map<string, LiveConsensusRound>>(new Map());
  const pendingDeliberations = useRef<Map<string, LiveDeliberation>>(new Map());
  const pendingFeedEntries = useRef<ConsensusEventEntry[]>([]);
  const throttleTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isProcessing = useRef(false);

  // Keep current state refs for merging in callbacks without re-subscribing
  const consensusRef = useRef(consensusRounds);
  consensusRef.current = consensusRounds;
  const deliberationsRef = useRef(deliberations);
  deliberationsRef.current = deliberations;

  /** Flush accumulated updates to React state */
  const flushUpdates = useCallback(() => {
    if (isProcessing.current) return;
    if (
      pendingConsensus.current.size === 0 &&
      pendingDeliberations.current.size === 0 &&
      pendingFeedEntries.current.length === 0
    ) {
      return;
    }
    isProcessing.current = true;

    // Consensus rounds
    if (pendingConsensus.current.size > 0) {
      setConsensusRounds((prev) => {
        const next = new Map(prev);
        pendingConsensus.current.forEach((round, id) => {
          next.set(id, round);
        });
        return next;
      });
      pendingConsensus.current.clear();
    }

    // Deliberations
    if (pendingDeliberations.current.size > 0) {
      setDeliberations((prev) => {
        const next = new Map(prev);
        pendingDeliberations.current.forEach((delib, id) => {
          next.set(id, delib);
        });
        return next;
      });
      pendingDeliberations.current.clear();
    }

    // Event feed (prepend newest, cap at MAX_FEED_SIZE)
    if (pendingFeedEntries.current.length > 0) {
      setEventFeed((prev) => {
        const merged = [...pendingFeedEntries.current, ...prev];
        pendingFeedEntries.current = [];
        return merged.slice(0, MAX_FEED_SIZE);
      });
    }

    isProcessing.current = false;
  }, []);

  /** Handle incoming WebSocket message */
  const handleMessage = useCallback(
    (msg: WebSocketMessage) => {
      if (!isConsensusEvent(msg)) return;

      const event = msg as ConsensusWebSocketEvent;
      const feedEntry = buildFeedEntry(event);
      pendingFeedEntries.current.push(feedEntry);

      switch (event.type) {
        case 'consensus_vote': {
          const existing =
            pendingConsensus.current.get(event.consensus_id) ??
            consensusRef.current.get(event.consensus_id);
          pendingConsensus.current.set(
            event.consensus_id,
            applyVoteEvent(existing, event)
          );
          break;
        }
        case 'consensus_state_change': {
          const existing =
            pendingConsensus.current.get(event.consensus_id) ??
            consensusRef.current.get(event.consensus_id);
          const updated = applyStateChangeEvent(existing, event);
          if (updated) {
            pendingConsensus.current.set(event.consensus_id, updated);
          }
          break;
        }
        case 'consensus_complete': {
          const existing =
            pendingConsensus.current.get(event.consensus_id) ??
            consensusRef.current.get(event.consensus_id);
          pendingConsensus.current.set(
            event.consensus_id,
            applyCompleteEvent(existing, event)
          );
          break;
        }
        case 'deliberation_round': {
          const existing =
            pendingDeliberations.current.get(event.deliberation_id) ??
            deliberationsRef.current.get(event.deliberation_id);
          pendingDeliberations.current.set(
            event.deliberation_id,
            applyDeliberationRoundEvent(existing, event)
          );
          break;
        }
        case 'deliberation_position': {
          const existing =
            pendingDeliberations.current.get(event.deliberation_id) ??
            deliberationsRef.current.get(event.deliberation_id);
          const updated = applyDeliberationPositionEvent(existing, event);
          if (updated) {
            pendingDeliberations.current.set(event.deliberation_id, updated);
          }
          break;
        }
        case 'deliberation_argument': {
          // Arguments feed into the event log but don't mutate deliberation state
          // beyond what positions already track
          break;
        }
        case 'deliberation_finalized': {
          const existing =
            pendingDeliberations.current.get(event.deliberation_id) ??
            deliberationsRef.current.get(event.deliberation_id);
          pendingDeliberations.current.set(
            event.deliberation_id,
            applyDeliberationFinalizedEvent(existing, event)
          );
          break;
        }
      }

      // Schedule flush if not already scheduled
      if (!throttleTimeout.current) {
        throttleTimeout.current = setTimeout(() => {
          throttleTimeout.current = null;
          flushUpdates();
        }, throttleInterval);
      }
    },
    [throttleInterval, flushUpdates]
  );

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
    consensusRounds,
    deliberations,
    eventFeed,
    connected,
    error,
    disconnect,
  };
}
