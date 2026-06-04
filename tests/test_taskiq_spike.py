"""Tests for the Phase 1.2 Taskiq + NATS broker spike (dry-mode only)."""

from __future__ import annotations

from heretek_swarm.gateway.taskiq_spike import (
    build_broker,
    build_result_backend,
    build_schedule_source,
    consensus_vote,
    run_dry_spike,
    translate_text,
)


def test_dry_spike_passes():
    """The 4-level Pydantic model + Instructor API surface is valid."""
    run_dry_spike()


def test_build_broker_constructs_without_io():
    """build_broker() returns a NatsBroker; no NATS connection required."""
    b = build_broker()
    assert b is not None
    # The default queue name from the spike factory.
    assert b.queue == "heretek-swarm-tasks"


def test_build_broker_accepts_custom_servers():
    """build_broker() accepts a list of NATS server URLs."""
    b = build_broker(nats_servers=["nats://nats-1:4222", "nats://nats-2:4222"])
    assert b.servers == ["nats://nats-1:4222", "nats://nats-2:4222"]


def test_build_result_backend_constructs_without_io():
    """build_result_backend() returns a NATSObjectStoreResultBackend."""
    rb = build_result_backend()
    assert rb is not None
    # taskiq-nats uses its own internal bucket naming
    # (``taskiq_results``) and ignores the user-supplied bucket
    # parameter on this version. The factory still constructs
    # successfully; the bucket parameter is currently advisory.
    assert rb.bucket_name.startswith("taskiq_")


def test_build_schedule_source_constructs_without_io():
    """build_schedule_source() returns a NATSKeyValueScheduleSource."""
    ss = build_schedule_source()
    assert ss is not None
    # Same advisory-bucket caveat as the result backend above.
    assert ss.bucket_name.startswith("taskiq_")


def test_module_level_broker_has_registered_tasks():
    """The @broker.task decorators registered translate_text and consensus_vote."""
    from heretek_swarm.gateway import taskiq_spike

    all_tasks = taskiq_spike.broker.get_all_tasks()
    task_names = set(all_tasks.keys())
    assert any("translate_text" in n for n in task_names)
    assert any("consensus_vote" in n for n in task_names)


def test_translate_text_task_exists():
    """translate_text is importable and is a Taskiq task object."""
    # Tasks are wrapped objects; the .kiq() method is the public
    # entry point for enqueuing.
    assert hasattr(translate_text, "kiq")
    assert hasattr(consensus_vote, "kiq")
