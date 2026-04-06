"""
Guardrails System for Heretek Swarm

Provides input validation, output filtering, and content safety checks.
Reference: PraisonAI guardrails pattern
"""

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


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
    
    def __init__(self, config: Optional[GuardrailsConfig] = None):
        """
        Initialize guardrails system.
        
        Args:
            config: Guardrails configuration
        """
        self.config = config or GuardrailsConfig()
        self._blocked_patterns = self._compile_blocked_patterns()
        logger.info(
            "guardrails_initialized",
            blocked_patterns_count=len(self.config.blocked_patterns),
            max_input_length=self.config.max_input_length
        )
    
    def _compile_blocked_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for efficient matching"""
        compiled = []
        for bp in self.config.blocked_patterns:
            try:
                pattern = re.compile(bp.pattern, re.IGNORECASE)
                compiled.append(pattern)
            except re.error as e:
                logger.warning(
                    "invalid_pattern",
                    pattern=bp.pattern,
                    error=str(e)
                )
        return compiled
    
    async def validate_input(
        self,
        input_text: str,
        agent_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate user input against guardrails.
        
        Args:
            input_text: Input text to validate
            agent_id: Agent ID for logging
            
        Returns:
            ValidationResult with validation status
        """
        # Check length limits
        if len(input_text) < self.config.min_input_length:
            logger.warning(
                "input_too_short",
                agent_id=agent_id,
                length=len(input_text)
            )
            return ValidationResult(
                valid=False,
                reason="Input too short",
                max_length=self.config.max_input_length,
                min_length=self.config.min_input_length
            )
        
        if len(input_text) > self.config.max_input_length:
            logger.warning(
                "input_too_long",
                agent_id=agent_id,
                length=len(input_text),
                max_length=self.config.max_input_length
            )
            return ValidationResult(
                valid=False,
                reason="Input too long",
                max_length=self.config.max_input_length,
                min_length=self.config.min_input_length
            )
        
        # Check blocked patterns
        for pattern in self._blocked_patterns:
            match = pattern.search(input_text)
            if match:
                logger.warning(
                    "input_blocked",
                    agent_id=agent_id,
                    pattern=pattern.pattern,
                    match=match.group(0)
                )
                return ValidationResult(
                    valid=False,
                    reason=pattern.description,
                    pattern=pattern.pattern,
                    modified_content=None
                )
        
        # Check for personal information disclosure
        if self.config.block_personal_info:
            # Email addresses
            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', input_text):
                logger.warning(
                    "input_blocked_personal_email",
                    agent_id=agent_id
                )
                return ValidationResult(
                    valid=False,
                    reason="Personal email address detected",
                    modified_content=None
                )
            
            # Phone numbers
            if re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', input_text):
                logger.warning(
                    "input_blocked_personal_phone",
                    agent_id=agent_id
                )
                return ValidationResult(
                    valid=False,
                    reason="Personal phone number detected",
                    modified_content=None
                )
            
            # SSN patterns
            if re.search(r'\b\d{3}[-]\d{2}[-]\d{4}\b', input_text):
                logger.warning(
                    "input_blocked_personal_ssn",
                    agent_id=agent_id
                )
                return ValidationResult(
                    valid=False,
                    reason="Personal SSN pattern detected",
                    modified_content=None
                )
            
            # API keys
            if re.search(r'\b[A-Za-z0-9]{20,}[_-][A-Za-z0-9]{10,}\b', input_text):
                logger.warning(
                    "input_blocked_personal_api_key",
                    agent_id=agent_id
                )
                return ValidationResult(
                    valid=False,
                    reason="API key pattern detected",
                    modified_content=None
                )
        
        # Check for code execution attempts
        if self.config.block_code_execution:
            # Shell command patterns
            if re.search(r'\b(sh|bash|cmd|powershell|exec)\s+[^\s]', input_text, re.IGNORECASE):
                logger.warning(
                    "input_blocked_code_execution",
                    agent_id=agent_id
                )
                return ValidationResult(
                    valid=False,
                    reason="Code execution attempt detected",
                    modified_content=None
                )
            
            # Python exec patterns
            if re.search(r'\b(exec|eval|__import__|open\()[\'"]\s*\(', input_text, re.IGNORECASE):
                logger.warning(
                    "input_blocked_python_execution",
                    agent_id=agent_id
                )
                return ValidationResult(
                    valid=False,
                    reason="Python execution attempt detected",
                    modified_content=None
                )
        
        # Check allowed patterns
        if self.config.allowed_patterns:
            allowed = False
            for pattern in self.config.allowed_patterns:
                if re.search(pattern, input_text, re.IGNORECASE):
                    allowed = True
                    break
            
            if not allowed:
                logger.warning(
                    "input_not_allowed",
                    agent_id=agent_id,
                    input=input_text[:100]
                )
                return ValidationResult(
                    valid=False,
                    reason="Input does not match allowed patterns",
                    modified_content=None
                )
        
        # Input passed all checks
        logger.info(
            "input_validated",
            agent_id=agent_id,
            length=len(input_text)
        )
        return ValidationResult(valid=True)
    
    async def filter_output(
        self,
        output_text: str,
        agent_id: Optional[str] = None
    ) -> FilterResult:
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
                original=output_text,
                filtered=output_text,
                blocked_content=None,
                reason=None
            )
        
        filtered = output_text
        blocked_content = None
        reason = None
        
        # Block personal information in output
        if self.config.block_personal_info:
            # Email addresses
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', filtered)
            if emails:
                filtered = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', filtered)
                blocked_content = ", ".join(emails)
                reason = "Personal email addresses redacted"
        
        # Phone numbers
        phones = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', filtered)
        if phones:
            filtered = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[REDACTED]', filtered)
            if blocked_content:
                blocked_content += f", {phones}"
            reason = "Personal phone numbers redacted"
        
        # API keys
        api_keys = re.findall(r'\b[A-Za-z0-9]{20,}[_-][A-Za-z0-9]{10,}\b', filtered)
        if api_keys:
            filtered = re.sub(r'\b[A-Za-z0-9]{20,}[_-][A-Za-z0-9]{10,}\b', '[REDACTED]', filtered)
            if blocked_content:
                blocked_content += f", {api_keys}"
                reason = "API keys redacted"
        
        # Block code execution in output
        if self.config.block_code_execution:
            # Shell command patterns
            if re.search(r'\b(sh|bash|cmd|powershell|exec)\s+[^\s]', filtered, re.IGNORECASE):
                filtered = re.sub(r'\b(sh|bash|cmd|powershell|exec)\s+[^\s]', '[BLOCKED]', filtered, re.IGNORECASE)
                blocked_content = "Shell commands"
                reason = "Code execution blocked"
            
            # Python exec patterns
            if re.search(r'\b(exec|eval|__import__|open\()[\'"]\s*\(', filtered, re.IGNORECASE):
                filtered = re.sub(r'\b(exec|eval|__import__|open\()[\'"]\s*\(', '[BLOCKED]', filtered, re.IGNORECASE)
                if blocked_content:
                    blocked_content = f"{blocked_content}, Python exec"
                reason = "Python execution blocked"
        
        if filtered != output_text:
            logger.warning(
                "output_filtered",
                agent_id=agent_id,
                original_length=len(output_text),
                filtered_length=len(filtered),
                reason=reason
            )
        
        return FilterResult(
            original=output_text,
            filtered=filtered,
            blocked_content=blocked_content,
            reason=reason
        )
    
    def add_blocked_pattern(
        self,
        pattern: str,
        description: str,
        severity: str = "medium",
        action: GuardrailsAction = GuardrailsAction.BLOCK
    ) -> None:
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
    
    def remove_blocked_pattern(self, pattern: str) -> bool:
        """
        Remove a blocked pattern from the guardrails system.
        
        Args:
            pattern: Pattern to remove
            
        Returns:
            True if pattern was removed
        """
        original_count = len(self.config.blocked_patterns)
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
    
    async def check_agent_rate_limit(
        self,
        agent_id: str,
        action: str
    ) -> bool:
        """
        Check if agent has exceeded its rate limit.
        
        Args:
            agent_id: Agent ID
            action: Action being performed
            
        Returns:
            True if action is allowed, False otherwise
        """
        limit = self.config.agent_rate_limits.get(agent_id, 100)
        
        # This would integrate with rate limiting system
        # For now, return True (allow all actions)
        return True


# =============================================================================
# Default Blocked Patterns
# =============================================================================

DEFAULT_BLOCKED_PATTERNS = [
    # SQL Injection patterns
    BlockedPattern(
        pattern=r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        description="SQL injection attempt",
        severity="critical",
        action=GuardrailsAction.BLOCK
    ),
    
    # Command injection patterns
    BlockedPattern(
        pattern=r"(?i)(\b(sh|bash|cmd|powershell|exec)\s+[^\s])",
        description="Command injection attempt",
        severity="critical",
        action=GuardrailsAction.BLOCK
    ),
    
    # XSS patterns
    BlockedPattern(
        pattern=r"<script[^>]*>.*?</script>|javascript:|on\w+\s*=",
        description="XSS attempt",
        severity="critical",
        action=GuardrailsAction.BLOCK
    ),
    
    # Path traversal patterns
    BlockedPattern(
        pattern=r"\.\./|\.\.\\|[A-Za-z]:\\|[A-Za-z]:\.\./",
        description="Path traversal attempt",
        severity="critical",
        action=GuardrailsAction.BLOCK
    ),
]


def create_default_guardrails() -> GuardrailsSystem:
    """
    Create a guardrails system with default blocked patterns.
    
    Returns:
        Configured GuardrailsSystem instance
    """
    config = GuardrailsConfig(
        blocked_patterns=DEFAULT_BLOCKED_PATTERNS.copy(),
        block_personal_info=True,
        block_code_execution=True,
        enable_content_filter=True,
    )
    
    return GuardrailsSystem(config=config)
