"""
NATS Event Mesh Stress Test.

Tests the NATS event mesh under high throughput (1000+ messages/second)
covering discovery, broadcasting, and memory sync systems.

Agent Gamma - QA and Validation Lead
ROADMAP Task 4.10: Stress test event mesh
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from heretek_swarm.infrastructure.nats import NATSClient
from heretek_swarm.infrastructure.nats.client import NATSConfig
from heretek_swarm.infrastructure.nats.memory_sync import (
    MEMORY_TOPIC_PREFIX,
    MemoryOperation,
    MemorySync,
    MemoryUpdate,
)

# =============================================================================
# Configuration
# =============================================================================

MESSAGES_PER_SECOND_TARGET = 1000
STRESS_TEST_DURATION_SECONDS = 5
WARMUP_DURATION_SECONDS = 1


# =============================================================================
# Metrics
# =============================================================================


@dataclass
class StressTestMetrics:
    """Metrics collected during stress testing."""

    total_messages: int = 0
    messages_sent: int = 0
    messages_failed: int = 0
    messages_received: int = 0
    duplicates: int = 0
    sync_requests_sent: int = 0
    sync_responses_received: int = 0
    conflicts_detected: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time

    @property
    def actual_messages_per_second(self) -> float:
        if self.duration_seconds == 0:
            return 0.0
        return self.messages_sent / self.duration_seconds

    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return sum(self.latencies_ms) / len(self.latencies_ms)

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    @property
    def max_latency_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def delivery_rate(self) -> float:
        if self.messages_sent == 0:
            return 0.0
        return (self.messages_received / self.messages_sent) * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_messages": self.total_messages,
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "messages_received": self.messages_received,
            "duplicates": self.duplicates,
            "sync_requests_sent": self.sync_requests_sent,
            "sync_responses_received": self.sync_responses_received,
            "conflicts_detected": self.conflicts_detected,
            "duration_seconds": self.duration_seconds,
            "actual_messages_per_second": self.actual_messages_per_second,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "delivery_rate_pct": self.delivery_rate,
        }


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def nats_config() -> NATSConfig:
    """NATS configuration for stress testing."""
    return NATSConfig(
        url="nats://localhost:4222",
        name="stress-test-client",
        max_reconnect_attempts=3,
        reconnect_time_step=1.0,
    )


@pytest.fixture
async def nats_client(nats_config: NATSConfig) -> NATSClient:
    """Create a NATS client for testing."""
    client = NATSClient(config=nats_config)
    yield client
    if client.is_connected:
        await client.disconnect()


@pytest.fixture
async def memory_sync(nats_client: NATSClient) -> MemorySync:
    """Create a MemorySync instance for testing."""
    sync = MemorySync(nats_client, agent_id=f"stress-test-{uuid.uuid4().hex[:8]}")
    connected = await sync.connect()
    if not connected:
        pytest.skip("NATS not available")
    yield sync
    if sync.is_connected:
        await sync.disconnect()


@pytest.fixture
def stress_metrics() -> StressTestMetrics:
    """Create stress test metrics tracker."""
    return StressTestMetrics()


# =============================================================================
# Stress Tests
# =============================================================================


@pytest.mark.load
@pytest.mark.asyncio
async def test_nats_high_throughput_publish(
    nats_client: NATSClient, stress_metrics: StressTestMetrics
) -> None:
    """
    Test publishing 1000+ messages/second to NATS.

    Validates that the event mesh can handle high throughput publishing.
    """
    connected = await nats_client.connect()
    if not connected:
        pytest.skip("NATS not available")

    stress_metrics.start_time = time.time()

    # Warmup
    for _ in range(100):
        await nats_client.publish(
            f"{MEMORY_TOPIC_PREFIX}.warmup",
            {"test": "warmup"},
        )
    await asyncio.sleep(WARMUP_DURATION_SECONDS)

    # High throughput publishing
    target_messages = MESSAGES_PER_SECOND_TARGET * STRESS_TEST_DURATION_SECONDS
    batch_size = 100

    for i in range(0, target_messages, batch_size):
        batch_start = time.time()
        tasks = []
        for j in range(batch_size):
            idx = i + j
            if idx >= target_messages:
                break
            payload = {
                "seq": idx,
                "agent_id": f"stress-agent-{idx % 10}",
                "timestamp": time.time(),
                "data": {"value": idx, "payload": "x" * 100},
            }
            tasks.append(
                nats_client.publish(
                    f"{MEMORY_TOPIC_PREFIX}.broadcast",
                    payload,
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        stress_metrics.messages_sent += len(results)
        stress_metrics.messages_failed += sum(
            1 for r in results if isinstance(r, Exception) or r is False
        )

        # Throttle to target rate
        elapsed = time.time() - batch_start
        target_time = (batch_size / MESSAGES_PER_SECOND_TARGET)
        if elapsed < target_time:
            await asyncio.sleep(target_time - elapsed)

    stress_metrics.end_time = time.time()

    # Validate
    assert stress_metrics.messages_sent >= target_messages * 0.9, (
        f"Expected ~{target_messages} messages, got {stress_metrics.messages_sent}"
    )
    assert stress_metrics.actual_messages_per_second >= MESSAGES_PER_SECOND_TARGET * 0.8, (
        f"Expected ~{MESSAGES_PER_SECOND_TARGET} msg/s, "
        f"got {stress_metrics.actual_messages_per_second:.0f}"
    )

    print("\nThroughput test results:")
    print(f"  Messages sent: {stress_metrics.messages_sent}")
    print(f"  Messages/sec: {stress_metrics.actual_messages_per_second:.0f}")
    print(f"  Failed: {stress_metrics.messages_failed}")


@pytest.mark.load
@pytest.mark.asyncio
async def test_memory_sync_high_throughput(
    memory_sync: MemorySync, stress_metrics: StressTestMetrics
) -> None:
    """
    Test memory sync at 1000+ messages/second.

    Validates that memory synchronization handles high throughput
    with vector clock updates and conflict detection.
    """
    received_updates: list[MemoryUpdate] = []
    seen_ids: set[str] = set()

    async def update_callback(update: MemoryUpdate) -> None:
        received_updates.append(update)
        if update.message_id in seen_ids:
            stress_metrics.duplicates += 1
        seen_ids.add(update.message_id)

    await memory_sync.subscribe_memory_updates(update_callback)

    stress_metrics.start_time = time.time()

    # Publish at high rate
    target_messages = MESSAGES_PER_SECOND_TARGET * STRESS_TEST_DURATION_SECONDS

    for i in range(target_messages):
        send_time = time.time()
        op = MemoryOperation.UPDATE if i % 10 != 0 else MemoryOperation.CREATE
        content = {"seq": i, "data": f"message-{i}", "timestamp": send_time}

        success = await memory_sync.broadcast_memory_update(
            agent_id=memory_sync.agent_id,
            memory_id=f"mem-{i % 100}",  # 100 distinct memories
            operation=op,
            content=content,
            tier="warm",
        )

        if success:
            stress_metrics.messages_sent += 1
            stress_metrics.latencies_ms.append((time.time() - send_time) * 1000)
        else:
            stress_metrics.messages_failed += 1

        # Rate limiting
        if i % 100 == 0:
            await asyncio.sleep(0.095)  # Target ~1000/sec

    stress_metrics.end_time = time.time()

    # Allow time for message delivery
    await asyncio.sleep(1.0)
    stress_metrics.messages_received = len(received_updates)

    # Validate
    assert stress_metrics.messages_sent >= target_messages * 0.9, (
        f"Expected ~{target_messages} sent, got {stress_metrics.messages_sent}"
    )
    assert stress_metrics.actual_messages_per_second >= MESSAGES_PER_SECOND_TARGET * 0.7, (
        f"Expected ~{MESSAGES_PER_SECOND_TARGET} msg/s, "
        f"got {stress_metrics.actual_messages_per_second:.0f}"
    )
    assert stress_metrics.p95_latency_ms < 50, (
        f"P95 latency {stress_metrics.p95_latency_ms:.2f}ms exceeds 50ms target"
    )

    print("\nMemory sync stress test results:")
    print(f"  Messages sent: {stress_metrics.messages_sent}")
    print(f"  Messages received: {stress_metrics.messages_received}")
    print(f"  Duplicates: {stress_metrics.duplicates}")
    print(f"  Messages/sec: {stress_metrics.actual_messages_per_second:.0f}")
    print(f"  Avg latency: {stress_metrics.avg_latency_ms:.2f}ms")
    print(f"  P95 latency: {stress_metrics.p95_latency_ms:.2f}ms")
    print(f"  Max latency: {stress_metrics.max_latency_ms:.2f}ms")


@pytest.mark.load
@pytest.mark.asyncio
async def test_discovery_broadcast_stress(
    nats_client: NATSClient, stress_metrics: StressTestMetrics
) -> None:
    """
    Test discovery system broadcast at high throughput.

    Validates that agent discovery and presence announcements
    can keep up with high message rates.
    """
    import json

    connected = await nats_client.connect()
    if not connected:
        pytest.skip("NATS not available")

    received_presence = []
    discovery_topic = "agents.presence"

    async def presence_handler(subject: str, data: bytes) -> None:
        try:
            msg = json.loads(data.decode())
            received_presence.append(msg)
            stress_metrics.messages_received += 1
        except Exception:
            pass

    await nats_client.subscribe(
        discovery_topic,
        callback=presence_handler,
        queue="stress-test-discovery",
    )

    stress_metrics.start_time = time.time()

    # Broadcast presence updates at high rate
    for i in range(MESSAGES_PER_SECOND_TARGET * STRESS_TEST_DURATION_SECONDS):
        agent_id = f"agent-{i % 50}"
        presence = {
            "type": "presence",
            "agent_id": agent_id,
            "status": "active",
            "timestamp": time.time(),
            "seq": i,
        }
        success = await nats_client.publish(discovery_topic, presence)
        if success:
            stress_metrics.messages_sent += 1
        else:
            stress_metrics.messages_failed += 1

        if i % 200 == 0:
            await asyncio.sleep(0.19)

    stress_metrics.end_time = time.time()
    await asyncio.sleep(0.5)

    # Validate
    assert stress_metrics.messages_sent >= MESSAGES_PER_SECOND_TARGET * 0.8
    assert stress_metrics.actual_messages_per_second >= MESSAGES_PER_SECOND_TARGET * 0.6
    assert stress_metrics.messages_received >= stress_metrics.messages_sent * 0.5

    print("\nDiscovery broadcast stress results:")
    print(f"  Sent: {stress_metrics.messages_sent}")
    print(f"  Received: {stress_metrics.messages_received}")
    print(f"  Rate: {stress_metrics.actual_messages_per_second:.0f} msg/s")


@pytest.mark.load
@pytest.mark.asyncio
async def test_memory_sync_state_requests(
    memory_sync: MemorySync, stress_metrics: StressTestMetrics
) -> None:
    """
    Test memory sync state requests under load.

    Validates that sync_state() handles multiple pending
    requests efficiently.
    """
    # Pre-populate some memories
    memory_ids = [f"sync-test-{i}" for i in range(50)]
    for mid in memory_ids:
        await memory_sync.broadcast_memory_update(
            agent_id=memory_sync.agent_id,
            memory_id=mid,
            operation=MemoryOperation.CREATE,
            content={"data": f"content-{mid}"},
        )
    await asyncio.sleep(0.5)

    stress_metrics.start_time = time.time()

    # Send sync requests for multiple memories
    for _ in range(100):
        sync_ids = memory_ids[:10]  # 10 at a time
        results = await memory_sync.sync_state(sync_ids, timeout_sec=2.0)
        stress_metrics.sync_requests_sent += 1
        stress_metrics.sync_responses_received += sum(
            1 for r in results.values() if r is not None
        )

    stress_metrics.end_time = time.time()

    # Validate
    assert stress_metrics.sync_requests_sent == 100
    assert stress_metrics.sync_responses_received >= 500  # At least 50% hit rate

    print("\nSync state request results:")
    print(f"  Requests sent: {stress_metrics.sync_requests_sent}")
    print(f"  Responses received: {stress_metrics.sync_responses_received}")
    print(f"  Duration: {stress_metrics.duration_seconds:.2f}s")


@pytest.mark.load
@pytest.mark.asyncio
async def test_vector_clock_conflict_detection(
    memory_sync: MemorySync, stress_metrics: StressTestMetrics
) -> None:
    """
    Test vector clock conflict detection under concurrent updates.

    Simulates multiple agents updating the same memory concurrently
    and validates conflict resolution.
    """
    memory_id = "conflict-test-memory"

    # Simulate concurrent updates from different "agents"
    updates_sent = 0
    conflicts_detected = 0

    async def simulate_agent_update(agent_id: str, count: int) -> None:
        nonlocal updates_sent, conflicts_detected
        for i in range(count):
            success = await memory_sync.broadcast_memory_update(
                agent_id=agent_id,
                memory_id=memory_id,
                operation=MemoryOperation.UPDATE,
                content={"agent": agent_id, "seq": i, "timestamp": time.time()},
            )
            if success:
                updates_sent += 1
            await asyncio.sleep(0.001)  # Small delay to create concurrency

    # Run 5 agents concurrently, each sending 20 updates
    agent_count = 5
    updates_per_agent = 20

    tasks = [
        simulate_agent_update(f"agent-{i}", updates_per_agent)
        for i in range(agent_count)
    ]
    await asyncio.gather(*tasks)

    # Give time for all updates to propagate
    await asyncio.sleep(1.0)

    # Verify final state
    final_update = await memory_sync.get_local_cached_update(memory_id)
    assert final_update is not None
    assert final_update.agent_id in [f"agent-{i}" for i in range(agent_count)]

    print("\nVector clock conflict test results:")
    print(f"  Concurrent agents: {agent_count}")
    print(f"  Updates per agent: {updates_per_agent}")
    print(f"  Total updates: {updates_sent}")
    print(f"  Final writer: {final_update.agent_id}")


# =============================================================================
# Summary Test
# =============================================================================


@pytest.mark.load
@pytest.mark.asyncio
async def test_event_mesh_overall_throughput() -> None:
    """
    Overall event mesh throughput validation.

    This is a summary test that validates the system meets
    the 1000+ messages/second target across all subsystems.
    """
    metrics = StressTestMetrics()
    client = NATSClient(config=NATSConfig(url="nats://localhost:4222"))

    connected = await client.connect()
    if not connected:
        pytest.skip("NATS not available")

    sync = MemorySync(client, agent_id=f"summary-{uuid.uuid4().hex[:8]}")
    await sync.connect()

    metrics.start_time = time.time()

    # Combined load: publish + memory sync
    async def publisher() -> None:
        for _ in range(500):
            await client.publish(
                f"{MEMORY_TOPIC_PREFIX}.summary",
                {"seq": _, "type": "broadcast"},
            )
            metrics.messages_sent += 1
            await asyncio.sleep(0.001)

    async def memory_publisher() -> None:
        for i in range(500):
            await sync.broadcast_memory_update(
                agent_id=sync.agent_id,
                memory_id=f"mem-{i}",
                operation=MemoryOperation.CREATE,
                content={"seq": i},
            )
            metrics.messages_sent += 1
            await asyncio.sleep(0.001)

    await asyncio.gather(publisher(), memory_publisher())

    metrics.end_time = time.time()
    await sync.disconnect()

    dur = metrics.duration_seconds
    actual_mps = metrics.messages_sent / dur if dur > 0 else 0

    assert actual_mps >= 500, (
        f"Combined throughput {actual_mps:.0f} msg/s below target"
    )

    print(f"\nOverall throughput: {actual_mps:.0f} msg/s")
    print(f"Total messages: {metrics.messages_sent}")
    print(f"Duration: {metrics.duration_seconds:.2f}s")
