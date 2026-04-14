import asyncio
from typing import Any

import pytest

from heretek_swarm.gateway.nats_event_mesh import _InMemoryFallback


@pytest.fixture
def fallback():
    return _InMemoryFallback()


async def _subscribe(fallback: _InMemoryFallback, subject: str) -> list[dict[str, Any]]:
    received: list[dict[str, Any]] = []

    async def cb(mesh_obj: Any, subj: str, data: dict[str, Any]) -> None:
        received.append({"mesh_obj": mesh_obj, "subject": subj, "data": data})

    await fallback.subscribe(subject, cb)
    return received


async def test_exact_subject_match(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "test.exact")
    await fallback.publish("test.exact", {"msg": 1})

    assert len(received) == 1
    assert received[0]["data"] == {"msg": 1}
    assert received[0]["subject"] == "test.exact"
    assert received[0]["mesh_obj"] is None


async def test_exact_subject_no_match(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "test.exact")
    await fallback.publish("test.other", {"msg": 1})

    assert len(received) == 0


async def test_wildcard_gt_matches_single_child(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "test.>")
    await fallback.publish("test.event", {"msg": 1})

    assert len(received) == 1
    assert received[0]["data"] == {"msg": 1}


async def test_wildcard_gt_matches_nested(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "test.>")
    await fallback.publish("test.a.b.c", {"msg": 1})

    assert len(received) == 1


async def test_wildcard_gt_no_match_different_prefix(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "test.>")
    await fallback.publish("other.event", {"msg": 1})

    assert len(received) == 0


async def test_wildcard_star_matches_one_token(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "events.*")
    await fallback.publish("events.click", {"msg": 1})

    assert len(received) == 1
    assert received[0]["data"] == {"msg": 1}


async def test_wildcard_star_no_match_nested(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "events.*")
    await fallback.publish("events.click.button", {"msg": 1})

    assert len(received) == 0


async def test_wildcard_star_no_match_prefix_only(fallback: _InMemoryFallback) -> None:
    received = await _subscribe(fallback, "events.*")
    await fallback.publish("events", {"msg": 1})

    assert len(received) == 0


async def test_multiple_subscribers_all_receive(fallback: _InMemoryFallback) -> None:
    r1: list[dict[str, Any]] = []
    r2: list[dict[str, Any]] = []

    async def cb1(mesh_obj: Any, subj: str, data: dict[str, Any]) -> None:
        r1.append(data)

    async def cb2(mesh_obj: Any, subj: str, data: dict[str, Any]) -> None:
        r2.append(data)

    await fallback.subscribe("topic", cb1)
    await fallback.subscribe("topic", cb2)
    await fallback.publish("topic", {"msg": "hello"})

    assert len(r1) == 1
    assert len(r2) == 1
    assert r1[0] == {"msg": "hello"}
    assert r2[0] == {"msg": "hello"}


async def test_wildcard_and_exact_both_match(fallback: _InMemoryFallback) -> None:
    exact: list[dict[str, Any]] = []
    wild: list[dict[str, Any]] = []

    async def cb_exact(mesh_obj: Any, subj: str, data: dict[str, Any]) -> None:
        exact.append(data)

    async def cb_wild(mesh_obj: Any, subj: str, data: dict[str, Any]) -> None:
        wild.append(data)

    await fallback.subscribe("events.click", cb_exact)
    await fallback.subscribe("events.*", cb_wild)
    await fallback.publish("events.click", {"msg": 1})

    assert len(exact) == 1
    assert len(wild) == 1


async def test_matches_subject_unit() -> None:
    m = _InMemoryFallback._matches_subject

    assert m("test.>", "test.a")
    assert m("test.>", "test.a.b.c")
    assert not m("test.>", "other.a")

    assert m("events.*", "events.click")
    assert not m("events.*", "events.click.button")
    assert not m("events.*", "events")

    assert m("a.b.c", "a.b.c")
    assert not m("a.b.c", "a.b")
    assert not m("a.b.c", "a.b.c.d")
