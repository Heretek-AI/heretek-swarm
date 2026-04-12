"""
Arbiter Agent - Conflict Resolution & Dispute Mediation.

The Arbiter provides:
- Inter-agent conflict detection and resolution
- Dispute mediation and arbitration
- Consensus facilitation
- Resource contention management
- Priority-based task arbitration
- Relationship health monitoring

The Arbiter is the "peacekeeper" of the Collective, ensuring harmonious
multi-agent coordination and resolving conflicts before they escalate.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import ValidationError

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.validation import validate_message

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import (
    DeliberationResult,
    Position,
    SwarmDeliberationEngine,
)

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

logger = structlog.get_logger("ArbiterAgent")


class ConflictType(StrEnum):
    """Types of inter-agent conflicts."""
    RESOURCE_CONTENTION = "resource_contention"
    TASK_OVERLAP = "task_overlap"
    PRIORITY_DISPUTE = "priority_dispute"
    COMMUNICATION_BREAKDOWN = "communication_breakdown"
    AUTHORITY_CONFLICT = "authority_conflict"
    DATA_INCONSISTENCY = "data_inconsistency"
    GOAL_MISALIGNMENT = "goal_misalignment"
    CAPABILITY_OVERLAP = "capability_overlap"
    MESSAGE_FLOOD = "message_flood"
    DEADLOCK = "deadlock"


class ConflictSeverity(StrEnum):
    """Conflict severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionStrategy(StrEnum):
    """Conflict resolution strategies."""
    NEGOTIATION = "negotiation"
    MEDIATION = "mediation"
    ARBITRATION = "arbitration"
    PRIORITY_BASED = "priority_based"
    ROUND_ROBIN = "round_robin"
    RESOURCE_POOLING = "resource_pooling"
    TASK_REASSIGNMENT = "task_reassignment"
    ESCALATION = "escalation"
    COMPROMISE = "compromise"
    CONSENSUS_VOTE = "consensus_vote"


class ResolutionStatus(StrEnum):
    """Resolution process status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class Conflict:
    """Record of an inter-agent conflict."""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    status: ResolutionStatus
    timestamp: datetime
    parties: list[str]  # Agent IDs involved
    description: str
    context: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    proposed_resolutions: list[dict[str, Any]] = field(default_factory=list)
    selected_resolution: dict[str, Any] | None = None
    resolved_at: datetime | None = None
    resolution_notes: str = ""


@dataclass
class Relationship:
    """Inter-agent relationship health record."""
    agent_a: str
    agent_b: str
    health_score: float  # 0.0 - 1.0
    interaction_count: int
    conflict_count: int
    cooperation_count: int
    last_interaction: datetime
    trust_level: float  # 0.0 - 1.0
    tags: list[str] = field(default_factory=list)


@dataclass
class ArbitrationReport:
    """Comprehensive arbitration report."""
    report_id: str
    timestamp: datetime
    active_conflicts: int
    resolved_conflicts: int
    failed_resolutions: int
    conflicts_by_type: dict[str, int]
    conflicts_by_severity: dict[str, int]
    relationship_health: dict[str, float]
    recommendations: list[str]


class ArbiterAgent(AgentActor):
    """
    Arbiter Agent - Conflict Resolution Specialist for the Heretek Swarm Collective.

    The Arbiter mediates disputes, resolves resource contentions, and maintains
    healthy inter-agent relationships across the Collective.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        name: str = "Arbiter",
        description: str = "Conflict Resolution & Dispute Mediation",
        config: dict[str, Any] | None = None,
        db_pool: Any | None = None,
        redis_client: Any | None = None,
        # Session 44: Integration components
        pattern_extractor: PatternExtractor | None = None,
        deliberation_engine: SwarmDeliberationEngine | None = None,
        access_analyzer: AccessPatternAnalyzer | None = None,
        zero_trust_validator: ZeroTrustValidator | None = None,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            config=config,
            db_pool=db_pool,
            redis_client=redis_client,
        )

        # Configuration
        self._auto_resolution = config.get("auto_resolution", True) if config else True
        self._escalation_threshold = config.get("escalation_threshold", ConflictSeverity.HIGH.value) if config else ConflictSeverity.HIGH.value
        self._max_conflicts = config.get("max_conflicts", 1000) if config else 1000
        self._relationship_decay = config.get("relationship_decay", 0.01) if config else 0.01

        # State
        self._conflicts: dict[str, Conflict] = {}
        self._conflict_history: list[str] = []  # LRU keys
        self._relationships: dict[tuple[str, str], Relationship] = {}
        self._pending_arbitrations: dict[str, list[str]] = {}  # conflict_id -> waiting agents

        # Statistics
        self._stats = {
            "total_conflicts": 0,
            "conflicts_by_type": defaultdict(int),
            "conflicts_by_severity": defaultdict(int),
            "resolutions_successful": 0,
            "resolutions_failed": 0,
            "resolutions_escalated": 0,
            "average_resolution_time": 0.0,
        }

        # Session 44: Collective Learning Integration
        # PatternExtractor for tracking conflict resolution patterns
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)

        # Session 44: Consensus Integration
        # SwarmDeliberationEngine for multi-party dispute resolution
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        # AccessPatternAnalyzer for tracking conflict resolution memory access
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: dict[str, str] = {}  # conflict_id -> deliberation_id
        self._pattern_emitted_conflicts: set[str] = set()  # Track which conflicts emitted patterns

        # Resolution strategies registry
        self._resolution_strategies = {
            ResolutionStrategy.NEGOTIATION: self._resolve_negotiation,
            ResolutionStrategy.MEDIATION: self._resolve_mediation,
            ResolutionStrategy.ARBITRATION: self._resolve_arbitration,
            ResolutionStrategy.PRIORITY_BASED: self._resolve_priority_based,
            ResolutionStrategy.ROUND_ROBIN: self._resolve_round_robin,
            ResolutionStrategy.RESOURCE_POOLING: self._resolve_resource_pooling,
            ResolutionStrategy.TASK_REASSIGNMENT: self._resolve_task_reassignment,
            ResolutionStrategy.ESCALATION: self._resolve_escalation,
            ResolutionStrategy.COMPROMISE: self._resolve_compromise,
            ResolutionStrategy.CONSENSUS_VOTE: self._resolve_consensus_vote,
        }

        logger.info(
            "Arbiter Agent initialized",
            agent_id=self.agent_id,
            auto_resolution=self._auto_resolution,
            escalation_threshold=self._escalation_threshold,
        )

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming message with conflict resolution.

        Session 44: Enhanced with collective learning pattern tracking,
        consensus deliberation support, and memory access optimization.
        """
        try:
            # Session 44: Track memory access for this message processing
            memory_id = f"arbiter_msg_{message.message_type}_{message.sender_id}"
            if self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=memory_id,
                    access_type="read",
                    agent_id=self.agent_id,
                )

            # Session 44: Zero-trust validation of incoming message
            if self.zero_trust_validator:
                validation_result = self.zero_trust_validator.validate_message(message.content)
                if not validation_result.get("valid", True):
                    logger.warning(
                        "Zero-trust validation failed",
                        message_type=message.message_type,
                        reason=validation_result.get("reason", "unknown"),
                    )

            handler = self._message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                logger.warning(
                    "Unknown message type",
                    message_type=message.message_type,
                    sender=message.sender_id,
                )
        except Exception as e:
            logger.error(
                "Error processing message",
                message_type=message.message_type,
                error=str(e),
                exc_info=True,
            )

    def _register_handlers(self) -> None:
        """Register message handlers."""
        self._message_handlers = {
            "report_conflict": self._handle_report_conflict,
            "request_arbitration": self._handle_request_arbitration,
            "mediate_dispute": self._handle_mediate_dispute,
            "resolve_contention": self._handle_resolve_contention,
            "get_conflict_details": self._handle_get_conflict_details,
            "get_active_conflicts": self._handle_get_active_conflicts,
            "propose_resolution": self._handle_propose_resolution,
            "accept_resolution": self._handle_accept_resolution,
            "get_relationship_status": self._handle_get_relationship_status,
            "get_relationship_health": self._handle_get_relationship_health,
            "update_relationship": self._handle_update_relationship,
            "get_arbitration_report": self._handle_get_arbitration_report,
            "register_interaction": self._handle_register_interaction,
        }

    async def _handle_report_conflict(self, message: ActorMessage) -> None:
        """
        Report an inter-agent conflict.

        Content: {
            "conflict_type": str,
            "severity": str (optional),
            "parties": List[str],
            "description": str,
            "context": Dict (optional),
            "evidence": List[Dict] (optional)
        }
        """
        try:
            content = message.content
            conflict_type_str = content.get("conflict_type")
            severity_str = content.get("severity", ConflictSeverity.MEDIUM.value)
            parties = content.get("parties", [])
            description = content.get("description", "")
            context = content.get("context", {})
            evidence = content.get("evidence", [])

            # Validate
            validate_message({
                "sender_id": message.sender_id,
                "message_type": "report_conflict",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Convert enums
            try:
                conflict_type = ConflictType(conflict_type_str)
            except ValueError:
                conflict_type = ConflictType.COMMUNICATION_BREAKDOWN

            try:
                severity = ConflictSeverity(severity_str)
            except ValueError:
                severity = ConflictSeverity.MEDIUM

            # Create conflict record
            conflict_id = self._create_conflict_id()
            conflict = Conflict(
                conflict_id=conflict_id,
                conflict_type=conflict_type,
                severity=severity,
                status=ResolutionStatus.PENDING,
                timestamp=datetime.now(UTC),
                parties=parties,
                description=description,
                context=context,
                evidence=evidence,
            )

            # Store conflict
            self._conflicts[conflict_id] = conflict
            self._conflict_history.append(conflict_id)

            # Update statistics
            self._stats["total_conflicts"] += 1
            self._stats["conflicts_by_type"][conflict_type.value] += 1
            self._stats["conflicts_by_severity"][severity.value] += 1

            # Update relationships
            self._update_relationships_for_conflict(conflict)

            # Auto-resolution if enabled
            resolution_result = None
            if self._auto_resolution:
                resolution_result = await self._attempt_auto_resolution(conflict)

            # LRU cleanup
            if len(self._conflict_history) > self._max_conflicts:
                oldest = self._conflict_history.pop(0)
                self._conflicts.pop(oldest, None)

            logger.warning(
                "Conflict reported",
                conflict_id=conflict_id,
                conflict_type=conflict_type.value,
                severity=severity.value,
                parties=parties,
                auto_resolution=resolution_result is not None,
            )

            response_content = {
                "conflict_id": conflict_id,
                "status": conflict.status.value,
                "severity": severity.value,
                "auto_resolution_attempted": resolution_result is not None,
                "resolution_status": resolution_result.get("status") if resolution_result else None,
                "next_steps": self._get_next_steps(conflict),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid conflict report", str(ve))
        except Exception as e:
            logger.error("Error reporting conflict", error=str(e), exc_info=True)
            await self._send_error(message, "Conflict report failed", str(e))

    async def _handle_request_arbitration(self, message: ActorMessage) -> None:
        """
        Request formal arbitration for a conflict.

        Content: {
            "conflict_id": str (optional),
            "parties": List[str] (optional),
            "dispute": str,
            "desired_outcome": str (optional),
            "urgency": str (optional)
        }
        """
        try:
            content = message.content
            conflict_id = content.get("conflict_id")
            parties = content.get("parties", [])
            dispute = content.get("dispute", "")
            desired_outcome = content.get("desired_outcome")
            urgency = content.get("urgency", "normal")

            # Validate
            validate_message({
                "sender_id": message.sender_id,
                "message_type": "request_arbitration",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Get or create conflict
            if conflict_id and conflict_id in self._conflicts:
                conflict = self._conflicts[conflict_id]
            else:
                # Create new conflict for arbitration
                conflict_id = self._create_conflict_id()
                conflict = Conflict(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.AUTHORITY_CONFLICT,
                    severity=ConflictSeverity.HIGH if urgency == "urgent" else ConflictSeverity.MEDIUM,
                    status=ResolutionStatus.IN_PROGRESS,
                    timestamp=datetime.now(UTC),
                    parties=[*parties, message.sender_id],
                    description=dispute,
                    context={"desired_outcome": desired_outcome, "urgency": urgency},
                )
                self._conflicts[conflict_id] = conflict
                self._conflict_history.append(conflict_id)

            # Register for arbitration
            self._pending_arbitrations[conflict_id] = self._pending_arbitrations.get(conflict_id, [])
            self._pending_arbitrations[conflict_id].append(message.sender_id)

            # Check if all parties are present
            all_parties_present = all(p in self._pending_arbitrations[conflict_id] for p in conflict.parties)

            response_content = {
                "conflict_id": conflict_id,
                "arbitration_status": "in_progress",
                "parties_registered": len(self._pending_arbitrations[conflict_id]),
                "total_parties": len(set(conflict.parties)),
                "all_parties_present": all_parties_present,
                "next_step": "waiting_for_parties" if not all_parties_present else "arbitration_scheduled",
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid arbitration request", str(ve))
        except Exception as e:
            logger.error("Error requesting arbitration", error=str(e), exc_info=True)
            await self._send_error(message, "Arbitration request failed", str(e))

    async def _handle_mediate_dispute(self, message: ActorMessage) -> None:
        """
        Request mediation for a dispute.

        Content: {
            "conflict_id": str (optional),
            "dispute_description": str,
            "other_party": str,
            "proposed_solution": str (optional)
        }
        """
        try:
            content = message.content
            _ = content.get("conflict_id")  # Required for message contract
            dispute_description = content.get("dispute_description", "")
            other_party = content.get("other_party")
            proposed_solution = content.get("proposed_solution")

            # Validate
            validate_message({
                "sender_id": message.sender_id,
                "message_type": "mediate_dispute",
                "content": content,
                "timestamp": message.timestamp,
                })

                # Perform mediation:
            mediation_result = await self._conduct_mediation(
                sender=message.sender_id,
                other_party=other_party,
                dispute=dispute_description,
                proposed_solution=proposed_solution,
            )

            response_content = {
                "mediation_status": mediation_result["status"],
                "resolution_achieved": mediation_result["resolved"],
                "agreement": mediation_result.get("agreement"),
                "follow_up_actions": mediation_result.get("actions", []),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid mediation request", str(ve))
        except Exception as e:
            logger.error("Error mediating dispute", error=str(e), exc_info=True)
            await self._send_error(message, "Mediation failed", str(e))

    async def _handle_resolve_contention(self, message: ActorMessage) -> None:
        """
        Resolve resource or task contention.

        Content: {
            "contention_type": str,
            "resource": str (optional),
            "competing_agents": List[str],
            "priority_override": Dict[str, int] (optional)
        }
        """
        try:
            content = message.content
            contention_type = content.get("contention_type", "resource")
            resource = content.get("resource")
            competing_agents = content.get("competing_agents", [])
            priority_override = content.get("priority_override", {})

            # Validate
            validate_message({
                "sender_id": message.sender_id,
                "message_type": "resolve_contention",
                "content": content,
                "timestamp": message.timestamp,
            })

            # Resolve based on contention type
            if contention_type == "resource":
                resolution = await self._resolve_resource_contention(
                    resource=resource,
                    competing_agents=competing_agents,
                    priority_override=priority_override,
                )
            elif contention_type == "task":
                resolution = await self._resolve_task_contention(
                    competing_agents=competing_agents,
                    priority_override=priority_override,
                )
            else:
                resolution = await self._resolve_generic_contention(
                    contention_type=contention_type,
                    competing_agents=competing_agents,
                )

            response_content = {
                "resolution": resolution,
                "assigned_to": resolution.get("winner"),
                "reasoning": resolution.get("reasoning"),
                "alternative安排": resolution.get("alternatives"),
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid contention resolution", str(ve))
        except Exception as e:
            logger.error("Error resolving contention", error=str(e), exc_info=True)
            await self._send_error(message, "Contention resolution failed", str(e))

    async def _handle_get_conflict_details(self, message: ActorMessage) -> None:
        """
        Get detailed information about a specific conflict.

        Content: {
            "conflict_id": str
        }
        """
        try:
            content = message.content
            conflict_id = content.get("conflict_id")

            if not conflict_id:
                await self._send_error(message, "Missing conflict_id")
                return

            conflict = self._conflicts.get(conflict_id)
            if not conflict:
                await self._send_error(message, "Conflict not found", conflict_id)
                return

            response_content = {
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict.conflict_type.value,
                "severity": conflict.severity.value,
                "status": conflict.status.value,
                "timestamp": conflict.timestamp.isoformat(),
                "parties": conflict.parties,
                "description": conflict.description,
                "context": conflict.context,
                "evidence": conflict.evidence,
                "proposed_resolutions": conflict.proposed_resolutions,
                "selected_resolution": conflict.selected_resolution,
                "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None,
                "resolution_notes": conflict.resolution_notes,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid request", str(ve))
        except Exception as e:
            logger.error("Error getting conflict details", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get conflict details", str(e))

    async def _handle_get_active_conflicts(self, message: ActorMessage) -> None:
        """
        Get all active (unresolved) conflicts.

        Content: {
            "severity_filter": str (optional),
            "party_filter": str (optional),
            "limit": int (optional)
        }
        """
        try:
            content = message.content
            severity_filter = content.get("severity_filter")
            party_filter = content.get("party_filter")
            limit = content.get("limit", 100)

            active_conflicts = [
                c for c in self._conflicts.values()
                if c.status not in [ResolutionStatus.RESOLVED, ResolutionStatus.FAILED]
            ]

            # Apply filters
            if severity_filter:
                try:
                    min_severity = ConflictSeverity(severity_filter)
                    severity_order = {
                        ConflictSeverity.LOW: 0,
                        ConflictSeverity.MEDIUM: 1,
                        ConflictSeverity.HIGH: 2,
                        ConflictSeverity.CRITICAL: 3,
                    }
                    min_order = severity_order.get(min_severity, 0)
                    active_conflicts = [
                        c for c in active_conflicts
                        if severity_order.get(c.severity, 0) >= min_order
                    ]
                except ValueError:
                    pass

            if party_filter:
                active_conflicts = [
                    c for c in active_conflicts
                    if party_filter in c.parties
                ]

            # Sort by severity
            severity_order = {
                ConflictSeverity.CRITICAL: 3,
                ConflictSeverity.HIGH: 2,
                ConflictSeverity.MEDIUM: 1,
                ConflictSeverity.LOW: 0,
            }
            active_conflicts.sort(
                key=lambda x: severity_order.get(x.severity, 0),
                reverse=True,
            )

            # Apply limit
            active_conflicts = active_conflicts[:limit]

            response_content = {
                "active_conflicts_count": len(active_conflicts),
                "conflicts": [
                    {
                        "conflict_id": c.conflict_id,
                        "conflict_type": c.conflict_type.value,
                        "severity": c.severity.value,
                        "status": c.status.value,
                        "parties": c.parties,
                        "description": c.description,
                    }
                    for c in active_conflicts
                ],
            }

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting active conflicts", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get active conflicts", str(e))

    async def _handle_propose_resolution(self, message: ActorMessage) -> None:
        """
        Propose a resolution for a conflict.

        Content: {
            "conflict_id": str,
            "resolution_strategy": str,
            "proposal": Dict,
            "rationale": str (optional)
        }
        """
        try:
            content = message.content
            conflict_id = content.get("conflict_id")
            resolution_strategy = content.get("resolution_strategy")
            proposal = content.get("proposal", {})
            rationale = content.get("rationale", "")

            if not conflict_id:
                await self._send_error(message, "Missing conflict_id")
                return

            conflict = self._conflicts.get(conflict_id)
            if not conflict:
                await self._send_error(message, "Conflict not found", conflict_id)
                return

            # Add proposed resolution
            proposed = {
                "proposed_by": message.sender_id,
                "strategy": resolution_strategy,
                "proposal": proposal,
                "rationale": rationale,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            conflict.proposed_resolutions.append(proposed)

            response_content = {
                "conflict_id": conflict_id,
                "proposal_accepted": True,
                "total_proposals": len(conflict.proposed_resolutions),
                "next_step": "waiting_for_acceptance",
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid proposal", str(ve))
        except Exception as e:
            logger.error("Error proposing resolution", error=str(e), exc_info=True)
            await self._send_error(message, "Proposal failed", str(e))

    async def _handle_accept_resolution(self, message: ActorMessage) -> None:
        """
        Accept a proposed resolution.

        Content: {
            "conflict_id": str,
            "proposal_index": int (optional),
            "resolution_data": Dict (optional)
        }
        """
        try:
            content = message.content
            conflict_id = content.get("conflict_id")
            proposal_index = content.get("proposal_index", -1)
            resolution_data = content.get("resolution_data")

            if not conflict_id:
                await self._send_error(message, "Missing conflict_id")
                return

            conflict = self._conflicts.get(conflict_id)
            if not conflict:
                await self._send_error(message, "Conflict not found", conflict_id)
                return

            # Select or create resolution
            if resolution_data:
                selected = resolution_data
            elif 0 <= proposal_index < len(conflict.proposed_resolutions):
                selected = conflict.proposed_resolutions[proposal_index]
            elif conflict.proposed_resolutions:
                selected = conflict.proposed_resolutions[-1]
            else:
                selected = {"resolution": "default", "details": {}}

            # Apply resolution
            conflict.selected_resolution = selected
            conflict.status = ResolutionStatus.RESOLVED
            conflict.resolved_at = datetime.now(UTC)

            # Update statistics
            self._stats["resolutions_successful"] += 1

            # Update relationships
            self._update_relationships_for_resolution(conflict)

            response_content = {
                "conflict_id": conflict_id,
                "resolution_accepted": True,
                "status": ResolutionStatus.RESOLVED.value,
                "resolution": selected,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid acceptance", str(ve))
        except Exception as e:
            logger.error("Error accepting resolution", error=str(e), exc_info=True)
            await self._send_error(message, "Acceptance failed", str(e))

    async def _handle_get_relationship_status(self, message: ActorMessage) -> None:
        """
        Get relationship status between two agents.

        Content: {
            "agent_a": str,
            "agent_b": str
        }
        """
        try:
            content = message.content
            agent_a = content.get("agent_a")
            agent_b = content.get("agent_b")

            if not agent_a or not agent_b:
                await self._send_error(message, "Missing agent_a or agent_b")
                return

            # Normalize key (alphabetically ordered)
            key = tuple(sorted([agent_a, agent_b]))
            relationship = self._relationships.get(key)

            if not relationship:
                response_content = {
                    "agent_a": agent_a,
                    "agent_b": agent_b,
                    "relationship_exists": False,
                    "health_score": 0.5,  # Default neutral
                }
            else:
                response_content = {
                    "agent_a": relationship.agent_a,
                    "agent_b": relationship.agent_b,
                    "health_score": relationship.health_score,
                    "interaction_count": relationship.interaction_count,
                    "conflict_count": relationship.conflict_count,
                    "cooperation_count": relationship.cooperation_count,
                    "trust_level": relationship.trust_level,
                    "last_interaction": relationship.last_interaction.isoformat(),
                    "tags": relationship.tags,
                }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid request", str(ve))
        except Exception as e:
            logger.error("Error getting relationship status", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get relationship status", str(e))

    async def _handle_get_relationship_health(self, message: ActorMessage) -> None:
        """
        Get overall relationship health across the Collective.

        Content: {
            "include_details": bool (optional)
        }
        """
        try:
            content = message.content
            include_details = content.get("include_details", False)

            # Calculate aggregate health
            if self._relationships:
                avg_health = sum(r.health_score for r in self._relationships.values()) / len(self._relationships)
                avg_trust = sum(r.trust_level for r in self._relationships.values()) / len(self._relationships)
            else:
                avg_health = 1.0
                avg_trust = 1.0

            response_content = {
                "total_relationships": len(self._relationships),
                "average_health_score": avg_health,
                "average_trust_level": avg_trust,
                "relationships_needing_attention": len([
                    r for r in self._relationships.values()
                    if r.health_score < 0.5
                ]),
            }

            if include_details:
                response_content["relationships"] = [
                    {
                        "agents": [r.agent_a, r.agent_b],
                        "health_score": r.health_score,
                        "trust_level": r.trust_level,
                        "conflict_count": r.conflict_count,
                    }
                    for r in self._relationships.values()
                ]

            await self._send_response(message, response_content)

        except Exception as e:
            logger.error("Error getting relationship health", error=str(e), exc_info=True)
            await self._send_error(message, "Relationship health check failed", str(e))

    async def _handle_update_relationship(self, message: ActorMessage) -> None:
        """
        Update relationship metrics based on interaction.

        Content: {
            "other_agent": str,
            "interaction_type": str,
            "outcome": str (optional),
            "trust_delta": float (optional)
        }
        """
        try:
            content = message.content
            other_agent = content.get("other_agent")
            interaction_type = content.get("interaction_type", "neutral")
            content.get("outcome", "neutral")
            trust_delta = content.get("trust_delta", 0.0)

            if not other_agent:
                await self._send_error(message, "Missing other_agent")
                return

            # Get or create relationship
            key = tuple(sorted([message.sender_id, other_agent]))

            if key not in self._relationships:
                self._relationships[key] = Relationship(
                    agent_a=key[0],
                    agent_b=key[1],
                    health_score=0.7,  # Start slightly positive
                    interaction_count=0,
                    conflict_count=0,
                    cooperation_count=0,
                    last_interaction=datetime.now(UTC),
                    trust_level=0.5,  # Start neutral
                )

            relationship = self._relationships[key]

            # Update metrics
            relationship.interaction_count += 1
            relationship.last_interaction = datetime.now(UTC)

            if interaction_type in ["cooperation", "helpful", "collaborative"]:
                relationship.cooperation_count += 1
                relationship.health_score = min(1.0, relationship.health_score + 0.05)
            elif interaction_type in ["conflict", "dispute", "contention"]:
                relationship.conflict_count += 1
                relationship.health_score = max(0.0, relationship.health_score - 0.1)

            # Apply trust delta
            relationship.trust_level = max(0.0, min(1.0, relationship.trust_level + trust_delta))

            # Apply decay to health score
            relationship.health_score = max(0.0, relationship.health_score - self._relationship_decay)

            response_content = {
                "relationship_updated": True,
                "health_score": relationship.health_score,
                "trust_level": relationship.trust_level,
                "interaction_count": relationship.interaction_count,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid update", str(ve))
        except Exception as e:
            logger.error("Error updating relationship", error=str(e), exc_info=True)
            await self._send_error(message, "Relationship update failed", str(e))

    async def _handle_get_arbitration_report(self, message: ActorMessage) -> None:
        """
        Generate comprehensive arbitration report.

        Content: {
            "time_range": str (optional),
            "include_recommendations": bool (optional)
        }
        """
        try:
            content = message.content
            time_range = content.get("time_range", "24h")
            include_recommendations = content.get("include_recommendations", True)

            # Calculate statistics
            active_conflicts = len([
                c for c in self._conflicts.values()
                if c.status not in [ResolutionStatus.RESOLVED, ResolutionStatus.FAILED]
            ])
            resolved_conflicts = len([
                c for c in self._conflicts.values()
                if c.status == ResolutionStatus.RESOLVED
            ])
            failed_resolutions = len([
                c for c in self._conflicts.values()
                if c.status == ResolutionStatus.FAILED
            ])

            conflicts_by_type = dict(self._stats["conflicts_by_type"])
            conflicts_by_severity = dict(self._stats["conflicts_by_severity"])

            # Relationship health summary
            relationship_health = {
                f"{r.agent_a}-{r.agent_b}": r.health_score
                for r in self._relationships.values()
            }

            # Generate recommendations
            recommendations = []
            if include_recommendations:
                recommendations = self._generate_recommendations()

            report = {
                "report_id": f"arb_report_{datetime.now(UTC).timestamp()}",
                "timestamp": datetime.now(UTC).isoformat(),
                "time_range": time_range,
                "active_conflicts": active_conflicts,
                "resolved_conflicts": resolved_conflicts,
                "failed_resolutions": failed_resolutions,
                "conflicts_by_type": conflicts_by_type,
                "conflicts_by_severity": conflicts_by_severity,
                "relationship_health": relationship_health,
                "statistics": {
                    "total_conflicts": self._stats["total_conflicts"],
                    "resolutions_successful": self._stats["resolutions_successful"],
                    "resolutions_failed": self._stats["resolutions_failed"],
                    "resolutions_escalated": self._stats["resolutions_escalated"],
                    "average_resolution_time": self._stats["average_resolution_time"],
                },
                "recommendations": recommendations,
            }

            await self._send_response(message, {"report": report})

        except Exception as e:
            logger.error("Error generating arbitration report", error=str(e), exc_info=True)
            await self._send_error(message, "Report generation failed", str(e))

    async def _handle_register_interaction(self, message: ActorMessage) -> None:
        """
        Register an inter-agent interaction for relationship tracking.

        Content: {
            "other_agent": str,
            "interaction_type": str,
            "outcome": str (optional),
            "success": bool (optional)
        }
        """
        try:
            content = message.content
            other_agent = content.get("other_agent")
            content.get("interaction_type", "communication")
            outcome = content.get("outcome", "neutral")
            success = content.get("success", True)

            if not other_agent:
                await self._send_error(message, "Missing other_agent")
                return

            # Update relationship
            key = tuple(sorted([message.sender_id, other_agent]))

            if key not in self._relationships:
                self._relationships[key] = Relationship(
                    agent_a=key[0],
                    agent_b=key[1],
                    health_score=0.7,
                    interaction_count=0,
                    conflict_count=0,
                    cooperation_count=0,
                    last_interaction=datetime.now(UTC),
                    trust_level=0.5,
                )

            relationship = self._relationships[key]
            relationship.interaction_count += 1
            relationship.last_interaction = datetime.now(UTC)

            if success and outcome in ["positive", "successful", "helpful"]:
                relationship.cooperation_count += 1
                relationship.health_score = min(1.0, relationship.health_score + 0.02)
                relationship.trust_level = min(1.0, relationship.trust_level + 0.01)

            response_content = {
                "interaction_registered": True,
                "relationship_health": relationship.health_score,
                "trust_level": relationship.trust_level,
            }

            await self._send_response(message, response_content)

        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid interaction", str(ve))
        except Exception as e:
            logger.error("Error registering interaction", error=str(e), exc_info=True)
            await self._send_error(message, "Interaction registration failed", str(e))

    def _create_conflict_id(self) -> str:
        """Generate unique conflict ID."""
        import hashlib
        timestamp = datetime.now(UTC).timestamp()
        random_suffix = hashlib.sha256(str(timestamp).encode()).hexdigest()[:8]
        return f"CONFLICT_{int(timestamp)}_{random_suffix}"

    def _update_relationships_for_conflict(self, conflict: Conflict) -> None:
        """Update relationship records when a conflict is reported."""
        # Decrement health for all party pairs
        for i, party_a in enumerate(conflict.parties):
            for party_b in conflict.parties[i+1:]:
                key = tuple(sorted([party_a, party_b]))

                if key not in self._relationships:
                    self._relationships[key] = Relationship(
                        agent_a=key[0],
                        agent_b=key[1],
                        health_score=0.7,
                        interaction_count=0,
                        conflict_count=0,
                        cooperation_count=0,
                        last_interaction=datetime.now(UTC),
                        trust_level=0.5,
                    )

                relationship = self._relationships[key]
                relationship.conflict_count += 1
                relationship.health_score = max(0.0, relationship.health_score - 0.1)
                relationship.trust_level = max(0.0, relationship.trust_level - 0.05)

    def _update_relationships_for_resolution(self, conflict: Conflict) -> None:
        """Update relationship records when a conflict is resolved."""
        for i, party_a in enumerate(conflict.parties):
            for party_b in conflict.parties[i+1:]:
                key = tuple(sorted([party_a, party_b]))

                if key in self._relationships:
                    relationship = self._relationships[key]
                    relationship.health_score = min(1.0, relationship.health_score + 0.1)
                    relationship.trust_level = min(1.0, relationship.trust_level + 0.05)

    async def _attempt_auto_resolution(self, conflict: Conflict) -> dict[str, Any] | None:
        """Attempt automatic resolution based on conflict type and severity."""
        # Select strategy based on conflict type
        strategy_map = {
            ConflictType.RESOURCE_CONTENTION: ResolutionStrategy.RESOURCE_POOLING,
            ConflictType.TASK_OVERLAP: ResolutionStrategy.TASK_REASSIGNMENT,
            ConflictType.PRIORITY_DISPUTE: ResolutionStrategy.PRIORITY_BASED,
            ConflictType.COMMUNICATION_BREAKDOWN: ResolutionStrategy.MEDIATION,
            ConflictType.AUTHORITY_CONFLICT: ResolutionStrategy.ARBITRATION,
            ConflictType.DATA_INCONSISTENCY: ResolutionStrategy.CONSENSUS_VOTE,
            ConflictType.GOAL_MISALIGNMENT: ResolutionStrategy.NEGOTIATION,
            ConflictType.CAPABILITY_OVERLAP: ResolutionStrategy.ROUND_ROBIN,
            ConflictType.MESSAGE_FLOOD: ResolutionStrategy.RATE_LIMIT,
            ConflictType.DEADLOCK: ResolutionStrategy.ESCALATION,
        }

        strategy = strategy_map.get(conflict.conflict_type, ResolutionStrategy.MEDIATION)

        # Skip auto-resolution for critical conflicts
        if conflict.severity == ConflictSeverity.CRITICAL:
            return {"status": "escalated", "reason": "critical_severity"}

        # Execute resolution strategy
        if strategy in self._resolution_strategies:
            return await self._resolution_strategies[strategy](conflict)

        return None

    async def _resolve_negotiation(self, conflict: Conflict) -> dict[str, Any]:
        """Negotiation-based resolution."""
        # Generate compromise proposal
        proposal = {
            "strategy": "negotiation",
            "approach": "find_common_ground",
            "suggested_compromise": "Equal resource sharing with time-boxed access",
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "proposal_generated", "strategy": "negotiation"}

    async def _resolve_mediation(self, conflict: Conflict) -> dict[str, Any]:
        """Mediation-based resolution."""
        proposal = {
            "strategy": "mediation",
            "approach": "facilitated_dialogue",
            "mediator_notes": "Parties encouraged to find mutually beneficial solution",
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "mediation_initiated", "strategy": "mediation"}

    async def _resolve_arbitration(self, conflict: Conflict) -> dict[str, Any]:
        """
        Arbitration-based resolution (binding decision).

        Session 44: Enhanced with pattern emission for collective learning
        and memory access tracking.
        """
        # Make binding decision based on evidence
        decision = {
            "strategy": "arbitration",
            "binding": True,
            "decision": "Based on evidence, ruling in favor of party with stronger justification",
        }
        conflict.selected_resolution = decision
        conflict.status = ResolutionStatus.RESOLVED
        conflict.resolved_at = datetime.now(UTC)
        self._stats["resolutions_successful"] += 1

        # Session 44: Emit pattern for collective learning
        await self._emit_conflict_pattern(conflict, "success")

        # Session 44: Track memory access for this resolution
        self._track_resolution_memory_access(conflict.conflict_id, "write")

        return {"status": "arbitration_complete", "decision": decision}

    async def _resolve_priority_based(self, conflict: Conflict) -> dict[str, Any]:
        """Priority-based resolution."""
        # Assign based on priority (would need priority data from context)
        proposal = {
            "strategy": "priority_based",
            "approach": "assign_to_highest_priority",
            "note": "Priority data required from parties",
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "priority_check_required", "strategy": "priority_based"}

    async def _resolve_round_robin(self, conflict: Conflict) -> dict[str, Any]:
        """Round-robin resource allocation."""
        proposal = {
            "strategy": "round_robin",
            "approach": "alternating_access",
            "schedule": "Equal time slices with rotation",
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "round_robin_proposed", "strategy": "round_robin"}

    async def _resolve_resource_pooling(self, conflict: Conflict) -> dict[str, Any]:
        """Resource pooling resolution."""
        proposal = {
            "strategy": "resource_pooling",
            "approach": "shared_resource_pool",
            "allocation_method": "dynamic_based_on_need",
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "pooling_proposed", "strategy": "resource_pooling"}

    async def _resolve_task_reassignment(self, conflict: Conflict) -> dict[str, Any]:
        """Task reassignment resolution."""
        proposal = {
            "strategy": "task_reassignment",
            "approach": "redistribute_tasks",
            "note": "Task boundaries to be clarified",
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "reassignment_proposed", "strategy": "task_reassignment"}

    async def _resolve_escalation(self, conflict: Conflict) -> dict[str, Any]:
        """Escalation to higher authority."""
        conflict.status = ResolutionStatus.ESCALATED
        self._stats["resolutions_escalated"] += 1
        return {"status": "escalated", "strategy": "escalation", "escalated_to": "supervisor"}

    async def _resolve_compromise(self, conflict: Conflict) -> dict[str, Any]:
        """Compromise-based resolution."""
        proposal = {
            "strategy": "compromise",
            "approach": "mutual_concessions",
            "suggested_terms": "Each party concedes on lower-priority items",
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "compromise_proposed", "strategy": "compromise"}

    async def _resolve_consensus_vote(self, conflict: Conflict) -> dict[str, Any]:
        """Consensus vote resolution."""
        proposal = {
            "strategy": "consensus_vote",
            "approach": "majority_decision",
            "voting_parties": conflict.parties,
        }
        conflict.proposed_resolutions.append(proposal)
        return {"status": "vote_scheduled", "strategy": "consensus_vote"}

    async def _conduct_mediation(
        self,
        sender: str,
        other_party: str,
        dispute: str,
        proposed_solution: str | None = None,
    ) -> dict[str, Any]:
        """Conduct mediation between two parties."""
        # Check if other party is available
        # In a real implementation, this would message the other party

        mediation_result = {
            "status": "mediation_complete",
            "resolved": False,
            "agreement": None,
            "actions": [],
        }

        if proposed_solution:
            # Try to broker agreement around proposed solution
            mediation_result["resolved"] = True
            mediation_result["agreement"] = {
                "solution": proposed_solution,
                "mediated_by": self.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            mediation_result["actions"] = [
                f"Both parties to implement: {proposed_solution}",
                "Follow-up review in 24 hours",
            ]
        else:
            # Generate mediated solution
            mediated_solution = f"Both parties agree to cooperate on: {dispute}"
            mediation_result["resolved"] = True
            mediation_result["agreement"] = {
                "solution": mediated_solution,
                "mediated_by": self.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Update relationship
        key = tuple(sorted([sender, other_party]))
        if key in self._relationships:
            self._relationships[key].health_score = min(1.0, self._relationships[key].health_score + 0.1)

        return mediation_result

    async def _resolve_resource_contention(
        self,
        resource: str | None,  # noqa: ARG002 — part of public API signature
        competing_agents: list[str],
        priority_override: dict[str, int],
    ) -> dict[str, Any]:
        """Resolve contention over a resource."""
        if not competing_agents:
            return {"winner": None, "reasoning": "No competing agents"}

        # Use priority if available
        if priority_override:
            winner = max(competing_agents, key=lambda a: priority_override.get(a, 0))
            return {
                "winner": winner,
                "reasoning": "Highest priority agent selected",
                "alternatives": [a for a in competing_agents if a != winner],
            }

        # Default: first agent gets resource (could be improved with more sophisticated logic)
        winner = competing_agents[0]
        return {
            "winner": winner,
            "reasoning": "First-come-first-served (no priority data)",
            "alternatives": competing_agents[1:],
            "suggestion": "Implement priority-based allocation for better fairness",
        }

    async def _resolve_task_contention(
        self,
        competing_agents: list[str],
        priority_override: dict[str, int],  # noqa: ARG002 — part of public API signature
    ) -> dict[str, Any]:
        """Resolve contention over task ownership."""
        if not competing_agents:
            return {"assigned_to": None, "reasoning": "No competing agents"}

        # Split task if possible
        return {
            "assigned_to": competing_agents[0],
            "reasoning": "Task assigned to first agent",
            "alternatives": [
                {"agent": a, "subtask": f"Supporting role for agent {a}"}
                for a in competing_agents[1:]
            ],
        }

    async def _resolve_generic_contention(
        self,
        contention_type: str,
        competing_agents: list[str],
    ) -> dict[str, Any]:
        """Resolve generic contention."""
        return {
            "contention_type": contention_type,
            "resolution": "mediation_recommended",
            "parties": competing_agents,
            "next_step": "Schedule mediation session",
        }

    def _get_next_steps(self, conflict: Conflict) -> list[str]:
        """Get recommended next steps for a conflict."""
        steps = []

        if conflict.status == ResolutionStatus.PENDING:
            steps.append("Awaiting auto-resolution or manual intervention")
            if conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
                steps.append("Consider escalation due to high severity")

        elif conflict.status == ResolutionStatus.IN_PROGRESS:
            steps.append("Resolution process underway")
            steps.append("Monitor for party cooperation")

        elif conflict.status == ResolutionStatus.RESOLVED:
            steps.append("Implement resolution terms")
            steps.append("Monitor for compliance")

        return steps

    def _generate_recommendations(self) -> list[str]:
        """
        Generate strategic recommendations based on conflict patterns.

        Session 44: Enhanced with collective learning pattern analysis
        and memory access pattern insights.
        """
        recommendations = []

        # Check conflict volume
        if self._stats["total_conflicts"] > 50:
            recommendations.append(
                f"High conflict volume ({self._stats['total_conflicts']}) - review agent coordination protocols"
            )

        # Check resolution success rate
        if self._stats["resolutions_failed"] > 10:
            recommendations.append(
                "Multiple failed resolutions - consider alternative resolution strategies"
            )

        # Check relationship health
        unhealthy_relationships = [
            r for r in self._relationships.values()
            if r.health_score < 0.3
        ]
        if unhealthy_relationships:
            recommendations.append(
                f"{len(unhealthy_relationships)} relationships need attention - schedule mediation"
            )

        # Session 44: Add collective learning insights
        if self.pattern_extractor:
            validated_patterns = self.pattern_extractor.get_validated_patterns(
                pattern_type=PatternType.FAILURE,
                min_confidence=0.5,
            )
            if validated_patterns:
                recommendations.append(
                    f"Collective learning identified {len(validated_patterns)} failure patterns - review for systemic issues"
                )

        # Session 44: Add memory optimization insights
        if self.access_analyzer:
            stats = self.access_analyzer.get_statistics()
            if stats.frozen_count > stats.unique_memories * 0.5:
                recommendations.append(
                    f"High frozen memory ratio ({stats.frozen_count}/{stats.unique_memories}) - consider archive cleanup"
                )

        if not recommendations:
            recommendations.append("Collective harmony stable - continue monitoring")

        return recommendations

    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_conflict_pattern(self, conflict: Conflict, outcome: str) -> None:
        """
        Emit pattern for collective learning when conflict is resolved.

        Args:
            conflict: The resolved conflict
            outcome: Resolution outcome (success, failure, partial)
        """
        if not self.pattern_extractor:
            return

        if conflict.conflict_id in self._pattern_emitted_conflicts:
            return  # Already emitted

        # Emit pattern for collective learning
        try:
            # Analyze conflict resolution as a pattern
            await self.pattern_extractor.analyze_message(
                message_id=f"conflict_{conflict.conflict_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type="conflict_resolution",
                content={
                    "conflict_type": conflict.conflict_type.value,
                    "severity": conflict.severity.value,
                    "parties": conflict.parties,
                    "outcome": outcome,
                    "resolution_strategy": conflict.selected_resolution.get("strategy") if conflict.selected_resolution else None,
                },
                timestamp=conflict.timestamp.isoformat(),
            )

            self._pattern_emitted_conflicts.add(conflict.conflict_id)

            logger.info(
                "conflict_pattern_emitted",
                conflict_id=conflict.conflict_id,
                outcome=outcome,
            )
        except Exception as e:
            logger.warning(
                "failed_to_emit_conflict_pattern",
                conflict_id=conflict.conflict_id,
                error=str(e),
            )

    async def _consume_resolution_patterns(self) -> list[dict[str, Any]]:
        """
        Consume patterns from collective learning for resolution guidance.

        Returns:
            List of relevant patterns for current conflict resolution
        """
        if not self.pattern_extractor:
            return []

        try:
            # Extract patterns from recent history
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=[PatternType.SUCCESS, PatternType.HANDOFF, PatternType.DECISION],
            )

            # Return high-confidence patterns for resolution guidance
            return [
                p.to_dict() for p in patterns
                if p.metadata.confidence >= 0.7
            ]
        except Exception as e:
            logger.warning(
                "failed_to_consume_patterns",
                error=str(e),
            )
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation_for_conflict(
        self,
        conflict: Conflict,
        participating_agents: list[str],
    ) -> str | None:
        """
        Initiate swarm deliberation for complex conflict resolution.

        Args:
            conflict: Conflict requiring deliberation
            participating_agents: List of agent IDs to participate

        Returns:
            Deliberation ID if initiated, None otherwise
        """
        if not self.deliberation_engine:
            return None

        try:
            deliberation_id = f"delib_{conflict.conflict_id}"

            # Start deliberation with conflict domain
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=f"Resolve conflict: {conflict.description[:100]}",
                participants=participating_agents,
                domain="conflict_resolution",
            )

            # Store mapping
            self._active_deliberations[conflict.conflict_id] = deliberation_id

            logger.info(
                "deliberation_initiated",
                deliberation_id=deliberation_id,
                conflict_id=conflict.conflict_id,
                participants=len(participating_agents),
            )

            return deliberation_id
        except Exception as e:
            logger.error(
                "failed_to_initiate_deliberation",
                conflict_id=conflict.conflict_id,
                error=str(e),
            )
            return None

    async def _submit_deliberation_position(
        self,
        conflict: Conflict,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """
        Submit agent position in conflict deliberation.

        Args:
            conflict: Related conflict
            agent_id: Submitting agent
            position: Agent position (AGREE, DISAGREE, etc.)
            confidence: Confidence level
            argument: Supporting argument

        Returns:
            True if position submitted successfully
        """
        if not self.deliberation_engine:
            return False

        deliberation_id = self._active_deliberations.get(conflict.conflict_id)
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

            if success:
                # Track memory access for deliberation
                if self.access_analyzer:
                    self.access_analyzer.record_access(
                        memory_id=f"delib_{deliberation_id}_{agent_id}",
                        access_type="write",
                        agent_id=agent_id,
                    )

            return success
        except Exception as e:
            logger.error(
                "failed_to_submit_deliberation_position",
                deliberation_id=deliberation_id,
                error=str(e),
            )
            return False

    async def _finalize_deliberation(self, conflict: Conflict) -> DeliberationResult | None:
        """
        Finalize deliberation and apply result to conflict.

        Args:
            conflict: Related conflict

        Returns:
            Deliberation result if successful
        """
        if not self.deliberation_engine:
            return None

        deliberation_id = self._active_deliberations.get(conflict.conflict_id)
        if not deliberation_id:
            return None

        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)

            if result:
                # Apply deliberation result to conflict
                conflict.selected_resolution = {
                    "strategy": "consensus_deliberation",
                    "deliberation_id": deliberation_id,
                    "final_position": result.final_position.value,
                    "consensus_score": result.consensus_score,
                    "minority_report": result.minority_report,
                }
                conflict.status = ResolutionStatus.RESOLVED
                conflict.resolved_at = datetime.now(UTC)

                # Clean up deliberation
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[conflict.conflict_id]

                logger.info(
                    "deliberation_finalized",
                    deliberation_id=deliberation_id,
                    consensus_score=result.consensus_score,
                )

            return result
        except Exception as e:
            logger.error(
                "failed_to_finalize_deliberation",
                deliberation_id=deliberation_id,
                error=str(e),
            )
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_resolution_memory_access(self, conflict_id: str, access_type: str = "read") -> None:
        """
        Track memory access patterns for conflict resolution data.

        Args:
            conflict_id: Conflict identifier
            access_type: Type of access (read/write/delete)
        """
        if not self.access_analyzer:
            return

        memory_id = f"conflict_{conflict_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_conflict_memory_tier(self, conflict_id: str) -> AccessTier:
        """
        Get memory tier classification for a conflict.

        Args:
            conflict_id: Conflict identifier

        Returns:
            Access tier (HOT, WARM, COLD, FROZEN)
        """
        if not self.access_analyzer:
            return AccessTier.COLD

        memory_id = f"conflict_{conflict_id}"
        profile = self.access_analyzer.get_profile(memory_id)

        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant_conflicts(self, agent_id: str) -> list[str]:
        """
        Prefetch conflicts an agent is likely to need based on access patterns.

        Args:
            agent_id: Agent identifier

        Returns:
            List of predicted conflict IDs to prefetch
        """
        if not self.access_analyzer:
            return []

        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)

            # Extract conflict IDs from memory IDs
            return [
                mem.replace("conflict_", "")
                for mem in predicted_memories
                if mem.startswith("conflict_")
            ]

        except Exception as e:
            logger.warning(
                "failed_to_prefetch_conflicts",
                agent_id=agent_id,
                error=str(e),
            )
            return []

    def get_learning_status(self) -> dict[str, Any]:
        """
        Get collective learning and memory optimization status.

        Returns:
            Status dictionary with learning metrics
        """
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

