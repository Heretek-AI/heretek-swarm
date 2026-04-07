/**
 * Settings Page
 * 
 * Configuration management for Heretek Swarm.
 * Provides UI for managing LLM providers, embedding providers, system settings, and more.
 */

import React, { useState, useCallback } from 'react';
import { useToast } from '../UI/Toast';
import { DeveloperModeToggle } from './DeveloperModeToggle';
import {
  LLMProvidersSection,
  EmbeddingProvidersSection,
  SystemConfigSection,
  AgentDefaultsSection,
  ImportExportSection,
} from '.';

interface TabConfig {
  id: string;
  label: string;
  icon: string;
}

const tabs: TabConfig[] = [
  { id: 'llm', label: 'LLM Providers', icon: '🤖' },
  { id: 'embedding', label: 'Embedding', icon: '📊' },
  { id: 'system', label: 'System', icon: '⚙️' },
  { id: 'agents', label: 'Agent Defaults', icon: '👥' },
  { id: 'import', label: 'Import/Export', icon: '📁' },
];

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<string>('llm');
  const [apiKey, setApiKey] = useState(localStorage.getItem('api_key') || '');
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || '');
  const toast = useToast();

  const handleSaveApiKey = useCallback(() => {
    localStorage.setItem('api_key', apiKey);
    toast.success('API Key Saved', 'Your API key has been stored locally');
  }, [apiKey, toast]);

  const handleSaveApiUrl = useCallback(() => {
    localStorage.setItem('api_url', apiUrl);
    toast.success('API URL Saved', 'The API URL will be used on next refresh');
  }, [apiUrl, toast]);

  const handleClearApiKey = useCallback(() => {
    localStorage.removeItem('api_key');
    setApiKey('');
    toast.info('API Key Cleared', 'Your API key has been removed');
  }, [toast]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'llm':
        return <LLMProvidersSection />;
      case 'embedding':
        return <EmbeddingProvidersSection />;
      case 'system':
        return <SystemConfigSection />;
      case 'agents':
        return <AgentDefaultsSection />;
      case 'import':
        return <ImportExportSection />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-400 text-sm mt-1">
          System configuration and provider management
        </p>
      </div>

      {/* Developer Mode Toggle */}
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🔧</span> Developer Tools
        </h2>
        <DeveloperModeToggle />
      </div>

      {/* Connection Settings */}
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🔌</span> Connection Settings
        </h2>
        <div className="space-y-4">
          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              API Key
            </label>
            <div className="flex gap-2">
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="flex-1 px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={handleSaveApiKey}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
              >
                Save
              </button>
              {apiKey && (
                <button
                  onClick={handleClearApiKey}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Your API key is stored locally in your browser and used for authenticated requests.
            </p>
          </div>

          {/* API URL */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              API URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="API base URL (leave empty for relative path)"
                className="flex-1 px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={handleSaveApiUrl}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
              >
                Save
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to use the relative path (recommended for nginx proxy setup).
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl">
        <div className="border-b border-gray-700">
          <nav className="flex overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {renderTabContent()}
        </div>
      </div>

      {/* About Section */}
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>ℹ️</span> About
        </h2>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Version</span>
            <span className="text-white font-mono">0.2.0</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Build</span>
            <span className="text-white font-mono">2026.04</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-400">Repository</span>
            <a
              href="https://github.com/heretek/heretek-swarm"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              heretek/heretek-swarm
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
