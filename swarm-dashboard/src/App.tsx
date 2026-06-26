/**
 * Heretek Swarm Dashboard - Main Application
 *
 * Central control panel for deploying, monitoring, and configuring
 * the Heretek Swarm application.
 *
 * Health check pattern (M005/S01): `checkSystemHealth()` reads the top-level
 * `data.status === 'healthy'` as primary signal. Service-level status lives
 * under `data.services.*.status` and is only consulted for 'degraded' detection.
 * This handles `--no-infra` mode where infra services report 'unhealthy' but
 * the top-level status is still 'healthy'.
 */

import { useState, useEffect, useCallback } from 'react';
import { MemoryRouter, Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { HomePage as NewHomePage } from './pages/home-page';
import { DeliberationListPage as NewDeliberationListPage } from './pages/deliberation-list-page';
import { DeliberationPage as NewDeliberationPage } from './pages/deliberation-page';

/**
 * Validates that a URL is safe for use in client-side requests.
 * Returns the URL if it starts with '/' (relative) or http(s):// (absolute),
 * otherwise returns empty string to prevent javascript: or data: URLs.
 */
function _safeUrl(raw: string): string {
  if (!raw || typeof raw !== 'string') return '';
  const trimmed = raw.trim();
  if (trimmed.startsWith('/') || /^https?:\/\//i.test(trimmed)) return trimmed;
  return '';
}
import { DashboardLayout, NavItem } from './components/Dashboard/Layout';
import { AgentsPage } from './components/Agents/AgentsPage';
import { ConsciousnessPage } from './components/Consciousness/ConsciousnessPage';
import { AutonomousPage } from './components/Autonomous/AutonomousPage';
import { ObservabilityPage } from './components/Observability/ObservabilityPage';
import { MessageList } from './components/Chat/MessageList';
import { AnalysisHistory } from './components/Autonomous/AnalysisHistory';
import { EnhancedCanvas } from './components/Canvas/EnhancedCanvas';
import { SettingsPage } from './components/Settings/SettingsPage';
import { LogsPage } from './components/Logs/LogsPage';
import { ToastProvider, useToast } from './components/UI/Toast';
import { ErrorBoundary } from './components/UI/ErrorBoundary';
import { DebugPanel } from './components/UI/DebugPanel';
import { PerformanceOverlay } from './components/UI/PerformanceOverlay';
import { SetupWizard } from './components/Setup';
import { useSetupStore } from './stores/setupStore';
import { setToastInstance } from './api/client';

import { WorkflowBuilder } from './components/WorkflowBuilder/WorkflowBuilder';
import { CommandPalette, CommandItem } from './components/UI/CommandPalette';

type View =
  | 'agents'
  | 'consciousness'
  | 'autonomous'
  | 'workflows'
  | 'logs'
  | 'settings'
  | 'observability'
  | 'chat'
  | 'memory'
  | 'canvas';

const navItems: NavItem[] = [
  { id: 'agents', label: 'Agents', icon: '🤖' },
  { id: 'consciousness', label: 'Consciousness', icon: '🧠' },
  { id: 'autonomous', label: 'Autonomous', icon: '🔄' },
  { id: 'observability', label: 'Observability', icon: '🔍' },
  { id: 'memory', label: 'Memory', icon: '🧠' },
  { id: 'chat', label: 'Chat', icon: '💬' },
  { id: 'canvas', label: 'Canvas', icon: '🎨' },
  { id: 'workflows', label: 'Workflows', icon: '🔀' },
  { id: 'logs', label: 'Terminal/Logs', icon: '📟' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

function DashboardContent() {
  const [currentView, setCurrentView] = useState<View>('agents');
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded' | 'offline'>('healthy');
  const toast = useToast();

  // Setup store integration
  const { config, setRerunning, resetSetup } = useSetupStore();

  const [showSetup, setShowSetup] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Check if setup is needed on mount
  useEffect(() => {
    const checkConfiguration = () => {
      const storedConfigured = localStorage.getItem('swarm_configured') === 'true';
      const storedApiHost = localStorage.getItem('swarm_api_host');

      // Check for VITE environment variables first (set by docker-compose)
      const envApiKey = import.meta.env.VITE_API_KEY;
      const envApiHost = import.meta.env.VITE_API_HOST;

      if (!storedConfigured || !storedApiHost) {
        // Not configured or no stored API host - check env vars
        // Only auto-skip wizard if BOTH host AND key are set via env
        // Having only envApiHost means the user still needs to enter the key interactively
        if (envApiKey && envApiHost) {
          // Both env vars present — pre-populate and skip wizard
          localStorage.setItem('swarm_api_host', envApiHost);
          localStorage.setItem('swarm_configured', 'true');

          useSetupStore.getState().setConfig({
            apiHost: envApiHost,
            apiKey: envApiKey,
            wsHost: '',
          });

          setShowSetup(false);
        } else {
          // No env vars or missing key — show wizard so user can enter credentials
          setShowSetup(true);
        }
      } else {
        // Restore config from localStorage if not in store
        if (!config.apiHost) {
          useSetupStore.getState().setConfig({
            apiHost: storedApiHost,
            apiKey: '',
            wsHost: localStorage.getItem('swarm_ws_host') || '',
          });
        }
        setShowSetup(false);
      }
      setIsInitialized(true);
    };

    checkConfiguration();
  }, []);

  // Set toast instance for API client
  useEffect(() => {
    setToastInstance({
      error: (title, message) => toast.error(title, message),
    });
  }, [toast]);

  // Check system health periodically
  const checkSystemHealth = useCallback(async () => {
    try {
      // Use stored API host or fall back to environment variable
      const apiHost = _safeUrl(
        localStorage.getItem('swarm_api_host') || import.meta.env.VITE_API_HOST || '',
      );
      if (!apiHost) {
        setSystemStatus('offline');
        return;
      }

      const response = await fetch(`${apiHost}/api/health`);
      if (!response.ok) {
        setSystemStatus('offline');
        return;
      }
      const data = await response.json();

      // Primary signal: top-level status from the API.
      // In --no-infra mode, the API returns { status: 'healthy' } even when
      // infra services are unavailable — this is correct behavior.
      if (data.status === 'healthy') {
        setSystemStatus('healthy');
        return;
      }

      // Secondary: if the API responded but top-level status isn't 'healthy',
      // check individual services for the 'degraded' state.
      const svc = data.services || {};
      const anyServiceHealthy =
        svc.gateway?.status === 'healthy' ||
        svc.redis?.status === 'healthy' ||
        svc.postgres?.status === 'healthy' ||
        svc.qdrant?.status === 'healthy';

      setSystemStatus(anyServiceHealthy ? 'degraded' : 'offline');
    } catch {
      setSystemStatus('offline');
    }
  }, []);

  useEffect(() => {
    // Only check health if not showing setup
    if (!showSetup && isInitialized) {
      checkSystemHealth();
      const interval = setInterval(checkSystemHealth, 30000); // Check every 30 seconds
      return () => clearInterval(interval);
    }
  }, [checkSystemHealth, showSetup, isInitialized]);

  const handleNavClick = useCallback((navId: string) => {
    setCurrentView(navId as View);
  }, []);

  // Handle setup completion
  const handleSetupComplete = useCallback(() => {
    setShowSetup(false);
    // Trigger health check after setup
    setTimeout(checkSystemHealth, 1000);
  }, [checkSystemHealth]);

  // Handle re-running setup from settings
  const handleRerunSetup = useCallback(() => {
    resetSetup();
    setRerunning(true);
    setShowSetup(true);
  }, [resetSetup, setRerunning]);

  const renderView = () => {
    // Tier 3: a real router drives the view via <Routes> below; this
    // function is kept only as a fallback for legacy callers. The
    // router is now the source of truth.
    switch (currentView) {
      case 'agents':
        return <AgentsPage />;
      case 'consciousness':
        return <ConsciousnessPage />;
      case 'autonomous':
        return <AutonomousPage />;
      case 'observability':
        return <ObservabilityPage />;
      case 'chat':
        return <MessageList />;
      case 'memory':
        return <AnalysisHistory />;
      case 'canvas':
        return <EnhancedCanvas />;
      case 'workflows':
        return <WorkflowBuilder />;
      case 'logs':
        return <LogsPage />;
      case 'settings':
        return <SettingsPage onRerunSetup={handleRerunSetup} />;
      default:
        return <NewHomePage />;
    }
  };

  // Tier-1 routes take precedence over the legacy view switcher.
  const location = useLocation();
  const isTier1Route =
    location.pathname === '/' ||
    location.pathname === '/deliberations' ||
    location.pathname.startsWith('/deliberations/');

  const renderTier1 = () => {
    if (location.pathname === '/') return <NewHomePage />;
    if (location.pathname === '/deliberations') return <NewDeliberationListPage />;
    if (location.pathname.startsWith('/deliberations/')) return <NewDeliberationPage />;
    return null;
  };

  // Don't render until we've checked configuration
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {showSetup ? (
        <SetupWizard onComplete={handleSetupComplete} />
      ) : (
        <DashboardLayout
          activeNav={currentView}
          onNavClick={handleNavClick}
          navItems={navItems}
          systemStatus={systemStatus}
        >
          <ErrorBoundary>{isTier1Route ? renderTier1() : renderView()}</ErrorBoundary>
        </DashboardLayout>
      )}
      <CommandPalette
        items={navItems.map<CommandItem>((item) => ({
          id: `nav:${item.id}`,
          label: item.label,
          group: 'Page',
          icon: item.icon,
          keywords: ['navigate', 'go to', item.id],
        }))}
      />
    </>
  );
}

function App() {
  return (
    <ToastProvider>
      <MemoryRouter>
        <DashboardContent />
      </MemoryRouter>
      {/* Debug features - only visible when Developer Mode is enabled */}
      <DebugPanel />
      <PerformanceOverlay position="top-right" />
    </ToastProvider>
  );
}

export default App;
