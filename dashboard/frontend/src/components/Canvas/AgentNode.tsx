/**
 * Agent Node Component for ReactFlow
 * 
 * Displays individual agent with status indicators.
 * Reference: MiniMax Audit Lines 488-535 (Flowise AgentNode pattern)
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export interface AgentData {
  agentId: string;
  agentType: 'steward' | 'alpha' | 'beta' | 'coder' | 'sentinel' | 'historian';
  status: 'idle' | 'thinking' | 'acting' | 'error';
  lastActivity: string;
}

const statusColors = {
  idle: { border: '#6B7280', bg: '#374151', text: '#9CA3AF' },
  thinking: { border: '#3B82F6', bg: '#1E3A5F', text: '#60A5FA' },
  acting: { border: '#22C55E', bg: '#14532D', text: '#4ADE80' },
  error: { border: '#EF4444', bg: '#7F1D1D', text: '#F87171' },
};

const agentIcons: Record<AgentData['agentType'], string> = {
  steward: '🎯',
  alpha: '🔬',
  beta: '✅',
  coder: '💻',
  sentinel: '🛡️',
  historian: '📚',
};

function AgentNode({ data, selected }: NodeProps<AgentData>) {
  const colors = statusColors[data.status] || statusColors.idle;
  const icon = agentIcons[data.agentType] || '🤖';
  
  const timeAgo = (timestamp: string) => {
    const now = new Date();
    const past = new Date(timestamp);
    const diff = Math.floor((now.getTime() - past.getTime()) / 1000);
    
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div
      className={`
        px-4 py-3 rounded-lg shadow-lg border-2 transition-all duration-200
        ${selected ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-900' : ''}
      `}
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
        minWidth: '220px',
        maxWidth: '280px',
      }}
    >
      {/* Target Handle (input) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-gray-600 !border-2 !border-gray-500"
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span
          className="text-xs font-semibold px-2 py-1 rounded uppercase"
          style={{
            backgroundColor: colors.border,
            color: '#FFFFFF',
          }}
        >
          {data.status}
        </span>
      </div>

      {/* Agent Type */}
      <div className="text-white font-bold text-lg mb-1">
        {data.agentType.charAt(0).toUpperCase() + data.agentType.slice(1)}
      </div>

      {/* Agent ID */}
      <div className="text-gray-400 text-xs font-mono mb-2 truncate">
        {data.agentId}
      </div>

      {/* Last Activity */}
      <div className="text-gray-500 text-xs">
        Active: {timeAgo(data.lastActivity)}
      </div>

      {/* Source Handle (output) */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-gray-600 !border-2 !border-gray-500"
      />
    </div>
  );
}

export default memo(AgentNode);
