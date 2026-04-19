/**
 * Configuration Wizard - Cyberpunk Heretek Edition
 *
 * Zero-Touch Configuration Wizard following Tenet #1.
 * Dark-mode cyberpunk aesthetic with neon accents.
 *
 * Features:
 * - Provider selection with validation
 * - API key input with real-time validation
 * - Model preferences
 * - Agent tier selection
 * - Review and deploy
 */

import React, { useEffect, useCallback, useState } from 'react';
import {
  getProviders,
  getTiers,
  getConfigStatus,
  validateCredentials,
  submitConfig,
  resetWizard as apiResetWizard,
  getInfrastructureConfigs,
  saveInfrastructureConfig,
  checkInfrastructureHealth,
} from '../../api/wizard';
import type { Provider, InfrastructureConfig } from '../../api/wizard';
import { useConfigWizardStore, type SelectedProvider, type WizardStep, INFRASTRUCTURE_SERVICES, type SelectedInfrastructure } from '../../stores/configWizardStore';
import { useToast } from '../UI/Toast';

// =============================================================================
// Styles
// =============================================================================

const styles = {
  // Base container
  container: 'min-h-screen bg-[#0a0a0f] text-white flex flex-col',

  // Header
  header: 'border-b border-[#1a1a2e] bg-[#0d0d15]/80 backdrop-blur-xl sticky top-0 z-10',
  headerContent: 'max-w-6xl mx-auto px-6 py-4 flex items-center justify-between',
  logo: 'flex items-center gap-3',
  logoIcon: 'w-10 h-10 bg-gradient-to-br from-[#00f0ff] to-[#ff00f0] rounded-lg flex items-center justify-center shadow-lg shadow-[#00f0ff]/20',
  logoText: 'text-xl font-bold bg-gradient-to-r from-[#00f0ff] to-[#ff00f0] bg-clip-text text-transparent',

  // Main content
  main: 'flex-1 flex items-center justify-center p-6',
  card: 'w-full max-w-4xl bg-[#12121a] border border-[#1a1a2e] rounded-2xl shadow-2xl shadow-black/50',

  // Progress
  progressContainer: 'mb-8',
  progressBar: 'h-1 bg-[#1a1a2e] rounded-full overflow-hidden',
  progressFill: 'h-full bg-gradient-to-r from-[#00f0ff] via-[#ff00f0] to-[#00f0ff] transition-all duration-500',
  progressSteps: 'flex justify-between mt-3 text-xs text-gray-500',

  // Step titles
  stepTitle: 'text-2xl font-bold text-white mb-2 flex items-center gap-3',
  stepIcon: 'w-8 h-8 bg-gradient-to-br from-[#00f0ff] to-[#ff00f0] rounded-lg flex items-center justify-center text-sm',

  // Provider cards
  providerGrid: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6',
  providerCard: (isSelected: boolean, color: string) => `
    relative p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer
    ${isSelected
      ? `border-[${color}] bg-[${color}]/10 shadow-lg shadow-[${color}]/20`
      : 'border-[#1a1a2e] bg-[#0d0d15] hover:border-gray-600'
    }
  `,
  providerIcon: 'w-12 h-12 rounded-xl flex items-center justify-center mb-3',
  providerName: 'font-semibold text-white mb-1',
  providerDesc: 'text-xs text-gray-400',

  // Form inputs
  inputGroup: 'mb-6',
  label: 'block text-sm font-medium text-gray-300 mb-2',
  input: `w-full px-4 py-3 bg-[#0d0d15] border border-[#1a1a2e] rounded-lg
    focus:ring-2 focus:ring-[#00f0ff] focus:border-transparent
    text-white placeholder-gray-500 transition-all duration-200`,
  inputError: 'border-red-500 focus:ring-red-500',
  inputSuccess: 'border-green-500 focus:ring-green-500',

  // Buttons
  buttonPrimary: `px-8 py-3 bg-gradient-to-r from-[#00f0ff] to-[#ff00f0]
    hover:shadow-lg hover:shadow-[#00f0ff]/30
    rounded-lg font-semibold transition-all duration-200
    disabled:opacity-50 disabled:cursor-not-allowed`,
  buttonSecondary: `px-6 py-2.5 bg-[#1a1a2e] hover:bg-[#252538]
    border border-[#2a2a3e] rounded-lg font-medium transition-all duration-200`,
  buttonGhost: 'px-4 py-2 text-gray-400 hover:text-white hover:bg-[#1a1a2e] rounded-lg transition-all',

  // Navigation
  nav: 'flex justify-between items-center pt-6 mt-6 border-t border-[#1a1a2e]',

  // Tier cards
  tierCard: (isSelected: boolean) => `
    p-6 rounded-xl border-2 transition-all duration-200 cursor-pointer
    ${isSelected
      ? 'border-[#00f0ff] bg-[#00f0ff]/10 shadow-lg shadow-[#00f0ff]/20'
      : 'border-[#1a1a2e] bg-[#0d0d15] hover:border-gray-600'
    }
  `,
  tierName: 'text-lg font-bold text-white mb-1',
  tierDesc: 'text-sm text-gray-400 mb-3',
  tierStats: 'flex gap-4 text-xs',
  tierStat: 'text-gray-500',

  // Review section
  reviewSection: 'space-y-4',
  reviewItem: 'flex justify-between items-center p-4 bg-[#0d0d15] rounded-lg border border-[#1a1a2e]',
  reviewLabel: 'text-gray-400 text-sm',
  reviewValue: 'text-white font-medium',

  // Status indicators
  statusBadge: (status: 'pending' | 'validating' | 'valid' | 'invalid') => {
    const colors = {
      pending: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
      validating: 'bg-[#00f0ff]/20 text-[#00f0ff] border-[#00f0ff]/30',
      valid: 'bg-green-500/20 text-green-400 border-green-500/30',
      invalid: 'bg-red-500/20 text-red-400 border-red-500/30',
    };
    return `px-3 py-1 rounded-full text-xs font-medium border ${colors[status]}`;
  },

  // Neon glow effects
  neonBorder: 'border border-[#00f0ff]/30 hover:border-[#00f0ff]/50',
  neonGlow: 'shadow-[0_0_20px_rgba(0,240,255,0.3)]',

  // Loading spinner
  spinner: 'w-5 h-5 border-2 border-[#00f0ff] border-t-transparent rounded-full animate-spin',

  // Success/Error states
  successBox: 'p-6 rounded-xl bg-green-500/10 border border-green-500/30',
  errorBox: 'p-6 rounded-xl bg-red-500/10 border border-red-500/30',
};

// =============================================================================
// Sub-components
// =============================================================================

function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' };
  return <div className={`${styles.spinner} ${sizeClasses[size]}`} />;
}

function StepProgress({ currentStep, totalSteps, currentIndex }: {
  currentStep: string;
  totalSteps: number;
  currentIndex: number;
}) {
  const progress = (currentIndex / (totalSteps - 1)) * 100;

  return (
    <div className={styles.progressContainer}>
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className={styles.progressSteps}>
        {Array.from({ length: totalSteps }, (_, i) => (
          <span key={i} className={i <= currentIndex ? 'text-[#00f0ff]' : ''}>
            {i + 1}
          </span>
        ))}
      </div>
    </div>
  );
}

function ProviderCard({
  provider,
  isSelected,
  onSelect,
  onRemove,
}: {
  provider: Provider;
  isSelected: boolean;
  onSelect: () => void;
  onRemove?: () => void;
}) {
  return (
    <div
      className={styles.providerCard(isSelected, provider.color)}
      onClick={onSelect}
      style={{ '--provider-color': provider.color } as React.CSSProperties}
    >
      {isSelected && onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="absolute top-2 right-2 w-6 h-6 bg-red-500/20 hover:bg-red-500/40 rounded-full flex items-center justify-center text-red-400 text-xs"
        >
          x
        </button>
      )}

      <div
        className={styles.providerIcon}
        style={{ backgroundColor: `${provider.color}20` }}
      >
        <span className="text-2xl" style={{ color: provider.color }}>
          {provider.icon === 'brain' && '🧠'}
          {provider.icon === 'sparkles' && '✨'}
          {provider.icon === 'cpu' && '💻'}
          {provider.icon === 'zap' && '⚡'}
          {provider.icon === 'cloud' && '☁️'}
          {provider.icon === 'fish' && '🐟'}
          {provider.icon === 'server' && '🖥️'}
        </span>
      </div>

      <div className={styles.providerName}>{provider.name}</div>
      <div className={styles.providerDesc}>{provider.description}</div>

      <div className="mt-3 flex flex-wrap gap-2">
        {provider.supports_streaming && (
          <span className="px-2 py-0.5 bg-[#00f0ff]/10 text-[#00f0ff] text-xs rounded">
            Streaming
          </span>
        )}
        {provider.supports_function_calling && (
          <span className="px-2 py-0.5 bg-[#ff00f0]/10 text-[#ff00f0] text-xs rounded">
            Fn Calling
          </span>
        )}
        {provider.supports_vision && (
          <span className="px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded">
            Vision
          </span>
        )}
      </div>

      {isSelected && (
        <div
          className="absolute inset-0 rounded-xl border-2 pointer-events-none"
          style={{ borderColor: provider.color }}
        />
      )}
    </div>
  );
}

function TierCard({
  tier,
  isSelected,
  onSelect,
}: {
  tier: { id: string; name: string; description: string; agent_count: number; agents: string[] };
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <div className={styles.tierCard(isSelected)} onClick={onSelect}>
      <div className={styles.tierName}>{tier.name}</div>
      <div className={styles.tierDesc}>{tier.description}</div>
      <div className={styles.tierStats}>
        <span className={styles.tierStat}>
          <span className="text-[#00f0ff] font-semibold">{tier.agent_count}</span> agents
        </span>
        <span className={styles.tierStat}>
          <span className="text-[#ff00f0] font-semibold">{tier.agents.length}</span> roles
        </span>
      </div>
      {isSelected && (
        <div className="mt-3 pt-3 border-t border-[#00f0ff]/30">
          <div className="text-xs text-gray-400">
            Agents: {tier.agents.slice(0, 5).join(', ')}
            {tier.agents.length > 5 && ` +${tier.agents.length - 5} more`}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Step Components
// =============================================================================

function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center space-y-8 py-12">
      {/* Hero animation */}
      <div className="relative mx-auto w-32 h-32">
        <div className="absolute inset-0 bg-gradient-to-br from-[#00f0ff] to-[#ff00f0] rounded-full blur-2xl opacity-30 animate-pulse" />
        <div className="relative w-full h-full bg-gradient-to-br from-[#00f0ff]/20 to-[#ff00f0]/20 rounded-full border border-[#00f0ff]/30 flex items-center justify-center">
          <span className="text-5xl">⚙️</span>
        </div>
      </div>

      {/* Title */}
      <div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-[#00f0ff] to-[#ff00f0] bg-clip-text text-transparent">
          Configuration Wizard
        </h1>
        <p className="text-gray-400 mt-3 text-lg">
          Zero-Touch Setup for Heretek Swarm
        </p>
      </div>

      {/* Description */}
      <p className="text-gray-400 max-w-xl mx-auto leading-relaxed">
        Initialize your AI agent collective with intelligent defaults.
        Select your LLM providers, configure API keys, and deploy your swarm -
        all through an intuitive guided interface.
      </p>

      {/* Feature highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto pt-4">
        <div className="p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]">
          <div className="text-3xl mb-2">🔗</div>
          <div className="font-semibold text-white">LLM Providers</div>
          <div className="text-xs text-gray-400 mt-1">
            Connect Anthropic, OpenAI, Ollama & more
          </div>
        </div>
        <div className="p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]">
          <div className="text-3xl mb-2">🔐</div>
          <div className="font-semibold text-white">Secure Setup</div>
          <div className="text-xs text-gray-400 mt-1">
            API keys validated before storage
          </div>
        </div>
        <div className="p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]">
          <div className="text-3xl mb-2">🤖</div>
          <div className="font-semibold text-white">Agent Swarm</div>
          <div className="text-xs text-gray-400 mt-1">
            Deploy 1 to 23 specialized agents
          </div>
        </div>
      </div>

      {/* Start button */}
      <button onClick={onNext} className={styles.buttonPrimary}>
        Initialize Configuration
        <span className="ml-2">→</span>
      </button>
    </div>
  );
}

function ProviderSelectionStep({
  providers,
  selectedProviders,
  onAddProvider,
  onRemoveProvider,
  onNext,
  onBack,
}: {
  providers: Provider[];
  selectedProviders: SelectedProvider[];
  onAddProvider: (p: Provider) => void;
  onRemoveProvider: (id: string) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const selectedIds = selectedProviders.map((p) => p.provider.id);
  const availableToAdd = providers.filter((p) => !selectedIds.includes(p.id));

  return (
    <div className="space-y-6">
      <div>
        <div className={styles.stepTitle}>
          <div className={styles.stepIcon}>1</div>
          Select LLM Providers
        </div>
        <p className="text-gray-400">
          Choose one or more LLM providers for your agent swarm.
        </p>
      </div>

      {selectedProviders.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-300">
            Selected Providers ({selectedProviders.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {selectedProviders.map((sp) => (
              <div
                key={sp.provider.id}
                className="p-3 rounded-lg bg-[#0d0d15] border border-[#1a1a2e] flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-lg"
                    style={{ backgroundColor: `${sp.provider.color}20` }}
                  >
                    {sp.provider.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-medium text-white">{sp.provider.name}</div>
                    <div className="text-xs text-gray-500">{sp.model}</div>
                  </div>
                </div>
                <button
                  onClick={() => onRemoveProvider(sp.provider.id)}
                  className="text-gray-500 hover:text-red-400 transition-colors"
                >
                  x
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {availableToAdd.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-300">
            Available Providers ({availableToAdd.length})
          </h3>
          <div className={styles.providerGrid}>
            {availableToAdd.map((provider) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                isSelected={false}
                onSelect={() => onAddProvider(provider)}
                onRemove={() => {}}
              />
            ))}
          </div>
        </div>
      )}

      <div className={styles.nav}>
        <button onClick={onBack} className={styles.buttonSecondary}>
          Back
        </button>
        <button
          onClick={onNext}
          className={styles.buttonPrimary}
          disabled={selectedProviders.length === 0}
        >
          Continue to API Keys
        </button>
      </div>
    </div>
  );
}

function ApiKeysStep({
  selectedProviders,
  onUpdateProvider,
  onValidate,
  onNext,
  onBack,
}: {
  selectedProviders: SelectedProvider[];
  onUpdateProvider: (id: string, updates: Partial<SelectedProvider>) => void;
  onValidate: (provider: SelectedProvider) => Promise<void>;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <div className={styles.stepTitle}>
          <div className={styles.stepIcon}>2</div>
          Configure API Keys
        </div>
        <p className="text-gray-400">
          Enter API keys for your selected providers.
          Keys are validated locally before being securely stored.
        </p>
      </div>

      <div className="space-y-6">
        {selectedProviders.map((sp) => (
          <div
            key={sp.provider.id}
            className="p-6 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                  style={{ backgroundColor: `${sp.provider.color}20` }}
                >
                  {sp.provider.name.charAt(0)}
                </div>
                <div>
                  <div className="font-semibold text-white">{sp.provider.name}</div>
                  <div className="text-xs text-gray-500">
                    {sp.provider.api_key_env_var}
                  </div>
                </div>
              </div>

              <div className={styles.statusBadge(
                sp.isValidated
                  ? 'valid'
                  : sp.validationError
                  ? 'invalid'
                  : 'pending'
              )}>
                {sp.isValidated
                  ? '✓ Valid'
                  : sp.validationError
                  ? '✕ Invalid'
                  : 'Pending'}
              </div>
            </div>

            <div className="space-y-3">
              {sp.provider.requires_api_key ? (
                <div>
                  <label className={styles.label}>
                    {sp.provider.api_key_label}
                  </label>
                  <input
                    type="password"
                    value={sp.apiKey}
                    onChange={(e) =>
                      onUpdateProvider(sp.provider.id, {
                        apiKey: e.target.value,
                        isValidated: false,
                        validationError: undefined,
                      })
                    }
                    placeholder="sk-..."
                    className={`${styles.input} font-mono`}
                  />
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-[#00f0ff]/10 border border-[#00f0ff]/30 text-sm text-[#00f0ff]">
                  This provider does not require an API key
                </div>
              )}

              {sp.validationError && (
                <div className="text-sm text-red-400">{sp.validationError}</div>
              )}

              {sp.provider.requires_api_key && sp.apiKey && !sp.isValidated && (
                <button
                  onClick={() => onValidate(sp)}
                  className="px-4 py-2 bg-[#1a1a2e] hover:bg-[#252538] rounded-lg text-sm transition-colors"
                >
                  Validate Key
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className={styles.nav}>
        <button onClick={onBack} className={styles.buttonSecondary}>
          Back
        </button>
        <button
          onClick={onNext}
          className={styles.buttonPrimary}
          disabled={selectedProviders.some((p) => p.provider.requires_api_key && !p.isValidated)}
        >
          Continue to Models
        </button>
      </div>
    </div>
  );
}

function ModelPreferencesStep({
  selectedProviders,
  onUpdateProvider,
  preferences,
  onUpdatePreference,
  onNext,
  onBack,
}: {
  selectedProviders: SelectedProvider[];
  onUpdateProvider: (id: string, updates: Partial<SelectedProvider>) => void;
  preferences: { streaming: boolean; functionCalling: boolean; vision: boolean };
  onUpdatePreference: <K extends keyof typeof preferences>(
    key: K,
    value: (typeof preferences)[K]
  ) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <div className={styles.stepTitle}>
          <div className={styles.stepIcon}>3</div>
          Model Preferences
        </div>
        <p className="text-gray-400">
          Select default models for each provider and configure capabilities.
        </p>
      </div>

      {/* Provider models */}
      <div className="space-y-4">
        {selectedProviders.map((sp) => (
          <div
            key={sp.provider.id}
            className="p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]"
          >
            <div className="flex items-center gap-3 mb-3">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: `${sp.provider.color}20` }}
              >
                {sp.provider.name.charAt(0)}
              </div>
              <span className="font-medium text-white">{sp.provider.name}</span>
            </div>

            <div>
              <label className={styles.label}>Default Model</label>
              <input
                type="text"
                value={sp.model}
                onChange={(e) =>
                  onUpdateProvider(sp.provider.id, { model: e.target.value })
                }
                placeholder={sp.provider.default_model}
                className={styles.input}
              />
              <p className="text-xs text-gray-500 mt-1">
                Default: {sp.provider.default_model}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Global preferences */}
      <div className="p-6 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]">
        <h3 className="font-medium text-white mb-4">Global Capabilities</h3>

        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.streaming}
              onChange={(e) => onUpdatePreference('streaming', e.target.checked)}
              className="w-5 h-5 rounded bg-[#0d0d15] border border-[#1a1a2e] text-[#00f0ff] focus:ring-[#00f0ff]"
            />
            <div>
              <div className="text-white">Streaming Responses</div>
              <div className="text-xs text-gray-500">
                Enable streaming for faster agent responses
              </div>
            </div>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.functionCalling}
              onChange={(e) => onUpdatePreference('functionCalling', e.target.checked)}
              className="w-5 h-5 rounded bg-[#0d0d15] border border-[#1a1a2e] text-[#ff00f0] focus:ring-[#ff00f0]"
            />
            <div>
              <div className="text-white">Function Calling</div>
              <div className="text-xs text-gray-500">
                Enable agents to call external tools and APIs
              </div>
            </div>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.vision}
              onChange={(e) => onUpdatePreference('vision', e.target.checked)}
              className="w-5 h-5 rounded bg-[#0d0d15] border border-[#1a1a2e] text-green-400 focus:ring-green-400"
            />
            <div>
              <div className="text-white">Vision Support</div>
              <div className="text-xs text-gray-500">
                Enable image understanding capabilities
              </div>
            </div>
          </label>
        </div>
      </div>

      <div className={styles.nav}>
        <button onClick={onBack} className={styles.buttonSecondary}>
          Back
        </button>
        <button onClick={onNext} className={styles.buttonPrimary}>
          Continue to Tier Selection
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// Infrastructure Steps
// =============================================================================

function InfrastructureStep({
  selectedInfrastructure,
  deployMode,
  onToggleService,
  onUpdateService,
  onSetDeployMode,
  onNext,
  onBack,
}: {
  selectedInfrastructure: SelectedInfrastructure[];
  deployMode: 'external' | 'local' | null;
  onToggleService: (serviceType: string) => void;
  onUpdateService: (serviceType: string, updates: Partial<SelectedInfrastructure>) => void;
  onSetDeployMode: (mode: 'external' | 'local') => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const selectedTypes = selectedInfrastructure.map(s => s.service.service_type);

  return (
    <div className="space-y-6">
      <div>
        <div className={styles.stepTitle}>
          <div className={styles.stepIcon}>⚡</div>
          Infrastructure Setup
        </div>
        <p className="text-gray-400">
          Configure infrastructure services for your swarm.
          Select which services to enable and choose your deployment mode.
        </p>
      </div>

      {/* Deployment mode selection */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-300">Deployment Mode</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => onSetDeployMode('external')}
            className={`p-4 rounded-xl border-2 transition-all text-left ${
              deployMode === 'external'
                ? 'border-[#00f0ff] bg-[#00f0ff]/10 shadow-lg shadow-[#00f0ff]/20'
                : 'border-[#1a1a2e] bg-[#0d0d15] hover:border-gray-600'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                deployMode === 'external' ? 'bg-[#00f0ff]/20' : 'bg-[#1a1a2e]'
              }`}>
                <span className="text-2xl">☁️</span>
              </div>
              <div>
                <div className="font-semibold text-white">External Services</div>
                <div className="text-xs text-gray-500">Connect to managed cloud services</div>
              </div>
            </div>
          </button>

          <button
            onClick={() => onSetDeployMode('local')}
            className={`p-4 rounded-xl border-2 transition-all text-left ${
              deployMode === 'local'
                ? 'border-[#ff00f0] bg-[#ff00f0]/10 shadow-lg shadow-[#ff00f0]/20'
                : 'border-[#1a1a2e] bg-[#0d0d15] hover:border-gray-600'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                deployMode === 'local' ? 'bg-[#ff00f0]/20' : 'bg-[#1a1a2e]'
              }`}>
                <span className="text-2xl">🖥️</span>
              </div>
              <div>
                <div className="font-semibold text-white">Local Services</div>
                <div className="text-xs text-gray-500">Self-hosted on your infrastructure</div>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Service selection */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-300">
          Infrastructure Services ({selectedInfrastructure.length} selected)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {INFRASTRUCTURE_SERVICES.map((service) => {
            const isSelected = selectedTypes.includes(service.service_type);
            const selected = selectedInfrastructure.find(s => s.service.service_type === service.service_type);

            return (
              <div
                key={service.service_type}
                className={`p-4 rounded-xl border transition-all ${
                  isSelected
                    ? 'border-[#00f0ff] bg-[#00f0ff]/5'
                    : 'border-[#1a1a2e] bg-[#0d0d15]'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{service.icon}</span>
                    <div>
                      <div className="font-medium text-white">{service.name}</div>
                      <div className="text-xs text-gray-500">{service.description}</div>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleService(service.service_type)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-[#1a1a2e] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00f0ff]"></div>
                  </label>
                </div>

                {isSelected && selected && (
                  <div className="space-y-3 pt-3 border-t border-[#1a1a2e]">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className={styles.label}>Host</label>
                        <input
                          type="text"
                          value={selected.host}
                          onChange={(e) => onUpdateService(service.service_type, { host: e.target.value })}
                          className={styles.input}
                          placeholder={service.default_host}
                        />
                      </div>
                      <div>
                        <label className={styles.label}>Port</label>
                        <input
                          type="number"
                          value={selected.port}
                          onChange={(e) => onUpdateService(service.service_type, { port: parseInt(e.target.value) || service.default_port })}
                          className={styles.input}
                          placeholder={String(service.default_port)}
                        />
                      </div>
                    </div>
                    {service.requires_connection_url && (
                      <div>
                        <label className={styles.label}>Connection URL</label>
                        <input
                          type="text"
                          value={selected.connectionUrl}
                          onChange={(e) => onUpdateService(service.service_type, { connectionUrl: e.target.value })}
                          className={`${styles.input} font-mono text-sm`}
                          placeholder="postgresql://user:pass@host:5432/db"
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className={styles.nav}>
        <button onClick={onBack} className={styles.buttonSecondary}>
          Back
        </button>
        <button
          onClick={onNext}
          className={styles.buttonPrimary}
          disabled={selectedInfrastructure.length === 0 || !deployMode}
        >
          Review Infrastructure
        </button>
      </div>
    </div>
  );
}

function InfrastructureReviewStep({
  selectedInfrastructure,
  deployMode,
  onNext,
  onBack,
}: {
  selectedInfrastructure: SelectedInfrastructure[];
  deployMode: 'external' | 'local' | null;
  onNext: () => void;
  onBack: () => void;
}) {
  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✓';
      case 'unhealthy': return '✕';
      case 'degraded': return '⚠';
      default: return '?';
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-400';
      case 'unhealthy': return 'text-red-400';
      case 'degraded': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className={styles.stepTitle}>
          <div className={styles.stepIcon}>📋</div>
          Infrastructure Review
        </div>
        <p className="text-gray-400">
          Review your infrastructure configuration before proceeding.
        </p>
      </div>

      {/* Deployment mode badge */}
      <div className="flex items-center gap-3 p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]">
        <span className="text-2xl">{deployMode === 'external' ? '☁️' : '🖥️'}</span>
        <div>
          <div className="text-sm text-gray-400">Deployment Mode</div>
          <div className="font-medium text-white capitalize">{deployMode} Services</div>
        </div>
      </div>

      {/* Selected services */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-300">
          Configured Services ({selectedInfrastructure.length})
        </h3>
        <div className="space-y-2">
          {selectedInfrastructure.map((infra) => (
            <div
              key={infra.service.service_type}
              className="flex items-center justify-between p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]"
            >
              <div className="flex items-center gap-4">
                <span className="text-2xl">{infra.service.icon}</span>
                <div>
                  <div className="font-medium text-white">{infra.service.name}</div>
                  <div className="text-xs text-gray-500 font-mono">
                    {infra.host}:{infra.port}
                  </div>
                </div>
              </div>
              <div className={`flex items-center gap-2 ${getHealthColor(infra.healthStatus)}`}>
                <span className="text-lg">{getHealthIcon(infra.healthStatus)}</span>
                <span className="text-sm capitalize">{infra.healthStatus}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e] text-center">
          <div className="text-2xl font-bold text-[#00f0ff]">{selectedInfrastructure.length}</div>
          <div className="text-xs text-gray-500">Services Enabled</div>
        </div>
        <div className="p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e] text-center">
          <div className="text-2xl font-bold text-[#ff00f0]">
            {selectedInfrastructure.filter(s => s.service.service_type === 'nats').length}
          </div>
          <div className="text-xs text-gray-500">NATS Enabled</div>
        </div>
        <div className="p-4 rounded-xl bg-[#0d0d15] border border-[#1a1a2e] text-center">
          <div className="text-2xl font-bold text-green-400">
            {selectedInfrastructure.filter(s => s.service.service_type === 'postgres' || s.service.service_type === 'qdrant').length}
          </div>
          <div className="text-xs text-gray-500">Vector Stores</div>
        </div>
      </div>

      <div className={styles.nav}>
        <button onClick={onBack} className={styles.buttonSecondary}>
          Back
        </button>
        <button onClick={onNext} className={styles.buttonPrimary}>
          Continue to Model Preferences
        </button>
      </div>
    </div>
  );
}

function TierSelectionStep({
  tiers,
  selectedTierId,
  onSelectTier,
  onNext,
  onBack,
}: {
  tiers: Array<{ id: string; name: string; description: string; agent_count: number; agents: string[] }>;
  selectedTierId: string;
  onSelectTier: (id: string) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <div className={styles.stepTitle}>
          <div className={styles.stepIcon}>4</div>
          Agent Tier Selection
        </div>
        <p className="text-gray-400">
          Choose your agent swarm configuration.
          Each tier offers different capabilities and agent specializations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tiers.map((tier) => (
          <TierCard
            key={tier.id}
            tier={tier}
            isSelected={tier.id === selectedTierId}
            onSelect={() => onSelectTier(tier.id)}
          />
        ))}
      </div>

      <div className={styles.nav}>
        <button onClick={onBack} className={styles.buttonSecondary}>
          Back
        </button>
        <button onClick={onNext} className={styles.buttonPrimary}>
          Review Configuration
        </button>
      </div>
    </div>
  );
}

function ReviewStep({
  selectedProviders,
  selectedTier,
  preferences,
  onDeploy,
  onBack,
  isDeploying,
}: {
  selectedProviders: SelectedProvider[];
  selectedTier: { id: string; name: string; agent_count: number };
  preferences: { streaming: boolean; functionCalling: boolean; vision: boolean };
  onDeploy: () => void;
  onBack: () => void;
  isDeploying: boolean;
}) {
  return (
    <div className="space-y-6">
      <div>
        <div className={styles.stepTitle}>
          <div className={styles.stepIcon}>5</div>
          Review & Deploy
        </div>
        <p className="text-gray-400">
          Verify your configuration before deploying the swarm.
        </p>
      </div>

      <div className={styles.reviewSection}>
        <h3 className="text-sm font-medium text-gray-300 mb-3">LLM Providers</h3>
        {selectedProviders.map((sp) => (
          <div key={sp.provider.id} className={styles.reviewItem}>
            <div className="flex items-center gap-3">
              <div
                className="w-6 h-6 rounded flex items-center justify-center text-xs font-bold"
                style={{ backgroundColor: `${sp.provider.color}20`, color: sp.provider.color }}
              >
                {sp.provider.name.charAt(0)}
              </div>
              <span className={styles.reviewValue}>{sp.provider.name}</span>
            </div>
            <span className="text-gray-500 text-sm">{sp.model}</span>
          </div>
        ))}
      </div>

      <div className={styles.reviewSection}>
        <h3 className="text-sm font-medium text-gray-300 mb-3">Agent Configuration</h3>
        <div className={styles.reviewItem}>
          <span className={styles.reviewLabel}>Tier</span>
          <span className={styles.reviewValue}>{selectedTier.name}</span>
        </div>
        <div className={styles.reviewItem}>
          <span className={styles.reviewLabel}>Agent Count</span>
          <span className={styles.reviewValue}>{selectedTier.agent_count}</span>
        </div>
        <div className={styles.reviewItem}>
          <span className={styles.reviewLabel}>Capabilities</span>
          <span className={styles.reviewValue}>
            {[
              preferences.streaming && 'Streaming',
              preferences.functionCalling && 'Function Calling',
              preferences.vision && 'Vision',
            ]
              .filter(Boolean)
              .join(', ') || 'None'}
          </span>
        </div>
      </div>

      <div className={styles.nav}>
        <button onClick={onBack} className={styles.buttonSecondary} disabled={isDeploying}>
          Back
        </button>
        <button
          onClick={onDeploy}
          className={styles.buttonPrimary}
          disabled={isDeploying}
        >
          {isDeploying ? (
            <>
              <LoadingSpinner size="sm" />
              <span className="ml-2">Deploying...</span>
            </>
          ) : (
            'Deploy Swarm'
          )}
        </button>
      </div>
    </div>
  );
}

function DeployingStep({ onNext }: { onNext: () => void }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(interval);
          return 100;
        }
        return p + Math.random() * 15;
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-center space-y-8 py-12">
      <div className="relative mx-auto w-32 h-32">
        <div
          className="absolute inset-0 rounded-full border-4 border-[#00f0ff]/20"
          style={{ clipPath: `polygon(50% 50%, 50% 0%, ${progress}% 0%, ${progress}% 100%, 50% 100%, 50% 0%)` }}
        />
        <div className="absolute inset-2 bg-gradient-to-br from-[#00f0ff]/10 to-[#ff00f0]/10 rounded-full" />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-3xl">🚀</span>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-white">Deploying Your Swarm</h2>
        <p className="text-gray-400 mt-2">
          Initializing agents and configuring infrastructure...
        </p>
      </div>

      <div className="max-w-md mx-auto">
        <div className="h-2 bg-[#1a1a2e] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#00f0ff] to-[#ff00f0] transition-all duration-500"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-2 text-right">
          {Math.round(Math.min(progress, 100))}% complete
        </p>
      </div>

      {progress >= 100 && (
        <button onClick={onNext} className={styles.buttonPrimary}>
          View Results
        </button>
      )}
    </div>
  );
}

function CompleteStep({
  result,
  onReset,
}: {
  result: { success: boolean; errors: string[]; providersCreated: number; agentCount: number } | null;
  onReset: () => void;
}) {
  return (
    <div className="text-center space-y-8 py-12">
      {result?.success ? (
        <>
          <div className="relative mx-auto w-32 h-32">
            <div className="absolute inset-0 bg-gradient-to-br from-green-400 to-emerald-600 rounded-full blur-xl opacity-30" />
            <div className="relative w-full h-full bg-gradient-to-br from-green-400 to-emerald-600 rounded-full flex items-center justify-center">
              <span className="text-5xl">✓</span>
            </div>
          </div>

          <div>
            <h2 className="text-3xl font-bold text-white">Deployment Complete!</h2>
            <p className="text-gray-400 mt-2">
              Your Heretek Swarm is ready to operate
            </p>
          </div>

          <div className="max-w-md mx-auto p-6 rounded-xl bg-[#0d0d15] border border-[#1a1a2e]">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Providers Configured</span>
                <span className="text-[#00f0ff] font-semibold">{result.providersCreated}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Agents Deployed</span>
                <span className="text-[#ff00f0] font-semibold">{result.agentCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Status</span>
                <span className="text-green-400 font-semibold">Active</span>
              </div>
            </div>
          </div>

          <button onClick={onReset} className={styles.buttonSecondary}>
            Reconfigure
          </button>
        </>
      ) : (
        <>
          <div className="relative mx-auto w-32 h-32">
            <div className="absolute inset-0 bg-gradient-to-br from-red-400 to-red-600 rounded-full blur-xl opacity-30" />
            <div className="relative w-full h-full bg-gradient-to-br from-red-400 to-red-600 rounded-full flex items-center justify-center">
              <span className="text-5xl">✕</span>
            </div>
          </div>

          <div>
            <h2 className="text-3xl font-bold text-white">Deployment Failed</h2>
            <p className="text-gray-400 mt-2">
              There were errors during configuration
            </p>
          </div>

          <div className={styles.errorBox}>
            <div className="text-sm text-red-400 space-y-2">
              {result?.errors.map((err, i) => (
                <div key={i}>{err}</div>
              ))}
            </div>
          </div>

          <button onClick={onReset} className={styles.buttonPrimary}>
            Try Again
          </button>
        </>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

const STEP_ORDER: WizardStep[] = [
  'welcome',
  'providers',
  'api-keys',
  'infrastructure',
  'infrastructure-review',
  'models',
  'tier',
  'review',
  'deploy',
  'complete',
];

export function ConfigWizard({ onComplete }: { onComplete?: () => void }) {
  const toast = useToast();
  const {
    currentStep,
    availableProviders,
    selectedProviders,
    availableTiers,
    selectedTierId,
    preferences,
    isDeploying,
    deploymentResult,
    isLoadingProviders,
    isLoadingTiers,
    selectedInfrastructure,
    deployMode,
    setStep,
    nextStep,
    goBack,
    setProviders,
    setTiers,
    addProvider,
    removeProvider,
    updateProvider,
    setSelectedTier,
    setPreference,
    setIsDeploying,
    setDeploymentResult,
    setIsValidating,
    setIsLoadingInfrastructure,
    setError,
    resetWizard,
    addInfrastructure,
    removeInfrastructure,
    updateInfrastructure,
    setDeployMode,
  } = useConfigWizardStore();

  // Load providers and tiers on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [providersData, tiersData] = await Promise.all([
          getProviders(),
          getTiers(),
        ]);
        setProviders(providersData.providers);
        setTiers(tiersData.tiers);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load wizard data');
        toast.error('Error', 'Failed to load wizard data');
      }
    };

    if (currentStep !== 'welcome' && availableProviders.length === 0) {
      loadData();
    }
  }, [currentStep, availableProviders.length, setProviders, setTiers, setError, toast]);

  // Infrastructure service toggle handler
  const toggleInfrastructureService = useCallback((serviceType: string) => {
    const isSelected = selectedInfrastructure.some(s => s.service.service_type === serviceType);
    if (isSelected) {
      removeInfrastructure(serviceType);
    } else {
      const service = INFRASTRUCTURE_SERVICES.find(s => s.service_type === serviceType);
      if (service) {
        addInfrastructure(service);
      }
    }
  }, [selectedInfrastructure, addInfrastructure, removeInfrastructure]);

  // Update infrastructure config (host, port, connectionUrl)
  const updateInfrastructureConfig = useCallback((serviceType: string, updates: Partial<SelectedInfrastructure>) => {
    updateInfrastructure(serviceType, updates);
  }, [updateInfrastructure]);

  const handleValidate = useCallback(
    async (provider: SelectedProvider) => {
      if (!provider.apiKey) return;

      setIsValidating(true);
      updateProvider(provider.provider.id, { validationError: undefined });

      try {
        const result = await validateCredentials(
          provider.provider.id,
          provider.apiKey,
          provider.baseUrl
        );

        if (result.valid) {
          updateProvider(provider.provider.id, {
            isValidated: true,
            validationError: undefined,
          });
          toast.success('Valid', `${provider.provider.name} API key validated`);
        } else {
          updateProvider(provider.provider.id, {
            isValidated: false,
            validationError: result.error,
          });
          toast.error('Invalid', result.error || 'API key validation failed');
        }
      } catch (err) {
        updateProvider(provider.provider.id, {
          isValidated: false,
          validationError: err instanceof Error ? err.message : 'Validation failed',
        });
        toast.error('Error', 'Failed to validate API key');
      } finally {
        setIsValidating(false);
      }
    },
    [updateProvider, setIsValidating, toast]
  );

  const handleDeploy = useCallback(async () => {
    setIsDeploying(true);

    // Move to deploying step
    nextStep();

    try {
      const tier = availableTiers.find((t) => t.id === selectedTierId);

      const config = {
        providers: selectedProviders.map((sp) => ({
          provider_id: sp.provider.id,
          api_key: sp.apiKey || undefined,
          model: sp.model,
          base_url: sp.baseUrl,
          is_default: sp.isDefault,
        })),
        tier: selectedTierId,
        preferences: {
          streaming: preferences.streaming,
          function_calling: preferences.functionCalling,
          vision: preferences.vision,
        },
      };

      const result = await submitConfig(config);

      setDeploymentResult({
        success: result.success,
        errors: result.errors,
        providersCreated: result.providers_created.length,
        agentCount: result.config.agent_count || tier?.agent_count || 0,
      });

      if (result.success) {
        toast.success('Success', 'Swarm deployed successfully');
      } else {
        toast.error('Deployment Issues', `${result.errors.length} errors occurred`);
      }
    } catch (err) {
      setDeploymentResult({
        success: false,
        errors: [err instanceof Error ? err.message : 'Deployment failed'],
        providersCreated: 0,
        agentCount: 0,
      });
      toast.error('Error', 'Failed to deploy swarm');
    } finally {
      setIsDeploying(false);
    }
  }, [
    selectedProviders,
    selectedTierId,
    preferences,
    availableTiers,
    nextStep,
    setIsDeploying,
    setDeploymentResult,
    toast,
  ]);

  const handleReset = useCallback(async () => {
    try {
      await apiResetWizard();
      resetWizard();
      setStep('welcome');
    } catch (err) {
      toast.error('Error', 'Failed to reset wizard');
    }
  }, [resetWizard, setStep, toast]);

  const handleComplete = useCallback(() => {
    onComplete?.();
  }, [onComplete]);

  const currentIndex = STEP_ORDER.indexOf(currentStep);
  const selectedTier = availableTiers.find((t) => t.id === selectedTierId);

  const renderStep = () => {
    switch (currentStep) {
      case 'welcome':
        return <WelcomeStep onNext={nextStep} />;

      case 'providers':
        return (
          <ProviderSelectionStep
            providers={availableProviders}
            selectedProviders={selectedProviders}
            onAddProvider={addProvider}
            onRemoveProvider={removeProvider}
            onNext={nextStep}
            onBack={goBack}
          />
        );

      case 'api-keys':
        return (
          <ApiKeysStep
            selectedProviders={selectedProviders}
            onUpdateProvider={updateProvider}
            onValidate={handleValidate}
            onNext={nextStep}
            onBack={goBack}
          />
        );

      case 'infrastructure':
        return (
          <InfrastructureStep
            selectedInfrastructure={selectedInfrastructure}
            deployMode={deployMode}
            onToggleService={toggleInfrastructureService}
            onUpdateService={updateInfrastructureConfig}
            onSetDeployMode={setDeployMode}
            onNext={nextStep}
            onBack={goBack}
          />
        );

      case 'infrastructure-review':
        return (
          <InfrastructureReviewStep
            selectedInfrastructure={selectedInfrastructure}
            deployMode={deployMode}
            onNext={nextStep}
            onBack={goBack}
          />
        );

      case 'models':
        return (
          <ModelPreferencesStep
            selectedProviders={selectedProviders}
            onUpdateProvider={updateProvider}
            preferences={preferences}
            onUpdatePreference={setPreference}
            onNext={nextStep}
            onBack={goBack}
          />
        );

      case 'tier':
        return (
          <TierSelectionStep
            tiers={availableTiers}
            selectedTierId={selectedTierId}
            onSelectTier={setSelectedTier}
            onNext={nextStep}
            onBack={goBack}
          />
        );

      case 'review':
        return (
          <ReviewStep
            selectedProviders={selectedProviders}
            selectedTier={selectedTier || { id: selectedTierId, name: 'Unknown', agent_count: 0 }}
            preferences={preferences}
            onDeploy={handleDeploy}
            onBack={goBack}
            isDeploying={isDeploying}
          />
        );

      case 'deploy':
        return <DeployingStep onNext={nextStep} />;

      case 'complete':
        return <CompleteStep result={deploymentResult} onReset={handleReset} />;

      default:
        return <WelcomeStep onNext={nextStep} />;
    }
  };

  const showProgress = currentStep !== 'welcome' && currentStep !== 'complete' && currentStep !== 'deploy';

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logo}>
            <div className={styles.logoIcon}>
              <span className="text-xl">⚙️</span>
            </div>
            <span className={styles.logoText}>Heretek Swarm</span>
          </div>

          {showProgress && (
            <StepProgress
              currentStep={currentStep}
              totalSteps={STEP_ORDER.length - 1}
              currentIndex={currentIndex}
            />
          )}

          <button
            onClick={handleComplete}
            className={styles.buttonGhost}
          >
            Skip Setup
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className={styles.main}>
        <div className={styles.card}>
          <div className="p-8">
            {isLoadingProviders || isLoadingTiers ? (
              <div className="flex items-center justify-center py-20">
                <LoadingSpinner size="lg" />
                <span className="ml-4 text-gray-400">Loading wizard data...</span>
              </div>
            ) : (
              renderStep()
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1a1a2e] py-4">
        <div className="max-w-6xl mx-auto px-6 text-center text-xs text-gray-600">
          Heretek Swarm Configuration Wizard
        </div>
      </footer>
    </div>
  );
}

export default ConfigWizard;
