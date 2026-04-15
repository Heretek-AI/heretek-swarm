/**
 * Agent Metrics Grid
 * 
 * Grid view of per-agent performance metrics with filtering,
 * sorting, and detailed agent information.
 */

import { useState, useEffect, useCallback, useMemo } from "react";

// Types
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

interface AgentMetricsGridProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
  showFilters?: boolean;
  showPagination?: boolean;
  pageSize?: number;
  onAgentSelect?: (agentId: string | null) => void;
}

type SortField = "health_score" | "success_rate" | "tasks_completed" | "error_count" | "last_activity";
type SortOrder = "asc" | "desc";
type FilterStatus = "all" | "healthy" | "degraded" | "critical";

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_HOST || "";

export function AgentMetricsGrid({
  apiBaseUrl = API_URL,
  refreshInterval = 5000,
  showFilters = true,
  showPagination = true,
  pageSize = 10,
  onAgentSelect,
}: AgentMetricsGridProps) {
  const [agents, setAgents] = useState<Record<string, AgentMetrics>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>("health_score");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  const [filterType, setFilterType] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch agents
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
      setAgents(data.agents || {});
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch agents";
      setError(errorMessage);
      console.error("AgentMetricsGrid error:", err);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Initial fetch and refresh interval
  useEffect(() => {
    fetchAgents();
    
    const interval = setInterval(() => {
      fetchAgents();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [fetchAgents, refreshInterval]);

  // Get unique agent types for filter
  const agentTypes = useMemo(() => {
    const types = new Set<string>();
    Object.values(agents).forEach((agent) => {
      types.add(agent.agent_type);
    });
    return Array.from(types);
  }, [agents]);

  // Filter and sort agents
  const filteredAndSortedAgents = useMemo(() => {
    let agentList = Object.entries(agents).map(([id, metrics]) => ({ id, ...metrics }));

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      agentList = agentList.filter(
        (agent) =>
          agent.id.toLowerCase().includes(query) ||
          agent.agent_type.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (filterStatus !== "all") {
      agentList = agentList.filter((agent) => {
        if (filterStatus === "healthy") return agent.health_score >= 70;
        if (filterStatus === "degraded") return agent.health_score >= 50 && agent.health_score < 70;
        if (filterStatus === "critical") return agent.health_score < 50;
        return true;
      });
    }

    // Apply type filter
    if (filterType !== "all") {
      agentList = agentList.filter((agent) => agent.agent_type === filterType);
    }

    // Apply sorting
    agentList.sort((a, b) => {
      let comparison = 0;
      
      if (sortField === "last_activity") {
        comparison = new Date(a.last_activity).getTime() - new Date(b.last_activity).getTime();
      } else {
        comparison = a[sortField] - b[sortField];
      }
      
      return sortOrder === "asc" ? comparison : -comparison;
    });

    return agentList;
  }, [agents, searchQuery, filterStatus, filterType, sortField, sortOrder]);

  // Apply pagination
  const paginatedAgents = useMemo(() => {
    if (!showPagination) return filteredAndSortedAgents;
    
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredAndSortedAgents.slice(startIndex, endIndex);
  }, [filteredAndSortedAgents, currentPage, pageSize, showPagination]);

  // Calculate total pages
  const totalPages = Math.ceil(filteredAndSortedAgents.length / pageSize);

  // Handle sort change
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  // Handle agent selection
  const handleAgentClick = (agentId: string) => {
    const newSelected = selectedAgent === agentId ? null : agentId;
    setSelectedAgent(newSelected);
    onAgentSelect?.(newSelected);
  };

  // Get health color
  const getHealthColor = (score: number): string => {
    if (score >= 70) return "text-green-400";
    if (score >= 50) return "text-yellow-400";
    return "text-red-400";
  };

  // Get health bar color
  const getHealthBarColor = (score: number): string => {
    if (score >= 70) return "bg-green-500";
    if (score >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  // Get status badge
  const getStatusBadge = (score: number) => {
    if (score >= 70) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-900/50 text-green-400">
          Healthy
        </span>
      );
    }
    if (score >= 50) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-900/50 text-yellow-400">
          Degraded
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-900/50 text-red-400">
        Critical
      </span>
    );
  };

  // Sort icon
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <span className="text-gray-600">⇅</span>;
    }
    return sortOrder === "asc" ? <span className="text-blue-400">↑</span> : <span className="text-blue-400">↓</span>;
  };

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
        <h2 className="text-xl font-semibold text-white">Agent Metrics</h2>
        <div className="text-sm text-gray-400">
          {filteredAndSortedAgents.length} agents
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="mb-4 bg-red-900/30 border border-red-500 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Search</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search agents..."
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Status</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="healthy">Healthy (70+)</option>
              <option value="degraded">Degraded (50-69)</option>
              <option value="critical">Critical {String.fromCharCode(60)}50)</option>
            </select>
          </div>

          {/* Type Filter */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Agent Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Types</option>
              {agentTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Sort */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sort By</label>
            <select
              value={`${sortField}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split("-");
                setSortField(field as SortField);
                setSortOrder(order as SortOrder);
              }}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="health_score-desc">Health (High to Low)</option>
              <option value="health_score-asc">Health (Low to High)</option>
              <option value="success_rate-desc">Success Rate (High to Low)</option>
              <option value="success_rate-asc">Success Rate (Low to High)</option>
              <option value="tasks_completed-desc">Tasks (High to Low)</option>
              <option value="tasks_completed-asc">Tasks (Low to High)</option>
              <option value="error_count-desc">Errors (High to Low)</option>
              <option value="error_count-asc">Errors (Low to High)</option>
              <option value="last_activity-desc">Recent Activity</option>
              <option value="last_activity-asc">Oldest Activity</option>
            </select>
          </div>
        </div>
      )}

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {paginatedAgents.map((agent) => (
          <div
            key={agent.id}
            className={`bg-gray-900 rounded-lg border p-4 cursor-pointer transition-all ${
              selectedAgent === agent.id
                ? "border-blue-500 bg-blue-900/20"
                : "border-gray-700 hover:border-gray-600"
            }`}
            onClick={() => handleAgentClick(agent.id)}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getHealthBarColor(agent.health_score)}`} />
                <h3 className="text-white font-mono text-sm truncate">{agent.id}</h3>
              </div>
              {getStatusBadge(agent.health_score)}
            </div>

            {/* Metrics */}
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Type</span>
                <span className="text-white">{agent.agent_type}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Tasks</span>
                <span className="text-white">
                  {agent.tasks_completed}/{agent.tasks_completed + agent.tasks_failed}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Success Rate</span>
                <span className={agent.success_rate >= 0.8 ? "text-green-400" : "text-red-400"}>
                  {(agent.success_rate * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Errors</span>
                <span className={agent.error_count > 5 ? "text-red-400" : "text-gray-400"}>
                  {agent.error_count}
                </span>
              </div>
              
              {/* Health Bar */}
              <div className="mt-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-400">Health</span>
                  <span className={`text-xs ${getHealthColor(agent.health_score)}`}>
                    {agent.health_score.toFixed(0)}
                  </span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getHealthBarColor(agent.health_score)} transition-all duration-300`}
                    style={{ width: `${agent.health_score}%` }}
                  />
                </div>
              </div>

              {/* Last Activity */}
              <div className="mt-2 text-xs text-gray-500">
                Last activity: {new Date(agent.last_activity).toLocaleString()}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {paginatedAgents.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>No agents found matching your criteria</p>
        </div>
      )}

      {/* Pagination */}
      {showPagination && totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-gray-400">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Selected Agent Details */}
      {selectedAgent && agents[selectedAgent] && (
        <div className="mt-6 bg-blue-900/20 border border-blue-500/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-blue-400">
              Selected Agent: {selectedAgent}
            </h3>
            <button
              onClick={() => {
                setSelectedAgent(null);
                onAgentSelect?.(null);
              }}
              className="text-gray-400 hover:text-white"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Type</span>
              <p className="text-white font-medium">{agents[selectedAgent].agent_type}</p>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Tasks Completed</span>
              <p className="text-white font-medium">{agents[selectedAgent].tasks_completed}</p>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Success Rate</span>
              <p className={`font-medium ${agents[selectedAgent].success_rate >= 0.8 ? "text-green-400" : "text-red-400"}`}>
                {(agents[selectedAgent].success_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Health Score</span>
              <p className={`font-medium ${getHealthColor(agents[selectedAgent].health_score)}`}>
                {agents[selectedAgent].health_score.toFixed(1)}
              </p>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Messages Sent</span>
              <p className="text-white font-medium">{agents[selectedAgent].messages_sent}</p>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Messages Received</span>
              <p className="text-white font-medium">{agents[selectedAgent].messages_received}</p>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Error Count</span>
              <p className={`font-medium ${agents[selectedAgent].error_count > 5 ? "text-red-400" : "text-white"}`}>
                {agents[selectedAgent].error_count}
              </p>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <span className="text-gray-400">Avg Task Duration</span>
              <p className="text-white font-medium">
                {agents[selectedAgent].avg_task_duration_seconds.toFixed(2)}s
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AgentMetricsGrid;
