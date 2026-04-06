/**
 * API Client - Consciousness metrics endpoints
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ConsciousnessStatistics {
  total_agents: number;
  average_phi: number;
  average_free_energy: number;
  active_connections: number;
  timestamp: string;
}

export interface AgentMetrics {
  agent_id: string;
  phi_score: number;
  fep_metrics: {
    free_energy: number;
    prediction_accuracy: number;
    surprise: number;
    belief_precision: number;
  };
  state: 'dormant' | 'emerging' | 'coherent' | 'transcendent';
  timestamp: string;
}

export interface TimeSeriesData {
  agent_id: string;
  metric: string;
  hours: number;
  data_points: {
    timestamp: string;
    value: number;
  }[];
  count: number;
}

export interface NetworkVisualization {
  nodes: {
    id: string;
    phi: number;
    state: 'dormant' | 'emerging' | 'coherent' | 'transcendent';
  }[];
  links: {
    source: string;
    target: string;
    weight: number;
  }[];
}

/**
 * Get collective consciousness statistics
 */
export const getConsciousnessStatistics = async (): Promise<ConsciousnessStatistics> => {
  const response = await api.get('/api/consciousness/statistics');
  return response.data;
};

/**
 * Get consciousness metrics for specific agent
 */
export const getAgentMetrics = async (agentId: string): Promise<AgentMetrics> => {
  const response = await api.get(`/api/consciousness/agents/${agentId}`);
  return response.data;
};

/**
 * Get time series data for metrics visualization
 */
export const getTimeSeriesData = async (
  agentId: string,
  metric: string,
  hours: number = 24
): Promise<TimeSeriesData> => {
  const response = await api.get(
    `/api/consciousness/visualization/timeseries?agent_id=${agentId}&metric=${metric}&hours=${hours}`
  );
  return response.data;
};

/**
 * Get network visualization data
 */
export const getNetworkVisualization = async (): Promise<NetworkVisualization> => {
  const response = await api.get('/api/consciousness/visualization/network');
  return response.data;
};

/**
 * Get agent states distribution
 */
export const getAgentStates = async (): Promise<{
  counts: Record<string, number>;
  states: Record<string, 'dormant' | 'emerging' | 'coherent' | 'transcendent'>;
}> => {
  const response = await api.get('/api/consciousness/states');
  return response.data;
};
