/**
 * Live Deliberation Panel
 *
 * Real-time view of agent votes during consensus deliberation.
 * Subscribes to dashboard WebSocket events and displays live vote tallies,
 * argument threads, and consensus progress.
 */

import React, { useMemo } from 'react';
import { useConsensusWebSocket, LiveConsensusRound, LiveDeliberation, ConsensusEventEntry } from '../../hooks/useConsensusWebSocket';
import { MetricCard, MetricCardGrid } from '../UI/MetricCard';
import { EmptyState } from '../UI/EmptyState';
import type { DeliberationPosition } from '../../api/deliberation';

// =============================================================================
// Position styling
// =============================================================================

const POSITION_CONFIG: Record<DeliberationPosition, { color: string; bg: string; label: string; icon: string }> = {
  support: { color: 'text-green-400', bg: 'bg-green-500', label: 'Support', icon: '✓' },
  oppose: { color: 'text-red-400', bg: 'bg-red-500', label: 'Oppose', icon: '✕' },
  neutral: { color: 'text-gray-400', bg: 'bg-gray-500', label: 'Neutral', icon: '—' },
  modify: { color: 'text-yellow-400', bg: 'bg-yellow-500', label: 'Modify', icon: '✎' },
};

function getPositionConfig(position: DeliberationPosition | string) {
  return POSITION_CONFIG[position as DeliberationPosition] ?? {
    color: 'text-gray-400',
    bg: 'bg-gray-500',
    label: position,
    icon: '?',
  };
}

// =============================================================================
// Consensus state badge
// =============================================================================

const STATE_STYLES: Record<string, string> = {
  gathering: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  voting: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  aggregating: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  completed: 'bg-green-500/20 text-green-400 border-green-500/30',
  failed: 'bg-red-500/20 text-red-400 border-red-500/30',
};

function ConsensusStateBadge({ state }: { state: string }) {
  const style = STATE_STYLES[state] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${style}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      {state}
    </span>
  );
}

// =============================================================================
// Vote progress bar
// =============================================================================

function VoteProgressBar({ votes, totalExpected = 4 }: { votes: { agent_id: string; decision: string }[]; totalExpected?: number }) {
  const uniqueAgents = useMemo(() => new Set(votes.map(v => v.agent_id)), [votes]);
  const progress = Math.min((uniqueAgents.size / totalExpected) * 100, 100);

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-gray-400">
        <span>{uniqueAgents.size} of {totalExpected} agents voted</span>
        <span>{progress.toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 transition-all duration-500 ease-out rounded-full"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

// =============================================================================
// Consensus round card
// =============================================================================

function ConsensusRoundCard({ round }: { round: LiveConsensusRound }) {
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-5 space-y-4 hover:border-gray-600 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <ConsensusStateBadge state={round.state} />
            <span className="text-xs text-gray-500 font-mono truncate">{round.consensus_id.slice(0, 12)}…</span>
          </div>
          {round.topic && (
            <h3 className="text-sm font-semibold text-white mt-2 truncate">{round.topic}</h3>
          )}
        </div>
        {round.decision && (
          <div className="text-right shrink-0">
            <div className="text-xs text-gray-400">Decision</div>
            <div className="text-sm font-medium text-green-400 truncate max-w-[200px]">{round.decision}</div>
          </div>
        )}
      </div>

      {/* Vote progress */}
      <VoteProgressBar votes={round.votes} />

      {/* Vote tally */}
      {round.votes.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wide">Agent Votes</h4>
          <div className="space-y-2">
            {round.votes.map((vote, idx) => (
              <div
                key={`${vote.agent_id}-${idx}`}
                className="flex items-center gap-3 p-2.5 bg-gray-900/50 rounded-lg border border-gray-700/50"
              >
                <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center text-xs font-mono text-gray-300 shrink-0">
                  {vote.agent_id.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-white truncate">{vote.agent_id}</div>
                  <div className="text-xs text-gray-400 truncate">{vote.decision}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-bold text-blue-400">{(vote.confidence * 100).toFixed(0)}%</div>
                  <div className="text-xs text-gray-500">confidence</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confidence & red flags */}
      <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t border-gray-700/50">
        {round.confidence !== null && (
          <span>Confidence: <span className="text-white font-medium">{(round.confidence * 100).toFixed(1)}%</span></span>
        )}
        {round.red_flags.length > 0 && (
          <span className="text-red-400">⚠ {round.red_flags.length} red flag{round.red_flags.length !== 1 ? 's' : ''}</span>
        )}
        <span className="ml-auto">{new Date(round.last_updated).toLocaleTimeString()}</span>
      </div>
    </div>
  );
}

// =============================================================================
// Deliberation card
// =============================================================================

function DeliberationCard({ delib }: { delib: LiveDeliberation }) {
  const positionEntries = Object.entries(delib.positions) as [DeliberationPosition, number][];
  const totalPositions = positionEntries.reduce((sum, [, count]) => sum + count, 0);

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-5 space-y-4 hover:border-gray-600 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            {delib.finalized ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border bg-green-500/20 text-green-400 border-green-500/30">
                Finalized
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border bg-blue-500/20 text-blue-400 border-blue-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                In Progress
              </span>
            )}
            <span className="text-xs text-gray-500 font-mono truncate">{delib.deliberation_id.slice(0, 12)}…</span>
          </div>
        </div>
        {delib.final_position && (
          <div className="text-right shrink-0">
            <div className="text-xs text-gray-400">Final Position</div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className={getPositionConfig(delib.final_position).color}>{getPositionConfig(delib.final_position).icon}</span>
              <span className="text-sm font-medium text-white capitalize">{delib.final_position}</span>
            </div>
          </div>
        )}
      </div>

      {/* Round & consensus */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
          <div className="text-xs text-gray-400">Round</div>
          <div className="text-lg font-bold text-white">{delib.current_round}</div>
        </div>
        <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
          <div className="text-xs text-gray-400">Consensus Score</div>
          <div className="text-lg font-bold text-blue-400">{(delib.consensus_score * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Position distribution */}
      {positionEntries.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wide">Positions</h4>
          {/* Position bar */}
          <div className="h-3 bg-gray-700 rounded-full overflow-hidden flex">
            {positionEntries.map(([pos, count]) => {
              const pct = totalPositions > 0 ? (count / totalPositions) * 100 : 0;
              return (
                <div
                  key={pos}
                  className={`${getPositionConfig(pos).bg} transition-all duration-500`}
                  style={{ width: `${pct}%` }}
                  title={`${getPositionConfig(pos).label}: ${count}`}
                />
              );
            })}
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-3 text-xs">
            {positionEntries.map(([pos, count]) => (
              <div key={pos} className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${getPositionConfig(pos).bg}`} />
                <span className={`${getPositionConfig(pos).color} font-medium`}>{getPositionConfig(pos).label}</span>
                <span className="text-gray-500">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Last round summary */}
      {delib.last_round_summary && (
        <div className="p-3 bg-gray-900/30 rounded-lg border border-gray-700/30 text-xs text-gray-300">
          <span className="text-gray-500 font-medium">Latest round: </span>
          {delib.last_round_summary}
        </div>
      )}

      {/* Timestamp */}
      <div className="text-xs text-gray-500 text-right pt-2 border-t border-gray-700/50">
        Updated: {new Date(delib.last_updated).toLocaleTimeString()}
      </div>
    </div>
  );
}

// =============================================================================
// Event feed row
// =============================================================================

const EVENT_ICONS: Record<string, { icon: string; color: string }> = {
  consensus_vote: { icon: '🗳️', color: 'text-blue-400' },
  consensus_state_change: { icon: '🔄', color: 'text-yellow-400' },
  consensus_complete: { icon: '✅', color: 'text-green-400' },
  deliberation_round: { icon: '🔁', color: 'text-purple-400' },
  deliberation_position: { icon: '📍', color: 'text-blue-400' },
  deliberation_argument: { icon: '💬', color: 'text-gray-300' },
  deliberation_finalized: { icon: '🏁', color: 'text-green-400' },
};

function EventFeedRow({ entry }: { entry: ConsensusEventEntry }) {
  const cfg = EVENT_ICONS[entry.event_type] ?? { icon: '•', color: 'text-gray-400' };
  return (
    <div className="flex items-start gap-3 py-2 px-3 hover:bg-gray-800/30 rounded-lg transition-colors">
      <span className="text-base shrink-0">{cfg.icon}</span>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-gray-300 truncate">{entry.summary}</p>
        {entry.agent_id && (
          <span className="text-xs text-gray-500 font-mono">{entry.agent_id}</span>
        )}
      </div>
      <span className="text-xs text-gray-600 shrink-0">{new Date(entry.timestamp).toLocaleTimeString()}</span>
    </div>
  );
}

// =============================================================================
// Live Panel Component
// =============================================================================

export interface LiveDeliberationPanelProps {
  className?: string;
}

export function LiveDeliberationPanel({ className = '' }: LiveDeliberationPanelProps) {
  const { consensusRounds, deliberations, eventFeed, connected, error } = useConsensusWebSocket();

  const consensusArray = useMemo(() => Array.from(consensusRounds.values()), [consensusRounds]);
  const delibArray = useMemo(() => Array.from(deliberations.values()), [deliberations]);

  const hasData = consensusArray.length > 0 || delibArray.length > 0;

  // Summary metrics
  const activeConsensus = consensusArray.filter(r => r.state !== 'completed' && r.state !== 'failed').length;
  const activeDeliberations = delibArray.filter(d => !d.finalized).length;
  const totalVotes = consensusArray.reduce((sum, r) => sum + r.votes.length, 0);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Connection status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-400">
            {connected ? 'Live' : error ? 'Connection error' : 'Connecting…'}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {consensusArray.length} round{consensusArray.length !== 1 ? 's' : ''} · {delibArray.length} deliberation{delibArray.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Summary metrics */}
      {hasData && (
        <MetricCardGrid columns={3}>
          <MetricCard title="Active Rounds" value={activeConsensus} color="blue" size="sm" />
          <MetricCard title="Active Deliberations" value={activeDeliberations} color="purple" size="sm" />
          <MetricCard title="Total Votes" value={totalVotes} color="green" size="sm" />
        </MetricCardGrid>
      )}

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Active rounds & deliberations */}
        <div className="lg:col-span-2 space-y-6">
          {/* Consensus rounds */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">Consensus Rounds</h3>
            {consensusArray.length > 0 ? (
              <div className="space-y-4">
                {consensusArray.map(round => (
                  <ConsensusRoundCard key={round.consensus_id} round={round} />
                ))}
              </div>
            ) : (
              <EmptyState
                title="No active consensus rounds"
                description="Start a consensus round from the API to see live votes here"
                icon="🗳️"
                size="sm"
              />
            )}
          </div>

          {/* Deliberations */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">Deliberations</h3>
            {delibArray.length > 0 ? (
              <div className="space-y-4">
                {delibArray.map(delib => (
                  <DeliberationCard key={delib.deliberation_id} delib={delib} />
                ))}
              </div>
            ) : (
              <EmptyState
                title="No active deliberations"
                description="Start a deliberation from the API to see real-time positions and arguments"
                icon="💬"
                size="sm"
              />
            )}
          </div>
        </div>

        {/* Right: Event feed */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Event Feed</h3>
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-3 max-h-[600px] overflow-y-auto">
            {eventFeed.length > 0 ? (
              <div className="space-y-1">
                {eventFeed.slice(0, 50).map((entry, idx) => (
                  <EventFeedRow key={`${entry.id}-${entry.timestamp}-${idx}`} entry={entry} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                Waiting for events…
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveDeliberationPanel;
