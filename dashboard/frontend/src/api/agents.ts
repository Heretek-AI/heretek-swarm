/**
 * API Client - Agent Management endpoints
 */

import axios from 'axios';

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_HOST || '';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add API key interceptor
api.interceptors.request.use((config) => {
  const apiKey = import.meta.env.VITE_API_KEY;
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
  }
  return config;
});

// =============================================================================
// Types
// =============================================================================

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

export interface AgentType {
  type_name: string;
  module_path: string;
  description: string;
  capabilities: string[];
  topics: string[];
  config_schema: Record<string, unknown>;
  actor_type: string;
}

export interface AgentTypeResponse {
  available_agents: AgentType[];
  total: number;
}

export interface AgentInstance {
  instance_id: string;
  agent_type: string;
  state: 'available' | 'deployed' | 'running' | 'stopped' | 'suspended' | 'error';
  config: Record<string, unknown>;
  has_actor: boolean;
}

export interface AgentInstancesResponse {
  instances: AgentInstance[];
  total: number;
}

export interface AgentInstanceDetails {
  instance_id: string;
  agent_type: string;
  state: string;
  config: Record<string, unknown>;
  metadata: {
    type_name: string;
    description: string;
    capabilities: string[];
  } | null;
  actor_status: {
    agent_id: string;
    state: string;
    message_count: number;
    error_count: number;
    mailbox_size: number;
    last_activity: string | null;
  } | null;
}

export interface DeployConfig {
  name?: string;
  description?: string;
  topics?: string[];
  capabilities?: string[];
  max_mailbox_size?: number;
  heartbeat_interval?: number;
  persistence_interval?: number;
  [key: string]: unknown;
}

export interface AgentLog {
  timestamp: string;
  level: string;
  message: string;
  [key: string]: unknown;
}

export interface AgentLogsResponse {
  instance_id: string;
  logs: AgentLog[];
  total: number;
}

// =============================================================================
// Legacy Agent Endpoints (for existing agents managed by supervisor)
// =============================================================================

/**
 * Fetch all agents (legacy supervisor-managed)
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

// =============================================================================
// Agent Management API Endpoints (Enhanced)
// =============================================================================

/**
 * List all available agent types that can be deployed
 */
export const getAvailableAgentTypes = async (): Promise<AgentTypeResponse> => {
  const response = await api.get('/api/agents/available');
  return response.data;
};

/**
 * Get metadata for a specific agent type
 */
export const getAgentTypeMetadata = async (agentType: string): Promise<AgentType> => {
  const response = await api.get(`/api/agents/types/${agentType}`);
  return response.data;
};

/**
 * List all deployed agent instances
 */
export const getAgentInstances = async (agentType?: string): Promise<AgentInstancesResponse> => {
  const params = agentType ? { agent_type: agentType } : {};
  const response = await api.get('/api/agents/instances', { params });
  return response.data;
};

/**
 * Get details of a specific agent instance
 */
export const getAgentInstance = async (instanceId: string): Promise<AgentInstanceDetails> => {
  const response = await api.get(`/api/agents/${instanceId}`);
  return response.data;
};

/**
 * Deploy a new agent instance
 */
export const deployAgent = async (
  agentType: string,
  config?: DeployConfig,
  instanceId?: string
): Promise<{
  instance_id: string;
  agent_type: string;
  config: DeployConfig;
  state: string;
  status: string;
}> => {
  const params: Record<string, unknown> = { agent_type: agentType };
  if (config) params.config = config;
  if (instanceId) params.instance_id = instanceId;
  
  const response = await api.post('/api/agents/deploy', params);
  return response.data;
};

/**
 * Start a deployed agent instance
 */
export const startAgent = async (instanceId: string): Promise<{
  instance_id: string;
  status: string;
  state: string;
}> => {
  const response = await api.post(`/api/agents/${instanceId}/start`);
  return response.data;
};

/**
 * Stop a running agent instance
 */
export const stopAgent = async (instanceId: string): Promise<{
  instance_id: string;
  status: string;
  state: string;
}> => {
  const response = await api.post(`/api/agents/${instanceId}/stop`);
  return response.data;
};

/**
 * Suspend a running agent instance
 */
export const suspendAgent = async (instanceId: string): Promise<{
  instance_id: string;
  status: string;
  state: string;
}> => {
  const response = await api.post(`/api/agents/${instanceId}/suspend`);
  return response.data;
};

/**
 * Resume a suspended agent instance
 */
export const resumeAgent = async (instanceId: string): Promise<{
  instance_id: string;
  status: string;
  state: string;
}> => {
  const response = await api.post(`/api/agents/${instanceId}/resume`);
  return response.data;
};

/**
 * Remove an agent instance
 */
export const removeAgent = async (instanceId: string): Promise<{
  instance_id: string;
  status: string;
}> => {
  const response = await api.delete(`/api/agents/${instanceId}`);
  return response.data;
};

/**
 * Update agent configuration
 */
export const updateAgentConfig = async (
  instanceId: string,
  config: Record<string, unknown>
): Promise<{
  instance_id: string;
  config: Record<string, unknown>;
  status: string;
}> => {
  const response = await api.put(`/api/agents/${instanceId}/config`, { config });
  return response.data;
};

/**
 * Get agent-specific logs
 */
export const getAgentLogs = async (
  instanceId: string,
  limit: number = 100
): Promise<AgentLogsResponse> => {
  const response = await api.get(`/api/agents/${instanceId}/logs`, {
    params: { limit },
  });
  return response.data;
};

/**
 * Get registry statistics
 */
export const getRegistryStats = async (): Promise<{
  total_agent_types: number;
  total_instances: number;
  instances_by_state: Record<string, number>;
  agent_types: string[];
}> => {
  const response = await api.get('/api/agents/stats');
  return response.data;
};

// =============================================================================
// Autonomous Runtime Agents
// =============================================================================

export interface AutonomousAgentStatus {
  agent_id: string;
  agent_type: string;
  state: string;
  message_count: number;
  error_count: number;
  mailbox_size: number;
  last_activity: string | null;
  uptime_seconds: number;
}

export interface AutonomousAgentsResponse {
  agents: AutonomousAgentStatus[];
  total: number;
  last_update: string | null;
  healthy: boolean;
}

/**
 * Fetch agents running in the autonomous runtime.
 * This queries the autonomous runtime's registered agents, not the API server's supervisor.
 */
export const getAutonomousAgents = async (): Promise<AutonomousAgentsResponse> => {
  const response = await api.get('/api/autonomous/agents');
  return response.data;
};

// =============================================================================
// Execute workflow (existing)
// =============================================================================

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
