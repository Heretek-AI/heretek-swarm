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

  // Loading states
  isLoadingProviders: boolean;
  isLoadingTiers: boolean;
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
  isLoadingProviders: false,
  isLoadingTiers: false,
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
