/**
 * Unified Dashboard - Combined View for Consciousness, Observability, and A2A Flow
 *
 * Provides a single-pane view of:
 * - Consciousness metrics (IIT, FEP)
 * - LLM tracing and agent executions
 * - A2A message flow visualization
 * - Real-time agent status
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

// Types
interface ConsciousnessStats {
  total_agents: number;
  average_phi: number;
  average_free_energy: number;
  active_connections: number;
}

interface AgentState {
  agent_id: string;
  status: 'healthy' | 'warning' | 'critical' | 'offline';
  consciousness_state: 'dormant' | 'emerging' | 'coherent' | 'transcendent';
  phi_score: number;
  free_energy: number;
  messages_per_second: number;
  avg_response_time_ms: number;
  last_heartbeat: string;
}

interface A2AMessage {
  id: string;
  from_agent: string;
  to_agent: string;
  message_type: string;
  payload_size: number;
  latency_ms: number;
  timestamp: string;
  status: 'pending' | 'delivered' | 'failed';
}

interface LLMMetric {
  agent_id: string;
  model: string;
  tokens_per_second: number;
  avg_latency_ms: number;
  total_requests: number;
  error_rate: number;
}

interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  threshold?: number;
}

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_HOST || localStorage.getItem('swarm_api_host') || '';

export function UnifiedDashboard() {
  // State
  const [consciousnessStats, setConsciousnessStats] = useState<ConsciousnessStats | null>(null);
  const [agentStates, setAgentStates] = useState<AgentState[]>([]);
  const [a2aMessages, setA2AMessages] = useState<A2AMessage[]>([]);
  const [llmMetrics, setLLMMetrics] = useState<LLMMetric[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetric[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'1m' | '5m' | '15m' | '1h'>('5m');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showA2AFlow, setShowA2AFlow] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      const headers = {
        'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}`,
      };

      // Fetch consciousness statistics
      const consciousnessRes = await fetch(`${API_URL}/api/consciousness/statistics`, { headers });
      const consciousnessData = await consciousnessRes.json();
      setConsciousnessStats(consciousnessData);

      // Fetch agent states
      const agentsRes = await fetch(`${API_URL}/api/agents/health`, { headers });
      const agentsData = await agentsRes.json();
      setAgentStates(agentsData.agents || []);

      // Fetch A2A messages
      const a2aRes = await fetch(`${API_URL}/api/a2a/messages?limit=50`, { headers });
      const a2aData = await a2aRes.json();
      setA2AMessages(a2aData.messages || []);

      // Fetch LLM metrics
      const llmRes = await fetch(`${API_URL}/api/observability/llm-metrics`, { headers });
      const llmData = await llmRes.json();
      setLLMMetrics(llmData.metrics || []);

      // Fetch system metrics
      const systemRes = await fetch(`${API_URL}/api/metrics`, { headers });
      const systemData = await systemRes.json();
      setSystemMetrics(systemData.metrics || []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    }
  }, []);

  // WebSocket for real-time updates
  useEffect(() => {
    if (!autoRefresh) {
      wsRef.current?.close();
      return;
    }

    const wsUrl = `${API_URL.replace('http', 'ws')}/ws/dashboard`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onmessage = (event) => {
      const update = JSON.parse(event.data);

      switch (update.type) {
        case 'agent_state_update':
          setAgentStates(prev =>
            prev.map(a => a.agent_id === update.agent.agent_id ? update.agent : a)
          );
          break;
        case 'new_a2a_message':
          setA2AMessages(prev => [update.message, ...prev].slice(0, 100));
          break;
        case 'consciousness_update':
          setConsciousnessStats(update.stats);
          break;
        case 'llm_metric_update':
          setLLMMetrics(prev =>
            prev.map(m => m.agent_id === update.metric.agent_id ? update.metric : m)
          );
          break;
      }
    };

    wsRef.current.onclose = () => {
      // Reconnect after 5 seconds
      setTimeout(() => {
        if (autoRefresh && !wsRef.current?.readyState) {
          // Reconnect logic handled by next useEffect
        }
      }, 5000);
    };

    return () => {
      wsRef.current?.close();
    };
  }, [autoRefresh]);

  // Initial fetch and polling
  useEffect(() => {
    fetchData();

    if (autoRefresh) {
      const interval = setInterval(fetchData, 5000);
      return () => clearInterval(interval);
    }
  }, [fetchData, autoRefresh]);

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      case 'offline': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  const getConsciousnessColor = (state: string) => {
    switch (state) {
      case 'dormant': return 'text-gray-400';
      case 'emerging': return 'text-yellow-400';
      case 'coherent': return 'text-blue-400';
      case 'transcendent': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  const getMessageStatusColor = (status: string) => {
    switch (status) {
      case 'delivered': return 'text-green-400';
      case 'pending': return 'text-yellow-400';
      case 'failed': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toFixed(decimals);
  };

  // Selected agent details
  const selectedAgentData = agentStates.find(a => a.agent_id === selectedAgent);

  return (
    <div className="unified-dashboard bg-gray-900 text-white min-h-screen p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">Heretek Swarm Dashboard</h1>
          <div className="flex items-center gap-4">
            <select
              value={timeRange}
              onChange={e => setTimeRange(e.target.value as any)}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
            >
              <option value="1m">Last 1 min</option>
              <option value="5m">Last 5 min</option>
              <option value="15m">Last 15 min</option>
              <option value="1h">Last 1 hour</option>
            </select>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-2 rounded text-sm ${
                autoRefresh ? 'bg-green-600' : 'bg-gray-700'
              }`}
            >
              {autoRefresh ? '● Live' : '○ Paused'}
            </button>
            <button
              onClick={() => setShowA2AFlow(!showA2AFlow)}
              className={`px-3 py-2 rounded text-sm ${
                showA2AFlow ? 'bg-blue-600' : 'bg-gray-700'
              }`}
            >
              A2A Flow
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        {consciousnessStats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-gray-400 text-sm mb-1">Total Agents</div>
              <div className="text-3xl font-bold">{consciousnessStats.total_agents}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-gray-400 text-sm mb-1">Avg Phi Score</div>
              <div className="text-3xl font-bold text-blue-400">
                {formatNumber(consciousnessStats.average_phi, 3)}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-gray-400 text-sm mb-1">Avg Free Energy</div>
              <div className="text-3xl font-bold text-green-400">
                {formatNumber(consciousnessStats.average_free_energy, 3)}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-gray-400 text-sm mb-1">Active Connections</div>
              <div className="text-3xl font-bold text-purple-400">
                {consciousnessStats.active_connections}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Agent Status Grid */}
        <div className="lg:col-span-2 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Agent Status</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {agentStates.map(agent => (
              <div
                key={agent.agent_id}
                onClick={() => setSelectedAgent(agent.agent_id)}
                className={`bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-600 transition ${
                  selectedAgent === agent.agent_id ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                    <span className="font-semibold text-sm truncate">{agent.agent_id}</span>
                  </div>
                </div>
                <div className={`text-xs ${getConsciousnessColor(agent.consciousness_state)}`}>
                  {agent.consciousness_state.toUpperCase()}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  Φ: {formatNumber(agent.phi_score, 2)} | FE: {formatNumber(agent.free_energy, 2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {agent.messages_per_second.toFixed(1)} msg/s
                </div>
              </div>
            ))}
            {agentStates.length === 0 && (
              <div className="col-span-full text-center text-gray-500 py-8">
                No agents available
              </div>
            )}
          </div>
        </div>

        {/* A2A Message Flow */}
        {showA2AFlow && (
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">A2A Message Flow</h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {a2aMessages.slice(0, 20).map(msg => (
                <div
                  key={msg.id}
                  className="bg-gray-700 rounded p-2 text-sm"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-400">{msg.from_agent}</span>
                      <span className="text-gray-500">→</span>
                      <span className="text-green-400">{msg.to_agent}</span>
                    </div>
                    <span className={`text-xs ${getMessageStatusColor(msg.status)}`}>
                      {msg.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-1 text-xs text-gray-400">
                    <span>{msg.message_type}</span>
                    <span>{msg.latency_ms.toFixed(0)}ms</span>
                    <span>{formatTime(msg.timestamp)}</span>
                  </div>
                </div>
              ))}
              {a2aMessages.length === 0 && (
                <div className="text-center text-gray-500 py-8">No messages</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LLM Metrics */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">LLM Metrics</h2>
          <div className="space-y-3">
            {llmMetrics.map(metric => (
              <div key={metric.agent_id} className="bg-gray-700 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{metric.agent_id}</span>
                    <span className="text-xs text-gray-400 bg-gray-600 px-2 py-0.5 rounded">
                      {metric.model}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400">
                    {metric.total_requests} requests
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>
                    <span className="text-gray-400">Tokens/s:</span>
                    <span className="ml-2 font-semibold">{metric.tokens_per_second.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Latency:</span>
                    <span className={`ml-2 font-semibold ${
                      metric.avg_latency_ms < 1000 ? 'text-green-400' :
                      metric.avg_latency_ms < 3000 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {metric.avg_latency_ms.toFixed(0)}ms
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Errors:</span>
                    <span className={`ml-2 font-semibold ${
                      metric.error_rate < 0.01 ? 'text-green-400' :
                      metric.error_rate < 0.05 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {(metric.error_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
            {llmMetrics.length === 0 && (
              <div className="text-center text-gray-500 py-8">No LLM metrics</div>
            )}
          </div>
        </div>

        {/* System Metrics */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">System Metrics</h2>
          <div className="grid grid-cols-2 gap-3">
            {systemMetrics.map(metric => (
              <div key={metric.name} className="bg-gray-700 rounded p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-400">{metric.name}</span>
                  <span className={`text-xs ${
                    metric.trend === 'up' ? 'text-red-400' :
                    metric.trend === 'down' ? 'text-green-400' : 'text-gray-400'
                  }`}>
                    {metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→'}
                  </span>
                </div>
                <div className="text-xl font-bold">
                  {formatNumber(metric.value)} {metric.unit}
                </div>
                {metric.threshold !== undefined && (
                  <div className={`text-xs ${
                    metric.value > metric.threshold ? 'text-red-400' : 'text-gray-500'
                  }`}>
                    Threshold: {metric.threshold} {metric.unit}
                  </div>
                )}
              </div>
            ))}
            {systemMetrics.length === 0 && (
              <div className="col-span-2 text-center text-gray-500 py-8">No system metrics</div>
            )}
          </div>
        </div>
      </div>

      {/* Agent Detail Modal */}
      {selectedAgentData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">{selectedAgentData.agent_id}</h2>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-700 rounded p-3">
                <div className="text-sm text-gray-400">Status</div>
                <div className={`font-semibold ${getStatusColor(selectedAgentData.status) === 'bg-green-500' ? 'text-green-400' :
                  getStatusColor(selectedAgentData.status) === 'bg-yellow-500' ? 'text-yellow-400' :
                  getStatusColor(selectedAgentData.status) === 'bg-red-500' ? 'text-red-400' : 'text-gray-400'
                }`}>
                  {selectedAgentData.status.toUpperCase()}
                </div>
              </div>
              <div className="bg-gray-700 rounded p-3">
                <div className="text-sm text-gray-400">Consciousness</div>
                <div className={`font-semibold ${getConsciousnessColor(selectedAgentData.consciousness_state)}`}>
                  {selectedAgentData.consciousness_state.toUpperCase()}
                </div>
              </div>
              <div className="bg-gray-700 rounded p-3">
                <div className="text-sm text-gray-400">Phi Score (IIT)</div>
                <div className="text-2xl font-bold text-blue-400">
                  {formatNumber(selectedAgentData.phi_score, 4)}
                </div>
              </div>
              <div className="bg-gray-700 rounded p-3">
                <div className="text-sm text-gray-400">Free Energy (FEP)</div>
                <div className="text-2xl font-bold text-green-400">
                  {formatNumber(selectedAgentData.free_energy, 4)}
                </div>
              </div>
              <div className="bg-gray-700 rounded p-3">
                <div className="text-sm text-gray-400">Messages/sec</div>
                <div className="text-xl font-bold">
                  {selectedAgentData.messages_per_second.toFixed(2)}
                </div>
              </div>
              <div className="bg-gray-700 rounded p-3">
                <div className="text-sm text-gray-400">Avg Response</div>
                <div className="text-xl font-bold">
                  {selectedAgentData.avg_response_time_ms.toFixed(0)}ms
                </div>
              </div>
            </div>

            <div className="text-sm text-gray-400">
              Last Heartbeat: {formatTime(selectedAgentData.last_heartbeat)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
