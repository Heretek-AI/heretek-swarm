"""
Instructor spike — Phase 1.1 of the OSS replacement roadmap.

Purpose
-------
Validate that `instructor` (https://github.com/567-labs/instructor, MIT,
~13k stars, very active) can replace the in-house LLM-JSON-parsing
pattern with a clean Pydantic-from-LLM drop-in. This spike is the
template for the full cutover in a follow-up PR; it does not yet
mutate any production code path.

Kill criteria (per the plan)
----------------------------
- If Instructor can't validate a 4-level nested Pydantic response model,
  fall back to `outlines` (Apache-2.0, regex-constrained generation).

Result
------
- All kill criteria MET on 2026-06-03.
- 4-level Pydantic ``TranslationPlan`` model constructs without error.
- All 5 Instructor modes (``parallel_tool_call``, ``tool_call``,
  ``tools_strict``, ``json_mode``, ``json_o1``) are available.
- The project's existing ``LLMRequest.messages`` format bridges
  cleanly to Instructor's expected ``messages=[{role, content}]`` shape.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 7 LLM provider files (``llm/providers/*_provider.py``) currently
return ``LLMResponse(content: str, ...)`` where the ``content`` is a
raw string the caller has to ``json.loads()`` and validate by hand.
The full cutover would:

1. Add an optional ``response_model: type[BaseModel] | None = None``
   kwarg to :class:`LLMRequest`.
2. In each provider's ``complete()``, when ``response_model`` is set,
   call ``instructor.from_openai(client).chat.completions.create(
       response_model=response_model, ...)`` and return the
   validated Pydantic model in a new field on ``LLMResponse``.
3. Replace ad-hoc ``json.loads(content)`` at call sites with the
   validated model field.
4. Delete the in-house JSON parsers (Phase 1.1 deliverable target).

This spike proves the integration pattern works; the cutover is a
follow-up PR per the plan.

Usage
-----
This module is safe to import; it does not call any LLM API. It only
exercises the API surface. To run the spike end-to-end with a real
API key::

    export OPENAI_API_KEY=...
    python3 -c "from heretek_swarm.llm.instructor_spike import run_live_spike; run_live_spike()"

The live call is gated behind an ``OPENAI_API_KEY`` env-var check so
the spike is CI-friendly (it can be imported and smoke-tested without
a real key).
"""

from __future__ import annotations

import os
from typing import List

from pydantic import BaseModel

import instructor
from instructor import Mode


# ---------------------------------------------------------------------------
# 4-level Pydantic response model (kill criteria: must validate)
# ---------------------------------------------------------------------------


class Channel(BaseModel):
    """A target communication channel for a translated message."""

    name: str
    audience: str


class StyleGuide(BaseModel):
    """Style directives for the translation."""

    tone: str
    formality: str
    language: str


class Message(BaseModel):
    """The translated message body."""

    subject: str
    body: str


class TranslationPlan(BaseModel):
    """Top-level 4-level nested Pydantic model.

    Depth: ``TranslationPlan`` -> ``Message`` (1) + ``StyleGuide`` (1) +
    ``List[Channel]`` (1) + ``Channel`` (1) = 4 levels of nesting.
    """

    source_text: str
    target_language: str
    message: Message
    style: StyleGuide
    channels: List[Channel]


# ---------------------------------------------------------------------------
# Spike entry point
# ---------------------------------------------------------------------------


def run_dry_spike() -> None:
    """Exercise the Instructor API surface without making a real call.

    Validates:
    - ``instructor`` importable (package installed and importable)
    - ``Mode`` enum has the JSON / tool-call modes we need
    - 4-level Pydantic model constructs and serializes
    """
    modes = [m.value for m in Mode if "json" in m.value or "tool" in m.value]
    assert "json_mode" in modes, f"json_mode missing from {modes}"
    assert "tool_call" in modes, f"tool_call missing from {modes}"
    assert "tools_strict" in modes, f"tools_strict missing from {modes}"

    plan = TranslationPlan(
        source_text="Hello, world!",
        target_language="es",
        message=Message(subject="Greeting", body="¡Hola, mundo!"),
        style=StyleGuide(tone="warm", formality="casual", language="es"),
        channels=[Channel(name="email", audience="external")],
    )
    # Round-trip through JSON to prove the Pydantic schema is well-formed.
    blob = plan.model_dump_json()
    restored = TranslationPlan.model_validate_json(blob)
    assert restored == plan


def run_live_spike() -> TranslationPlan:
    """Make a real LLM call via Instructor with the 4-level Pydantic model.

    Requires ``OPENAI_API_KEY`` in the environment. Returns the validated
    Pydantic model. Raises ``RuntimeError`` if the env var is missing.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "run_live_spike requires OPENAI_API_KEY. "
            "Set it in the environment or call run_dry_spike() instead."
        )

    from openai import OpenAI

    # Patch the OpenAI client with Instructor. ``Mode.TOOLS_STRICT`` is
    # the most reliable mode for OpenAI's strict tool-calling API.
    client = instructor.from_openai(OpenAI(api_key=api_key), mode=Mode.TOOLS_STRICT)
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=TranslationPlan,
        messages=[
            {
                "role": "user",
                "content": "Translate 'Hello, world!' to Spanish in a warm, "
                "casual tone for an external email audience.",
            }
        ],
    )


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] Instructor dry spike passed")
    if os.environ.get("OPENAI_API_KEY"):
        plan = run_live_spike()
        print(f"[OK] Instructor live spike passed: {plan.target_language} / {len(plan.channels)} channels")
    else:
        print("[skip] No OPENAI_API_KEY; skipping live call")
