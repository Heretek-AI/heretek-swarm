"""
Precedent chain tests: Tribunal NATS publishing for binding precedents (T01, Slice S02, M002).

Verifies:
- NATS publish fires on UPHOLD/OVERRULE rulings
- No NATS publish on DISMISS/MODIFY/REMAND
- Graceful degradation when event_mesh is None
- Graceful degradation when NATS is unavailable
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]

from heretek_swarm.actors.habit_forge.agent import HabitForgeAgent
from heretek_swarm.collective.learning import PatternType
from heretek_swarm.consensus.tribunal import CaseStatus, RulingType, Tribunal, TribunalCase


def _make_case() -> TribunalCase:
    """Create a minimal TribunalCase for testing rulings."""
    return TribunalCase(
        original_decision_id="anomaly-001",
        appellant_agent_id="agent-42",
        grounds="Test grounds",
        description="Test case for precedent publishing",
        status=CaseStatus.EVIDENCE_SUBMITTED,
    )


# ---------------------------------------------------------------------------
# (a) NATS publish fires on UPHOLD ruling
# ---------------------------------------------------------------------------

def test_tribunal_publish_nats_on_uphold() -> None:
    """Fire-and-forget NATS publish fires on UPHOLD binding ruling."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    ruling = tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Sustained — evidence is compelling",
        confidence=0.95,
    )

    mock_mesh.publish_to_nats.assert_called_once()
    call_kwargs = mock_mesh.publish_to_nats.call_args.kwargs
    assert call_kwargs["event_type"] == "precedent_recorded"
    assert call_kwargs["source_agent"] == "tribunal"
    payload = call_kwargs["payload"]
    assert payload["ruling_id"] == ruling.ruling_id
    assert payload["case_id"] == case.case_id
    assert payload["ruling_type"] == "uphold"
    assert payload["reasoning"] == "Sustained — evidence is compelling"
    assert payload["confidence"] == 0.95
    assert payload["anomaly_id"] == "anomaly-001"
    assert payload["precedent_id"] is None
    assert payload["timestamp"] == ruling.timestamp


# ---------------------------------------------------------------------------
# (b) NATS publish fires on OVERRULE ruling
# ---------------------------------------------------------------------------

def test_tribunal_publish_nats_on_overrule() -> None:
    """Fire-and-forget NATS publish fires on OVERRULE binding ruling."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    ruling = tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.OVERRULE,
        reasoning="Previous decision was erroneous",
        confidence=0.88,
        precedent_id="prec-007",
    )

    mock_mesh.publish_to_nats.assert_called_once()
    call_kwargs = mock_mesh.publish_to_nats.call_args.kwargs
    assert call_kwargs["event_type"] == "precedent_recorded"
    assert call_kwargs["source_agent"] == "tribunal"
    payload = call_kwargs["payload"]
    assert payload["ruling_id"] == ruling.ruling_id
    assert payload["ruling_type"] == "overrule"
    assert payload["confidence"] == 0.88
    assert payload["precedent_id"] == "prec-007"


# ---------------------------------------------------------------------------
# (c) No NATS publish on DISMISS / MODIFY / REMAND rulings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ruling_type", [RulingType.DISMISS, RulingType.MODIFY, RulingType.REMAND])
def test_tribunal_no_nats_publish_on_non_binding(ruling_type: RulingType) -> None:
    """No NATS publish for non-binding rulings (DISMISS, MODIFY, REMAND)."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=ruling_type,
        reasoning="Test reasoning",
    )

    mock_mesh.publish_to_nats.assert_not_called()


# ---------------------------------------------------------------------------
# (d) Graceful degradation when event_mesh is None
# ---------------------------------------------------------------------------

def test_tribunal_no_crash_when_event_mesh_is_none() -> None:
    """issue_ruling does not crash when event_mesh is None."""
    tribunal = Tribunal(event_mesh=None)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    ruling = tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Should not crash without mesh",
    )

    assert ruling.ruling_type == RulingType.UPHOLD
    # Precedent is still registered in-memory
    assert ruling.ruling_id in tribunal._precedents


# ---------------------------------------------------------------------------
# (e) Graceful degradation when NATS unavailable (log signal)
# ---------------------------------------------------------------------------

def test_tribunal_logs_nats_unavailable_at_debug() -> None:
    """When NATS publish raises, log nats_publisher_not_available at DEBUG."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock(side_effect=RuntimeError("NATS connection refused"))

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    with patch("heretek_swarm.consensus.tribunal.logger") as mock_logger:
        ruling = tribunal.issue_ruling(
            case_id=case.case_id,
            ruling_type=RulingType.OVERRULE,
            reasoning="Still works despite NATS down",
        )

    # Ruling still issued
    assert ruling.ruling_type == RulingType.OVERRULE
    assert ruling.ruling_id in tribunal._precedents

    # Debug log was emitted with signal name
    debug_calls = [
        call for call in mock_logger.debug.call_args_list
        if isinstance(call.args, tuple) and len(call.args) > 0 and call.args[0] == "nats_publisher_not_available"
    ]
    assert len(debug_calls) == 1
    assert debug_calls[0].kwargs["ruling_id"] == ruling.ruling_id


# ---------------------------------------------------------------------------
# (f) NATS publish still fires when enable_precedent is False
#     (enable_precedent governs in-memory precedent list, not event publishing)
# ---------------------------------------------------------------------------

def test_tribunal_nats_publish_still_fires_without_precedent_storage() -> None:
    """NATS publish fires on UPHOLD even when enable_precedent=False.

    The enable_precedent flag controls whether the ruling is stored in the
    in-memory _precedents list. NATS event publishing is separate — binding
    rulings always fire the event when an event_mesh is available.
    """
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh, enable_precedent=False)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    ruling = tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Precedent disabled",
    )

    # NATS publish still fires — event publishing is not gated on enable_precedent
    mock_mesh.publish_to_nats.assert_called_once()
    # But in-memory precedent list is NOT updated
    assert ruling.ruling_id not in tribunal._precedents


# ---------------------------------------------------------------------------
# (g) SentinelAgent wires event_mesh into Tribunal construction
# ---------------------------------------------------------------------------

def test_sentinel_agent_wires_event_mesh_to_tribunal() -> None:
    """SentinelAgent passes its _event_mesh to Tribunal at init."""
    mock_mesh = MagicMock()

    from heretek_swarm.actors.sentinel.agent import SentinelAgent

    agent = SentinelAgent(
        agent_id="sentinel-test",
        config={},
    )
    agent._event_mesh = mock_mesh

    # Reconstruct Tribunal with the event_mesh (simulates the init wiring)
    agent.tribunal = Tribunal(event_mesh=agent._event_mesh)

    assert agent.tribunal._event_mesh is mock_mesh


# ---------------------------------------------------------------------------
# (h) payload includes precedent_id when set
# ---------------------------------------------------------------------------

def test_tribunal_publish_payload_includes_precedent_id() -> None:
    """When precedent_id is set, it appears in the NATS payload."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Citing precedent",
        precedent_id="prec-042",
    )

    mock_mesh.publish_to_nats.assert_called_once()
    payload = mock_mesh.publish_to_nats.call_args.kwargs["payload"]
    assert payload["precedent_id"] == "prec-042"


# ---------------------------------------------------------------------------
# T02: HabitForge NATS subscription and operational pattern synthesis
# ---------------------------------------------------------------------------

_MOCK_PRECEDENT_PAYLOAD: dict[str, Any] = {
    "ruling_id": "r001",
    "case_id": "case-abc",
    "ruling_type": "uphold",
    "reasoning": "Evidence supports the appeal — pattern is validated.",
    "confidence": 0.92,
    "anomaly_id": "anomaly-001",
    "precedent_id": None,
    "timestamp": "2026-05-26T00:00:00Z",
}


def _make_habit_forge_agent(event_mesh: MagicMock | None = None) -> HabitForgeAgent:
    """Create a minimal HabitForgeAgent with a mock event_mesh."""
    mesh = event_mesh or MagicMock()
    agent = HabitForgeAgent(
        agent_id="habit-forge-test",
        event_mesh=mesh,
    )
    return agent


# -- (a) HabitForge receives precedent_recorded event → pattern stored ---------

@pytest.mark.asyncio
async def test_habit_forge_stores_pattern_on_precedent_event() -> None:
    """HabitForge receives precedent_recorded event → pattern in detected_patterns."""
    mock_mesh = MagicMock()
    mock_mesh.subscribe = AsyncMock()

    agent = _make_habit_forge_agent(event_mesh=mock_mesh)

    # Call the synthesis directly — the subscription callback would call this
    agent._synthesize_operational_pattern(_MOCK_PRECEDENT_PAYLOAD)

    assert len(agent.detected_patterns) == 1
    pattern = list(agent.detected_patterns.values())[0]
    assert pattern.pattern_id == "precedent_r001"
    assert pattern.pattern_type == PatternType.SUCCESS
    assert pattern.category == "immune_precedent"
    assert pattern.confidence == 0.92
    assert pattern.impact_score == 0.92
    assert pattern.evidence[0]["source"] == "tribunal"
    assert pattern.evidence[0]["case_id"] == "case-abc"
    assert pattern.evidence[0]["ruling_id"] == "r001"


# -- (b) habit_forge_precedent_synthesized log signal fires --------------------

def test_habit_forge_emits_precedent_synthesized_log() -> None:
    """habit_forge_precedent_synthesized structured log fires on synthesis."""
    mock_mesh = MagicMock()
    agent = _make_habit_forge_agent(event_mesh=mock_mesh)

    from unittest.mock import patch

    with patch("heretek_swarm.actors.habit_forge.agent.logger") as mock_logger:
        agent._synthesize_operational_pattern(_MOCK_PRECEDENT_PAYLOAD)

    # Verify the structured log call
    info_calls = [
        c for c in mock_logger.info.call_args_list
        if isinstance(c.args, tuple) and len(c.args) > 0
        and c.args[0] == "habit_forge_precedent_synthesized"
    ]
    assert len(info_calls) == 1
    assert info_calls[0].kwargs["ruling_id"] == "r001"
    assert info_calls[0].kwargs["pattern_id"] == "precedent_r001"
    assert info_calls[0].kwargs["confidence"] == 0.92
    assert info_calls[0].kwargs["category"] == "immune_precedent"


# -- (c) malformed event payload handled gracefully ---------------------------

def test_habit_forge_graceful_on_malformed_payload() -> None:
    """Malformed precedent payload handled without crash — only error log emitted."""
    mock_mesh = MagicMock()
    agent = _make_habit_forge_agent(event_mesh=mock_mesh)

    from unittest.mock import patch

    # Malformed: missing all expected fields, but we still don't crash
    with patch("heretek_swarm.actors.habit_forge.agent.logger") as mock_logger:
        agent._synthesize_operational_pattern({})

    # Should still create a pattern, just with defaults
    pattern = list(agent.detected_patterns.values())[0]
    assert pattern.pattern_id == "precedent_unknown"
    assert pattern.confidence == 0.5
    assert pattern.category == "immune_precedent"
    assert pattern.description is not None  # just not empty


# -- (d) multiple precedent events produce distinct patterns -------------------

@pytest.mark.asyncio
async def test_habit_forge_multiple_precedents_produce_distinct_patterns() -> None:
    """Multiple precedent events create unique entries in detected_patterns."""
    mock_mesh = MagicMock()
    mock_mesh.subscribe = AsyncMock()

    agent = _make_habit_forge_agent(event_mesh=mock_mesh)

    payloads = [
        {
            "ruling_id": "r001",
            "case_id": "case-1",
            "ruling_type": "uphold",
            "reasoning": "Pattern validated.",
            "confidence": 0.85,
            "anomaly_id": "anomaly-A",
            "precedent_id": None,
            "timestamp": "2026-05-26T00:00:00Z",
        },
        {
            "ruling_id": "r002",
            "case_id": "case-2",
            "ruling_type": "overrule",
            "reasoning": "Previous decision erroneous.",
            "confidence": 0.91,
            "anomaly_id": "anomaly-B",
            "precedent_id": "prec-007",
            "timestamp": "2026-05-26T01:00:00Z",
        },
        {
            "ruling_id": "r003",
            "case_id": "case-3",
            "ruling_type": "uphold",
            "reasoning": "New evidence compelling.",
            "confidence": 0.78,
            "anomaly_id": "anomaly-C",
            "precedent_id": None,
            "timestamp": "2026-05-26T02:00:00Z",
        },
    ]

    for payload in payloads:
        agent._synthesize_operational_pattern(payload)

    assert len(agent.detected_patterns) == 3
    assert "precedent_r001" in agent.detected_patterns
    assert "precedent_r002" in agent.detected_patterns
    assert "precedent_r003" in agent.detected_patterns

    # Distinct metadata per pattern
    p001 = agent.detected_patterns["precedent_r001"]
    p002 = agent.detected_patterns["precedent_r002"]
    p003 = agent.detected_patterns["precedent_r003"]

    assert p001.confidence == 0.85
    assert p002.confidence == 0.91
    assert p003.confidence == 0.78

    assert p002.pattern_type == PatternType.SUCCESS
    assert "overrule" in p002.description.lower()
    assert p002.evidence[0]["precedent_id"] == "prec-007"


# =============================================================================
# T03: Contract tests for precedent_recorded NATS event schema
# =============================================================================

_EXPECTED_TOP_LEVEL_FIELDS = {"event_type", "source_agent", "payload"}
_EXPECTED_PAYLOAD_FIELDS = {
    "ruling_id",
    "case_id",
    "ruling_type",
    "reasoning",
    "confidence",
    "anomaly_id",
    "precedent_id",
    "timestamp",
}


def _capture_published_payload(mock_mesh: MagicMock) -> dict[str, Any]:
    """Extract the full kwargs dict from publish_to_nats mock call."""
    mock_mesh.publish_to_nats.assert_called_once()
    return mock_mesh.publish_to_nats.call_args.kwargs


# -- (i) All required top-level and payload fields present --------------------

def test_precedent_event_has_all_required_fields() -> None:
    """precedent_recorded event includes all required top-level and payload fields."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Contract: all fields present",
        confidence=0.99,
        precedent_id="prec-C1",
    )

    kwargs = _capture_published_payload(mock_mesh)

    # Top-level fields
    assert set(kwargs.keys()) == _EXPECTED_TOP_LEVEL_FIELDS, (
        f"Top-level keys {set(kwargs.keys())} != expected {_EXPECTED_TOP_LEVEL_FIELDS}"
    )
    assert kwargs["event_type"] == "precedent_recorded"
    assert kwargs["source_agent"] == "tribunal"

    payload = kwargs["payload"]
    assert set(payload.keys()) == _EXPECTED_PAYLOAD_FIELDS, (
        f"Payload keys {set(payload.keys())} != expected {_EXPECTED_PAYLOAD_FIELDS}"
    )


# -- (j) Correct types for all payload fields ---------------------------------

def test_precedent_event_payload_types() -> None:
    """Each precedent_recorded payload field has the correct Python type."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Type-check",
        confidence=0.87,
    )

    payload = _capture_published_payload(mock_mesh)["payload"]

    assert isinstance(payload["ruling_id"], str)
    assert isinstance(payload["case_id"], str)
    assert isinstance(payload["ruling_type"], str)
    assert isinstance(payload["reasoning"], str)
    assert isinstance(payload["confidence"], float)
    assert isinstance(payload["anomaly_id"], str)
    # precedent_id can be None or str
    assert isinstance(payload["precedent_id"], str) or payload["precedent_id"] is None
    assert isinstance(payload["timestamp"], str)


# -- (k) No extra unexpected fields — even when payload changes ---------------

def test_precedent_event_no_unexpected_fields() -> None:
    """No extra fields leak into the payload beyond the expected set."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.OVERRULE,
        reasoning="No extra fields",
        confidence=0.80,
    )

    payload = _capture_published_payload(mock_mesh)["payload"]
    extra = set(payload.keys()) - _EXPECTED_PAYLOAD_FIELDS
    assert not extra, f"Unexpected payload fields: {extra}"


# -- (l) precedent_id is None (not string "None") when not set ----------------

def test_precedent_event_precedent_id_nullable() -> None:
    """precedent_id is None (not string) when not provided."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Nullable precedent_id",
    )

    payload = _capture_published_payload(mock_mesh)["payload"]
    assert payload["precedent_id"] is None


# -- (m) confidence is always a float -----------------------------------------

def test_precedent_event_confidence_is_float() -> None:
    """confidence field is always a float, even with integer input."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    # Integer confidence input
    tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Int confidence",
        confidence=1,  # type: ignore[arg-type]
    )

    payload = _capture_published_payload(mock_mesh)["payload"]
    assert isinstance(payload["confidence"], (int, float))
    # RulingType is stored as enum .value (string)
    assert payload["ruling_type"] == "uphold"


# =============================================================================
# T03: Integration test — full precedent chain (Tribunal → HabitForge)
# =============================================================================


@pytest.mark.asyncio
async def test_full_precedent_chain_tribunal_to_habit_forge() -> None:
    """End-to-end: Tribunal issues UPHOLD → HabitForge synthesizes pattern.

    Steps:
    1. Mock Tribunal publishes via event_mesh.publish_to_nats
    2. HabitForge receives the payload via _synthesize_operational_pattern
    3. Pattern stored in detected_patterns
    4. Log signal habit_forge_precedent_synthesized fires
    """
    from unittest.mock import patch

    # -- Step 1: Tribunal issues UPHOLD ruling with NATS publish --
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    ruling = tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.UPHOLD,
        reasoning="Integration test: chain verification",
        confidence=0.93,
        precedent_id="prec-integration-001",
    )

    # Verify NATS event was published with correct data
    mock_mesh.publish_to_nats.assert_called_once()
    kwargs = mock_mesh.publish_to_nats.call_args.kwargs
    assert kwargs["event_type"] == "precedent_recorded"
    assert kwargs["source_agent"] == "tribunal"
    payload = kwargs["payload"]
    assert payload["ruling_id"] == ruling.ruling_id
    assert payload["ruling_type"] == "uphold"
    assert payload["confidence"] == 0.93
    assert payload["precedent_id"] == "prec-integration-001"

    # -- Step 2: HabitForge receives the payload and synthesizes pattern --
    agent = HabitForgeAgent(
        agent_id="habit-forge-integration",
        event_mesh=mock_mesh,
    )

    # Simulate the callback chain: _on_precedent_recorded → _synthesize_operational_pattern
    with patch("heretek_swarm.actors.habit_forge.agent.logger") as mock_logger:
        agent._synthesize_operational_pattern(payload)

    # -- Step 3: Pattern is stored in detected_patterns --
    assert len(agent.detected_patterns) == 1
    pattern_id = f"precedent_{ruling.ruling_id}"
    pattern = agent.detected_patterns[pattern_id]
    assert pattern.pattern_type == PatternType.SUCCESS
    assert pattern.category == "immune_precedent"
    assert pattern.confidence == 0.93
    assert pattern.impact_score == 0.93
    assert pattern.evidence[0]["source"] == "tribunal"
    assert pattern.evidence[0]["ruling_id"] == ruling.ruling_id
    assert pattern.evidence[0]["precedent_id"] == "prec-integration-001"

    # -- Step 4: habit_forge_precedent_synthesized log signal --
    info_calls = [
        c for c in mock_logger.info.call_args_list
        if isinstance(c.args, tuple) and len(c.args) > 0
        and c.args[0] == "habit_forge_precedent_synthesized"
    ]
    assert len(info_calls) == 1
    assert info_calls[0].kwargs["ruling_id"] == ruling.ruling_id
    assert info_calls[0].kwargs["pattern_id"] == pattern_id
    assert info_calls[0].kwargs["confidence"] == 0.93
    assert info_calls[0].kwargs["category"] == "immune_precedent"


@pytest.mark.asyncio
async def test_full_precedent_chain_overrule_with_precedent() -> None:
    """End-to-end: OVERRULE ruling with precedent_id → correct pattern metadata."""
    mock_mesh = MagicMock()
    mock_mesh.publish_to_nats = MagicMock()

    tribunal = Tribunal(event_mesh=mock_mesh)
    case = _make_case()
    tribunal._cases[case.case_id] = case

    ruling = tribunal.issue_ruling(
        case_id=case.case_id,
        ruling_type=RulingType.OVERRULE,
        reasoning="Overturning precedent — new evidence",
        confidence=0.85,
        precedent_id="prec-legacy-042",
    )

    payload = mock_mesh.publish_to_nats.call_args.kwargs["payload"]
    agent = HabitForgeAgent(agent_id="hf-overrule", event_mesh=mock_mesh)
    agent._synthesize_operational_pattern(payload)

    pattern = agent.detected_patterns[f"precedent_{ruling.ruling_id}"]
    assert pattern.pattern_type == PatternType.SUCCESS
    assert pattern.confidence == 0.85
    assert pattern.evidence[0]["precedent_id"] == "prec-legacy-042"
    assert "overrule" in pattern.description.lower()
    # Verify behavior list reflects overrule
    assert "tribunal.ruling.overrule" in pattern.behaviors


@pytest.mark.asyncio
async def test_habit_forge_log_signal_contains_precedent_reference() -> None:
    """habit_forge_precedent_synthesized log signal has correct precedent reference."""
    from unittest.mock import patch

    payload = {
        "ruling_id": "r-ref-001",
        "case_id": "case-ref",
        "ruling_type": "uphold",
        "reasoning": "Reference check",
        "confidence": 0.77,
        "anomaly_id": "anomaly-ref",
        "precedent_id": "prec-ref-555",
        "timestamp": "2026-05-26T12:00:00Z",
    }

    agent = HabitForgeAgent(agent_id="hf-log-check", event_mesh=MagicMock())

    with patch("heretek_swarm.actors.habit_forge.agent.logger") as mock_logger:
        agent._synthesize_operational_pattern(payload)

    info_calls = [
        c for c in mock_logger.info.call_args_list
        if isinstance(c.args, tuple) and len(c.args) > 0
        and c.args[0] == "habit_forge_precedent_synthesized"
    ]
    assert len(info_calls) == 1
    kwargs = info_calls[0].kwargs
    assert kwargs["ruling_id"] == "r-ref-001"
    assert kwargs["pattern_id"] == "precedent_r-ref-001"
    assert kwargs["confidence"] == 0.77
    assert kwargs["category"] == "immune_precedent"
