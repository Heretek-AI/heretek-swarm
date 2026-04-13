/**
 * Heretek Swarm Dashboard - Main Application
 * 
 * Central control panel for deploying, monitoring, and configuring
 * the Heretek Swarm application.
 */

import { useState, useEffect, useCallback } from 'react';
import { DashboardLayout, NavItem } from './components/Dashboard/Layout';
import { HomePage } from './components/Home/HomePage';
import { AgentsPage } from './components/Agents/AgentsPage';
import { ConsciousnessPage } from './components/Consciousness/ConsciousnessPage';
import { SettingsPage } from './components/Settings/SettingsPage';
import { LogsPage } from './components/Logs/LogsPage';
import { ToastProvider, useToast } from './components/UI/Toast';
import { ErrorBoundary } from './components/UI/ErrorBoundary';
import { DebugPanel } from './components/UI/DebugPanel';
import { PerformanceOverlay } from './components/UI/PerformanceOverlay';
import { SetupWizard } from './components/Setup';
import { useSetupStore } from './stores/setupStore';
import { setToastInstance } from './api/client';

// Legacy components (keep for compatibility)
import { Dashboard } from './components/Dashboard/Dashboard';
import { CollectiveCanvas } from './components/Canvas/Canvas';
import { WorkflowBuilder } from './components/WorkflowBuilder/WorkflowBuilder';
import { Observability } from './components/Observability/Observability';
import { ChatInterface } from './components/Chat/ChatInterface';

type View = 
  | 'home' 
  | 'agents' 
  | 'consciousness' 
  | 'workflows' 
  | 'logs' 
  | 'settings'
  | 'legacy-dashboard'
  | 'legacy-canvas'
  | 'legacy-observability'
  | 'legacy-chat';

const navItems: NavItem[] = [
  { id: 'home', label: 'Home', icon: '🏠' },
  { id: 'agents', label: 'Agents', icon: '🤖' },
  { id: 'consciousness', label: 'Consciousness', icon: '🧠' },
  { id: 'workflows', label: 'Workflows', icon: '🔀' },
  { id: 'logs', label: 'Terminal/Logs', icon: '📟' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

function DashboardContent() {
  const [currentView, setCurrentView] = useState<View>('home');
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded' | 'offline'>('healthy');
  const toast = useToast();
  
  // Setup store integration
  const { 
    isConfigured, 
    isRerunning,
    config,
    setRerunning,
    resetSetup,
  } = useSetupStore();
  
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
          localStorage.setItem('api_key', envApiKey);
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
            apiKey: localStorage.getItem('api_key') || '',
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
      const apiHost = localStorage.getItem('swarm_api_host') || import.meta.env.VITE_API_URL || '';
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
      
      const isHealthy = 
        data.gateway?.status === 'healthy' &&
        data.redis?.status === 'healthy' &&
        data.postgres?.status === 'healthy' &&
        data.qdrant?.status === 'healthy';
      
      const isDegraded = 
        data.gateway?.status === 'healthy' ||
        data.redis?.status === 'healthy' ||
        data.postgres?.status === 'healthy' ||
        data.qdrant?.status === 'healthy';
      
      setSystemStatus(isHealthy ? 'healthy' : isDegraded ? 'degraded' : 'offline');
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
    switch (currentView) {
      case 'home':
        return <HomePage />;
      case 'agents':
        return <AgentsPage />;
      case 'consciousness':
        return <ConsciousnessPage />;
      case 'workflows':
        return <WorkflowBuilder />;
      case 'logs':
        return <LogsPage />;
      case 'settings':
        return <SettingsPage onRerunSetup={handleRerunSetup} />;
      // Legacy views
      case 'legacy-dashboard':
        return <Dashboard />;
      case 'legacy-canvas':
        return <CollectiveCanvas />;
      case 'legacy-observability':
        return <Observability />;
      case 'legacy-chat':
        return <ChatInterface />;
      default:
        return <HomePage />;
    }
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
          <ErrorBoundary>
            {renderView()}
          </ErrorBoundary>
        </DashboardLayout>
      )}
    </>
  );
}

function App() {
  return (
    <ToastProvider>
      <DashboardContent />
      {/* Debug features - only visible when Developer Mode is enabled */}
      <DebugPanel />
      <PerformanceOverlay position="top-right" />
    </ToastProvider>
  );
}

export default App;
