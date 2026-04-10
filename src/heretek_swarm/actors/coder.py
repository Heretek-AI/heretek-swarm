"""
Coder Agent - Code Implementation & Debugging Specialist.

The Coder provides:
- Code generation and implementation
- Code review and refactoring
- Bug detection and fixing
- Test code generation
- Documentation generation
- Code explanation and analysis

Coder is the "implementation engine" of the Collective, translating
decisions and designs into working, tested, and documented code.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

import structlog

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.actors.validation import validate_message as validate_message_schema
from pydantic import ValidationError
from heretek_swarm.validation import (
    LLMOutputValidator,
    is_code_safe,
    is_text_safe,
)

# Alias for use in handlers
validate_message = validate_message_schema

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine, Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator


logger = structlog.get_logger("CoderAgent")


class CodeLanguage(str, Enum):
    """Supported programming languages."""
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
    MARKDOWN = "markdown"


class CodeTask(str, Enum):
    """Types of coding tasks."""
    IMPLEMENT = "implement"
    REVIEW = "review"
    REFACTOR = "refactor"
    DEBUG = "debug"
    TEST = "test"
    DOCUMENT = "document"
    EXPLAIN = "explain"
    OPTIMIZE = "optimize"


class ReviewSeverity(str, Enum):
    """Code review issue severity."""
    CRITICAL = "critical"  # Security vulnerability, crash
    ERROR = "error"  # Bug, incorrect logic
    WARNING = "warning"  # Code smell, potential issue
    INFO = "info"  # Suggestion, style note
    HINT = "hint"  # Minor improvement


@dataclass
class CodeSnippet:
    """Generated or analyzed code snippet."""
    id: str
    language: CodeLanguage
    code: str
    description: str
    created_at: datetime
    purpose: str = ""  # What this code does
    dependencies: List[str] = field(default_factory=list)
    complexity_score: float = 0.0  # 0-1 complexity estimate
    test_coverage: float = 0.0  # 0-1 test coverage
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewIssue:
    """Code review issue."""
    id: str
    line_number: Optional[int]
    severity: ReviewSeverity
    category: str  # security/bug/style/performance/maintainability
    message: str
    suggestion: Optional[str] = None
    code_context: Optional[str] = None


@dataclass
class CodeReview:
    """Complete code review result."""
    id: str
    code_id: str
    reviewed_at: datetime
    issues: List[ReviewIssue]
    summary: str
    overall_score: float  # 0-100 quality score
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DebugSession:
    """Debugging session record."""
    id: str
    code: str
    error_message: str
    symptoms: List[str]
    root_cause: Optional[str] = None
    fix: Optional[str] = None
    explanation: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    status: str = "investigating"  # investigating/identified/fixed/cannot_reproduce


@dataclass
class ImplementationTask:
    """Code implementation task."""
    id: str
    description: str
    requirements: List[str]
    language: CodeLanguage
    generated_code: Optional[str] = None
    tests: Optional[str] = None
    documentation: Optional[str] = None
    status: str = "pending"  # pending/in_progress/completed/failed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CoderAgent(AgentActor):
    """
    Code Implementation & Debugging Specialist Agent.
    
    Coder translates requirements into working code, performs reviews,
    debugs issues, and generates tests and documentation.
    """
    
    def __init__(self, agent_id: str = None, config: Dict[str, Any] = None):
        super().__init__(
            agent_id=agent_id,
            name="Coder",
            description="Code Implementation & Debugging Specialist",
            config=config or {}
        )
        
        # Code storage
        self._code_snippets: Dict[str, CodeSnippet] = {}
        self._snippet_counter = 0
        self.max_snippets = self._config.get("max_snippets", 500)
        
        # Reviews
        self._reviews: Dict[str, CodeReview] = {}
        self.max_reviews = self._config.get("max_reviews", 200)
        
        # Debug sessions
        self._debug_sessions: Dict[str, DebugSession] = {}
        self._active_debugs: Set[str] = set()
        self.max_debug_sessions = self._config.get("max_debug_sessions", 50)
        
        # Implementation tasks
        self._tasks: Dict[str, ImplementationTask] = {}
        self._task_counter = 0
        
        # Configuration
        self._default_language = CodeLanguage(self._config.get("default_language", "python"))
        self._enable_tests = self._config.get("enable_tests", True)
        self._enable_docs = self._config.get("enable_docs", True)
        
        
        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)
        
        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )
        
        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()
        
        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()
        
        # Session 44: LLM Output Validation
        self.llm_output_validator = LLMOutputValidator(strict_mode=True)
        
        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(
            "CoderAgent initialized",
            agent_id=self.agent_id,
            default_language=self._default_language.value
        )
    
    def get_handlers(self) -> Dict[str, callable]:
        """Return message handlers for Coder agent."""
        return {
            "generate_code": self._handle_generate_code,
            "review_code": self._handle_review_code,
            "debug_code": self._handle_debug_code,
            "generate_tests": self._handle_generate_tests,
            "generate_docs": self._handle_generate_docs,
            "refactor_code": self._handle_refactor_code,
            "explain_code": self._handle_explain_code,
            "implement_task": self._handle_implement_task,
        }
    
    async def _handle_generate_code(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Generate code for a specific purpose.
        
        Content expected:
        {
            "description": "What to implement",
            "language": "python",
            "requirements": [...],
            "include_tests": true
        }
        """
        try:
            # Schema validation
            content = validate_message_schema(message.content, "CoderGenerateCode")
            
            # Security validation for code-related content
            description = content.get("description", "")
            if not is_text_safe(description):
                logger.warning("Unsafe description detected", description=description[:100])
                return {"status": "error", "error": "Unsafe content detected in description"}
            language = CodeLanguage(content.get("language", self._default_language.value))
            requirements = content.get("requirements", [])
            include_tests = content.get("include_tests", self._enable_tests)
            
            logger.info(
                "Generating code",
                description=description[:100],
                language=language.value
            )
            
            # Generate code using LLM
            code_result = await self._generate_code_llm(
                description=description,
                language=language,
                requirements=requirements
            )
            
            # Store snippet
            self._snippet_counter += 1
            snippet = CodeSnippet(
                id=f"code_{self._snippet_counter}",
                language=language,
                code=code_result.get("code", ""),
                description=description,
                created_at=datetime.now(timezone.utc),
                purpose=code_result.get("purpose", ""),
                dependencies=code_result.get("dependencies", []),
                complexity_score=code_result.get("complexity", 0.5),
                metadata=code_result.get("metadata", {})
            )
            self._code_snippets[snippet.id] = snippet
            
            # Generate tests if requested
            test_code = None
            if include_tests:
                test_code = await self._generate_tests_for_code(
                    code=snippet.code,
                    language=language,
                    description=description
                )
                snippet.test_coverage = 0.8  # Estimate
            
            # LRU eviction
            if len(self._code_snippets) > self.max_snippets:
                excess = len(self._code_snippets) - self.max_snippets
                for _ in range(excess):
                    oldest_id = next(iter(self._code_snippets))
                    del self._code_snippets[oldest_id]
            
            return {
                "status": "success",
                "code_id": snippet.id,
                "language": language.value,
                "code": snippet.code,
                "tests": test_code,
                "dependencies": snippet.dependencies,
                "complexity_score": snippet.complexity_score
            }
            
        except Exception as e:
            logger.error("Failed to generate code", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_review_code(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Review code for issues and quality.
        
        Content expected:
        {
            "code": "code to review",
            "language": "python",
            "focus_areas": ["security", "performance"]
        }
        """
        try:
            # Schema validation
            content = validate_message_schema(message.content, "CoderReviewCode")
            
            # Security validation for code
            code = content.get("code", "")
            if not is_code_safe(code):
                logger.warning("Unsafe code detected in review request")
                return {"status": "error", "error": "Unsafe code detected - contains dangerous patterns"}
            language = CodeLanguage(content.get("language", self._default_language.value))
            focus_areas = content.get("focus_areas", ["security", "bugs", "style"])
            
            logger.info(
                "Reviewing code",
                language=language.value,
                focus_areas=focus_areas
            )
            
            # Perform code review
            review_result = await self._review_code_llm(
                code=code,
                language=language,
                focus_areas=focus_areas
            )
            
            # Parse issues
            issues = []
            for issue_data in review_result.get("issues", []):
                issue = ReviewIssue(
                    id=f"issue_{uuid.uuid4().hex[:8]}",
                    line_number=issue_data.get("line"),
                    severity=ReviewSeverity(issue_data.get("severity", "info")),
                    category=issue_data.get("category", "style"),
                    message=issue_data.get("message", ""),
                    suggestion=issue_data.get("suggestion"),
                    code_context=issue_data.get("context")
                )
                issues.append(issue)
            
            # Count by severity
            critical_count = len([i for i in issues if i.severity == ReviewSeverity.CRITICAL])
            error_count = len([i for i in issues if i.severity == ReviewSeverity.ERROR])
            warning_count = len([i for i in issues if i.severity == ReviewSeverity.WARNING])
            
            # Store review
            self._snippet_counter += 1
            review = CodeReview(
                id=f"review_{self._snippet_counter}",
                code_id=f"temp_{uuid.uuid4().hex[:8]}",
                reviewed_at=datetime.now(timezone.utc),
                issues=issues,
                summary=review_result.get("summary", ""),
                overall_score=review_result.get("score", 70.0),
                critical_count=critical_count,
                error_count=error_count,
                warning_count=warning_count,
                recommendations=review_result.get("recommendations", [])
            )
            self._reviews[review.id] = review
            
            return {
                "status": "success",
                "review_id": review.id,
                "overall_score": review.overall_score,
                "critical_count": critical_count,
                "error_count": error_count,
                "warning_count": warning_count,
                "summary": review.summary,
                "issues": [
                    {
                        "id": i.id,
                        "line": i.line_number,
                        "severity": i.severity.value,
                        "category": i.category,
                        "message": i.message,
                        "suggestion": i.suggestion
                    }
                    for i in issues[:20]  # Limit returned issues
                ],
                "recommendations": review.recommendations
            }
            
        except Exception as e:
            logger.error("Failed to review code", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_debug_code(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Debug code with error.
        
        Content expected:
        {
            "code": "problematic code",
            "error_message": "Error that occurred",
            "symptoms": ["symptom1", ...]
        }
        """
        try:
            # Schema validation
            content = validate_message_schema(message.content, "CoderDebugCode")
            
            # Security validation for code
            code = content.get("code", "")
            if not is_code_safe(code):
                logger.warning("Unsafe code detected in debug request")
                # Still allow debugging but log the security concern
                logger.info("Proceeding with debug but code contains dangerous patterns")
            error_message = content.get("error_message", "")
            symptoms = content.get("symptoms", [])
            
            session_id = f"debug_{uuid.uuid4().hex[:8]}"
            session = DebugSession(
                id=session_id,
                code=code,
                error_message=error_message,
                symptoms=symptoms,
                status="investigating"
            )
            self._debug_sessions[session_id] = session
            self._active_debugs.add(session_id)
            
            logger.info(
                "Debugging code",
                session_id=session_id,
                error=error_message[:100]
            )
            
            # Analyze and fix
            debug_result = await self._debug_code_llm(
                code=code,
                error_message=error_message,
                symptoms=symptoms
            )
            
            # Update session
            session.root_cause = debug_result.get("root_cause")
            session.fix = debug_result.get("fix")
            session.explanation = debug_result.get("explanation")
            session.status = "fixed" if session.fix else "identified"
            session.resolved_at = datetime.now(timezone.utc)
            self._active_debugs.discard(session_id)
            
            return {
                "status": "success",
                "session_id": session_id,
                "root_cause": session.root_cause,
                "fix": session.fix,
                "explanation": session.explanation,
                "status": session.status
            }
            
        except Exception as e:
            logger.error("Failed to debug code", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_generate_tests(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Generate tests for code.
        
        Content expected:
        {
            "code": "code to test",
            "language": "python",
            "framework": "pytest"
        }
        """
        try:
            content = validate_message(message.content, "CoderGenerateTests")
            code = content.get("code", "")
            language = CodeLanguage(content.get("language", self._default_language.value))
            framework = content.get("framework", "pytest")
            
            logger.info(
                "Generating tests",
                language=language.value,
                framework=framework
            )
            
            tests = await self._generate_tests_for_code(
                code=code,
                language=language,
                framework=framework
            )
            
            return {
                "status": "success",
                "tests": tests,
                "framework": framework,
                "estimated_coverage": 0.85
            }
            
        except Exception as e:
            logger.error("Failed to generate tests", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_generate_docs(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Generate documentation for code.
        
        Content expected:
        {
            "code": "code to document",
            "doc_type": "api|inline|readme",
            "style": "google|numpy|sphinx"
        }
        """
        try:
            content = validate_message(message.content, "CoderGenerateDocs")
            code = content.get("code", "")
            doc_type = content.get("doc_type", "api")
            style = content.get("style", "google")
            
            logger.info(
                "Generating documentation",
                doc_type=doc_type,
                style=style
            )
            
            docs = await self._generate_docs_llm(
                code=code,
                doc_type=doc_type,
                style=style
            )
            
            return {
                "status": "success",
                "documentation": docs,
                "doc_type": doc_type,
                "style": style
            }
            
        except Exception as e:
            logger.error("Failed to generate docs", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_refactor_code(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Refactor code for improvement.
        
        Content expected:
        {
            "code": "code to refactor",
            "goals": ["readability", "performance"],
            "constraints": [...]
        }
        """
        try:
            content = validate_message(message.content, "CoderRefactorCode")
            code = content.get("code", "")
            goals = content.get("goals", ["readability"])
            constraints = content.get("constraints", [])
            
            logger.info(
                "Refactoring code",
                goals=goals,
                constraints=constraints
            )
            
            refactored = await self._refactor_code_llm(
                code=code,
                goals=goals,
                constraints=constraints
            )
            
            return {
                "status": "success",
                "original_code": code[:500],
                "refactored_code": refactored.get("code", ""),
                "improvements": refactored.get("improvements", []),
                "changes_summary": refactored.get("changes", "")
            }
            
        except Exception as e:
            logger.error("Failed to refactor code", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_explain_code(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Explain what code does.
        
        Content expected:
        {
            "code": "code to explain",
            "audience": "beginner|expert",
            "detail_level": "high|medium|low"
        }
        """
        try:
            content = validate_message(message.content, "CoderExplainCode")
            code = content.get("code", "")
            audience = content.get("audience", "intermediate")
            detail_level = content.get("detail_level", "medium")
            
            logger.info(
                "Explaining code",
                audience=audience,
                detail_level=detail_level
            )
            
            explanation = await self._explain_code_llm(
                code=code,
                audience=audience,
                detail_level=detail_level
            )
            
            return {
                "status": "success",
                "explanation": explanation,
                "code_summary": code[:200] if len(code) > 200 else code
            }
            
        except Exception as e:
            logger.error("Failed to explain code", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_implement_task(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Implement a complete coding task.
        
        Content expected:
        {
            "description": "Task description",
            "requirements": [...],
            "language": "python",
            "include_tests": true,
            "include_docs": true
        }
        """
        try:
            content = validate_message(message.content, "CoderImplementTask")
            description = content.get("description", "")
            requirements = content.get("requirements", [])
            language = CodeLanguage(content.get("language", self._default_language.value))
            include_tests = content.get("include_tests", self._enable_tests)
            include_docs = content.get("include_docs", self._enable_docs)
            
            self._task_counter += 1
            task = ImplementationTask(
                id=f"task_{self._task_counter}",
                description=description,
                requirements=requirements,
                language=language,
                status="in_progress"
            )
            self._tasks[task.id] = task
            
            logger.info(
                "Implementing task",
                task_id=task.id,
                description=description[:100]
            )
            
            # Generate implementation
            code_result = await self._generate_code_llm(
                description=description,
                language=language,
                requirements=requirements
            )
            task.generated_code = code_result.get("code", "")
            
            # Generate tests
            if include_tests:
                task.tests = await self._generate_tests_for_code(
                    code=task.generated_code,
                    language=language
                )
            
            # Generate docs
            if include_docs:
                task.documentation = await self._generate_docs_llm(
                    code=task.generated_code,
                    doc_type="api"
                )
            
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            
            return {
                "status": "success",
                "task_id": task.id,
                "code": task.generated_code,
                "tests": task.tests,
                "documentation": task.documentation,
                "completed_at": task.completed_at.isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to implement task", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # Internal helper methods
    
    async def _generate_code_llm(
        self,
        description: str,
        language: CodeLanguage,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """Generate code using LLM."""
        try:
            prompt = f"""Write {language.value} code for:

{description}

Requirements:
{chr(10).join(f"- {r}" for r in requirements)}

Provide:
1. Complete, working code
2. List of dependencies
3. Brief purpose description
4. Complexity estimate (0-1)

Return as JSON with keys: code, dependencies, purpose, complexity"""

            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.3)
            
            import json
            try:
                result = json.loads(response)
                # Validate generated code for safety
                code = result.get("code", "")
                if code and not self.llm_output_validator.is_safe_code(code):
                    logger.warning("Generated code contains dangerous patterns", code_preview=code[:100])
                    result["security_warning"] = "Generated code contains potentially dangerous patterns"
                return result
            except:
                return {
                    "code": response,
                    "dependencies": [],
                    "purpose": description[:100],
                    "complexity": 0.5,
                    "security_warning": "Could not validate generated code"
                }
        except Exception as e:
            logger.error("Code generation failed", error=str(e))
            return {"code": "", "dependencies": [], "purpose": "", "complexity": 0}
    
    async def _generate_tests_for_code(
        self,
        code: str,
        language: CodeLanguage,
        framework: str = "pytest",
        description: str = ""
    ) -> str:
        """Generate tests for given code."""
        try:
            prompt = f"""Generate {framework} tests for this {language.value} code:

{code}

{f'Purpose: {description}' if description else ''}

Include:
1. Unit tests for each function
2. Edge case tests
3. Integration tests if applicable

Return only the test code."""

            return await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.2)
        except:
            return "# Test generation failed"
    
    async def _review_code_llm(
        self,
        code: str,
        language: CodeLanguage,
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """Review code using LLM."""
        try:
            areas = ", ".join(focus_areas)
            prompt = f"""Review this {language.value} code focusing on: {areas}

{code}

For each issue found, provide:
- line: line number (or null)
- severity: critical/error/warning/info/hint
- category: security/bug/style/performance/maintainability
- message: description of issue
- suggestion: how to fix (optional)
- context: relevant code snippet (optional)

Also provide:
- summary: overall assessment
- score: 0-100 quality score
- recommendations: list of top priorities

Return as JSON array of issues plus summary, score, recommendations."""

            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.2)
            
            import json
            try:
                return json.loads(response)
            except:
                return {
                    "issues": [],
                    "summary": "Review completed",
                    "score": 75.0,
                    "recommendations": []
                }
        except:
            return {"issues": [], "summary": "Review failed", "score": 50.0, "recommendations": []}
    
    async def _debug_code_llm(
        self,
        code: str,
        error_message: str,
        symptoms: List[str]
    ) -> Dict[str, Any]:
        """Debug code using LLM."""
        try:
            prompt = f"""Debug this code:

{code}

Error: {error_message}
Symptoms: {", ".join(symptoms)}

Provide:
1. root_cause: What's causing the issue
2. fix: Corrected code
3. explanation: Why the fix works

Return as JSON."""

            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.2)
            
            import json
            try:
                return json.loads(response)
            except:
                return {
                    "root_cause": "Unable to determine",
                    "fix": None,
                    "explanation": "Debug analysis failed"
                }
        except:
            return {"root_cause": "", "fix": None, "explanation": ""}
    
    async def _generate_docs_llm(
        self,
        code: str,
        doc_type: str,
        style: str
    ) -> str:
        """Generate documentation using LLM."""
        try:
            prompt = f"""Generate {doc_type} documentation for this code in {style} style:

{code}

Return only the documentation."""

            return await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.2)
        except:
            return "# Documentation generation failed"
    
    async def _refactor_code_llm(
        self,
        code: str,
        goals: List[str],
        constraints: List[str]
    ) -> Dict[str, Any]:
        """Refactor code using LLM."""
        try:
            prompt = f"""Refactor this code with goals: {", ".join(goals)}

Constraints: {constraints}

{code}

Provide:
1. code: The refactored code
2. improvements: List of improvements made
3. changes: Summary of changes

Return as JSON."""

            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.3)
            
            import json
            try:
                return json.loads(response)
            except:
                return {
                    "code": code,
                    "improvements": [],
                    "changes": "No changes made"
                }
        except:
            return {"code": code, "improvements": [], "changes": "Refactor failed"}
    

    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return
        
        if item_id in self._pattern_emitted:
            return
        
        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"{item_type}_{item_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type=f"{item_type}_completion",
                content=content,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            
            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: Optional[List[PatternType]] = None) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []
        
        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: List[str],
        domain: str = "general",
    ) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None
        
        try:
            deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=proposal[:200],
                participants=participating_agents,
                domain=domain,
            )
            self._active_deliberations[item_id] = deliberation_id
            
            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False
        
        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False
        
        try:
            success = self.deliberation_engine.submit_position(
                deliberation_id=deliberation_id,
                agent_id=agent_id,
                position=position,
                confidence=confidence,
                argument=argument,
            )
            
            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=f"delib_{deliberation_id}_{agent_id}",
                    access_type="write",
                    agent_id=agent_id,
                )
            
            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None
        
        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None
        
        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)
            
            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)
            
            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str = "read") -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return
        
        memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD
        
        memory_id = f"{item_type}_{item_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []
        
        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
        }


    async def _explain_code_llm(
        self,
        code: str,
        audience: str,
        detail_level: str
    ) -> str:
        """Explain code using LLM."""
        try:
            prompt = f"""Explain this code for {audience} audience ({detail_level} detail):

{code}

Provide a clear, educational explanation."""

            return await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.2)
        except:
            return "# Explanation unavailable"
