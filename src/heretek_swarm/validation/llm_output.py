"""
LLM Output Validation Module

This module provides comprehensive validation and sanitization for LLM-generated outputs.
It uses Pydantic for schema validation and implements security patterns to block
dangerous code execution patterns.

Author: Heretek Swarm Collective
Date: 2026-04-07
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, validator as pydantic_validator


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Security vulnerability - reject immediately
    ERROR = "error"  # Invalid content - reject
    WARNING = "warning"  # Potentially problematic - log and sanitize
    INFO = "info"  # Informational - log only


class CodeLanguage(str, Enum):
    """Supported programming languages for code validation."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CPP = "cpp"
    SQL = "sql"
    SHELL = "shell"
    YAML = "yaml"
    JSON = "json"
    UNKNOWN = "unknown"


# Security patterns that should be blocked in LLM outputs
DANGEROUS_PATTERNS = {
    # Python code execution
    "eval": r"\beval\s*\(",
    "exec": r"\bexec\s*\(",
    "__import__": r"\b__import__\s*\(",
    "compile": r"\bcompile\s*\(",
    
    # Python introspection attacks
    "__class__": r"\b__class__\b",
    "__mro__": r"\b__mro__\b",
    "__subclasses__": r"\b__subclasses__\s*\(",
    "__globals__": r"\b__globals__\b",
    "__builtins__": r"\b__builtins__\b",
    "__code__": r"\b__code__\b",
    "__qualname__": r"\b__qualname__\b",
    
    # Attribute manipulation
    "getattr": r"\bgetattr\s*\(",
    "setattr": r"\bsetattr\s*\(",
    "delattr": r"\bdelattr\s*\(",
    "hasattr": r"\bhasattr\s*\(",
    
    # Namespace access
    "globals": r"\bglobals\s*\(",
    "locals": r"\blocals\s*\(",
    "vars": r"\bvars\s*\(",
    "dir": r"\bdir\s*\(",
    
    # File and I/O operations
    "input": r"\binput\s*\(",
    "open": r"\bopen\s*\(",
    "file": r"\bfile\s*\(",
    "io.open": r"\bio\.open\s*\(",
    
    # System commands
    "os.system": r"\bos\.system\s*\(",
    "os.popen": r"\bos\.popen\s*\(",
    "os.spawn": r"\bos\.spawn\w*\s*\(",
    "os.execl": r"\bos\.execl\w*\s*\(",
    "os.execle": r"\bos\.execle\w*\s*\(",
    "os.execlp": r"\bos\.execlp\w*\s*\(",
    "os.execv": r"\bos\.execv\w*\s*\(",
    "os.execve": r"\bos\.execve\w*\s*\(",
    "os.execvp": r"\bos\.execvp\w*\s*\(",
    "os.execvpe": r"\bos\.execvpe\w*\s*\(",
    "subprocess.call": r"\bsubprocess\.call\s*\(",
    "subprocess.run": r"\bsubprocess\.run\s*\(",
    "subprocess.Popen": r"\bsubprocess\.Popen\s*\(",
    "subprocess.check_output": r"\bsubprocess\.check_output\s*\(",
    "subprocess.check_call": r"\bsubprocess\.check_call\s*\(",
    "subprocess": r"\bsubprocess\.",
    
    # SQL injection patterns
    "sql_injection": r"(\bSELECT\b.*\bFROM\b.*\bWHERE\b.*=.*['\"]?\s*%s|\bINSERT\b.*\bINTO\b.*\bVALUES\b.*['\"]?\s*%s|\bDELETE\b.*\bFROM\b.*\bWHERE\b.*['\"]?\s*%s|\bUPDATE\b.*\bSET\b.*\bWHERE\b.*['\"]?\s*%s|;\s*DROP\s+TABLE|;\s*DELETE\s+FROM|--\s*$)",
    
    # Command injection (pipes, semicolons, logical operators, backticks)
    "cmd_injection_pipe": r"\|\s*(rm|cat|ls|wget|curl|bash|sh|nc|netcat|python|perl|ruby|php|node|java|gcc|g\+\+)",
    "cmd_injection_semicolon": r";\s*(rm|cat|ls|wget|curl|bash|sh|nc|netcat|python|perl|ruby|php|node|java|gcc|g\+\+)",
    "cmd_injection_and": r"&&\s*(rm|cat|ls|wget|curl|bash|sh|nc|netcat|python|perl|ruby|php|node|java|gcc|g\+\+)",
    "cmd_injection_or": r"\|\|\s*(rm|cat|ls|wget|curl|bash|sh|nc|netcat|python|perl|ruby|php|node|java|gcc|g\+\+)",
    "cmd_injection_backtick": r"`[^`]*`",
    
    # Pickle deserialization
    "pickle": r"\bpickle\.(load|loads|Unpickler)",
    
    # YAML unsafe loading
    "yaml_unsafe": r"\byaml\.load\s*\([^)]*\)\s*(?!Loader=yaml\.SafeLoader)",
    
    # Shell command substitution
    "shell_subst": r"\$\(.*\)|`.*`",
    
    # Path traversal
    "path_traversal": r"\.\./|\.\.\\",
    
    # XML external entity (XXE) patterns
    "xxe": r"<!ENTITY\s+.*SYSTEM",
    
    # Server-side request forgery (SSRF) patterns
    "ssrf": r"(https?://)(localhost|127\.0\.0\.1|0\.0\.0\.0|169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)",
}

# Patterns that should be sanitized (replaced) rather than rejected
SANITIZE_PATTERNS = {
    # HTML/XML that might be unintentional
    "html_tags": (r"<[^>]+>", "[REDACTED_HTML]"),
    
    # Potential markdown injection
    "markdown_code": (r"```[\s\S]*?```", "[CODE_BLOCK]"),
}


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    valid: bool
    content: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_content: Optional[Any] = None
    severity: ValidationSeverity = ValidationSeverity.INFO
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "valid": self.valid,
            "content": self.content,
            "errors": self.errors,
            "warnings": self.warnings,
            "sanitized_content": self.sanitized_content,
            "severity": self.severity.value,
        }


class LLMOutputBase(BaseModel):
    """Base class for all LLM output models."""
    
    class Config:
        extra = "forbid"  # Reject extra fields by default
        validate_assignment = True


class CodeBlock(LLMOutputBase):
    """Validated code block from LLM output."""
    
    language: CodeLanguage = Field(..., description="Programming language of the code")
    code: str = Field(..., min_length=1, description="The actual code content")
    description: Optional[str] = Field(None, max_length=500, description="Brief description of what the code does")
    
    @pydantic_validator("code")
    def validate_code_safety(cls, v: str) -> str:
        """Validate that code doesn't contain dangerous patterns."""
        if not v:
            return v
            
        for pattern_name, pattern in DANGEROUS_PATTERNS.items():
            if re.search(pattern, v, re.IGNORECASE | re.MULTILINE):
                raise ValueError(f"Code contains dangerous pattern: {pattern_name}")
        
        return v
    
    class Config:
        extra = "ignore"  # Allow extra fields for flexibility


class TextOutput(LLMOutputBase):
    """Validated text output from LLM."""
    
    content: str = Field(..., min_length=1, max_length=100000, description="The text content")
    content_type: str = Field(default="text", description="Type of content (text, markdown, json, etc.)")
    
    @pydantic_validator("content")
    def validate_text_safety(cls, v: str) -> str:
        """Validate that text doesn't contain dangerous patterns."""
        if not v:
            return v
            
        # Check for code execution patterns
        for pattern_name, pattern in DANGEROUS_PATTERNS.items():
            if pattern_name not in ["sql_injection", "cmd_injection"]:  # Skip context-specific patterns
                if re.search(pattern, v, re.IGNORECASE | re.MULTILINE):
                    raise ValueError(f"Text contains dangerous pattern: {pattern_name}")
        
        return v
    
    class Config:
        extra = "ignore"


class StructuredResponse(LLMOutputBase):
    """Validated structured JSON response from LLM."""
    
    data: Dict[str, Any] = Field(..., description="The structured data")
    schema_version: str = Field(default="1.0", description="Schema version for validation")
    
    @pydantic_validator("data")
    def validate_data_safety(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that structured data doesn't contain dangerous patterns."""
        if not v:
            return v
            
        def check_value(value: Any, path: str = "") -> None:
            """Recursively check values for dangerous patterns."""
            if isinstance(value, str):
                for pattern_name, pattern in DANGEROUS_PATTERNS.items():
                    if re.search(pattern, value, re.IGNORECASE | re.MULTILINE):
                        raise ValueError(f"Dangerous pattern '{pattern_name}' found at path: {path}")
            elif isinstance(value, dict):
                for key, val in value.items():
                    check_value(val, f"{path}.{key}" if path else key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    check_value(item, f"{path}[{i}]")
        
        check_value(v)
        return v
    
    class Config:
        extra = "allow"  # Allow extra fields in structured data


class ToolCall(LLMOutputBase):
    """Validated tool/function call from LLM."""
    
    tool_name: str = Field(..., min_length=1, max_length=100, description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    call_id: str = Field(default_factory=lambda: f"call_{datetime.now(timezone.utc).timestamp()}", description="Unique call identifier")
    
    @pydantic_validator("tool_name")
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name format."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"Invalid tool name format: {v}")
        return v
    
    @pydantic_validator("arguments")
    def validate_arguments_safety(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that arguments don't contain dangerous patterns."""
        if not v:
            return v
            
        for key, value in v.items():
            if isinstance(value, str):
                for pattern_name, pattern in DANGEROUS_PATTERNS.items():
                    if re.search(pattern, value, re.IGNORECASE | re.MULTILINE):
                        raise ValueError(f"Dangerous pattern '{pattern_name}' in argument '{key}'")
        
        return v
    
    class Config:
        extra = "forbid"


class LLMOutputValidator:
    """
    Comprehensive validator for LLM outputs.
    
    This class provides methods to validate and sanitize LLM-generated content
    before it's used in the system. It checks for dangerous patterns, validates
    schemas, and provides sanitization when possible.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the validator.
        
        Args:
            strict_mode: If True, reject any content with dangerous patterns.
                        If False, attempt sanitization first.
        """
        self.strict_mode = strict_mode
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for name, pattern in DANGEROUS_PATTERNS.items():
            self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    
    def validate_code(
        self,
        code: str,
        language: str = "python",
        allow_dangerous: bool = False,
    ) -> ValidationResult:
        """
        Validate a code block for safety.
        
        Args:
            code: The code to validate
            language: Programming language of the code
            allow_dangerous: If True, only warn about dangerous patterns instead of rejecting
        
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        if not code or not code.strip():
            return ValidationResult(
                valid=False,
                content=code,
                errors=["Code is empty"],
                severity=ValidationSeverity.ERROR,
            )
        
        # Check for dangerous patterns
        detected_patterns: List[str] = []
        for pattern_name, compiled_pattern in self._compiled_patterns.items():
            if compiled_pattern.search(code):
                detected_patterns.append(pattern_name)
        
        if detected_patterns:
            if self.strict_mode and not allow_dangerous:
                errors.append(f"Code contains dangerous patterns: {', '.join(detected_patterns)}")
            else:
                warnings.append(f"Code contains potentially dangerous patterns: {', '.join(detected_patterns)}")
        
        # Try to create validated model
        try:
            code_block = CodeBlock(
                language=CodeLanguage(language.lower()) if language.lower() in [e.value for e in CodeLanguage] else CodeLanguage.UNKNOWN,
                code=code,
            )
            validated_code = code_block.code
        except ValidationError as e:
            errors.append(f"Code validation failed: {e}")
            validated_code = code
        
        # Attempt sanitization if in non-strict mode
        sanitized = None
        if errors and not self.strict_mode:
            sanitized = self._sanitize_code(code)
            if sanitized != code:
                warnings.append("Code was sanitized")
                errors = []  # Clear errors if sanitization succeeded
        
        return ValidationResult(
            valid=len(errors) == 0,
            content=code,
            errors=errors,
            warnings=warnings,
            sanitized_content=sanitized,
            severity=ValidationSeverity.CRITICAL if errors else (ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO),
        )
    
    def validate_text(
        self,
        text: str,
        content_type: str = "text",
    ) -> ValidationResult:
        """
        Validate text output for safety.
        
        Args:
            text: The text to validate
            content_type: Type of content (text, markdown, json, etc.)
        
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        if not text or not text.strip():
            return ValidationResult(
                valid=False,
                content=text,
                errors=["Text is empty"],
                severity=ValidationSeverity.ERROR,
            )
        
        # Check for dangerous patterns (skip SQL and command injection for general text)
        detected_patterns: List[str] = []
        for pattern_name, compiled_pattern in self._compiled_patterns.items():
            if pattern_name in ["sql_injection", "cmd_injection"]:
                continue  # Skip context-specific patterns for general text
            if compiled_pattern.search(text):
                detected_patterns.append(pattern_name)
        
        if detected_patterns:
            if self.strict_mode:
                errors.append(f"Text contains dangerous patterns: {', '.join(detected_patterns)}")
            else:
                warnings.append(f"Text contains potentially dangerous patterns: {', '.join(detected_patterns)}")
        
        # Try to create validated model
        try:
            text_output = TextOutput(content=text, content_type=content_type)
            validated_text = text_output.content
        except ValidationError as e:
            errors.append(f"Text validation failed: {e}")
            validated_text = text
        
        return ValidationResult(
            valid=len(errors) == 0,
            content=text,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.CRITICAL if errors else (ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO),
        )
    
    def validate_structured(
        self,
        data: Dict[str, Any],
        schema_version: str = "1.0",
    ) -> ValidationResult:
        """
        Validate structured JSON response.
        
        Args:
            data: The structured data to validate
            schema_version: Version of the schema to use
        
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        if not data:
            return ValidationResult(
                valid=False,
                content=data,
                errors=["Data is empty"],
                severity=ValidationSeverity.ERROR,
            )
        
        # Try to create validated model
        try:
            structured = StructuredResponse(data=data, schema_version=schema_version)
            validated_data = structured.data
        except ValidationError as e:
            errors.append(f"Structured data validation failed: {e}")
            validated_data = data
        
        return ValidationResult(
            valid=len(errors) == 0,
            content=data,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.CRITICAL if errors else (ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO),
        )
    
    def validate_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate a tool/function call.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
        
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Try to create validated model
        try:
            tool_call = ToolCall(tool_name=tool_name, arguments=arguments)
            validated_args = tool_call.arguments
        except ValidationError as e:
            errors.append(f"Tool call validation failed: {e}")
            validated_args = arguments
        
        return ValidationResult(
            valid=len(errors) == 0,
            content={"tool_name": tool_name, "arguments": arguments},
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.CRITICAL if errors else (ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO),
        )
    
    def _sanitize_code(self, code: str) -> str:
        """
        Attempt to sanitize code by removing or replacing dangerous patterns.
        
        Args:
            code: The code to sanitize
        
        Returns:
            Sanitized code with dangerous patterns removed or replaced
        """
        sanitized = code
        
        # Apply sanitization patterns
        for pattern_name, (pattern, replacement) in SANITIZE_PATTERNS.items():
            sanitized = re.sub(pattern, replacement, sanitized)
        
        # Comment out dangerous Python patterns instead of removing them
        dangerous_python = ["eval(", "exec(", "__import__(", "getattr(", "setattr(", "delattr(", "globals(", "locals(", "vars("]
        for pattern in dangerous_python:
            if pattern in sanitized:
                # Replace the dangerous call with a commented version
                sanitized = sanitized.replace(pattern, f"# DANGEROUS: {pattern}")
        
        return sanitized
    
    def sanitize_string(self, text: str) -> str:
        """
        Sanitize a string by removing dangerous patterns.
        
        Args:
            text: The text to sanitize
        
        Returns:
            Sanitized text
        """
        sanitized = text
        
        # Apply sanitization patterns
        for pattern_name, (pattern, replacement) in SANITIZE_PATTERNS.items():
            sanitized = re.sub(pattern, replacement, sanitized)
        
        return sanitized
    
    def is_safe_code(self, code: str) -> bool:
        """
        Quick check if code is safe (no dangerous patterns).
        
        Args:
            code: The code to check
        
        Returns:
            True if code is safe, False otherwise
        """
        for compiled_pattern in self._compiled_patterns.values():
            if compiled_pattern.search(code):
                return False
        return True
    
    def is_safe_text(self, text: str) -> bool:
        """
        Quick check if text is safe (no dangerous patterns).
        
        Args:
            text: The text to check
        
        Returns:
            True if text is safe, False otherwise
        """
        for name, compiled_pattern in self._compiled_patterns.items():
            if name in ["sql_injection", "cmd_injection"]:
                continue
            if compiled_pattern.search(text):
                return False
        return True


# Convenience functions for quick validation
def validate_llm_code(code: str, language: str = "python", strict: bool = True) -> ValidationResult:
    """
    Validate LLM-generated code.
    
    Args:
        code: The code to validate
        language: Programming language
        strict: If True, reject dangerous patterns; if False, sanitize
    
    Returns:
        ValidationResult
    """
    validator = LLMOutputValidator(strict_mode=strict)
    return validator.validate_code(code, language)


def validate_llm_text(text: str, content_type: str = "text") -> ValidationResult:
    """
    Validate LLM-generated text.
    
    Args:
        text: The text to validate
        content_type: Type of content
    
    Returns:
        ValidationResult
    """
    validator = LLMOutputValidator(strict_mode=True)
    return validator.validate_text(text, content_type)


def validate_llm_structured(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate LLM-generated structured data.
    
    Args:
        data: The structured data to validate
    
    Returns:
        ValidationResult
    """
    validator = LLMOutputValidator(strict_mode=True)
    return validator.validate_structured(data)


def is_code_safe(code: str) -> bool:
    """
    Quick check if code is safe.
    
    Args:
        code: The code to check
    
    Returns:
        True if code is safe, False otherwise
    """
    validator = LLMOutputValidator()
    return validator.is_safe_code(code)


def is_text_safe(text: str) -> bool:
    """
    Quick check if text is safe.
    
    Args:
        text: The text to check
    
    Returns:
        True if text is safe, False otherwise
    """
    validator = LLMOutputValidator()
    return validator.is_safe_text(text)
