/**
 * Heretek Swarm Dashboard - Main Application
 */

import { useState } from 'react';
import { CollectiveCanvas } from './components/Canvas/Canvas';
import { Dashboard } from './components/Dashboard/Dashboard';
import { Observability } from './components/Observability/Observability';
import { ChatInterface } from './components/Chat/ChatInterface';
import { ConsciousnessDashboard } from './components/Consciousness';
import { WorkflowBuilder } from './components/WorkflowBuilder/WorkflowBuilder';

type View = 'canvas' | 'dashboard' | 'observability' | 'chat' | 'consciousness' | 'workflow';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const navItems: { id: View; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'canvas', label: 'Canvas', icon: '🎨' },
    { id: 'workflow', label: 'Workflow Builder', icon: '🔀' },
    { id: 'observability', label: 'Observability', icon: '🔍' },
    { id: 'consciousness', label: 'Consciousness', icon: '🧠' },
    { id: 'chat', label: 'Chat', icon: '💬' },
  ];

  return (
    <div className="App min-h-screen bg-gray-900 text-white">
      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🤖</span>
              <span className="font-bold text-xl">Heretek Swarm</span>
            </div>
            <div className="flex space-x-1">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentView === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <span className="mr-1">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        {currentView === 'canvas' && <CollectiveCanvas />}
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'observability' && <Observability />}
        {currentView === 'chat' && <ChatInterface />}
        {currentView === 'consciousness' && <ConsciousnessDashboard />}
        {currentView === 'workflow' && <WorkflowBuilder />}
      </main>
    </div>
  );
}

export default App;
