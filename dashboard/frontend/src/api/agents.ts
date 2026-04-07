/**
 * API Client - Agent endpoints
 */

import axios from 'axios';

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Agent {
  id: string;
  type: string;
  status: string;
  lastActivity?: string;
  consciousness_metrics?: {
    gwt_score: number;
    phi_value: number;
    ast_competence: number;
    free_energy: number;
  };
}

export interface AgentsResponse {
  agents: Agent[];
  total: number;
}

/**
 * Fetch all agents
 */
export const getAgents = async (): Promise<AgentsResponse> => {
  const response = await api.get('/api/agents');
  return response.data;
};

/**
 * Fetch single agent details
 */
export const getAgent = async (agentId: string): Promise<Agent> => {
  const response = await api.get(`/api/agents/${agentId}`);
  return response.data;
};

/**
 * Send chat message to agent
 */
export const sendChatMessage = async (
  agentId: string,
  message: string
): Promise<{ response: string; message?: string }> => {
  const response = await api.post(`/api/agents/${agentId}/chat`, { message });
  return response.data;
};

/**
 * Get agent status
 */
export const getAgentStatus = async (agentId: string): Promise<{
  agent_id: string;
  status: string;
  last_activity: string;
  message_count: number;
}> => {
  const response = await api.get(`/api/agents/${agentId}/status`);
  return response.data;
};

/**
 * Execute workflow
 */
export const executeWorkflow = async (
  workflowId: string,
  input?: Record<string, unknown>
): Promise<{
  execution_id: string;
  status: string;
  result?: unknown;
}> => {
  const response = await api.post(`/api/workflows/${workflowId}/execute`, {
    input,
  });
  return response.data;
};
