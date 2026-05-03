/**
 * Deliberation Page
 *
 * Dashboard page with tab navigation for viewing live deliberation voting
 * and browsing historical deliberations with full audit trails.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LiveDeliberationPanel } from './LiveDeliberationPanel';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { EmptyState } from '../UI/EmptyState';
import { useToast } from '../UI/Toast';
import {
  getConsensusHistory,
  getConsensusRound,
  getConsensusResults,
  type ConsensusHistoryEntry,
  type ConsensusRoundDetail,
} from '../../api/consensus';
import {
  getAuditStatistics,
  getSuccessfulAudits,
  getFailedAudits,
  type AuditStatistics,
  type AuditDecisionRecord,
} from '../../api/deliberation';

// =============================================================================
// Tab navigation
// =============================================================================

type TabId = 'live' | 'history';

interface Tab {
  id: TabId;
  label: string;
  icon: string;
}

const TABS: Tab[] = [
  { id: 'live', label: 'Live', icon: '🔴' },
  { id: 'history', label: 'History', icon: '📜' },
];

// =============================================================================
// Helpers
// =============================================================================

function formatTimestamp(ts: string | null): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

// =============================================================================
// History entry row
// =============================================================================

function HistoryEntryCard({
  entry,
  onSelect,
  isSelected,
}: {
  entry: ConsensusHistoryEntry;
  onSelect: (id: string) => void;
  isSelected: boolean;
}) {
  return (
    <button
      onClick={() => onSelect(entry.id)}
      className={`w-full text-left p-4 rounded-xl border transition-colors ${
        isSelected
          ? 'bg-blue-900/20 border-blue-500/50'
          : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-semibold text-white truncate">
            {entry.topic || 'Untitled Round'}
          </h4>
          <p className="text-xs text-gray-400 mt-1 font-mono">{entry.id.slice(0, 16)}…</p>
        </div>
        <div className="text-right shrink-0">
          {entry.decision && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
              Consensus
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
        <span>🗳️ {entry.vote_count} votes</span>
        {entry.confidence !== null && (
          <span>📊 {(entry.confidence * 100).toFixed(0)}% confidence</span>
        )}
        <span className="ml-auto">{formatTimestamp(entry.completed_at)}</span>
      </div>
      {entry.red_flags.length > 0 && (
        <div className="mt-2 text-xs text-red-400">
          ⚠ {entry.red_flags.length} red flag{entry.red_flags.length !== 1 ? 's' : ''}
        </div>
      )}
    </button>
  );
}

// =============================================================================
// Detail panel for selected history entry
// =============================================================================

function HistoryDetailPanel({ roundId }: { roundId: string }) {
  const [detail, setDetail] = useState<ConsensusRoundDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    getConsensusRound(roundId)
      .then(data => {
        if (!cancelled) setDetail(data);
      })
      .catch(err => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load details');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [roundId]);

  if (loading) return <LoadingSpinner size="sm" message="Loading round details…" />;
  if (error) return <div className="text-sm text-red-400 p-4">{error}</div>;
  if (!detail) return null;

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-bold text-white">{detail.topic || 'Untitled Round'}</h3>
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
          <span className="font-mono">{detail.id}</span>
          <span className={`px-2 py-0.5 rounded-full border ${
            detail.state === 'completed'
              ? 'bg-green-500/20 text-green-400 border-green-500/30'
              : detail.state === 'failed'
              ? 'bg-red-500/20 text-red-400 border-red-500/30'
              : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
          }`}>
            {detail.state}
          </span>
        </div>
      </div>

      {/* Decision */}
      {detail.decision && (
        <div className="p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
          <div className="text-xs text-green-400 font-medium uppercase tracking-wide mb-1">Decision</div>
          <p className="text-sm text-white">{detail.decision}</p>
          {detail.confidence !== null && (
            <p className="text-xs text-green-300 mt-2">
              Confidence: {(detail.confidence * 100).toFixed(1)}%
            </p>
          )}
        </div>
      )}

      {/* Votes */}
      <div>
        <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">
          Votes ({detail.votes.length})
        </h4>
        <div className="space-y-3">
          {detail.votes.map((vote, idx) => (
            <div
              key={`${vote.agent_id}-${idx}`}
              className="p-4 bg-gray-900/50 rounded-lg border border-gray-700/50"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-mono text-gray-300">
                    {vote.agent_id.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{vote.agent_id}</div>
                    <div className="text-xs text-gray-500">{formatTimestamp(vote.timestamp)}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-blue-400">{(vote.confidence * 100).toFixed(0)}%</div>
                  <div className="text-xs text-gray-500">confidence</div>
                </div>
              </div>
              <p className="mt-3 text-sm text-gray-300 bg-gray-800/50 rounded-lg p-3 border border-gray-700/30">
                {vote.decision}
              </p>
              {Object.keys(vote.metadata).length > 0 && (
                <div className="mt-2 text-xs text-gray-500">
                  Metadata: {JSON.stringify(vote.metadata)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Red flags */}
      {detail.red_flags.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-red-400 uppercase tracking-wide mb-3">
            ⚠ Red Flags ({detail.red_flags.length})
          </h4>
          <ul className="space-y-2">
            {detail.red_flags.map((flag, idx) => (
              <li key={idx} className="text-sm text-red-300 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Timeline */}
      <div className="text-xs text-gray-500 pt-4 border-t border-gray-700/50 flex items-center gap-4">
        <span>Created: {formatTimestamp(detail.created_at)}</span>
        {detail.completed_at && <span>Completed: {formatTimestamp(detail.completed_at)}</span>}
      </div>
    </div>
  );
}

// =============================================================================
// Audit Statistics Section
// =============================================================================

function AuditStatsSection() {
  const [stats, setStats] = useState<AuditStatistics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getAuditStatistics()
      .then(data => { if (!cancelled) setStats(data); })
      .catch(() => { /* silently ignore */ })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  if (loading || !stats) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
      <div className="p-3 bg-gray-800/50 border border-gray-700 rounded-lg">
        <div className="text-xs text-gray-400">Total Decisions</div>
        <div className="text-lg font-bold text-white">{stats.total_decisions}</div>
      </div>
      <div className="p-3 bg-gray-800/50 border border-gray-700 rounded-lg">
        <div className="text-xs text-gray-400">Successful</div>
        <div className="text-lg font-bold text-green-400">{stats.successful}</div>
      </div>
      <div className="p-3 bg-gray-800/50 border border-gray-700 rounded-lg">
        <div className="text-xs text-gray-400">Failed</div>
        <div className="text-lg font-bold text-red-400">{stats.failed}</div>
      </div>
      <div className="p-3 bg-gray-800/50 border border-gray-700 rounded-lg">
        <div className="text-xs text-gray-400">Avg Confidence</div>
        <div className="text-lg font-bold text-blue-400">{(stats.average_confidence * 100).toFixed(0)}%</div>
      </div>
      <div className="p-3 bg-gray-800/50 border border-gray-700 rounded-lg">
        <div className="text-xs text-gray-400">Avg Rounds</div>
        <div className="text-lg font-bold text-purple-400">{stats.average_deliberation_rounds.toFixed(1)}</div>
      </div>
    </div>
  );
}

// =============================================================================
// History tab
// =============================================================================

function HistoryTab() {
  const [history, setHistory] = useState<ConsensusHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);
  const toast = useToast();

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getConsensusHistory(limit);
      setHistory(data.consensus_history);
    } catch (err) {
      toast.error('Failed to load history', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [limit, toast]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" message="Loading deliberation history…" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <AuditStatsSection />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* History list */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
              Past Rounds ({history.length})
            </h3>
            <button
              onClick={fetchHistory}
              className="text-xs text-gray-400 hover:text-white transition-colors"
            >
              ↻ Refresh
            </button>
          </div>
          {history.length > 0 ? (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {history.map(entry => (
                <HistoryEntryCard
                  key={entry.id}
                  entry={entry}
                  onSelect={setSelectedId}
                  isSelected={selectedId === entry.id}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No deliberation history"
              description="Completed consensus rounds will appear here with full audit trails"
              icon="📜"
              size="sm"
            />
          )}
        </div>

        {/* Detail panel */}
        <div>
          {selectedId ? (
            <HistoryDetailPanel roundId={selectedId} />
          ) : (
            <div className="flex items-center justify-center h-64 border border-dashed border-gray-700 rounded-xl">
              <p className="text-sm text-gray-500">Select a round to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Deliberation Page
// =============================================================================

export function DeliberationPage() {
  const [activeTab, setActiveTab] = useState<TabId>('live');

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Deliberation</h1>
          <p className="text-gray-400 text-sm mt-1">
            Monitor live agent votes and browse past deliberation audit trails
          </p>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex items-center gap-1 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-1 w-fit">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'live' && <LiveDeliberationPanel />}
      {activeTab === 'history' && <HistoryTab />}
    </div>
  );
}

export default DeliberationPage;
