"""
Workflow Validator Tests

Tests for the workflow validator module covering:
- Disconnected node detection
- Circular dependency detection
- Missing required connections
- Invalid agent types
- Resource conflicts
- All validation error codes
"""

import pytest

from heretek_swarm.workflow.validator import (
    REGISTERED_AGENT_TYPES,
    REGISTERED_NODE_TYPES,
    ErrorCodes,
    ValidationError,
    ValidationResult,
    WorkflowValidator,
    validate_workflow,
    validate_workflow_strict,
)


class TestWorkflowValidator:
    """Test workflow validation functionality."""

    def test_valid_workflow(self):
        """Test validation of a valid workflow."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward"}},
                {"id": "node2", "type": "tool", "data": {"toolType": "code_execution"}},
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node2"},
            ],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_disconnected_node(self):
        """Test detection of disconnected nodes."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward"}},
                {"id": "node2", "type": "tool", "data": {"toolType": "code_execution"}},
                {"id": "node3", "type": "memory", "data": {"memoryType": "ephemeral"}},  # Disconnected
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node2"},
            ],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.DISCONNECTED_NODE for e in result.errors)

    def test_circular_dependency(self):
        """Test detection of circular dependencies."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward"}},
                {"id": "node2", "type": "tool", "data": {"toolType": "code_execution"}},
                {"id": "node3", "type": "memory", "data": {"memoryType": "ephemeral"}},
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node2"},
                {"id": "edge2", "source": "node2", "target": "node3"},
                {"id": "edge3", "source": "node3", "target": "node1"},  # Creates cycle
            ],
        }

        validator = WorkflowValidator(allow_cycles=False)
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.CIRCULAR_DEPENDENCY for e in result.errors)

    def test_circular_dependency_allowed(self):
        """Test that cycles are allowed when configured."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward"}},
                {"id": "node2", "type": "tool", "data": {"toolType": "code_execution"}},
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node2"},
                {"id": "edge2", "source": "node2", "target": "node1"},  # Creates cycle
            ],
        }

        validator = WorkflowValidator(allow_cycles=True)
        result = validator.validate(workflow)

        # Should not have circular dependency error
        assert not any(e.code == ErrorCodes.CIRCULAR_DEPENDENCY for e in result.errors)

    def test_invalid_agent_type(self):
        """Test detection of invalid agent types."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "invalid_agent"}},
            ],
            "edges": [],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.INVALID_AGENT_TYPE for e in result.errors)

    def test_valid_agent_types(self):
        """Test that all registered agent types are valid."""
        for agent_type in REGISTERED_AGENT_TYPES:
            workflow = {
                "id": f"test-{agent_type}",
                "name": "Test Workflow",
                "nodes": [
                    {"id": "node1", "type": "agent", "data": {"agentType": agent_type}},
                ],
                "edges": [],
            }

            validator = WorkflowValidator()
            result = validator.validate(workflow)

            # Should not have invalid agent type error
            assert not any(e.code == ErrorCodes.INVALID_AGENT_TYPE for e in result.errors)

    def test_invalid_node_type(self):
        """Test detection of invalid node types."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "invalid_node_type"},
            ],
            "edges": [],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.INVALID_NODE_TYPE for e in result.errors)

    def test_valid_node_types(self):
        """Test that all registered node types are valid."""
        for node_type in REGISTERED_NODE_TYPES:
            workflow = {
                "id": f"test-{node_type}",
                "name": "Test Workflow",
                "nodes": [
                    {"id": "node1", "type": node_type},
                ],
                "edges": [],
            }

            validator = WorkflowValidator()
            result = validator.validate(workflow)

            # Should not have invalid node type error
            assert not any(e.code == ErrorCodes.INVALID_NODE_TYPE for e in result.errors)

    def test_edge_to_nonexistent_node(self):
        """Test detection of edges connecting to non-existent nodes."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward"}},
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "nonexistent"},
            ],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.INVALID_EDGE_CONNECTION for e in result.errors)

    def test_duplicate_node_id(self):
        """Test detection of duplicate node IDs."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward"}},
                {"id": "node1", "type": "tool", "data": {"toolType": "code_execution"}},  # Duplicate
            ],
            "edges": [],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.DUPLICATE_NODE_ID for e in result.errors)

    def test_duplicate_edge_id(self):
        """Test detection of duplicate edge IDs."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent"},
                {"id": "node2", "type": "tool"},
                {"id": "node3", "type": "memory"},
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node2"},
                {"id": "edge1", "source": "node2", "target": "node3"},  # Duplicate
            ],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.DUPLICATE_EDGE_ID for e in result.errors)

    def test_self_loop(self):
        """Test detection of self-loops."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward"}},
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node1"},  # Self-loop
            ],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.INVALID_EDGE_CONNECTION for e in result.errors)
        assert "Self-loop" in str(result.errors[0].message)

    def test_decision_node_missing_input(self):
        """Test that decision nodes require input connections."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "decision", "data": {"condition": "true"}},
            ],
            "edges": [],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.MISSING_REQUIRED_INPUT for e in result.errors)

    def test_resource_conflict_warning(self):
        """Test detection of resource conflicts."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent", "data": {"agentType": "steward", "resourceId": "res1"}},
                {"id": "node2", "type": "agent", "data": {"agentType": "alpha", "resourceId": "res1"}},  # Same resource
            ],
            "edges": [],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        # Resource conflicts are warnings, not errors
        assert any(w.code == ErrorCodes.RESOURCE_CONFLICT for w in result.warnings)

    def test_no_start_node(self):
        """Test detection of workflows without a start node."""
        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "agent"},
                {"id": "node2", "type": "tool"},
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node2"},
                {"id": "edge2", "source": "node2", "target": "node1"},  # Cycle - no start
            ],
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        assert result.valid is False
        assert any(e.code == ErrorCodes.INVALID_START_NODE for e in result.errors)

    def test_degree_limits(self):
        """Test validation of node connection limits."""
        # Create a node with too many incoming connections
        nodes = [{"id": f"node{i}", "type": "agent"} for i in range(15)]
        nodes.append({"id": "target", "type": "tool"})

        edges = [
            {"id": f"edge{i}", "source": f"node{i}", "target": "target"}
            for i in range(15)
        ]

        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": nodes,
            "edges": edges,
        }

        validator = WorkflowValidator(max_in_degree=10)
        result = validator.validate(workflow)

        assert result.valid is False
        assert any("maximum input connections" in e.message.lower() for e in result.errors)

    def test_complex_graph_info(self):
        """Test that complex graphs generate info messages."""
        # Create a large workflow
        nodes = [{"id": f"node{i}", "type": "agent"} for i in range(60)]
        edges = [
            {"id": f"edge{i}", "source": f"node{i}", "target": f"node{i+1}"}
            for i in range(59)
        ]

        workflow = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": nodes,
            "edges": edges,
        }

        validator = WorkflowValidator()
        result = validator.validate(workflow)

        # Should have info about complex graph
        assert any(i.code == ErrorCodes.COMPLEX_GRAPH for i in result.info)

    def test_validation_result_to_dict(self):
        """Test ValidationResult serialization."""
        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    severity="error",
                    code=ErrorCodes.DISCONNECTED_NODE,
                    message="Test error",
                    node_id="node1",
                    suggestion="Fix it"
                )
            ],
            warnings=[],
            info=[]
        )

        result_dict = result.to_dict()

        assert result_dict["valid"] is False
        assert len(result_dict["errors"]) == 1
        assert result_dict["errors"][0]["code"] == ErrorCodes.DISCONNECTED_NODE
        assert result_dict["errors"][0]["node_id"] == "node1"

    def test_convenience_functions(self):
        """Test validate_workflow and validate_workflow_strict functions."""
        workflow = {
            "id": "test",
            "nodes": [{"id": "n1", "type": "invalid"}],
            "edges": []
        }

        # Test validate_workflow
        result = validate_workflow(workflow)
        assert isinstance(result, ValidationResult)

        # Test validate_workflow_strict
        result = validate_workflow_strict(workflow)
        assert isinstance(result, ValidationResult)


class TestErrorCodes:
    """Test error code constants."""

    def test_error_codes_defined(self):
        """Test that all expected error codes are defined."""
        expected_codes = [
            "DISCONNECTED_NODE",
            "CIRCULAR_DEPENDENCY",
            "MISSING_REQUIRED_INPUT",
            "INVALID_AGENT_TYPE",
            "INVALID_NODE_TYPE",
            "INVALID_EDGE_CONNECTION",
            "RESOURCE_CONFLICT",
            "DUPLICATE_NODE_ID",
            "DUPLICATE_EDGE_ID",
            "UNREACHABLE_NODE",
            "DEAD_END_NODE",
            "INVALID_START_NODE",
        ]

        for code in expected_codes:
            assert hasattr(ErrorCodes, code)
            assert getattr(ErrorCodes, code) == code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
