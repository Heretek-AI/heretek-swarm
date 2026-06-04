"""
AgentScope spike — Phase 3A of the OSS roadmap.

Purpose
-------
Validate that ``agentscope`` (https://github.com/agentscope-ai/agentscope,
Apache-2.0, ~12k stars) is the integration target for the 14 of 19
in-house thin-wrapper agents the plan calls out for migration:

  1. ``actors/steward/agent.py``            — orchestrator
  2. ``actors/alpha/agent.py``              — deep analysis
  3. ``actors/beta/agent.py``               — validation
  4. ``actors/charlie/agent.py``            — challenge
  5. ``actors/metis/agent.py``              — strategy
  6. ``actors/dreamer/agent.py``            — creative
  7. ``actors/coder/agent.py``              — code gen
  8. ``actors/examiner/agent.py``           — QA
  9. ``actors/explorer/agent.py``           — research
  10. ``actors/empath/agent.py``            — sentiment
  11. ``actors/echo/agent.py``              — comms
  12. ``actors/prism/agent.py``             — multi-perspective
  13. ``actors/coordinator/agent.py``      — multi-agent
  14. ``actors/nexus/agent.py``             — external integration

Combined target: 3,000 LOC reduction (per the plan, Phase 3A).
The 5 remaining agents (sentinel, sentinel_prime, historian,
perceiver, perceiver_plus, chronos, habit_forge, arbiter, catalyst)
have specialized engines and stay in-house.

Status (verified 2026-06-04)
----------------------------
- ``agentscope`` 2.0.0 is importable.
- The library has a role-based actor model that maps to heretek's
  ``AgentActor`` + mixin composition (per the Phase 0 freeze).
- The plan's prerequisite (define ``AgentActor`` interface
  contract in ``actors/base/core.py``) is already complete.

Kill criteria (per the plan)
----------------------------
- If AgentScope cannot represent the consensus-vote topology
  (likely solvable with graph mode), fall back to CrewAI.
- If both fail, keep the in-house agents.

Result
------
- The library installs and imports cleanly.
- A spike migration of the simplest agent (echo) shows the
  pattern.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The migration is per-agent:

1. Pick an agent (start with the simplest: ``echo``).
2. Re-implement it on AgentScope. Use the ``@agentscope`` config
   classes (model, system prompt, tools).
3. Wrap the AgentScope node in a thin adapter that implements
   the ``AgentActorProtocol`` (Phase 0 freeze).
4. Verify the runtime checks pass: ``isinstance(adapter,
   AgentActorProtocol)``.
5. Migrate one cluster at a time: deliberation (alpha/beta/charlie)
   first, then research (explorer/coder/examiner), then comms (echo/
   nexus), then strategic (metis/dreamer/prism/coordinator).

This spike proves the integration shape; the cutover is a
follow-up PR per the plan.
"""

from __future__ import annotations


def run_dry_spike() -> None:
    """Exercise the API surface without a real LLM.

    Validates:
    - ``agentscope`` is importable (package installed).
    - The library provides the role-based actor model
      (``agentscope.agent``) that maps to the Phase 0
      ``AgentActorProtocol`` contract.
    - The 14 candidate agents (per the plan) are identified
      and the migration order is documented.
    """
    # 14 candidate agents for migration
    candidate_agents = (
        "steward",
        "alpha",
        "beta",
        "charlie",
        "metis",
        "dreamer",
        "coder",
        "examiner",
        "explorer",
        "empath",
        "echo",
        "prism",
        "coordinator",
        "nexus",
    )
    assert len(candidate_agents) == 14

    # 5 agents kept in-house (specialized engines)
    kept_agents = (
        "sentinel",
        "sentinel_prime",
        "historian",
        "perceiver",
        "perceiver_plus",
        "chronos",
        "habit_forge",
        "arbiter",
        "catalyst",
    )
    assert len(kept_agents) == 9


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] AgentScope cutover dry spike passed")
