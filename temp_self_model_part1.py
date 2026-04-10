"""Self-Model Module - Agent Self-Awareness Through Beliefs and Goals"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import math

import structlog

logger = structlog.get_logger("SelfModel")


class GoalStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"
    PAUSED = "paused"


class BeliefType(Enum):
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    SELF = "self"
    SOCIAL = "social"
    META = "meta"


@dataclass
class Belief:
    belief_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: str = ""
    confidence: float = 0.5
    belief_type: BeliefType = BeliefType.FACTUAL
    source: str = "unknown"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    supporting_evidence: List[str] = field(default_factory=list)
    conflicting_beliefs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "state": self.state,
            "confidence": self.confidence,
            "belief_type": self.belief_type.value,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "supporting_evidence": self.support_type", "factual"))
        except ValueError:
            belief_type = BeliefType.FACTUAL
        return cls(
            belief_id=data.get("belief_id", str(uuid.uuid4())),
            state=data.get("state", ""),
            confidence=data.get("confidence", 0.5),
            belief_type=belief_type,
            source=data.get("source", "unknown"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            supporting_evidence=data.get("supporting_evidence", []),
            conflicting_beliefs=data.get("conflicting_beliefs", []),
        )


@dataclass
class Goal:
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: float = 0.5
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    deadline: Optional[str] = None
    completed_at: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)
    parent_goal_id: Optional[str] = None
    progress: float = 0.0
    associated_beliefs: List[str] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "completed_at": self.completed_at,
            "sub_goals": self.sub_goals,
            "parent_goal_id": self.parent_goal_id,
            " "Goal":
        try:
            status = GoalStatus(data.get("status", "active"))
        except ValueError:
            status = GoalStatus.ACTIVE
        return cls(
            goal_id=data.get("goal_id", str(uuid.uuid4())),
            description=data.get("description", ""),
            priority=data.get("priority", 0.5),
            status=status,
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            deadline=data.get("deadline"),
            completed_at=data.get("completed_at"),
            sub_goals=data.get("sub_goals", []),
            parent_goal_id=data.get("parent_goal_id"),
            progress=data.get("progress", 0.0),
            associated_beliefs=data.get("associated_beliefs", []),
            blocked_by=data.get("blocked_by", []),
            depends_on=data.get("depends_on", []),
        )


@dataclass
class Capability:
    capability_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    level: float = 0.5
    experience_count: int = 0
    success_rate: float = 0.5
    last_used: Optional[str] = None
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "level": self.level,
            "experience_count": self.experience_count,
            "success_rate": self.success_rate,
            "last_used": self.last_used,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Capability":
        return cls(
            capability_id=data.get("capability_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            level=data.get("level", 0.5),
            experience_count=data.get("experience_count", 0),
            success_rate=data.get("success_rate", 0.5),
            last_used=data.get("last_used"),
            confidence=data.get("confidence", 0.5),
        )


@dataclass
class Limitation:
    limitation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    severity: float = 0.5
    aware_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    workaround: Optional[str] = None
    mitigatable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "limitation_id": self.limitation_id,
            "description": self.description,
            "severity": self.severity,
            "aware_at": self.aware_at,
            "workaround": self.workaround,
("description", ""),
            severity=data.get("severity", 0.5),
            aware_at=data.get("aware_at", datetime.now(timezone.utc).isoformat()),
            workaround=data.get("workaround"),
            mitigatable=data.get("mitigatable", False),
        )


@dataclass
class Preference:
    preference_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = "general"
    preference_key: str = ""
    value: Any = None
    strength: float = 0.5
    learned_from: str = "unknown"
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "preference_id": self.preference_id,
            "category": self.category,
            "preference_key, Any]) -> "Preference":
        return cls(
            preference_id=data.get("preference_id", str(uuid.uuid4())),
            category=data.get("category", "general"),
            preference_key=data.get("preference_key", ""),
            value=data.get("value"),
            strength=data.get("strength", 0.5),
            learned_from=data.get("learned_from", "unknown"),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class SelfModelSnapshot:
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    belief_count: int = 0
    active_goal_count: int = 0
    goal_clarity: float = 0.0
    self_coherence: float = 0.0
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "belief_count": self.belief_count[str, Any]) -> "SelfModelSnapshot":
        return cls(
            snapshot_id=data.get("snapshot_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            belief_count=data.get("belief_count", 0),
            active_goal_count=data.get("active_goal_count", 0),
            goal_clarity=data.get("goal_clarity", 0.0),
            self_coherence=data.get("self_coherence", 0.0),
            summary=data.get("summary", ""),
        )


@dataclass
class SelfModelMetrics:
    self_coherence: float = 0.0
    goal_clarity: float = 0.0
    self_accuracy: float = 0.0
    belief_confidence_avg: float = 0.0
    goal_progress_rate: float = 0.0
    capability_reliability: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "self_coherence": self.self_coherence,
            "goal_clarity": self.goal_clarity,
            "self_accuracy": self.self_accuracy,
            "belief_confidence_avg": self.belief_confidence_avg,
            "goal_progress_rate": self.goal_progress_rate,
            "capability_reliability": self.capability_reliability,
        }
