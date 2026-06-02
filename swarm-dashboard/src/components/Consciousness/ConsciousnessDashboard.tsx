/**
 * Consciousness Metrics Dashboard
 *
 * Main dashboard component for visualizing consciousness metrics
 * including IIT scores, FEP metrics, and agent connectivity.
 */

import { useState, useEffect, useCallback } from "react";
import {
  ConsciousnessStatistics,
  ConsciousnessMetrics,
  NetworkVisualization,
  TimeSeriesResponse,
  AgentStates,
  ConsciousnessState,
  VisualizationMode,
} from "./types";

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_HOST || "";

export function ConsciousnessDashboard() {
  const [statistics, setStatistics] = useState<ConsciousnessStatistics | null>(null);
  const [agentStates, setAgentStates] = useState<AgentStates | null>(null);
  const [networkData, setNetworkData] = useState<NetworkVisualization | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<ConsciousnessMetrics | null>(null);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesResponse | null>(null);
  const [visualizationMode, setVisualizationMode] = useState<VisualizationMode>(
    VisualizationMode.NETWORK
  );
  const [selectedMetric, setSelectedMetric] = useState<"phi" | "free_energy" | "surprise">(
    "phi"
  );
  const [timeRange, setTimeRange] = useState<number>(24);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [disabled, setDisabled] = useState(false);

  // Fetch statistics
  const fetchStatistics = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/consciousness/statistics`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch statistics");
      const data = await response.json();
      setStatistics(data);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch statistics");
      return false;
    }
  }, []);

  // Fetch agent states
  const fetchAgentStates = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/consciousness/states`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch agent states");
      const data = await response.json();
      setAgentStates(data);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch agent states");
      return false;
    }
  }, []);

  // Fetch network visualization data
  const fetchNetworkData = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/consciousness/visualization/network`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch network data");
      const data = await response.json();
      setNetworkData(data);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch network data");
      return false;
    }
  }, []);;

  // Fetch agent metrics
  const fetchAgentMetrics = useCallback(async (agentId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/consciousness/agents/${agentId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch agent metrics");
      const data = await response.json();
      setAgentMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch agent metrics");
    }
  }, []);

  // Fetch time series data
  const fetchTimeSeriesData = useCallback(async (agentId: string, metric: string, hours: number) => {
    try {
      const response = await fetch(
        `${API_URL}/api/consciousness/visualization/timeseries?agent_id=${agentId}&metric=${metric}&hours=${hours}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      if (!response.ok) throw new Error("Failed to fetch time series data");
      const data = await response.json();
      setTimeSeriesData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch time series data");
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      setError(null);
      const results = await Promise.all([
        fetchStatistics(),
        fetchAgentStates(),
        fetchNetworkData(),
      ]);
      const failedCount = results.filter(r => !r).length;
      setDisabled(failedCount === 3);
      if (failedCount === 3) {
        setError('Consciousness metrics are unavailable. The consciousness plugin may be disabled or the backend is unreachable.');
      } else if (failedCount > 0 && failedCount < 3) {
        setError('Some consciousness data could not be loaded. Partial results are shown below.');
      }
      setLoading(false);
    };

    fetchInitialData();

    // Refresh data every 10 seconds
    const interval = setInterval(() => {
      fetchStatistics();
      fetchAgentStates();
      fetchNetworkData();
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchStatistics, fetchAgentStates, fetchNetworkData]);

  // Fetch time series when agent or metric changes
  useEffect(() => {
    if (selectedAgent) {
      fetchTimeSeriesData(selectedAgent, selectedMetric, timeRange);
    }
  }, [selectedAgent, selectedMetric, timeRange, fetchTimeSeriesData]);

  // Get state color
  const getStateColor = (state: ConsciousnessState): string => {
    switch (state) {
      case ConsciousnessState.DORMANT:
        return "bg-gray-500";
      case ConsciousnessState.EMERGING:
        return "bg-yellow-500";
      case ConsciousnessState.COHERENT:
        return "bg-blue-500";
      case ConsciousnessState.TRANSCENDENT:
        return "bg-purple-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStateTextColor = (state: ConsciousnessState): string => {
    switch (state) {
      case ConsciousnessState.DORMANT:
        return "text-gray-400";
      case ConsciousnessState.EMERGING:
        return "text-yellow-400";
      case ConsciousnessState.COHERENT:
        return "text-blue-400";
      case ConsciousnessState.TRANSCENDENT:
        return "text-purple-400";
      default:
        return "text-gray-400";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Consciousness Metrics Dashboard</h1>
          <p className="text-gray-400">
            Visualize IIT scores, FEP metrics, and agent connectivity
          </p>
        </div>

        {/* Error/Disabled display */}
        {disabled ? (
          <div className="mb-6 bg-yellow-900/30 border border-yellow-600/50 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🧠</span>
              <div>
                <p className="text-yellow-300 font-semibold">Consciousness Plugin Disabled</p>
                <p className="text-yellow-400/80 text-sm mt-1">
                  The consciousness plugin is not active. Enable it by setting{' '}
                  <code className="bg-yellow-900/50 px-1.5 py-0.5 rounded text-xs">CONSCIOUSNESS_ENABLED=true</code>{' '}
                  or{' '}
                  <code className="bg-yellow-900/50 px-1.5 py-0.5 rounded text-xs">PLUGIN_CONSCIOUSNESS_ENABLED=true</code>{' '}
                  in your environment configuration.
                </p>
              </div>
            </div>
          </div>
        ) : error ? (
          <div className="mb-6 bg-red-900/30 border border-red-500 rounded-lg p-4">
            <p className="text-red-400">{error}</p>
          </div>
        ) : null}

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-sm mb-2">Total Agents</h3>
              <p className="text-3xl font-bold">{statistics.total_agents}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-sm mb-2">Average Phi</h3>
              <p className="text-3xl font-bold text-blue-400">
                {statistics.average_phi.toFixed(3)}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-sm mb-2">Avg Free Energy</h3>
              <p className="text-3xl font-bold text-green-400">
                {statistics.average_free_energy.toFixed(3)}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-gray-400 text-sm mb-2">Active Connections</h3>
              <p className="text-3xl font-bold text-purple-400">
                {statistics.active_connections}
              </p>
            </div>
          </div>
        )}

        {/* State Distribution */}
        {agentStates && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Consciousness State Distribution</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(agentStates.counts).map(([state, count]) => (
                <div key={state} className="text-center">
                  <div className={`w-16 h-16 rounded-full ${getStateColor(state as ConsciousnessState)} mx-auto mb-2 flex items-center justify-center`}>
                    <span className="text-2xl font-bold">{count}</span>
                  </div>
                  <p className="text-sm capitalize text-gray-400">{state}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Visualization Mode Selector */}
        <div className="mb-6 flex flex-wrap gap-2">
          {Object.values(VisualizationMode).map((mode) => (
            <button
              key={mode}
              onClick={() => setVisualizationMode(mode)}
              className={`px-4 py-2 rounded-lg ${
                visualizationMode === mode
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        {/* Main Visualization Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Network/Visualization */}
          <div className="lg:col-span-2 bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">
              {visualizationMode === VisualizationMode.NETWORK && "Agent Connectivity Network"}
              {visualizationMode === VisualizationMode.TIMESERIES && "Time Series Metrics"}
              {visualizationMode === VisualizationMode.HEATMAP && "Interaction Heatmap"}
              {visualizationMode === VisualizationMode.RADAR && "Agent Radar Chart"}
            </h2>

            {visualizationMode === VisualizationMode.NETWORK && networkData && (
              <NetworkGraph data={networkData} onNodeClick={setSelectedAgent} />
            )}

            {visualizationMode === VisualizationMode.TIMESERIES && timeSeriesData && (
              <TimeSeriesChart data={timeSeriesData} metric={selectedMetric} />
            )}

            {visualizationMode === VisualizationMode.HEATMAP && networkData && (
              <InteractionHeatmap data={networkData} />
            )}

            {visualizationMode === VisualizationMode.RADAR && agentMetrics && (
              <RadarChart metrics={agentMetrics} />
            )}
          </div>

          {/* Right Panel - Agent Details */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Agent Details</h2>

            {selectedAgent ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm text-gray-400 mb-1">Selected Agent</h3>
                  <p className="text-lg font-semibold">{selectedAgent}</p>
                </div>

                {agentMetrics && (
                  <>
                    <div>
                      <h3 className="text-sm text-gray-400 mb-1">Consciousness State</h3>
                      <p className={`text-lg font-semibold ${getStateTextColor(agentMetrics.state)}`}>
                        {agentMetrics.state.toUpperCase()}
                      </p>
                    </div>

                    <div>
                      <h3 className="text-sm text-gray-400 mb-1">Phi Score (IIT)</h3>
                      <p className="text-2xl font-bold text-blue-400">
                        {agentMetrics.phi_score.toFixed(4)}
                      </p>
                    </div>

                    <div>
                      <h3 className="text-sm text-gray-400 mb-1">Free Energy (FEP)</h3>
                      <p className="text-2xl font-bold text-green-400">
                        {agentMetrics.fep_metrics.free_energy.toFixed(4)}
                      </p>
                    </div>

                    <div>
                      <h3 className="text-sm text-gray-400 mb-1">Prediction Accuracy</h3>
                      <p className="text-lg font-semibold text-purple-400">
                        {(agentMetrics.fep_metrics.prediction_accuracy * 100).toFixed(1)}%
                      </p>
                    </div>

                    <div>
                      <h3 className="text-sm text-gray-400 mb-1">Surprise Level</h3>
                      <p className="text-lg font-semibold text-yellow-400">
                        {agentMetrics.fep_metrics.surprise.toFixed(4)}
                      </p>
                    </div>
                  </>
                )}

                {/* Metric Selector for Time Series */}
                <div>
                  <h3 className="text-sm text-gray-400 mb-2">Time Series Metric</h3>
                  <select
                    value={selectedMetric}
                    onChange={(e) => setSelectedMetric(e.target.value as any)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                  >
                    <option value="phi">Phi Score (IIT)</option>
                    <option value="free_energy">Free Energy (FEP)</option>
                    <option value="surprise">Surprise Level</option>
                  </select>
                </div>

                <div>
                  <h3 className="text-sm text-gray-400 mb-2">Time Range (Hours)</h3>
                  <input
                    type="range"
                    min="1"
                    max="168"
                    value={timeRange}
                    onChange={(e) => setTimeRange(Number(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-sm text-gray-400 mt-1">{timeRange} hours</p>
                </div>
              </div>
            ) : (
              <p className="text-gray-400">Select an agent to view details</p>
            )}

            {/* Agent List */}
            <div className="mt-6">
              <h3 className="text-sm text-gray-400 mb-2">All Agents</h3>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {agentStates &&
                  Object.entries(agentStates.states).map(([agentId, state]) => (
                    <button
                      key={agentId}
                      onClick={() => {
                        setSelectedAgent(agentId);
                        fetchAgentMetrics(agentId);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg ${
                        selectedAgent === agentId
                          ? "bg-blue-600"
                          : "bg-gray-700 hover:bg-gray-600"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="truncate mr-2">{agentId}</span>
                        <div className={`w-3 h-3 rounded-full ${getStateColor(state)}`} />
                      </div>
                    </button>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Network Graph Component (simplified D3-like visualization)
function NetworkGraph({
  data,
  onNodeClick,
}: {
  data: NetworkVisualization;
  onNodeClick: (agentId: string) => void;
}) {
  return (
    <div className="relative w-full h-96 bg-gray-900 rounded-lg overflow-hidden">
      <svg className="w-full h-full">
        {/* Render links */}
        {data.links.map((link, index) => (
          <line
            key={`link-${index}`}
            x1="50%"
            y1="50%"
            x2="50%"
            y2="50%"
            stroke="#4B5563"
            strokeWidth={Math.max(1, link.weight * 2)}
            opacity={0.5}
          />
        ))}

        {/* Render nodes */}
        {data.nodes.map((node, index) => {
          const angle = (index / data.nodes.length) * 2 * Math.PI;
          const radius = 120;
          const x = 50 + radius * Math.cos(angle);
          const y = 50 + radius * Math.sin(angle);

          return (
            <g key={node.id} onClick={() => onNodeClick(node.id)} className="cursor-pointer">
              <circle
                cx={`${x}%`}
                cy={`${y}%`}
                r={20 + node.phi * 30}
                fill={
                  node.state === ConsciousnessState.DORMANT
                    ? "#6B7280"
                    : node.state === ConsciousnessState.EMERGING
                    ? "#EAB308"
                    : node.state === ConsciousnessState.COHERENT
                    ? "#3B82F6"
                    : "#A855F7"
                }
                opacity={0.8}
              />
              <text
                x={`${x}%`}
                y={`${y}%`}
                textAnchor="middle"
                dy="4"
                className="text-xs fill-white pointer-events-none"
              >
                {node.id.split("-")[0]}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="absolute bottom-4 left-4 text-xs text-gray-400">
        Click on a node to view agent details
      </div>
    </div>
  );
}

// Time Series Chart Component
function TimeSeriesChart({
  data,
  metric,
}: {
  data: TimeSeriesResponse;
  metric: string;
}) {
  if (data.data_points.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        No data available for selected metric
      </div>
    );
  }

  const values = data.data_points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return (
    <div className="w-full h-96">
      <svg className="w-full h-full">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct) => (
          <line
            key={pct}
            x1="0"
            y1={`${pct * 100}%`}
            x2="100%"
            y2={`${pct * 100}%`}
            stroke="#374151"
            strokeWidth="1"
            strokeDasharray="4"
          />
        ))}

        {/* Data line */}
        <polyline
          points={data.data_points
            .map((point, index) => {
              const x = (index / (data.data_points.length - 1)) * 100;
              const y = ((max - point.value) / range) * 100;
              return `${x},${y}`;
            })
            .join(" ")}
          fill="none"
          stroke="#3B82F6"
          strokeWidth="2"
        />

        {/* Data points */}
        {data.data_points.map((point, index) => {
          const x = (index / (data.data_points.length - 1)) * 100;
          const y = ((max - point.value) / range) * 100;
          return (
            <circle
              key={index}
              cx={`${x}%`}
              cy={`${y}%`}
              r="4"
              fill="#3B82F6"
              className="cursor-pointer"
            >
              <title>{`${point.timestamp}: ${point.value.toFixed(4)}`}</title>
            </circle>
          );
        })}
      </svg>
      <div className="mt-2 text-sm text-gray-400">
        {metric.toUpperCase()} over {data.hours} hours ({data.count} data points)
      </div>
    </div>
  );
}

// Interaction Heatmap Component
function InteractionHeatmap({ data }: { data: NetworkVisualization }) {
  const agents = data.nodes.map((n) => n.id);
  const maxWeight = Math.max(...data.links.map((l) => l.weight));

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="p-2"></th>
            {agents.map((agent) => (
              <th key={agent} className="p-2 text-left">
                {agent.split("-")[0]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {agents.map((fromAgent) => (
            <tr key={fromAgent}>
              <td className="p-2 text-left">{fromAgent.split("-")[0]}</td>
              {agents.map((toAgent) => {
                const link = data.links.find(
                  (l) => l.source === fromAgent && l.target === toAgent
                );
                const weight = link?.weight || 0;
                const intensity = maxWeight > 0 ? weight / maxWeight : 0;
                const bgColor = `rgba(59, 130, 246, ${intensity})`;

                return (
                  <td key={toAgent} className="p-2">
                    <div
                      className="w-8 h-8 rounded"
                      style={{ backgroundColor: bgColor }}
                      title={`${fromAgent} → ${toAgent}: ${weight.toFixed(2)}`}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Radar Chart Component
function RadarChart({ metrics }: { metrics: ConsciousnessMetrics }) {
  const dimensions = [
    { name: "Phi", value: metrics.phi_score },
    { name: "Free Energy", value: metrics.fep_metrics.free_energy },
    { name: "Accuracy", value: metrics.fep_metrics.prediction_accuracy },
    { name: "Surprise", value: metrics.fep_metrics.surprise },
    { name: "Precision", value: metrics.fep_metrics.belief_precision },
  ];

  const max = Math.max(...dimensions.map((d) => d.value), 1);
  const points = dimensions
    .map((dim, index) => {
      const angle = (index / dimensions.length) * 2 * Math.PI - Math.PI / 2;
      const radius = (dim.value / max) * 40;
      const x = 50 + radius * Math.cos(angle);
      const y = 50 + radius * Math.sin(angle);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="w-full h-80">
      <svg className="w-full h-full">
        {/* Background circles */}
        {[0.25, 0.5, 0.75, 1].map((pct) => (
          <circle
            key={pct}
            cx="50%"
            cy="50%"
            r={`${pct * 40}%`}
            fill="none"
            stroke="#374151"
            strokeWidth="1"
          />
        ))}

        {/* Dimension lines */}
        {dimensions.map((dim, index) => {
          const angle = (index / dimensions.length) * 2 * Math.PI - Math.PI / 2;
          const x = 50 + 40 * Math.cos(angle);
          const y = 50 + 40 * Math.sin(angle);
          return (
            <line
              key={dim.name}
              x1="50%"
              y1="50%"
              x2={`${x}%`}
              y2={`${y}%`}
              stroke="#374151"
              strokeWidth="1"
            />
          );
        })}

        {/* Data polygon */}
        <polygon
          points={points}
          fill="rgba(59, 130, 246, 0.3)"
          stroke="#3B82F6"
          strokeWidth="2"
        />

        {/* Labels */}
        {dimensions.map((dim, index) => {
          const angle = (index / dimensions.length) * 2 * Math.PI - Math.PI / 2;
          const x = 50 + 45 * Math.cos(angle);
          const y = 50 + 45 * Math.sin(angle);
          return (
            <text
              key={dim.name}
              x={`${x}%`}
              y={`${y}%`}
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-xs fill-gray-400"
            >
              {dim.name}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
