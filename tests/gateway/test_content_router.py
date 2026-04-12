"""
Unit and Integration Tests for Content Router

Tests for content-based message routing with:
- Filter operators (eq, ne, contains, regex, gt, lt, in)
- Priority-based rule evaluation
- Subject pattern matching
- Rate limiting
- Prometheus metrics
- Performance benchmarks (<10ms overhead)
"""

import time
from unittest.mock import Mock

import pytest

from heretek_swarm.gateway.content_router import (
    ContentFilter,
    ContentRouter,
    FilterOperator,
    RouteDecision,
    RoutingRule,
    SafeJSONPath,
    reset_content_router,
)

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def content_router():
    """Create a fresh content router for each test."""
    from prometheus_client import CollectorRegistry

    reset_content_router()
    # Use a fresh registry for each test to avoid metric registration conflicts
    return ContentRouter(
        rate_limit_per_second=10000,  # High limit for tests
        metrics_registry=CollectorRegistry()
    )


@pytest.fixture
def sample_routing_rules():
    """Sample routing rules for testing."""
    return [
        # High priority task routing
        RoutingRule(
            id="high-priority-tasks",
            name="High Priority Tasks",
            priority=100,
            subject_pattern="task.*",
            content_filters=[
                ContentFilter(field="$.priority", operator=FilterOperator.GT, value=8)
            ],
            target_channel="coordinator.input",
            target_agents=["coordinator"],
            enabled=True,
        ),
        # Error analysis routing
        RoutingRule(
            id="error-analysis",
            name="Error Analysis",
            priority=90,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.type", operator=FilterOperator.EQ, value="error"),
                ContentFilter(field="$.severity", operator=FilterOperator.IN, value=["critical", "high"])
            ],
            target_channel="sentinel.input",
            target_agents=["sentinel"],
            enabled=True,
        ),
        # Simple subject-only routing
        RoutingRule(
            id="health-checks",
            name="Health Checks",
            priority=50,
            subject_pattern="health.*",
            content_filters=[],
            target_channel="system.health",
            target_agents=["monitor"],
            enabled=True,
        ),
    ]


# =============================================================================
# ContentFilter Tests
# =============================================================================

class TestContentFilter:
    """Tests for ContentFilter validation and creation."""

    def test_create_valid_filter(self):
        """Test creating a valid content filter."""
        filter = ContentFilter(
            field="$.priority",
            operator=FilterOperator.GT,
            value=5
        )
        assert filter.field == "$.priority"
        assert filter.operator == FilterOperator.GT
        assert filter.value == 5

    def test_create_filter_with_string_operator(self):
        """Test creating filter with string operator (auto-converted)."""
        filter = ContentFilter(
            field="$.name",
            operator="eq",
            value="test"
        )
        assert filter.operator == FilterOperator.EQ

    def test_invalid_jsonpath(self):
        """Test that invalid JSONPath raises error."""
        with pytest.raises(ValueError, match="Invalid JSONPath"):
            ContentFilter(
                field="priority",  # Missing $ prefix
                operator=FilterOperator.EQ,
                value=5
            )

    def test_invalid_operator(self):
        """Test that invalid operator raises error."""
        with pytest.raises(ValueError, match="Invalid operator"):
            ContentFilter(
                field="$.priority",
                operator="invalid_op",
                value=5
            )

    def test_invalid_regex_pattern(self):
        """Test that invalid regex pattern raises error."""
        with pytest.raises(ValueError, match="Invalid regex"):
            ContentFilter(
                field="$.message",
                operator=FilterOperator.REGEX,
                value="[invalid(regex"
            )


# =============================================================================
# RoutingRule Tests
# =============================================================================

class TestRoutingRule:
    """Tests for RoutingRule validation and creation."""

    def test_create_valid_rule(self):
        """Test creating a valid routing rule."""
        rule = RoutingRule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            subject_pattern="test.*",
            content_filters=[],
            target_channel="test.channel",
            target_agents=["agent1"],
        )
        assert rule.id == "test-rule"
        assert rule.subject_pattern == "test.*"
        assert rule.enabled is True

    def test_invalid_subject_pattern_special_chars(self):
        """Test that dangerous special chars in pattern are rejected."""
        with pytest.raises(ValueError, match="Invalid subject pattern"):
            RoutingRule(
                id="bad-rule",
                name="Bad Rule",
                priority=50,
                subject_pattern="test;DROP TABLE",  # SQL injection attempt
                content_filters=[],
                target_channel="test.channel",
                target_agents=[],
            )

    def test_subject_pattern_with_wildcard(self):
        """Test valid wildcard patterns."""
        rule = RoutingRule(
            id="wildcard-rule",
            name="Wildcard Rule",
            priority=50,
            subject_pattern="task.*.high",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )
        assert rule.matches_subject("task.urgent.high")
        assert rule.matches_subject("task.low.high")
        assert not rule.matches_subject("task.urgent.low")

    def test_subject_pattern_exact_match(self):
        """Test exact subject matching."""
        rule = RoutingRule(
            id="exact-rule",
            name="Exact Rule",
            priority=50,
            subject_pattern="health.check",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )
        assert rule.matches_subject("health.check")
        assert not rule.matches_subject("health.check.extra")
        assert not rule.matches_subject("health")


# =============================================================================
# SafeJSONPath Tests
# =============================================================================

class TestSafeJSONPath:
    """Tests for safe JSONPath extraction."""

    def test_extract_root_field(self):
        """Test extracting root level field."""
        data = {"priority": 10, "type": "task"}
        success, value = SafeJSONPath.extract(data, "$.priority")
        assert success is True
        assert value == 10

    def test_extract_nested_field(self):
        """Test extracting nested field."""
        data = {"task": {"priority": 10, "name": "test"}}
        success, value = SafeJSONPath.extract(data, "$.task.priority")
        assert success is True
        assert value == 10

    def test_extract_array_index(self):
        """Test extracting array element by index."""
        data = {"items": ["a", "b", "c"]}
        success, value = SafeJSONPath.extract(data, "$.items[1]")
        assert success is True
        assert value == "b"

    def test_field_not_found(self):
        """Test when field doesn't exist."""
        data = {"priority": 10}
        success, value = SafeJSONPath.extract(data, "$.nonexistent")
        assert success is False
        assert "not found" in value.lower()

    def test_invalid_path_no_dollar(self):
        """Test invalid path without $ prefix."""
        data = {"priority": 10}
        success, value = SafeJSONPath.extract(data, "priority")
        assert success is False
        assert "must start with" in value.lower()

    def test_array_index_out_of_bounds(self):
        """Test array index out of bounds."""
        data = {"items": ["a", "b"]}
        success, value = SafeJSONPath.extract(data, "$.items[5]")
        assert success is False
        assert "out of bounds" in value.lower()


# =============================================================================
# ContentRouter Routing Tests
# =============================================================================

class TestContentRouterRouting:
    """Tests for content router message routing."""

    def test_route_with_matching_rule(self, content_router, sample_routing_rules):
        """Test routing when a rule matches."""
        # Add rules
        for rule in sample_routing_rules:
            content_router.add_rule(rule)

        # Route a high priority task
        decision = content_router.route(
            subject="task.create",
            payload={"priority": 9, "type": "task"},
            correlation_id="test-123",
        )

        assert decision.decision == RouteDecision.MATCHED
        assert decision.matched_rule.id == "high-priority-tasks"
        assert decision.correlation_id == "test-123"
        assert decision.evaluation_time_ms >= 0

    def test_route_with_no_matching_rule(self, content_router, sample_routing_rules):
        """Test routing when no rule matches."""
        # Add rules
        for rule in sample_routing_rules:
            content_router.add_rule(rule)

        # Route a low priority task (shouldn't match high priority rule)
        decision = content_router.route(
            subject="task.create",
            payload={"priority": 3, "type": "task"},
            correlation_id="test-456",
        )

        assert decision.decision == RouteDecision.NO_MATCH
        assert decision.matched_rule is None

    def test_route_with_error_type(self, content_router, sample_routing_rules):
        """Test routing error messages to sentinel."""
        # Add rules
        for rule in sample_routing_rules:
            content_router.add_rule(rule)

        # Route an error message
        decision = content_router.route(
            subject="system.alert",
            payload={"type": "error", "severity": "critical"},
            correlation_id="test-789",
        )

        assert decision.decision == RouteDecision.MATCHED
        assert decision.matched_rule.id == "error-analysis"
        assert "sentinel" in decision.matched_rule.target_agents

    def test_route_with_multiple_content_filters(self, content_router):
        """Test routing with multiple filters (all must match)."""
        rule = RoutingRule(
            id="multi-filter",
            name="Multi Filter Rule",
            priority=100,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.type", operator=FilterOperator.EQ, value="alert"),
                ContentFilter(field="$.priority", operator=FilterOperator.GT, value=5),
            ],
            target_channel="alerts.channel",
            target_agents=["alert-handler"],
        )
        content_router.add_rule(rule)

        # Both filters match
        decision = content_router.route(
            subject="system.event",
            payload={"type": "alert", "priority": 8},
        )
        assert decision.decision == RouteDecision.MATCHED
        assert decision.filters_matched == 2

        # Only first filter matches
        decision = content_router.route(
            subject="system.event",
            payload={"type": "alert", "priority": 2},
        )
        assert decision.decision == RouteDecision.NO_MATCH

    def test_route_priority_ordering(self, content_router):
        """Test that higher priority rules are evaluated first."""
        # Add rules in reverse priority order
        low_priority = RoutingRule(
            id="low",
            name="Low Priority",
            priority=10,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.value", operator=FilterOperator.EQ, value="test")
            ],
            target_channel="low.channel",
            target_agents=["low-agent"],
        )
        high_priority = RoutingRule(
            id="high",
            name="High Priority",
            priority=100,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.value", operator=FilterOperator.EQ, value="test")
            ],
            target_channel="high.channel",
            target_agents=["high-agent"],
        )

        content_router.add_rule(low_priority)
        content_router.add_rule(high_priority)

        # Should match high priority rule first
        decision = content_router.route(
            subject="any.subject",
            payload={"value": "test"},
        )

        assert decision.decision == RouteDecision.MATCHED
        assert decision.matched_rule.id == "high"


# =============================================================================
# Filter Operator Tests
# =============================================================================

class TestFilterOperators:
    """Tests for all filter operators."""

    def test_operator_eq(self, content_router):
        """Test exact match operator."""
        rule = RoutingRule(
            id="eq-test",
            name="EQ Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.status", operator=FilterOperator.EQ, value="active")
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"status": "active"})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"status": "inactive"})
        assert decision.decision == RouteDecision.NO_MATCH

    def test_operator_ne(self, content_router):
        """Test not equal operator."""
        rule = RoutingRule(
            id="ne-test",
            name="NE Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.status", operator=FilterOperator.NE, value="error")
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"status": "active"})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"status": "error"})
        assert decision.decision == RouteDecision.NO_MATCH

    def test_operator_contains(self, content_router):
        """Test string contains operator."""
        rule = RoutingRule(
            id="contains-test",
            name="Contains Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.message", operator=FilterOperator.CONTAINS, value="error")
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"message": "An error occurred"})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"message": "All good"})
        assert decision.decision == RouteDecision.NO_MATCH

    def test_operator_regex(self, content_router):
        """Test regex match operator."""
        rule = RoutingRule(
            id="regex-test",
            name="Regex Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.email", operator=FilterOperator.REGEX, value=r".+@.+\..+")
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"email": "user@example.com"})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"email": "invalid"})
        assert decision.decision == RouteDecision.NO_MATCH

    def test_operator_gt(self, content_router):
        """Test greater than operator."""
        rule = RoutingRule(
            id="gt-test",
            name="GT Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.score", operator=FilterOperator.GT, value=50)
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"score": 75})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"score": 50})
        assert decision.decision == RouteDecision.NO_MATCH

    def test_operator_lt(self, content_router):
        """Test less than operator."""
        rule = RoutingRule(
            id="lt-test",
            name="LT Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.attempts", operator=FilterOperator.LT, value=3)
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"attempts": 2})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"attempts": 3})
        assert decision.decision == RouteDecision.NO_MATCH

    def test_operator_in(self, content_router):
        """Test value in list operator."""
        rule = RoutingRule(
            id="in-test",
            name="IN Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.category", operator=FilterOperator.IN, value=["A", "B", "C"])
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"category": "B"})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"category": "D"})
        assert decision.decision == RouteDecision.NO_MATCH

    def test_operator_exists(self, content_router):
        """Test field exists operator."""
        rule = RoutingRule(
            id="exists-test",
            name="Exists Test",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.optional_field", operator=FilterOperator.EXISTS, value=True)
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        decision = content_router.route("test", {"optional_field": "value"})
        assert decision.decision == RouteDecision.MATCHED

        decision = content_router.route("test", {"other_field": "value"})
        assert decision.decision == RouteDecision.NO_MATCH


# =============================================================================
# Rule Management Tests
# =============================================================================

class TestRuleManagement:
    """Tests for rule CRUD operations."""

    def test_add_rule(self, content_router):
        """Test adding a rule."""
        rule = RoutingRule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            subject_pattern="test.*",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )

        result = content_router.add_rule(rule)
        assert result is True

        # Verify rule exists
        retrieved = content_router.get_rule("test-rule")
        assert retrieved is not None
        assert retrieved.name == "Test Rule"

    def test_add_duplicate_rule(self, content_router):
        """Test that adding duplicate rule fails."""
        rule = RoutingRule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            subject_pattern="test.*",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )

        assert content_router.add_rule(rule) is True
        assert content_router.add_rule(rule) is False

    def test_remove_rule(self, content_router):
        """Test removing a rule."""
        rule = RoutingRule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            subject_pattern="test.*",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )

        content_router.add_rule(rule)
        result = content_router.remove_rule("test-rule")
        assert result is True

        # Verify rule is gone
        retrieved = content_router.get_rule("test-rule")
        assert retrieved is None

    def test_enable_disable_rule(self, content_router):
        """Test enabling and disabling rules."""
        rule = RoutingRule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            subject_pattern="test.*",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )

        content_router.add_rule(rule)

        # Disable rule
        assert content_router.disable_rule("test-rule") is True
        retrieved = content_router.get_rule("test-rule")
        assert retrieved.enabled is False

        # Enable rule
        assert content_router.enable_rule("test-rule") is True
        retrieved = content_router.get_rule("test-rule")
        assert retrieved.enabled is True

    def test_list_rules(self, content_router):
        """Test listing rules."""
        # Add multiple rules
        for i in range(3):
            rule = RoutingRule(
                id=f"rule-{i}",
                name=f"Rule {i}",
                priority=i * 10,
                subject_pattern="test.*",
                content_filters=[],
                target_channel="test.channel",
                target_agents=[],
            )
            content_router.add_rule(rule)

        rules = content_router.list_rules()
        assert len(rules) == 3

        # Check sorting by priority (descending)
        assert rules[0]["priority"] == 20
        assert rules[2]["priority"] == 0


# =============================================================================
# Statistics and Metrics Tests
# =============================================================================

class TestStatistics:
    """Tests for routing statistics."""

    def test_get_stats(self, content_router):
        """Test getting router statistics."""
        stats = content_router.get_stats()

        assert "messages_evaluated" in stats
        assert "messages_matched" in stats
        assert "messages_no_match" in stats
        assert "active_rules" in stats
        assert "total_rules" in stats

    def test_stats_update_after_routing(self, content_router):
        """Test that stats update after routing."""
        rule = RoutingRule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            subject_pattern="*",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        # Initial stats
        initial_stats = content_router.get_stats()
        initial_evaluated = initial_stats["messages_evaluated"]

        # Route messages
        content_router.route("test", {"value": 1})
        content_router.route("test", {"value": 2})

        # Updated stats
        updated_stats = content_router.get_stats()
        assert updated_stats["messages_evaluated"] == initial_evaluated + 2


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance tests for routing overhead."""

    def test_routing_latency_under_10ms(self, content_router):
        """Test that routing completes in under 10ms."""
        # Add several rules
        for i in range(10):
            rule = RoutingRule(
                id=f"rule-{i}",
                name=f"Rule {i}",
                priority=i * 10,
                subject_pattern="test.*",
                content_filters=[
                    ContentFilter(field="$.value", operator=FilterOperator.GT, value=i)
                ],
                target_channel="test.channel",
                target_agents=[],
            )
            content_router.add_rule(rule)

        # Measure routing time
        times = []
        for _ in range(100):
            start = time.time()
            content_router.route(
                "test.subject",
                {"value": 15, "extra": "data" * 100}  # Some payload
            )
            elapsed_ms = (time.time() - start) * 1000
            times.append(elapsed_ms)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Average should be well under 10ms
        assert avg_time < 10, f"Average routing time {avg_time}ms exceeds 10ms"

        # Even max should be reasonable
        assert max_time < 50, f"Max routing time {max_time}ms exceeds 50ms"

    def test_routing_with_complex_payload(self, content_router):
        """Test routing performance with complex nested payload."""
        rule = RoutingRule(
            id="complex-rule",
            name="Complex Rule",
            priority=50,
            subject_pattern="*",
            content_filters=[
                ContentFilter(field="$.data.nested.value", operator=FilterOperator.GT, value=50)
            ],
            target_channel="test.channel",
            target_agents=[],
        )
        content_router.add_rule(rule)

        # Complex nested payload
        payload = {
            "header": {"version": "1.0", "timestamp": time.time()},
            "data": {
                "nested": {
                    "value": 75,
                    "array": [1, 2, 3, 4, 5],
                    "object": {"a": 1, "b": 2}
                }
            },
            "metadata": {"source": "test", "tags": ["a", "b", "c"]}
        }

        start = time.time()
        decision = content_router.route("test.subject", payload)
        elapsed_ms = (time.time() - start) * 1000

        assert decision.decision == RouteDecision.MATCHED
        assert elapsed_ms < 10, f"Routing time {elapsed_ms}ms exceeds 10ms"


# =============================================================================
# Rate Limiting Tests
# =============================================================================

class TestRateLimiting:
    """Tests for rate limiting protection."""

    def test_rate_limit_exceeded(self):
        """Test that rate limiting blocks excessive requests."""
        # Create router with very low rate limit
        router = ContentRouter(rate_limit_per_second=5)

        # Add a rule
        rule = RoutingRule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            subject_pattern="*",
            content_filters=[],
            target_channel="test.channel",
            target_agents=[],
        )
        router.add_rule(rule)

        # Send requests up to limit
        for i in range(5):
            decision = router.route("test", {"value": i})
            assert decision.decision != RouteDecision.ERROR

        # Next request should be rate limited
        decision = router.route("test", {"value": 99})
        assert decision.decision == RouteDecision.ERROR

    def test_rate_limit_recovery(self):
        """Test that rate limit resets after time window."""
        from prometheus_client import CollectorRegistry

        router = ContentRouter(
            rate_limit_per_second=2,
            metrics_registry=CollectorRegistry()
        )

        # Hit rate limit (no rules, so NO_MATCH)
        router.route("test", {"value": 1})
        router.route("test", {"value": 2})

        # Third request should be rate limited
        decision3 = router.route("test", {"value": 3})
        assert decision3.decision == RouteDecision.ERROR

        # Wait for window to reset (rate limit window is 1 second)
        time.sleep(1.2)

        # Should work again (no rules, so NO_MATCH)
        decision4 = router.route("test", {"value": 4})
        assert decision4.decision == RouteDecision.NO_MATCH


# =============================================================================
# Integration Tests with EventMesh
# =============================================================================

class TestEventMeshIntegration:
    """Integration tests for EventMesh with content routing."""

    def test_eventmesh_uses_content_router(self, content_router):
        """Test that EventMesh uses content router when available."""
        from heretek_swarm.gateway.event_mesh import EventMesh

        # Add a rule
        rule = RoutingRule(
            id="mesh-rule",
            name="Mesh Rule",
            priority=50,
            subject_pattern="test.*",
            content_filters=[
                ContentFilter(field="$.priority", operator=FilterOperator.GT, value=5)
            ],
            target_channel="test.channel",
            target_agents=["agent-1"],
        )
        content_router.add_rule(rule)

        # Create EventMesh with content router
        event_mesh = EventMesh(content_router=content_router)

        # Verify router is accessible
        assert event_mesh.get_content_router() is content_router

    @pytest.mark.asyncio
    async def test_eventmesh_broadcast_with_routing(self, content_router):
        """Test EventMesh broadcast with content-based routing."""
        from heretek_swarm.gateway.event_mesh import EventMesh

        # Add routing rule
        rule = RoutingRule(
            id="broadcast-rule",
            name="Broadcast Rule",
            priority=50,
            subject_pattern="alert.*",
            content_filters=[
                ContentFilter(field="$.severity", operator=FilterOperator.EQ, value="high")
            ],
            target_channel="alerts.high",
            target_agents=["sentinel"],
        )
        content_router.add_rule(rule)

        # Create EventMesh
        event_mesh = EventMesh(content_router=content_router)

        # Mock WebSocket client
        mock_websocket = Mock()
        mock_websocket.client_state = Mock()
        mock_websocket.client_state.disconnecting = False

        # Register mock client
        await event_mesh.register("sentinel", mock_websocket)
        await event_mesh.register("other-agent", mock_websocket)

        # Broadcast with subject and payload for routing
        import json
        message = json.dumps({"severity": "high", "type": "alert"}).encode()

        result = await event_mesh.broadcast(
            message,
            subject="alert.system",
            payload={"severity": "high", "type": "alert"},
            correlation_id="test-broadcast",
        )

        # Verify routing was applied
        assert result.get("routed") is True
        assert "routing_decision" in result
