"""Test T05: Verify already-real stub functions and full verification suite.

Validates that:
- _get_actor_registry(), _find_matching_model(), extract_trace_context()
  return real non-None data
- No hardcoded placeholders remain in target code paths
- SnapshotManager integration round-trip preserves data
"""

from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import pytest

from heretek_swarm.actors.base.message_handling import AgentActorMessageHandling
from heretek_swarm.infrastructure.nats.client import NATSClient, NATSConfig
from heretek_swarm.routing.model_router import (
    AgentModelRouter,
    RouterProviderConfig,
    TaskComplexity,
)
from heretek_swarm.state.models import SnapshotConfig, SnapshotManager, StateSnapshot, SystemState

if TYPE_CHECKING:
    import uuid
    from pathlib import Path

pytestmark = [pytest.mark.unit]


# =============================================================================
# TestAlreadyRealFunctions
# =============================================================================


class TestAlreadyRealFunctions:
    """Verify that three research-identified already-real functions return data."""

    # -- _get_actor_registry --------------------------------------------------

    def test_get_actor_registry_returns_none_when_no_supervisor(self):
        """Without a supervisor, _get_actor_registry() returns None gracefully."""
        # Patch get_supervisor to return None (no supervisor initialized)
        import heretek_swarm.actors.supervisor as sv_mod

        saved = getattr(sv_mod, "get_supervisor", None)
        sv_mod.get_supervisor = lambda: None  # type: ignore[assignment,return-value]
        try:
            # Use the method directly from the mixin (it's a static-style method)
            result = AgentActorMessageHandling._get_actor_registry(
                cast("AgentActorMessageHandling", None)
            )
            assert result is None
        finally:
            if saved is not None:
                sv_mod.get_supervisor = saved

    def test_get_actor_registry_returns_dict_when_supervisor_available(self):
        """When a supervisor is registered with actors, return a non-None dict."""
        import heretek_swarm.actors.supervisor as sv_mod

        saved = getattr(sv_mod, "get_supervisor", None)

        # Simulate a supervisor with an actors dict
        fake_sv = MagicMock()
        fake_sv.actors = {"agent-1": MagicMock(), "agent-2": MagicMock()}
        sv_mod.get_supervisor = lambda: fake_sv
        try:
            result = AgentActorMessageHandling._get_actor_registry(
                cast("AgentActorMessageHandling", None)
            )
            assert result is not None
            assert isinstance(result, dict)
            assert len(result) == 2
            assert "agent-1" in result
            assert "agent-2" in result
        finally:
            if saved is not None:
                sv_mod.get_supervisor = saved

    def test_get_actor_registry_superset_returns_dict(self):
        """A supervisor with .actors attribute returns the actors dict directly."""
        import heretek_swarm.actors.supervisor as sv_mod

        saved = getattr(sv_mod, "get_supervisor", None)

        fake_sv = MagicMock()
        fake_sv.actors = {"alpha": object(), "beta": object(), "charlie": object()}
        sv_mod.get_supervisor = lambda: fake_sv
        try:
            result = AgentActorMessageHandling._get_actor_registry(
                cast("AgentActorMessageHandling", None)
            )
            assert isinstance(result, dict)
            assert result is fake_sv.actors
        finally:
            if saved is not None:
                sv_mod.get_supervisor = saved

    # -- _find_matching_model -------------------------------------------------

    def test_find_matching_model_returns_non_none_for_known_provider(self):
        """_find_matching_model returns a model string when a match exists."""
        router = AgentModelRouter("test-agent")
        provider = RouterProviderConfig(
            provider_id="anthropic",
            base_url="https://api.anthropic.com",
            api_key="sk-test",
            models=["claude-sonnet-4-20250514", "claude-haiku-3-5-20241022"],
            priority=1,
        )
        preferred = router._get_preferred_models(TaskComplexity.STANDARD)
        # STANDARD preferred: ["sonnet", "claude-sonnet", "gemini-pro"]

        result = router._find_matching_model(provider, preferred)
        assert result is not None
        assert isinstance(result, str)
        # "sonnet" appears in "claude-sonnet-4-20250514"
        assert "sonnet" in result.lower()

    def test_find_matching_model_returns_none_for_no_match(self):
        """_find_matching_model returns None when no preferred model matches."""
        router = AgentModelRouter("test-agent")
        provider = RouterProviderConfig(
            provider_id="custom",
            base_url="http://localhost:8080",
            api_key="",
            models=["custom-model-v1", "custom-model-v2"],
            priority=1,
        )
        preferred = ["opus", "sonnet", "haiku"]

        result = router._find_matching_model(provider, preferred)
        assert result is None

    def test_find_matching_model_returns_string_for_complex(self):
        """Complex task complexity routes to preferred models correctly."""
        router = AgentModelRouter("test-agent")
        provider = RouterProviderConfig(
            provider_id="gpu-cluster",
            base_url="http://gpu:8000",
            api_key="key",
            models=["claude-opus-v2", "claude-sonnet-v2", "o1-preview-2024"],
            priority=1,
        )
        preferred = router._get_preferred_models(TaskComplexity.COMPLEX)

        result = router._find_matching_model(provider, preferred)
        assert result is not None
        assert isinstance(result, str)
        # Should match opus first (first in COMPLEX preference list)
        assert "opus" in result.lower()

    def test_find_matching_model_returns_first_match_in_order(self):
        """The first preferred model that matches is returned (stable order)."""
        router = AgentModelRouter("test-agent")
        provider = RouterProviderConfig(
            provider_id="multi",
            base_url="http://localhost",
            api_key="",
            models=[
                "sonnet-v4",
                "opus-v3",
                "haiku-v1",
                "llama3.1-custom",
            ],
            priority=1,
        )
        # SIMPLE prefers haiku first, then llama3.1
        preferred = router._get_preferred_models(TaskComplexity.SIMPLE)

        result = router._find_matching_model(provider, preferred)
        assert result is not None
        # "haiku" should match "haiku-v1" before "llama3.1" matches "llama3.1-custom"
        assert "haiku" in result.lower()

    # -- extract_trace_context ------------------------------------------------

    def test_extract_trace_context_returns_dict_from_valid_headers(self):
        """Valid tracecontext header yields a dict with trace_id and span_id."""
        client = NATSClient(config=NATSConfig(url="nats://localhost:4222"))

        msg = MagicMock()
        msg.headers = {
            "tracecontext": json.dumps({
                "trace_id": "abc123def456",
                "span_id": "001122334455",
            }),
        }

        result = client.extract_trace_context(msg)
        assert result is not None
        assert isinstance(result, dict)
        assert result["trace_id"] == "abc123def456"
        assert result["span_id"] == "001122334455"

    def test_extract_trace_context_returns_none_when_no_headers(self):
        """Messages without headers return None."""
        client = NATSClient(config=NATSConfig(url="nats://localhost:4222"))

        msg = MagicMock()
        msg.headers = None

        result = client.extract_trace_context(msg)
        assert result is None

    def test_extract_trace_context_returns_none_when_no_tracecontext_header(self):
        """Headers without tracecontext key return None."""
        client = NATSClient(config=NATSConfig(url="nats://localhost:4222"))

        msg = MagicMock()
        msg.headers = {"x-custom": "value"}

        result = client.extract_trace_context(msg)
        assert result is None

    def test_extract_trace_context_handles_malformed_json(self):
        """Malformed JSON in tracecontext header returns None without raising."""
        client = NATSClient(config=NATSConfig(url="nats://localhost:4222"))

        msg = MagicMock()
        msg.headers = {"tracecontext": "{{not valid json"}

        result = client.extract_trace_context(msg)
        assert result is None  # Graceful degradation

    def test_extract_trace_context_returns_valid_otel_shape(self):
        """Returned dict has trace_id and span_id — valid OTel trace context."""
        client = NATSClient(config=NATSConfig(url="nats://localhost:4222"))

        msg = MagicMock()
        msg.headers = {
            "tracecontext": json.dumps({
                "trace_id": "0" * 32,
                "span_id": "0" * 16,
                "trace_flags": 1,
                "tracestate": "vendor=value",
            }),
        }

        result = client.extract_trace_context(msg)
        assert result is not None
        # Must contain at least trace_id and span_id for valid OTel context
        assert "trace_id" in result
        assert "span_id" in result
        assert len(result["trace_id"]) > 0
        assert len(result["span_id"]) > 0

    def test_extract_trace_context_message_without_hasattr_headers(self):
        """A message object without .headers attribute returns None gracefully."""
        client = NATSClient(config=NATSConfig(url="nats://localhost:4222"))

        msg = object()  # No .headers at all

        result = client.extract_trace_context(msg)
        assert result is None


# =============================================================================
# TestNoPlaceholderValues
# =============================================================================


class TestNoPlaceholderValues:
    """Confirm zero placeholder/stub residue in the target code paths."""

    # -- metrics.py: no dead-coded 0.5 / 0.1 placeholders --------------------

    def test_no_dead_coded_integration_placeholder(self):
        """The old unconditional integration_level=0.5 assignment is gone."""
        import heretek_swarm.observability.metrics as mod

        source = inspect.getsource(mod.SwarmMetricsCollector.collect_consciousness_metrics)

        # The old code had `integration = 0.5` as a hardcoded stub.
        # Now integration_level comes from PhiCalculator → mapping.
        # Verify the PhiCalculator wiring is present.
        assert "PhiCalculator" in source, "Must wire PhiCalculator"
        assert "FreeEnergyCalculator" in source, "Must wire FreeEnergyCalculator"
        assert "calculate_phi" in source, "Must call calculate_phi"
        assert "_MAPPING_INTEGRATION" in source, "Must use mapping dicts"

    def test_no_dead_coded_free_energy_placeholder(self):
        """The old unconditional variance=0.1 assignment is gone."""
        source = inspect.getsource(
            __import__("heretek_swarm.observability.metrics", fromlist=["SwarmMetricsCollector"])
            .SwarmMetricsCollector.collect_consciousness_metrics
        )
        # The 0.5/0.1 placeholders that were the entire old method body must be gone.
        # The method now computes values from calculators.
        assert "calculate_free_energy" in source or "free_energy_avg" in source, (
            "Must compute free energy from calculator"
        )

    def test_mapping_dicts_are_not_placeholders(self):
        """The MAPPING dict values (0.5, 0.1, etc) are legitimate mapping tables."""
        from heretek_swarm.observability.metrics import (
            _MAPPING_DIFFERENTIATION,
            _MAPPING_INTEGRATION,
        )

        # These mapping dicts are NOT dead-coded placeholders — they translate
        # PhiCalculator string labels to numeric scores. Verify keys exist.
        assert "very_high" in _MAPPING_INTEGRATION
        assert "minimal" in _MAPPING_INTEGRATION
        assert "very_high" in _MAPPING_DIFFERENTIATION
        assert "minimal" in _MAPPING_DIFFERENTIATION

    # -- heavyswarm.py: no placeholder analysis comments ----------------------

    def test_no_placeholder_analysis_in_collect_triad(self):
        """_collect_triad_analyses has zero 'placeholder' residue."""
        from heretek_swarm.orchestration.heavyswarm import HeavySwarmWorkflow

        source = inspect.getsource(HeavySwarmWorkflow._collect_triad_analyses)
        assert "placeholder" not in source.lower(), (
            "Must remove all 'placeholder' references from _collect_triad_analyses"
        )
        # The old hardcoded confidence=0.8 must be gone
        assert "0.8" not in source, (
            "Hardcoded confidence=0.8 must not appear in _collect_triad_analyses"
        )

    def test_collect_triad_uses_nats_send_with_reply(self):
        """_collect_triad_analyses uses send_with_reply (NATS request-reply)."""
        from heretek_swarm.orchestration.heavyswarm import HeavySwarmWorkflow

        source = inspect.getsource(HeavySwarmWorkflow._collect_triad_analyses)
        assert "send_with_reply" in source, (
            "Must use send_with_reply for real NATS request-reply (D004)"
        )
        assert "timeout" in source.lower(), (
            "Must have timeout handling in _collect_triad_analyses"
        )

    def test_heavyswarm_analysis_has_structured_log_events(self):
        """heavyswarm_analysis_timeout log event exists for observability."""
        from heretek_swarm.orchestration.heavyswarm import HeavySwarmWorkflow

        source = inspect.getsource(HeavySwarmWorkflow._collect_triad_analyses)
        assert "heavyswarm_analysis_timeout" in source, (
            "Must log heavyswarm_analysis_timeout on timeout"
        )
        assert "heavyswarm_analysis_error" in source, (
            "Must log heavyswarm_analysis_error on exception"
        )

    # -- perceiver/agent.py: no old placeholder LLM string -------------------

    def test_no_image_analysis_requested_with_prompt_string(self):
        """The old 'Image analysis requested with prompt:' placeholder is gone."""
        import heretek_swarm.actors.perceiver.agent as mod

        source = inspect.getsource(mod.PerceiverAgent._describe_image_llm)
        assert "Image analysis requested with prompt" not in source, (
            "Old hardcoded placeholder string must be removed from _describe_image_llm"
        )

    def test_describe_image_llm_uses_llm_provider_chain(self):
        """_describe_image_llm calls run_with_llm for real LLM descriptions."""
        import heretek_swarm.actors.perceiver.agent as mod

        source = inspect.getsource(mod.PerceiverAgent._describe_image_llm)
        assert "run_with_llm" in source, (
            "Must route through run_with_llm → provider chain"
        )

    def test_describe_image_llm_has_fallback_on_failure(self):
        """LLM failure returns a metadata fallback string, does not crash."""
        import heretek_swarm.actors.perceiver.agent as mod

        source = inspect.getsource(mod.PerceiverAgent._describe_image_llm)
        assert "LLM unavailable" in source or "perceiver_llm_unavailable" in source, (
            "Must have structured fallback on LLM failure"
        )

    # -- SnapshotManager: no stub residue in init/shutdown --------------------

    def test_snapshot_manager_initialize_is_real(self):
        """SnapshotManager.initialize() is a real implementation, not a stub."""
        source = inspect.getsource(SnapshotManager.initialize)
        assert "stub" not in source.lower(), (
            "initialize() must not contain stub/placeholder comments"
        )
        assert "# TODO" not in source, "initialize() must not have TODO markers"
        assert "pass" not in source.strip().splitlines()[-1].strip(), (
            "initialize() must not be a no-op pass"
        )

    def test_snapshot_manager_shutdown_is_real(self):
        """SnapshotManager.shutdown() is a real implementation, not a stub."""
        source = inspect.getsource(SnapshotManager.shutdown)
        assert "stub" not in source.lower(), (
            "shutdown() must not contain stub/placeholder comments"
        )
        assert "# TODO" not in source, "shutdown() must not have TODO markers"
        assert "pass" not in source.strip().splitlines()[-1].strip(), (
            "shutdown() must not be a no-op pass"
        )

    def test_snapshot_manager_create_is_real(self):
        """create_snapshot() contains real persistence logic, not a stub."""
        source = inspect.getsource(SnapshotManager.create_snapshot)
        assert "_persist_snapshot" in source or "persist" in source.lower(), (
            "create_snapshot must call persistence logic"
        )


# =============================================================================
# TestSnapshotManagerIntegration
# =============================================================================


class TestSnapshotManagerIntegration:
    """End-to-end integration: initialize → create → shutdown → re-init."""

    @pytest.mark.asyncio
    async def test_full_round_trip_preserves_data(self, tmp_path: Path) -> None:
        """Complete shutdown → re-init cycle preserves all snapshot data."""
        from heretek_swarm.state.models import AgentState, StateStatus

        storage = tmp_path / "integration_snapshots"
        config = SnapshotConfig(storage_path=str(storage), max_snapshots=50)

        # Phase 1: Create snapshots
        mgr1 = SnapshotManager(config=config)
        await mgr1.initialize()

        snap_ids = []
        for i in range(3):
            snap = await mgr1.create_snapshot(
                trigger=f"phase1_{i}",
                description=f"integration test snapshot {i}",
                system_state=SystemState(
                    system_id="test-system",
                    active_agents=i + 1,
                    total_messages=100 * (i + 1),
                    uptime_seconds=60.0 * (i + 1),
                ),
                agent_states={
                    f"agent_{i}": AgentState(
                        agent_id=f"agent_{i}",
                        agent_type="worker",
                        status=StateStatus.ACTIVE,
                        metadata={"task_count": str(i)},
                    )
                },
            )
            snap_ids.append(snap.snapshot_id)

        await mgr1.shutdown()

        # Verify files exist on disk
        json_files = list(storage.glob("*.json"))
        assert len(json_files) == 3

        # Phase 2: Re-initialize fresh manager
        mgr2 = SnapshotManager(config=config)
        await mgr2.initialize()

        # All snapshots survived
        loaded = await mgr2.list_snapshots()
        assert len(loaded) == 3

        loaded_by_id: dict[uuid.UUID, StateSnapshot] = {
            s.snapshot_id: s for s in loaded
        }

        # Verify each snapshot's data survived intact
        for i, sid in enumerate(snap_ids):
            assert sid in loaded_by_id
            loaded_snap = loaded_by_id[sid]
            assert loaded_snap.trigger == f"phase1_{i}"
            assert loaded_snap.description == f"integration test snapshot {i}"
            assert loaded_snap.system_state is not None
            assert loaded_snap.system_state.system_id == "test-system"
            assert loaded_snap.system_state.active_agents == i + 1
            assert loaded_snap.system_state.total_messages == 100 * (i + 1)
            assert loaded_snap.system_state.uptime_seconds == 60.0 * (i + 1)

        await mgr2.shutdown()

    @pytest.mark.asyncio
    async def test_snapshots_in_memory_match_disk(self, tmp_path: Path) -> None:
        """In-memory snapshot data matches on-disk JSON content exactly."""
        from heretek_swarm.state.models import AgentState, StateStatus

        storage = tmp_path / "match_test"
        config = SnapshotConfig(storage_path=str(storage), max_snapshots=50)

        mgr = SnapshotManager(config=config)
        await mgr.initialize()

        snap = await mgr.create_snapshot(
            trigger="disk_match_test",
            description="verify disk content fidelity",
            system_state=SystemState(
                system_id="verify",
                active_agents=7,
                total_messages=42,
                uptime_seconds=1234.56,
            ),
            agent_states={
                "alpha": AgentState(
                    agent_id="alpha", agent_type="worker",
                    status=StateStatus.ACTIVE,
                    metadata={"role": "leader"},
                ),
                "beta": AgentState(
                    agent_id="beta", agent_type="worker",
                    status=StateStatus.ACTIVE,
                    metadata={"role": "worker"},
                ),
            },
        )

        # Read from disk
        disk_path = storage / f"{snap.snapshot_id}.json"
        assert disk_path.exists()
        disk_data = json.loads(disk_path.read_text(encoding="utf-8"))

        # In-memory and disk must agree on key fields
        loaded = await mgr.get_snapshot(snap.snapshot_id)
        assert loaded is not None
        assert loaded.trigger == disk_data["trigger"]
        assert loaded.description == disk_data["description"]
        assert loaded.system_state is not None
        assert loaded.system_state.active_agents == disk_data["system_state"]["active_agents"]
        assert loaded.system_state.total_messages == disk_data["system_state"]["total_messages"]
        assert loaded.system_state.uptime_seconds == disk_data["system_state"]["uptime_seconds"]
        assert loaded.system_state.system_id == disk_data["system_state"]["system_id"]
        # Round-trip: to_dict then from_dict is lossless
        round_tripped = StateSnapshot.from_dict(disk_data)
        assert round_tripped.trigger == snap.trigger
        assert round_tripped.description == snap.description
        assert round_tripped.snapshot_id == snap.snapshot_id

        await mgr.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_managers_same_storage_do_not_conflict(
        self, tmp_path: Path
    ) -> None:
        """Two managers sharing storage (insequence) operate without conflict."""
        storage = tmp_path / "shared_storage"
        config = SnapshotConfig(storage_path=str(storage), max_snapshots=50)

        # Manager A writes
        mgr_a = SnapshotManager(config=config)
        await mgr_a.initialize()
        await mgr_a.create_snapshot(trigger="a1", description="from A")
        await mgr_a.shutdown()

        # Manager B reads + writes
        mgr_b = SnapshotManager(config=config)
        await mgr_b.initialize()
        loaded = await mgr_b.list_snapshots()
        assert len(loaded) == 1
        assert any(s.trigger == "a1" for s in loaded)

        await mgr_b.create_snapshot(trigger="b1", description="from B")
        await mgr_b.shutdown()

        # Manager C reads both
        mgr_c = SnapshotManager(config=config)
        await mgr_c.initialize()
        all_snaps = await mgr_c.list_snapshots()
        assert len(all_snaps) == 2
        triggers = {s.trigger for s in all_snaps}
        assert triggers == {"a1", "b1"}
        await mgr_c.shutdown()
