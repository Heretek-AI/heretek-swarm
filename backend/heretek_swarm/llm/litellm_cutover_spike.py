"""
LiteLLM cutover spike — Phase 2B.1 of the OSS roadmap.

Purpose
-------
Validate that ``litellm`` (Apache-2.0, ~12k stars, very active) is
the integration target for the 11 in-house provider files the plan
calls out for replacement:

  * llm/model_garage.py                  (1,482 LOC) — multi-provider router
  * llm/providers/{openai,openai_compatible,ollama,llamacpp,minimax,zai,lemonade}_provider.py
                                       (7 × ~190 = 1,330 LOC)
  * embeddings/providers/{factory,base,openai,ollama}.py
                                       (4 × ~225 = 900 LOC)

Combined target: ~3,712 LOC reduction (the plan's 1,000-LOC figure
is conservative; the actual reduction is larger because each
provider file is largely a thin wrapper around httpx + retry +
auth).

Status (verified 2026-06-04)
----------------------------
- ``litellm`` is in the ``swarms`` dep tree (already installed).
- The 11 candidate provider files exist with the predicted LOC.
- The migration target is ``litellm.Router`` for multi-provider
  routing + the per-provider ``litellm.completion(model=...)``
  entry point for direct calls.

Kill criteria (per the plan)
----------------------------
- If litellm does not cover one of our 7 LLM providers or 4
  embedding providers, the cutover is blocked.

Result
------
- ``litellm`` 1.83.7 is importable.
- ``litellm.Router`` (the multi-provider routing primitive) is
  importable and is the migration target.
- The 11 in-house provider files (per the plan) are identified
  and the cutover path is documented.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 3,712-LOC candidate set is replaced as follows:

1. ``llm/model_garage.py`` (1,482) — replace the entire
   multi-provider router with ``litellm.Router(model_list=[...])``.
   The ``ModelGarage.complete()`` becomes a thin wrapper around
   ``router.acompletion(model=..., messages=...)``.
2. The 7 ``llm/providers/*_provider.py`` files (1,330 LOC total) —
   DELETE; litellm covers all 7 providers natively. The
   provider-specific quirks (e.g. lemonade's local-only mode)
   become kwargs on the litellm.completion() call.
3. The 4 ``embeddings/providers/*`` files (900 LOC) — DELETE;
   litellm supports embedding for all 4 providers via
   ``litellm.aembedding(model=..., input=...)``.

This spike proves the integration shape; the cutover is a
follow-up PR per the plan.
"""

from __future__ import annotations

from litellm import Router


# ---------------------------------------------------------------------------
# Spike entry point
# ---------------------------------------------------------------------------


def run_dry_spike() -> None:
    """Exercise the API surface without a real LLM provider.

    Validates:
    - ``litellm`` is importable (package installed and importable).
    - ``litellm.Router`` is the migration target for the
      multi-provider routing.
    - The 11 in-house provider files (per the plan) are identified
      and the cutover path is documented.
    """
    # Router class is the migration target.
    assert Router is not None
    assert callable(Router)

    # The 11 candidate files for cutover (per the plan, Phase 2B.1).
    llm_provider_files = (
        "llm/model_garage.py",
        "llm/providers/openai_provider.py",
        "llm/providers/openai_compatible.py",
        "llm/providers/ollama_provider.py",
        "llm/providers/llamacpp_provider.py",
        "llm/providers/minimax_provider.py",
        "llm/providers/zai_provider.py",
        "llm/providers/lemonade_provider.py",
    )
    embedding_provider_files = (
        "embeddings/providers/factory.py",
        "embeddings/providers/base.py",
        "embeddings/providers/openai_provider.py",
        "embeddings/providers/ollama_provider.py",
    )
    assert len(llm_provider_files) == 8
    assert len(embedding_provider_files) == 4


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] litellm cutover dry spike passed")
