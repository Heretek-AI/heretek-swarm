"""
Guardrails System for Heretek Swarm

Provides input validation, output filtering, and content safety checks.
Reference: PraisonAI guardrails pattern
"""

from .validators import (
    LengthValidator,
    BlockedPatternValidator,
    PersonalInfoValidator,
    CodeExecutionValidator,
    AllowedPatternsValidator,
    ValidatorChain,
)

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import structlog

_logger = structlog.get_logger()


class GuardrailsAction(str, Enum):
    """Actions to take when guardrails are triggered"""
    BLOCK = "block"
    WARN = "warn"
    MODIFY = "modify"
    ESCALATE = "escalate"


@dataclass
class BlockedPattern:
    """A blocked pattern configuration"""
    pattern: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    action: GuardrailsAction


@dataclass
class ValidationResult:
    """Result of input validation"""
    valid: bool
    reason: Optional[str] = None
    pattern: Optional[str] = None
    max_length: Optional[int] = None
    modified_content: Optional[str] = None


@dataclass
class FilterResult:
    """Result of output filtering"""
    original: str
    filtered: str
    blocked_content: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class GuardrailsConfig:
    """Configuration for guardrails system"""
    # Input validation
    max_input_length: int = 10000
    min_input_length: int = 1
    allowed_patterns: List[str] = field(default_factory=list)
    
    # Output filtering
    enable_content_filter: bool = True
    block_personal_info: bool = True
    block_code_execution: bool = True
    
    # Blocked patterns
    blocked_patterns: List[BlockedPattern] = field(default_factory=list)
    
    # Rate limiting per agent
    agent_rate_limits: Dict[str, int] = field(default_factory=dict)


class GuardrailsSystem:
    """
    Input/output validation and safety system for Heretek Swarm.
    
    Provides comprehensive security guardrails to prevent:
    - Malicious input injection
    - Personal information disclosure
    - Code execution attempts
    - Harmful content generation
    """
    
    def __init__(self, _config: Optional[GuardrailsConfig]):
        """
        Initialize guardrails system.
        
        Args:
            config: Guardrails configuration
        """
        self.config = config or GuardrailsConfig()
        self._blocked_patterns = self._compile_blocked_patterns()
        self._validator_chain = self._build_validator_chain()
        logger.info(
            "guardrails_initialized",
            _blocked_patterns_count = len(self.config.blocked_patterns),
            max_input_length=self.config.max_input_length
        )
    
    def _compile_blocked_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for efficient matching"""
        _compiled = []
        for bp in self.config.blocked_patterns:
            try:
                pattern = re.compile(bp.pattern, re.IGNORECASE)
                compiled.append(pattern)
            except re.error as e:
                logger.warning(
                    "invalid_pattern",
                    pattern=bp.pattern,
                    _error = str(e)
                )
        return compiled
    
    def _build_validator_chain(self) -> ValidatorChain:
        """Build the validator chain for input validation"""
        _chain = ValidatorChain()
        
        # Length validation
        chain.add(LengthValidator(
            _min_length = self.config.min_input_length,
            _max_length = self.config.max_input_length
        ))
        
        # Blocked patterns validation
        chain.add(BlockedPatternValidator(self._blocked_patterns))
        
        # Personal information validation
        chain.add(PersonalInfoValidator(self.config.block_personal_info))
        
        # Code execution validation
        chain.add(CodeExecutionValidator(self.config.block_code_execution))
        
        # Allowed patterns validation
        chain.add(AllowedPatternsValidator(self.config.allowed_patterns))
        
        return chain
    
    async def validate_input(self, _input_text: str, _agent_id: Optional[str]) -> ValidationResult:
        """
        Validate user input against guardrails.
        
        Args:
            input_text: Input text to validate
            agent_id: Agent ID for logging
            
        Returns:
            ValidationResult with validation status
        """
        # Use validator chain for all validation checks
        is_valid, reason = await self._validator_chain.validate(input_text, agent_id)
        
        if is_valid:
            logger.info(
                "input_validated",
                _agent_id = agent_id,
                _length = len(input_text)
            )
            return ValidationResult(valid=True)
        
        return ValidationResult(valid=False, reason=reason)
    
    async def filter_output(self, _output_text: str, _agent_id: Optional[str]) -> FilterResult:
        """
        Filter agent output against guardrails.
        
        Args:
            output_text: Output text to filter
            agent_id: Agent ID for logging
            
        Returns:
            FilterResult with filtered content
        """
        if not self.config.enable_content_filter:
            return FilterResult(
                _original = output_text,
                _filtered = output_text,
                _blocked_content = None,
                _reason = None
            )
        
        _filtered = output_text
        _blocked_content = None
        _reason = None
        
        # Block personal information in output
        if self.config.block_personal_info:
            # Email addresses
            _emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', filtered)
            if emails:
                _filtered = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', filtered)
                _blocked_content = ", ".join(emails)
                _reason = "Personal email addresses redacted"
        
        # Phone numbers
        _phones = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', filtered)
        if phones:
            _filtered = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[REDACTED]', filtered)
            if blocked_content:
                blocked_content += f", {phones}"
            _reason = "Personal phone numbers redacted"
        
        # API keys - match common API key patterns
        # Patterns: sk_live_*, sk_test_*, AKIA*, ghp_*, github_pat_*, etc.
        # Note: Use [^\s] to match any non-whitespace including brackets in redacted keys
        _api_key_patterns = [
            r'\bsk_live_[^\s]{10,}\b',      # Stripe live keys (allow brackets in redacted values)
            r'\bsk_test_[^\s]{10,}\b',      # Stripe test keys
            r'\bAKIA[A-Z0-9]{16}\b',        # AWS Access Key ID
            r'\bghp_[A-Za-z0-9]{36}\b',    # GitHub personal access tokens
            r'\bgithub_pat_[^\s]{22,}\b',   # GitHub fine-grained tokens
            r'\b[A-Za-z0-9]{20,}[_-][^\s]{10,}\b',  # Generic long API keys
        ]
        _api_keys = []
        for pattern in api_key_patterns:
            api_keys.extend(re.findall(pattern, filtered))
        if api_keys:
            # Replace each API key pattern found
            for pattern in api_key_patterns:
                _filtered = re.sub(pattern, '[REDACTED]', filtered)
            if blocked_content:
                blocked_content += f", {api_keys}"
            _reason = "API keys redacted"
        
        # Block code execution in output
        if self.config.block_code_execution:
            # Shell command patterns
            if re.search(r'\b(sh|bash|cmd|powershell|exec)\s+[^\s]', filtered, re.IGNORECASE):
                _filtered = re.sub(r'\b(sh|bash|cmd|powershell|exec)\s+[^\s]', '[BLOCKED]', filtered, re.IGNORECASE)
                _blocked_content = "Shell commands"
                _reason = "Code execution blocked"
            
            # Python exec patterns
            if re.search(r'\b(exec|eval|__import__|open\()[\'"]\s*\(', filtered, re.IGNORECASE):
                _filtered = re.sub(r'\b(exec|eval|__import__|open\()[\'"]\s*\(', '[BLOCKED]', filtered, re.IGNORECASE)
                if blocked_content:
                    _blocked_content = f"{blocked_content}, Python exec"
                _reason = "Python execution blocked"
        
        if filtered != output_text:
            logger.warning(
                "output_filtered",
                _agent_id = agent_id,
                _original_length = len(output_text),
                _filtered_length = len(filtered),
                _reason = reason
            )
        
        return FilterResult(
            _original = output_text,
            _filtered = filtered,
            _blocked_content = blocked_content,
            _reason = reason
        )
    
    def add_blocked_pattern(self, _pattern: str, _description: str, _severity: str, _action: GuardrailsAction) -> None:
        """
        Add a blocked pattern to the guardrails system.
        
        Args:
            pattern: Regex pattern to block
            description: Description of the pattern
            severity: Severity level
            action: Action to take when pattern matches
        """
        blocked_pattern = BlockedPattern(
            pattern=pattern,
            description=description,
            severity=severity,
            action=action
        )
        self.config.blocked_patterns.append(blocked_pattern)
        self._blocked_patterns = self._compile_blocked_patterns()
        
        logger.info(
            "blocked_pattern_added",
            pattern=pattern,
            severity=severity
        )
    
    def remove_blocked_pattern(self, _pattern: str) -> bool:
        """
        Remove a blocked pattern from the guardrails system.
        
        Args:
            pattern: Pattern to remove
            
        Returns:
            True if pattern was removed
        """
        _original_count = len(self.config.blocked_patterns)
        self.config.blocked_patterns = [
            bp for bp in self.config.blocked_patterns
            if bp.pattern != pattern
        ]
        
        if len(self.config.blocked_patterns) < original_count:
            self._blocked_patterns = self._compile_blocked_patterns()
            logger.info(
                "blocked_pattern_removed",
                pattern=pattern
            )
            return True
        
        logger.warning(
            "blocked_pattern_not_found",
            pattern=pattern
        )
        return False
    
    def get_blocked_patterns(self) -> List[Dict[str, Any]]:
        """
        Get list of all blocked patterns.
        
        Returns:
            List of blocked pattern configurations
        """
        return [
            {
                "pattern": bp.pattern,
                "description": bp.description,
                "severity": bp.severity,
                "action": bp.action.value
            }
            for bp in self.config.blocked_patterns
        ]
    
    async def check_agent_rate_limit(self, _agent_id: str, _action: str) -> bool:
        """
        Check if agent has exceeded its rate limit.
        
        Args:
            agent_id: Agent ID
            action: Action being performed
            
        Returns:
            True if action is allowed, False otherwise
        """
        _limit = self.config.agent_rate_limits.get(agent_id, 100)
        
        # This would integrate with rate limiting system
        # For now, return True (allow all actions)
        return True


# =============================================================================
# Default Blocked Patterns
# =============================================================================

DEFAULT_BLOCKED_PATTERNS = [
    # SQL Injection patterns
    BlockedPattern(
        _pattern = r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        _description = "SQL injection attempt",
        _severity = "critical",
        _action = GuardrailsAction.BLOCK
    ),
    
    # Command injection patterns
    BlockedPattern(
        _pattern = r"(?i)(\b(sh|bash|cmd|powershell|exec)\s+[^\s])",
        _description = "Command injection attempt",
        _severity = "critical",
        _action = GuardrailsAction.BLOCK
    ),
    
    # XSS patterns
    BlockedPattern(
        _pattern = r"<script[^>]*>.*?</script>|javascript:|on\w+\s*=",
        _description = "XSS attempt",
        _severity = "critical",
        _action = GuardrailsAction.BLOCK
    ),
    
    # Path traversal patterns
    BlockedPattern(
        _pattern = r"\.\./|\.\.\\|[A-Za-z]:\\|[A-Za-z]:\.\./",
        _description = "Path traversal attempt",
        _severity = "critical",
        _action = GuardrailsAction.BLOCK
    ),
]


def create_default_guardrails() -> GuardrailsSystem:
    """
    Create a guardrails system with default blocked patterns.
    
    Returns:
        Configured GuardrailsSystem instance
    """
    _config = GuardrailsConfig(
        _blocked_patterns = DEFAULT_BLOCKED_PATTERNS.copy(),
        _block_personal_info = True,
        _block_code_execution = True,
        _enable_content_filter = True,
    )
    
    return GuardrailsSystem(config=config)
