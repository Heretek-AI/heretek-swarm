"""
NATS Event Mesh Uptime Stress Test — Gate 1 Criterion 6

Validates: NATS event mesh uptime >= 99.9% during sustained operation.
Duration: Configurable via NATS_STRESS_DURATION env var (default: 30s for CI,
          set to 3600 for the real Gate 1 run).

Requirements:
    - Running NATS server (``docker-compose up nats``)
    - ``pytest -m load --timeout=3700``

Skip conditions:
    - No NATS server available (automatic skip for CI without Docker)
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any

import pytest

from heretek_swarm.gateway.nats_event_mesh import NATSEventMesh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class UptimeMetrics:
    """Track connection state over time."""

    start_time: float = 0.0
    end_time: float = 0.0
    connected_seconds: float = 0.0
    disconnected_seconds: float = 0.0
    fallback_seconds: float = 0.0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    poll_count: int = 0
    state_transitions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def uptime_ratio(self) -> float:
        total = self.connected_seconds + self.disconnected_seconds + self.fallback_seconds
        if total == 0:
            return 0.0
        # Only count true connected (NOT fallback) as uptime
        return self.connected_seconds / total

    @property
    def message_delivery_rate(self) -> float:
        if self.total_messages_sent == 0:
            return 0.0
        return self.total_messages_received / self.total_messages_sent


def get_stress_duration() -> float:
    """Get test duration from env var or default (30 s)."""
    return float(os.environ.get("NATS_STRESS_DURATION", "30"))


async def check_nats_available() -> bool:
    """Return *True* if a real NATS server is reachable."""
    try:
        import nats

        nc = await nats.connect("nats://localhost:4222", connect_timeout=2)
        await nc.close()
        return True
    except Exception:
        return False


async def create_event_mesh_connect() -> NATSEventMesh:
    """Create and connect a NATSEventMesh instance to the local NATS server."""
    mesh = NATSEventMesh(
        servers=["nats://localhost:4222"],
        name="stress_test",
        fallback=False,  # We want a hard failure, not silent fallback
    )
    await mesh.connect()
    return mesh


# ---------------------------------------------------------------------------
# Long-running stress tests (require real NATS)
# ---------------------------------------------------------------------------


@pytest.mark.load
@pytest.mark.slow
class TestNATSUptimeStress:
    """NATS Event Mesh uptime stress tests for Gate 1."""

    @pytest.fixture(autouse=True)
    async def _require_nats(self) -> None:  # noqa: PT021
        """Skip the entire class if NATS is not reachable."""
        if not await check_nats_available():
            pytest.skip("NATS server not available — start with: docker-compose up nats")

    async def test_nats_event_mesh_uptime(self) -> None:
        """
        Gate 1 Criterion 6: NATS event mesh uptime >= 99.9%.

        Continuously polls connection state for the configured duration.
        Asserts that connected time / total time >= 0.999.
        Fallback mode is explicitly counted as *non-uptime*.
        """
        duration = get_stress_duration()
        metrics = UptimeMetrics()

        mesh = await create_event_mesh_connect()

        try:
            metrics.start_time = time.monotonic()
            last_state = "connected" if mesh.is_connected else "disconnected"
            last_poll = metrics.start_time

            poll_interval = 0.1  # 100 ms polling

            while time.monotonic() - metrics.start_time < duration:
                await asyncio.sleep(poll_interval)
                now = time.monotonic()
                elapsed = now - last_poll

                # Determine current state — fallback is NOT uptime
                is_connected = mesh.is_connected
                is_fallback = getattr(mesh, "_use_fallback", False)

                if is_fallback:
                    current_state = "fallback"
                elif is_connected:
                    current_state = "connected"
                else:
                    current_state = "disconnected"

                # Accumulate time in the current state bucket
                if current_state == "connected":
                    metrics.connected_seconds += elapsed
                elif current_state == "fallback":
                    metrics.fallback_seconds += elapsed
                else:
                    metrics.disconnected_seconds += elapsed

                # Track state transitions for diagnostics
                if current_state != last_state:
                    metrics.state_transitions.append(
                        {
                            "time": now - metrics.start_time,
                            "from": last_state,
                            "to": current_state,
                        }
                    )
                    last_state = current_state

                metrics.poll_count += 1
                last_poll = now

            metrics.end_time = time.monotonic()

        finally:
            await mesh.disconnect()

        # Gate 1 assertion
        assert metrics.uptime_ratio >= 0.999, (
            f"NATS uptime {metrics.uptime_ratio:.4f} below 99.9% threshold. "
            f"Connected: {metrics.connected_seconds:.1f}s, "
            f"Fallback: {metrics.fallback_seconds:.1f}s, "
            f"Disconnected: {metrics.disconnected_seconds:.1f}s, "
            f"Transitions: {len(metrics.state_transitions)}"
        )

    async def test_sustained_message_delivery(self) -> None:
        """
        Verify messages are delivered reliably under sustained load.

        Target: ~100 msg/s for test duration, >= 99.9% delivery rate.
        """
        duration = get_stress_duration()
        mesh = await create_event_mesh_connect()

        received: list[dict[str, Any]] = []
        subject = "stress.test.delivery"

        try:
            # Subscribe — NATSEventMesh callbacks are (mesh, subject, data)
            async def handler(
                _mesh: NATSEventMesh,
                _subject: str,
                data: dict[str, Any],
            ) -> None:
                received.append(data)

            await mesh.subscribe(subject, handler)
            await asyncio.sleep(0.5)  # Let subscription settle

            # Publish at ~100 msg/s
            sent = 0
            start = time.monotonic()
            publish_interval = 0.01  # 10 ms → 100 msg/s

            while time.monotonic() - start < duration:
                await mesh.publish(subject, {"seq": sent, "ts": time.monotonic()})
                sent += 1
                await asyncio.sleep(publish_interval)

            # Wait for stragglers
            await asyncio.sleep(2.0)

        finally:
            await mesh.disconnect()

        delivery_rate = len(received) / sent if sent > 0 else 0.0
        assert delivery_rate >= 0.999, (
            f"Message delivery rate {delivery_rate:.4f} below 99.9%. "
            f"Sent: {sent}, Received: {len(received)}"
        )

    async def test_no_silent_fallback(self) -> None:
        """
        Verify NATSEventMesh doesn't silently fall back to in-memory mode.

        With ``fallback=False`` the mesh should stay connected to real NATS
        for the entire test duration and never enter fallback state.
        """
        duration = min(get_stress_duration(), 30)  # Cap at 30 s
        mesh = await create_event_mesh_connect()

        try:
            start = time.monotonic()
            fallback_activations = 0

            while time.monotonic() - start < duration:
                is_fallback = getattr(mesh, "_use_fallback", False)
                if is_fallback:
                    fallback_activations += 1
                await asyncio.sleep(0.5)

        finally:
            await mesh.disconnect()

        assert fallback_activations == 0, (
            f"NATSEventMesh fell back to in-memory mode {fallback_activations} times "
            f"during {duration:.0f}s test. Should stay connected to real NATS."
        )


# ---------------------------------------------------------------------------
# Short mock-based tests (work without real NATS)
# ---------------------------------------------------------------------------


@pytest.mark.load
@pytest.mark.slow
class TestNATSUptimeShort:
    """Shorter tests for quick CI validation (no real NATS required)."""

    @staticmethod
    async def test_metrics_calculation_with_simulated_states() -> None:
        """
        Verify UptimeMetrics correctly classifies connected vs fallback.

        Uses the _InMemoryFallback directly to exercise state tracking.
        """
        from heretek_swarm.gateway.nats_event_mesh import _InMemoryFallback

        fallback = _InMemoryFallback()

        metrics = UptimeMetrics()
        metrics.start_time = time.monotonic()

        # Simulate 30 s connected, 0.01 s disconnected → well above 99.9%
        metrics.connected_seconds = 30.0
        metrics.disconnected_seconds = 0.01
        metrics.fallback_seconds = 0.0
        metrics.end_time = metrics.start_time + 30.01

        assert metrics.uptime_ratio >= 0.999
        assert metrics.uptime_ratio < 1.0  # Not perfect — 0.01 s downtime

        # Simulate fallback: should NOT count as uptime
        metrics2 = UptimeMetrics()
        metrics2.connected_seconds = 0.0
        metrics2.fallback_seconds = 30.0
        metrics2.disconnected_seconds = 0.0

        assert metrics2.uptime_ratio == 0.0, "Fallback must not count as uptime"

        # Exercise the fallback pub/sub to keep coverage honest
        messages: list[dict[str, Any]] = []

        async def cb(
            _mesh_obj: Any,
            subj: str,
            data: dict[str, Any],
        ) -> None:
            messages.append({"subject": subj, "data": data})

        await fallback.subscribe("test.topic", cb)
        await fallback.publish("test.topic", {"hello": "world"})

        assert len(messages) == 1
        assert messages[0]["data"] == {"hello": "world"}
