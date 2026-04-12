"""
Security tests for workflow engine - P0-2 Security Fix Validation

These tests verify that the dangerous eval() call has been replaced with
a safe AST-based expression evaluator that prevents:
- Object introspection attacks
- Method access through dunder attributes
- Code injection attempts

Related to: P0-2 - Remove Dangerous eval() in workflow/engine.py
Location: src/heretek_swarm/workflow/engine.py:800 (formerly line 561)
"""

from datetime import datetime, timezone

import pytest

from heretek_swarm.workflow.engine import (
    SafeExpressionEvaluator,
    WorkflowContext,
    WorkflowEngine,
    WorkflowState,
)


class TestSafeExpressionEvaluator:
    """Test the SafeExpressionEvaluator security measures."""

    def test_safe_literal_evaluation(self):
        """Test that literal values can be evaluated safely."""
        evaluator = SafeExpressionEvaluator()

        # Test basic literals
        assert evaluator.validate_and_eval("123") == 123
        assert evaluator.validate_and_eval("3.14") == 3.14
        assert evaluator.validate_and_eval("'hello'") == "hello"
        assert evaluator.validate_and_eval("True") is True
        assert evaluator.validate_and_eval("False") is False
        assert evaluator.validate_and_eval("None") is None

    def test_safe_comparison_operations(self):
        """Test that comparison operations work safely."""
        evaluator = SafeExpressionEvaluator({
            "a": 10,
            "b": 20,
            "x": "hello",
            "y": "world"
        })

        # Test comparison operators
        assert evaluator.validate_and_eval("a < b") is True
        assert evaluator.validate_and_eval("a > b") is False
        assert evaluator.validate_and_eval("a == 10") is True
        assert evaluator.validate_and_eval("a != b") is True
        assert evaluator.validate_and_eval("a <= 10") is True
        assert evaluator.validate_and_eval("b >= 20") is True

    def test_safe_boolean_operations(self):
        """Test that boolean operations work safely."""
        evaluator = SafeExpressionEvaluator({
            "a": True,
            "b": False,
            "x": 10,
            "y": 20
        })

        # Test boolean operators
        assert evaluator.validate_and_eval("a and not b") is True
        assert evaluator.validate_and_eval("a or b") is True
        assert evaluator.validate_and_eval("not b") is True
        assert evaluator.validate_and_eval("x < y and a") is True

    def test_safe_in_operator(self):
        """Test that 'in' operator works safely."""
        evaluator = SafeExpressionEvaluator({
            "items": [1, 2, 3, 4, 5],
            "value": 3,
            "data": {"key": "value"}
        })

        assert evaluator.validate_and_eval("value in items") is True
        assert evaluator.validate_and_eval("10 in items") is False
        assert evaluator.validate_and_eval("'key' in data") is True

    def test_safe_subscript_access(self):
        """Test that subscript access works safely."""
        evaluator = SafeExpressionEvaluator({
            "items": [1, 2, 3, 4, 5],
            "data": {"key": "value", "num": 42}
        })

        assert evaluator.validate_and_eval("items[0]") == 1
        assert evaluator.validate_and_eval("items[2]") == 3
        assert evaluator.validate_and_eval("data['key']") == "value"
        assert evaluator.validate_and_eval("data['num']") == 42


class TestObjectIntrospectionAttacks:
    """Test that object introspection attacks are blocked."""

    def test_block_dunder_class_access(self):
        """Test that __class__ access is blocked."""
        evaluator = SafeExpressionEvaluator({"value": "test"})

        # This should raise ValueError - unsafe node type (attribute access)
        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("value.__class__")

    def test_block_dunder_mro_access(self):
        """Test that __mro__ access is blocked."""
        evaluator = SafeExpressionEvaluator({"value": "test"})

        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("value.__class__.__mro__")

    def test_block_subclasses_access(self):
        """Test that __subclasses__() access is blocked."""
        evaluator = SafeExpressionEvaluator({"value": "test"})

        # Attribute access is blocked
        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("value.__class__.__mro__[1].__subclasses__()")

    def test_block_getattr_access(self):
        """Test that getattr() calls are blocked."""
        evaluator = SafeExpressionEvaluator({"value": "test"})

        # Function calls are blocked
        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("getattr(value, '__class__')")

    def test_block_exec_call(self):
        """Test that exec() calls are blocked."""
        evaluator = SafeExpressionEvaluator({"cmd": "print('hello')"})

        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("exec(cmd)")

    def test_block_eval_call(self):
        """Test that eval() calls are blocked."""
        evaluator = SafeExpressionEvaluator({"expr": "1+1"})

        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("eval(expr)")

    def test_block_import_attempts(self):
        """Test that import attempts are blocked."""
        evaluator = SafeExpressionEvaluator({})

        # Import statements should fail at parse time (not expression)
        # or be blocked as unsafe nodes
        with pytest.raises(ValueError):
            evaluator.validate_and_eval("__import__('os')")

    def test_block_builtin_access(self):
        """Test that __builtins__ access is blocked."""
        evaluator = SafeExpressionEvaluator({})

        # __builtins__ should be blocked because it's not in allowed variables
        with pytest.raises(ValueError, match="not in the allowed variables"):
            evaluator.validate_and_eval("__builtins__")

    def test_block_globals_access(self):
        """Test that globals() access is blocked."""
        evaluator = SafeExpressionEvaluator({})

        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("globals()")

    def test_block_locals_access(self):
        """Test that locals() access is blocked."""
        evaluator = SafeExpressionEvaluator({})

        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("locals()")

    def test_block_attr_chain_attack(self):
        """Test that attribute chain attacks are blocked."""
        evaluator = SafeExpressionEvaluator({"s": ""})

        # Classic Python sandbox escape attempt
        with pytest.raises(ValueError, match="Unsafe node type"):
            evaluator.validate_and_eval("s.__class__.__mro__[2].__subclasses__()")

    def test_block_system_call_via_os(self):
        """Test that os.system calls are blocked."""
        evaluator = SafeExpressionEvaluator({})

        with pytest.raises(ValueError):
            evaluator.validate_and_eval("__import__('os').system('id')")


class TestVariableValidation:
    """Test that variable access is properly validated."""

    def test_allowed_variable_access(self):
        """Test that allowed variables can be accessed."""
        evaluator = SafeExpressionEvaluator({
            "allowed_var": 42,
            "another_var": "hello"
        })

        assert evaluator.validate_and_eval("allowed_var") == 42
        assert evaluator.validate_and_eval("another_var") == "hello"

    def test_blocked_undefined_variable(self):
        """Test that undefined variables are blocked."""
        evaluator = SafeExpressionEvaluator({"allowed": 1})

        # Undefined variable should raise ValueError
        with pytest.raises(ValueError, match="not in the allowed variables"):
            evaluator.validate_and_eval("undefined_var")

    def test_blocked_dunder_variable(self):
        """Test that dunder variables are blocked."""
        evaluator = SafeExpressionEvaluator({})

        with pytest.raises(ValueError, match="not in the allowed variables"):
            evaluator.validate_and_eval("__import__")

    def test_complex_expression_with_only_allowed_vars(self):
        """Test complex expressions with only allowed variables."""
        evaluator = SafeExpressionEvaluator({
            "user_role": "admin",
            "required_role": "user",
            "is_active": True,
            "permissions": ["read", "write", "delete"]
        })

        # Complex but safe expression
        result = evaluator.validate_and_eval(
            "user_role == 'admin' and is_active and 'delete' in permissions"
        )
        assert result is True


class TestWorkflowEngineConditionEvaluation:
    """Test the workflow engine's condition evaluation with the safe evaluator."""

    def test_workflow_condition_with_safe_vars(self):
        """Test workflow condition evaluation with safe variables."""
        engine = WorkflowEngine()

        # Create a mock context with variables
        context = WorkflowContext(
            workflow_id="test-wf",
            execution_id="test-exec",
            start_time=datetime.now(timezone.utc),
            state=WorkflowState.RUNNING
        )
        context.variables = {
            "status": "completed",
            "score": 85,
            "is_valid": True,
            "threshold": 50
        }

        # Test various condition expressions
        assert engine._evaluate_condition("score > threshold", context) is True
        assert engine._evaluate_condition("score < 100", context) is True
        assert engine._evaluate_condition("status == 'completed'", context) is True
        assert engine._evaluate_condition("is_valid and score > threshold", context) is True
        assert engine._evaluate_condition("is_valid and score < threshold", context) is False

    def test_workflow_condition_blocks_injection(self):
        """Test that workflow condition blocks injection attempts."""
        engine = WorkflowEngine()

        context = WorkflowContext(
            workflow_id="test-wf",
            execution_id="test-exec",
            start_time=datetime.now(timezone.utc),
            state=WorkflowState.RUNNING
        )
        context.variables = {"value": "test"}

        # These malicious conditions should fail safely and return False
        # rather than executing arbitrary code
        assert engine._evaluate_condition("value.__class__", context) is False
        assert engine._evaluate_condition("__import__('os')", context) is False
        assert engine._evaluate_condition("globals()", context) is False

        # The condition should fail safely, not raise an exception
        # (the engine catches exceptions and returns False)

    def test_workflow_condition_with_bracket_syntax(self):
        """Test workflow condition with {var} bracket syntax (legacy support)."""
        engine = WorkflowEngine()

        context = WorkflowContext(
            workflow_id="test-wf",
            execution_id="test-exec",
            start_time=datetime.now(timezone.utc),
            state=WorkflowState.RUNNING
        )
        context.variables = {
            "status": "completed",
            "count": 10
        }

        # Note: The new SafeExpressionEvaluator uses direct variable names
        # The old {var} syntax is no longer needed since variables are
        # passed directly to the evaluator
        # Test direct variable access
        assert engine._evaluate_condition("status == 'completed'", context) is True
        assert engine._evaluate_condition("count > 5", context) is True

    def test_workflow_condition_error_handling(self):
        """Test that condition evaluation errors are handled gracefully."""
        engine = WorkflowEngine()

        context = WorkflowContext(
            workflow_id="test-wf",
            execution_id="test-exec",
            start_time=datetime.now(timezone.utc),
            state=WorkflowState.RUNNING
        )
        context.variables = {}

        # Invalid expressions should return False, not crash
        assert engine._evaluate_condition("invalid syntax here", context) is False
        assert engine._evaluate_condition("", context) is False
        assert engine._evaluate_condition("undefined_var", context) is False


class TestRegressionPrevention:
    """Tests to ensure the dangerous eval() pattern doesn't return."""

    def test_no_dangerous_eval_in_module(self):
        """Verify that dangerous eval patterns are not present in the code."""
        import inspect

        import heretek_swarm.workflow.engine as engine_module

        source = inspect.getsource(engine_module)

        # Check for dangerous eval patterns
        # The pattern eval(expr, {"__builtins__": {}}) should NOT exist
        assert 'eval(expr, {"__builtins__": {}})' not in source
        assert "eval(expr, {'__builtins__': {}})" not in source

        # Safe usage with SafeExpressionEvaluator is OK
        # The source should contain SafeExpressionEvaluator usage
        assert "SafeExpressionEvaluator" in source

    def test_safe_evaluator_has_comprehensive_validation(self):
        """Verify SafeExpressionEvaluator has proper AST validation."""
        evaluator = SafeExpressionEvaluator()

        # Verify the evaluator has the safe node types defined
        assert hasattr(evaluator, "SAFE_NODE_TYPES")
        assert len(evaluator.SAFE_NODE_TYPES) > 0

        # Verify unsafe node types are NOT in the safe list
        # ast.Call should not be in safe types (function calls)
        assert ast.Call not in evaluator.SAFE_NODE_TYPES
        # ast.Attribute should not be in safe types (attribute access)
        assert ast.Attribute not in evaluator.SAFE_NODE_TYPES
        # ast.Import should not be in safe types (imports)
        assert ast.Import not in evaluator.SAFE_NODE_TYPES
        # ast.ImportFrom should not be in safe types (from imports)
        assert ast.ImportFrom not in evaluator.SAFE_NODE_TYPES


# Import ast for the regression test
import ast
