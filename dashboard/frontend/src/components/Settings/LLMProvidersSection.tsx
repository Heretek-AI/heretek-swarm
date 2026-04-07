/**
 * LLM Providers Section
 * 
 * Component for managing LLM provider configurations.
 * Allows users to add, edit, test, and remove LLM providers.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useToast } from '../UI/Toast';
import configurationApi, { LLMProvider, LLMProviderCreate } from '../../api/configuration';

interface LLMProvidersSectionProps {
  onProviderChange?: () => void;
}

interface ProviderFormData {
  provider_name: string;
  provider_type: string;
  base_url: string;
  api_key: string;
  api_key_hint: string;
  default_model: string;
  is_enabled: boolean;
  is_default: boolean;
  priority: number;
}

const PROVIDER_TYPES = [
  { value: 'openai', label: 'OpenAI', default_url: 'https://api.openai.com/v1' },
  { value: 'openai_compatible', label: 'OpenAI Compatible', default_url: '' },
  { value: 'ollama', label: 'Ollama', default_url: 'http://localhost:11434' },
  { value: 'llamacpp', label: 'llama.cpp', default_url: 'http://localhost:8080' },
  { value: 'zai', label: 'Z.AI (Zhipu)', default_url: 'https://open.bigmodel.cn/api/paas/v4' },
  { value: 'minimax', label: 'MiniMax', default_url: 'https://api.minimax.chat/v1' },
  { value: 'lemonade', label: 'lemonade-server', default_url: 'http://localhost:5000' },
];

const DEFAULT_MODELS: Record<string, string> = {
  openai: 'gpt-4o',
  openai_compatible: '',
  ollama: 'llama2',
  llamacpp: '',
  zai: 'glm-4',
  minimax: 'abab6.5',
  lemonade: '',
};

export function LLMProvidersSection({ onProviderChange }: LLMProvidersSectionProps) {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const toast = useToast();

  const [formData, setFormData] = useState<ProviderFormData>({
    provider_name: '',
    provider_type: 'openai',
    base_url: '',
    api_key: '',
    api_key_hint: '',
    default_model: '',
    is_enabled: true,
    is_default: false,
    priority: 100,
  });

  const loadProviders = useCallback(async () => {
    try {
      setLoading(true);
      const data = await configurationApi.listLLMProviders();
      setProviders(data);
    } catch (error) {
      toast.error('Failed to load providers', 'Could not fetch LLM providers');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  const handleOpenForm = useCallback((provider?: LLMProvider) => {
    if (provider) {
      setEditingId(provider.id);
      setFormData({
        provider_name: provider.provider_name,
        provider_type: provider.provider_type,
        base_url: provider.base_url,
        api_key: '', // Don't populate API key for security
        api_key_hint: provider.api_key_hint || '',
        default_model: provider.default_model || '',
        is_enabled: provider.is_enabled,
        is_default: provider.is_default,
        priority: provider.priority,
      });
    } else {
      setEditingId(null);
      setFormData({
        provider_name: '',
        provider_type: 'openai',
        base_url: '',
        api_key: '',
        api_key_hint: '',
        default_model: '',
        is_enabled: true,
        is_default: false,
        priority: 100,
      });
    }
    setShowForm(true);
  }, []);

  const handleCloseForm = useCallback(() => {
    setShowForm(false);
    setEditingId(null);
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const providerData: LLMProviderCreate = {
        provider_name: formData.provider_name,
        provider_type: formData.provider_type,
        base_url: formData.base_url,
        default_model: formData.default_model || undefined,
        is_enabled: formData.is_enabled,
        is_default: formData.is_default,
        priority: formData.priority,
      };

      if (formData.api_key) {
        providerData.api_key = formData.api_key;
      }
      if (formData.api_key_hint) {
        providerData.api_key_hint = formData.api_key_hint;
      }

      if (editingId) {
        await configurationApi.updateLLMProvider(editingId, providerData);
        toast.success('Provider updated', `${formData.provider_name} has been updated`);
      } else {
        await configurationApi.createLLMProvider(providerData);
        toast.success('Provider added', `${formData.provider_name} has been added`);
      }

      handleCloseForm();
      loadProviders();
      onProviderChange?.();
    } catch (error: any) {
      toast.error('Failed to save provider', error.message || 'An error occurred');
    }
  }, [formData, editingId, toast, handleCloseForm, loadProviders, onProviderChange]);

  const handleDelete = useCallback(async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;

    try {
      await configurationApi.deleteLLMProvider(id);
      toast.success('Provider deleted', `${name} has been removed`);
      loadProviders();
      onProviderChange?.();
    } catch (error: any) {
      toast.error('Failed to delete provider', error.message || 'An error occurred');
    }
  }, [toast, loadProviders, onProviderChange]);

  const handleTest = useCallback(async (id: string, providerName: string) => {
    try {
      setTesting(id);
      const result = await configurationApi.testLLMProvider(id);
      
      if (result.success) {
        toast.success(
          'Connection successful',
          `${providerName} responded in ${result.latency_ms.toFixed(0)}ms`
        );
      } else {
        toast.error('Connection failed', result.error || 'Unknown error');
      }
    } catch (error: any) {
      toast.error('Test failed', error.message || 'Could not test provider');
    } finally {
      setTesting(null);
    }
  }, [toast]);

  const handleProviderTypeChange = useCallback((type: string) => {
    const providerType = PROVIDER_TYPES.find(p => p.value === type);
    setFormData(prev => ({
      ...prev,
      provider_type: type,
      base_url: providerType?.default_url || prev.base_url,
      default_model: DEFAULT_MODELS[type] || prev.default_model,
    }));
  }, []);

  const getProviderTypeLabel = useCallback((type: string) => {
    return PROVIDER_TYPES.find(p => p.value === type)?.label || type;
  }, []);

  const getHealthStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'unhealthy': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'degraded': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">LLM Providers</h2>
          <p className="text-sm text-gray-400 mt-1">
            Configure and manage your LLM provider connections
          </p>
        </div>
        <button
          onClick={() => handleOpenForm()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
        >
          + Add Provider
        </button>
      </div>

      {/* Provider List */}
      {loading ? (
        <div className="text-center py-8 text-gray-400">Loading providers...</div>
      ) : providers.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          No LLM providers configured. Add one to get started.
        </div>
      ) : (
        <div className="grid gap-4">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className="p-4 bg-gray-900/50 border border-gray-700 rounded-xl hover:border-gray-600 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-white">{provider.provider_name}</h3>
                    <span className="text-xs px-2 py-1 bg-gray-700 rounded-full text-gray-300">
                      {getProviderTypeLabel(provider.provider_type)}
                    </span>
                    {provider.is_default && (
                      <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full">
                        Default
                      </span>
                    )}
                    {provider.is_enabled ? (
                      <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full">
                        Enabled
                      </span>
                    ) : (
                      <span className="text-xs px-2 py-1 bg-gray-500/20 text-gray-400 rounded-full">
                        Disabled
                      </span>
                    )}
                  </div>
                  <div className="mt-2 text-sm text-gray-400">
                    <span className="font-mono">{provider.base_url}</span>
                    {provider.default_model && (
                      <span className="ml-4">Model: {provider.default_model}</span>
                    )}
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span>Priority: {provider.priority}</span>
                    <span className={`px-2 py-0.5 rounded border ${getHealthStatusColor(provider.health_status)}`}>
                      {provider.health_status}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTest(provider.id, provider.provider_name)}
                    disabled={testing === provider.id}
                    className="px-3 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
                  >
                    {testing === provider.id ? 'Testing...' : 'Test'}
                  </button>
                  <button
                    onClick={() => handleOpenForm(provider)}
                    className="px-3 py-1.5 text-xs bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(provider.id, provider.provider_name)}
                    className="px-3 py-1.5 text-xs bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold text-white">
                {editingId ? 'Edit Provider' : 'Add Provider'}
              </h3>
              <button
                onClick={handleCloseForm}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Provider Name
                </label>
                <input
                  type="text"
                  value={formData.provider_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, provider_name: e.target.value }))}
                  placeholder="e.g., my-openai"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Provider Type
                </label>
                <select
                  value={formData.provider_type}
                  onChange={(e) => handleProviderTypeChange(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {PROVIDER_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Base URL
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData(prev => ({ ...prev, base_url: e.target.value }))}
                  placeholder="https://api.example.com/v1"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={formData.api_key}
                  onChange={(e) => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
                  placeholder={editingId ? 'Leave blank to keep existing' : 'sk-...'}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required={!editingId}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  API Key Hint
                </label>
                <input
                  type="text"
                  value={formData.api_key_hint}
                  onChange={(e) => setFormData(prev => ({ ...prev, api_key_hint: e.target.value }))}
                  placeholder="e.g., sk-proj-..."
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Default Model
                </label>
                <input
                  type="text"
                  value={formData.default_model}
                  onChange={(e) => setFormData(prev => ({ ...prev, default_model: e.target.value }))}
                  placeholder="e.g., gpt-4o"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_enabled: e.target.checked }))}
                    className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-400">Enabled</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_default: e.target.checked }))}
                    className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-400">Default for type</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Priority
                </label>
                <input
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: parseInt(e.target.value) || 100 }))}
                  min="1"
                  max="1000"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Lower numbers = higher priority</p>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
                <button
                  type="button"
                  onClick={handleCloseForm}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
                >
                  {editingId ? 'Save Changes' : 'Add Provider'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default LLMProvidersSection;
