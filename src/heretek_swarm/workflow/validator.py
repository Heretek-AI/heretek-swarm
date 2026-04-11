"""
Workflow Validator - Validate workflow graphs before execution

Provides comprehensive validation for visual workflows including:
- Disconnected node detection
- Circular dependency detection
- Missing required connections
- Invalid agent types
- Resource conflicts

Inspired by LangGraph workflow validation patterns.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

import structlog

_logger = structlog.get_logger(__name__)


class ValidationErrorSeverity(str, Enum):
    """Severity levels for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """
    Validation error representation.
    
    Attributes:
        severity: Error severity level
        code: Error code identifier
        message: Human-readable error message
        node_id: Optional node ID associated with error
        edge_id: Optional edge ID associated with error
        suggestion: Optional suggestion for fixing the error
    """
    severity: Literal['error', 'warning', 'info']
    code: str
    message: str
    node_id: Optional[str] = None
    edge_id: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "node_id": self.node_id,
            "edge_id": self.edge_id,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """
    Result of workflow validation.
    
    Attributes:
        valid: Whether workflow passed validation
        errors: List of validation errors
        warnings: List of validation warnings
        info: List of informational messages
    """
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": [i.to_dict() for i in self.info],
        }


# =============================================================================
# Error Codes
# =============================================================================

class ErrorCodes:
    """Standard error codes for workflow validation."""
    # Structure errors
    DISCONNECTED_NODE = "DISCONNECTED_NODE"
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"
    MISSING_REQUIRED_INPUT = "MISSING_REQUIRED_INPUT"
    MISSING_REQUIRED_OUTPUT = "MISSING_REQUIRED_OUTPUT"

    # Configuration errors
    INVALID_AGENT_TYPE = "INVALID_AGENT_TYPE"
    INVALID_NODE_TYPE = "INVALID_NODE_TYPE"
    INVALID_EDGE_CONNECTION = "INVALID_EDGE_CONNECTION"
    MISSING_NODE_CONFIG = "MISSING_NODE_CONFIG"

    # Resource errors
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    DUPLICATE_NODE_ID = "DUPLICATE_NODE_ID"
    DUPLICATE_EDGE_ID = "DUPLICATE_EDGE_ID"

    # Execution errors
    UNREACHABLE_NODE = "UNREACHABLE_NODE"
    DEAD_END_NODE = "DEAD_END_NODE"
    INVALID_START_NODE = "INVALID_START_NODE"

    # Warnings
    UNUSED_OUTPUT = "UNUSED_OUTPUT"
    ORPHANED_NODE = "ORPHANED_NODE"
    COMPLEX_GRAPH = "COMPLEX_GRAPH"


# =============================================================================
# Registered Agent Types
# =============================================================================

REGISTERED_AGENT_TYPES = {
    'steward', 'alpha', 'beta', 'charlie',
    'historian', 'explorer', 'examiner', 'coder',
    'dreamer', 'empath', 'sentinel', 'sentinel-prime',
    'metis', 'nexus', 'perceiver', 'chronos',
    'catalyst', 'coordinator', 'arbiter', 'prism',
    'habit-forge', 'custom'
}

REGISTERED_NODE_TYPES = {
    'agent', 'tool', 'memory', 'decision',
    'connector', 'llm', 'input', 'output', 'template'
}


# =============================================================================
# Workflow Validator
# =============================================================================

class WorkflowValidator:
    """
    Validates workflow graphs for structural and configuration errors.
    
    Usage:
        _validator = WorkflowValidator()
        _result = validator.validate(workflow_definition)
        if not result.valid:
            for error in result.errors:
                print(f"{error.code}: {error.message}")
    """

    def __init__(self, allow_cycles: bool, max_in_degree: int, max_out_degree: int):
        """
        Initialize workflow validator.
        
        Args:
            allow_cycles: Whether to allow circular dependencies (default: False)
            max_in_degree: Maximum incoming connections per node (default: 10)
            max_out_degree: Maximum outgoing connections per node (default: 10)
        """
        self.allow_cycles = allow_cycles
        self.max_in_degree = max_in_degree
        self.max_out_degree = max_out_degree

    def validate(self, workflow_definition: Dict[str, Any]) -> ValidationResult:
        """
        Validate a workflow definition.
        
        Args:
            workflow_definition: Workflow definition with nodes and edges
            
        Returns:
            ValidationResult with errors, warnings, and info messages
        """
        _result = ValidationResult(valid=True)

        _nodes = workflow_definition.get("nodes", [])
        _edges = workflow_definition.get("edges", [])

        # Run all validators
        self._validate_duplicate_ids(nodes, edges, result)
        self._validate_node_types(nodes, result)
        self._validate_agent_types(nodes, result)
        self._validate_edge_connections(nodes, edges, result)
        self._validate_disconnected_nodes(nodes, edges, result)
        self._validate_circular_dependencies(nodes, edges, result)
        self._validate_required_connections(nodes, edges, result)
        self._validate_resource_conflicts(nodes, result)
        self._validate_degree_limits(nodes, edges, result)
        self._validate_start_node(nodes, edges, result)

        # Check for warnings
        self._check_orphaned_nodes(nodes, edges, result)
        self._check_unused_outputs(nodes, edges, result)
        self._check_graph_complexity(nodes, edges, result)

        # Update validity
        result.valid = len(result.errors) == 0

        return result

    def _validate_duplicate_ids(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Check for duplicate node and edge IDs."""
        _node_ids = set()
        _edge_ids = set()

        for node in nodes:
            _node_id = node.get("id")
            if node_id in node_ids:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.DUPLICATE_NODE_ID,
                    _message = f"Duplicate node ID: {node_id}",
                    _node_id = node_id,
                    _suggestion = "Ensure each node has a unique ID"
                ))
            node_ids.add(node_id)

        for edge in edges:
            _edge_id = edge.get("id")
            if edge_id in edge_ids:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.DUPLICATE_EDGE_ID,
                    _message = f"Duplicate edge ID: {edge_id}",
                    _edge_id = edge_id,
                    _suggestion = "Ensure each edge has a unique ID"
                ))
            edge_ids.add(edge_id)

    def _validate_node_types(self, nodes: List[Dict], result: ValidationResult) -> None:
        """Validate node types are registered."""
        for node in nodes:
            _node_type = node.get("type")
            if node_type and node_type not in REGISTERED_NODE_TYPES:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.INVALID_NODE_TYPE,
                    _message = f"Invalid node type: {node_type}",
                    _node_id = node.get("id"),
                    _suggestion = f"Valid node types are: {', '.join(REGISTERED_NODE_TYPES)}"
                ))

    def _validate_agent_types(self, nodes: List[Dict], result: ValidationResult) -> None:
        """Validate agent types are registered."""
        for node in nodes:
            if node.get("type") == "agent":
                _data = node.get("data", {})
                _agent_type = data.get("agentType")

                if agent_type and agent_type not in REGISTERED_AGENT_TYPES:
                    result.errors.append(ValidationError(
                        _severity = "error",
                        _code = ErrorCodes.INVALID_AGENT_TYPE,
                        _message = f"Invalid agent type: {agent_type}",
                        _node_id = node.get("id"),
                        _suggestion = f"Valid agent types are: {', '.join(REGISTERED_AGENT_TYPES)}"
                    ))

    def _validate_edge_connections(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Validate edges connect existing nodes."""
        _node_ids = {node.get("id") for node in nodes}

        for edge in edges:
            _source = edge.get("source")
            _target = edge.get("target")

            if source not in node_ids:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.INVALID_EDGE_CONNECTION,
                    _message = f"Edge source node does not exist: {source}",
                    _edge_id = edge.get("id"),
                    _suggestion = "Connect edge to an existing node"
                ))

            if target not in node_ids:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.INVALID_EDGE_CONNECTION,
                    _message = f"Edge target node does not exist: {target}",
                    _edge_id = edge.get("id"),
                    _suggestion = "Connect edge to an existing node"
                ))

            # Self-loops are errors unless explicitly allowed
            if source == target:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.INVALID_EDGE_CONNECTION,
                    _message = f"Self-loop detected: {source} -> {source}",
                    _edge_id = edge.get("id"),
                    _node_id = source,
                    _suggestion = "Remove self-loop or use a proper cycle pattern"
                ))

    def _validate_disconnected_nodes(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Check for nodes with no connections."""
        if len(nodes) <= 1:
            return

        _connected_nodes = set()

        for edge in edges:
            connected_nodes.add(edge.get("source"))
            connected_nodes.add(edge.get("target"))

        for node in nodes:
            _node_id = node.get("id")
            if node_id not in connected_nodes:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.DISCONNECTED_NODE,
                    _message = f"Node has no input or output connections",
                    _node_id = node_id,
                    _suggestion = "Connect the node to the workflow or remove it"
                ))

    def _validate_circular_dependencies(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Detect circular dependencies in the workflow graph."""
        if self.allow_cycles:
            return

        # Build adjacency list
        graph: Dict[str, List[str]] = {node.get("id"): [] for node in nodes}
        for edge in edges:
            _source = edge.get("source")
            _target = edge.get("target")
            if source in graph:
                graph[source].append(target)

        # Detect cycles using DFS
        _visited = set()
        _rec_stack = set()
        _cycle_path = []

        def has_cycle(node_id: str, path: List[str]) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    _cycle_start = path.index(neighbor)
                    cycle_path.extend(path[cycle_start:])
                    cycle_path.append(neighbor)
                    return True

            path.pop()
            rec_stack.remove(node_id)
            return False

        for node in nodes:
            _node_id = node.get("id")
            if node_id not in visited:
                if has_cycle(node_id, []):
                    result.errors.append(ValidationError(
                        _severity = "error",
                        _code = ErrorCodes.CIRCULAR_DEPENDENCY,
                        _message = f"Circular dependency detected: {' -> '.join(cycle_path)}",
                        _node_id = cycle_path[0] if cycle_path else None,
                        _suggestion = "Remove or break the cycle by reordering nodes"
                    ))
                    break

    def _validate_required_connections(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Validate nodes have required inputs/outputs."""
        # Build connection maps
        incoming: Dict[str, List[str]] = {node.get("id"): [] for node in nodes}
        outgoing: Dict[str, List[str]] = {node.get("id"): [] for node in nodes}

        for edge in edges:
            _source = edge.get("source")
            _target = edge.get("target")
            if source in outgoing:
                outgoing[source].append(target)
            if target in incoming:
                incoming[target].append(source)

        # Check each node type for requirements
        for node in nodes:
            _node_id = node.get("id")
            _node_type = node.get("type")
            _data = node.get("data", {})

            # Decision nodes require at least one input
            if node_type == "decision" and not incoming.get(node_id):
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.MISSING_REQUIRED_INPUT,
                    _message = "Decision node requires at least one input connection",
                    _node_id = node_id,
                    _suggestion = "Connect a previous node to this decision node"
                ))

            # Tool nodes require input
            if node_type == "tool" and not incoming.get(node_id):
                result.warnings.append(ValidationError(
                    _severity = "warning",
                    _code = ErrorCodes.MISSING_REQUIRED_INPUT,
                    _message = "Tool node has no input connection",
                    _node_id = node_id,
                    _suggestion = "Connect a previous node to provide input"
                ))

    def _validate_resource_conflicts(self, nodes: List[Dict], result: ValidationResult) -> None:
        """Detect resource conflicts (e.g., multiple agents competing for same resource)."""
        # Track resources by type
        resources: Dict[str, List[str]] = {}

        for node in nodes:
            _data = node.get("data", {})
            _resource_id = data.get("resourceId")

            if resource_id:
                if resource_id not in resources:
                    resources[resource_id] = []
                resources[resource_id].append(node.get("id"))

        # Check for conflicts
        for resource_id, node_ids in resources.items():
            if len(node_ids) > 1:
                result.warnings.append(ValidationError(
                    _severity = "warning",
                    _code = ErrorCodes.RESOURCE_CONFLICT,
                    _message = f"Multiple nodes competing for resource: {resource_id}",
                    _node_id = node_ids[0],
                    _suggestion = f"Nodes {', '.join(node_ids)} share the same resource. Ensure proper synchronization."
                ))

    def _validate_degree_limits(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Validate node connection limits."""
        in_degree: Dict[str, int] = {node.get("id"): 0 for node in nodes}
        out_degree: Dict[str, int] = {node.get("id"): 0 for node in nodes}

        for edge in edges:
            _source = edge.get("source")
            _target = edge.get("target")
            if source in out_degree:
                out_degree[source] += 1
            if target in in_degree:
                in_degree[target] += 1

        for node in nodes:
            _node_id = node.get("id")

            if in_degree.get(node_id, 0) > self.max_in_degree:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.INVALID_EDGE_CONNECTION,
                    _message = f"Node exceeds maximum input connections ({self.max_in_degree})",
                    _node_id = node_id,
                    _suggestion = f"Reduce input connections to {self.max_in_degree} or fewer"
                ))

            if out_degree.get(node_id, 0) > self.max_out_degree:
                result.errors.append(ValidationError(
                    _severity = "error",
                    _code = ErrorCodes.INVALID_EDGE_CONNECTION,
                    _message = f"Node exceeds maximum output connections ({self.max_out_degree})",
                    _node_id = node_id,
                    _suggestion = f"Reduce output connections to {self.max_out_degree} or fewer"
                ))

    def _validate_start_node(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Validate workflow has a valid start node."""
        if not nodes:
            return

        # Find nodes with no incoming edges (potential start nodes)
        _has_incoming = {edge.get("target") for edge in edges}
        _start_candidates = [n for n in nodes if n.get("id") not in has_incoming]

        if not start_candidates:
            result.errors.append(ValidationError(
                _severity = "error",
                _code = ErrorCodes.INVALID_START_NODE,
                _message = "No valid start node found (all nodes have incoming connections)",
                _suggestion = "Add an input node or ensure at least one node has no incoming connections"
            ))

    def _check_orphaned_nodes(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Check for orphaned nodes (only warnings)."""
        if len(nodes) <= 1:
            return

        _connected = set()
        for edge in edges:
            connected.add(edge.get("source"))
            connected.add(edge.get("target"))

        # Find input/output nodes that should be connected
        for node in nodes:
            _node_id = node.get("id")
            _node_type = node.get("type")

            if node_type in ("input", "output") and node_id not in connected:
                result.warnings.append(ValidationError(
                    _severity = "warning",
                    _code = ErrorCodes.ORPHANED_NODE,
                    _message = f"{node_type.capitalize()} node is not connected",
                    _node_id = node_id,
                    _suggestion = f"Connect the {node_type} node to the workflow"
                ))

    def _check_unused_outputs(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Check for nodes with outputs that aren't used."""
        _sources = {edge.get("source") for edge in edges}
        _targets = {edge.get("target") for edge in edges}

        for node in nodes:
            _node_id = node.get("id")
            _node_type = node.get("type")

            # Check if node has output but isn't connected to anything
            if node_id in sources and node_id not in targets:
                if node_type in ("agent", "tool", "memory"):
                    result.info.append(ValidationError(
                        _severity = "info",
                        _code = ErrorCodes.UNUSED_OUTPUT,
                        _message = f"Node output is not consumed by any other node",
                        _node_id = node_id,
                        _suggestion = "Consider connecting this node's output to another node"
                    ))

    def _check_graph_complexity(self, nodes: List[Dict], edges: List[Dict], result: ValidationResult) -> None:
        """Check for overly complex graphs."""
        _node_count = len(nodes)
        _edge_count = len(edges)

        # Warn for very large graphs
        if node_count > 50:
            result.info.append(ValidationError(
                _severity = "info",
                _code = ErrorCodes.COMPLEX_GRAPH,
                _message = f"Workflow has {node_count} nodes",
                _suggestion = "Consider breaking into smaller sub-workflows for better maintainability"
            ))

        # Warn for dense graphs
        if node_count > 0 and edge_count / node_count > 3:
            result.info.append(ValidationError(
                _severity = "info",
                _code = ErrorCodes.COMPLEX_GRAPH,
                _message = f"Workflow is densely connected ({edge_count} edges for {node_count} nodes)",
                _suggestion = "Consider simplifying the workflow structure"
            ))


# =============================================================================
# Convenience Functions
# =============================================================================

def validate_workflow(workflow_definition: Dict[str, Any]) -> ValidationResult:
    """
    Validate a workflow definition.
    
    Args:
        workflow_definition: Workflow definition with nodes and edges
        
    Returns:
        ValidationResult with validation results
    """
    _validator = WorkflowValidator()
    return validator.validate(workflow_definition)


def validate_workflow_strict(workflow_definition: Dict[str, Any]) -> ValidationResult:
    """
    Validate a workflow with strict settings (no cycles allowed).
    
    Args:
        workflow_definition: Workflow definition with nodes and edges
        
    Returns:
        ValidationResult with validation results
    """
    _validator = WorkflowValidator(allow_cycles=False)
    return validator.validate(workflow_definition)


# Export for API
__all__ = [
    "WorkflowValidator",
    "ValidationError",
    "ValidationResult",
    "ValidationErrorSeverity",
    "ErrorCodes",
    "validate_workflow",
    "validate_workflow_strict",
]
