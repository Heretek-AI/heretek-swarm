/**
 * AgentStatusGrid - Grid View of All 23 Agent Statuses
 * 
 * Displays all agents in a responsive grid with status indicators,
 * icons, and last activity timestamps.
 */

import React, { useState, useMemo } from 'react';

export type AgentStatus = 'idle' | 'thinking' | 'acting' | 'error';

export interface Agent {
  id: string;
  type: string;
  status: AgentStatus;
  lastActivity: string;
  tier?: number;
  description?: string;
}

export interface AgentStatusGridProps {
  agents?: Agent[];
  onAgentClick?: (agent: Agent) => void;
  showDescriptions?: boolean;
  compact?: boolean;
}

interface StatusConfig {
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
  pulse: boolean;
}

const STATUS_CONFIG: Record<AgentStatus, StatusConfig> = {
  idle: {
    color: '#9CA3AF',
    bgColor: '#374151',
    borderColor: '#6B7280',
    label: 'Idle',
    pulse: false,
  },
  thinking: {
    color: '#60A5FA',
    bgColor: '#1E3A5F',
    borderColor: '#3B82F6',
    label: 'Thinking',
    pulse: true,
  },
  acting: {
    color: '#4ADE80',
    bgColor: '#14532D',
    borderColor: '#22C55E',
    label: 'Acting',
    pulse: true,
  },
  error: {
    color: '#F87171',
    bgColor: '#7F1D1D',
    borderColor: '#EF4444',
    label: 'Error',
    pulse: false,
  },
};

const AGENT_ICONS: Record<string, string> = {
  steward: '🎯',
  alpha: '🔬',
  beta: '✅',
  charlie: '⚔️',
  historian: '📚',
  metis: '🧠',
  empath: '💚',
  perceiver: '👁️',
  echo: '🔊',
  explorer: '🧭',
  examiner: '🔍',
  dreamer: '💭',
  coder: '💻',
  sentinel: '🛡️',
  'sentinel-prime': '🚨',
  arbiter: '⚖️',
  coordinator: '🔄',
  nexus: '🔗',
  catalyst: '⚡',
  chronos: '⏰',
  prism: '🌈',
  'habit-forge': '🔨',
  'perceiver-plus': '📊',
};

const timeAgo = (timestamp: string): string => {
  const now = new Date();
  const past = new Date(timestamp);
  const diff = Math.floor((now.getTime() - past.getTime()) / 1000);
  
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

// Default agents if none provided
const getDefaultAgents = (): Agent[] => [
  // Tier 1
  { id: 'steward-001', type: 'Steward', status: 'idle', lastActivity: new Date().toISOString(), tier: 1, description: 'Governance & orchestration' },
  { id: 'alpha-001', type: 'Alpha', status: 'thinking', lastActivity: new Date().toISOString(), tier: 1, description: 'Deep analysis' },
  { id: 'beta-001', type: 'Beta', status: 'idle', lastActivity: new Date().toISOString(), tier: 1, description: 'Validation' },
  { id: 'charlie-001', type: 'Charlie', status: 'idle', lastActivity: new Date().toISOString(), tier: 1, description: 'Challenge agent' },
  // Tier 2
  { id: 'historian-001', type: 'Historian', status: 'acting', lastActivity: new Date().toISOString(), tier: 2, description: 'Memory management' },
  { id: 'metis-001', type: 'Metis', status: 'idle', lastActivity: new Date().toISOString(), tier: 2, description: 'Strategic planning' },
  { id: 'empath-001', type: 'Empath', status: 'idle', lastActivity: new Date().toISOString(), tier: 2, description: 'Emotional intelligence' },
  { id: 'perceiver-001', type: 'Perceiver', status: 'thinking', lastActivity: new Date().toISOString(), tier: 2, description: 'Multi-modal processing' },
  { id: 'echo-001', type: 'Echo', status: 'idle', lastActivity: new Date().toISOString(), tier: 2, description: 'Communication' },
  // Tier 3
  { id: 'explorer-001', type: 'Explorer', status: 'acting', lastActivity: new Date().toISOString(), tier: 3, description: 'Intelligence gathering' },
  { id: 'examiner-001', type: 'Examiner', status: 'idle', lastActivity: new Date().toISOString(), tier: 3, description: 'Quality assurance' },
  { id: 'dreamer-001', type: 'Dreamer', status: 'thinking', lastActivity: new Date().toISOString(), tier: 3, description: 'Creative solutions' },
  { id: 'coder-001', type: 'Coder', status: 'acting', lastActivity: new Date().toISOString(), tier: 3, description: 'Code generation' },
  // Tier 4
  { id: 'sentinel-001', type: 'Sentinel', status: 'idle', lastActivity: new Date().toISOString(), tier: 4, description: 'Safety validation' },
  { id: 'sentinel-prime-001', type: 'Sentinel Prime', status: 'idle', lastActivity: new Date().toISOString(), tier: 4, description: 'Threat response' },
  { id: 'arbiter-001', type: 'Arbiter', status: 'idle', lastActivity: new Date().toISOString(), tier: 4, description: 'Conflict resolution' },
  // Tier 5
  { id: 'coordinator-001', type: 'Coordinator', status: 'thinking', lastActivity: new Date().toISOString(), tier: 5, description: 'Task synchronization' },
  { id: 'nexus-001', type: 'Nexus', status: 'idle', lastActivity: new Date().toISOString(), tier: 5, description: 'API integration' },
  { id: 'catalyst-001', type: 'Catalyst', status: 'idle', lastActivity: new Date().toISOString(), tier: 5, description: 'Change management' },
  { id: 'chronos-001', type: 'Chronos', status: 'idle', lastActivity: new Date().toISOString(), tier: 5, description: 'Scheduling' },
  // Tier 6
  { id: 'prism-001', type: 'Prism', status: 'idle', lastActivity: new Date().toISOString(), tier: 6, description: 'Multi-perspective analysis' },
  { id: 'habit-forge-001', type: 'Habit Forge', status: 'idle', lastActivity: new Date().toISOString(), tier: 6, description: 'Behavior optimization' },
  { id: 'perceiver-plus-001', type: 'Perceiver+', status: 'idle', lastActivity: new Date().toISOString(), tier: 6, description: 'Advanced analytics' },
];

export function AgentStatusGrid({
  agents,
  onAgentClick,
  showDescriptions = true,
  compact = false,
}: AgentStatusGridProps) {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<AgentStatus | 'all'>('all');

  const agentList = useMemo(() => agents || getDefaultAgents(), [agents]);

  const filteredAgents = useMemo(() => {
    if (statusFilter === 'all') return agentList;
    return agentList.filter(agent => agent.status === statusFilter);
  }, [agentList, statusFilter]);

  const statusCounts = useMemo(() => {
    const counts: Record<AgentStatus | 'all', number> = {
      all: agentList.length,
      idle: 0,
      thinking: 0,
      acting: 0,
      error: 0,
    };
    agentList.forEach(agent => {
      counts[agent.status]++;
    });
    return counts;
  }, [agentList]);

  const handleAgentClick = (agent: Agent) => {
    setSelectedAgent(agent.id);
    onAgentClick?.(agent);
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      {/* Header with filters */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-bold text-lg flex items-center gap-2">
          <span>🤖</span> Agent Status Grid
        </h2>
        
        {/* Status filter buttons */}
        <div className="flex gap-2">
          {(['all', 'idle', 'thinking', 'acting', 'error'] as const).map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`
                px-3 py-1 rounded-full text-xs font-semibold transition-colors
                ${statusFilter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}
              `}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)} 
              ({statusCounts[status]})
            </button>
          ))}
        </div>
      </div>
      
      {/* Agent Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
        {filteredAgents.map(agent => {
          const statusConfig = STATUS_CONFIG[agent.status];
          const icon = AGENT_ICONS[agent.type.toLowerCase()] || '🤖';
          const isSelected = selectedAgent === agent.id;
          
          return (
            <div
              key={agent.id}
              onClick={() => handleAgentClick(agent)}
              className={`
                p-3 rounded-lg border-2 cursor-pointer transition-all duration-200
                hover:scale-105 hover:shadow-lg
                ${isSelected ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-800' : ''}
              `}
              style={{
                backgroundColor: statusConfig.bgColor,
                borderColor: statusConfig.borderColor,
              }}
            >
              {/* Header with icon and status */}
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{icon}</span>
                <div className="flex items-center gap-1">
                  {statusConfig.pulse && (
                    <span
                      className="w-2 h-2 rounded-full animate-pulse"
                      style={{ backgroundColor: statusConfig.color }}
                    />
                  )}
                  <span
                    className="text-xs font-semibold px-2 py-0.5 rounded uppercase"
                    style={{
                      backgroundColor: statusConfig.borderColor,
                      color: statusConfig.color,
                    }}
                  >
                    {statusConfig.label}
                  </span>
                </div>
              </div>
              
              {/* Agent name */}
              <div className="text-white font-bold text-sm mb-1 truncate">
                {agent.type}
              </div>
              
              {/* Agent ID */}
              <div className="text-gray-500 text-xs font-mono truncate mb-1">
                {agent.id}
              </div>
              
              {/* Last activity */}
              <div className="text-gray-400 text-xs">
                {timeAgo(agent.lastActivity)}
              </div>
              
              {/* Description */}
              {showDescriptions && agent.description && (
                <div className="text-gray-500 text-xs mt-2 pt-2 border-t border-gray-600">
                  {agent.description}
                </div>
              )}
              
              {/* Tier badge */}
              {agent.tier && (
                <div className="absolute top-2 right-2">
                  <span className="text-xs bg-gray-900/50 text-gray-400 px-1.5 py-0.5 rounded">
                    T{agent.tier}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Empty state */}
      {filteredAgents.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          <div className="text-4xl mb-2">🔍</div>
          <div>No agents found with status "{statusFilter}"</div>
        </div>
      )}
      
      {/* Summary footer */}
      <div className="mt-4 pt-4 border-t border-gray-700 flex items-center justify-between text-sm">
        <div className="text-gray-400">
          Total: <span className="text-white font-semibold">{agentList.length}</span> agents
        </div>
        <div className="flex gap-4">
          <span className="flex items-center gap-1 text-gray-400">
            <span className="w-2 h-2 rounded-full bg-gray-500" /> Idle: {statusCounts.idle}
          </span>
          <span className="flex items-center gap-1 text-gray-400">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" /> Thinking: {statusCounts.thinking}
          </span>
          <span className="flex items-center gap-1 text-gray-400">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" /> Acting: {statusCounts.acting}
          </span>
          <span className="flex items-center gap-1 text-gray-400">
            <span className="w-2 h-2 rounded-full bg-red-500" /> Error: {statusCounts.error}
          </span>
        </div>
      </div>
    </div>
  );
}

export default AgentStatusGrid;
