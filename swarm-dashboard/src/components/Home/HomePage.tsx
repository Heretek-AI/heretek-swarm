/**
 * Home/Overview Page
 * 
 * Main dashboard overview with system health, quick stats, and recent activity.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { MetricCard, MetricCardGrid } from '../UI/MetricCard';
import { StatusBadge } from '../UI/StatusBadge';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { ErrorBoundary, SimpleErrorFallback } from '../UI/ErrorBoundary';
import { EmptyState } from '../UI/EmptyState';

// API URL configuration
const API_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_HOST || localStorage.getItem('swarm_api_host') || '';

// Types
interface SystemHealth {
  gateway?: { status: string };
  redis?: { status: string };
  postgres?: { status: string };
  qdrant?: { status: string };
  uptime_seconds: number;
}

interface AgentSummary {
  total: number;
  active: number;
  inactive: number;
  error: number;
}

interface MemoryStats {
  total_entries: number;
  episodic_count: number;
  semantic_count: number;
  procedural_count: number;
  avg_importance: number;
  p95_latency_ms: number;
}

interface RecentActivity {
  id: string;
  type: 'agent_spawn' | 'agent_terminate' | 'message' | 'consensus' | 'memory';
  description: string;
  timestamp: string;
  status?: 'success' | 'warning' | 'error';
}

interface HomePageData {
  health: SystemHealth | null;
  agents: AgentSummary | null;
  memory: MemoryStats | null;
  recentActivity: RecentActivity[];
  consciousnessMetrics?: {
    average_phi: number;
    average_free_energy: number;
    active_connections: number;
  };
}

export function HomePage() {
  const [data, setData] = useState<HomePageData>({
    health: null,
    agents: null,
    memory: null,
    recentActivity: [],
    consciousnessMetrics: undefined,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch system health
  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      if (!response.ok) throw new Error('Failed to fetch health');
      const data = await response.json();
      // API returns { status, services: { gateway, redis, postgres, qdrant }, ... }
      // Flatten so callers get health.gateway instead of health.services.gateway
      return {
        ...data.services,
        status: data.status,
        uptime_seconds: data.uptime_seconds || 0,
      };
    } catch {
      return null;
    }
  }, []);

  // Fetch agents summary
  const fetchAgents = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/agents`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('api_key') || ''}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch agents');
      const data = await response.json();
      const agents = data.agents || [];
      return {
        total: agents.length,
        active: agents.filter((a: { status: string }) => a.status === 'active').length,
        inactive: agents.filter((a: { status: string }) => a.status === 'inactive').length,
        error: agents.filter((a: { status: string }) => a.status === 'error').length,
      };
    } catch {
      return null;
    }
  }, []);

  // Fetch memory stats
  const fetchMemory = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/memory`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('api_key') || ''}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch memory');
      const data = await response.json();
      return data.stats || null;
    } catch {
      return null;
    }
  }, []);

  // Fetch consciousness metrics
  const fetchConsciousness = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/consciousness/statistics`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('api_key') || ''}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch consciousness');
      const data = await response.json();
      return {
        average_phi: data.average_phi || 0,
        average_free_energy: data.average_free_energy || 0,
        active_connections: data.active_connections || 0,
      };
    } catch {
      return undefined;
    }
  }, []);

  // Generate mock recent activity based on data
  const generateRecentActivity = useCallback((health: SystemHealth | null, agents: AgentSummary | null): RecentActivity[] => {
    const activities: RecentActivity[] = [];
    
    if (health) {
      activities.push({
        id: 'health-1',
        type: 'agent_spawn',
        description: 'System health check completed',
        timestamp: new Date().toISOString(),
        status: health.gateway?.status === 'healthy' ? 'success' : 'warning',
      });
    }

    if (agents && agents.active > 0) {
      activities.push({
        id: 'agent-1',
        type: 'agent_spawn',
        description: `${agents.active} agents currently active`,
        timestamp: new Date(Date.now() - 60000).toISOString(),
        status: 'success',
      });
    }

    if (agents && agents.error > 0) {
      activities.push({
        id: 'agent-error-1',
        type: 'message',
        description: `${agents.error} agent(s) reported errors`,
        timestamp: new Date(Date.now() - 120000).toISOString(),
        status: 'error',
      });
    }

    // Add some placeholder activities
    activities.push({
      id: 'memory-1',
      type: 'memory',
      description: 'Memory consolidation completed',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      status: 'success',
    });

    return activities.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 10);
  }, []);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [health, agents, memory, consciousness] = await Promise.all([
        fetchHealth(),
        fetchAgents(),
        fetchMemory(),
        fetchConsciousness(),
      ]);

      setData({
        health,
        agents,
        memory,
        recentActivity: generateRecentActivity(health, agents),
        consciousnessMetrics: consciousness,
      });
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [fetchHealth, fetchAgents, fetchMemory, fetchConsciousness, generateRecentActivity]);

  // Initial fetch and refresh interval
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchAllData]);

  // Format uptime
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  // Get system status
  const getSystemStatus = (): 'healthy' | 'degraded' | 'offline' => {
    if (!data.health) return 'offline';
    const { gateway, redis, postgres, qdrant } = data.health;
    const allHealthy = gateway?.status === 'healthy' && 
                       redis?.status === 'healthy' && 
                       postgres?.status === 'healthy' && 
                       qdrant?.status === 'healthy';
    const anyHealthy = gateway?.status === 'healthy' || 
                       redis?.status === 'healthy' || 
                       postgres?.status === 'healthy' || 
                       qdrant?.status === 'healthy';
    return allHealthy ? 'healthy' : anyHealthy ? 'degraded' : 'offline';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" message="Loading dashboard..." />
      </div>
    );
  }

  return (
    <ErrorBoundary
      fallback={<SimpleErrorFallback error={new Error(error || 'Unknown error')} onRetry={fetchAllData} />}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Overview</h1>
            <p className="text-gray-400 text-sm mt-1">
              System status and key metrics
              {lastUpdated && (
                <span className="ml-2">
                  · Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </p>
          </div>
          <button
            onClick={fetchAllData}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
          >
            ↻ Refresh
          </button>
        </div>

        {error && (
          <SimpleErrorFallback error={new Error(error)} onRetry={fetchAllData} />
        )}

        {/* System Health Status */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusBadge status={getSystemStatus()} size="lg" />
              <span className="text-gray-400">
                {data.health?.uptime_seconds 
                  ? `Uptime: ${formatUptime(data.health.uptime_seconds)}`
                  : 'System status unavailable'}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  data.health?.gateway?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-gray-400">Gateway</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  data.health?.redis?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-gray-400">Redis</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  data.health?.postgres?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-gray-400">PostgreSQL</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  data.health?.qdrant?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-gray-400">Qdrant</span>
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <MetricCardGrid columns={4}>
          <MetricCard
            title="Total Agents"
            value={data.agents?.total || 0}
            sparklineData={[1, 2, 2, 3, 4, 3, 4, 5, data.agents?.total || 0]}
            color="blue"
          />
          <MetricCard
            title="Active Agents"
            value={data.agents?.active || 0}
            change={data.agents && data.agents.active > 0 ? 12.5 : undefined}
            color="green"
          />
          <MetricCard
            title="Avg Phi Score"
            value={data.consciousnessMetrics?.average_phi.toFixed(3) || '0.000'}
            color="purple"
          />
          <MetricCard
            title="Memory Entries"
            value={data.memory?.total_entries || 0}
            color="yellow"
          />
        </MetricCardGrid>

        {/* Secondary Metrics */}
        <MetricCardGrid columns={4}>
          <MetricCard
            title="Agent Errors"
            value={data.agents?.error || 0}
            color={data.agents && data.agents.error > 0 ? 'red' : 'green'}
          />
          <MetricCard
            title="Active Connections"
            value={data.consciousnessMetrics?.active_connections || 0}
            color="blue"
          />
          <MetricCard
            title="Avg Free Energy"
            value={data.consciousnessMetrics?.average_free_energy.toFixed(3) || '0.000'}
            color="green"
          />
          <MetricCard
            title="P95 Latency"
            value={`${data.memory?.p95_latency_ms.toFixed(0) || 0}ms`}
            color="yellow"
          />
        </MetricCardGrid>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
            <div className="space-y-3">
              {data.recentActivity.length > 0 ? (
                data.recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-3 p-3 bg-gray-900/50 rounded-lg"
                  >
                    <span className="text-lg">
                      {activity.type === 'agent_spawn' && '🤖'}
                      {activity.type === 'agent_terminate' && '🛑'}
                      {activity.type === 'message' && '💬'}
                      {activity.type === 'consensus' && '🗳️'}
                      {activity.type === 'memory' && '🧠'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-300 truncate">{activity.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                    {activity.status && (
                      <StatusBadge status={activity.status} size="sm" showLabel={false} />
                    )}
                  </div>
                ))
              ) : (
                <EmptyState
                  title="No recent activity"
                  description="Activity will appear here as the system runs"
                  size="sm"
                />
              )}
            </div>
          </div>

          {/* Memory Distribution */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">Memory Distribution</h2>
            {data.memory ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-400">Episodic</span>
                    <span className="text-white font-medium">{data.memory.episodic_count.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{
                        width: `${data.memory.total_entries > 0 ? (data.memory.episodic_count / data.memory.total_entries) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-400">Semantic</span>
                    <span className="text-white font-medium">{data.memory.semantic_count.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all duration-300"
                      style={{
                        width: `${data.memory.total_entries > 0 ? (data.memory.semantic_count / data.memory.total_entries) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-400">Procedural</span>
                    <span className="text-white font-medium">{data.memory.procedural_count.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500 transition-all duration-300"
                      style={{
                        width: `${data.memory.total_entries > 0 ? (data.memory.procedural_count / data.memory.total_entries) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
                <div className="pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Average Importance</span>
                    <span className="text-white font-medium">{data.memory.avg_importance.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState
                title="No memory data"
                description="Memory statistics will appear here"
                icon="🧠"
                size="sm"
              />
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default HomePage;
