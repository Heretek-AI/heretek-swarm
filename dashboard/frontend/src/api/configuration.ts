/**
 * Configuration API Client
 *
 * TypeScript client for interacting with the configuration API endpoints.
 * Provides type-safe methods for managing LLM providers, embedding providers,
 * and system configurations.
 */

import apiClient from './client';

// =============================================================================
// Types
// =============================================================================

export interface UserConfiguration {
  id: string;
  config_key: string;
  config_value: any;
  config_type: 'string' | 'integer' | 'float' | 'boolean' | 'json' | 'array';
  description?: string;
  category: string;
  is_sensitive: boolean;
  is_editable: boolean;
  created_at: string;
  updated_at: string;
}

export interface LLMProvider {
  id: string;
  provider_name: string;
  provider_type: 'openai' | 'openai_compatible' | 'ollama' | 'llamacpp' | 'zai' | 'minimax' | 'lemonade';
  base_url: string;
  api_key_hint?: string;
  default_model?: string;
  available_models: string[];
  is_enabled: boolean;
  is_default: boolean;
  priority: number;
  health_status: 'healthy' | 'unhealthy' | 'unknown' | 'degraded';
  created_at: string;
  updated_at: string;
}

export interface EmbeddingProvider {
  id: string;
  provider_name: string;
  provider_type: 'openai' | 'openai_compatible' | 'ollama' | 'local' | 'huggingface';
  base_url: string;
  api_key_hint?: string;
  default_model?: string;
  embedding_dimensions?: number;
  is_enabled: boolean;
  is_default: boolean;
  priority: number;
  health_status: 'healthy' | 'unhealthy' | 'unknown' | 'degraded';
  created_at: string;
  updated_at: string;
}

export interface AgentConfig {
  id: string;
  agent_type: string;
  agent_id?: string;
  config_name: string;
  config_data: Record<string, any>;
  llm_provider_id?: string;
  embedding_provider_id?: string;
  is_active: boolean;
  is_default_for_type: boolean;
  description?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface LLMProviderCreate {
  provider_name: string;
  provider_type: string;
  base_url: string;
  api_key?: string;
  api_key_hint?: string;
  default_model?: string;
  is_enabled?: boolean;
  is_default?: boolean;
  priority?: number;
  extra_config?: Record<string, any>;
}

export interface EmbeddingProviderCreate {
  provider_name: string;
  provider_type: string;
  base_url: string;
  api_key?: string;
  api_key_hint?: string;
  default_model?: string;
  embedding_dimensions?: number;
  is_enabled?: boolean;
  is_default?: boolean;
  priority?: number;
}

export interface ProviderTestResult {
  success: boolean;
  provider_name: string;
  model_used: string;
  latency_ms: number;
  response_text?: string;
  error?: string;
}

export interface EmbeddingProviderTestResult {
  success: boolean;
  provider_name: string;
  model_used: string;
  dimensions?: number;
  latency_ms: number;
  error?: string;
}

// =============================================================================
// Configuration Endpoints
// =============================================================================

export const configurationApi = {
  // User Configurations
  getConfigs: async (category?: string): Promise<UserConfiguration[]> => {
    const params = category ? { category } : {};
    const response = await apiClient.get('/api/config', { params });
    return response.data.configurations;
  },

  getConfig: async (key: string): Promise<UserConfiguration> => {
    const response = await apiClient.get(`/api/config/${key}`);
    return response.data;
  },

  updateConfig: async (key: string, value: any): Promise<UserConfiguration> => {
    const response = await apiClient.put(`/api/config/${key}`, { config_value: value });
    return response.data;
  },

  createConfig: async (config: Partial<UserConfiguration>): Promise<UserConfiguration> => {
    const response = await apiClient.post('/api/config', config);
    return response.data;
  },

  deleteConfig: async (key: string): Promise<void> => {
    await apiClient.delete(`/api/config/${key}`);
  },

  // LLM Providers
  listLLMProviders: async (providerType?: string, enabledOnly?: boolean): Promise<LLMProvider[]> => {
    const params: Record<string, string> = {};
    if (providerType) params.provider_type = providerType;
    if (enabledOnly) params.enabled_only = 'true';
    const response = await apiClient.get('/api/config/llm/providers', { params });
    return response.data.providers;
  },

  getLLMProvider: async (id: string): Promise<LLMProvider> => {
    const response = await apiClient.get(`/api/config/llm/providers/${id}`);
    return response.data;
  },

  createLLMProvider: async (provider: LLMProviderCreate): Promise<LLMProvider> => {
    const response = await apiClient.post('/api/config/llm/providers', provider);
    return response.data;
  },

  updateLLMProvider: async (id: string, provider: Partial<LLMProviderCreate>): Promise<LLMProvider> => {
    const response = await apiClient.put(`/api/config/llm/providers/${id}`, provider);
    return response.data;
  },

  deleteLLMProvider: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/config/llm/providers/${id}`);
  },

  testLLMProvider: async (id: string, prompt?: string, model?: string): Promise<ProviderTestResult> => {
    const response = await apiClient.post(`/api/config/llm/providers/${id}/test`, {
      prompt: prompt || 'Hello, this is a connectivity test.',
      model,
      max_tokens: 10,
    });
    return response.data;
  },

  listLLMProviderTypes: async (): Promise<any[]> => {
    const response = await apiClient.get('/api/config/llm/types');
    return response.data.provider_types;
  },

  // Embedding Providers
  listEmbeddingProviders: async (providerType?: string, enabledOnly?: boolean): Promise<EmbeddingProvider[]> => {
    const params: Record<string, string> = {};
    if (providerType) params.provider_type = providerType;
    if (enabledOnly) params.enabled_only = 'true';
    const response = await apiClient.get('/api/config/embedding/providers', { params });
    return response.data.providers;
  },

  getEmbeddingProvider: async (id: string): Promise<EmbeddingProvider> => {
    const response = await apiClient.get(`/api/config/embedding/providers/${id}`);
    return response.data;
  },

  createEmbeddingProvider: async (provider: EmbeddingProviderCreate): Promise<EmbeddingProvider> => {
    const response = await apiClient.post('/api/config/embedding/providers', provider);
    return response.data;
  },

  updateEmbeddingProvider: async (id: string, provider: Partial<EmbeddingProviderCreate>): Promise<EmbeddingProvider> => {
    const response = await apiClient.put(`/api/config/embedding/providers/${id}`, provider);
    return response.data;
  },

  deleteEmbeddingProvider: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/config/embedding/providers/${id}`);
  },

  testEmbeddingProvider: async (id: string, text?: string, model?: string): Promise<EmbeddingProviderTestResult> => {
    const response = await apiClient.post(`/api/config/embedding/providers/${id}/test`, {
      text: text || 'This is a test sentence for embedding.',
      model,
    });
    return response.data;
  },

  listEmbeddingProviderTypes: async (): Promise<any[]> => {
    const response = await apiClient.get('/api/config/embedding/types');
    return response.data.provider_types;
  },

  // Agent Configurations
  listAgentConfigs: async (agentType?: string, activeOnly?: boolean): Promise<AgentConfig[]> => {
    const params: Record<string, string> = {};
    if (agentType) params.agent_type = agentType;
    if (activeOnly !== undefined) params.active_only = String(activeOnly);
    const response = await apiClient.get('/api/config/agent/configs', { params });
    return response.data.configs;
  },

  getAgentConfig: async (id: string): Promise<AgentConfig> => {
    const response = await apiClient.get(`/api/config/agent/configs/${id}`);
    return response.data;
  },

  createAgentConfig: async (config: Partial<AgentConfig>): Promise<AgentConfig> => {
    const response = await apiClient.post('/api/config/agent/configs', config);
    return response.data;
  },

  updateAgentConfig: async (id: string, config: Partial<AgentConfig>): Promise<AgentConfig> => {
    const response = await apiClient.put(`/api/config/agent/configs/${id}`, config);
    return response.data;
  },

  deleteAgentConfig: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/config/agent/configs/${id}`);
  },

  // Import/Export
  exportConfigurations: async (): Promise<any> => {
    const response = await apiClient.get('/api/config/export');
    return response.data;
  },

  importConfigurations: async (data: any, options?: any): Promise<any> => {
    const response = await apiClient.post('/api/config/import', {
      import_data: data,
      options: options || {},
    });
    return response.data;
  },

  // Migration
  migrateFromEnv: async (): Promise<any> => {
    const response = await apiClient.post('/api/config/migrate-from-env');
    return response.data;
  },
};

export default configurationApi;
