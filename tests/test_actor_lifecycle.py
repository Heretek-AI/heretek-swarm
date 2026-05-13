"""
Lifecycle smoke tests for all canonical AgentActor subclasses.

Verifies that every AgentActor subclass can: construct with stubs → spawn →
confirm ACTIVE state → process a health_check message via mailbox → terminate
gracefully → confirm TERMINATED state with zero errors.

All tests use ``@pytest.mark.asyncio`` and minimal stub dependencies.
No real infrastructure required.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from heretek_swarm.actors import (
    AgentActor,
    AlphaAgent,
    ArbiterAgent,
    BetaAgent,
    CatalystAgent,
    CharlieAgent,
    ChronosAgent,
    CoderAgent,
    CoordinatorAgent,
    DreamerAgent,
    EchoAgent,
    EmpathAgent,
    ExaminerAgent,
    ExplorerAgent,
    HabitForgeAgent,
    HistorianAgent,
    MetisAgent,
    NexusAgent,
    PerceiverAgent,
    PerceiverPlusAgent,
    PrismAgent,
    SentinelAgent,
    SentinelPrimeAgent,
    StewardAgent,
)
from heretek_swarm.actors.base.core import ActorMessage, ActorState
from heretek_swarm.actors.profiling import BehaviorProfiler
from heretek_swarm.actors.stubs import (
    StubAccessAnalyzer,
    StubDeliberationEngine,
    StubEventMesh,
    StubLLMProvider,
    StubPatternExtractor,
    StubTribunal,
)
from heretek_swarm.actors.supervisor import ActorSupervisor


def _make_stubs() -> dict[str, Any]:
    """Return a dict of all 6 injectable stubs."""
    return {
        "access_analyzer": StubAccessAnalyzer(),
        "pattern_extractor": StubPatternExtractor(),
        "tribunal": StubTribunal(),
        "deliberation_engine": StubDeliberationEngine(),
        "llm_provider": StubLLMProvider(canned_response="lifecycle_test"),
        "event_mesh": StubEventMesh(),
    }


def _health_check_message() -> ActorMessage:
    """Return a minimal health_check ActorMessage."""
    return ActorMessage(
        sender="pytest",
        message_type="health_check",
        content={"reply_to": "health"},
        timestamp=datetime.now(UTC).isoformat(),
    )


async def _run_lifecycle(
    agent: AgentActor,
    *,
    label: str,
    brief_delay: float = 0.05,
) -> None:
    """Execute the standard lifecycle: spawn → health_check → terminate."""
    await agent.spawn()
    assert agent.state == ActorState.ACTIVE, (
        f"{label}: expected ACTIVE after spawn, got {agent.state}"
    )

    await agent.put_message(_health_check_message())
    await asyncio.sleep(brief_delay)

    await agent.terminate()
    assert agent.state == ActorState.TERMINATED, (
        f"{label}: expected TERMINATED after terminate, got {agent.state}"
    )

    assert agent.error_count == 0, f"{label}: expected 0 errors, got {agent.error_count}"


SIMPLE_AGENTS: list[tuple[type[AgentActor], dict[str, Any]]] = [
    (AgentActor, {"agent_id": "lc-base"}),
    (AlphaAgent, {"agent_id": "lc-alpha"}),
    (BetaAgent, {"agent_id": "lc-beta"}),
    (CharlieAgent, {"agent_id": "lc-charlie"}),
    (StewardAgent, {"agent_id": "lc-steward"}),
    (DreamerAgent, {"agent_id": "lc-dreamer"}),
    (EmpathAgent, {"agent_id": "lc-empath"}),
    (PrismAgent, {"agent_id": "lc-prism"}),
    (HistorianAgent, {"agent_id": "lc-historian"}),
    (MetisAgent, {"agent_id": "lc-metis"}),
    (PerceiverAgent, {"agent_id": "lc-perceiver"}),
    (ExplorerAgent, {"agent_id": "lc-explorer"}),
    (HabitForgeAgent, {"agent_id": "lc-habit-forge"}),
    (PerceiverPlusAgent, {"agent_id": "lc-perceiver-plus"}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_class", "base_kwargs"),
    SIMPLE_AGENTS,
    ids=[cls.__name__ for cls, _ in SIMPLE_AGENTS],
)
async def test_simple_agent_lifecycle(
    agent_class: type[AgentActor],
    base_kwargs: dict[str, Any],
) -> None:
    """Lifecycle test for agents with **kwargs passthrough."""
    stubs = _make_stubs()
    kwargs = {**base_kwargs, **stubs}
    agent = agent_class(**kwargs)
    await _run_lifecycle(agent, label=kwargs.get("agent_id", "simple"))


EXPLICIT_STUB_AGENTS: list[tuple[type[AgentActor], dict[str, Any]]] = [
    (ArbiterAgent, {"agent_id": "lc-arbiter"}),
    (CatalystAgent, {"agent_id": "lc-catalyst"}),
    (CoderAgent, {"agent_id": "lc-coder"}),
    (ExaminerAgent, {"agent_id": "lc-examiner"}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_class", "base_kwargs"),
    EXPLICIT_STUB_AGENTS,
    ids=[cls.__name__ for cls, _ in EXPLICIT_STUB_AGENTS],
)
async def test_explicit_stub_agent_lifecycle(
    agent_class: type[AgentActor],
    base_kwargs: dict[str, Any],
) -> None:
    """Lifecycle test for agents with explicit stub constructor params."""
    stubs = _make_stubs()
    kwargs = {
        **base_kwargs,
        "pattern_extractor": stubs["pattern_extractor"],
        "deliberation_engine": stubs["deliberation_engine"],
        "access_analyzer": stubs["access_analyzer"],
    }
    agent = agent_class(**kwargs)
    await _run_lifecycle(agent, label=base_kwargs.get("agent_id", "explicit"))


CONFIG_AGENTS: list[tuple[type[AgentActor], dict[str, Any]]] = [
    (CoordinatorAgent, {"agent_id": "lc-coordinator", "config": {}}),
    (ChronosAgent, {"agent_id": "lc-chronos", "config": {}}),
    (NexusAgent, {"agent_id": "lc-nexus", "config": {}}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_class", "kwargs"),
    CONFIG_AGENTS,
    ids=[cls.__name__ for cls, _ in CONFIG_AGENTS],
)
async def test_config_agent_lifecycle(
    agent_class: type[AgentActor],
    kwargs: dict[str, Any],
) -> None:
    """Lifecycle test for agents with config-based constructors."""
    agent = agent_class(**kwargs)
    await _run_lifecycle(agent, label=kwargs.get("agent_id", "config-agent"))


@pytest.mark.asyncio
async def test_echo_actor_lifecycle() -> None:
    """EchoAgent has a unique constructor; test it separately."""
    agent = EchoAgent(
        agent_id="lc-echo",
        config={},
        _pattern_extractor=StubPatternExtractor(),
        _deliberation_engine=StubDeliberationEngine(),
        _access_analyzer=StubAccessAnalyzer(),
        zero_trust_validator=None,
    )
    await _run_lifecycle(agent, label="lc-echo")


@pytest.mark.asyncio
async def test_sentinel_agent_lifecycle() -> None:
    """SentinelAgent uses config+db_pool+redis_client; test separately."""
    agent = SentinelAgent(agent_id="lc-sentinel", config={})
    await _run_lifecycle(agent, label="lc-sentinel")


@pytest.mark.asyncio
async def test_sentinel_prime_agent_lifecycle() -> None:
    """SentinelPrimeAgent uses config+db_pool+redis_client; test separately."""
    agent = SentinelPrimeAgent(agent_id="lc-sentinel-prime", config={})
    await _run_lifecycle(agent, label="lc-sentinel-prime")


@pytest.mark.asyncio
async def test_actor_supervisor_lifecycle() -> None:
    """ActorSupervisor has a unique constructor (name first)."""
    agent = ActorSupervisor(
        name="lc-supervisor",
        pattern_extractor=StubPatternExtractor(),
    )
    await _run_lifecycle(agent, label="lc-supervisor")


@pytest.mark.asyncio
async def test_behavior_profiler_lifecycle() -> None:
    """BehaviorProfiler has a (config, *args, **kwargs) constructor."""
    stubs = _make_stubs()
    agent = BehaviorProfiler(
        agent_id="lc-profiler",
        pattern_extractor=stubs["pattern_extractor"],
        access_analyzer=stubs["access_analyzer"],
        deliberation_engine=stubs["deliberation_engine"],
        tribunal=stubs["tribunal"],
        llm_provider=stubs["llm_provider"],
        event_mesh=stubs["event_mesh"],
    )
    await _run_lifecycle(agent, label="lc-profiler")
