/**
 * RealTimeAgentPanel - Live agent monitoring component
 * 
 * Displays real-time status of all 23 agents with:
 * - Online/offline status
 * - Current task indicator
 * - Message count
 * - Consciousness score
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useAgentStatus } from '../hooks/useAgentStatus';
import { useWebSocket } from '../hooks/useWebSocket';

interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  currentTask?: string;
  messagesCount: number;
  consciousnessScore?: number;
  lastActivity?: string;
}

// Status color mapping
const STATUS_COLORS = {
  idle: 'bg-green-500',
  busy: 'bg-yellow-500',
  error: 'bg-red-500',
  offline: 'bg-gray-400',
};

// Agent tier mapping
const AGENT_TIERS = {
  'steward': 'Tier 1 - Core',
  'alpha': 'Tier 1 - Core',
  'beta': 'Tier 1 - Core',
  'charlie': 'Tier 1 - Core',
  'historian': 'Tier 2 - Support',
  'metis': 'Tier 2 - Support',
  'empath': 'Tier 2 - Support',
  'perceiver': 'Tier 2 - Support',
  'echo': 'Tier 2 - Support',
  'explorer': 'Tier 3 - Exploration',
  'examiner': 'Tier 3 - Exploration',
  'dreamer': 'Tier 3 - Exploration',
  'coder': 'Tier 3 - Exploration',
  'sentinel': 'Tier 4 - Security',
  'sentinel-prime': 'Tier 4 - Security',
  'arbiter': 'Tier 4 - Security',
  'coordinator': 'Tier 5 - Coordination',
  'nexus': 'Tier 5 - Coordination',
  'catalyst': 'Tier 5 - Coordination',
  'chronos': 'Tier 5 - Coordination',
  'prism': 'Tier 6 - Enhancement',
  'habit-forge': 'Tier 6 - Enhancement',
  'perceiver-plus': 'Tier 6 - Enhancement',
};

interface RealTimeAgentPanelProps {
  refreshInterval?: number;
  showConsciousness?: boolean;
}

export function RealTimeAgentPanel({ 
  refreshInterval = 5000,
  showConsciousness = true 
}: RealTimeAgentPanelProps) {
  const { agents, loading, error, refetch } = useAgentStatus(refreshInterval);
  const { connectionStatus } = useWebSocket();
  
  // Group agents by tier
  const agentsByTier = agents.reduce((acc, agent) => {
    const tier = AGENT_TIERS[agent.id] || 'Unknown';
    if (!acc[tier]) acc[tier] = [];
    acc[tier].push(agent);
    return acc;
  }, {} as Record<string, AgentStatus[]>);

  const formatLastActivity = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    const diff = Date.now() - new Date(timestamp).getTime();
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    return `${Math.floor(minutes / 60)}h ago`;
  };

  return (
    <div className="real-time-panel bg-slate-900 rounded-lg p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-white">Agent Status</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-400">
            {connectionStatus === 'connected' ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-400">
            {agents.filter(a => a.status === 'idle').length}
          </div>
          <div className="text-xs text-gray-400">Idle</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-yellow-400">
            {agents.filter(a => a.status === 'busy').length}
          </div>
          <div className="text-xs text-gray-400">Busy</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-red-400">
            {agents.filter(a => a.status === 'error').length}
          </div>
          <div className="text-xs text-gray-400">Error</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-gray-400">
            {agents.length}
          </div>
          <div className="text-xs text-gray-400">Total</div>
        </div>
      </div>

      {/* Agents by Tier */}
      <div className="space-y-4">
        {Object.entries(agentsByTier).map(([tier, tierAgents]) => (
          <div key={tier} className="bg-slate-800 rounded-lg p-3">
            <h3 className="text-sm font-semibold text-gray-300 mb-2">{tier}</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {tierAgents.map(agent => (
                <div 
                  key={agent.id}
                  className="bg-slate-700 rounded p-2 flex flex-col gap-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-white capitalize">
                      {agent.id.replace('-', ' ')}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[agent.status]}`} />
                  </div>
                  <div className="text-xs text-gray-400">
                    {agent.currentTask || agent.status}
                  </div>
                  {showConsciousness && agent.consciousnessScore !== undefined && (
                    <div className="flex items-center gap-1">
                      <div className="flex-1 h-1 bg-slate-600 rounded overflow-hidden">
                        <div 
                          className="h-full bg-purple-500 transition-all"
                          style={{ width: `${agent.consciousnessScore * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">
                        {(agent.consciousnessScore * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                  <div className="text-xs text-gray-500">
                    {agent.messagesCount} msgs • {formatLastActivity(agent.lastActivity)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <div className="mt-4 p-3 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
          Error fetching agent status: {error}
        </div>
      )}

      {/* Loading State */}
      {loading && agents.length === 0 && (
        <div className="flex justify-center py-8">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
        </div>
      )}
    </div>
  );
}

export default RealTimeAgentPanel;