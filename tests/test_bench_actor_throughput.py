"""
Benchmark tests for actor message processing throughput.

Exercises the message_handling module's process_message path via a mock agent
and measures throughput (msg/sec) using pytest-benchmark.

Design:
- Creates a lightweight mock agent that exercises `_process_mailbox` core path
- Uses @pytest.mark.bench marker so it can be run selectively with `-k bench_actor_throughput`
- Does NOT start a full swarm — only exercises the hot path in isolation

Usage:
    # Run benchmarks only (requires pytest-benchmark):
    pytest tests/test_bench_actor_throughput.py -k bench_actor_throughput --benchmark-only

    # Collect without running (verify benchmarks are registered):
    pytest tests/test_bench_actor_throughput.py -k bench_actor_throughput --benchmark-skip
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from heretek_swarm.actors.base.core import ActorMessage, AgentActor
from heretek_swarm.observability.timing import TimedContext


class _BenchAgent(AgentActor):
    """Minimal agent for benchmarking message processing hot path."""

    def __init__(self) -> None:
        # We avoid calling the real AgentActor.__init__ which requires
        # actor_type, agent_id, and swarms_agent. Instead, we manually
        # wire only the attributes needed for _process_mailbox / process_message.
        self.agent_id = "bench_agent"
        self.actor_type = "bench"
        self._running = True
        self.mailbox: asyncio.Queue[ActorMessage] = asyncio.Queue()
        self.message_count = 0
        self.error_count = 0
        self._messages_since_persist = 0
        self._persistence_interval = None
        self.last_activity = ""

    def __getattr__(self, name: str) -> Any:
        """Minimal attr fallback so mixins don't crash on missing attrs."""
        if name.startswith("_"):
            return None
        raise AttributeError(name)


@pytest.mark.bench
@pytest.mark.asyncio
async def test_bench_mailbox_throughput(benchmark: Any) -> None:
    """Benchmark: how many messages/sec can the mailbox processing loop handle?

    This exercises the core hot path: put_message → _process_mailbox iteration
    → process_message → handler dispatch.  Each iteration processes one message
    through the full pipeline including TimedContext instrumentation.
    """
    agent = _BenchAgent()

    # Mock the handler so we measure the path, not handler execution time
    agent._message_handlers = {}

    # Pre-populate the mailbox with 100 messages
    for i in range(100):
        await agent.mailbox.put(ActorMessage(
            sender="bench",
            message_type="bench_test",
            content={"index": i},
        ))

    async def process_one_batch() -> int:
        """Process all queued messages in a single _process_mailbox iteration."""
        agent._running = True
        count = 0
        while not agent.mailbox.empty() and agent._running and count < 100:
            with TimedContext(
                "actor_message_processed",
                histogram=None,
                histogram_labels={"actor_type": "bench"},
                agent_id=agent.agent_id,
                message_type="bench_test",
            ):
                # Directly exercise process_message which is the core path
                msg = await agent.mailbox.get()
                await agent.process_message(msg)
                agent.message_count += 1
                agent.mailbox.task_done()
                count += 1
        agent._running = False
        return count

    # Run the benchmark
    count = await benchmark(process_one_batch)
    assert count == 100


@pytest.mark.bench
@pytest.mark.asyncio
async def test_bench_process_message_isolated(benchmark: Any) -> None:
    """Benchmark: isolate single-message processing (handler dispatch) cost.

    Measures the overhead of validate → find handler → execute per message.
    """
    agent = _BenchAgent()

    # Register a mock handler that does minimal work
    handler_call_count = 0

    async def mock_handler(msg: ActorMessage) -> None:
        nonlocal handler_call_count
        handler_call_count += 1

    agent._message_handlers = {"bench_test": mock_handler}

    msg = ActorMessage(
        sender="bench",
        message_type="bench_test",
        content={"test": True},
    )

    async def bench_call() -> str:
        with TimedContext(
            "actor_message_processed",
            histogram=None,
            histogram_labels={"actor_type": "bench"},
            agent_id=agent.agent_id,
            message_type="bench_test",
        ):
            await agent.process_message(msg)
        return "ok"

    result = await benchmark(bench_call)
    assert result
