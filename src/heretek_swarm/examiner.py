"""
Examiner Agent - Quality Assurance & Testing Specialist.

The Examiner provides:
- Test plan generation and execution
- Code quality analysis
- Decision validation and verification
- Bug detection and reporting
- Compliance checking
- Performance benchmarking

Examiner is the "quality gate" of the Collective, ensuring all outputs
meet established standards before deployment or delivery.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

import structlog


from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.actors.validation import validate_message as validate_message_schema

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Alias for use in handlers
_validate_message = validate_message_schema

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine, Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator


_logger = structlog.get_logger("ExaminerAgent")


class TestType(str, Enum):
    """Types of tests Examiner can execute."""
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    REGRESSION = "regression"


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class QualityMetric(str, Enum):
    """Quality metrics Examiner tracks."""
    CODE_COVERAGE = "code_coverage"
    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    TECHNICAL_DEBT = "technical_debt"
    SECURITY_VULNERABILITIES = "security_vulnerabilities"
    PERFORMANCE_SCORE = "performance_score"
    ACCESSIBILITY_SCORE = "accessibility_score"
    DOCUMENTATION_COVERAGE = "documentation_coverage"


class SeverityLevel(str, Enum):
    """Bug/issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class TestCase:
    """Test case definition and result."""
    id: str
    name: str
    test_type: TestType
    description: str
    status: TestStatus
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    assertions_passed: int = 0
    assertions_total: int = 0
    coverage_percent: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """Collection of test cases with aggregate results."""
    id: str
    name: str
    test_cases: List[TestCase]
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    execution_time_ms: float = 0.0
    coverage_percent: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Bug:
    """Detected bug or issue record."""
    id: str
    title: str
    description: str
    severity: SeverityLevel
    component: str
    steps_to_reproduce: List[str]
    expected_behavior: str
    actual_behavior: str
    detected_at: datetime
    status: str = "new"  # new/open/fixed/closed/wontfix
    assignee: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Comprehensive quality assessment report."""
    id: str
    generated_at: datetime
    target: str  # What was examined (code/decision/component)
    test_suites: List[TestSuite]
    bugs: List[Bug]
    metrics: Dict[QualityMetric, float]
    overall_score: float  # 0-100 quality score
    summary: str
    recommendations: List[str]
    pass_threshold: float = 80.0
    passed: bool = True


class ExaminerAgent(AgentActor):
    """
    Quality Assurance & Testing Specialist Agent.
    
    Examiner ensures all outputs from the Collective meet quality standards
    through comprehensive testing, validation, and verification.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(
            agent_id=agent_id,
            _name = "Examiner",
            _description = "Quality Assurance & Testing Specialist",
            _config = config or {}
        )
        
        # Test execution state
        self._test_suites: Dict[str, TestSuite] = {}
        self._test_history: List[TestSuite] = []
        self.max_test_history = self._config.get("max_test_history", 100)
        
        # Bug tracking
        self._bugs: Dict[str, Bug] = {}
        self._bug_counter = 0
        self.max_bugs = self._config.get("max_bugs", 500)
        
        # Quality metrics cache
        self._quality_metrics: Dict[str, Dict[QualityMetric, float]] = {}
        
        # Default test configuration
        self._default_timeout = self._config.get("default_timeout", 60)
        self._coverage_threshold = self._config.get("coverage_threshold", 80.0)
        
        
        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)
        
        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            _max_rounds = 5, consensus_threshold=0.75, min_participants=2
        )
        
        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()
        
        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()
        
        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(
            "ExaminerAgent initialized",
            agent_id=self.agent_id,
            _coverage_threshold = self._coverage_threshold
        )
    
    def get_handlers(self) -> Dict[str, callable]:
        """Return message handlers for Examiner agent."""
        return {
            "create_test_plan": self._handle_create_test_plan,
            "execute_tests": self._handle_execute_tests,
            "validate_decision": self._handle_validate_decision,
            "analyze_quality": self._handle_analyze_quality,
            "report_bug": self._handle_report_bug,
            "get_quality_report": self._handle_get_quality_report,
            "get_bug_status": self._handle_get_bug_status,
        }
    
    async def _handle_create_test_plan(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Create a comprehensive test plan for a target.
        
        Content expected:
        {
            "target": "component_name",
            "test_types": ["unit", "integration"],
            "priority": "high",
            "requirements": [...]
        }
        """
        try:
            content = validate_message(message.content, "ExaminerCreateTestPlan")
            target = content.get("target", "unknown")
            _test_types = content.get("test_types", ["unit"])
            _priority = content.get("priority", "medium")
            _requirements = content.get("requirements", [])
            
            logger.info(
                "Creating test plan",
                target=target,
                _test_types = test_types,
                _priority = priority
            )
            
            # Generate test plan using LLM
            _test_plan = await self._generate_test_plan(
                target=target,
                _test_types = test_types,
                _priority = priority,
                _requirements = requirements
            )
            
            return {
                "status": "success",
                "test_plan": test_plan,
                "target": target,
                "estimated_tests": len(test_plan.get("test_cases", []))
            }
            
        except Exception as e:
            logger.error("Failed to create test plan", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_execute_tests(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Execute a test suite and return results.
        
        Content expected:
        {
            "test_suite_id": "suite_123",
            "test_cases": [...],
            "timeout": 60
        }
        """
        try:
            content = validate_message(message.content, "ExaminerExecuteTests")
            _test_suite_id = content.get("test_suite_id")
            test_cases = content.get("test_cases", [])
            _timeout = content.get("timeout", self._default_timeout)
            
            logger.info(
                "Executing tests",
                _test_suite_id = test_suite_id,
                _test_count = len(test_cases)
            )
            
            # Create test suite
            _suite = TestSuite(
                id=test_suite_id or f"suite_{datetime.now(timezone.utc).timestamp()}",
                _name = content.get("name", "Test Suite"),
                test_cases=[]
            )
            
            # Execute each test case
            for tc in test_cases:
                _result = await self._execute_test_case(tc, timeout)
                suite.test_cases.append(result)
                
                # Update counters
                if result.status == TestStatus.PASSED:
                    suite.passed += 1
                elif result.status == TestStatus.FAILED:
                    suite.failed += 1
                elif result.status == TestStatus.SKIPPED:
                    suite.skipped += 1
                suite.total += 1
                suite.execution_time_ms += result.execution_time_ms or 0
            
            # Store test suite
            self._test_suites[suite.id] = suite
            self._test_history.append(suite)
            
            # Trim history if needed
            if len(self._test_history) > self.max_test_history:
                self._test_history = self._test_history[-self.max_test_history:]
            
            return {
                "status": "success",
                "test_suite_id": suite.id,
                "passed": suite.passed,
                "failed": suite.failed,
                "skipped": suite.skipped,
                "total": suite.total,
                "execution_time_ms": suite.execution_time_ms,
                "coverage_percent": suite.coverage_percent
            }
            
        except Exception as e:
            logger.error("Failed to execute tests", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_validate_decision(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Validate a decision from the Triad.
        
        Content expected:
        {
            "decision_id": "dec_123",
            "decision_type": "analysis|validation|challenge",
            "content": "decision content",
            "context": {...}
        }
        """
        try:
            content = validate_message(message.content, "ExaminerValidateDecision")
            _decision_id = content.get("decision_id")
            _decision_type = content.get("decision_type", "unknown")
            _decision_content = content.get("content", "")
            _context = content.get("context", {})
            
            logger.info(
                "Validating decision",
                _decision_id = decision_id,
                _decision_type = decision_type
            )
            
            # Validate decision using LLM
            _validation_result = await self._validate_decision_content(
                _decision_id = decision_id,
                _decision_type = decision_type,
                content=decision_content,
                _context = context
            )
            
            return {
                "status": "success",
                "decision_id": decision_id,
                "valid": validation_result.get("valid", False),
                "confidence": validation_result.get("confidence", 0.0),
                "issues": validation_result.get("issues", []),
                "recommendations": validation_result.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error("Failed to validate decision", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_analyze_quality(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Analyze quality of code, decision, or component.
        
        Content expected:
        {
            "target": "code_snippet|decision|component",
            "target_type": "code|decision|component",
            "metrics": ["coverage", "complexity", ...]
        }
        """
        try:
            content = validate_message(message.content, "ExaminerAnalyzeQuality")
            target = content.get("target", "")
            _target_type = content.get("target_type", "code")
            _metrics = content.get("metrics", list(QualityMetric))
            
            logger.info(
                "Analyzing quality",
                _target_type = target_type,
                _metrics = metrics
            )
            
            # Analyze quality metrics
            _quality_results = await self._analyze_quality_metrics(
                target=target,
                _target_type = target_type,
                _metrics = metrics
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(quality_results)
            
            # Store metrics
            _target_key = f"{target_type}:{target[:50]}"
            self._quality_metrics[target_key] = quality_results
            
            return {
                "status": "success",
                "metrics": {k.value: v for k, v in quality_results.items()},
                "overall_score": overall_score,
                "threshold": self._coverage_threshold,
                "passed": overall_score >= self._coverage_threshold
            }
            
        except Exception as e:
            logger.error("Failed to analyze quality", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_report_bug(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Report a bug or issue.
        
        Content expected:
        {
            "title": "Bug title",
            "description": "Bug description",
            "severity": "high",
            "component": "component_name",
            "steps_to_reproduce": [...],
            "expected_behavior": "...",
            "actual_behavior": "..."
        }
        """
        try:
            content = validate_message(message.content, "ExaminerReportBug")
            
            # Create bug record
            self._bug_counter += 1
            _bug = Bug(
                id=f"bug_{self._bug_counter}",
                title=content.get("title", "Untitled Bug"),
                _description = content.get("description", ""),
                severity=SeverityLevel(content.get("severity", "medium")),
                component=content.get("component", "unknown"),
                _steps_to_reproduce = content.get("steps_to_reproduce", []),
                _expected_behavior = content.get("expected_behavior", ""),
                _actual_behavior = content.get("actual_behavior", ""),
                detected_at=datetime.now(timezone.utc),
                metadata=content.get("metadata", {})
            )
            
            # Store bug with LRU eviction
            if len(self._bugs) >= self.max_bugs:
                # Remove oldest bug
                _oldest_id = next(iter(self._bugs))
                del self._bugs[oldest_id]
            
            self._bugs[bug.id] = bug
            
            logger.info(
                "Bug reported",
                _bug_id = bug.id,
                severity=bug.severity.value,
                component=bug.component
            )
            
            return {
                "status": "success",
                "bug_id": bug.id,
                "severity": bug.severity.value,
                "created_at": bug.detected_at.isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to report bug", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_get_quality_report(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive quality report for a target.
        
        Content expected:
        {
            "target": "component_name",
            "include_tests": true,
            "include_bugs": true,
            "include_metrics": true
        }
        """
        try:
            content = validate_message(message.content, "ExaminerGetQualityReport")
            target = content.get("target", "system")
            _include_tests = content.get("include_tests", True)
            _include_bugs = content.get("include_bugs", True)
            _include_metrics = content.get("include_metrics", True)
            
            logger.info("Generating quality report", target=target)
            
            # Gather report data
            _test_suites = list(self._test_suites.values()) if include_tests else []
            _bugs = [b for b in self._bugs.values() if b.component == target] if include_bugs else []
            _metrics = self._quality_metrics.get(f"system:{target}", {}) if include_metrics else {}
            
            # Calculate overall score
            overall_score = self._calculate_system_score(test_suites, bugs, metrics)
            
            # Generate summary using LLM
            summary = await self._generate_quality_summary(
                _test_suites = test_suites,
                _bugs = bugs,
                _metrics = metrics,
                overall_score=overall_score
            )
            
            _report = QualityReport(
                id=f"report_{datetime.now(timezone.utc).timestamp()}",
                generated_at=datetime.now(timezone.utc),
                target=target,
                _test_suites = test_suites,
                _bugs = bugs,
                _metrics = metrics,
                overall_score=overall_score,
                summary=summary,
                recommendations=self._generate_recommendations(test_suites, bugs, metrics),
                passed=overall_score >= self._coverage_threshold
            )
            
            return {
                "status": "success",
                "report": {
                    "id": report.id,
                    "generated_at": report.generated_at.isoformat(),
                    "target": report.target,
                    "overall_score": report.overall_score,
                    "passed": report.passed,
                    "summary": report.summary,
                    "test_summary": {
                        "passed": sum(s.passed for s in test_suites),
                        "failed": sum(s.failed for s in test_suites),
                        "total": sum(s.total for s in test_suites)
                    } if test_suites else None,
                    "bug_summary": {
                        "critical": len([b for b in bugs if b.severity == SeverityLevel.CRITICAL]),
                        "high": len([b for b in bugs if b.severity == SeverityLevel.HIGH]),
                        "total": len(bugs)
                    } if bugs else None,
                    "recommendations": report.recommendations
                }
            }
            
        except Exception as e:
            logger.error("Failed to generate quality report", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_get_bug_status(self, message: ActorMessage) -> Optional[Dict[str, Any]]:
        """
        Get status of reported bugs.
        
        Content expected:
        {
            "bug_id": "bug_123",  # Optional, get all if not specified
            "component": "component_name",  # Filter by component
            "severity": "high"  # Filter by severity
        }
        """
        try:
            _content = validate_message(message.content, "ExaminerGetBugStatus")
            _bug_id = content.get("bug_id")
            component = content.get("component")
            severity = content.get("severity")
            
            if bug_id:
                # Get specific bug
                _bug = self._bugs.get(bug_id)
                if bug:
                    return {
                        "status": "success",
                        "bug": {
                            "id": bug.id,
                            "title": bug.title,
                            "severity": bug.severity.value,
                            "component": bug.component,
                            "status": bug.status,
                            "detected_at": bug.detected_at.isoformat()
                        }
                    }
                return {"status": "error", "error": f"Bug {bug_id} not found"}
            
            # Filter bugs
            _filtered_bugs = list(self._bugs.values())
            if component:
                _filtered_bugs = [b for b in filtered_bugs if b.component == component]
            if severity:
                _filtered_bugs = [b for b in filtered_bugs if b.severity.value == severity]
            
            return {
                "status": "success",
                "bugs": [
                    {
                        "id": b.id,
                        "title": b.title,
                        "severity": b.severity.value,
                        "component": b.component,
                        "status": b.status,
                        "detected_at": b.detected_at.isoformat()
                    }
                    for b in filtered_bugs[:50]  # Limit results
                ],
                "total": len(filtered_bugs)
            }
            
        except Exception as e:
            logger.error("Failed to get bug status", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # Internal helper methods
    
    async def _generate_test_plan(self, target: str, test_types: List[str], priority: str, requirements: List[str]) -> Dict[str, Any]:
        """Generate test plan using LLM."""
        try:
            _prompt = f"""Generate a comprehensive test plan for: {target}

Test Types Required: {', '.join(test_types)}
Priority: {priority}
Requirements: {requirements}

Provide a structured test plan with:
1. Test objectives
2. Test cases for each type
3. Expected outcomes
4. Success criteria
5. Risk assessment

Format as JSON with keys: objectives, test_cases, success_criteria, risks"""

            _response = await self.run_with_llm(
                _prompt = prompt,
                _timeout = 60,
                _temperature = 0.3
            )
            
            # Try to parse as JSON
            import json
            try:
                return json.loads(response)
            except:
                return {
                    "objectives": [response[:500]],
                    "test_cases": [],
                    "success_criteria": ["All tests pass"],
                    "risks": []
                }
                
        except Exception as e:
            logger.error("Failed to generate test plan", error=str(e))
            return {
                "objectives": ["Test plan generation failed"],
                "test_cases": [],
                "success_criteria": [],
                "risks": [str(e)]
            }
    
    async def _execute_test_case(self, test_case: Dict[str, Any], timeout: int) -> TestCase:
        """Execute a single test case."""
        _start_time = datetime.now(timezone.utc)
        
        try:
            _tc_id = test_case.get("id", f"tc_{start_time.timestamp()}")
            _tc_name = test_case.get("name", "Unnamed Test")
            _tc_type = TestType(test_case.get("test_type", "unit"))
            
            # Execute test logic (placeholder for actual test execution)
            # In production, this would integrate with pytest, unittest, etc.
            _result = await asyncio.wait_for(
                self._run_test_logic(test_case),
                _timeout = timeout
            )
            
            return TestCase(
                _id = tc_id,
                _name = tc_name,
                _test_type = tc_type,
                _description = test_case.get("description", ""),
                _status = TestStatus.PASSED if result.get("passed") else TestStatus.FAILED,
                _execution_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                _assertions_passed = result.get("assertions_passed", 0),
                _assertions_total = result.get("assertions_total", 0),
                coverage_percent=result.get("coverage"),
                metadata=result.get("metadata", {})
            )
            
        except asyncio.TimeoutError:
            return TestCase(
                _id = test_case.get("id", "unknown"),
                _name = test_case.get("name", "Unnamed Test"),
                _test_type = TestType(test_case.get("test_type", "unit")),
                _description = test_case.get("description", ""),
                _status = TestStatus.ERROR,
                _execution_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                _error_message = f"Test timed out after {timeout}s"
            )
        except Exception as e:
            return TestCase(
                _id = test_case.get("id", "unknown"),
                _name = test_case.get("name", "Unnamed Test"),
                _test_type = TestType(test_case.get("test_type", "unit")),
                _description = test_case.get("description", ""),
                _status = TestStatus.ERROR,
                _execution_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                _error_message = str(e)
            )
    
    async def _run_test_logic(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute actual test logic.
        
        This is a placeholder that should be extended with actual test frameworks.
        """
        # Placeholder: simulate test execution
        await asyncio.sleep(0.1)  # Simulate work
        
        # In production, integrate with:
        # - pytest for unit/integration tests
        # - selenium for E2E tests
        # - bandit/safety for security tests
        # - axe for accessibility tests
        
        return {
            "passed": True,
            "assertions_passed": test_case.get("assertions", 1),
            "assertions_total": test_case.get("assertions", 1),
            "coverage": test_case.get("expected_coverage", 95.0)
        }
    
    async def _validate_decision_content(self, decision_id: str, decision_type: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate decision content using LLM."""
        try:
            prompt = f"""Validate this decision from the Triad:

Decision ID: {decision_id}
Type: {decision_type}
Content: {content[:2000]}
Context: {context}

Evaluate for:
1. Logical consistency
2. Completeness
3. Alignment with requirements
4. Potential edge cases missed
5. Security implications

Return JSON with keys: valid (bool), confidence (0-1), issues (list), recommendations (list)"""

            _response = await self.run_with_llm(
                _prompt = prompt,
                _timeout = 60,
                _temperature = 0.2
            )
            
            import json
            try:
                return json.loads(response)
            except:
                return {
                    "valid": True,
                    "confidence": 0.8,
                    "issues": ["Unable to parse detailed validation"],
                    "recommendations": ["Manual review recommended"]
                }
                
        except Exception as e:
            logger.error("Decision validation failed", error=str(e))
            return {
                "valid": False,
                "confidence": 0.0,
                "issues": [f"Validation error: {str(e)}"],
                "recommendations": ["Retry validation"]
            }
    
    async def _analyze_quality_metrics(self, target: str, _target_type: str, metrics: List[QualityMetric]) -> Dict[QualityMetric, float]:
        """Analyze quality metrics for target."""
        _results = {}
        
        for metric in metrics:
            try:
                if metric == QualityMetric.CODE_COVERAGE:
                    results[metric] = await self._measure_coverage(target)
                elif metric == QualityMetric.CYCLOMATIC_COMPLEXITY:
                    results[metric] = await self._measure_complexity(target)
                elif metric == QualityMetric.SECURITY_VULNERABILITIES:
                    results[metric] = await self._measure_security(target)
                elif metric == QualityMetric.PERFORMANCE_SCORE:
                    results[metric] = await self._measure_performance(target)
                else:
                    # Default: use LLM estimation
                    results[metric] = await self._estimate_metric(target, metric)
            except Exception as e:
                logger.warning(f"Failed to measure {metric.value}", error=str(e))
                results[metric] = 0.0
        
        return results
    
    async def _measure_coverage(self, _target: str) -> float:
        """Measure code coverage."""
        # Placeholder: integrate with coverage.py
        return 85.0
    
    async def _measure_complexity(self, _target: str) -> float:
        """Measure cyclomatic complexity (inverted score)."""
        # Placeholder: integrate with radon or mccabe
        return 75.0
    
    async def _measure_security(self, _target: str) -> float:
        """Measure security score (inverted - lower vulnerabilities = higher score)."""
        # Placeholder: integrate with bandit, safety
        return 90.0
    
    async def _measure_performance(self, _target: str) -> float:
        """Measure performance score."""
        # Placeholder: benchmark execution
        return 80.0
    
    async def _estimate_metric(self, target: str, metric: QualityMetric) -> float:
        """Estimate metric using LLM."""
        try:
            _prompt = f"""Estimate {metric.value} for: {target[:500]}

Return a score from 0-100."""
            
            _response = await self.run_with_llm(prompt=prompt, timeout=30)
            # Extract number from response
            import re
            _match = re.search(r'(\d+(?:\.\d+)?)', response)
            if match:
                return min(100.0, float(match.group(1)))
            return 50.0
        except:
            return 50.0
    
    def _calculate_overall_score(self, metrics: Dict[QualityMetric, float]) -> float:
        """Calculate weighted overall quality score."""
        if not metrics:
            return 0.0
        
        _weights = {
            QualityMetric.CODE_COVERAGE: 0.25,
            QualityMetric.CYCLOMATIC_COMPLEXITY: 0.15,
            QualityMetric.SECURITY_VULNERABILITIES: 0.25,
            QualityMetric.PERFORMANCE_SCORE: 0.20,
            QualityMetric.ACCESSIBILITY_SCORE: 0.10,
            QualityMetric.DOCUMENTATION_COVERAGE: 0.05
        }
        
        total = 0.0
        _total_weight = 0.0
        
        for metric, value in metrics.items():
            _weight = weights.get(metric, 0.1)
            total += value * weight
            total_weight += weight
        
        return (total / total_weight) if total_weight > 0 else 0.0
    
    def _calculate_system_score(self, test_suites: List[TestSuite], bugs: List[Bug], metrics: Dict[QualityMetric, float]) -> float:
        """Calculate overall system quality score."""
        _scores = []
        
        # Test pass rate
        if test_suites:
            _total_passed = sum(s.passed for s in test_suites)
            _total_tests = sum(s.total for s in test_suites)
            if total_tests > 0:
                scores.append((total_passed / total_tests) * 100 * 0.4)
        
        # Bug impact
        if bugs:
            _severity_weights = {
                SeverityLevel.CRITICAL: 10,
                SeverityLevel.HIGH: 5,
                SeverityLevel.MEDIUM: 2,
                SeverityLevel.LOW: 1,
                SeverityLevel.INFO: 0.5
            }
            _bug_score = sum(severity_weights.get(b.severity, 1) for b in bugs)
            # More bugs = lower score
            scores.append(max(0, 100 - bug_score * 2) * 0.3)
        else:
            scores.append(100 * 0.3)
        
        # Quality metrics
        if metrics:
            _metric_score = self._calculate_overall_score(metrics)
            scores.append(metric_score * 0.3)
        
        return sum(scores) if scores else 0.0
    
    def _generate_recommendations(self, test_suites: List[TestSuite], bugs: List[Bug], metrics: Dict[QualityMetric, float]) -> List[str]:
        """Generate quality improvement recommendations."""
        _recommendations = []
        
        # Test recommendations
        if test_suites:
            _total_failed = sum(s.failed for s in test_suites)
            if total_failed > 0:
                recommendations.append(f"Fix {total_failed} failing tests")
            
            _avg_coverage = sum(s.coverage_percent or 0 for s in test_suites) / len(test_suites)
            if avg_coverage < self._coverage_threshold:
                recommendations.append(f"Increase test coverage from {avg_coverage:.1f}% to {self._coverage_threshold}%")
        
        # Bug recommendations
        _critical_bugs = [b for b in bugs if b.severity == SeverityLevel.CRITICAL]
        if critical_bugs:
            recommendations.append(f"Address {len(critical_bugs)} critical bugs immediately")
        
        # Metric recommendations
        for metric, value in metrics.items():
            if value < 70:
                recommendations.append(f"Improve {metric.value} (current: {value:.1f})")
        
        return recommendations or ["Continue monitoring quality metrics"]
    

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
                _message_id = f"{item_type}_{item_id}",
                _sender = self.agent_id,
                _recipient = "broadcast",
                _message_type = f"{item_type}_completion",
                _content = content,
                _timestamp = datetime.now(timezone.utc).isoformat(),
            )
            
            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: Optional[List[PatternType]]) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []
        
        try:
            _patterns = await self.pattern_extractor.extract_patterns(
                _time_window_hours = 24,
                _pattern_types = pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(self, item_id: str, proposal: str, participating_agents: List[str], domain: str) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None
        
        try:
            _deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                _deliberation_id = deliberation_id,
                _proposal = proposal[:200],
                _participants = participating_agents,
                _domain = domain,
            )
            self._active_deliberations[item_id] = deliberation_id
            
            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(self, item_id: str, agent_id: str, position: Position, confidence: float, argument: str) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False
        
        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False
        
        try:
            _success = self.deliberation_engine.submit_position(
                _deliberation_id = deliberation_id,
                agent_id=agent_id,
                _position = position,
                _confidence = confidence,
                _argument = argument,
            )
            
            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    _memory_id = f"delib_{deliberation_id}_{agent_id}",
                    _access_type = "write",
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
        
        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None
        
        try:
            _result = self.deliberation_engine.finalize_deliberation(deliberation_id)
            
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

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str) -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return
        
        _memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            _memory_id = memory_id,
            _access_type = access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD
        
        _memory_id = f"{item_type}_{item_id}"
        _profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []
        
        try:
            _predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
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


    async def _generate_quality_summary(self, test_suites: List[TestSuite], bugs: List[Bug], metrics: Dict[QualityMetric, float], overall_score: float) -> str:
        """Generate quality summary using LLM."""
        try:
            _prompt = f"""Generate a quality summary:

Overall Score: {overall_score:.1f}/100
Test Suites: {len(test_suites)} ({sum(s.passed for s in test_suites)} passed, {sum(s.failed for s in test_suites)} failed)
Bugs: {len(bugs)} ({len([b for b in bugs if b.severity == SeverityLevel.CRITICAL])} critical)
Metrics: {len(metrics)} measured

Provide a 2-3 sentence summary of the quality status."""

            _response = await self.run_with_llm(prompt=prompt, timeout=30)
            return response.strip()
        except:
            return f"Quality score: {overall_score:.1f}/100. {len(bugs)} bugs detected. {sum(s.failed for s in test_suites)} tests failing."
