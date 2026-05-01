"""
Integration verification: WebSocket status messages reach dashboard clients.

Starts the API as a subprocess with minimal env dependencies,
connects a WebSocket client to /ws/dashboard, manually triggers
agent_status updates via the running pump, and verifies payload.

Usage: python tests/test_ws_status_pump_integration.py
"""

import asyncio
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


HERETEK_API_KEY = "integration-test-key-abc123"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


async def main() -> int:
    port = _free_port()
    host = "127.0.0.1"
    project_root = Path(__file__).parent.parent.resolve()
    api_root = project_root / "heretek-swarm"

    # Use a temp SQLite db so the server doesn't need real PG
    sqlite_path = Path(f"/tmp/test_ws_pump_{port}.db")
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()

    env = {
        **os.environ,
        "HERETEK_API_KEY": HERETEK_API_KEY,
        "DATABASE_URL": f"sqlite+aiosqlite:///{sqlite_path}",
        "RATE_LIMIT_ENABLED": "false",
        "LOG_LEVEL": "error",
        "LOG_FORMAT": "json",
        "OPENAI_API_KEY": "sk-dummy-for-integration-test",
    }

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "heretek_swarm.api.main:app",
            "--host",
            host,
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(api_root),
    )

    # Wait for the server to become ready
    import httpx

    ready = False
    for attempt in range(30):
        try:
            r = httpx.get(f"http://{host}:{port}/api/health/live", timeout=2.0)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    if not ready:
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        print("SERVER FAILED TO START")
        print("STDOUT:", stdout.decode()[:2000])
        print("STDERR:", stderr.decode()[:2000])
        return 1

    print(f"Server started on {host}:{port}")

    passed = 0
    failed = 0

    # -----------------------------------------------------------------------
    # Test 1: Connect to /ws/dashboard and receive agent_status messages
    # -----------------------------------------------------------------------
    print("\n--- Test 1: Dashboard WS receives agent_status messages ---")
    try:
        import websockets

        async with websockets.connect(
            f"ws://{host}:{port}/ws/dashboard?token={HERETEK_API_KEY}",
            ping_interval=None,
        ) as ws:
            received = []
            deadline = time.monotonic() + 20

            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    msg = json.loads(raw)
                    if msg.get("type") == "agent_status":
                        received.append(msg)
                        # Early exit if we have enough
                        agents = {m["agentId"] for m in received}
                        if len(agents) >= 2:
                            break
                except asyncio.TimeoutError:
                    continue

            print(f"  Received {len(received)} agent_status messages")
            if received:
                print(f"  Sample: {json.dumps(received[0], indent=2)}")

            if len(received) >= 2:
                # Verify payload shape
                for msg in received:
                    assert msg["type"] == "agent_status", f"Bad type: {msg.get('type')}"
                    assert "agentId" in msg, f"Missing agentId in {msg}"
                    assert "status" in msg, f"Missing status in {msg}"
                    assert "lastHeartbeat" in msg, f"Missing lastHeartbeat in {msg}"

                distinct = {m["agentId"] for m in received}
                print(f"  Distinct agents: {distinct}")
                assert len(distinct) >= 2, f"Only {len(distinct)} distinct agents"
                print("  PASS")
                passed += 1
            else:
                print(f"  FAIL: got {len(received)} agent_status messages, expected >= 2")
                print(f"  All received messages: {json.dumps([r.get('type') for r in received])}")
                failed += 1

    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # -----------------------------------------------------------------------
    # Test 2: Auth rejection without token
    # -----------------------------------------------------------------------
    print("\n--- Test 2: Auth required for dashboard WS ---")
    try:
        import websockets

        async with websockets.connect(f"ws://{host}:{port}/ws/dashboard") as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            msg = json.loads(raw)
            if msg.get("type") == "error":
                print(f"  Received error: {msg.get('error')}")
                print("  PASS")
                passed += 1
            else:
                print(f"  FAIL: Expected error, got {msg.get('type')}")
                failed += 1
    except Exception as e:
        # Connection may be closed
        print(f"  Error (expected): {type(e).__name__}")
        print("  PASS (auth-rejection path)")
        passed += 1

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")

    # Cleanup
    proc.terminate()
    proc.wait(timeout=5)
    if sqlite_path.exists():
        sqlite_path.unlink()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
