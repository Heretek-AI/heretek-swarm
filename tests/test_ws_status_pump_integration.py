"""
Integration test for WebSocket status pump (M005/S02/T02).

Starts the API server, connects a dashboard WebSocket client, and verifies
that agent_status messages arrive with the correct envelope format and recur
every ~10s.

Usage:
    pytest tests/test_ws_status_pump_integration.py -v --timeout=30
"""

from __future__ import annotations

import asyncio
import json
import multiprocessing
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import structlog

# This integration test requires a running infrastructure stack (Postgres,
# Redis, etc.) and a real API server.  Skip unconditionally unless the
# HERETEK_RUN_INTEGRATION env-var is set.
pytestmark = pytest.mark.skipif(
    not os.environ.get("HERETEK_RUN_INTEGRATION"),
    reason="Integration test requires running infrastructure (set HERETEK_RUN_INTEGRATION=1 to enable)",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_PORT = 19877  # Non-standard port to avoid conflicts
API_KEY = "htsk_your_api_key_here"
WS_URL = f"ws://localhost:{API_PORT}/ws/dashboard?token={API_KEY}"
PUMP_INTERVAL = 10  # The pump fires every 10s
CAPTURE_TIMEOUT = 18  # Slightly more than 1 pump interval (allow for startup)
BATCH_COUNT = 2  # We want at least 2 batches


@pytest.fixture(scope="module")
def api_server():
    """Start the API server as a subprocess for the duration of the module.

    We need a live server with a supervisor that has spawned actors so the
    pump has data to broadcast.
    """
    env = os.environ.copy()
    env.update({
        "DATABASE_URL": "sqlite+aiosqlite:///./test_ws_integration.db",
        "HERETEK_API_KEY": API_KEY,
        "LOG_LEVEL": "WARNING",
        "LOG_FORMAT": "json",
    })

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "heretek_swarm.api.main:app",
            "--host", "0.0.0.0",
            "--port", str(API_PORT),
            "--log-level", "warning",
        ],
        cwd=str(Path(__file__).resolve().parent.parent / "heretek-swarm"),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for the server to become responsive
    import httpx

    deadline = time.time() + 20
    ready = False
    while time.time() < deadline:
        try:
            r = httpx.get(f"http://localhost:{API_PORT}/api/health/live", timeout=2)
            if r.status_code == 200:
                ready = True
                break
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
            pass
        time.sleep(0.5)

    if not ready:
        proc.terminate()
        proc.wait()
        pytest.fail("API server did not start within 20s")

    yield

    # Teardown
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    # Clean up test DB
    db_path = Path(__file__).resolve().parent.parent / "heretek-swarm" / "test_ws_integration.db"
    if db_path.exists():
        db_path.unlink()


@pytest.mark.asyncio
async def test_agent_status_messages_received(api_server):
    """Connect to /ws/dashboard and verify agent_status messages arrive
    with correct payload structure and repeat at ~10s intervals."""
    import websockets

    messages: list[dict] = []
    start = time.time()

    async with websockets.connect(WS_URL, max_size=2 ** 20) as ws:
        # Wait for messages up to CAPTURE_TIMEOUT seconds
        deadline = start + CAPTURE_TIMEOUT
        while time.time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                msg = json.loads(raw)
                messages.append(msg)
            except asyncio.TimeoutError:
                continue

    # --- Assertions ---

    # Filter to agent_status messages only (ignore heartbeats, pong, etc.)
    status_msgs = [m for m in messages if m.get("type") == "agent_status"]

    assert len(status_msgs) > 0, (
        f"No agent_status messages received in {CAPTURE_TIMEOUT}s "
        f"(got {len(messages)} total messages)"
    )

    # Check payload structure on first message
    first = status_msgs[0]
    assert "agentId" in first, f"Missing agentId in {first}"
    assert "status" in first, f"Missing status in {first}"
    assert "lastHeartbeat" in first, f"Missing lastHeartbeat in {first}"

    # Check unique agents — we should hear from multiple agents
    unique_agents = {m["agentId"] for m in status_msgs}
    assert len(unique_agents) >= 2, (
        f"Expected 2+ unique agents, got {len(unique_agents)}: {unique_agents}"
    )

    # Status must be a known value
    known_statuses = {"active", "idle", "processing", "error", "suspended", "unknown"}
    for m in status_msgs:
        assert m["status"] in known_statuses, (
            f"Unexpected status '{m['status']}' for agent {m['agentId']}"
        )

    # lastHeartbeat must be a valid ISO timestamp
    from datetime import datetime
    for m in status_msgs:
        try:
            datetime.fromisoformat(m["lastHeartbeat"])
        except (ValueError, TypeError):
            pytest.fail(f"Invalid lastHeartbeat '{m['lastHeartbeat']}' for agent {m['agentId']}")

    # Verify we got 2+ batches (pump fires every 10s, we waited 18s)
    # Group messages by approximate timestamp (bucket by 5s intervals)
    timestamps = sorted(
        datetime.fromisoformat(m["lastHeartbeat"]) for m in status_msgs
    )
    time_spans = (timestamps[-1] - timestamps[0]).total_seconds()
    assert time_spans >= 8, (
        f"Expected messages spanning at least 8s (2 pump cycles), "
        f"got {time_spans:.1f}s span — pump may not be recurring"
    )
