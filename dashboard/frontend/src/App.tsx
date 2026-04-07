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

  // Set toast instance for API client
  useEffect(() => {
    setToastInstance({
      error: (title, message) => toast.error(title, message),
    });
  }, [toast]);

  // Check system health periodically
  const checkSystemHealth = useCallback(async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${API_URL}/api/health`);
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
    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [checkSystemHealth]);

  const handleNavClick = useCallback((navId: string) => {
    setCurrentView(navId as View);
  }, []);

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
        return <SettingsPage />;
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

  return (
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
