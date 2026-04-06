"""
Catalyst Agent - Change Management Specialist

Tier 5 Coordination Agent responsible for:
- Change detection and impact analysis
- Transition planning and execution
- Version management and migration
- Rollback coordination
- Change communication and stakeholder notification

Author: Heretek Swarm Collective
Date: 2026-04-06
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.actors.validation import validate_message, CoordinationRequest

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine, Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

logger = structlog.get_logger(__name__)


class ChangeStatus(Enum):
    """Status of a change request."""
    PROPOSED = "proposed"
    ANALYZING = "analyzing"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ChangeType(Enum):
    """Type of change."""
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    MIGRATION = "migration"
    UPGRADE = "upgrade"
    PATCH = "patch"
    HOTFIX = "hotfix"
    ROLLBACK = "rollback"


class ImpactLevel(Enum):
    """Change impact level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChangeRequest:
    """A change request under management."""
    change_id: str
    title: str
    description: str
    change_type: ChangeType
    status: ChangeStatus = ChangeStatus.PROPOSED
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    requested_by: str = ""
    affected_components: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    rollback_plan: str = ""
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    approval_status: Dict[str, bool] = field(default_factory=dict)
    required_approvals: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "change_id": self.change_id,
            "title": self.title,
            "description": self.description,
            "change_type": self.change_type.value,
            "status": self.status.value,
            "impact_level": self.impact_level.value,
            "requested_by": self.requested_by,
            "affected_components": self.affected_components,
            "dependencies": self.dependencies,
            "rollback_plan": self.rollback_plan,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
            "approval_status": self.approval_status,
            "required_approvals": self.required_approvals,
            "approval_count": sum(1 for v in self.approval_status.values() if v),
        }


@dataclass
class ChangeNotification:
    """A change notification to stakeholders."""
    notification_id: str
    change_id: str
    recipients: List[str]
    message: str
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_by: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "notification_id": self.notification_id,
            "change_id": self.change_id,
            "recipients": self.recipients,
            "message": self.message,
            "sent_at": self.sent_at.isoformat(),
            "acknowledged_by": list(self.acknowledged_by),
            "acknowledgment_count": len(self.acknowledged_by),
        }


class CatalystAgent(AgentActor):
    """
    Change Management Specialist.

    Responsibilities:
    - Detect and analyze proposed changes
    - Plan and schedule transitions
    - Manage version migrations
    - Coordinate rollbacks when needed
    - Notify stakeholders of changes

    Message Handlers:
    - propose_change: Propose a new change request
    - analyze_change: Analyze change impact
    - approve_change: Approve a change request
    - schedule_change: Schedule approved change
    - execute_change: Execute scheduled change
    - request_rollback: Initiate rollback
    - execute_rollback: Execute rollback procedure
    - get_change_status: Get status of a change
    - get_change_history: Get change history
    - notify_stakeholders: Send change notifications
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        # Session 44: Integration components
        pattern_extractor: Optional[PatternExtractor] = None,
        deliberation_engine: Optional[SwarmDeliberationEngine] = None,
        access_analyzer: Optional[AccessPatternAnalyzer] = None,
        zero_trust_validator: Optional[ZeroTrustValidator] = None,
    ):
        super().__init__(
            agent_id=agent_id or f"catalyst_{uuid.uuid4().hex[:8]}",
            config=config or {},
        )

        # Change management
        self._changes: Dict[str, ChangeRequest] = {}
        self._max_changes: int = self._config.get("max_changes", 500)

        # Notifications
        self._notifications: Dict[str, ChangeNotification] = {}
        self._max_notifications: int = self._config.get("max_notifications", 1000)

        # Stakeholders
        self._stakeholders: Set[str] = set()

        # Change history
        self._history: List[Dict[str, Any]] = []
        self._max_history: int = self._config.get("max_history", 1000)

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
        
        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}  # change_id -> deliberation_id
        self._pattern_emitted_changes: Set[str] = set()

        logger.info(
            "catalyst_initialized",
            agent_id=self.agent_id,
            max_changes=self._max_changes,
            collective_learning_enabled=self.pattern_extractor is not None,
            consensus_enabled=self.deliberation_engine is not None,
            memory_optimization_enabled=self.access_analyzer is not None,
        )

    async def _validate_message(self, message: ActorMessage) -> Dict[str, Any]:
        """Validate incoming message content."""
        try:
            validated = validate_message(message.message_type, message.content)
            if hasattr(validated, 'dict'):
                return validated.dict()
            return validated
        except Exception:
            return message.content

    async def _handle_propose_change(self, message: ActorMessage) -> None:
        """
        Propose a new change request.

        Content:
        - change_id: Optional[str]
        - title: str
        - description: str
        - change_type: str (configuration|deployment|migration|upgrade|patch|hotfix|rollback)
        - affected_components: List[str]
        - rollback_plan: str
        - impact_level: Optional[str] (low|medium|high|critical)
        - required_approvals: Optional[int]
        - metadata: Optional[Dict]
        """
        try:
            content = await self._validate_message(message)

            if len(self._changes) >= self._max_changes:
                await self._send_error(
                    message.sender_id,
                    f"Change limit reached ({self._max_changes})",
                    message.message_type,
                )
                return

            change_id = content.get("change_id") or f"change_{uuid.uuid4().hex[:12]}"

            if change_id in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} already exists",
                    message.message_type,
                )
                return

            change_type = ChangeType(content.get("change_type", "configuration"))
            impact_level = ImpactLevel(content.get("impact_level", "medium"))

            change = ChangeRequest(
                change_id=change_id,
                title=content.get("title", "Untitled Change"),
                description=content.get("description", ""),
                change_type=change_type,
                impact_level=impact_level,
                requested_by=message.sender_id,
                affected_components=content.get("affected_components", []),
                rollback_plan=content.get("rollback_plan", ""),
                required_approvals=content.get("required_approvals", 1),
                metadata=content.get("metadata", {}),
            )

            self._changes[change_id] = change

            logger.info(
                "change_proposed",
                change_id=change_id,
                title=change.title,
                type=change_type.value,
                impact=impact_level.value,
            )

            # Notify stakeholders
            await self._notify_stakeholders(change_id, f"Change proposed: {change.title}")

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="change_proposed",
                    content={"change": change.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("propose_change_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to propose change: {str(e)}",
                message.message_type,
            )

    async def _handle_analyze_change(self, message: ActorMessage) -> None:
        """
        Analyze change impact.

        Content:
        - change_id: str
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            change = self._changes[change_id]
            change.status = ChangeStatus.ANALYZING

            # Perform impact analysis
            analysis = {
                "change_id": change_id,
                "impact_assessment": {
                    "affected_components": change.affected_components,
                    "component_count": len(change.affected_components),
                    "impact_level": change.impact_level.value,
                    "risk_score": self._calculate_risk_score(change),
                },
                "dependencies": {
                    "internal": change.dependencies,
                    "external": [],  # Can be extended
                },
                "recommendations": self._generate_recommendations(change),
            }

            change.status = ChangeStatus.PROPOSED  # Back to proposed after analysis

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="change_analyzed",
                    content={"analysis": analysis},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("analyze_change_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to analyze change: {str(e)}",
                message.message_type,
            )

    async def _handle_approve_change(self, message: ActorMessage) -> None:
        """
        Approve a change request.

        Content:
        - change_id: str
        - approver_id: str
        - approved: bool
        - comments: Optional[str]
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")
            approver_id = content.get("approver_id", message.sender_id)
            approved = content.get("approved", False)

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            change = self._changes[change_id]
            change.approval_status[approver_id] = approved

            approval_count = sum(1 for v in change.approval_status.values() if v)
            needs_more_approvals = approval_count < change.required_approvals

            if approved and not needs_more_approvals:
                change.status = ChangeStatus.APPROVED
                logger.info(
                    "change_approved",
                    change_id=change_id,
                    approver=approver_id,
                    approval_count=approval_count,
                )
            elif approved:
                logger.info(
                    "change_partial_approval",
                    change_id=change_id,
                    approver=approver_id,
                    approval_count=approval_count,
                    needed=change.required_approvals,
                )
            else:
                logger.info(
                    "change_rejected",
                    change_id=change_id,
                    approver=approver_id,
                )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="change_approval_recorded",
                    content={
                        "change_id": change_id,
                        "approved": approved,
                        "approval_count": approval_count,
                        "required": change.required_approvals,
                        "status": change.status.value,
                    },
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("approve_change_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to record approval: {str(e)}",
                message.message_type,
            )

    async def _handle_schedule_change(self, message: ActorMessage) -> None:
        """
        Schedule an approved change.

        Content:
        - change_id: str
        - scheduled_at: str (ISO8601)
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")
            scheduled_at = content.get("scheduled_at")

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            change = self._changes[change_id]

            if change.status != ChangeStatus.APPROVED:
                await self._send_error(
                    message.sender_id,
                    f"Change must be approved before scheduling (current: {change.status.value})",
                    message.message_type,
                )
                return

            change.scheduled_at = datetime.fromisoformat(scheduled_at) if scheduled_at else datetime.now(timezone.utc)
            change.status = ChangeStatus.SCHEDULED

            logger.info(
                "change_scheduled",
                change_id=change_id,
                scheduled_at=change.scheduled_at.isoformat(),
            )

            await self._notify_stakeholders(change_id, f"Change scheduled: {change.title}")

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="change_scheduled",
                    content={"change": change.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("schedule_change_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to schedule change: {str(e)}",
                message.message_type,
            )

    async def _handle_execute_change(self, message: ActorMessage) -> None:
        """
        Execute a scheduled change.

        Content:
        - change_id: str
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            change = self._changes[change_id]
            change.status = ChangeStatus.IN_PROGRESS
            change.started_at = datetime.now(timezone.utc)

            logger.info(
                "change_started",
                change_id=change_id,
                title=change.title,
            )

            # Simulate execution (would be extended for real implementation)
            # In production, this would coordinate with actual deployment systems

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="change_started",
                    content={"change": change.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("execute_change_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to execute change: {str(e)}",
                message.message_type,
            )

    async def _handle_request_rollback(self, message: ActorMessage) -> None:
        """
        Request a rollback of a change.

        Content:
        - change_id: str
        - reason: str
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")
            reason = content.get("reason", "Unspecified")

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            change = self._changes[change_id]

            if change.status not in (ChangeStatus.COMPLETED, ChangeStatus.IN_PROGRESS, ChangeStatus.FAILED):
                await self._send_error(
                    message.sender_id,
                    f"Cannot rollback change in {change.status.value} state",
                    message.message_type,
                )
                return

            # Create rollback change request
            rollback_id = f"rollback_{change_id}"
            rollback = ChangeRequest(
                change_id=rollback_id,
                title=f"Rollback: {change.title}",
                description=f"Rolling back {change_id} due to: {reason}",
                change_type=ChangeType.ROLLBACK,
                impact_level=change.impact_level,
                requested_by=message.sender_id,
                affected_components=change.affected_components,
                rollback_plan="",  # Rollback of a rollback
                metadata={"original_change_id": change_id, "rollback_reason": reason},
            )

            self._changes[rollback_id] = rollback

            logger.info(
                "rollback_requested",
                change_id=change_id,
                rollback_id=rollback_id,
                reason=reason,
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="rollback_requested",
                    content={"rollback": rollback.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("request_rollback_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to request rollback: {str(e)}",
                message.message_type,
            )

    async def _handle_execute_rollback(self, message: ActorMessage) -> None:
        """
        Execute a rollback.

        Content:
        - change_id: str (original change to rollback)
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            change = self._changes[change_id]
            change.status = ChangeStatus.ROLLED_BACK
            change.completed_at = datetime.now(timezone.utc)

            # Record in history
            self._record_change_event(change_id, "rolled_back")

            logger.info(
                "rollback_executed",
                change_id=change_id,
            )

            await self._notify_stakeholders(change_id, f"Change rolled back: {change.title}")

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="rollback_executed",
                    content={"change": change.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("execute_rollback_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to execute rollback: {str(e)}",
                message.message_type,
            )

    async def _handle_get_change_status(self, message: ActorMessage) -> None:
        """
        Get status of a change.

        Content:
        - change_id: str
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            change = self._changes[change_id]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="change_status",
                    content={"change": change.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_change_status_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get change status: {str(e)}",
                message.message_type,
            )

    async def _handle_get_change_history(self, message: ActorMessage) -> None:
        """
        Get change history.

        Content:
        - limit: Optional[int]
        - change_type: Optional[str]
        - status: Optional[str]
        """
        try:
            content = await self._validate_message(message)
            limit = min(content.get("limit", 50), 100)
            change_type = content.get("change_type")
            status = content.get("status")

            history = self._history.copy()

            # Filter by change_type
            if change_type:
                history = [h for h in history if h.get("change_type") == change_type]

            # Filter by status
            if status:
                history = [h for h in history if h.get("status") == status]

            # Limit results
            history = history[-limit:]

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="change_history",
                    content={"history": history, "count": len(history)},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("get_change_history_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to get change history: {str(e)}",
                message.message_type,
            )

    async def _handle_notify_stakeholders(self, message: ActorMessage) -> None:
        """
        Send notifications to stakeholders.

        Content:
        - change_id: str
        - message: str
        - recipients: Optional[List[str]]
        """
        try:
            content = await self._validate_message(message)
            change_id = content.get("change_id")
            notification_message = content.get("message", "")
            recipients = content.get("recipients", list(self._stakeholders))

            if not change_id or change_id not in self._changes:
                await self._send_error(
                    message.sender_id,
                    f"Change {change_id} not found",
                    message.message_type,
                )
                return

            notification_id = f"notif_{uuid.uuid4().hex[:12]}"
            notification = ChangeNotification(
                notification_id=notification_id,
                change_id=change_id,
                recipients=recipients,
                message=notification_message,
            )

            self._notifications[notification_id] = notification

            # Trim notifications if needed
            if len(self._notifications) > self._max_notifications:
                oldest = sorted(self._notifications.keys())[0]
                del self._notifications[oldest]

            logger.info(
                "stakeholders_notified",
                notification_id=notification_id,
                change_id=change_id,
                recipient_count=len(recipients),
            )

            await self.send(
                message.sender_id,
                ActorMessage(
                    message_type="notification_sent",
                    content={"notification": notification.to_dict()},
                    sender_id=self.agent_id,
                ),
            )

        except Exception as e:
            logger.error("notify_stakeholders_failed", error=str(e))
            await self._send_error(
                message.sender_id,
                f"Failed to notify stakeholders: {str(e)}",
                message.message_type,
            )

    async def _notify_stakeholders(self, change_id: str, message: str) -> None:
        """Internal helper to notify all stakeholders."""
        if not self._stakeholders:
            return

        notification_id = f"notif_{uuid.uuid4().hex[:12]}"
        notification = ChangeNotification(
            notification_id=notification_id,
            change_id=change_id,
            recipients=list(self._stakeholders),
            message=message,
        )

        self._notifications[notification_id] = notification

        # Trim if needed
        if len(self._notifications) > self._max_notifications:
            oldest = sorted(self._notifications.keys())[0]
            del self._notifications[oldest]

    def _calculate_risk_score(self, change: ChangeRequest) -> float:
        """Calculate risk score for a change (0.0-1.0)."""
        base_scores = {
            ImpactLevel.LOW: 0.1,
            ImpactLevel.MEDIUM: 0.3,
            ImpactLevel.HIGH: 0.6,
            ImpactLevel.CRITICAL: 0.9,
        }

        score = base_scores.get(change.impact_level, 0.3)

        # Increase score based on affected components
        component_factor = min(len(change.affected_components) * 0.05, 0.2)
        score += component_factor

        # Increase score for complex change types
        complex_types = {ChangeType.DEPLOYMENT, ChangeType.MIGRATION, ChangeType.UPGRADE}
        if change.change_type in complex_types:
            score += 0.1

        return min(score, 1.0)

    def _generate_recommendations(self, change: ChangeRequest) -> List[str]:
        """Generate recommendations for a change."""
        recommendations = []

        if change.impact_level == ImpactLevel.CRITICAL:
            recommendations.append("Consider breaking this change into smaller increments")
            recommendations.append("Ensure rollback plan is thoroughly tested")

        if len(change.affected_components) > 5:
            recommendations.append("High component count - consider phased rollout")

        if change.change_type == ChangeType.MIGRATION:
            recommendations.append("Create backup before migration")
            recommendations.append("Test migration on staging environment first")

        if not change.rollback_plan:
            recommendations.append("Document detailed rollback procedure")

        if change.required_approvals < 2 and change.impact_level in (ImpactLevel.HIGH, ImpactLevel.CRITICAL):
            recommendations.append("Consider requiring additional approvals for high-impact changes")

        return recommendations

    def _record_change_event(self, change_id: str, event_type: str) -> None:
        """Record a change event in history."""
        change = self._changes.get(change_id)
        if not change:
            return

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "change_id": change_id,
            "change_type": change.change_type.value,
            "event_type": event_type,
            "status": change.status.value,
            "title": change.title,
        }

        self._history.append(event)

        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_change_pattern(self, change: ChangeRequest, outcome: str) -> None:
        """
        Emit pattern for collective learning when change is completed.
        
        Args:
            change: The completed change
            outcome: Completion outcome (success, failure, rolled_back)
        """
        if not self.pattern_extractor:
            return
        
        if change.change_id in self._pattern_emitted_changes:
            return
        
        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"change_{change.change_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type="change_completion",
                content={
                    "change_type": change.change_type.value,
                    "impact_level": change.impact_level.value,
                    "outcome": outcome,
                    "affected_components": change.affected_components,
                    "approval_count": sum(1 for v in change.approval_status.values() if v),
                },
                timestamp=change.completed_at.isoformat() if change.completed_at else datetime.now(timezone.utc).isoformat(),
            )
            
            self._pattern_emitted_changes.add(change.change_id)
            logger.info("change_pattern_emitted", change_id=change.change_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_change_pattern", change_id=change.change_id, error=str(e))

    async def _consume_change_patterns(self) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning for change guidance."""
        if not self.pattern_extractor:
            return []
        
        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=[PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation_for_change(
        self,
        change: ChangeRequest,
        participating_agents: List[str],
    ) -> Optional[str]:
        """Initiate swarm deliberation for high-impact change approval."""
        if not self.deliberation_engine:
            return None
        
        try:
            deliberation_id = f"delib_{change.change_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=f"Approve change: {change.title[:100]}",
                participants=participating_agents,
                domain="change_management",
            )
            self._active_deliberations[change.change_id] = deliberation_id
            
            logger.info("deliberation_initiated", deliberation_id=deliberation_id, change_id=change.change_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", change_id=change.change_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        change: ChangeRequest,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in change deliberation."""
        if not self.deliberation_engine:
            return False
        
        deliberation_id = self._active_deliberations.get(change.change_id)
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
            logger.error("failed_to_submit_deliberation_position", deliberation_id=deliberation_id, error=str(e))
            return False

    async def _finalize_deliberation(self, change: ChangeRequest) -> Optional[Any]:
        """Finalize deliberation and apply result to change approval."""
        if not self.deliberation_engine:
            return None
        
        deliberation_id = self._active_deliberations.get(change.change_id)
        if not deliberation_id:
            return None
        
        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)
            
            if result:
                change.approval_status[f"deliberation_{deliberation_id}"] = (
                    result.consensus_score >= 0.75
                )
                change.metadata["deliberation_result"] = {
                    "deliberation_id": deliberation_id,
                    "final_position": result.final_position.value,
                    "consensus_score": result.consensus_score,
                }
                
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[change.change_id]
                
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)
            
            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", deliberation_id=deliberation_id, error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_change_memory_access(self, change_id: str, access_type: str = "read") -> None:
        """Track memory access patterns for change data."""
        if not self.access_analyzer:
            return
        
        memory_id = f"change_{change_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_change_memory_tier(self, change_id: str) -> AccessTier:
        """Get memory tier classification for a change."""
        if not self.access_analyzer:
            return AccessTier.COLD
        
        memory_id = f"change_{change_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant_changes(self, agent_id: str) -> List[str]:
        """Prefetch changes an agent is likely to need."""
        if not self.access_analyzer:
            return []
        
        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace("change_", "")
                for mem in predicted_memories
                if mem.startswith("change_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch_changes", agent_id=agent_id, error=str(e))
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

    async def _send_error(
        self,
        recipient: str,
        error_message: str,
        original_type: str,
    ) -> None:
        """Send error response."""
        await self.send(
            recipient,
            ActorMessage(
                message_type="error",
                content={"error": error_message, "original_type": original_type},
                sender_id=self.agent_id,
            ),
        )

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "change_management",
            "impact_analysis",
            "transition_planning",
            "version_management",
            "rollback_coordination",
            "stakeholder_notification",
        ]
