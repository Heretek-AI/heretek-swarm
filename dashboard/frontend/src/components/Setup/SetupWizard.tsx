/**
 * Setup Wizard Component
 * 
 * First-time setup wizard for configuring external services,
 * LLM providers, and embedding providers.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useToast } from '../UI/Toast';

interface SetupWizardProps {
  onComplete: () => void;
}

type Step = 'welcome' | 'llm' | 'embedding' | 'test' | 'complete';

interface LLMConfig {
  provider_type: string;
  api_key: string;
  base_url: string;
  default_model: string;
}

interface EmbeddingConfig {
  provider_type: string;
  api_key: string;
  base_url: string;
  model: string;
}

const LLM_PROVIDERS = [
  { value: 'openai', label: 'OpenAI', defaultModel: 'gpt-4o', defaultUrl: 'https://api.openai.com/v1' },
  { value: 'ollama', label: 'Ollama (Local)', defaultModel: 'llama2', defaultUrl: 'http://localhost:11434' },
  { value: 'openai_compatible', label: 'OpenAI Compatible', defaultModel: '', defaultUrl: '' },
  { value: 'zai', label: 'Z.AI (Zhipu)', defaultModel: 'glm-4', defaultUrl: 'https://open.bigmodel.cn/api/paas/v4' },
];

const EMBEDDING_PROVIDERS = [
  { value: 'openai', label: 'OpenAI', defaultModel: 'text-embedding-3-small', defaultUrl: 'https://api.openai.com/v1' },
  { value: 'ollama', label: 'Ollama (Local)', defaultModel: 'nomic-embed-text', defaultUrl: 'http://localhost:11434' },
  { value: 'azure', label: 'Azure OpenAI', defaultModel: 'text-embedding-3-small', defaultUrl: '' },
];

export function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState<Step>('welcome');
  const [llmConfig, setLlmConfig] = useState<LLMConfig>({
    provider_type: 'openai',
    api_key: '',
    base_url: 'https://api.openai.com/v1',
    default_model: 'gpt-4o',
  });
  const [embeddingConfig, setEmbeddingConfig] = useState<EmbeddingConfig>({
    provider_type: 'openai',
    api_key: '',
    base_url: 'https://api.openai.com/v1',
    model: 'text-embedding-3-small',
  });
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState<{llm?: boolean; embedding?: boolean}>({});
  const toast = useToast();

  const isConfigured = localStorage.getItem('swarm_configured') === 'true';

  useEffect(() => {
    if (isConfigured) {
      onComplete();
    }
  }, [isConfigured, onComplete]);

  const handleLLMProviderChange = useCallback((providerType: string) => {
    const provider = LLM_PROVIDERS.find(p => p.value === providerType);
    if (provider) {
      setLlmConfig(prev => ({
        ...prev,
        provider_type: providerType,
        base_url: provider.defaultUrl,
        default_model: provider.defaultModel,
      }));
    }
  }, []);

  const handleEmbeddingProviderChange = useCallback((providerType: string) => {
    const provider = EMBEDDING_PROVIDERS.find(p => p.value === providerType);
    if (provider) {
      setEmbeddingConfig(prev => ({
        ...prev,
        provider_type: providerType,
        base_url: provider.defaultUrl,
        model: provider.defaultModel,
      }));
    }
  }, []);

  const handleTestConnection = useCallback(async () => {
    setTesting(true);
    setTestResults({});

    // Test LLM connection
    let llmSuccess = false;
    if (llmConfig.api_key && llmConfig.base_url) {
      try {
        const response = await fetch(`${llmConfig.base_url}/models`, {
          headers: {
            'Authorization': `Bearer ${llmConfig.api_key}`,
          },
        });
        llmSuccess = response.ok;
      } catch {
        llmSuccess = false;
      }
    }

    // Test embedding connection
    let embeddingSuccess = false;
    if (embeddingConfig.api_key && embeddingConfig.base_url) {
      try {
        const response = await fetch(`${embeddingConfig.base_url}/embeddings`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${embeddingConfig.api_key}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: embeddingConfig.model,
            input: 'test',
          }),
        });
        embeddingSuccess = response.ok;
      } catch {
        embeddingSuccess = false;
      }
    }

    setTestResults({ llm: llmSuccess, embedding: embeddingSuccess });
    setTesting(false);
  }, [llmConfig, embeddingConfig]);

  const handleComplete = useCallback(() => {
    // Save configuration to localStorage
    localStorage.setItem('llm_provider', JSON.stringify(llmConfig));
    localStorage.setItem('embedding_provider', JSON.stringify(embeddingConfig));
    localStorage.setItem('swarm_configured', 'true');
    toast.success('Setup Complete', 'Your Heretek Swarm is now configured!');
    onComplete();
  }, [llmConfig, embeddingConfig, onComplete, toast]);

  const renderStep = () => {
    switch (step) {
      case 'welcome':
        return (
          <div className="text-center space-y-6">
            <div className="text-6xl">🚀</div>
            <h2 className="text-2xl font-bold">Welcome to Heretek Swarm</h2>
            <p className="text-gray-400 max-w-md">
              Let's get your swarm configured. We'll set up your LLM provider, 
              embedding service, and verify connectivity to external services.
            </p>
            <button
              onClick={() => setStep('llm')}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
            >
              Get Started
            </button>
          </div>
        );

      case 'llm':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">🤖</div>
              <h2 className="text-xl font-bold">LLM Provider Configuration</h2>
              <p className="text-gray-400 text-sm">Select your language model provider</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Provider</label>
                <select
                  value={llmConfig.provider_type}
                  onChange={(e) => handleLLMProviderChange(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {LLM_PROVIDERS.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">API URL</label>
                <input
                  type="text"
                  value={llmConfig.base_url}
                  onChange={(e) => setLlmConfig(prev => ({ ...prev, base_url: e.target.value }))}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.openai.com/v1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <input
                  type="password"
                  value={llmConfig.api_key}
                  onChange={(e) => setLlmConfig(prev => ({ ...prev, api_key: e.target.value }))}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="sk-..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Default Model</label>
                <input
                  type="text"
                  value={llmConfig.default_model}
                  onChange={(e) => setLlmConfig(prev => ({ ...prev, default_model: e.target.value }))}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="gpt-4o"
                />
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep('welcome')}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setStep('embedding')}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        );

      case 'embedding':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">📊</div>
              <h2 className="text-xl font-bold">Embedding Provider Configuration</h2>
              <p className="text-gray-400 text-sm">Select your embedding service for vector search</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Provider</label>
                <select
                  value={embeddingConfig.provider_type}
                  onChange={(e) => handleEmbeddingProviderChange(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {EMBEDDING_PROVIDERS.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">API URL</label>
                <input
                  type="text"
                  value={embeddingConfig.base_url}
                  onChange={(e) => setEmbeddingConfig(prev => ({ ...prev, base_url: e.target.value }))}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.openai.com/v1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <input
                  type="password"
                  value={embeddingConfig.api_key}
                  onChange={(e) => setEmbeddingConfig(prev => ({ ...prev, api_key: e.target.value }))}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="sk-..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Model</label>
                <input
                  type="text"
                  value={embeddingConfig.model}
                  onChange={(e) => setEmbeddingConfig(prev => ({ ...prev, model: e.target.value }))}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="text-embedding-3-small"
                />
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep('llm')}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setStep('test')}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        );

      case 'test':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">🔗</div>
              <h2 className="text-xl font-bold">Test Connections</h2>
              <p className="text-gray-400 text-sm">Verify your configuration works</p>
            </div>

            <div className="space-y-4">
              <div className="bg-gray-800 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <div className="font-medium">LLM Provider</div>
                  <div className="text-sm text-gray-400">{llmConfig.provider_type} - {llmConfig.default_model}</div>
                </div>
                {testResults.llm !== undefined && (
                  <span className={testResults.llm ? 'text-green-400' : 'text-red-400'}>
                    {testResults.llm ? '✓ Connected' : '✗ Failed'}
                  </span>
                )}
              </div>

              <div className="bg-gray-800 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <div className="font-medium">Embedding Provider</div>
                  <div className="text-sm text-gray-400">{embeddingConfig.provider_type} - {embeddingConfig.model}</div>
                </div>
                {testResults.embedding !== undefined && (
                  <span className={testResults.embedding ? 'text-green-400' : 'text-red-400'}>
                    {testResults.embedding ? '✓ Connected' : '✗ Failed'}
                  </span>
                )}
              </div>
            </div>

            <button
              onClick={handleTestConnection}
              disabled={testing}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-lg font-semibold transition-colors"
            >
              {testing ? 'Testing...' : 'Test Connections'}
            </button>

            <div className="flex justify-between">
              <button
                onClick={() => setStep('embedding')}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setStep('complete')}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
              >
                Skip Test
              </button>
            </div>
          </div>
        );

      case 'complete':
        return (
          <div className="text-center space-y-6">
            <div className="text-6xl">✅</div>
            <h2 className="text-2xl font-bold">Setup Complete!</h2>
            <p className="text-gray-400 max-w-md">
              Your Heretek Swarm is now configured. You can always change these 
              settings in the Settings page.
            </p>
            <button
              onClick={handleComplete}
              className="px-8 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors"
            >
              Enter Dashboard
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-8">
      <div className="max-w-lg w-full bg-gray-800 rounded-2xl p-8 shadow-2xl">
        {renderStep()}
      </div>
    </div>
  );
}