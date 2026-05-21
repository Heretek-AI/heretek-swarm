/**
 * PerformancePanel - Live performance metrics display
 *
 * Shows real-time actor processing duration and DB query latency
 * with color-coded bars.  Fetches data from /api/metrics/json and
 * /api/observability/agents on a 30-second polling interval.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchMetricsJson,
  fetchAgentMetrics,
  MetricsJsonResponse,
  AgentMetrics,
} from '../api/metrics';

// =============================================================================
// Helpers
// =============================================================================

function computeAvgActorProcessing(
  agentMetrics: Record<string, AgentMetrics>,
): number {
  const agents = Object.values(agentMetrics);
  if (agents.length === 0) return 0;

  const sum = agents.reduce(
    (acc, a) => acc + (a.avg_task_duration_seconds || 0),
    0,
  );
  return sum / agents.length;
}

/** Derive an approximate DB query latency from the swarm health score.
 *
 *  The Prometheus histogram `heretek_swarm_db_query_duration_seconds` is
 *  exported in text format, not JSON.  Until a dedicated DB-latency JSON
 *  endpoint is available we compute a synthetic value from the overall
 *  health score — higher health implies lower latency.
 */
function computeDbLatencyEstimate(healthScore: number): number {
  // Invert health score: 100 → ~1ms, 50 → ~50ms, 0 → ~200ms
  if (healthScore >= 95) return 1;
  if (healthScore >= 80) return 5;
  if (healthScore >= 60) return 20;
  if (healthScore >= 40) return 50;
  if (healthScore >= 20) return 100;
  return 200;
}

function formatMs(value: number): string {
  if (value < 1) return `${(value * 1000).toFixed(1)}μs`;
  if (value < 1000) return `${value.toFixed(1)}ms`;
  return `${(value / 1000).toFixed(2)}s`;
}

function getBarColor(valueMs: number): string {
  if (valueMs < 10) return 'bg-green-500';
  if (valueMs < 50) return 'bg-yellow-500';
  return 'bg-red-500';
}

function getTextColor(valueMs: number): string {
  if (valueMs < 10) return 'text-green-400';
  if (valueMs < 50) return 'text-yellow-400';
  return 'text-red-400';
}

// =============================================================================
// Component
// =============================================================================

export function PerformancePanel() {
  const [metricsData, setMetricsData] = useState<MetricsJsonResponse | null>(null);
  const [avgActorMs, setAvgActorMs] = useState<number>(0);
  const [dbLatencyMs, setDbLatencyMs] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [metrics, agentData] = await Promise.all([
        fetchMetricsJson(),
        fetchAgentMetrics(),
      ]);

      setMetricsData(metrics);
      setAvgActorMs(computeAvgActorProcessing(agentData.agents));
      setDbLatencyMs(computeDbLatencyEstimate(metrics.health_score));
      setLastFetch(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
    }
  }, []);

  // Initial fetch + 30-second polling
  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const maxMs = Math.max(avgActorMs, dbLatencyMs, 50); // ensure visible bar

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Performance Metrics</h2>
        {lastFetch && (
          <span className="text-xs text-gray-500">
            Updated {lastFetch.toLocaleTimeString()}
          </span>
        )}
      </div>

      {error && (
        <div className="mb-3 p-2 bg-red-900/50 border border-red-500 rounded text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Actor Processing Card */}
        <div className="bg-gray-700 rounded p-3">
          <div className="text-sm text-gray-400 mb-2">
            Avg Actor Processing
          </div>
          <div className={`text-2xl font-bold mb-3 ${getTextColor(avgActorMs)}`}>
            {formatMs(avgActorMs)}
          </div>
          <div className="w-full bg-gray-600 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${getBarColor(avgActorMs)}`}
              style={{ width: `${Math.min((avgActorMs / maxMs) * 100, 100)}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Per-agent average task duration
          </div>
        </div>

        {/* DB Query Latency Card */}
        <div className="bg-gray-700 rounded p-3">
          <div className="text-sm text-gray-400 mb-2">
            DB Query Latency (est.)
          </div>
          <div className={`text-2xl font-bold mb-3 ${getTextColor(dbLatencyMs)}`}>
            {formatMs(dbLatencyMs)}
          </div>
          <div className="w-full bg-gray-600 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${getBarColor(dbLatencyMs)}`}
              style={{ width: `${Math.min((dbLatencyMs / maxMs) * 100, 100)}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Estimated from health score
          </div>
        </div>
      </div>

      {/* Quick context from swarm */}
      {metricsData && (
        <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-gray-500">
          <div>
            Agents: {metricsData.swarm.active_agents}/{metricsData.swarm.total_agents} active
          </div>
          <div>
            Tasks: {metricsData.swarm.tasks_completed} done, {metricsData.swarm.tasks_failed} failed
          </div>
          <div>
            Health: {metricsData.health_score.toFixed(0)}%
          </div>
        </div>
      )}
    </div>
  );
}
