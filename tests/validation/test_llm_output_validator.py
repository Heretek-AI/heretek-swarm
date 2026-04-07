"""
Tests for LLM Output Validator

This module contains comprehensive tests for the LLM output validation
functionality, including security pattern detection and Pydantic model validation.
"""

import pytest
from pydantic import ValidationError

from heretek_swarm.validation.llm_output import (
    LLMOutputValidator,
    ValidationResult,
    ValidationSeverity,
    CodeLanguage,
    CodeBlock,
    TextOutput,
    StructuredResponse,
    ToolCall,
    validate_llm_code,
    validate_llm_text,
    validate_llm_structured,
    is_code_safe,
    is_text_safe,
    DANGEROUS_PATTERNS,
)


class TestDangerousPatterns:
    """Test that all dangerous patterns are defined."""
    
    def test_python_code_execution_patterns(self):
        """Test Python code execution patterns are defined."""
        assert "eval" in DANGEROUS_PATTERNS
        assert "exec" in DANGEROUS_PATTERNS
        assert "__import__" in DANGEROUS_PATTERNS
        assert "compile" in DANGEROUS_PATTERNS
    
    def test_python_introspection_patterns(self):
        """Test Python introspection attack patterns are defined."""
        assert "__class__" in DANGEROUS_PATTERNS
        assert "__mro__" in DANGEROUS_PATTERNS
        assert "__subclasses__" in DANGEROUS_PATTERNS
        assert "__globals__" in DANGEROUS_PATTERNS
        assert "__builtins__" in DANGEROUS_PATTERNS
        assert "__code__" in DANGEROUS_PATTERNS
        assert "__qualname__" in DANGEROUS_PATTERNS
    
    def test_attribute_manipulation_patterns(self):
        """Test attribute manipulation patterns are defined."""
        assert "getattr" in DANGEROUS_PATTERNS
        assert "setattr" in DANGEROUS_PATTERNS
        assert "delattr" in DANGEROUS_PATTERNS
        assert "hasattr" in DANGEROUS_PATTERNS
    
    def test_namespace_access_patterns(self):
        """Test namespace access patterns are defined."""
        assert "globals" in DANGEROUS_PATTERNS
        assert "locals" in DANGEROUS_PATTERNS
        assert "vars" in DANGEROUS_PATTERNS
        assert "dir" in DANGEROUS_PATTERNS
    
    def test_file_io_patterns(self):
        """Test file and I/O operation patterns are defined."""
        assert "input" in DANGEROUS_PATTERNS
        assert "open" in DANGEROUS_PATTERNS
        assert "file" in DANGEROUS_PATTERNS
        assert "io.open" in DANGEROUS_PATTERNS
    
    def test_system_command_patterns(self):
        """Test system command patterns are defined."""
        assert "os.system" in DANGEROUS_PATTERNS
        assert "os.popen" in DANGEROUS_PATTERNS
        assert "subprocess" in DANGEROUS_PATTERNS
        assert "subprocess.call" in DANGEROUS_PATTERNS
        assert "subprocess.run" in DANGEROUS_PATTERNS
        assert "subprocess.Popen" in DANGEROUS_PATTERNS
        assert "subprocess.check_output" in DANGEROUS_PATTERNS
        assert "subprocess.check_call" in DANGEROUS_PATTERNS
    
    def test_command_injection_patterns(self):
        """Test command injection patterns are defined."""
        assert "cmd_injection_pipe" in DANGEROUS_PATTERNS
        assert "cmd_injection_semicolon" in DANGEROUS_PATTERNS
        assert "cmd_injection_and" in DANGEROUS_PATTERNS
        assert "cmd_injection_or" in DANGEROUS_PATTERNS
        assert "cmd_injection_backtick" in DANGEROUS_PATTERNS
    
    def test_sql_injection_pattern(self):
        """Test SQL injection pattern is defined."""
        assert "sql_injection" in DANGEROUS_PATTERNS
    
    def test_other_dangerous_patterns(self):
        """Test other dangerous patterns are defined."""
        assert "pickle" in DANGEROUS_PATTERNS
        assert "yaml_unsafe" in DANGEROUS_PATTERNS
        assert "shell_subst" in DANGEROUS_PATTERNS
        assert "path_traversal" in DANGEROUS_PATTERNS
        assert "xxe" in DANGEROUS_PATTERNS
        assert "ssrf" in DANGEROUS_PATTERNS


class TestLLMOutputValidator:
    """Tests for the LLMOutputValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return LLMOutputValidator(strict_mode=True)
    
    def test_validator_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator.strict_mode is True
        assert len(validator._compiled_patterns) > 0
    
    def test_validate_code_safe(self, validator):
        """Test validation of safe code."""
        result = validator.validate_code("print('Hello, World!')")
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_code_empty(self, validator):
        """Test validation of empty code."""
        result = validator.validate_code("")
        assert result.valid is False
        assert "Code is empty" in result.errors
    
    def test_validate_code_eval_pattern(self, validator):
        """Test that eval() pattern is blocked."""
        result = validator.validate_code("eval(user_input)")
        assert result.valid is False
        assert any("eval" in error for error in result.errors)
    
    def test_validate_code_exec_pattern(self, validator):
        """Test that exec() pattern is blocked."""
        result = validator.validate_code("exec(code)")
        assert result.valid is False
        assert any("exec" in error for error in result.errors)
    
    def test_validate_code_import_pattern(self, validator):
        """Test that __import__() pattern is blocked."""
        result = validator.validate_code("__import__('os')")
        assert result.valid is False
    
    def test_validate_code_compile_pattern(self, validator):
        """Test that compile() pattern is blocked."""
        result = validator.validate_code("compile('x=1', '', 'exec')")
        assert result.valid is False
    
    def test_validate_code_class_introspection(self, validator):
        """Test that __class__ introspection is blocked."""
        result = validator.validate_code("x.__class__.__mro__")
        assert result.valid is False
    
    def test_validate_code_subclasses(self, validator):
        """Test that __subclasses__() is blocked."""
        result = validator.validate_code("().__class__.__mro__[2].__subclasses__()")
        assert result.valid is False
    
    def test_validate_code_globals(self, validator):
        """Test that __globals__ access is blocked."""
        result = validator.validate_code("func.__globals__")
        assert result.valid is False
    
    def test_validate_code_getattr(self, validator):
        """Test that getattr() is blocked."""
        result = validator.validate_code("getattr(obj, 'attr')")
        assert result.valid is False
    
    def test_validate_code_setattr(self, validator):
        """Test that setattr() is blocked."""
        result = validator.validate_code("setattr(obj, 'attr', value)")
        assert result.valid is False
    
    def test_validate_code_delattr(self, validator):
        """Test that delattr() is blocked."""
        result = validator.validate_code("delattr(obj, 'attr')")
        assert result.valid is False
    
    def test_validate_code_hasattr(self, validator):
        """Test that hasattr() is blocked."""
        result = validator.validate_code("hasattr(obj, 'attr')")
        assert result.valid is False
    
    def test_validate_code_globals_namespace(self, validator):
        """Test that globals() is blocked."""
        result = validator.validate_code("globals()")
        assert result.valid is False
    
    def test_validate_code_locals_namespace(self, validator):
        """Test that locals() is blocked."""
        result = validator.validate_code("locals()")
        assert result.valid is False
    
    def test_validate_code_vars(self, validator):
        """Test that vars() is blocked."""
        result = validator.validate_code("vars(obj)")
        assert result.valid is False
    
    def test_validate_code_dir(self, validator):
        """Test that dir() is blocked."""
        result = validator.validate_code("dir(obj)")
        assert result.valid is False
    
    def test_validate_code_input(self, validator):
        """Test that input() is blocked."""
        result = validator.validate_code("input('Enter: ')")
        assert result.valid is False
    
    def test_validate_code_open(self, validator):
        """Test that open() is blocked."""
        result = validator.validate_code("open('/etc/passwd')")
        assert result.valid is False
    
    def test_validate_code_os_system(self, validator):
        """Test that os.system() is blocked."""
        result = validator.validate_code("os.system('ls -la')")
        assert result.valid is False
    
    def test_validate_code_subprocess_call(self, validator):
        """Test that subprocess.call() is blocked."""
        result = validator.validate_code("subprocess.call(['ls'])")
        assert result.valid is False
    
    def test_validate_code_subprocess_run(self, validator):
        """Test that subprocess.run() is blocked."""
        result = validator.validate_code("subprocess.run(['cat', '/etc/passwd'])")
        assert result.valid is False
    
    def test_validate_code_subprocess_popen(self, validator):
        """Test that subprocess.Popen() is blocked."""
        result = validator.validate_code("subprocess.Popen('rm -rf /')")
        assert result.valid is False
    
    def test_validate_code_pipe_injection(self, validator):
        """Test that pipe command injection is blocked."""
        result = validator.validate_code("os.system('ls | bash')")
        assert result.valid is False
    
    def test_validate_code_semicolon_injection(self, validator):
        """Test that semicolon command injection is blocked."""
        result = validator.validate_code("os.system('ls; rm -rf /')")
        assert result.valid is False
    
    def test_validate_code_and_injection(self, validator):
        """Test that && command injection is blocked."""
        result = validator.validate_code("os.system('ls && cat /etc/passwd')")
        assert result.valid is False
    
    def test_validate_code_backtick_injection(self, validator):
        """Test that backtick command injection is blocked."""
        result = validator.validate_code("os.system('echo `whoami`')")
        assert result.valid is False
    
    def test_validate_code_path_traversal(self, validator):
        """Test that path traversal is blocked."""
        result = validator.validate_code("open('../../../etc/passwd')")
        assert result.valid is False
    
    def test_validate_code_pickle(self, validator):
        """Test that pickle loading is blocked."""
        result = validator.validate_code("pickle.loads(data)")
        assert result.valid is False
    
    def test_validate_code_shell_substitution(self, validator):
        """Test that shell substitution is blocked."""
        result = validator.validate_code("os.system('$(whoami)')")
        assert result.valid is False
    
    def test_is_safe_code(self, validator):
        """Test is_safe_code method."""
        assert validator.is_safe_code("print('hello')") is True
        assert validator.is_safe_code("eval(x)") is False
        assert validator.is_safe_code("exec(x)") is False
    
    def test_validate_text_safe(self, validator):
        """Test validation of safe text."""
        result = validator.validate_text("This is a safe text message.")
        assert result.valid is True
    
    def test_validate_text_empty(self, validator):
        """Test validation of empty text."""
        result = validator.validate_text("")
        assert result.valid is False
    
    def test_validate_text_with_eval(self, validator):
        """Test that text containing eval is blocked."""
        result = validator.validate_text("You should use eval() for this")
        assert result.valid is False
    
    def test_validate_structured_safe(self, validator):
        """Test validation of safe structured data."""
        result = validator.validate_structured({"name": "John", "age": 30})
        assert result.valid is True
    
    def test_validate_structured_nested_dangerous(self, validator):
        """Test that nested dangerous patterns are detected."""
        result = validator.validate_structured({
            "config": {
                "callback": "eval(user_input)"
            }
        })
        assert result.valid is False
    
    def test_validate_tool_call_safe(self, validator):
        """Test validation of safe tool call."""
        result = validator.validate_tool_call("calculator", {"operation": "add", "a": 1, "b": 2})
        assert result.valid is True
    
    def test_validate_tool_call_dangerous_args(self, validator):
        """Test that tool call with dangerous args is blocked."""
        result = validator.validate_tool_call("executor", {"code": "eval(x)"})
        assert result.valid is False
    
    def test_non_strict_mode_sanitization(self):
        """Test that non-strict mode attempts sanitization."""
        validator = LLMOutputValidator(strict_mode=False)
        result = validator.validate_code("eval(x)")
        # In non-strict mode, should have warnings but may still be invalid
        assert len(result.warnings) > 0 or not result.valid


class TestCodeBlock:
    """Tests for CodeBlock Pydantic model."""
    
    def test_valid_code_block(self):
        """Test creating a valid code block."""
        block = CodeBlock(language=CodeLanguage.PYTHON, code="print('hello')")
        assert block.language == CodeLanguage.PYTHON
        assert block.code == "print('hello')"
    
    def test_code_block_with_eval_fails(self):
        """Test that code block with eval fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CodeBlock(language=CodeLanguage.PYTHON, code="eval(x)")
        assert "dangerous pattern" in str(exc_info.value).lower()
    
    def test_code_block_empty_code_fails(self):
        """Test that empty code fails validation."""
        with pytest.raises(ValidationError):
            CodeBlock(language=CodeLanguage.PYTHON, code="")


class TestTextOutput:
    """Tests for TextOutput Pydantic model."""
    
    def test_valid_text_output(self):
        """Test creating a valid text output."""
        output = TextOutput(content="Hello, World!")
        assert output.content == "Hello, World!"
    
    def test_text_output_with_exec_fails(self):
        """Test that text with exec fails validation."""
        with pytest.raises(ValidationError):
            TextOutput(content="Use exec() to run code")


class TestStructuredResponse:
    """Tests for StructuredResponse Pydantic model."""
    
    def test_valid_structured_response(self):
        """Test creating a valid structured response."""
        response = StructuredResponse(data={"key": "value"})
        assert response.data == {"key": "value"}
    
    def test_nested_dangerous_pattern_fails(self):
        """Test that nested dangerous patterns fail."""
        with pytest.raises(ValidationError) as exc_info:
            StructuredResponse(data={"nested": {"dangerous": "eval(x)"}})
        assert "dangerous pattern" in str(exc_info.value).lower()


class TestToolCall:
    """Tests for ToolCall Pydantic model."""
    
    def test_valid_tool_call(self):
        """Test creating a valid tool call."""
        call = ToolCall(tool_name="calculator", arguments={"op": "add"})
        assert call.tool_name == "calculator"
    
    def test_invalid_tool_name_format(self):
        """Test that invalid tool name format fails."""
        with pytest.raises(ValidationError):
            ToolCall(tool_name="123invalid", arguments={})
    
    def test_dangerous_tool_arguments(self):
        """Test that dangerous tool arguments fail."""
        with pytest.raises(ValidationError):
            ToolCall(tool_name="executor", arguments={"code": "eval(x)"})


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_validate_llm_code(self):
        """Test validate_llm_code function."""
        result = validate_llm_code("print('hello')")
        assert result.valid is True
    
    def test_validate_llm_text(self):
        """Test validate_llm_text function."""
        result = validate_llm_text("Safe text")
        assert result.valid is True
    
    def test_validate_llm_structured(self):
        """Test validate_llm_structured function."""
        result = validate_llm_structured({"safe": "data"})
        assert result.valid is True
    
    def test_is_code_safe(self):
        """Test is_code_safe function."""
        assert is_code_safe("print('hello')") is True
        assert is_code_safe("eval(x)") is False
    
    def test_is_text_safe(self):
        """Test is_text_safe function."""
        assert is_text_safe("Safe text") is True
        assert is_text_safe("Use eval()") is False


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_to_dict(self):
        """Test ValidationResult.to_dict method."""
        result = ValidationResult(
            valid=True,
            content="test",
            errors=[],
            warnings=[],
            severity=ValidationSeverity.INFO
        )
        d = result.to_dict()
        assert d["valid"] is True
        assert d["content"] == "test"
        assert d["errors"] == []
        assert d["severity"] == "info"


class TestValidationSeverity:
    """Tests for ValidationSeverity enum."""
    
    def test_severity_levels(self):
        """Test all severity levels exist."""
        assert ValidationSeverity.CRITICAL.value == "critical"
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.INFO.value == "info"


class TestCodeLanguage:
    """Tests for CodeLanguage enum."""
    
    def test_supported_languages(self):
        """Test all supported languages."""
        assert CodeLanguage.PYTHON.value == "python"
        assert CodeLanguage.JAVASCRIPT.value == "javascript"
        assert CodeLanguage.TYPESCRIPT.value == "typescript"
        assert CodeLanguage.GO.value == "go"
        assert CodeLanguage.RUST.value == "rust"
        assert CodeLanguage.JAVA.value == "java"
        assert CodeLanguage.CPP.value == "cpp"
        assert CodeLanguage.SQL.value == "sql"
        assert CodeLanguage.SHELL.value == "shell"
        assert CodeLanguage.YAML.value == "yaml"
        assert CodeLanguage.JSON.value == "json"
        assert CodeLanguage.UNKNOWN.value == "unknown"
