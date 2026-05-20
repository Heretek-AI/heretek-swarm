/**
 * Real-time Dashboard - Live Agent Monitoring
 *
 * Provides real-time updates for:
 * - Agent status and health
 * - Memory statistics
 * - A2A message flow
 * - Consensus state
 * - System health
 * - Performance metrics (actor processing + DB query latency)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { PerformancePanel } from '../PerformancePanel';

/**
 * Validates that a URL is safe for use in client-side requests.
 * Returns the URL if it starts with '/' (relative) or http(s):// (absolute),
 * otherwise returns empty string to prevent javascript: or data: URLs.
 */
function _safeUrl(raw: string): string {
  if (!raw || typeof raw !== 'string') return '';
  const trimmed = raw.trim();
  if (trimmed.startsWith('/') || /^https?:\/\//i.test(trimmed)) return trimmed;
  // Reject non-http schemes (javascript:, data:, etc.)
  return '';
}

interface Agent {
  id: string;
  type: string;
  status: 'active' | 'inactive' | 'error' | 'starting';
  state: string;
  capabilities: string[];
  topics: string[];
  last_heartbeat: string;
  message_count: number;
  error_count: number;
}

interface MemoryStats {
  total_entries: number;
  episodic_count: number;
  semantic_count: number;
  procedural_count: number;
  avg_importance: number;
  p95_latency_ms: number;
}

interface A2AMessage {
  id: string;
  from_agent: string;
  to_agent: string;
  content: string;
  timestamp: string;
  type: string;
}

interface ConsensusState {
  process_id: string;
  state: string;
  participants: number;
  votes_collected: number;
  required_votes: number;
  result?: string;
}

interface SystemHealth {
  gateway: boolean;
  redis: boolean;
  postgres: boolean;
  qdrant: boolean;
  uptime_seconds: number;
}

interface DashboardData {
  agents: Agent[];
  memory_stats: MemoryStats;
  messages: A2AMessage[];
  consensus: ConsensusState[];
  health: SystemHealth;
}

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = _safeUrl(import.meta.env.VITE_API_HOST || localStorage.getItem('swarm_api_host') || '');

export function Dashboard() {
  const [data, setData] = useState<DashboardData>({
    agents: [],
    memory_stats: {
      total_entries: 0,
      episodic_count: 0,
      semantic_count: 0,
      procedural_count: 0,
      avg_importance: 0,
      p95_latency_ms: 0,
    },
    messages: [],
    consensus: [],
    health: {
      gateway: false,
      redis: false,
      postgres: false,
      qdrant: false,
      uptime_seconds: 0,
    },
  });
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial data
  const fetchInitialData = useCallback(async () => {
    try {
      // Fetch agents
      const agentsRes = await fetch(`${API_URL}/api/agents`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}` },
      });
      const agentsData = await agentsRes.json();

      // Fetch memory stats
      const memoryRes = await fetch(`${API_URL}/api/memory`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}` },
      });
      const memoryData = await memoryRes.json();

      // Fetch A2A messages
      const messagesRes = await fetch(`${API_URL}/api/a2a/messages?limit=50`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}` },
      });
      const messagesData = await messagesRes.json();

      // Fetch health
      const healthRes = await fetch(`${API_URL}/api/health`);
      const healthData = await healthRes.json();

      setData(prev => ({
        ...prev,
        agents: agentsData.agents || [],
        memory_stats: memoryData.stats || prev.memory_stats,
        messages: messagesData.messages || [],
        health: {
          gateway: healthData.gateway?.status === 'healthy',
          redis: healthData.redis?.status === 'healthy',
          postgres: healthData.postgres?.status === 'healthy',
          qdrant: healthData.qdrant?.status === 'healthy',
          uptime_seconds: healthData.uptime_seconds || 0,
        },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch initial data');
    }
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    fetchInitialData();

    const wsUrl = `${API_URL.replace('http', 'ws')}/ws/dashboard`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);

        setData(prev => {
          const newData = { ...prev };

          switch (update.type) {
            case 'agent_update':
              newData.agents = prev.agents.map(agent =>
                agent.id === update.agent.id ? update.agent : agent
              );
              break;

            case 'agent_spawned':
              newData.agents = [...prev.agents, update.agent];
              break;

            case 'agent_terminated':
              newData.agents = prev.agents.filter(a => a.id !== update.agent_id);
              break;

            case 'a2a_message':
              newData.messages = [update.message, ...prev.messages].slice(0, 100);
              break;

            case 'memory_update':
              newData.memory_stats = update.stats;
              break;

            case 'consensus_update':
              newData.consensus = prev.consensus.map(c =>
                c.process_id === update.consensus.process_id ? update.consensus : c
              );
              if (!prev.consensus.find(c => c.process_id === update.consensus.process_id)) {
                newData.consensus = [...prev.consensus, update.consensus];
              }
              break;

            case 'health_update':
              newData.health = update.health;
              break;
          }

          return newData;
        });
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('WebSocket connection error');
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [fetchInitialData]);

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-500';
      case 'inactive': return 'text-gray-500';
      case 'error': return 'text-red-500';
      case 'starting': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  const getHealthColor = (healthy: boolean) => {
    return healthy ? 'bg-green-500' : 'bg-red-500';
  };

  return (
    <div className="dashboard p-6 bg-gray-900 text-white min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">The Collective Dashboard</h1>
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm">{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
        {error && (
          <div className="mt-2 p-2 bg-red-900/50 border border-red-500 rounded text-sm">
            {error}
          </div>
        )}
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-400">Gateway</span>
            <span className={`w-2 h-2 rounded-full ${getHealthColor(data.health.gateway)}`} />
          </div>
          <div className="text-lg font-semibold">{data.health.gateway ? 'Healthy' : 'Unhealthy'}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-400">Redis</span>
            <span className={`w-2 h-2 rounded-full ${getHealthColor(data.health.redis)}`} />
          </div>
          <div className="text-lg font-semibold">{data.health.redis ? 'Healthy' : 'Unhealthy'}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-400">PostgreSQL</span>
            <span className={`w-2 h-2 rounded-full ${getHealthColor(data.health.postgres)}`} />
          </div>
          <div className="text-lg font-semibold">{data.health.postgres ? 'Healthy' : 'Unhealthy'}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-400">Qdrant</span>
            <span className={`w-2 h-2 rounded-full ${getHealthColor(data.health.qdrant)}`} />
          </div>
          <div className="text-lg font-semibold">{data.health.qdrant ? 'Healthy' : 'Unhealthy'}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-400">Uptime</span>
          </div>
          <div className="text-lg font-semibold">{formatUptime(data.health.uptime_seconds)}</div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agents Panel */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Agents ({data.agents.length})</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {data.agents.map(agent => (
              <div key={agent.id} className="bg-gray-700 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{agent.id}</span>
                    <span className={`text-sm ${getStatusColor(agent.status)}`}>
                      {agent.status}
                    </span>
                  </div>
                  <span className="text-sm text-gray-400">{agent.type}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                  <div>Messages: {agent.message_count}</div>
                  <div>Errors: {agent.error_count}</div>
                  <div>Capabilities: {agent.capabilities.length}</div>
                  <div>Topics: {agent.topics.length}</div>
                </div>
              </div>
            ))}
            {data.agents.length === 0 && (
              <div className="text-center text-gray-500 py-8">No active agents</div>
            )}
          </div>
        </div>

        {/* Memory Stats */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Memory Statistics</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Total Entries</div>
              <div className="text-2xl font-bold">{data.memory_stats.total_entries}</div>
            </div>
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Avg Importance</div>
              <div className="text-2xl font-bold">
                {data.memory_stats.avg_importance.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Episodic</div>
              <div className="text-2xl font-bold">{data.memory_stats.episodic_count}</div>
            </div>
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Semantic</div>
              <div className="text-2xl font-bold">{data.memory_stats.semantic_count}</div>
            </div>
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">Procedural</div>
              <div className="text-2xl font-bold">{data.memory_stats.procedural_count}</div>
            </div>
            <div className="bg-gray-700 rounded p-3">
              <div className="text-sm text-gray-400">P95 Latency</div>
              <div className="text-2xl font-bold">
                {data.memory_stats.p95_latency_ms.toFixed(0)}ms
              </div>
            </div>
          </div>
        </div>

        {/* A2A Messages */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">A2A Message Flow</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {data.messages.map(msg => (
              <div key={msg.id} className="bg-gray-700 rounded p-2 text-sm">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold">{msg.from_agent}</span>
                  <span className="text-gray-400">→</span>
                  <span className="font-semibold">{msg.to_agent}</span>
                  <span className="text-xs text-gray-500 ml-auto">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-gray-300 truncate">{msg.content}</div>
              </div>
            ))}
            {data.messages.length === 0 && (
              <div className="text-center text-gray-500 py-8">No messages</div>
            )}
          </div>
        </div>

        {/* Consensus State */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Consensus Processes</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {data.consensus.map(consensus => (
              <div key={consensus.process_id} className="bg-gray-700 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{consensus.process_id}</span>
                  <span className="text-sm text-gray-400">{consensus.state}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-600 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{
                        width: `${(consensus.votes_collected / consensus.required_votes) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm text-gray-400">
                    {consensus.votes_collected}/{consensus.required_votes}
                  </span>
                </div>
                {consensus.result && (
                  <div className="mt-2 text-sm text-green-400">
                    Result: {consensus.result}
                  </div>
                )}
              </div>
            ))}
            {data.consensus.length === 0 && (
              <div className="text-center text-gray-500 py-8">No active consensus</div>
            )}
          </div>
        </div>
      </div>

      {/* Performance Metrics (full-width below main grid) */}
      <div className="mt-6">
        <PerformancePanel />
      </div>
    </div>
  );
}
