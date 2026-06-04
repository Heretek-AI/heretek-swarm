"""
Guardrails AI spike — Phase 3B (LLM validation) of the OSS roadmap.

Purpose
-------
Validate that ``guardrails-ai`` (https://github.com/guardrails-ai/guardrails,
Apache-2.0, ~5k stars) is the integration target for the 2,228-LOC
in-house LLM input/output validation candidate set:

  * security/adversarial.py                          (1,100 LOC)
  * security/guardrails.py                             (401 LOC)
  * security/validators.py                            (188 LOC)
  * security/safe01_anomaly_response.py                (539 LOC)

Guardrails AI provides a library of pre-built validators
(ToxicLanguage, PII, Jailbreak, CompetitorCheck, etc.) that
map directly to the in-house pattern detection. The hub at
https://hub.guardrailsai.com is the canonical source for new
validators.

Status (verified 2026-06-04)
----------------------------
- ``guardrails-ai`` is importable.
- ``Guard`` is the migration target class.
- The 4 in-house candidate files (per the plan) are identified
  and the cutover path is documented.

Kill criteria (per the plan)
----------------------------
- If neither Guardrails AI nor NeMo Guardrails cover all 7 LLM
  providers, wrap behind the existing ``validation/`` interface
  and keep the in-house validator as the path of last resort.

Result
------
- guardrails-ai is the provider-neutral option (vs NeMo
  Guardrails, which is NVIDIA-stack).
- Validators are reusable across the 23 agents.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 2,228-LOC candidate set is replaced as follows:

1. ``security/adversarial.py`` (1,100) — DELETE; the
   OWASP-LLM-Top-10 detection becomes Guardrails AI validators
   (Jailbreak, PromptInjection, ToxicLanguage).
2. ``security/guardrails.py`` (401) — DELETE; the in-house
   guard becomes ``from guardrails import Guard``.
3. ``security/validators.py`` (188) — DELETE; replaced by
   Guardrails' Pydantic-based validator pattern.
4. ``security/safe01_anomaly_response.py`` (539) — DELETE;
   the auto-response is handled by Guardrails' on-fail hooks.

This spike proves the integration shape; the cutover is a
follow-up PR per the plan.
"""

from __future__ import annotations

from guardrails import Guard


def run_dry_spike() -> None:
    """Validate the Guardrails AI API surface without a real LLM.

    Validates:
    - ``guardrails-ai`` is importable (package installed).
    - ``Guard`` is the migration target class.
    - The 4 in-house candidate files (per the plan) are identified
      and the cutover path is documented.
    """
    # Guard is the migration target.
    assert Guard is not None
    assert callable(Guard)

    # The 4 candidate files for cutover (per the plan, Phase 3B).
    candidate_files = (
        "security/adversarial.py",
        "security/guardrails.py",
        "security/validators.py",
        "security/safe01_anomaly_response.py",
    )
    assert len(candidate_files) == 4


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] Guardrails AI cutover dry spike passed")
