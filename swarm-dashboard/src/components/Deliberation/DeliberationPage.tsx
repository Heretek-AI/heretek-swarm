/**
 * Deliberation Page
 *
 * Dashboard page with tab navigation for viewing live deliberation voting
 * and browsing historical deliberations with full audit trails.
 */

import React, { useState } from 'react';
import { LiveDeliberationPanel } from './LiveDeliberationPanel';
import { HistoricalDeliberations } from './HistoricalDeliberations';

// =============================================================================
// Tab navigation
// =============================================================================

type TabId = 'live' | 'history';

interface Tab {
  id: TabId;
  label: string;
  icon: string;
}

const TABS: Tab[] = [
  { id: 'live', label: 'Live', icon: '🔴' },
  { id: 'history', label: 'History', icon: '📜' },
];

// =============================================================================
// Main Deliberation Page
// =============================================================================

export function DeliberationPage() {
  const [activeTab, setActiveTab] = useState<TabId>('live');

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Deliberation</h1>
          <p className="text-gray-400 text-sm mt-1">
            Monitor live agent votes and browse past deliberation audit trails
          </p>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex items-center gap-1 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-1 w-fit">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'live' && <LiveDeliberationPanel />}
      {activeTab === 'history' && <HistoricalDeliberations />}
    </div>
  );
}

export default DeliberationPage;
