/**
 * Node Configuration Panel - Form-based agent configuration
 */

import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { AgentData, ConsciousnessMetrics } from '../../stores/canvasStore';

interface NodeConfigPanelProps {
  node: Node<AgentData> | null;
  onClose: () => void;
  onSave?: (nodeId: string, config: Partial<AgentData>) => void;
}

export function NodeConfigPanel({ node, onClose, onSave }: NodeConfigPanelProps) {
  const [config, setConfig] = useState<Partial<AgentData>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (node) {
      setConfig(node.data);
    }
  }, [node]);

  if (!node) return null;

  const handleSave = async () => {
    setSaving(true);
    try {
      onSave?.(node.id, config);
    } finally {
      setSaving(false);
    }
  };

  const statusColors = {
    idle: 'bg-gray-500',
    thinking: 'bg-blue-500',
    acting: 'bg-green-500',
    error: 'bg-red-500',
    offline: 'bg-gray-700',
  };

  const agentIcons: Record<string, string> = {
    steward: '🎯',
    alpha: '🔬',
    beta: '✅',
    charlie: '🎭',
    historian: '📚',
    metis: '🧠',
    empath: '💝',
    perceiver: '👁️',
    echo: '🔊',
    explorer: '🧭',
    examiner: '📋',
    dreamer: '💭',
    coder: '💻',
    sentinel: '🛡️',
    'sentinel-prime': '🛡️⚡',
    arbiter: '⚖️',
    coordinator: '🔄',
    nexus: '🔗',
    catalyst: '⚗️',
    chronos: '⏰',
    prism: '🔮',
    'habit-forge': '⚒️',
    'perceiver-plus': '👁️🧠',
  };

  const renderMetricsBar = (label: string, value: number, color: string) => (
    <div className="mb-2">
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-white font-mono">{value.toFixed(3)}</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${color}`}
          style={{ width: `${Math.min(100, value * 100)}%` }}
        />
      </div>
    </div>
  );

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-gray-800 border-l border-gray-700 shadow-xl z-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
        <h2 className="text-white font-bold flex items-center gap-2">
          <span className="text-2xl">
            {agentIcons[config.agentType as string] || '🤖'}
          </span>
          Agent Configuration
        </h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Agent Info */}
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
          <h3 className="text-gray-400 text-sm mb-2">Agent Information</h3>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-gray-500">ID</label>
              <div className="text-white font-mono text-sm truncate">
                {config.agentId}
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500">Type</label>
              <div className="text-white capitalize">
                {config.agentType?.replace('-', ' ')}
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500">Status</label>
              <div className="flex items-center gap-2 mt-1">
                <div
                  className={`w-3 h-3 rounded-full ${statusColors[config.status as keyof typeof statusColors] || 'bg-gray-500'}`}
                />
                <span className="text-white capitalize">{config.status}</span>
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500">Last Activity</label>
              <div className="text-gray-400 text-sm">
                {config.lastActivity
                  ? new Date(config.lastActivity).toLocaleString()
                  : 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {/* Consciousness Metrics */}
        {config.consciousnessMetrics && (
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-gray-400 text-sm mb-3">Consciousness Metrics</h3>
            {config.consciousnessMetrics && renderMetricsBar(
              'GWT (Global Workspace)',
              config.consciousnessMetrics.gwt_score,
              'bg-blue-500'
            )}
            {renderMetricsBar(
              'Φ (Integrated Information)',
              config.consciousnessMetrics.phi_value,
              'bg-purple-500'
            )}
            {renderMetricsBar(
              'AST (Attention Schema)',
              config.consciousnessMetrics.ast_competence,
              'bg-green-500'
            )}
            {renderMetricsBar(
              'FEP (Free Energy)',
              1 - config.consciousnessMetrics.free_energy,
              'bg-orange-500'
            )}
            
            {/* Composite Score */}
            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-gray-400 text-sm">Composite Score</span>
                <span className="text-2xl font-bold text-white">
                  {(
                    ((config.consciousnessMetrics.gwt_score +
                      config.consciousnessMetrics.phi_value +
                      config.consciousnessMetrics.ast_competence +
                      (1 - config.consciousnessMetrics.free_energy)) /
                      4) *
                    100
                  ).toFixed(1)}
                  %
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Message Statistics */}
        {config.messageCount !== undefined && (
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-gray-400 text-sm mb-2">Message Statistics</h3>
            <div className="text-3xl font-bold text-white">
              💬 {config.messageCount}
            </div>
            <div className="text-gray-500 text-xs mt-1">Total messages processed</div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-4 border-t border-gray-700">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default NodeConfigPanel;
