"""
Input Validators for Guardrails System

Provides specialized validator classes for different validation checks.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import structlog

_logger = structlog.get_logger(__name__)


class InputValidator(ABC):
    """Abstract base class for input validators"""
    
    @abstractmethod
    async def validate(self, _input_text: str, _agent_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate input and return (is_valid, reason)
        
        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        pass


class LengthValidator(InputValidator):
    """Validates input length constraints"""
    
    def __init__(self, _min_length: int, _max_length: int):
        self.min_length = min_length
        self.max_length = max_length
    
    async def validate(self, _input_text: str, _agent_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        _text_length = len(input_text)
        
        if text_length < self.min_length:
            logger.warning(
                "input_too_short",
                _agent_id = agent_id,
                _length = text_length
            )
            return False, f"Input too short (min: {self.min_length})"
        
        if text_length > self.max_length:
            logger.warning(
                "input_too_long",
                _agent_id = agent_id,
                _length = text_length,
                max_length=self.max_length
            )
            return False, f"Input too long (max: {self.max_length})"
        
        return True, None


class BlockedPatternValidator(InputValidator):
    """Validates input against blocked regex patterns"""
    
    def __init__(self, _compiled_patterns: List[re.Pattern]):
        self.patterns = compiled_patterns
    
    async def validate(self, _input_text: str, _agent_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        for pattern in self.patterns:
            _match = pattern.search(input_text)
            if match:
                logger.warning(
                    "input_blocked",
                    _agent_id = agent_id,
                    pattern=pattern.pattern,
                    _match = match.group(0)
                )
                return False, f"Blocked pattern detected: {pattern.pattern}"
        
        return True, None


class PersonalInfoValidator(InputValidator):
    """Validates input for personal information disclosure"""
    
    # Pre-compiled patterns for performance
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}[-]\d{2}[-]\d{4}\b')
    API_KEY_PATTERN = re.compile(r'\b[A-Za-z0-9]{20,}[_-][A-Za-z0-9]{10,}\b')
    
    def __init__(self, _block_personal_info: bool):
        self.block_personal_info = block_personal_info
    
    async def validate(self, _input_text: str, _agent_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not self.block_personal_info:
            return True, None
        
        # Check email
        if self.EMAIL_PATTERN.search(input_text):
            logger.warning("input_blocked_personal_email", agent_id=agent_id)
            return False, "Personal email address detected"
        
        # Check phone
        if self.PHONE_PATTERN.search(input_text):
            logger.warning("input_blocked_personal_phone", agent_id=agent_id)
            return False, "Personal phone number detected"
        
        # Check SSN
        if self.SSN_PATTERN.search(input_text):
            logger.warning("input_blocked_personal_ssn", agent_id=agent_id)
            return False, "Personal SSN pattern detected"
        
        # Check API keys
        if self.API_KEY_PATTERN.search(input_text):
            logger.warning("input_blocked_personal_api_key", agent_id=agent_id)
            return False, "API key pattern detected"
        
        return True, None


class CodeExecutionValidator(InputValidator):
    """Validates input for code execution attempts"""
    
    # Pre-compiled patterns for performance
    SHELL_PATTERN = re.compile(r'\b(sh|bash|cmd|powershell|exec)\s+[^\s]', re.IGNORECASE)
    PYTHON_EXEC_PATTERN = re.compile(r'\b(exec|eval|__import__|open\()[\'"]\s*\(', re.IGNORECASE)
    
    def __init__(self, _block_code_execution: bool):
        self.block_code_execution = block_code_execution
    
    async def validate(self, _input_text: str, _agent_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not self.block_code_execution:
            return True, None
        
        # Check shell commands
        if self.SHELL_PATTERN.search(input_text):
            logger.warning("input_blocked_code_execution", agent_id=agent_id)
            return False, "Shell command execution attempt detected"
        
        # Check Python exec
        if self.PYTHON_EXEC_PATTERN.search(input_text):
            logger.warning("input_blocked_python_execution", agent_id=agent_id)
            return False, "Python execution attempt detected"
        
        return True, None


class AllowedPatternsValidator(InputValidator):
    """Validates input against allowed patterns"""
    
    def __init__(self, _allowed_patterns: List[str]):
        self.allowed_patterns = allowed_patterns
        self._compiled = [re.compile(p, re.IGNORECASE) for p in allowed_patterns]
    
    async def validate(self, _input_text: str, _agent_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not self.allowed_patterns:
            return True, None
        
        for pattern in self._compiled:
            if pattern.search(input_text):
                return True, None
        
        logger.warning(
            "input_not_allowed",
            _agent_id = agent_id,
            _input = input_text[:100]
        )
        return False, "Input does not match allowed patterns"


class ValidatorChain:
    """Chains multiple validators together"""
    
    def __init__(self):
        self._validators: List[InputValidator] = []
    
    def add(self, _validator: InputValidator) -> 'ValidatorChain':
        """Add a validator to the chain"""
        self._validators.append(validator)
        return self
    
    async def validate(self, _input_text: str, _agent_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Run all validators in sequence"""
        for validator in self._validators:
            is_valid, reason = await validator.validate(input_text, agent_id)
            if not is_valid:
                return False, reason
        return True, None