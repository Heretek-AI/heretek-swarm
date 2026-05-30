"""Unit tests for Pydantic v2 strict models in llm_output.py and agent_messages.py.

Covers:
- StrictStr/StrictInt/StrictBool/StrictFloat type rejection
- extra=forbid rejection (extra unknown field raises ValidationError)
- field_validator safety checks (dangerous patterns raise ValueError)
- Valid creation for all models
- DANGEROUS_PATTERNS regex still catches eval/exec/subprocess
- validate_message factory returns correct model for each MessageType
- Factory functions (create_actor_message, create_state_update, etc.)
- LLMOutputValidator convenience functions
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from pydantic import ValidationError

pytestmark = [pytest.mark.unit]

from heretek_swarm.validation.llm_output import (
    CodeBlock,
    CodeLanguage,
    DANGEROUS_PATTERNS,
    LLMOutputValidator,
    StructuredResponse,
    TextOutput,
    ToolCall,
    ValidationResult,
    ValidationSeverity,
    is_code_safe,
    is_text_safe,
    validate_llm_code,
    validate_llm_structured,
    validate_llm_text,
)
from heretek_swarm.validation.agent_messages import (
    ActorMessage,
    CodeExecutionRequest,
    ConsensusProposal,
    ConsensusVote,
    CoordinationRequest,
    ErrorMessage,
    MessagePriority,
    MessageType,
    MESSAGE_TYPES,
    StateUpdate,
    TaskMessage,
    ToolRequest,
    ToolResponse,
    create_actor_message,
    create_state_update,
    create_tool_request,
    create_tool_response,
    validate_message,
)


# ===========================================================================
# DANGEROUS_PATTERNS regex tests
# ===========================================================================


class TestDangerousPatterns:
    """Verify DANGEROUS_PATTERNS regex still catches key injection vectors."""

    def test_eval_pattern_matches(self) -> None:
        assert re.search(DANGEROUS_PATTERNS["eval"], "eval(", re.IGNORECASE)
        assert re.search(DANGEROUS_PATTERNS["eval"], " eval (  1+1)", re.IGNORECASE)

    def test_exec_pattern_matches(self) -> None:
        assert re.search(DANGEROUS_PATTERNS["exec"], "exec(", re.IGNORECASE)
        assert re.search(DANGEROUS_PATTERNS["exec"], " exec (  code )", re.IGNORECASE)

    def test_subprocess_pattern_matches(self) -> None:
        assert re.search(DANGEROUS_PATTERNS["subprocess"], "subprocess.run", re.IGNORECASE)
        assert re.search(DANGEROUS_PATTERNS["subprocess.call"], "subprocess.call(", re.IGNORECASE)
        assert re.search(DANGEROUS_PATTERNS["subprocess.Popen"], "subprocess.Popen(", re.IGNORECASE)

    def test_os_system_matches(self) -> None:
        assert re.search(DANGEROUS_PATTERNS["os.system"], "os.system(", re.IGNORECASE)

    def test_dunder_import_matches(self) -> None:
        assert re.search(DANGEROUS_PATTERNS["__import__"], "__import__(", re.IGNORECASE)

    def test_pickle_loads_matches(self) -> None:
        assert re.search(DANGEROUS_PATTERNS["pickle"], "pickle.loads(", re.IGNORECASE)

    def test_path_traversal_matches(self) -> None:
        assert re.search(DANGEROUS_PATTERNS["path_traversal"], "../etc/passwd", re.IGNORECASE)

    def test_safe_text_does_not_match(self) -> None:
        safe = "This is a normal response about system architecture and design patterns."
        for name, pattern in DANGEROUS_PATTERNS.items():
            assert not re.search(pattern, safe, re.IGNORECASE), (
                f"Pattern '{name}' should not match safe text"
            )


# ===========================================================================
# CodeBlock tests
# ===========================================================================


class TestCodeBlock:
    def test_valid_creation(self) -> None:
        cb = CodeBlock(language=CodeLanguage.PYTHON, code="print('hello')")
        assert cb.language == CodeLanguage.PYTHON
        assert cb.code == "print('hello')"
        assert cb.description is None

    def test_valid_with_description(self) -> None:
        cb = CodeBlock(
            language=CodeLanguage.JAVASCRIPT,
            code="console.log('hi')",
            description="A simple log statement",
        )
        assert cb.language == CodeLanguage.JAVASCRIPT
        assert cb.description == "A simple log statement"

    def test_unknown_language_fallback(self) -> None:
        cb = CodeBlock(language=CodeLanguage.UNKNOWN, code="some code")
        assert cb.language == CodeLanguage.UNKNOWN

    def test_strict_str_code_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            CodeBlock(language=CodeLanguage.PYTHON, code=123)  # type: ignore[arg-type]

    def test_strict_str_code_rejects_none(self) -> None:
        with pytest.raises(ValidationError):
            CodeBlock(language=CodeLanguage.PYTHON, code=None)  # type: ignore[arg-type]

    def test_extra_ignore_drops_unknown_field(self) -> None:
        # CodeBlock.model_config has extra="ignore" (overrides base extra="forbid")
        # so unknown fields are silently dropped, not rejected
        cb = CodeBlock(language=CodeLanguage.PYTHON, code="x=1", unknown_field="bad")  # type: ignore[call-arg]
        assert cb.code == "x=1"
        assert not hasattr(cb, "unknown_field")

    def test_field_validator_rejects_eval(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            CodeBlock(language=CodeLanguage.PYTHON, code="eval('1+1')")

    def test_field_validator_rejects_exec(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            CodeBlock(language=CodeLanguage.PYTHON, code="exec('import os')")

    def test_field_validator_rejects_subprocess(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            CodeBlock(language=CodeLanguage.PYTHON, code="subprocess.run(['ls'])")

    def test_field_validator_rejects_double_underscore_import(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            CodeBlock(language=CodeLanguage.PYTHON, code="__import__('os')")

    def test_field_validator_allows_safe_code(self) -> None:
        cb = CodeBlock(language=CodeLanguage.PYTHON, code="def foo():\n    return 42")
        assert cb.code == "def foo():\n    return 42"


# ===========================================================================
# TextOutput tests
# ===========================================================================


class TestTextOutput:
    def test_valid_creation(self) -> None:
        to = TextOutput(content="Hello world")
        assert to.content == "Hello world"
        assert to.content_type == "text"

    def test_valid_with_content_type(self) -> None:
        to = TextOutput(content="# Heading\n\nContent", content_type="markdown")
        assert to.content_type == "markdown"

    def test_strict_str_content_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            TextOutput(content=42)  # type: ignore[arg-type]

    def test_content_min_length(self) -> None:
        with pytest.raises(ValidationError):
            TextOutput(content="")

    def test_extra_ignore_allows_extra(self) -> None:
        # TextOutput has ConfigDict(extra="ignore") — extra fields are dropped
        to = TextOutput(content="hello", extra_field="ignored")  # type: ignore[call-arg]
        assert to.content == "hello"
        assert not hasattr(to, "extra_field")

    def test_field_validator_rejects_eval_in_text(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            TextOutput(content="You should use eval('1+1') to compute this")

    def test_field_validator_rejects_exec_in_text(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            TextOutput(content="Try exec('import os') for system access")

    def test_field_validator_rejects_subprocess_in_text(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            TextOutput(content="Call subprocess.run(['rm', '-rf', '/']) to clean up")

    def test_field_validator_rejects_pickle_in_text(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            TextOutput(content="Use pickle.loads(data) to deserialize")

    def test_field_validator_rejects_path_traversal_in_text(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            TextOutput(content="Read from ../../etc/passwd to get users")

    def test_field_validator_rejects_ssrf_in_text(self) -> None:
        with pytest.raises(ValueError, match="dangerous pattern"):
            TextOutput(content="Fetch http://localhost:8080/admin to get config")

    def test_field_validator_allows_safe_text(self) -> None:
        to = TextOutput(
            content="This is a safe response about designing a REST API with proper "
            "authentication and rate limiting."
        )
        assert "safe response" in to.content


# ===========================================================================
# StructuredResponse tests
# ===========================================================================


class TestStructuredResponse:
    def test_valid_creation(self) -> None:
        sr = StructuredResponse(data={"key": "value"})
        assert sr.data == {"key": "value"}
        assert sr.schema_version == "1.0"

    def test_custom_schema_version(self) -> None:
        sr = StructuredResponse(data={"a": 1}, schema_version="2.0")
        assert sr.schema_version == "2.0"

    def test_strict_str_schema_version_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            StructuredResponse(data={"key": "val"}, schema_version=123)  # type: ignore[arg-type]

    def test_extra_allow_accepts_extra(self) -> None:
        sr = StructuredResponse(data={"key": "val"}, extra="allowed")  # type: ignore[call-arg]
        assert sr.extra == "allowed"  # type: ignore[attr-defined]

    def test_field_validator_rejects_dangerous_nested_string(self) -> None:
        with pytest.raises(ValueError, match="Dangerous pattern"):
            StructuredResponse(data={"nested": {"cmd": "eval('1+1')"}})

    def test_field_validator_rejects_dangerous_list_item(self) -> None:
        with pytest.raises(ValueError, match="Dangerous pattern"):
            StructuredResponse(data={"items": ["safe", "exec('bad')"]})

    def test_field_validator_allows_safe_nested_data(self) -> None:
        sr = StructuredResponse(
            data={
                "name": "test",
                "nested": {"key": "safe_value"},
                "items": ["a", "b", "c"],
            }
        )
        assert sr.data["nested"]["key"] == "safe_value"


# ===========================================================================
# ToolCall tests
# ===========================================================================


class TestToolCall:
    def test_valid_creation(self) -> None:
        tc = ToolCall(tool_name="search_docs", arguments={"query": "pydantic"})
        assert tc.tool_name == "search_docs"
        assert tc.arguments == {"query": "pydantic"}
        assert tc.call_id.startswith("call_")

    def test_default_arguments(self) -> None:
        tc = ToolCall(tool_name="list_files")
        assert tc.arguments == {}

    def test_strict_str_tool_name_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            ToolCall(tool_name=42)  # type: ignore[arg-type]

    def test_invalid_tool_name_format_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid tool name format"):
            ToolCall(tool_name="bad tool name!")

    def test_tool_name_must_start_with_alpha(self) -> None:
        with pytest.raises(ValueError, match="Invalid tool name format"):
            ToolCall(tool_name="123bad")

    def test_extra_forbid_rejects_unknown_field(self) -> None:
        with pytest.raises(ValidationError):
            ToolCall(tool_name="my_tool", bad_field="nope")  # type: ignore[call-arg]

    def test_field_validator_rejects_dangerous_arguments(self) -> None:
        with pytest.raises(ValueError, match="Dangerous pattern"):
            ToolCall(
                tool_name="process_input",
                arguments={"code": "eval('malicious')"},
            )

    def test_field_validator_allows_safe_arguments(self) -> None:
        tc = ToolCall(
            tool_name="search",
            arguments={"query": "pydantic strict mode", "limit": 10},
        )
        assert tc.arguments["limit"] == 10


# ===========================================================================
# ActorMessage tests
# ===========================================================================


class TestActorMessage:
    def test_valid_creation_minimal(self) -> None:
        msg = ActorMessage(
            sender_id="agent-1",
            content={"text": "hello"},
        )
        assert msg.sender_id == "agent-1"
        assert msg.content == {"text": "hello"}
        assert msg.message_type == MessageType.ACTOR_MESSAGE.value
        assert msg.priority == MessagePriority.NORMAL

    def test_full_fields(self) -> None:
        msg = ActorMessage(
            sender_id="alpha",
            recipient_id="beta",
            content={"action": "analyze"},
            priority=MessagePriority.HIGH,
            correlation_id="corr-123",
            metadata={"source": "test"},
        )
        assert msg.recipient_id == "beta"
        assert msg.priority == MessagePriority.HIGH
        assert msg.correlation_id == "corr-123"

    def test_message_id_auto_generated(self) -> None:
        msg = ActorMessage(sender_id="agent-1", content={"x": 1})
        assert msg.message_id.startswith("msg_")
        assert len(msg.message_id) > 4

    def test_strict_str_sender_id_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            ActorMessage(sender_id=123, content={"x": 1})  # type: ignore[arg-type]

    def test_field_validator_rejects_dangerous_content(self) -> None:
        with pytest.raises(ValueError, match="Unsafe content"):
            ActorMessage(
                sender_id="agent-1",
                content={"code": "eval('rm -rf /')"},
            )

    def test_field_validator_allows_safe_nested_content(self) -> None:
        msg = ActorMessage(
            sender_id="agent-1",
            content={"text": "safe content", "nested": {"key": "value"}, "items": [1, 2, 3]},
        )
        assert msg.content["nested"]["key"] == "value"


# ===========================================================================
# StateUpdate tests
# ===========================================================================


class TestStateUpdate:
    def test_valid_creation(self) -> None:
        su = StateUpdate(
            sender_id="agent-1",
            state_key="agent_state",
            state_value="active",
        )
        assert su.state_key == "agent_state"
        assert su.operation == "set"

    def test_invalid_state_key_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid state key format"):
            StateUpdate(sender_id="a", state_key="bad key!", state_value=1)

    def test_valid_dotted_state_key(self) -> None:
        su = StateUpdate(sender_id="a", state_key="nested.deep.key", state_value="x")
        assert su.state_key == "nested.deep.key"

    def test_strict_str_state_key_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            StateUpdate(sender_id="a", state_key=42, state_value="x")  # type: ignore[arg-type]

    def test_invalid_operation_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid operation"):
            StateUpdate(sender_id="a", state_key="k", state_value=1, operation="destroy")

    def test_valid_operations_accepted(self) -> None:
        for op in ("set", "append", "delete", "merge", "increment", "decrement"):
            su = StateUpdate(sender_id="a", state_key="k", state_value=1, operation=op)
            assert su.operation == op

    def test_strict_int_version_rejects_string(self) -> None:
        with pytest.raises(ValidationError):
            StateUpdate(sender_id="a", state_key="k", state_value=1, version="abc")  # type: ignore[arg-type]

    def test_version_accepts_int(self) -> None:
        su = StateUpdate(sender_id="a", state_key="k", state_value=1, version=5)
        assert su.version == 5

    def test_extra_forbid_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            StateUpdate(sender_id="a", state_key="k", state_value=1, hack="bad")  # type: ignore[call-arg]

    def test_field_validator_rejects_dangerous_state_value(self) -> None:
        with pytest.raises(ValueError, match="Unsafe state value"):
            StateUpdate(sender_id="a", state_key="k", state_value="exec('bad')")

    def test_field_validator_sanitizes_nested(self) -> None:
        su = StateUpdate(
            sender_id="a",
            state_key="config",
            state_value={"name": "safe", "items": [1, 2]},
        )
        assert su.state_value["name"] == "safe"


# ===========================================================================
# ToolRequest tests
# ===========================================================================


class TestToolRequest:
    def test_valid_creation(self) -> None:
        tr = ToolRequest(
            sender_id="agent-1",
            tool_name="list_files",
            arguments={"path": "/tmp"},  # noqa: S108
        )
        assert tr.tool_name == "list_files"
        assert tr.timeout == 30  # default

    def test_strict_int_timeout_rejects_string(self) -> None:
        with pytest.raises(ValidationError):
            ToolRequest(sender_id="a", tool_name="t", timeout="thirty")  # type: ignore[arg-type]

    def test_timeout_ge_1(self) -> None:
        with pytest.raises(ValidationError):
            ToolRequest(sender_id="a", tool_name="t", timeout=0)

    def test_timeout_le_300(self) -> None:
        with pytest.raises(ValidationError):
            ToolRequest(sender_id="a", tool_name="t", timeout=301)

    def test_dangerous_tool_name_rejected(self) -> None:
        for bad_name in ("eval", "exec", "compile", "open", "__import__"):
            with pytest.raises(ValueError, match="Dangerous tool name"):
                ToolRequest(sender_id="a", tool_name=bad_name)

    def test_dangerous_tool_name_case_insensitive(self) -> None:
        with pytest.raises(ValueError, match="Dangerous tool name"):
            ToolRequest(sender_id="a", tool_name="EVAL")

    def test_invalid_tool_name_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid tool name format"):
            ToolRequest(sender_id="a", tool_name="bad name")

    def test_extra_forbid_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            ToolRequest(sender_id="a", tool_name="t", evil="yes")  # type: ignore[call-arg]

    def test_field_validator_rejects_dangerous_arguments(self) -> None:
        with pytest.raises(ValueError, match="Unsafe argument"):
            ToolRequest(
                sender_id="a",
                tool_name="safe_tool",
                arguments={"code": "subprocess.run(['ls'])"},
            )

    def test_field_validator_allows_safe_arguments(self) -> None:
        tr = ToolRequest(
            sender_id="a",
            tool_name="read_file",
            arguments={"path": "/safe/path", "encoding": "utf-8"},
        )
        assert tr.arguments["encoding"] == "utf-8"


# ===========================================================================
# ToolResponse tests
# ===========================================================================


class TestToolResponse:
    def test_valid_success_response(self) -> None:
        tr = ToolResponse(
            sender_id="agent-1",
            execution_id="exec-123",
            success=True,
            result={"data": "done"},
            execution_time_ms=150,
        )
        assert tr.success is True
        assert tr.result == {"data": "done"}

    def test_valid_error_response(self) -> None:
        tr = ToolResponse(
            sender_id="agent-1",
            execution_id="exec-456",
            success=False,
            error="File not found",
        )
        assert tr.success is False
        assert tr.error == "File not found"

    def test_strict_bool_success_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            ToolResponse(sender_id="a", execution_id="e1", success=1)  # type: ignore[arg-type]

    def test_strict_bool_success_rejects_string(self) -> None:
        with pytest.raises(ValidationError):
            ToolResponse(sender_id="a", execution_id="e1", success="true")  # type: ignore[arg-type]

    def test_strict_int_execution_time_rejects_string(self) -> None:
        with pytest.raises(ValidationError):
            ToolResponse(sender_id="a", execution_id="e1", success=True, execution_time_ms="fast")  # type: ignore[arg-type]

    def test_execution_time_ge_0(self) -> None:
        with pytest.raises(ValidationError):
            ToolResponse(sender_id="a", execution_id="e1", success=True, execution_time_ms=-1)

    def test_extra_forbid_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            ToolResponse(sender_id="a", execution_id="e1", success=True, nope="bad")  # type: ignore[call-arg]


# ===========================================================================
# CoordinationRequest tests
# ===========================================================================


class TestCoordinationRequest:
    def test_valid_creation(self) -> None:
        cr = CoordinationRequest(
            sender_id="agent-1",
            request_type="code_review",
            description="Please review the attached code.",
        )
        assert cr.request_type == "code_review"
        assert cr.required_capabilities == []

    def test_with_capabilities(self) -> None:
        cr = CoordinationRequest(
            sender_id="agent-1",
            request_type="analysis",
            description="Analyze this data.",
            required_capabilities=["python", "statistics"],
        )
        assert len(cr.required_capabilities) == 2

    def test_strict_str_description_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            CoordinationRequest(sender_id="a", request_type="r", description=123)  # type: ignore[arg-type]

    def test_extra_forbid_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            CoordinationRequest(sender_id="a", request_type="r", description="d", hack="bad")  # type: ignore[call-arg]

    def test_field_validator_rejects_dangerous_description(self) -> None:
        with pytest.raises(ValueError, match="Unsafe description"):
            CoordinationRequest(
                sender_id="a",
                request_type="r",
                description="Run eval('rm -rf /') to complete",
            )


# ===========================================================================
# ConsensusProposal tests
# ===========================================================================


class TestConsensusProposal:
    def test_valid_creation(self) -> None:
        cp = ConsensusProposal(
            sender_id="agent-1",
            title="Upgrade dependencies",
            description="We should upgrade pydantic to v3.",
            proposer_id="agent-1",
        )
        assert cp.title == "Upgrade dependencies"
        assert cp.proposal_id.startswith("prop_")

    def test_with_options(self) -> None:
        cp = ConsensusProposal(
            sender_id="a",
            title="Choose strategy",
            description="Pick one.",
            proposer_id="a",
            options=["option_a", "option_b"],
        )
        assert cp.options == ["option_a", "option_b"]

    def test_strict_str_title_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            ConsensusProposal(sender_id="a", title=42, description="d", proposer_id="a")  # type: ignore[arg-type]

    def test_field_validator_rejects_dangerous_title(self) -> None:
        with pytest.raises(ValueError, match="Unsafe text"):
            ConsensusProposal(
                sender_id="a",
                title="Use eval('1+1') for computing",
                description="Safe description here.",
                proposer_id="a",
            )

    def test_field_validator_rejects_dangerous_description(self) -> None:
        with pytest.raises(ValueError, match="Unsafe text"):
            ConsensusProposal(
                sender_id="a",
                title="Safe title",
                description="You should run exec('import os')",
                proposer_id="a",
            )


# ===========================================================================
# ConsensusVote tests
# ===========================================================================


class TestConsensusVote:
    def test_valid_creation(self) -> None:
        cv = ConsensusVote(
            sender_id="agent-1",
            proposal_id="prop-abc",
            vote="yes",
            confidence=0.85,
        )
        assert cv.vote == "yes"
        assert cv.confidence == 0.85

    def test_strict_float_confidence_rejects_string(self) -> None:
        # StrictFloat rejects string values
        with pytest.raises(ValidationError):
            ConsensusVote(sender_id="a", proposal_id="p1", vote="yes", confidence="high")  # type: ignore[arg-type]

    def test_strict_float_confidence_accepts_int(self) -> None:
        # StrictFloat accepts int in non-strict model mode (safe coercion to float)
        cv = ConsensusVote(sender_id="a", proposal_id="p1", vote="yes", confidence=1)  # type: ignore[arg-type]
        assert cv.confidence == 1.0

    def test_strict_float_confidence_accepts_float(self) -> None:
        cv = ConsensusVote(sender_id="a", proposal_id="p1", vote="yes", confidence=0.5)
        assert cv.confidence == 0.5

    def test_confidence_ge_0(self) -> None:
        with pytest.raises(ValidationError):
            ConsensusVote(sender_id="a", proposal_id="p1", vote="yes", confidence=-0.1)  # type: ignore[arg-type]

    def test_confidence_le_1(self) -> None:
        with pytest.raises(ValidationError):
            ConsensusVote(sender_id="a", proposal_id="p1", vote="yes", confidence=1.5)  # type: ignore[arg-type]

    def test_field_validator_rejects_dangerous_reasoning(self) -> None:
        with pytest.raises(ValueError, match="Unsafe reasoning"):
            ConsensusVote(
                sender_id="a",
                proposal_id="p1",
                vote="yes",
                reasoning="Because eval('1+1') confirms this is correct",
            )

    def test_none_reasoning_ok(self) -> None:
        cv = ConsensusVote(sender_id="a", proposal_id="p1", vote="yes", reasoning=None)
        assert cv.reasoning is None


# ===========================================================================
# ErrorMessage tests
# ===========================================================================


class TestErrorMessage:
    def test_valid_creation(self) -> None:
        em = ErrorMessage(
            sender_id="agent-1",
            error_code="E001",
            error_message="Something went wrong",
        )
        assert em.error_code == "E001"
        assert em.message_type == MessageType.ERROR.value

    def test_with_stack_trace(self) -> None:
        em = ErrorMessage(
            sender_id="a",
            error_code="E500",
            error_message="Internal error",
            stack_trace="Traceback...",
        )
        assert em.stack_trace == "Traceback..."

    def test_strict_str_error_code_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            ErrorMessage(sender_id="a", error_code=500, error_message="msg")  # type: ignore[arg-type]

    def test_extra_forbid_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            ErrorMessage(sender_id="a", error_code="E", error_message="m", bad="x")  # type: ignore[call-arg]


# ===========================================================================
# TaskMessage tests
# ===========================================================================


class TestTaskMessage:
    def test_valid_creation(self) -> None:
        tm = TaskMessage(
            sender_id="agent-1",
            message_type=MessageType.TASK_CREATED.value,
            task_id="task-42",
            task_status="pending",
        )
        assert tm.task_id == "task-42"
        assert tm.message_type == MessageType.TASK_CREATED.value

    def test_with_task_data(self) -> None:
        tm = TaskMessage(
            sender_id="a",
            message_type="task_updated",
            task_id="t1",
            task_data={"progress": 50},
        )
        assert tm.task_data == {"progress": 50}

    def test_strict_str_task_id_rejects_int(self) -> None:
        with pytest.raises(ValidationError):
            TaskMessage(sender_id="a", message_type="m", task_id=42)  # type: ignore[arg-type]

    def test_extra_forbid_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            TaskMessage(sender_id="a", message_type="m", task_id="t", hack="x")  # type: ignore[call-arg]

    def test_field_validator_rejects_dangerous_task_data(self) -> None:
        with pytest.raises(ValueError, match="Unsafe task data"):
            TaskMessage(
                sender_id="a",
                message_type="task_created",
                task_id="t1",
                task_data={"inject": "subprocess.run(['rm'])"},
            )

    def test_field_validator_allows_safe_task_data(self) -> None:
        tm = TaskMessage(
            sender_id="a",
            message_type="task_completed",
            task_id="t1",
            task_data={"result": "success", "count": 42},
        )
        assert tm.task_data["result"] == "success"


# ===========================================================================
# CodeExecutionRequest tests
# ===========================================================================


class TestCodeExecutionRequest:
    def test_valid_creation(self) -> None:
        cer = CodeExecutionRequest(
            sender_id="agent-1",
            code="print('hello')",
            language="python",
        )
        assert cer.language == "python"
        assert cer.sandbox is True

    def test_strict_bool_sandbox_rejects_string(self) -> None:
        with pytest.raises(ValidationError):
            CodeExecutionRequest(sender_id="a", code="c", sandbox="yes")  # type: ignore[arg-type]

    def test_strict_int_timeout_rejects_string(self) -> None:
        with pytest.raises(ValidationError):
            CodeExecutionRequest(sender_id="a", code="c", timeout="forever")  # type: ignore[arg-type]

    def test_field_validator_rejects_dangerous_code(self) -> None:
        with pytest.raises(ValueError, match="Unsafe code"):
            CodeExecutionRequest(
                sender_id="a",
                code="eval('print(1)')",
            )

    def test_field_validator_allows_safe_code(self) -> None:
        cer = CodeExecutionRequest(
            sender_id="a",
            code="def add(a, b):\n    return a + b",
        )
        assert "def add" in cer.code

    def test_extra_forbid_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            CodeExecutionRequest(sender_id="a", code="c", evil="yes")  # type: ignore[call-arg]


# ===========================================================================
# validate_message factory tests
# ===========================================================================


class TestValidateMessage:
    def test_actor_message_type_returns_actor_message(self) -> None:
        result = validate_message(
            MessageType.ACTOR_MESSAGE.value,
            {"sender_id": "agent-1", "content": {"text": "hi"}},
        )
        assert result.valid is True
        assert result.content["sender_id"] == "agent-1"

    def test_state_update_type_returns_state_update(self) -> None:
        result = validate_message(
            MessageType.STATE_UPDATE.value,
            {"sender_id": "a", "state_key": "k", "state_value": "v"},
        )
        assert result.valid is True

    def test_tool_request_type_returns_tool_request(self) -> None:
        result = validate_message(
            MessageType.TOOL_REQUEST.value,
            {"sender_id": "a", "tool_name": "search"},
        )
        assert result.valid is True

    def test_tool_response_type_returns_tool_response(self) -> None:
        result = validate_message(
            MessageType.TOOL_RESPONSE.value,
            {"sender_id": "a", "execution_id": "e1", "success": True},
        )
        assert result.valid is True

    def test_error_type_returns_error_message(self) -> None:
        result = validate_message(
            MessageType.ERROR.value,
            {"sender_id": "a", "error_code": "E1", "error_message": "fail"},
        )
        assert result.valid is True

    def test_consensus_proposal_type_returns_proposal(self) -> None:
        result = validate_message(
            MessageType.CONSENSUS_PROPOSAL.value,
            {
                "sender_id": "a",
                "title": "Proposal",
                "description": "Desc",
                "proposer_id": "a",
            },
        )
        assert result.valid is True

    def test_consensus_vote_type_returns_vote(self) -> None:
        result = validate_message(
            MessageType.CONSENSUS_VOTE.value,
            {"sender_id": "a", "proposal_id": "p1", "vote": "yes"},
        )
        assert result.valid is True

    def test_code_execution_request_type_returns_code_request(self) -> None:
        result = validate_message(
            "code_execution_request",
            {"sender_id": "a", "code": "print(1)"},
        )
        assert result.valid is True

    def test_unknown_type_falls_back_to_structured_validation(self) -> None:
        result = validate_message("fantasy_type", {"data": "safe_value"})
        # Falls back to StructuredResponse validation (valid because safe)
        assert result.valid is True

    def test_unknown_type_with_empty_data(self) -> None:
        result = validate_message("fantasy_type", {})
        assert result.valid is False  # Data is empty

    def test_invalid_model_returns_errors(self) -> None:
        result = validate_message(
            MessageType.ACTOR_MESSAGE.value,
            {"sender_id": 123, "content": {}},  # int for StrictStr
        )
        assert result.valid is False
        assert len(result.errors) > 0


# ===========================================================================
# Factory function tests
# ===========================================================================


class TestFactoryFunctions:
    def test_create_actor_message(self) -> None:
        msg = create_actor_message(
            content={"action": "greet"},
            sender_id="alpha",
            recipient_id="beta",
            priority=MessagePriority.HIGH,
        )
        assert msg.sender_id == "alpha"
        assert msg.recipient_id == "beta"
        assert msg.priority == MessagePriority.HIGH
        assert msg.content == {"action": "greet"}

    def test_create_state_update(self) -> None:
        msg = create_state_update(
            state_key="agent.mode",
            state_value="idle",
            sender_id="agent-1",
            operation="set",
            version=3,
        )
        assert msg.state_key == "agent.mode"
        assert msg.state_value == "idle"
        assert msg.version == 3

    def test_create_tool_request(self) -> None:
        msg = create_tool_request(
            tool_name="read_file",
            arguments={"path": "/tmp/test.txt"},  # noqa: S108
            sender_id="coder-1",
            timeout=60,
        )
        assert msg.tool_name == "read_file"
        assert msg.timeout == 60
        assert msg.arguments == {"path": "/tmp/test.txt"}  # noqa: S108

    def test_create_tool_response_success(self) -> None:
        msg = create_tool_response(
            execution_id="exec-abc",
            success=True,
            sender_id="agent-1",
            result={"output": "done"},
            execution_time_ms=200,
        )
        assert msg.success is True
        assert msg.result == {"output": "done"}

    def test_create_tool_response_error(self) -> None:
        msg = create_tool_response(
            execution_id="exec-xyz",
            success=False,
            sender_id="agent-1",
            error="timeout",
            execution_time_ms=0,
        )
        assert msg.success is False
        assert msg.error == "timeout"


# ===========================================================================
# MESSAGE_TYPES registry completeness
# ===========================================================================


class TestMessageTypeRegistry:
    def test_all_registered_types_are_valid_models(self) -> None:
        """Every model class in MESSAGE_TYPES can be instantiated with minimal valid data."""
        for msg_type, model_class in MESSAGE_TYPES.items():
            # Build minimal valid data per type
            data: dict[str, Any] = {"sender_id": "test-agent"}

            if msg_type == MessageType.ACTOR_MESSAGE.value:
                data["content"] = {"text": "hi"}
            elif msg_type == MessageType.STATE_UPDATE.value:
                data["state_key"] = "k"
                data["state_value"] = "v"
            elif msg_type == MessageType.TOOL_REQUEST.value:
                data["tool_name"] = "search"
            elif msg_type == MessageType.TOOL_RESPONSE.value:
                data["execution_id"] = "e"
                data["success"] = True
            elif msg_type == MessageType.COORDINATION_REQUEST.value:
                data["request_type"] = "review"
                data["description"] = "please review"
            elif msg_type == MessageType.CONSENSUS_PROPOSAL.value:
                data["title"] = "T"
                data["description"] = "D"
                data["proposer_id"] = "p"
            elif msg_type == MessageType.CONSENSUS_VOTE.value:
                data["proposal_id"] = "p"
                data["vote"] = "yes"
            elif msg_type == MessageType.ERROR.value:
                data["error_code"] = "E"
                data["error_message"] = "err"
            elif msg_type == "code_execution_request":
                data["code"] = "print(1)"

            model = model_class(**data)
            assert model.sender_id == "test-agent", f"{msg_type} creation failed"


# ===========================================================================
# LLMOutputValidator convenience functions
# ===========================================================================


class TestLLMOutputValidatorConvenience:
    def test_validate_llm_text_safe(self) -> None:
        result = validate_llm_text("This is a perfectly safe response.")
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_llm_text_dangerous(self) -> None:
        result = validate_llm_text("Use eval('print(1)') for computation.")
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_llm_code_safe(self) -> None:
        result = validate_llm_code("def foo(): return 1", language="python")
        assert result.valid is True

    def test_validate_llm_code_dangerous(self) -> None:
        result = validate_llm_code("exec('import os')", language="python")
        assert result.valid is False

    def test_validate_llm_structured_safe(self) -> None:
        result = validate_llm_structured({"key": "safe_value"})
        assert result.valid is True

    def test_validate_llm_structured_dangerous(self) -> None:
        result = validate_llm_structured({"cmd": "subprocess.run(['ls'])"})
        assert result.valid is False

    def test_is_text_safe_true(self) -> None:
        assert is_text_safe("hello world") is True

    def test_is_text_safe_false(self) -> None:
        assert is_text_safe("eval('x')") is False

    def test_is_code_safe_true(self) -> None:
        assert is_code_safe("def add(a,b): return a+b") is True

    def test_is_code_safe_false(self) -> None:
        assert is_code_safe("pickle.loads(data)") is False


# ===========================================================================
# ValidationResult tests
# ===========================================================================


class TestValidationResult:
    def test_to_dict(self) -> None:
        vr = ValidationResult(
            valid=False,
            content="bad",
            errors=["error1"],
            warnings=["warning1"],
            severity=ValidationSeverity.CRITICAL,
        )
        d = vr.to_dict()
        assert d["valid"] is False
        assert d["errors"] == ["error1"]
        assert d["severity"] == "critical"

    def test_valid_result_to_dict(self) -> None:
        vr = ValidationResult(valid=True, content="good")
        d = vr.to_dict()
        assert d["valid"] is True
        assert d["errors"] == []


# ===========================================================================
# Strict type enforcement summary tests
# ===========================================================================


class TestStrictTypeEnforcement:
    """Comprehensive StrictStr/StrictInt/StrictBool/StrictFloat rejection tests."""

    def test_strict_str_rejects_int_on_all_models(self) -> None:
        """StrictStr fields must reject int values."""
        # CodeBlock.code is StrictStr
        with pytest.raises(ValidationError):
            CodeBlock(language=CodeLanguage.PYTHON, code=1)  # type: ignore[arg-type]
        # TextOutput.content is StrictStr
        with pytest.raises(ValidationError):
            TextOutput(content=1)  # type: ignore[arg-type]
        # ToolCall.tool_name is StrictStr
        with pytest.raises(ValidationError):
            ToolCall(tool_name=1)  # type: ignore[arg-type]

    def test_strict_str_rejects_bool_on_all_models(self) -> None:
        """StrictStr fields must reject bool values."""
        with pytest.raises(ValidationError):
            CodeBlock(language=CodeLanguage.PYTHON, code=True)  # type: ignore[arg-type]

    def test_strict_int_rejects_string_on_state_update(self) -> None:
        """StrictInt version rejects string '5'."""
        with pytest.raises(ValidationError):
            StateUpdate(sender_id="a", state_key="k", state_value=1, version="abc")  # type: ignore[arg-type]

    def test_strict_bool_rejects_string(self) -> None:
        """StrictBool must reject the string 'true'."""
        with pytest.raises(ValidationError):
            ToolResponse(sender_id="a", execution_id="e", success="true")  # type: ignore[arg-type]

    def test_strict_int_rejects_string_on_tool_request(self) -> None:
        """StrictInt timeout rejects string."""
        with pytest.raises(ValidationError):
            ToolRequest(sender_id="a", tool_name="t", timeout="abc")  # type: ignore[arg-type]

    def test_strict_int_rejects_float_on_tool_request(self) -> None:
        """StrictInt timeout should reject float (strict means exact type)."""
        with pytest.raises(ValidationError):
            ToolRequest(sender_id="a", tool_name="t", timeout=30.5)  # type: ignore[arg-type]

    def test_strict_float_accepts_int_on_consensus_vote(self) -> None:
        """StrictFloat confidence accepts int value (safe coercion in non-strict model)."""
        cv = ConsensusVote(sender_id="a", proposal_id="p", vote="y", confidence=1)  # type: ignore[arg-type]
        assert cv.confidence == 1.0

    def test_strict_float_rejects_string_on_consensus_vote(self) -> None:
        """StrictFloat confidence rejects string value."""
        with pytest.raises(ValidationError):
            ConsensusVote(sender_id="a", proposal_id="p", vote="y", confidence="high")  # type: ignore[arg-type]

    def test_strict_bool_rejects_int(self) -> None:
        """StrictBool sandbox rejects integer."""
        with pytest.raises(ValidationError):
            CodeExecutionRequest(sender_id="a", code="c", sandbox=1)  # type: ignore[arg-type]
