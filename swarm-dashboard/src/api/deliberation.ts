/**
 * API Client - Deliberation endpoints
 *
 * Provides typed functions for interacting with the deliberation API:
 * - Starting and managing deliberation processes
 * - Submitting positions, arguments, and evidence
 * - Running deliberation rounds
 * - Retrieving deliberation state and history
 * - Finalizing deliberations
 * - Audit trail access
 */

import { api } from './client';

// =============================================================================
// Types
// =============================================================================

/** Position a participant can take in deliberation */
export type DeliberationPosition = 'support' | 'oppose' | 'neutral' | 'modify';

/** Deliberation lifecycle state */
export type DeliberationState =
  | 'initiated'
  | 'in_progress'
  | 'concluded'
  | 'finalized'
  | 'failed';

/** An argument submitted during deliberation */
export interface DeliberationArgument {
  argument_id: string;
  agent_id: string;
  position: DeliberationPosition;
  reasoning: string;
  evidence_refs: string[];
  confidence: number;
  timestamp: string;
}

/** Evidence submitted to support an argument */
export interface DeliberationEvidence {
  evidence_id: string;
  argument_id: string;
  content: string;
  source: string | null;
  quality_score: number;
}

/** Round result after running a deliberation round */
export interface DeliberationRoundResult {
  deliberation_id: string;
  round_number: number;
  arguments_submitted: number;
  positions: Record<DeliberationPosition, number>;
  consensus_score: number;
  summary: string;
  timestamp: string;
}

/** Deliberation state snapshot (from GET .../state) */
export interface DeliberationStateResponse {
  deliberation_id: string;
  state: DeliberationState;
  proposal: string;
  topic: string | null;
  participants: string[];
  current_round: number;
  max_rounds: number;
  consensus_score: number;
  position_distribution: Record<string, number>;
}

/** Final deliberation result after finalization */
export interface DeliberationFinalResult {
  deliberation_id: string;
  final_position: DeliberationPosition;
  consensus_score: number;
  total_rounds: number;
  total_arguments: number;
  total_participants: number;
  minority_report: string | null;
  summary: string;
  timestamp: string;
}

/** Audit decision record */
export interface AuditDecisionRecord {
  decision_id: string;
  consensus_id: string;
  topic: string;
  decision: string;
  confidence: number;
  votes: Array<{
    agent_id: string;
    decision: string;
    confidence: number;
  }>;
  deliberation_rounds: number;
  timestamp: string;
}

/** Audit statistics */
export interface AuditStatistics {
  total_decisions: number;
  successful: number;
  failed: number;
  average_confidence: number;
  average_deliberation_rounds: number;
}

// =============================================================================
// API Functions — Deliberation Management
// =============================================================================

/**
 * Start a new deliberation process.
 *
 * Calls POST /api/consensus/deliberation/start.
 */
export async function startDeliberation(
  proposal: string,
  participants: string[],
  options?: {
    topic?: string;
    maxRounds?: number;
    timeoutMinutes?: number;
  }
): Promise<{
  deliberation_id: string;
  proposal: string;
  topic: string | null;
  participants: string[];
  max_rounds: number;
  timeout_minutes: number;
  state: string;
}> {
  const response = await api.post<{
    deliberation_id: string;
    proposal: string;
    topic: string | null;
    participants: string[];
    max_rounds: number;
    timeout_minutes: number;
    state: string;
  }>('/api/consensus/deliberation/start', {
    proposal,
    participants,
    topic: options?.topic,
    max_rounds: options?.maxRounds ?? 5,
    timeout_minutes: options?.timeoutMinutes ?? 30,
  });
  return response.data;
}

/**
 * Submit a position in a deliberation.
 *
 * Calls POST /api/consensus/deliberation/:deliberationId/submit_position.
 */
export async function submitDeliberationPosition(
  deliberationId: string,
  position: DeliberationPosition,
  confidence: number = 0.5,
  reasoning?: string
): Promise<{
  deliberation_id: string;
  agent_id: string;
  position: DeliberationPosition;
  confidence: number;
  submitted: boolean;
}> {
  const response = await api.post<{
    deliberation_id: string;
    agent_id: string;
    position: DeliberationPosition;
    confidence: number;
    submitted: boolean;
  }>(
    `/api/consensus/deliberation/${deliberationId}/submit_position`,
    { position, confidence, reasoning }
  );
  return response.data;
}

/**
 * Submit an argument in a deliberation.
 *
 * Calls POST /api/consensus/deliberation/:deliberationId/submit_argument.
 */
export async function submitDeliberationArgument(
  deliberationId: string,
  position: DeliberationPosition,
  reasoning: string,
  evidenceRefs?: string[],
  confidence: number = 0.5
): Promise<{
  argument_id: string;
  deliberation_id: string;
  agent_id: string;
  position: DeliberationPosition;
  reasoning: string;
  evidence_refs: string[];
}> {
  const response = await api.post<{
    argument_id: string;
    deliberation_id: string;
    agent_id: string;
    position: DeliberationPosition;
    reasoning: string;
    evidence_refs: string[];
  }>(
    `/api/consensus/deliberation/${deliberationId}/submit_argument`,
    { position, reasoning, evidence_refs: evidenceRefs, confidence }
  );
  return response.data;
}

/**
 * Submit evidence for an argument.
 *
 * Calls POST /api/consensus/deliberation/:deliberationId/submit_evidence.
 */
export async function submitDeliberationEvidence(
  deliberationId: string,
  argumentId: string,
  content: string,
  source?: string,
  qualityScore: number = 0.5
): Promise<{
  evidence_id: string;
  argument_id: string;
  deliberation_id: string;
  content_length: number;
  quality_score: number;
}> {
  const response = await api.post<{
    evidence_id: string;
    argument_id: string;
    deliberation_id: string;
    content_length: number;
    quality_score: number;
  }>(
    `/api/consensus/deliberation/${deliberationId}/submit_evidence`,
    { argument_id: argumentId, content, source, quality_score: qualityScore }
  );
  return response.data;
}

/**
 * Run a single deliberation round.
 *
 * Calls POST /api/consensus/deliberation/:deliberationId/run_round.
 */
export async function runDeliberationRound(
  deliberationId: string
): Promise<DeliberationRoundResult> {
  const response = await api.post<DeliberationRoundResult>(
    `/api/consensus/deliberation/${deliberationId}/run_round`
  );
  return response.data;
}

/**
 * Get current deliberation state.
 *
 * Calls GET /api/consensus/deliberation/:deliberationId/state.
 */
export async function getDeliberationState(
  deliberationId: string
): Promise<DeliberationStateResponse> {
  const response = await api.get<DeliberationStateResponse>(
    `/api/consensus/deliberation/${deliberationId}/state`
  );
  return response.data;
}

/**
 * Get deliberation round history.
 *
 * Calls GET /api/consensus/deliberation/:deliberationId/history.
 */
export async function getDeliberationHistory(
  deliberationId: string,
  limit: number = 10
): Promise<{ deliberation_id: string; rounds: DeliberationRoundResult[] }> {
  const response = await api.get<{
    deliberation_id: string;
    rounds: DeliberationRoundResult[];
  }>(`/api/consensus/deliberation/${deliberationId}/history?limit=${limit}`);
  return response.data;
}

/**
 * Finalize a deliberation and return results.
 *
 * Calls POST /api/consensus/deliberation/:deliberationId/finalize.
 */
export async function finalizeDeliberation(
  deliberationId: string
): Promise<DeliberationFinalResult> {
  const response = await api.post<DeliberationFinalResult>(
    `/api/consensus/deliberation/${deliberationId}/finalize`
  );
  return response.data;
}

/**
 * Cleanup and remove a deliberation.
 *
 * Calls DELETE /api/consensus/deliberation/:deliberationId.
 */
export async function cleanupDeliberation(
  deliberationId: string
): Promise<{ deliberation_id: string; cleaned_up: boolean }> {
  const response = await api.delete<{
    deliberation_id: string;
    cleaned_up: boolean;
  }>(
    `/api/consensus/deliberation/${deliberationId}`
  );
  return response.data;
}

// =============================================================================
// API Functions — Audit Trail
// =============================================================================

/**
 * Get comprehensive decision audit record.
 *
 * Calls GET /api/consensus/audit/decision/:decisionId.
 */
export async function getDecisionAudit(
  decisionId: string
): Promise<AuditDecisionRecord> {
  const response = await api.get<AuditDecisionRecord>(
    `/api/consensus/audit/decision/${decisionId}`
  );
  return response.data;
}

/**
 * Export decision audit record as JSON.
 *
 * Calls GET /api/consensus/audit/decision/:decisionId/export.
 */
export async function exportDecisionAudit(
  decisionId: string
): Promise<{ decision_id: string; export_format: string; data: unknown }> {
  const response = await api.get<{
    decision_id: string;
    export_format: string;
    data: unknown;
  }>(
    `/api/consensus/audit/decision/${decisionId}/export`
  );
  return response.data;
}

/**
 * Verify integrity of decision audit record.
 *
 * Calls GET /api/consensus/audit/decision/:decisionId/verify.
 */
export async function verifyDecisionAudit(
  decisionId: string
): Promise<{ decision_id: string; valid: boolean; error?: string }> {
  const response = await api.get<{
    decision_id: string;
    valid: boolean;
    error?: string;
  }>(
    `/api/consensus/audit/decision/${decisionId}/verify`
  );
  return response.data;
}

/**
 * Get audit trail statistics.
 *
 * Calls GET /api/consensus/audit/statistics.
 */
export async function getAuditStatistics(): Promise<AuditStatistics> {
  const response = await api.get<AuditStatistics>(
    '/api/consensus/audit/statistics'
  );
  return response.data;
}

/**
 * Get all failed decision audits.
 *
 * Calls GET /api/consensus/audit/failed.
 */
export async function getFailedAudits(): Promise<{
  total_failed: number;
  audits: AuditDecisionRecord[];
}> {
  const response = await api.get<{
    total_failed: number;
    audits: AuditDecisionRecord[];
  }>('/api/consensus/audit/failed');
  return response.data;
}

/**
 * Get all successful decision audits.
 *
 * Calls GET /api/consensus/audit/successful.
 */
export async function getSuccessfulAudits(): Promise<{
  total_successful: number;
  audits: AuditDecisionRecord[];
}> {
  const response = await api.get<{
    total_successful: number;
    audits: AuditDecisionRecord[];
  }>('/api/consensus/audit/successful');
  return response.data;
}
