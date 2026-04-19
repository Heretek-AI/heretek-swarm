/**
 * Configuration Wizard Store
 *
 * Zustand store for managing the Configuration Wizard state.
 * Handles provider selection, API key input, model preferences, and tier selection.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  Provider,
  AgentTier,
  ProviderConfig,
  ConfigStatus,
} from '../api/wizard';

// =============================================================================
// Types
// =============================================================================

export type WizardStep =
  | 'welcome'
  | 'providers'
  | 'api-keys'
  | 'infrastructure'
  | 'infrastructure-review'
  | 'models'
  | 'tier'
  | 'review'
  | 'deploy'
  | 'complete';

export interface SelectedProvider {
  provider: Provider;
  apiKey: string;
  model: string;
  baseUrl?: string;
  isDefault: boolean;
  isValidated: boolean;
  validationError?: string;
}

// Infrastructure service types
export interface InfrastructureServiceConfig {
  service_type: 'postgres' | 'redis' | 'qdrant' | 'nats' | 'mem0';
  name: string;
  description: string;
  icon: string;
  default_host: string;
  default_port: number;
  requires_connection_url: boolean;
}

export interface SelectedInfrastructure {
  service: InfrastructureServiceConfig;
  host: string;
  port: number;
  connectionUrl: string;
  isConfigured: boolean;
  healthStatus: 'healthy' | 'unhealthy' | 'unknown' | 'degraded';
  healthError?: string;
}

// Available infrastructure services
export const INFRASTRUCTURE_SERVICES: InfrastructureServiceConfig[] = [
  {
    service_type: 'postgres',
    name: 'PostgreSQL',
    description: 'Vector store and persistent data',
    icon: '🐘',
    default_host: 'localhost',
    default_port: 5432,
    requires_connection_url: false,
  },
  {
    service_type: 'redis',
    name: 'Redis',
    description: 'Cache and pub/sub messaging',
    icon: '🔴',
    default_host: 'localhost',
    default_port: 6379,
    requires_connection_url: false,
  },
  {
    service_type: 'qdrant',
    name: 'Qdrant',
    description: 'Vector similarity search engine',
    icon: '🔍',
    default_host: 'localhost',
    default_port: 6333,
    requires_connection_url: false,
  },
  {
    service_type: 'nats',
    name: 'NATS',
    description: 'Agent communication and events',
    icon: '📨',
    default_host: 'localhost',
    default_port: 4222,
    requires_connection_url: false,
  },
  {
    service_type: 'mem0',
    name: 'Mem0',
    description: 'Agent memory and context',
    icon: '🧠',
    default_host: 'localhost',
    default_port: 8000,
    requires_connection_url: false,
  },
];

export interface WizardState {
  // Current wizard step
  currentStep: WizardStep;
  stepHistory: WizardStep[];

  // Provider selection
  availableProviders: Provider[];
  selectedProviders: SelectedProvider[];

  // Agent tier
  availableTiers: AgentTier[];
  selectedTierId: string;

  // Model preferences
  preferences: {
    streaming: boolean;
    functionCalling: boolean;
    vision: boolean;
  };

  // Deployment status
  isDeploying: boolean;
  deploymentResult: {
    success: boolean;
    errors: string[];
    providersCreated: number;
    agentCount: number;
  } | null;

  // Configuration status
  configStatus: ConfigStatus | null;

  // Infrastructure services
  availableInfrastructure: InfrastructureServiceConfig[];
  selectedInfrastructure: SelectedInfrastructure[];
  deployMode: 'external' | 'local' | null;

  // Loading states
  isLoadingProviders: boolean;
  isLoadingTiers: boolean;
  isLoadingInfrastructure: boolean;
  isValidating: boolean;
  isSubmitting: boolean;

  // Error state
  error: string | null;

  // Actions
  setStep: (step: WizardStep) => void;
  nextStep: () => void;
  prevStep: () => void;
  goBack: () => void;

  setProviders: (providers: Provider[]) => void;
  setTiers: (tiers: AgentTier[]) => void;
  setConfigStatus: (status: ConfigStatus) => void;

  setInfrastructure: (services: InfrastructureServiceConfig[]) => void;
  addInfrastructure: (service: InfrastructureServiceConfig) => void;
  removeInfrastructure: (serviceType: string) => void;
  updateInfrastructure: (serviceType: string, updates: Partial<SelectedInfrastructure>) => void;
  setDeployMode: (mode: 'external' | 'local' | null) => void;

  addProvider: (provider: Provider) => void;
  removeProvider: (providerId: string) => void;
  updateProvider: (providerId: string, updates: Partial<SelectedProvider>) => void;
  setDefaultProvider: (providerId: string) => void;

  setSelectedTier: (tierId: string) => void;
  setPreference: <K extends keyof WizardState['preferences']>(
    key: K,
    value: WizardState['preferences'][K]
  ) => void;

  setIsDeploying: (isDeploying: boolean) => void;
  setDeploymentResult: (
    result: WizardState['deploymentResult']
  ) => void;

  setIsLoadingProviders: (isLoading: boolean) => void;
  setIsLoadingTiers: (isLoading: boolean) => void;
  setIsLoadingInfrastructure: (isLoading: boolean) => void;
  setIsValidating: (isValidating: boolean) => void;
  setIsSubmitting: (isSubmitting: boolean) => void;
  setError: (error: string | null) => void;

  resetWizard: () => void;
}

// Step order for navigation
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

// =============================================================================
// Store Implementation
// =============================================================================

const initialState = {
  currentStep: 'welcome' as WizardStep,
  stepHistory: [] as WizardStep[],
  availableProviders: [] as Provider[],
  selectedProviders: [] as SelectedProvider[],
  availableTiers: [] as AgentTier[],
  selectedTierId: 'standard',
  preferences: {
    streaming: true,
    functionCalling: true,
    vision: false,
  },
  isDeploying: false,
  deploymentResult: null,
  configStatus: null,
  availableInfrastructure: [] as InfrastructureServiceConfig[],
  selectedInfrastructure: [] as SelectedInfrastructure[],
  deployMode: null,
  isLoadingProviders: false,
  isLoadingTiers: false,
  isLoadingInfrastructure: false,
  isValidating: false,
  isSubmitting: false,
  error: null,
};

export const useConfigWizardStore = create<WizardState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Navigation
      setStep: (step: WizardStep) => {
        const { currentStep, stepHistory } = get();
        set({
          currentStep: step,
          stepHistory: [...stepHistory, currentStep],
        });
      },

      nextStep: () => {
        const { currentStep } = get();
        const currentIndex = STEP_ORDER.indexOf(currentStep);
        if (currentIndex < STEP_ORDER.length - 1) {
          set({
            currentStep: STEP_ORDER[currentIndex + 1],
            stepHistory: [...get().stepHistory, currentStep],
          });
        }
      },

      prevStep: () => {
        const { stepHistory } = get();
        if (stepHistory.length > 0) {
          const previousStep = stepHistory[stepHistory.length - 1];
          set({
            currentStep: previousStep,
            stepHistory: stepHistory.slice(0, -1),
          });
        }
      },

      goBack: () => {
        const { stepHistory } = get();
        if (stepHistory.length > 0) {
          const previousStep = stepHistory[stepHistory.length - 1];
          set({
            currentStep: previousStep,
            stepHistory: stepHistory.slice(0, -1),
          });
        } else {
          // Default to going to welcome
          set({ currentStep: 'welcome', stepHistory: [] });
        }
      },

      // Data setters
      setProviders: (providers: Provider[]) => {
        set({ availableProviders: providers });
      },

      setTiers: (tiers: AgentTier[]) => {
        set({ availableTiers: tiers });
      },

      setConfigStatus: (status: ConfigStatus) => {
        set({ configStatus: status });
      },

      // Infrastructure management
      setInfrastructure: (services: InfrastructureServiceConfig[]) => {
        set({ availableInfrastructure: services });
      },

      addInfrastructure: (service: InfrastructureServiceConfig) => {
        const { selectedInfrastructure } = get();
        const exists = selectedInfrastructure.some((s) => s.service.service_type === service.service_type);
        if (!exists) {
          const selected: SelectedInfrastructure = {
            service,
            host: service.default_host,
            port: service.default_port,
            connectionUrl: '',
            isConfigured: false,
            healthStatus: 'unknown',
          };
          set({ selectedInfrastructure: [...selectedInfrastructure, selected] });
        }
      },

      removeInfrastructure: (serviceType: string) => {
        const { selectedInfrastructure } = get();
        set({
          selectedInfrastructure: selectedInfrastructure.filter(
            (s) => s.service.service_type !== serviceType
          ),
        });
      },

      updateInfrastructure: (serviceType: string, updates: Partial<SelectedInfrastructure>) => {
        const { selectedInfrastructure } = get();
        set({
          selectedInfrastructure: selectedInfrastructure.map((s) =>
            s.service.service_type === serviceType ? { ...s, ...updates } : s
          ),
        });
      },

      setDeployMode: (mode: 'external' | 'local' | null) => {
        set({ deployMode: mode });
      },

      // Provider management
      addProvider: (provider: Provider) => {
        const { selectedProviders } = get();
        const exists = selectedProviders.some((p) => p.provider.id === provider.id);

        if (!exists) {
          const newProvider: SelectedProvider = {
            provider,
            apiKey: '',
            model: provider.default_model,
            isDefault: selectedProviders.length === 0, // First one is default
            isValidated: false,
          };
          set({ selectedProviders: [...selectedProviders, newProvider] });
        }
      },

      removeProvider: (providerId: string) => {
        const { selectedProviders } = get();
        const filtered = selectedProviders.filter(
          (p) => p.provider.id !== providerId
        );

        // If we removed the default, make the first one default
        if (filtered.length > 0 && !filtered.some((p) => p.isDefault)) {
          filtered[0].isDefault = true;
        }

        set({ selectedProviders: filtered });
      },

      updateProvider: (providerId: string, updates: Partial<SelectedProvider>) => {
        const { selectedProviders } = get();
        set({
          selectedProviders: selectedProviders.map((p) =>
            p.provider.id === providerId ? { ...p, ...updates } : p
          ),
        });
      },

      setDefaultProvider: (providerId: string) => {
        const { selectedProviders } = get();
        set({
          selectedProviders: selectedProviders.map((p) => ({
            ...p,
            isDefault: p.provider.id === providerId,
          })),
        });
      },

      // Tier selection
      setSelectedTier: (tierId: string) => {
        set({ selectedTierId: tierId });
      },

      // Preferences
      setPreference: (key, value) => {
        const { preferences } = get();
        set({ preferences: { ...preferences, [key]: value } });
      },

      // Deployment
      setIsDeploying: (isDeploying: boolean) => {
        set({ isDeploying });
      },

      setDeploymentResult: (result) => {
        set({ deploymentResult: result });
      },

      // Loading states
      setIsLoadingProviders: (isLoading: boolean) => {
        set({ isLoadingProviders: isLoading });
      },

      setIsLoadingTiers: (isLoading: boolean) => {
        set({ isLoadingTiers: isLoading });
      },

      setIsLoadingInfrastructure: (isLoading: boolean) => {
        set({ isLoadingInfrastructure: isLoading });
      },

      setIsValidating: (isValidating: boolean) => {
        set({ isValidating });
      },

      setIsSubmitting: (isSubmitting: boolean) => {
        set({ isSubmitting });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      // Reset
      resetWizard: () => {
        set({
          ...initialState,
          availableProviders: get().availableProviders,
          availableTiers: get().availableTiers,
        });
      },
    }),
    {
      name: 'heretek-config-wizard-storage',
      partialize: (state) => ({
        selectedTierId: state.selectedTierId,
        preferences: state.preferences,
        selectedProviders: state.selectedProviders,
      }),
    }
  )
);

// =============================================================================
// Selector Hooks
// =============================================================================

export const useCurrentWizardStep = () =>
  useConfigWizardStore((state) => state.currentStep);
export const useSelectedProviders = () =>
  useConfigWizardStore((state) => state.selectedProviders);
export const useSelectedTier = () =>
  useConfigWizardStore((state) =>
    state.availableTiers.find((t) => t.id === state.selectedTierId)
  );
export const usePreferences = () =>
  useConfigWizardStore((state) => state.preferences);
export const useIsDeploying = () =>
  useConfigWizardStore((state) => state.isDeploying);
export const useDeploymentResult = () =>
  useConfigWizardStore((state) => state.deploymentResult);
export const useWizardError = () =>
  useConfigWizardStore((state) => state.error);
