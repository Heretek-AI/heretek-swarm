"""Integration tests for NatsClient. Requires a live NATS at $TIER1_TEST_NATS_URL."""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest

from tier1.events.channels import subject_for
from tier1.events.nats_client import NatsClient


URL = os.environ.get("TIER1_TEST_NATS_URL", "")


@pytest.fixture
async def nats_client():
    if not URL:
        pytest.skip("set TIER1_TEST_NATS_URL to enable NATS integration tests")
    c = NatsClient(URL)
    await c.connect()
    yield c
    await c.close()


async def test_publish_and_subscribe(nats_client: NatsClient):
    sub_id = f"test-{uuid.uuid4().hex}"
    subject = subject_for(sub_id)

    received: list[bytes] = []

    async def consume():
        async for payload in nats_client.subscribe(subject):
            received.append(payload)
            if len(received) >= 1:
                return

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.3)
    await nats_client.publish(subject, b"hello")
    await asyncio.sleep(0.3)
    task.cancel()
    assert b"hello" in received


async def test_health(nats_client: NatsClient):
    assert await nats_client.health() is True
