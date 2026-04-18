/**
 * AgentDetailDrawer - Slide-in detail panel for agent inspection
 *
 * Slides in from the right when an agent is selected. Displays four tabs:
 * - Consciousness: phi score, FEP metrics, consciousness state badge
 * - Memory: placeholder (backend endpoint not yet confirmed)
 * - Tools/MCP: placeholder (backend endpoint not yet confirmed)
 * - Tasks: placeholder (backend endpoint not yet confirmed)
 *
 * Data refreshes via polling every 10s while open (via useAgentDetail hook).
 * Gracefully degrades: individual sections show "unavailable" when their endpoint fails,
 * without crashing the drawer.
 */

import { useState } from 'react';
import { useAgentDetail } from './useAgentDetail';

interface AgentDetailDrawerProps {
  /** The selected agent ID. Pass null to hide the drawer. */
  agentId: string | null;
  /** Called when the user clicks the close button. */
  onClose: () => void;
}

// ----------------------------------------------------------------------------
// Tab definitions
// ----------------------------------------------------------------------------
type TabId = 'consciousness' | 'memory' | 'tools' | 'tasks';

const TABS: { id: TabId; label: string }[] = [
  { id: 'consciousness', label: 'Consciousness' },
  { id: 'memory', label: 'Memory' },
  { id: 'tools', label: 'Tools/MCP' },
  { id: 'tasks', label: 'Tasks' },
];

// ----------------------------------------------------------------------------
// Status badge helpers
// ----------------------------------------------------------------------------
function getStatusDotColor(status: string): string {
  switch (status) {
    case 'idle':    return 'bg-gray-500';
    case 'thinking':return 'bg-blue-500';
    case 'acting':  return 'bg-green-500';
    case 'error':   return 'bg-red-500';
    case 'offline': return 'bg-gray-600';
    default:        return 'bg-gray-500';
  }
}

function getConsciousnessStateColor(state: string): string {
  switch (state) {
    case 'transcendent': return 'bg-purple-900 text-purple-300 border-purple-600';
    case 'coherent':     return 'bg-green-900 text-green-300 border-green-600';
    case 'emerging':     return 'bg-blue-900 text-blue-300 border-blue-600';
    case 'dormant':      return 'bg-gray-800 text-gray-400 border-gray-600';
    default:            return 'bg-gray-800 text-gray-400 border-gray-600';
  }
}

// ----------------------------------------------------------------------------
// Skeleton placeholder (loading state)
// ----------------------------------------------------------------------------
function SkeletonBar({ className = 'h-4 w-full' }: { className?: string }) {
  return <div className={`bg-gray-700 rounded animate-pulse ${className}`} />;
}

// ----------------------------------------------------------------------------
// Tab content components
// ----------------------------------------------------------------------------

function ConsciousnessTabContent({
  consciousness,
  agency,
  loading,
  error,
}: {
  /** consciousness.metrics: null = no metrics yet (404); undefined = not yet loaded */
  consciousness: import('../../api/consciousness').AgentMetrics | null;
  agency: import('../../api/consciousness').AgencyMetrics | null;
  loading: boolean;
  error?: string;
}) {
  // Error state — show error message inline (not a crash)
  if (error && consciousness == null) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 text-sm">Metrics unavailable</p>
        <p className="text-gray-600 text-xs mt-1">{error}</p>
      </div>
    );
  }

  // Loading with no prior data (initial state: consciousness = null, loading = true)
  if (loading && consciousness == null) {
    return (
      <div className="space-y-3 px-1">
        <SkeletonBar className="h-12 w-full" />
        <SkeletonBar className="h-4 w-3/4" />
        <SkeletonBar className="h-4 w-2/3" />
        <SkeletonBar className="h-4 w-4/5" />
        <SkeletonBar className="h-4 w-1/2" />
      </div>
    );
  }

  // null = no metrics yet recorded (404 from backend); treat same as initial "no data" state
  if (consciousness == null) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 text-sm">No metrics available for this agent yet.</p>
      </div>
    );
  }

  // TypeScript narrows consciousness to AgentMetrics here
  const m = consciousness;


  return (
    <div className="space-y-4 px-1">
      {/* Phi score — large hero number */}
      <div className="text-center py-2">
        <div className="text-5xl font-bold text-white">{m.phi_score.toFixed(3)}</div>
        <div className="text-gray-400 text-sm mt-1">Φ Score</div>
      </div>

      {/* State badge */}
      <div className="flex justify-center">
        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getConsciousnessStateColor(m.state)}`}>
          {m.state.charAt(0).toUpperCase() + m.state.slice(1)}
        </span>
      </div>

      {/* FEP Metrics */}
      <div>
        <h4 className="text-gray-400 text-xs font-semibold uppercase tracking-wide mb-2">
          FEP Metrics
        </h4>
        <div className="bg-gray-800 rounded-lg p-3 space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-400 text-sm">Free Energy</span>
            <span className="text-white font-mono text-sm">
              {m.fep_metrics.free_energy.toFixed(4)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400 text-sm">Prediction Accuracy</span>
            <span className="text-white font-mono text-sm">
              {m.fep_metrics.prediction_accuracy.toFixed(4)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400 text-sm">Surprise</span>
            <span className="text-white font-mono text-sm">
              {m.fep_metrics.surprise.toFixed(4)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400 text-sm">Belief Precision</span>
            <span className="text-white font-mono text-sm">
              {m.fep_metrics.belief_precision.toFixed(4)}
            </span>
          </div>
        </div>
      </div>

      {/* Agency metrics */}
      {agency && (
        <div>
          <h4 className="text-gray-400 text-xs font-semibold uppercase tracking-wide mb-2">
            Agency
          </h4>
          <div className="bg-gray-800 rounded-lg p-3 space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Agency Score</span>
              <span className="text-white font-mono text-sm">{agency.agency_score.toFixed(4)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Autonomy Score</span>
              <span className="text-white font-mono text-sm">{agency.autonomy_score.toFixed(4)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Decision Count</span>
              <span className="text-white font-mono text-sm">{agency.decision_count}</span>
            </div>
            {agency.last_decision && (
              <div className="flex justify-between">
                <span className="text-gray-400 text-sm">Last Decision</span>
                <span className="text-gray-300 text-xs font-mono">
                  {new Date(agency.last_decision).toLocaleTimeString()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Last updated */}
      <div className="text-center">
        <span className="text-gray-600 text-xs">
          Updated {new Date(m.timestamp).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}

function PlaceholderTab({ message }: { message: string }) {
  return (
    <div className="text-center py-8">
      <p className="text-gray-500 text-sm">{message}</p>
    </div>
  );
}

// ----------------------------------------------------------------------------
// Main drawer component
// ----------------------------------------------------------------------------
export function AgentDetailDrawer({ agentId, onClose }: AgentDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState<TabId>('consciousness');

  // agentId null = drawer not rendered
  const { data, loading, errors } = useAgentDetail(agentId);

  return (
    <div
      // Slide in from right: start off-screen, slide in when rendered
      className="absolute top-0 right-0 h-full w-96 bg-gray-900 border-l border-gray-700 shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out"
      style={{ transform: 'translateX(0)' }}
    >
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-3 min-w-0">
          {/* Agent type icon */}
          <span className="text-2xl flex-shrink-0">
            {data?.agent ? getAgentIcon(data.agent.type) : '🤖'}
          </span>
          <div className="min-w-0">
            <h2 className="text-white font-semibold text-sm truncate">
              {data?.agent?.type ?? agentId ?? 'Agent'}
            </h2>
            {data?.agent && (
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusDotColor(data.agent.status)}`} />
                <span className="text-gray-400 text-xs capitalize">{data.agent.status}</span>
              </div>
            )}
          </div>
        </div>
        {/* Close button */}
        <button
          onClick={onClose}
          aria-label="Close agent detail drawer"
          className="flex-shrink-0 text-gray-400 hover:text-white p-1 rounded transition-colors"
        >
          ✕
        </button>
      </div>

      {/* ── Tab bar ────────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-b border-gray-700">
        <nav className="flex" role="tablist">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-2.5 text-xs font-medium text-center transition-colors relative ${
                activeTab === tab.id
                  ? 'text-blue-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* ── Tab content ────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-4" role="tabpanel">
        {activeTab === 'consciousness' && (
          <ConsciousnessTabContent
            consciousness={data?.consciousness ?? null}
            agency={data?.agency ?? null}
            loading={loading}
            error={errors.consciousness}
          />
        )}
        {activeTab === 'memory' && (
          <PlaceholderTab message="Memory metrics not available" />
        )}
        {activeTab === 'tools' && (
          <PlaceholderTab message="Tools/MCP not available" />
        )}
        {activeTab === 'tasks' && (
          <PlaceholderTab message="Tasks not available" />
        )}
      </div>

      {/* ── Footer: polling indicator ─────────────────────────── */}
      {agentId !== null && (
        <div className="flex-shrink-0 px-4 py-2 border-t border-gray-800 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-gray-600 text-xs">Polling every 10s</span>
          {loading && data && (
            <span className="ml-auto text-gray-600 text-xs">Refreshing…</span>
          )}
        </div>
      )}
    </div>
  );
}

// Small icon lookup (mirrors AgentNode.tsx)
function getAgentIcon(agentType: string): string {
  const icons: Record<string, string> = {
    steward: '🎯',
    alpha: '🔬',
    beta: '✅',
    charlie: '🎭',
    historian: '📚',
    metis: '🧠',
    empath: '💝',
    perceiver: '👁️',
    default: '🤖',
  };
  return icons[agentType?.toLowerCase()] ?? icons.default;
}

export default AgentDetailDrawer;
