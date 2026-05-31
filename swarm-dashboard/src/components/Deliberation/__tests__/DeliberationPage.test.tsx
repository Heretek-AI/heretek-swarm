/**
 * DeliberationPage Component Tests
 *
 * Tests tab navigation, live panel rendering, history tab, and
 * WebSocket event-driven state updates.
 *
 * Follows the same mocking strategy as ExternalCallsPanel.test.tsx:
 * a minimal global WebSocket mock whose onmessage we trigger manually.
 */

import { act, waitFor, cleanup } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

// --- Minimal WebSocket mock (must come before module imports that use useWebSocket) ---
const mockWsInstance = {
  onopen: null as (() => void) | null,
  onclose: null as (() => void) | null,
  onmessage: null as ((event: MessageEvent) => void) | null,
  onerror: null as ((event: Event) => void) | null,
  readyState: 1, // OPEN
  close: vi.fn(),
  send: vi.fn(),
};
 
(global as any).WebSocket = vi.fn(() => mockWsInstance);

// --- Mock the API modules to avoid real HTTP calls in history tab ---
vi.mock('../../../api/consensus', () => ({
  getConsensusHistory: vi.fn().mockResolvedValue({
    consensus_history: [],
    total: 0,
  }),
  getConsensusRound: vi.fn().mockResolvedValue({
    id: 'test-round-1',
    topic: 'Test Topic',
    state: 'completed',
    votes: [],
    decision: null,
    confidence: null,
    red_flags: [],
    created_at: '2025-01-01T00:00:00Z',
    completed_at: null,
    metadata: {},
  }),
  getConsensusResults: vi.fn(),
}));

vi.mock('../../../api/deliberation', () => ({
  getAuditStatistics: vi.fn().mockResolvedValue({
    total_decisions: 0,
    successful: 0,
    failed: 0,
    average_confidence: 0,
    average_deliberation_rounds: 0,
  }),
  getSuccessfulAudits: vi.fn().mockResolvedValue({ total_successful: 0, audits: [] }),
  getFailedAudits: vi.fn().mockResolvedValue({ total_failed: 0, audits: [] }),
}));

// --- Import after mocks ---
import { DeliberationPage } from '../DeliberationPage';
import { LiveDeliberationPanel } from '../LiveDeliberationPanel';
import { ToastProvider } from '../../UI/Toast';

// Wrapper that provides ToastProvider context
function renderWithToast(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>);
}

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function feedWsEvent(event: Record<string, unknown>) {
  act(() => {
    const handler = mockWsInstance.onmessage;
    if (handler) {
      handler({ data: JSON.stringify(event) } as MessageEvent);
    }
  });
}

function feedWsEvents(events: Array<Record<string, unknown>>) {
  act(() => {
    const handler = mockWsInstance.onmessage;
    if (handler) {
      events.forEach(evt => {
        handler({ data: JSON.stringify(evt) } as MessageEvent);
      });
    }
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DeliberationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockWsInstance.onmessage = null;
    mockWsInstance.onopen = null;
    mockWsInstance.onclose = null;
    mockWsInstance.onerror = null;
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  // -----------------------------------------------------------------
  // Basic rendering
  // -----------------------------------------------------------------
  describe('render', () => {
    it('should render without crashing', () => {
      expect(() => renderWithToast(<DeliberationPage />)).not.toThrow();
    });

    it('should display the page heading', () => {
      renderWithToast(<DeliberationPage />);
      expect(screen.getByRole('heading', { name: 'Deliberation' })).toBeInTheDocument();
    });

    it('should display the page description', () => {
      renderWithToast(<DeliberationPage />);
      expect(screen.getByText(/Monitor live agent votes/)).toBeInTheDocument();
    });

    it('should render tab navigation with Live and History tabs', () => {
      renderWithToast(<DeliberationPage />);
      expect(screen.getByRole('button', { name: /Live/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /History/ })).toBeInTheDocument();
    });

    it('should have Live tab active by default', () => {
      renderWithToast(<DeliberationPage />);
      const liveTab = screen.getByRole('button', { name: /Live/ });
      expect(liveTab.className).toContain('bg-blue-600');
    });
  });

  // -----------------------------------------------------------------
  // Tab navigation
  // -----------------------------------------------------------------
  describe('tab navigation', () => {
    it('should switch to History tab when clicked', () => {
      renderWithToast(<DeliberationPage />);
      const historyTab = screen.getByRole('button', { name: /History/ });
      fireEvent.click(historyTab);
      expect(historyTab.className).toContain('bg-blue-600');
    });

    it('should switch back to Live tab', () => {
      renderWithToast(<DeliberationPage />);
      const liveTab = screen.getByRole('button', { name: /Live/ });
      const historyTab = screen.getByRole('button', { name: /History/ });

      fireEvent.click(historyTab);
      fireEvent.click(liveTab);
      expect(liveTab.className).toContain('bg-blue-600');
    });

    it('should show Live panel content when Live tab is active', () => {
      renderWithToast(<DeliberationPage />);
      // Live tab is active, so the Live panel shows (with consensus rounds heading)
      expect(screen.getByText('Consensus Rounds')).toBeInTheDocument();
    });

    it('should show History content when History tab is active', async () => {
      renderWithToast(<DeliberationPage />);
      const historyTab = screen.getByRole('button', { name: /History/ });
      fireEvent.click(historyTab);

      // Should show history-related text
      await waitFor(() => {
        expect(screen.getByText(/Past Rounds/)).toBeInTheDocument();
      });
    });
  });
});

describe('LiveDeliberationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockWsInstance.onmessage = null;
    mockWsInstance.onopen = null;
    mockWsInstance.onclose = null;
    mockWsInstance.onerror = null;
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  // -----------------------------------------------------------------
  // Basic rendering
  // -----------------------------------------------------------------
  describe('render', () => {
    it('should render without crashing', () => {
      expect(() => render(<LiveDeliberationPanel />)).not.toThrow();
    });

    it('should show connection status indicator', () => {
      render(<LiveDeliberationPanel />);
      // The status text appears once in the panel
      const statusEls = screen.getAllByText(/Connecting…|Live/);
      expect(statusEls.length).toBeGreaterThan(0);
    });

    it('should show empty state for consensus rounds when no data', () => {
      render(<LiveDeliberationPanel />);
      expect(screen.getByText(/No active consensus rounds/)).toBeInTheDocument();
    });

    it('should show empty state for deliberations when no data', () => {
      render(<LiveDeliberationPanel />);
      expect(screen.getByText(/No active deliberations/)).toBeInTheDocument();
    });

    it('should show event feed placeholder', () => {
      render(<LiveDeliberationPanel />);
      expect(screen.getByText(/Waiting for events/)).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------
  // WebSocket connection lifecycle
  // -----------------------------------------------------------------
  describe('WebSocket lifecycle', () => {
    it('should show "Live" when WebSocket connects', () => {
      render(<LiveDeliberationPanel />);

      act(() => {
        if (mockWsInstance.onopen) mockWsInstance.onopen();
      });

      expect(screen.getByText('Live')).toBeInTheDocument();
    });

    it('should show "Connection error" when WebSocket errors', () => {
      render(<LiveDeliberationPanel />);

      act(() => {
        if (mockWsInstance.onerror) mockWsInstance.onerror(new Event('error'));
      });

      expect(screen.getByText('Connection error')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------
  // Consensus vote events
  // -----------------------------------------------------------------
  describe('consensus vote events', () => {
    it('should display agent name after vote event', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.85,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      // Should show the agent name (may appear in card + feed)
      const agentEls = screen.getAllByText('agent-alpha');
      expect(agentEls.length).toBeGreaterThan(0);
    });

    it('should display vote decision', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.85,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      // Decision appears in both the vote card and the event feed
      const decisionEls = screen.getAllByText('approve');
      expect(decisionEls.length).toBeGreaterThan(0);
    });

    it('should display the consensus state badge', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.85,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      const stateEls = screen.getAllByText('gathering');
      expect(stateEls.length).toBeGreaterThan(0);
    });

    it('should display multiple votes from different agents', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvents([
        {
          type: 'consensus_vote',
          consensus_id: 'round-abc-123',
          agent_id: 'agent-alpha',
          decision: 'approve',
          confidence: 0.85,
          vote_count: 1,
          current_state: 'gathering',
          timestamp: '2025-01-01T12:00:00Z',
        },
        {
          type: 'consensus_vote',
          consensus_id: 'round-abc-123',
          agent_id: 'agent-beta',
          decision: 'reject',
          confidence: 0.6,
          vote_count: 2,
          current_state: 'gathering',
          timestamp: '2025-01-01T12:00:01Z',
        },
      ]);
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getAllByText('agent-alpha').length).toBeGreaterThan(0);
      expect(screen.getAllByText('agent-beta').length).toBeGreaterThan(0);
      expect(screen.getAllByText('approve').length).toBeGreaterThan(0);
      expect(screen.getAllByText('reject').length).toBeGreaterThan(0);
    });

    it('should update vote count display', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.85,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getByText('1 of 4 agents voted')).toBeInTheDocument();

      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-beta',
        decision: 'approve',
        confidence: 0.9,
        vote_count: 2,
        current_state: 'voting',
        timestamp: '2025-01-01T12:00:01Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getByText('2 of 4 agents voted')).toBeInTheDocument();
    });

    it('should show confidence percentages', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.85,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      // 85% appears in both the vote card and the event feed
      const confidenceEls = screen.getAllByText('85%');
      expect(confidenceEls.length).toBeGreaterThan(0);
    });
  });

  // -----------------------------------------------------------------
  // Consensus state change events
  // -----------------------------------------------------------------
  describe('consensus state changes', () => {
    it('should update round state on state change event', () => {
      render(<LiveDeliberationPanel />);

      // First, create a round with a vote
      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.85,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getAllByText('gathering').length).toBeGreaterThan(0);

      // Then change state
      feedWsEvent({
        type: 'consensus_state_change',
        consensus_id: 'round-abc-123',
        old_state: 'gathering',
        new_state: 'voting',
        timestamp: '2025-01-01T12:00:02Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getAllByText('voting').length).toBeGreaterThan(0);
    });
  });

  // -----------------------------------------------------------------
  // Consensus complete events
  // -----------------------------------------------------------------
  describe('consensus completion', () => {
    it('should display completed consensus with decision', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_complete',
        consensus_id: 'round-abc-123',
        decision: 'proceed with deployment',
        confidence: 0.92,
        vote_count: 4,
        red_flags: [],
        timestamp: '2025-01-01T12:05:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getAllByText('proceed with deployment').length).toBeGreaterThan(0);
      expect(screen.getAllByText('completed').length).toBeGreaterThan(0);
    });

    it('should show red flags when present', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_complete',
        consensus_id: 'round-abc-123',
        decision: 'proceed with caution',
        confidence: 0.6,
        vote_count: 4,
        red_flags: ['Low confidence threshold', 'Conflicting opinions'],
        timestamp: '2025-01-01T12:05:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getByText(/2 red flags/)).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------
  // Deliberation events
  // -----------------------------------------------------------------
  describe('deliberation events', () => {
    it('should display deliberation card on round event', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'deliberation_round',
        deliberation_id: 'delib-xyz-789',
        round_number: 1,
        consensus_score: 0.6,
        positions: { support: 2, oppose: 1, neutral: 1 },
        summary: 'Initial positions collected',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getByText('In Progress')).toBeInTheDocument();
      // Consensus score appears in both the deliberation card and the event feed
      expect(screen.getAllByText('60%').length).toBeGreaterThan(0);
      // Round number
      const roundNums = screen.getAllByText('1');
      expect(roundNums.length).toBeGreaterThan(0);
      expect(screen.getByText('Initial positions collected')).toBeInTheDocument();
    });

    it('should display position labels', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'deliberation_round',
        deliberation_id: 'delib-xyz-789',
        round_number: 2,
        consensus_score: 0.75,
        positions: { support: 3, oppose: 1 },
        summary: 'Positions shifting toward support',
        timestamp: '2025-01-01T12:01:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      // Position labels may appear in both the deliberation card legend and event feed
      expect(screen.getAllByText('Support').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Oppose').length).toBeGreaterThan(0);
    });

    it('should show finalized deliberation', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'deliberation_finalized',
        deliberation_id: 'delib-xyz-789',
        final_position: 'support',
        consensus_score: 0.85,
        total_rounds: 3,
        timestamp: '2025-01-01T12:10:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getByText('Finalized')).toBeInTheDocument();
      // "support" appears in multiple places (position label + final position)
      expect(screen.getAllByText('support').length).toBeGreaterThan(0);
    });
  });

  // -----------------------------------------------------------------
  // Event feed
  // -----------------------------------------------------------------
  describe('event feed', () => {
    it('should populate event feed from WebSocket events', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvents([
        {
          type: 'consensus_vote',
          consensus_id: 'round-abc-123',
          agent_id: 'agent-alpha',
          decision: 'approve',
          confidence: 0.85,
          vote_count: 1,
          current_state: 'gathering',
          timestamp: '2025-01-01T12:00:00Z',
        },
        {
          type: 'consensus_state_change',
          consensus_id: 'round-abc-123',
          old_state: 'gathering',
          new_state: 'voting',
          timestamp: '2025-01-01T12:00:02Z',
        },
      ]);
      act(() => { vi.advanceTimersByTime(200); });

      // Event feed should show summaries (may appear in multiple elements)
      expect(screen.getAllByText(/Vote: "approve"/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/gathering → voting/).length).toBeGreaterThan(0);
    });

    it('should display event feed heading', () => {
      render(<LiveDeliberationPanel />);
      // "Event Feed" heading appears in the panel itself
      const headings = screen.getAllByText('Event Feed');
      expect(headings.length).toBeGreaterThan(0);
    });
  });

  // -----------------------------------------------------------------
  // Multiple rounds
  // -----------------------------------------------------------------
  describe('multiple rounds', () => {
    it('should track multiple independent consensus rounds', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvents([
        {
          type: 'consensus_vote',
          consensus_id: 'round-1',
          agent_id: 'agent-alpha',
          decision: 'yes',
          confidence: 0.9,
          vote_count: 1,
          current_state: 'gathering',
          timestamp: '2025-01-01T12:00:00Z',
        },
        {
          type: 'consensus_vote',
          consensus_id: 'round-2',
          agent_id: 'agent-beta',
          decision: 'no',
          confidence: 0.7,
          vote_count: 1,
          current_state: 'gathering',
          timestamp: '2025-01-01T12:00:01Z',
        },
      ]);
      act(() => { vi.advanceTimersByTime(200); });

      // Should show both agents from different rounds
      expect(screen.getAllByText('agent-alpha').length).toBeGreaterThan(0);
      expect(screen.getAllByText('agent-beta').length).toBeGreaterThan(0);
      expect(screen.getAllByText('yes').length).toBeGreaterThan(0);
      expect(screen.getAllByText('no').length).toBeGreaterThan(0);
    });
  });

  // -----------------------------------------------------------------
  // Summary metrics
  // -----------------------------------------------------------------
  describe('summary metrics', () => {
    it('should show summary metrics when data is present', () => {
      render(<LiveDeliberationPanel />);

      feedWsEvent({
        type: 'consensus_vote',
        consensus_id: 'round-abc-123',
        agent_id: 'agent-alpha',
        decision: 'approve',
        confidence: 0.85,
        vote_count: 1,
        current_state: 'gathering',
        timestamp: '2025-01-01T12:00:00Z',
      });
      act(() => { vi.advanceTimersByTime(200); });

      expect(screen.getAllByText('Active Rounds').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Total Votes').length).toBeGreaterThan(0);
    });
  });
});
