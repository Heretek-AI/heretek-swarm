/**
 * Swarm Health Dashboard
 * 
 * Main dashboard component for visualizing overall swarm health,
 * agent status, and system metrics.
 */

import { useState, useEffect, useCallback } from "react";

// Types
interface SwarmMetrics {
  total_agents: number;
  active_agents: number;
  idle_agents: number;
  total_tasks_completed: number;
  total_tasks_failed: number;
  avg_task_duration_seconds: number;
  total_messages_sent: number;
  total_messages_received: number;
  avg_message_latency_seconds: number;
  consensus_rounds: number;
  consensus_success_rate: number;
  overall_health_score: number;
  timestamp: string;
  metadata: Record<string, any>;
}

interface AgentMetrics {
  agent_id: string;
  agent_type: string;
  tasks_completed: number;
  tasks_failed: number;
  avg_task_duration_seconds: number;
  messages_sent: number;
  messages_received: number;
  error_count: number;
  success_rate: number;
  health_score: number;
  last_activity: string;
  metadata: Record<string, any>;
}

interface Alert {
  alert_id: string;
  severity: "critical" | "warning" | "info";
  type: string;
  agent_id?: string;
  message: string;
  value: number;
  threshold: number;
  timestamp: string;
}

interface SwarmHealthDashboardProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
  showAgentDetails?: boolean;
  showAlerts?: boolean;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function SwarmHealthDashboard({
  apiBaseUrl = API_URL,
  refreshInterval = 5000,
  showAgentDetails = true,
  showAlerts = true,
}: SwarmHealthDashboardProps) {
  const [swarmMetrics, setSwarmMetrics] = useState<SwarmMetrics | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<Record<string, AgentMetrics>>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Fetch swarm health
  const fetchSwarmHealth = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/observability/swarm`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch swarm health: ${response.status}`);
      }
      
      const data = await response.json();
      setSwarmMetrics(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch swarm health";
      setError(errorMessage);
      console.error("SwarmHealthDashboard error:", err);
    }
  }, [apiBaseUrl]);

  // Fetch all agents
  const fetchAgents = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/observability/agents`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch agents: ${response.status}`);
      }
      
      const data = await response.json();
      setAgentMetrics(data.agents || {});
    } catch (err) {
      console.error("Failed to fetch agents:", err);
    }
  }, [apiBaseUrl]);

  // Fetch alerts
  const fetchAlerts = useCallback(async () => {
    if (!showAlerts) return;
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/observability/alerts`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch alerts: ${response.status}`);
      }
      
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error("Failed to fetch alerts:", err);
    }
  }, [apiBaseUrl, showAlerts]);

  // Initial fetch and refresh interval
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      await Promise.all([fetchSwarmHealth(), fetchAgents(), fetchAlerts()]);
      setLoading(false);
    };
    
    fetchAll();
    
    const interval = setInterval(() => {
      fetchSwarmHealth();
      fetchAgents();
      fetchAlerts();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [fetchSwarmHealth, fetchAgents, fetchAlerts, refreshInterval]);

  // Get health score color
  const getHealthColor = (score: number): string => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-blue-400";
    if (score >= 40) return "text-yellow-400";
    if (score >= 20) return "text-orange-400";
    return "text-red-400";
  };

  // Get health bar color
  const getHealthBarColor = (score: number): string => {
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-blue-500";
    if (score >= 40) return "bg-yellow-500";
    if (score >= 20) return "bg-orange-500";
    return "bg-red-500";
  };

  // Get agent status color
  const getAgentStatusColor = (agent: AgentMetrics): string => {
    if (agent.health_score >= 70) return "bg-green-500";
    if (agent.health_score >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  // Get severity color for alerts
  const getAlertColor = (severity: string): string => {
    switch (severity) {
      case "critical":
        return "border-red-500 bg-red-900/20 text-red-400";
      case "warning":
        return "border-yellow-500 bg-yellow-900/20 text-yellow-400";
      default:
        return "border-blue-500 bg-blue-900/20 text-blue-400";
    }
  };

  // Calculate agent availability percentage
  const availabilityPercentage = swarmMetrics
    ? ((swarmMetrics.active_agents + swarmMetrics.idle_agents) / Math.max(1, swarmMetrics.total_agents)) * 100
    : 0;

  // Calculate task success rate
  const taskSuccessRate = swarmMetrics && (swarmMetrics.total_tasks_completed + swarmMetrics.total_tasks_failed) > 0
    ? (swarmMetrics.total_tasks_completed / (swarmMetrics.total_tasks_completed + swarmMetrics.total_tasks_failed)) * 100
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-800 rounded-lg border border-gray-700">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Swarm Health Dashboard</h2>
        <div className="text-sm text-gray-400">
          {swarmMetrics?.timestamp ? new Date(swarmMetrics.timestamp).toLocaleTimeString() : ""}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="mb-4 bg-red-900/30 border border-red-500 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {swarmMetrics && (
        <>
          {/* Main Health Score */}
          <div className="mb-6 bg-gray-900 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-2">
                  Overall Swarm Health
                </h3>
                <p className={`text-5xl font-bold ${getHealthColor(swarmMetrics.overall_health_score)}`}>
                  {swarmMetrics.overall_health_score.toFixed(1)}
                </p>
                <p className="text-gray-500 text-sm mt-1">out of 100</p>
              </div>
              <div className="w-48 h-48 relative">
                <svg className="w-full h-full" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#374151"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke={
                      swarmMetrics.overall_health_score >= 80
                        ? "#22c55e"
                        : swarmMetrics.overall_health_score >= 60
                        ? "#3b82f6"
                        : swarmMetrics.overall_health_score >= 40
                        ? "#eab308"
                        : swarmMetrics.overall_health_score >= 20
                        ? "#f97316"
                        : "#ef4444"
                    }
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${(swarmMetrics.overall_health_score / 100) * 283} 283`}
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">
                    {swarmMetrics.overall_health_score.toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Alerts Section */}
          {showAlerts && alerts.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-400 mb-3">
                Active Alerts ({alerts.length})
              </h3>
              <div className="space-y-2">
                {alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.alert_id}
                    className={`border rounded-lg p-3 ${getAlertColor(alert.severity)}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-xs font-medium uppercase">{alert.severity}</span>
                        <p className="text-sm mt-1">{alert.message}</p>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {/* Agent Count */}
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-xs uppercase tracking-wider mb-2">
                Agents
              </h3>
              <p className="text-3xl font-bold text-white">
                {swarmMetrics.total_agents}
              </p>
              <div className="mt-2 text-xs text-gray-500">
                <span className="text-green-400">{swarmMetrics.active_agents} active</span>
                {" | "}
                <span className="text-gray-400">{swarmMetrics.idle_agents} idle</span>
              </div>
            </div>

            {/* Availability */}
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-xs uppercase tracking-wider mb-2">
                Availability
              </h3>
              <p className="text-3xl font-bold text-blue-400">
                {availabilityPercentage.toFixed(1)}%
              </p>
              <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${availabilityPercentage}%` }}
                />
              </div>
            </div>

            {/* Task Success Rate */}
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-xs uppercase tracking-wider mb-2">
                Task Success
              </h3>
              <p className="text-3xl font-bold text-green-400">
                {taskSuccessRate.toFixed(1)}%
              </p>
              <div className="mt-2 text-xs text-gray-500">
                {swarmMetrics.total_tasks_completed} completed / {swarmMetrics.total_tasks_failed} failed
              </div>
            </div>

            {/* Messages */}
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-xs uppercase tracking-wider mb-2">
                Messages
              </h3>
              <p className="text-3xl font-bold text-purple-400">
                {swarmMetrics.total_messages_sent + swarmMetrics.total_messages_received}
              </p>
              <div className="mt-2 text-xs text-gray-500">
                {swarmMetrics.total_messages_sent} sent / {swarmMetrics.total_messages_received} received
              </div>
            </div>
          </div>

          {/* Agent Details */}
          {showAgentDetails && (
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Agent Status</h3>
              <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-950">
                    <tr>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Agent ID</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Type</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Tasks</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Success Rate</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Health</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {Object.entries(agentMetrics).map(([agentId, metrics]) => (
                      <tr
                        key={agentId}
                        className={`hover:bg-gray-800 cursor-pointer ${
                          selectedAgent === agentId ? "bg-blue-900/20" : ""
                        }`}
                        onClick={() => setSelectedAgent(agentId === selectedAgent ? null : agentId)}
                      >
                        <td className="px-4 py-3 text-white font-mono">{agentId}</td>
                        <td className="px-4 py-3 text-gray-400">{metrics.agent_type}</td>
                        <td className="px-4 py-3 text-gray-400">
                          {metrics.tasks_completed}/{metrics.tasks_completed + metrics.tasks_failed}
                        </td>
                        <td className="px-4 py-3">
                          <span className={metrics.success_rate >= 0.8 ? "text-green-400" : "text-red-400"}>
                            {(metrics.success_rate * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${getHealthBarColor(metrics.health_score)}`}
                                style={{ width: `${metrics.health_score}%` }}
                              />
                            </div>
                            <span className={`text-xs ${getHealthColor(metrics.health_score)}`}>
                              {metrics.health_score.toFixed(0)}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${getAgentStatusColor(metrics)}`} />
                            <span className="text-gray-400 text-xs">
                              {metrics.health_score >= 70 ? "Healthy" : metrics.health_score >= 50 ? "Degraded" : "Critical"}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {Object.keys(agentMetrics).length === 0 && (
                  <div className="px-4 py-8 text-center text-gray-500">
                    No agent data available
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Selected Agent Details */}
          {selectedAgent && agentMetrics[selectedAgent] && (
            <div className="mt-6 bg-blue-900/20 border border-blue-500/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-blue-400">
                  Agent Details: {selectedAgent}
                </h3>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="text-gray-400 hover:text-white"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Type:</span>
                  <span className="ml-2 text-white">{agentMetrics[selectedAgent].agent_type}</span>
                </div>
                <div>
                  <span className="text-gray-400">Tasks:</span>
                  <span className="ml-2 text-white">
                    {agentMetrics[selectedAgent].tasks_completed} completed
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Success Rate:</span>
                  <span className={`ml-2 ${(agentMetrics[selectedAgent].success_rate >= 0.8) ? "text-green-400" : "text-red-400"}`}>
                    {(agentMetrics[selectedAgent].success_rate * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Health:</span>
                  <span className={`ml-2 ${getHealthColor(agentMetrics[selectedAgent].health_score)}`}>
                    {agentMetrics[selectedAgent].health_score.toFixed(0)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default SwarmHealthDashboard;
