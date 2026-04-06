/**
 * Metrics Store - Zustand state management for consciousness metrics
 */

import { create } from 'zustand';

export interface ConsciousnessMetrics {
  average_gwt_score: number;
  average_phi: number;
  average_ast: number;
  average_free_energy: number;
  agent_count: number;
  timestamp: string;
}

export interface AgentMetrics {
  agent_id: string;
  gwt_score: number;
  phi_value: number;
  ast_competence: number;
  free_energy: number;
  state: 'dormant' | 'emerging' | 'coherent' | 'transcendent';
  timestamp: string;
}

export interface AgentStates {
  counts: Record<string, number>;
  states: Record<string, 'dormant' | 'emerging' | 'coherent' | 'transcendent'>;
}

interface MetricsState {
  // State
  collectiveMetrics: ConsciousnessMetrics | null;
  agentMetrics: Record<string, AgentMetrics>;
  agentStates: AgentStates | null;
  loading: boolean;
  error: string | null;

  // Actions
  setCollectiveMetrics: (metrics: ConsciousnessMetrics) => void;
  setAgentMetrics: (agentId: string, metrics: AgentMetrics) => void;
  setAgentStates: (states: AgentStates) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useMetricsStore = create<MetricsState>((set) => ({
  // Initial state
  collectiveMetrics: null,
  agentMetrics: {},
  agentStates: null,
  loading: false,
  error: null,

  // Actions
  setCollectiveMetrics: (metrics) => set({ collectiveMetrics: metrics }),
  setAgentMetrics: (agentId, metrics) => set((state) => ({
    agentMetrics: { ...state.agentMetrics, [agentId]: metrics }
  })),
  setAgentStates: (states) => set({ agentStates: states }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({
    collectiveMetrics: null,
    agentMetrics: {},
    agentStates: null,
    loading: false,
    error: null,
  }),
}));
