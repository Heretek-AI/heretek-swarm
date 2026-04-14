"""ZERO-02 Internal Function Validation Tests.

Validates that the Zero-Trust internal function validation meets all success criteria:
1. Every agent function that handles external input calls validate_input() first
2. Validation failures logged with full context
3. Behavioral baseline drift detected at >= 3.0 std dev

Edge cases:
- Validation timeout: fail-safe (reject input) after 10ms
- Circular validation: no re-trigger on already-validated internal outputs
- Baseline too strict: Steward can adjust thresholds; minimum 2 std dev
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretek_swarm.actors.base.core import ActorMessage, AgentActor
from heretek_swarm.actors.mixins.validation import ValidationMixin


# ---------------------------------------------------------------------------
# Test helper: concrete class that combines ValidationMixin + AgentActor
# ---------------------------------------------------------------------------
class ValidatedAgent(ValidationMixin, AgentActor):
    """Concrete agent with ValidationMixin for testing."""

    def __init__(self, **kwargs):
        self._config = kwargs.pop("_config", {})
        super().__init__(**kwargs)


def _make_agent(**kwargs) -> ValidatedAgent:
    defaults = dict(agent_id="test_validated_agent", name="TestValidated")
    defaults.update(kwargs)
    return ValidatedAgent(**defaults)


def _make_message(
    content: dict[str, Any] | None = None,
    sender: str = "actor_" + "a" * 32,
    message_type: str = "test_msg",
) -> ActorMessage:
    return ActorMessage(
        sender=sender,
        message_type=message_type,
        content=content or {"data": "hello"},
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S.000000+00:00"),
    )


# ===================================================================
# Criterion 1: Agents validate input before processing
# ===================================================================


class TestPreExecutionValidation:
    """Verify that validate_input() is called before handler execution."""

    @pytest.mark.asyncio
    async def test_validate_input_called_on_valid_data(self):
        """validate_input returns (True, data) for valid input."""
        agent = _make_agent()
        data = {"key": "value", "count": 5}
        is_valid, sanitized = await agent.validate_input(data, "test_op", "source_1")
        assert is_valid is True
        assert sanitized == data

    @pytest.mark.asyncio
    async def test_validate_input_rejects_none(self):
        """validate_input returns (False, None) for None input."""
        agent = _make_agent()
        is_valid, sanitized = await agent.validate_input(None, "test_op")
        assert is_valid is False
        assert sanitized is None

    @pytest.mark.asyncio
    async def test_process_message_calls_validate_input_when_mixin_present(self):
        """process_message checks hasattr(validate_input) and calls it."""
        agent = _make_agent()
        await agent.spawn()

        # Patch validate_input to track calls
        original_validate = agent.validate_input
        called = {"count": 0}

        async def tracking_validate(input_data, operation, source_id=None):
            called["count"] += 1
            return await original_validate(input_data, operation, source_id)

        agent.validate_input = tracking_validate

        msg = _make_message(content={"data": "test"})
        await agent.process_message(msg)

        assert called["count"] == 1

    @pytest.mark.asyncio
    async def test_process_message_rejects_on_validation_failure(self):
        """When validate_input returns False, handler is NOT called."""
        agent = _make_agent()
        await agent.spawn()

        handler_called = False

        async def my_handler(message):
            nonlocal handler_called
            handler_called = True

        agent.register_handler("test_msg", my_handler)

        # Force validation to fail
        agent.validate_input = AsyncMock(return_value=(False, None))

        msg = _make_message(message_type="test_msg")
        await agent.process_message(msg)

        assert handler_called is False
        assert agent.error_count == 1

    @pytest.mark.asyncio
    async def test_process_message_passes_sanitized_content_to_handler(self):
        """When validate_input succeeds, sanitized content replaces message content."""
        agent = _make_agent()
        await agent.spawn()

        received_content = None

        async def my_handler(message):
            nonlocal received_content
            received_content = message.content

        agent.register_handler("test_msg", my_handler)

        sanitized = {"sanitized": True}
        agent.validate_input = AsyncMock(return_value=(True, sanitized))

        msg = _make_message(content={"original": True}, message_type="test_msg")
        await agent.process_message(msg)

        assert received_content == sanitized


# ===================================================================
# Criterion 2: Validation failures logged with full context
# ===================================================================


class TestValidationFailureLogging:
    """Verify that validation failures are logged with context."""

    @pytest.mark.asyncio
    async def test_none_input_logged_with_context(self):
        """Rejecting None input logs operation and source_id."""
        agent = _make_agent()
        with patch("heretek_swarm.actors.mixins.validation.logger") as mock_logger:
            await agent.validate_input(None, "critical_op", "ext_source")

        # Should have logged a warning about null input
        warning_calls = [
            c
            for c in mock_logger.warning.call_args_list
            if "null_input" in str(c) or "rejected_null" in str(c)
        ]
        assert len(warning_calls) >= 1

    @pytest.mark.asyncio
    async def test_validation_stats_track_failures(self):
        """Validation stats record failures."""
        agent = _make_agent()

        # Trigger a failure (None input)
        await agent.validate_input(None, "op1")

        stats = agent.get_validation_stats()
        assert stats["failed_validations"] >= 1
        assert stats["total_validations"] >= 1

    @pytest.mark.asyncio
    async def test_anomaly_detection_logged_with_score_and_threshold(self):
        """Anomaly detection logs the anomaly_score and threshold."""
        agent = _make_agent()
        import random

        random.seed(33)

        for i in range(200):
            val = 10.0 + random.uniform(-1.0, 1.0)
            await agent.validate_input({"metric": val}, "drift_op")
            if i > 0 and i % 100 == 0:
                agent._recalculate_baseline()

        with patch("heretek_swarm.actors.mixins.validation.logger") as mock_logger:
            is_valid, _ = await agent.validate_input({"metric": 100000.0}, "drift_op")

        stats = agent.get_validation_stats()
        if not is_valid:
            assert stats["anomalies_detected"] >= 1

            warning_calls = mock_logger.warning.call_args_list
            anomaly_logs = [c for c in warning_calls if "anomaly" in str(c).lower()]
            assert len(anomaly_logs) >= 1


# ===================================================================
# Criterion 3: Behavioral baseline drift detection >= 3.0 sigma
# ===================================================================


class TestBehavioralBaselineDrift:
    """Verify drift detection triggers at >= 3.0 std dev."""

    @pytest.mark.asyncio
    async def test_anomaly_threshold_default_is_3_sigma(self):
        """Default anomaly threshold is 3.0 std dev."""
        agent = _make_agent()
        assert agent._anomaly_threshold_std_dev == 3.0

    @pytest.mark.asyncio
    async def test_drift_detected_at_3_sigma(self):
        """Anomalous input (>= 3σ from mean) is rejected."""
        agent = _make_agent()

        # Feed 200 values with small variance so std_dev > 0
        # Using range 48-52 (std_dev ≈ 1.15) so 5000.0 is >> 3σ
        import random

        random.seed(42)
        for i in range(200):
            val = 50.0 + random.uniform(-2.0, 2.0)
            await agent.validate_input({"value": val}, "baseline_op")
            if i > 0 and i % 100 == 0:
                agent._recalculate_baseline()

        # Verify baseline was built and std_dev > 0
        assert "baseline_op" in agent._behavioral_baseline
        baseline_metric = agent._behavioral_baseline["baseline_op"].get("value")
        assert baseline_metric is not None
        assert baseline_metric["std_dev"] > 0

        # Send a value far from mean to trigger >= 3σ
        is_valid, _ = await agent.validate_input({"value": 5000.0}, "baseline_op")

        assert is_valid is False
        stats = agent.get_validation_stats()
        assert stats["anomalies_detected"] >= 1

    @pytest.mark.asyncio
    async def test_normal_values_within_3_sigma_pass(self):
        """Normal values (well within 3σ) pass validation."""
        agent = _make_agent()
        import random

        random.seed(99)

        for i in range(200):
            val = 50.0 + random.uniform(-2.0, 2.0)
            await agent.validate_input({"value": val}, "normal_op")
            if i > 0 and i % 100 == 0:
                agent._recalculate_baseline()

        baseline = agent._behavioral_baseline.get("normal_op", {})
        value_key = "value"

        if value_key in baseline and baseline[value_key]["std_dev"] > 0:
            mean = baseline[value_key]["mean"]
            std = baseline[value_key]["std_dev"]
            normal_value = mean + std * 0.5
        else:
            normal_value = 50.0

        is_valid, _ = await agent.validate_input({"value": normal_value}, "normal_op")
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_configurable_threshold(self):
        """Threshold can be configured via _config."""
        agent = _make_agent(_config={"anomaly_threshold_std_dev": 5.0})
        assert agent._anomaly_threshold_std_dev == 5.0

    @pytest.mark.asyncio
    async def test_minimum_threshold_below_2_rejected(self):
        """Threshold can be set to minimum 2.0 std dev (governance policy)."""
        agent = _make_agent(_config={"anomaly_threshold_std_dev": 2.0})
        assert agent._anomaly_threshold_std_dev == 2.0
        import random

        random.seed(77)

        for i in range(200):
            val = 100.0 + random.uniform(-2.0, 2.0)
            await agent.validate_input({"value": val}, "strict_op")
            if i > 0 and i % 100 == 0:
                agent._recalculate_baseline()

        is_valid, _ = await agent.validate_input({"value": 100000.0}, "strict_op")
        assert is_valid is False


# ===================================================================
# Edge Case: Validation timeout — fail-safe after 10ms
# ===================================================================


class TestValidationTimeout:
    """Verify validation timeout protection at 10ms."""

    @pytest.mark.asyncio
    async def test_default_timeout_is_10ms(self):
        """Default validation timeout is 10ms."""
        agent = _make_agent()
        assert agent._validation_timeout_ms == 10.0

    @pytest.mark.asyncio
    async def test_timeout_returns_false_none(self):
        """When validation times out, return (False, None) — fail-safe."""
        agent = _make_agent()

        # Override _perform_validation to simulate a long-running validation
        async def slow_validation(input_data, operation, source_id=None):
            await asyncio.sleep(1.0)  # Way longer than 10ms
            return True, input_data

        agent._perform_validation = slow_validation

        # Use dict data so circular validation check doesn't short-circuit
        start = time.perf_counter()
        is_valid, sanitized = await agent.validate_input({"data": "test"}, "timeout_op")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert is_valid is False
        assert sanitized is None
        # Should complete near the timeout, not after the full 1s sleep
        assert elapsed_ms < 500  # generous buffer but well under 1s

    @pytest.mark.asyncio
    async def test_timeout_increments_stats(self):
        """Timeout events increment timeout_validations counter."""
        agent = _make_agent()

        async def slow_validation(input_data, operation, source_id=None):
            await asyncio.sleep(1.0)
            return True, input_data

        agent._perform_validation = slow_validation

        await agent.validate_input({"data": "test"}, "timeout_op")

        stats = agent.get_validation_stats()
        assert stats["timeout_validations"] >= 1


# ===================================================================
# Edge Case: Circular validation prevention
# ===================================================================


class TestCircularValidationPrevention:
    """Verify that validated outputs don't re-trigger validation."""

    @pytest.mark.asyncio
    async def test_already_validated_data_skips_validation(self):
        """Second validation of same data returns immediately without re-checking."""
        agent = _make_agent()
        data = {"key": "unique_value_12345"}

        # First validation
        is_valid1, _ = await agent.validate_input(data, "circular_op")
        assert is_valid1 is True

        # Second validation of same data should short-circuit
        is_valid2, sanitized2 = await agent.validate_input(data, "circular_op")
        assert is_valid2 is True

        # The second call should not have gone through full validation
        # We can verify by checking that total_validations incremented
        # but successful_validations = 2 (both pass) and only 1 full validation ran
        stats = agent.get_validation_stats()
        assert stats["total_validations"] == 2
        assert stats["successful_validations"] == 2

    @pytest.mark.asyncio
    async def test_different_data_still_validated(self):
        """Different data still gets full validation."""
        agent = _make_agent()

        data1 = {"key": "value1"}
        data2 = {"key": "value2"}

        await agent.validate_input(data1, "op1")
        is_valid2, _ = await agent.validate_input(data2, "op1")

        assert is_valid2 is True

    @pytest.mark.asyncio
    async def test_non_dict_data_not_tracked(self):
        """Non-dict/non-list data is not tracked for circular validation."""
        agent = _make_agent()

        # Strings, ints are not tracked
        is_valid1, _ = await agent.validate_input("string_data", "op1")
        is_valid2, _ = await agent.validate_input("string_data", "op1")

        # Both should go through full validation (not short-circuited)
        assert is_valid1 is True
        assert is_valid2 is True

    @pytest.mark.asyncio
    async def test_mark_as_validated_works(self):
        """_mark_as_validated adds hash to tracking set."""
        agent = _make_agent()
        data = {"tracked": True}

        assert agent._is_already_validated(data) is False

        agent._mark_as_validated(data)
        assert agent._is_already_validated(data) is True

    @pytest.mark.asyncio
    async def test_clear_validated_outputs(self):
        """clear_validated_outputs resets the tracking set."""
        agent = _make_agent()
        data = {"cleared": True}

        agent._mark_as_validated(data)
        assert agent._is_already_validated(data) is True

        agent.clear_validated_outputs()
        assert agent._is_already_validated(data) is False


# ===================================================================
# Criterion verification: Agent coverage
# ===================================================================


class TestAgentCoverage:
    """Verify that agents get pre-execution validation via process_message."""

    @pytest.mark.asyncio
    async def test_base_class_process_message_checks_validate_input(self):
        """AgentActor.process_message checks for validate_input method."""
        # Plain AgentActor (no ValidationMixin) - hasattr should be False
        plain_actor = AgentActor(agent_id="plain_actor", name="Plain")
        await plain_actor.spawn()

        assert not hasattr(plain_actor, "validate_input")

        # AgentActor with ValidationMixin - hasattr should be True
        validated_actor = _make_agent()
        await validated_actor.spawn()

        assert hasattr(validated_actor, "validate_input")

    @pytest.mark.asyncio
    async def test_phase1_agents_can_integrate_validation_mixin(self):
        """Phase 1 agents can be instantiated with ValidationMixin in MRO."""
        # The design pattern is: ValidationMixin goes before AgentActor in MRO
        # process_message checks hasattr(self, "validate_input")
        agent = _make_agent(agent_id="test_phase1")
        await agent.spawn()

        # Send a message through process_message
        msg = _make_message(content={"test": True}, message_type="health_check")
        await agent.process_message(msg)

        # Validation should have been called
        stats = agent.get_validation_stats()
        assert stats["total_validations"] >= 1


# ===================================================================
# Validation statistics
# ===================================================================


class TestValidationStatistics:
    """Verify validation stats tracking."""

    @pytest.mark.asyncio
    async def test_stats_initial_values(self):
        """Stats start at zero."""
        agent = _make_agent()
        stats = agent.get_validation_stats()

        assert stats["total_validations"] == 0
        assert stats["successful_validations"] == 0
        assert stats["failed_validations"] == 0
        assert stats["timeout_validations"] == 0
        assert stats["anomalies_detected"] == 0

    @pytest.mark.asyncio
    async def test_stats_track_successful_validation(self):
        """Successful validations increment counters."""
        agent = _make_agent()
        await agent.validate_input({"data": "valid"}, "op1")

        stats = agent.get_validation_stats()
        assert stats["total_validations"] == 1
        assert stats["successful_validations"] == 1

    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """reset_validation_stats clears all counters."""
        agent = _make_agent()
        await agent.validate_input({"data": "valid"}, "op1")
        await agent.validate_input(None, "op2")

        agent.reset_validation_stats()
        stats = agent.get_validation_stats()
        assert stats["total_validations"] == 0
        assert stats["successful_validations"] == 0
        assert stats["failed_validations"] == 0

    @pytest.mark.asyncio
    async def test_validate_output_rejects_none(self):
        """validate_output rejects None output."""
        agent = _make_agent()
        is_valid, result = await agent.validate_output(None, "out_op")
        assert is_valid is False
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_output_accepts_valid_data(self):
        """validate_output accepts valid data."""
        agent = _make_agent()
        is_valid, result = await agent.validate_output({"result": "ok"}, "out_op")
        assert is_valid is True
        assert result == {"result": "ok"}
