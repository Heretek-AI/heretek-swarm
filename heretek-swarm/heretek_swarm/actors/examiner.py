"""
Examiner Agent - Backward Compatibility Module.

This module exists for backward compatibility. All exports have been moved to
the examiner/ directory. Import from the new location:

    from heretek_swarm.actors.examiner import ExaminerAgent, TestType, ...

Or import directly from specific modules:

    from heretek_swarm.actors.examiner.agent import ExaminerAgent
    from heretek_swarm.actors.examiner.types import (
        TestType,
        TestStatus,
        QualityMetric,
        SeverityLevel,
        TestCase,
        TestSuite,
        Bug,
        QualityReport,
    )
    from heretek_swarm.actors.examiner.testing import (
        ExaminingTestingMixin,
        ExaminingValidationMixin,
    )

This module will be removed in a future version.
"""

# Re-export everything from the new module structure for backward compatibility
from heretek_swarm.actors.examiner import (
    Bug,
    ExaminingTestingMixin,
    ExaminingValidationMixin,
    ExaminerAgent,
    QualityMetric,
    QualityReport,
    SeverityLevel,
    TestCase,
    TestStatus,
    TestSuite,
    TestType,
)

__all__ = [
    # Agent
    "ExaminerAgent",
    # Types (enums and data classes)
    "Bug",
    "QualityMetric",
    "QualityReport",
    "SeverityLevel",
    "TestCase",
    "TestStatus",
    "TestSuite",
    "TestType",
    # Mixins
    "ExaminingTestingMixin",
    "ExaminingValidationMixin",
]
