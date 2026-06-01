/**
 * Observability UI - LLM Tracing and Agent Monitoring
 *
 * Provides:
 * - LLM tracing visualization
 * - Agent execution timeline
 * - Decision tree display
 * - Performance metrics
 * - Error tracking
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ExternalCallsPanel } from './ExternalCallsPanel';

interface LLMTrace {
  id: string;
  agent_id: string;
  model: string;
  prompt: string;
  response: string;
  tokens: {
    prompt: number;
    completion: number;
    total: number;
  };
  latency_ms: number;
  timestamp: string;
  metadata: Record<string, any>;
}

interface AgentExecution {
  id: string;
  agent_id: string;
  task: string;
  start_time: string;
  end_time?: string;
  duration_ms?: number;
  status: 'running' | 'completed' | 'failed';
  steps: ExecutionStep[];
}

interface ExecutionStep {
  id: string;
  type: string;
  description: string;
  start_time: string;
  end_time?: string;
  duration_ms?: number;
  status: 'running' | 'completed' | 'failed';
  output?: any;
  error?: string;
}

interface DecisionNode {
  id: string;
  type: 'decision' | 'action' | 'branch';
  label: string;
  condition?: string;
  children: DecisionNode[];
  executed: boolean;
  result?: string;
}

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
}

interface ErrorLog {
  id: string;
  timestamp: string;
  level: 'error' | 'warning' | 'info';
  agent_id: string;
  message: string;
  stack_trace?: string;
  context: Record<string, any>;
}

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_HOST || localStorage.getItem('swarm_api_host') || '';

export function Observability() {
  const [traces, setTraces] = useState<LLMTrace[]>([]);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [errors, setErrors] = useState<ErrorLog[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<LLMTrace | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<AgentExecution | null>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('1h');
  const [activeTab, setActiveTab] = useState<'overview' | 'llm' | 'a2a' | 'external'>('overview');

  // Fetch observability data
  const fetchData = useCallback(async () => {
    try {
      // Fetch traces
      const tracesRes = await fetch(`${API_URL}/api/observability/traces?range=${timeRange}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}` },
      });
      const tracesData = await tracesRes.json();

      // Fetch executions
      const execRes = await fetch(`${API_URL}/api/observability/executions?range=${timeRange}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}` },
      });
      const execData = await execRes.json();

      // Fetch metrics
      const metricsRes = await fetch(`${API_URL}/api/observability/metrics?range=${timeRange}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}` },
      });
      const metricsData = await metricsRes.json();

      // Fetch errors
      const errorsRes = await fetch(`${API_URL}/api/observability/errors?range=${timeRange}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || ''}` },
      });
      const errorsData = await errorsRes.json();

      setTraces(tracesData.traces || []);
      setExecutions(execData.executions || []);
      setMetrics(metricsData.metrics || []);
      setErrors(errorsData.errors || []);
    } catch (err) {
      console.error('Failed to fetch observability data:', err);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchData();

    // Set up WebSocket for real-time updates
    const wsUrl = `${API_URL.replace('http', 'ws')}/ws/observability`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      switch (update.type) {
        case 'new_trace':
          setTraces(prev => [update.trace, ...prev].slice(0, 100));
          break;

        case 'execution_update':
          setExecutions(prev => prev.map(exec =>
            exec.id === update.execution.id ? update.execution : exec
          ));
          break;

        case 'new_execution':
          setExecutions(prev => [update.execution, ...prev]);
          break;

        case 'metric_update':
          setMetrics(prev => prev.map(metric =>
            metric.name === update.metric.name ? update.metric : metric
          ));
          break;

        case 'new_error':
          setErrors(prev => [update.error, ...prev].slice(0, 100));
          break;
      }
    };

    return () => ws.close();
  }, [fetchData]);

  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const getLatencyColor = (ms: number) => {
    if (ms < 1000) return 'text-green-500';
    if (ms < 5000) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-blue-500';
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getErrorLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'bg-red-900/50 border-red-500';
      case 'warning': return 'bg-yellow-900/50 border-yellow-500';
      case 'info': return 'bg-blue-900/50 border-blue-500';
      default: return 'bg-gray-900/50 border-gray-500';
    }
  };

  const renderDecisionNode = (node: DecisionNode, depth: number = 0) => {
    const paddingLeft = depth * 24;

    return (
      <div key={node.id} className="mb-2">
        <div
          className={`flex items-center gap-2 p-2 rounded border ${
            node.executed ? 'bg-gray-700 border-gray-600' : 'bg-gray-800 border-gray-700'
          }`}
          style={{ paddingLeft: `${paddingLeft}px` }}
        >
          <span className="text-gray-400">
            {node.type === 'decision' ? '◇' : node.type === 'action' ? '▶' : '◯'}
          </span>
          <span className="font-semibold">{node.label}</span>
          {node.condition && (
            <span className="text-sm text-gray-400">({node.condition})</span>
          )}
          {node.executed && node.result && (
            <span className="text-sm text-green-400">→ {node.result}</span>
          )}
        </div>
        {node.children.map(child => renderDecisionNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="observability p-6 bg-gray-900 text-white min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">Observability</h1>
          <select
            value={timeRange}
            onChange={e => setTimeRange(e.target.value as any)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'overview'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('llm')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'llm'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            LLM Traces
          </button>
          <button
            onClick={() => setActiveTab('a2a')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'a2a'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            A2A Tracker
          </button>
          <button
            onClick={() => setActiveTab('external')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'external'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            External Calls
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'external' ? (
        <ExternalCallsPanel />
      ) : (
        <>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* LLM Traces */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">LLM Traces</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {traces.map(trace => (
              <div
                key={trace.id}
                className={`bg-gray-700 rounded p-3 cursor-pointer hover:bg-gray-600 ${
                  selectedTrace?.id === trace.id ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setSelectedTrace(trace)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{trace.agent_id}</span>
                    <span className="text-sm text-gray-400">{trace.model}</span>
                  </div>
                  <span className={`text-sm ${getLatencyColor(trace.latency_ms)}`}>
                    {formatLatency(trace.latency_ms)}
                  </span>
                </div>
                <div className="text-sm text-gray-400 truncate">
                  {trace.prompt.substring(0, 100)}...
                </div>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                  <span>Tokens: {trace.tokens.total}</span>
                  <span>{new Date(trace.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
            {traces.length === 0 && (
              <div className="text-center text-gray-500 py-8">No traces available</div>
            )}
          </div>
        </div>

        {/* Agent Executions */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Agent Executions</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {executions.map(exec => (
              <div
                key={exec.id}
                className={`bg-gray-700 rounded p-3 cursor-pointer hover:bg-gray-600 ${
                  selectedExecution?.id === exec.id ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setSelectedExecution(exec)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{exec.agent_id}</span>
                    <span className={`text-sm ${getStatusColor(exec.status)}`}>
                      {exec.status}
                    </span>
                  </div>
                  {exec.duration_ms && (
                    <span className="text-sm text-gray-400">
                      {formatLatency(exec.duration_ms)}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-400">{exec.task}</div>
                <div className="text-sm text-gray-500 mt-1">
                  {exec.steps.length} steps
                </div>
              </div>
            ))}
            {executions.length === 0 && (
              <div className="text-center text-gray-500 py-8">No executions available</div>
            )}
          </div>
        </div>
      </div>

      {/* Detail Panels */}
      {selectedTrace && (
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-4">Trace Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-400">Agent ID</div>
              <div className="font-semibold">{selectedTrace.agent_id}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Model</div>
              <div className="font-semibold">{selectedTrace.model}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Latency</div>
              <div className={`font-semibold ${getLatencyColor(selectedTrace.latency_ms)}`}>
                {formatLatency(selectedTrace.latency_ms)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Tokens</div>
              <div className="font-semibold">
                {selectedTrace.tokens.prompt} + {selectedTrace.tokens.completion} = {selectedTrace.tokens.total}
              </div>
            </div>
          </div>
          <div className="mt-4">
            <div className="text-sm text-gray-400 mb-2">Prompt</div>
            <div className="bg-gray-700 rounded p-3 text-sm whitespace-pre-wrap">
              {selectedTrace.prompt}
            </div>
          </div>
          <div className="mt-4">
            <div className="text-sm text-gray-400 mb-2">Response</div>
            <div className="bg-gray-700 rounded p-3 text-sm whitespace-pre-wrap">
              {selectedTrace.response}
            </div>
          </div>
          <button
            onClick={() => setSelectedTrace(null)}
            className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            Close
          </button>
        </div>
      )}

      {selectedExecution && (
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-4">Execution Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-400">Agent ID</div>
              <div className="font-semibold">{selectedExecution.agent_id}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Status</div>
              <div className={`font-semibold ${getStatusColor(selectedExecution.status)}`}>
                {selectedExecution.status}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Task</div>
              <div className="font-semibold">{selectedExecution.task}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Duration</div>
              <div className="font-semibold">
                {selectedExecution.duration_ms ? formatLatency(selectedExecution.duration_ms) : 'Running...'}
              </div>
            </div>
          </div>
          <div className="mt-4">
            <div className="text-sm text-gray-400 mb-2">Execution Steps</div>
            <div className="space-y-2">
              {selectedExecution.steps.map((step, index) => (
                <div key={step.id} className="bg-gray-700 rounded p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-gray-400">#{index + 1}</span>
                    <span className="font-semibold">{step.type}</span>
                    <span className={`text-sm ${getStatusColor(step.status)}`}>
                      {step.status}
                    </span>
                    {step.duration_ms && (
                      <span className="text-sm text-gray-400 ml-auto">
                        {formatLatency(step.duration_ms)}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-400">{step.description}</div>
                  {step.error && (
                    <div className="mt-2 text-sm text-red-400">{step.error}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
          <button
            onClick={() => setSelectedExecution(null)}
            className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            Close
          </button>
        </div>
      )}

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Metrics */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
          <div className="grid grid-cols-2 gap-4">
            {metrics.map(metric => (
              <div key={metric.name} className="bg-gray-700 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">{metric.name}</span>
                  <span className={`text-sm ${
                    metric.trend === 'up' ? 'text-red-500' :
                    metric.trend === 'down' ? 'text-green-500' :
                    'text-gray-500'
                  }`}>
                    {metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→'}
                  </span>
                </div>
                <div className="text-2xl font-bold">
                  {metric.value.toFixed(2)} {metric.unit}
                </div>
              </div>
            ))}
            {metrics.length === 0 && (
              <div className="col-span-2 text-center text-gray-500 py-8">No metrics available</div>
            )}
          </div>
        </div>

        {/* Error Logs */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Error Logs</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {errors.map(error => (
              <div
                key={error.id}
                className={`border rounded p-3 ${getErrorLevelColor(error.level)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{error.agent_id}</span>
                    <span className="text-sm uppercase">{error.level}</span>
                  </div>
                  <span className="text-sm text-gray-400">
                    {new Date(error.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="text-sm">{error.message}</div>
                {error.stack_trace && (
                  <details className="mt-2">
                    <summary className="text-sm text-gray-400 cursor-pointer">Stack Trace</summary>
                    <pre className="mt-2 text-xs text-gray-500 overflow-x-auto">
                      {error.stack_trace}
                    </pre>
                  </details>
                )}
              </div>
            ))}
            {errors.length === 0 && (
              <div className="text-center text-gray-500 py-8">No errors logged</div>
            )}
          </div>
        </div>
      </div>
        </>
      )}
    </div>
  );
}
