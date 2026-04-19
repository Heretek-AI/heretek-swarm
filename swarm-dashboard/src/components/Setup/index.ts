/**
 * Setup Components
 *
 * Exports for the setup wizard system including:
 * - Main SetupWizard component
 * - ConfigWizard component (new cyberpunk version)
 * - Setup store for state management
 * - Validation utilities
 */

export { SetupWizard } from './SetupWizard';
export { ConfigWizard } from './ConfigWizard';

// Re-export types and utilities for external use
export {
  useSetupStore,
  useCurrentStep,
  useIsConfigured,
  useConfig,
  useApiConnection,
  useWsConnection,
  useAgentHealth,
  useIsCheckingAgents,
  useValidationErrors,
  useIsValidating,
} from '../../stores/setupStore';

export type {
  WizardStep,
  ConnectionTestResult,
  AgentHealthResult,
  SetupConfig,
  SetupState,
} from '../../stores/setupStore';

// Re-export new config wizard store
export {
  useConfigWizardStore,
  useCurrentWizardStep,
  useSelectedProviders,
  useSelectedTier,
  usePreferences,
  useIsDeploying,
  useDeploymentResult,
  useWizardError,
} from '../../stores/configWizardStore';

export type {
  WizardStep as ConfigWizardStep,
  SelectedProvider,
  WizardState as ConfigWizardState,
} from '../../stores/configWizardStore';

export {
  testApiHealth,
  testWebSocket,
  testApiKey,
  testDatabaseConnection,
  checkAgentHealth,
  validateApiHost,
  validateApiKey,
  normalizeUrl,
  deriveWsUrl,
  isValidUrl,
} from '../../utils/setupValidation';

export type {
  ValidationResult,
} from '../../utils/setupValidation';
