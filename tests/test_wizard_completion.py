"""
Tests for Wizard Completion Event Emission

Tests:
- WizardState tracks completion status
- SwarmEvent payload structure and serialization
- submit_config returns correct tier config
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.api.wizard import WizardState


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def wizard_state():
    """Create a fresh WizardState instance for testing."""
    return WizardState()


# =============================================================================
# Test: WizardState completion tracking
# =============================================================================

class TestWizardStateCompletion:
    """Test suite for WizardState completion tracking."""

    def test_wizard_state_set_completed(self, wizard_state):
        """Test wizard state can be marked completed."""
        assert wizard_state.is_completed() is False
        wizard_state.set_completed(True)
        assert wizard_state.is_completed() is True

    def test_wizard_state_clear(self, wizard_state):
        """Test wizard state can be cleared."""
        wizard_state.set_completed(True)
        wizard_state.clear()
        assert wizard_state.is_completed() is False

    def test_wizard_state_stores_tier_config(self, wizard_state):
        """Test wizard state stores tier configuration."""
        tier_config = {
            "tier": "standard",
            "agent_count": 5,
            "agents": ["coordinator", "coder"],
            "memory_enabled": True,
            "consciousness_enabled": False,
        }
        wizard_state.set_wizard_config(tier_config)

        stored_config = wizard_state.get_wizard_config()
        assert stored_config["tier"] == "standard"
        assert stored_config["agent_count"] == 5
        assert stored_config["agents"] == ["coordinator", "coder"]
        assert stored_config["memory_enabled"] is True
        assert stored_config["consciousness_enabled"] is False

    def test_wizard_state_stores_minimal_tier(self, wizard_state):
        """Test wizard state stores minimal tier config."""
        tier_config = {
            "tier": "minimal",
            "agent_count": 1,
            "agents": ["coordinator"],
            "memory_enabled": False,
            "consciousness_enabled": False,
        }
        wizard_state.set_wizard_config(tier_config)

        stored_config = wizard_state.get_wizard_config()
        assert stored_config["tier"] == "minimal"
        assert stored_config["agent_count"] == 1
        assert stored_config["agents"] == ["coordinator"]
        assert stored_config["memory_enabled"] is False
        assert stored_config["consciousness_enabled"] is False

    def test_wizard_state_stores_enhanced_tier(self, wizard_state):
        """Test wizard state stores enhanced tier config."""
        tier_config = {
            "tier": "enhanced",
            "agent_count": 11,
            "agents": [
                "coordinator", "coder", "examiner", "historian", "catalyst",
                "explorer", "dreamer", "echo", "metis", "nexus", "arbiter",
            ],
            "memory_enabled": True,
            "consciousness_enabled": True,
        }
        wizard_state.set_wizard_config(tier_config)

        stored_config = wizard_state.get_wizard_config()
        assert stored_config["tier"] == "enhanced"
        assert stored_config["agent_count"] == 11
        assert len(stored_config["agents"]) == 11
        assert stored_config["memory_enabled"] is True
        assert stored_config["consciousness_enabled"] is True


# =============================================================================
# Test: SwarmEvent payload structure
# =============================================================================

class TestSwarmEventPayload:
    """Test suite for SwarmEvent payload structure."""

    def test_event_payload_structure(self):
        """Test that SwarmEvent can be created with correct payload structure."""
        from heretek_swarm.infrastructure.nats.publisher import SwarmEvent

        event = SwarmEvent(
            event_type="wizard.completed",
            source_agent="wizard",
            payload={
                "tier_id": "standard",
                "agent_count": 5,
                "agents": ["coordinator", "coder"],
                "memory_enabled": True,
                "consciousness_enabled": False,
            },
        )

        assert event.event_type == "wizard.completed"
        assert event.source_agent == "wizard"
        assert event.payload["tier_id"] == "standard"
        assert event.payload["agent_count"] == 5
        assert event.payload["agents"] == ["coordinator", "coder"]
        assert event.payload["memory_enabled"] is True
        assert event.payload["consciousness_enabled"] is False

    def test_event_to_dict(self):
        """Test SwarmEvent serialization to dict."""
        from heretek_swarm.infrastructure.nats.publisher import SwarmEvent

        event = SwarmEvent(
            event_type="wizard.completed",
            source_agent="wizard",
            payload={"tier_id": "minimal"},
        )

        event_dict = event.to_dict()
        assert event_dict["event_type"] == "wizard.completed"
        assert event_dict["source_agent"] == "wizard"
        assert event_dict["payload"]["tier_id"] == "minimal"
        assert "timestamp" in event_dict

    def test_event_to_json(self):
        """Test SwarmEvent serialization to JSON."""
        from heretek_swarm.infrastructure.nats.publisher import SwarmEvent

        import json

        event = SwarmEvent(
            event_type="wizard.completed",
            source_agent="wizard",
            payload={"tier_id": "minimal"},
        )

        event_json = event.to_json()
        parsed = json.loads(event_json)
        assert parsed["event_type"] == "wizard.completed"
        assert parsed["source_agent"] == "wizard"

    def test_event_topic_routing(self):
        """Test that event topic is swarm.wizard.completed."""
        from heretek_swarm.infrastructure.nats.publisher import NATSPublisher, SwarmEvent

        publisher = NATSPublisher()
        event = SwarmEvent(
            event_type="wizard.completed",
            source_agent="wizard",
            payload={"tier_id": "standard"},
        )

        topic = publisher._get_topic(event.target_agent, event.event_type)
        assert topic == "swarm.wizard.completed"


# =============================================================================
# Test: submit_config integration
# =============================================================================

class TestSubmitConfigIntegration:
    """Integration tests for submit_config."""

    @pytest.mark.asyncio
    async def test_submit_config_returns_correct_tier(self):
        """Test that submit_config returns correct tier config in result."""
        from heretek_swarm.api.wizard import submit_config

        mock_service = MagicMock()
        mock_service.create_llm_provider = AsyncMock(return_value=MagicMock())
        mock_service.list_llm_providers = AsyncMock(return_value=[])
        mock_service.get_config_value = AsyncMock(return_value=None)

        wizard_state = WizardState()

        async def test_submit():
            with patch(
                "heretek_swarm.api.wizard.get_service",
                return_value=mock_service,
            ), patch(
                "heretek_swarm.api.wizard.get_wizard_state",
                return_value=wizard_state,
            ), patch(
                "heretek_swarm.api.wizard._emit_wizard_completed_event",
                new_callable=AsyncMock,
            ):
                result = await submit_config({
                    "providers": [],
                    "tier": "enhanced",
                    "preferences": {},
                })
            return result

        result = await test_submit()

        # Verify the tier config was returned correctly
        assert result["config"]["tier"] == "enhanced"
        assert result["config"]["agent_count"] == 11

    @pytest.mark.asyncio
    async def test_submit_config_marks_wizard_completed(self):
        """Test that submit_config marks wizard as completed."""
        from heretek_swarm.api.wizard import submit_config

        mock_service = MagicMock()
        mock_service.create_llm_provider = AsyncMock(return_value=MagicMock())
        mock_service.list_llm_providers = AsyncMock(return_value=[])
        mock_service.get_config_value = AsyncMock(return_value=None)

        wizard_state = WizardState()

        async def test_submit():
            with patch(
                "heretek_swarm.api.wizard.get_service",
                return_value=mock_service,
            ), patch(
                "heretek_swarm.api.wizard.get_wizard_state",
                return_value=wizard_state,
            ), patch(
                "heretek_swarm.api.wizard._emit_wizard_completed_event",
                new_callable=AsyncMock,
            ):
                result = await submit_config({
                    "providers": [],
                    "tier": "minimal",
                    "preferences": {},
                })
            return result

        result = await test_submit()

        # Verify wizard was marked completed
        assert wizard_state.is_completed() is True
        assert result["success"] is True
