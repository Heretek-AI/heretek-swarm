"""Agent factory for constructing swarms.Agent instances from environment variables.

This module provides a single function, ``build_agent_for``, that reads
``OPENAI_API_KEY``, ``OPENAI_BASE_URL``, and ``LLM_MODEL`` from the
environment and returns a configured ``swarms.Agent``.

Usage::

    from heretek_swarm.agents.agent_factory import build_agent_for

    agent = build_agent_for("alpha", "AlphaAgent")
    response = agent.run("your prompt here")
"""

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swarms import Agent

logger = logging.getLogger(__name__)


def build_agent_for(
    agent_id: str,
    agent_class_name: str,
    system_prompt: str | None = None,
) -> "Agent":
    """Construct and return a ``swarms.Agent`` configured from environment variables.

    The following environment variables are read **inside this function**
    (not at module level) so that importing the module stays fast:

    ====================  =============================================
    Variable              Behaviour
    ====================  =============================================
    ``OPENAI_API_KEY``    **Required.**  Raises ``ValueError`` if unset.
    ``OPENAI_BASE_URL``   Optional.  Defaults to ``https://api.openai.com/v1``.
    ``LLM_MODEL``         Optional.  Defaults to ``gpt-4.1``.
    ====================  =============================================

    The returned agent is a plain synchronous ``swarms.Agent``.  Callers
    that need async execution (e.g. ``AgentActor.run_with_llm``) already
    wrap calls with ``asyncio.to_thread``.

    Parameters
    ----------
    agent_id : str
        Unique identifier for this agent instance.  Used as the agent's
        ``agent_name`` so the ID is visible in logs and downstream systems.
    agent_class_name : str
        Human-readable class / type label (e.g. ``"AlphaAgent"``).
        Included in logs for traceability.
    system_prompt : str or None, optional
        Optional system prompt to pass to the agent.  When ``None``
        (the default) swarms will auto-generate a default prompt.

    Returns
    -------
    swarms.Agent
        A fully configured agent instance.

    Raises
    ------
    ValueError
        If ``OPENAI_API_KEY`` is not set in the environment.
    """
    from swarms import Agent  # noqa: PLC0415 — deferred so module load stays fast

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Agent construction requires a valid OpenAI-compatible API key."
        )

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-4.1")

    agent = Agent(
        agent_name=agent_id,
        model_name=model,
        llm_base_url=base_url,
        llm_api_key=api_key,
        system_prompt=system_prompt,
    )

    logger.info(
        "Built agent %s (%s) — model=%s base_url=%s",
        agent_id,
        agent_class_name,
        model,
        base_url,
    )
    return agent
