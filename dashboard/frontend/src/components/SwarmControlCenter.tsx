/**
 * SwarmControlCenter
 * 
 * Main integrated dashboard for the Beta Agent (Frontend).
 * Combines FlowCanvas, A2ATracker, and ModelGarage into a unified interface.
 */

import React, { useState, useCallback } from 'react';
import { FlowCanvas } from '../Canvas/FlowCanvas';
import { A2ATracker } from '../Observability/A2ATracker';
import { ModelGarage } from '../Settings/ModelGarage';

type View = 'canvas' | 'tracker' | 'garage' | 'all';

interface SwarmControlCenterProps {
  defaultView?: View;
  natsUrl?: string;
  apiUrl?: string;
}

/**
 * SwarmControlCenter - Integrated dashboard for Heretek Swarm
 */
export function SwarmControlCenter({
  defaultView = 'all',
  natsUrl = 'nats://localhost:4222',
  apiUrl = 'http://localhost:8000',
}: SwarmControlCenterProps) {
  const [activeView, setActiveView] = useState<View>(defaultView);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Heretek Swarm Control Center
            </h1>
            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
              Beta Agent v2.1.0
            </span>
          </div>
          
          {/* View Tabs */}
          <nav className="flex items-center gap-2">
            <button
              onClick={() => setActiveView('canvas')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeView === 'canvas'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              🎨 Flow Canvas
            </button>
            <button
              onClick={() => setActiveView('tracker')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeView === 'tracker'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              📡 A2A Tracker
            </button>
            <button
              onClick={() => setActiveView('garage')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeView === 'garage'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              🤖 Model Garage
            </button>
            <button
              onClick={() => setActiveView('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeView === 'all'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              📊 All Views
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {activeView === 'canvas' && (
          <div className="h-[calc(100vh-140px)]">
            <FlowCanvas />
          </div>
        )}

        {activeView === 'tracker' && (
          <div className="h-[calc(100vh-140px)]">
            <A2ATracker natsUrl={natsUrl} />
          </div>
        )}

        {activeView === 'garage' && (
          <div className="h-[calc(100vh-140px)] overflow-auto">
            <ModelGarage />
          </div>
        )}

        {activeView === 'all' && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Flow Canvas - Full Width */}
            <div className="xl:col-span-2 h-[500px]">
              <div className="h-full bg-gray-900 rounded-lg border border-gray-700">
                <FlowCanvas />
              </div>
            </div>

            {/* A2A Tracker */}
            <div className="h-[450px]">
              <A2ATracker natsUrl={natsUrl} />
            </div>

            {/* Model Garage */}
            <div className="h-[450px] overflow-auto">
              <ModelGarage />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-6 py-2">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-4">
            <span>Agents: <span className="text-green-400">23</span></span>
            <span>Triads: <span className="text-blue-400">3</span></span>
            <span>Phase: <span className="text-purple-400">4 - A2A NATS</span></span>
          </div>
          <div className="flex items-center gap-4">
            <span>NATS: <span className="text-green-400">Connected</span></span>
            <span>API: <span className="text-green-400">Healthy</span></span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default SwarmControlCenter;
