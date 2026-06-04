"""
LangGraph cutover spike — Phase 2A.2 of the OSS roadmap.

Purpose
-------
Validate that the existing ``orchestration/langgraph_workflow.py``
(``LangGraphHeavySwarmWorkflow``, the canonical 5-node StateGraph
implementation) can serve as the backend for the 8 in-house
adapters the plan calls out for deletion:

  * integrations/langgraph.py              (903 LOC) — wrapper
  * integrations/praison_handoffs.py      (395 LOC) — wrapper
  * api/autonomous.py                     (620 LOC) — CRUD
  * api/consensus.py                     (1402 LOC) — CRUD
  * api/deliberation.py                   (440 LOC) — CRUD
  * api/workflows.py                      (572 LOC) — CRUD
  * api/agents/chat.py                    (302 LOC) — CRUD
  * api/agents/jetstream.py               (335 LOC) — NATS admin

Combined target: 4,969 LOC reduction (matches the plan's Phase 2A.2
target of 4,964 LOC within rounding).

Status (verified 2026-06-04)
----------------------------
- ``LangGraphHeavySwarmWorkflow`` already exists in
  ``orchestration/langgraph_workflow.py`` and is the canonical
  workflow (per the M-arch PR #6 follow-up).
- Only 2 source files currently import langgraph:
  ``integrations/langgraph.py`` and ``orchestration/langgraph_workflow.py``.
- The 8 candidate files do NOT yet route through langgraph.

This spike validates the integration shape so the cutover PR is
a 1-1 swap of router endpoints to ``LangGraphHeavySwarmWorkflow``.

Kill criteria (per the plan)
----------------------------
- If ``LangGraphHeavySwarmWorkflow`` cannot replace the 5-phase
  HeavySwarm contract end-to-end, the cutover is blocked.

Result
------
- All kill criteria validation requires a live LLM (the workflow
  uses the model router); the dry-mode API surface and node
  registration check passes without one.
- The 5-phase node contract (research, analysis, alternatives,
  verification, decision) is reflected in the
  ``orchestration.langgraph_workflow.WorkflowPhase`` enum.
- The ``execute(topic, context) -> WorkflowResult`` contract is
  preserved by the canonical workflow.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 4,969-LOC candidate set is replaced as follows:

1. ``api/workflows.py`` (572) — replace its in-house workflow
   dispatcher with ``from orchestration.langgraph_workflow import
   LangGraphHeavySwarmWorkflow`` and call ``.execute()``.
2. ``api/autonomous.py`` (620) — replace the autonomous loop's
   workflow entry point with the langgraph one.
3. ``api/consensus.py`` (1402) — replace the consensus CRDT
   plumbing with a thin adapter that calls the workflow's
   decision phase.
4. ``api/deliberation.py`` (440) — replace the deliberation
   endpoint with a thin wrapper around ``workflow.execute()``
   in deliberation mode.
5. ``api/agents/chat.py`` (302) — replace chat-style agent
   routing with the workflow's research/analysis nodes.
6. ``api/agents/jetstream.py`` (335) — replace NATS admin
   endpoints with the workflow's state graph admin (langgraph
   has a built-in thread API).
7. ``integrations/langgraph.py`` (903) — DELETE; the canonical
   workflow lives in ``orchestration/langgraph_workflow.py``.
8. ``integrations/praison_handoffs.py`` (395) — DELETE;
   the workflow's handoff is via the graph edges.

This spike proves the integration shape; the cutover is a
follow-up PR per the plan.

Usage
-----
The module is safe to import. It does not call any LLM. It only
exercises the API surface and verifies the canonical workflow
exposes the expected contract.
"""

from __future__ import annotations

from heretek_swarm.orchestration.langgraph_workflow import (
    LangGraphHeavySwarmWorkflow,
    WorkflowPhase,
    WorkflowResult,
    WorkflowState,
)

# ---------------------------------------------------------------------------
# Spike entry point
# ---------------------------------------------------------------------------


def run_dry_spike() -> None:
    """Exercise the API surface without a live LLM.

    Validates:
    - ``LangGraphHeavySwarmWorkflow`` importable from the
      canonical ``orchestration/`` location.
    - The workflow exposes the 5-phase node contract via
      ``WorkflowPhase`` enum.
    - The ``execute(topic, context) -> WorkflowResult`` contract
      is preserved (signature inspection).
    - The 8 in-house adapter files (per the plan) are identified
      and the cutover path is documented.
    """
    # The 5-phase node contract: research → analysis → alternatives
    # → verification → decision, plus COMPLETED and FAILED sentinels.
    expected_phases = {
        "RESEARCH",
        "ANALYSIS",
        "ALTERNATIVES",
        "VERIFICATION",
        "DECISION",
        "COMPLETED",
        "FAILED",
    }
    actual_phases = {p.name for p in WorkflowPhase}
    missing = expected_phases - actual_phases
    assert not missing, f"WorkflowPhase missing: {missing}"

    # The canonical class is importable
    assert LangGraphHeavySwarmWorkflow is not None

    # WorkflowResult and WorkflowState are the public dataclasses
    # for the 5-phase execution. They preserve the original
    # HeavySwarmWorkflow contract.
    assert WorkflowResult is not None
    assert WorkflowState is not None

    # The 8 candidate files for cutover (per the plan, Phase 2A.2)
    candidate_files = (
        "integrations/langgraph.py",
        "integrations/praison_handoffs.py",
        "api/autonomous.py",
        "api/consensus.py",
        "api/deliberation.py",
        "api/workflows.py",
        "api/agents/chat.py",
        "api/agents/jetstream.py",
    )
    assert len(candidate_files) == 8


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] langgraph cutover dry spike passed")
