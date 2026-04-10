"""
Pattern Extraction Module - Cross-Agent Learning

Implements pattern extraction from agent message history for emergent intelligence.
This module analyzes agent interactions to identify successful patterns, track
decision outcomes, and extract learning signals for knowledge transfer.

Features:
- Pattern extraction from agent message history
- Successful interaction pattern identification
- Decision outcome tracking
- Learning signal extraction
- Pattern confidence scoring
- Temporal pattern analysis

Zero-Trust Principles:
- All patterns validated before storage
- Source attribution required
- Confidence thresholds enforced
- Audit logging for all extractions
"""

import asyncio
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import structlog

_logger = structlog.get_logger(__name__)


class PatternType(str, Enum):
    """Types of patterns that can be extracted."""
    
    SUCCESS = "success"
    FAILURE = "failure"
    OPTIMIZATION = "optimization"
    HANDOFF = "handoff"
    COLLABORATION = "collaboration"
    DECISION = "decision"
    COMMUNICATION = "communication"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RECOVERY = "error_recovery"
    EMERGENT = "emergent"


class PatternSource(str, Enum):
    """Source of pattern extraction."""
    
    MESSAGE_HISTORY = "message_history"
    DECISION_LOG = "decision_log"
    PERFORMANCE_METRICS = "performance_metrics"
    ERROR_LOG = "error_log"
    CONSENSUS_VOTES = "consensus_votes"
    TASK_OUTCOMES = "task_outcomes"
    AGENT_STATE = "agent_state"


@dataclass
class PatternMetadata:
    """Metadata for extracted patterns."""
    
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: PatternType = PatternType.SUCCESS
    source: PatternSource = PatternSource.MESSAGE_HISTORY
    confidence: float = 0.0
    support_count: int = 0
    first_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_observed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agents_involved: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: int = 1


@dataclass
class ExtractedPattern:
    """Represents an extracted pattern from agent interactions."""
    
    metadata: PatternMetadata
    pattern_data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    outcomes: List[Dict[str, Any]] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    applicability_conditions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary for serialization."""
        return {
            "pattern_id": self.metadata.pattern_id,
            "pattern_type": self.metadata.pattern_type.value,
            "source": self.metadata.source.value,
            "confidence": self.metadata.confidence,
            "support_count": self.metadata.support_count,
            "first_observed": self.metadata.first_observed,
            "last_observed": self.metadata.last_observed,
            "agents_involved": self.metadata.agents_involved,
            "topics": self.metadata.topics,
            "tags": self.metadata.tags,
            "pattern_data": self.pattern_data,
            "context": self.context,
            "outcomes": self.outcomes,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "applicability_conditions": self.applicability_conditions,
        }


@dataclass
class LearningSignal:
    """Represents a learning signal extracted from agent interactions."""
    
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_type: str = "reward"
    magnitude: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_agent: Optional[str] = None
    target_agents: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary for serialization."""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "magnitude": self.magnitude,
            "timestamp": self.timestamp,
            "source_agent": self.source_agent,
            "target_agents": self.target_agents,
            "context": self.context,
            "metadata": self.metadata,
        }


@dataclass
class MessageAnalysis:
    """Analysis result for a single message."""
    
    message_id: str
    sender: str
    recipient: str
    message_type: str
    timestamp: str
    content_hash: str
    sentiment_score: float = 0.0
    complexity_score: float = 0.0
    topic: Optional[str] = None
    intent: Optional[str] = None
    outcome: Optional[str] = None
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PatternExtractor:
    """
    Extracts patterns from agent message history and interactions.
    
    This class implements pattern extraction algorithms for identifying
    recurring successful interactions, decision patterns, and emergent
    behaviors in the agent swarm.
    
    Attributes:
        min_support: Minimum number of occurrences for pattern to be valid
        min_confidence: Minimum confidence threshold for pattern acceptance
        max_pattern_age_days: Maximum age for patterns before expiration
    """
    
    def __init__(self, min_support: int, min_confidence: float, max_pattern_age_days: int):
        """
        Initialize pattern extractor.
        
        Args:
            min_support: Minimum occurrences for pattern validity (default: 3)
            min_confidence: Minimum confidence threshold (default: 0.6)
            max_pattern_age_days: Maximum pattern age in days (default: 30)
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.max_pattern_age_days = max_pattern_age_days
        
        self._message_cache: List[MessageAnalysis] = []
        self._pattern_candidates: Dict[str, ExtractedPattern] = {}
        self._validated_patterns: Dict[str, ExtractedPattern] = {}
        self._learning_signals: List[LearningSignal] = []
        
        # Pattern extraction callbacks
        self._extraction_hooks: List[Callable] = []
        
        logger.info(
            "pattern_extractor_initialized",
            _min_support = min_support,
            _min_confidence = min_confidence,
            _max_pattern_age_days = max_pattern_age_days,
        )
    
    def register_extraction_hook(self, hook: Callable) -> None:
        """
        Register a hook to be called after pattern extraction.
        
        Args:
            hook: Async callable that receives ExtractedPattern
        """
        self._extraction_hooks.append(hook)
        logger.debug("extraction_hook_registered", hook=hook.__name__)
    
    async def analyze_message(self, message_id: str, sender: str, recipient: str, message_type: str, content: Dict[str, Any], timestamp: Optional[str]) -> MessageAnalysis:
        """
        Analyze a single message for pattern extraction.
        
        Args:
            message_id: Unique message identifier
            sender: Sending agent ID
            recipient: Receiving agent ID or topic
            message_type: Type of message
            content: Message content dictionary
            timestamp: Message timestamp (auto-generated if None)
            
        Returns:
            MessageAnalysis with extracted features
        """
        _ts = timestamp or datetime.now(timezone.utc).isoformat()
        
        # Generate content hash for deduplication
        _content_hash = self._generate_content_hash(content)
        
        # Analyze message characteristics
        sentiment = self._analyze_sentiment(content)
        complexity = self._analyze_complexity(content)
        topic = self._extract_topic(content)
        intent = self._infer_intent(message_type, content)
        
        _analysis = MessageAnalysis(
            _message_id = message_id,
            _sender = sender,
            _recipient = recipient,
            _message_type = message_type,
            timestamp=ts,
            _content_hash = content_hash,
            sentiment_score=sentiment,
            complexity_score=complexity,
            topic=topic,
            intent=intent,
            metadata={
                "content_length": len(str(content)),
                "has_reply_to": "reply_to" in content,
                "has_correlation": "correlation_id" in content,
            },
        )
        
        # Cache for pattern analysis
        self._message_cache.append(analysis)
        
        # Trim cache if too large
        if len(self._message_cache) > 10000:
            self._message_cache = self._message_cache[-5000:]
        
        logger.debug(
            "message_analyzed",
            _message_id = message_id,
            _sender = sender,
            topic=topic,
            intent=intent,
        )
        
        return analysis
    
    async def extract_patterns(self, time_window_hours: int, pattern_types: Optional[List[PatternType]]) -> List[ExtractedPattern]:
        """
        Extract patterns from cached message history.
        
        Args:
            time_window_hours: Time window for pattern extraction (default: 24)
            pattern_types: Specific pattern types to extract (default: all)
            
        Returns:
            List of extracted patterns meeting confidence thresholds
        """
        if pattern_types is None:
            _pattern_types = list(PatternType)
        
        # Filter messages within time window
        _cutoff = datetime.now(timezone.utc)
        from datetime import timedelta
        _cutoff = cutoff - timedelta(hours=time_window_hours)
        
        _recent_messages = [
            m for m in self._message_cache
            if datetime.fromisoformat(m.timestamp) >= cutoff
        ]
        
        logger.info(
            "extracting_patterns",
            _message_count = len(recent_messages),
            _time_window_hours = time_window_hours,
            _pattern_types = [pt.value for pt in pattern_types],
        )
        
        _extracted = []
        
        # Extract different pattern types
        for pattern_type in pattern_types:
            _patterns = await self._extract_pattern_type(
                pattern_type,
                recent_messages,
            )
            extracted.extend(patterns)
        
        # Validate and store patterns
        _validated = []
        for pattern in extracted:
            if await self._validate_pattern(pattern):
                self._validated_patterns[pattern.metadata.pattern_id] = pattern
                validated.append(pattern)
                
                # Call extraction hooks
                for hook in self._extraction_hooks:
                    try:
                        if asyncio.iscoroutinefunction(hook):
                            await hook(pattern)
                        else:
                            hook(pattern)
                    except Exception as e:
                        logger.error(
                            "extraction_hook_error",
                            _hook = hook.__name__,
                            _error = str(e),
                        )
        
        logger.info(
            "pattern_extraction_complete",
            _total_extracted = len(extracted),
            _total_validated = len(validated),
        )
        
        return validated
    
    async def track_outcome(self, pattern_id: str, outcome: str, outcome_data: Dict[str, Any]) -> None:
        """
        Track outcome for a specific pattern.
        
        Args:
            pattern_id: Pattern identifier
            outcome: Outcome type (success, failure, partial)
            outcome_data: Additional outcome data
        """
        if pattern_id in self._validated_patterns:
            pattern = self._validated_patterns[pattern_id]
            pattern.outcomes.append({
                "outcome": outcome,
                "data": outcome_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            
            # Update confidence based on outcome
            self._update_pattern_confidence(pattern, outcome)
            
            logger.debug(
                "outcome_tracked",
                pattern_id=pattern_id,
                outcome=outcome,
                _total_outcomes = len(pattern.outcomes),
            )
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate SHA256 hash of message content."""
        _content_str = str(sorted(content.items()))
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _analyze_sentiment(self, _content: Dict[str, Any]) -> float:
        """
        Analyze sentiment of message content.
        
        Returns float between -1.0 (negative) and 1.0 (positive).
        Default implementation returns neutral 0.0.
        """
        # Placeholder for sentiment analysis
        # Could integrate with NLP library for actual analysis
        return 0.0
    
    def _analyze_complexity(self, content: Dict[str, Any]) -> float:
        """
        Analyze complexity of message content.
        
        Returns float between 0.0 (simple) and 1.0 (complex).
        """
        # Measure complexity based on content structure
        _content_str = str(content)
        _length = len(content_str)
        _nesting = content_str.count("{") + content_str.count("[")
        
        # Normalize complexity score
        _length_score = min(length / 1000, 1.0)
        _nesting_score = min(nesting / 10, 1.0)
        
        return (length_score + nesting_score) / 2
    
    def _extract_topic(self, content: Dict[str, Any]) -> Optional[str]:
        """Extract topic from message content."""
        # Look for topic indicators in content
        if "topic" in content:
            return content["topic"]
        if "subject" in content:
            return content["subject"]
        if "task_type" in content:
            return content["task_type"]
        return None
    
    def _infer_intent(self, message_type: str, _content: Dict[str, Any]) -> Optional[str]:
        """Infer intent from message type and content."""
        _intent_map = {
            "request": "information_seeking",
            "response": "information_providing",
            "command": "action_request",
            "notification": "awareness",
            "handoff": "task_transfer",
            "collective_task": "collaboration_request",
            "collective_task_response": "collaboration_response",
            "health_check": "status_inquiry",
            "health_response": "status_report",
        }
        return intent_map.get(message_type, "unknown")
    
    async def _extract_pattern_type(self, pattern_type: PatternType, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns of a specific type."""
        _extractors = {
            PatternType.SUCCESS: self._extract_success_patterns,
            PatternType.FAILURE: self._extract_failure_patterns,
            PatternType.OPTIMIZATION: self._extract_optimization_patterns,
            PatternType.HANDOFF: self._extract_handoff_patterns,
            PatternType.COLLABORATION: self._extract_collaboration_patterns,
            PatternType.DECISION: self._extract_decision_patterns,
            PatternType.COMMUNICATION: self._extract_communication_patterns,
            PatternType.ERROR_RECOVERY: self._extract_error_recovery_patterns,
            PatternType.EMERGENT: self._extract_emergent_patterns,
        }
        
        extractor = extractors.get(pattern_type)
        if extractor:
            return await extractor(messages)
        return []
    
    async def _extract_success_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns from successful interactions."""
        _patterns = []
        
        # Group by sender-recipient pairs
        interaction_groups: Dict[Tuple[str, str], List[MessageAnalysis]] = {}
        for msg in messages:
            _key = (msg.sender, msg.recipient)
            if key not in interaction_groups:
                interaction_groups[key] = []
            interaction_groups[key].append(msg)
        
        # Find recurring successful interactions
        for (sender, recipient), group in interaction_groups.items():
            if len(group) >= self.min_support:
                # Calculate success rate based on outcomes
                _successful = sum(1 for m in group if m.outcome == "success")
                _success_rate = successful / len(group) if group else 0
                
                if success_rate >= self.min_confidence:
                    pattern = ExtractedPattern(
                        metadata=PatternMetadata(
                            pattern_type=PatternType.SUCCESS,
                            _source = PatternSource.MESSAGE_HISTORY,
                            confidence=success_rate,
                            support_count=len(group),
                            agents_involved=[sender, recipient],
                            _topics = list(set(m.topic for m in group if m.topic)),
                        ),
                        pattern_data={
                            "sender": sender,
                            "recipient": recipient,
                            "interaction_count": len(group),
                            "success_rate": success_rate,
                            "message_types": list(set(m.message_type for m in group)),
                        },
                        _applicability_conditions = [
                            f"sender_type={sender.split('_')[0] if '_' in sender else sender}",
                            f"recipient_type={recipient.split('_')[0] if '_' in recipient else recipient}",
                        ],
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _extract_optimization_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns for optimization opportunities."""
        _patterns = []
        
        # Group by interaction type
        interaction_groups: Dict[str, List[MessageAnalysis]] = {}
        for msg in messages:
            _key = f"{msg.sender}->{msg.recipient}"
            if key not in interaction_groups:
                interaction_groups[key] = []
            interaction_groups[key].append(msg)
        
        # Find interactions with high latency or resource usage
        for interaction_type, group in interaction_groups.items():
            if len(group) >= self.min_support:
                # Calculate average latency
                _latencies = [m.latency_ms for m in group if m.latency_ms is not None]
                if latencies:
                    _avg_latency = sum(latencies) / len(latencies)
                    # Flag high-latency interactions
                    if avg_latency > 1000:  # 1 second threshold
                        pattern = ExtractedPattern(
                            metadata=PatternMetadata(
                                pattern_type=PatternType.OPTIMIZATION,
                                _source = PatternSource.MESSAGE_HISTORY,
                                confidence=0.8,
                                _description = f"High latency detected in {interaction_type} interactions",
                            ),
                            _content = f"Average latency: {avg_latency:.2f}ms across {len(group)} interactions",
                            agents_involved=list(set([m.sender for m in group] + [m.recipient for m in group])),
                            _context = {"avg_latency_ms": avg_latency, "interaction_count": len(group)},
                        )
                        patterns.append(pattern)
        
        return patterns
    
    async def _extract_failure_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns from failed interactions."""
        _patterns = []
        
        # Group failures by type
        failure_groups: Dict[str, List[MessageAnalysis]] = {}
        for msg in messages:
            if msg.outcome == "failure":
                _key = msg.message_type
                if key not in failure_groups:
                    failure_groups[key] = []
                failure_groups[key].append(msg)
        
        # Find recurring failure patterns
        for failure_type, group in failure_groups.items():
            if len(group) >= self.min_support:
                pattern = ExtractedPattern(
                    metadata=PatternMetadata(
                        pattern_type=PatternType.FAILURE,
                        _source = PatternSource.MESSAGE_HISTORY,
                        confidence=min(len(group) / 10, 1.0),
                        support_count=len(group),
                        agents_involved=list(set(m.sender for m in group)),
                        _tags = ["failure", failure_type],
                    ),
                    pattern_data={
                        "failure_type": failure_type,
                        "occurrence_count": len(group),
                        "affected_agents": list(set(m.sender for m in group)),
                        "common_characteristics": self._find_common_characteristics(group),
                    },
                    _preconditions = self._extract_preconditions(group),
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _extract_handoff_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns from agent handoffs."""
        _patterns = []
        
        # Find handoff message sequences
        _handoffs = [m for m in messages if m.message_type == "handoff"]
        
        # Group by source-target agent pairs
        handoff_pairs: Dict[Tuple[str, str], List[MessageAnalysis]] = {}
        for handoff in handoffs:
            _key = (handoff.sender, handoff.recipient)
            if key not in handoff_pairs:
                handoff_pairs[key] = []
            handoff_pairs[key].append(handoff)
        
        # Create patterns for frequent handoffs
        for (source, target), group in handoff_pairs.items():
            if len(group) >= self.min_support:
                pattern = ExtractedPattern(
                    metadata=PatternMetadata(
                        pattern_type=PatternType.HANDOFF,
                        _source = PatternSource.MESSAGE_HISTORY,
                        confidence=min(len(group) / 5, 1.0),
                        support_count=len(group),
                        agents_involved=[source, target],
                        _topics = list(set(m.topic for m in group if m.topic)),
                    ),
                    pattern_data={
                        "source_agent": source,
                        "target_agent": target,
                        "handoff_count": len(group),
                        "avg_handoff_time": self._calculate_avg_handoff_time(group),
                    },
                    _applicability_conditions = [
                        "task_requires_specialization",
                        "source_agent_lacks_capability",
                    ],
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _extract_collaboration_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns from collaborative interactions."""
        _patterns = []
        
        # Find collective task messages
        _collaborative = [
            m for m in messages
            if m.message_type in ["collective_task", "collective_task_response"]
        ]
        
        if len(collaborative) >= self.min_support:
            # Analyze collaboration structures
            _participants = set()
            for msg in collaborative:
                participants.add(msg.sender)
                if msg.recipient != "broadcast":
                    participants.add(msg.recipient)
            
            pattern = ExtractedPattern(
                metadata=PatternMetadata(
                    pattern_type=PatternType.COLLABORATION,
                    _source = PatternSource.MESSAGE_HISTORY,
                    confidence=min(len(collaborative) / 10, 1.0),
                    support_count=len(collaborative),
                    agents_involved=list(participants),
                    _topics = list(set(m.topic for m in collaborative if m.topic)),
                ),
                pattern_data={
                    "participant_count": len(participants),
                    "collaboration_count": len(collaborative),
                    "collaboration_types": list(set(m.message_type for m in collaborative)),
                },
                _applicability_conditions = [
                    "complex_task_requires_multiple_agents",
                    "consensus_needed",
                ],
            )
            patterns.append(pattern)
        
        return patterns
    
    async def _extract_decision_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns from decision-making processes."""
        _patterns = []
        
        # Find decision-related messages
        _decisions = [
            m for m in messages
            if "decision" in m.intent or "consensus" in (m.topic or "")
        ]
        
        if len(decisions) >= self.min_support:
            pattern = ExtractedPattern(
                metadata=PatternMetadata(
                    pattern_type=PatternType.DECISION,
                    _source = PatternSource.MESSAGE_HISTORY,
                    confidence=min(len(decisions) / 5, 1.0),
                    support_count=len(decisions),
                    agents_involved=list(set(m.sender for m in decisions)),
                ),
                pattern_data={
                    "decision_count": len(decisions),
                    "decision_makers": list(set(m.sender for m in decisions)),
                    "avg_decision_time": self._calculate_avg_decision_time(decisions),
                },
            )
            patterns.append(pattern)
        
        return patterns
    
    async def _extract_communication_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns from communication flows."""
        _patterns = []
        
        # Analyze communication frequency and patterns
        comm_matrix: Dict[str, Dict[str, int]] = {}
        for msg in messages:
            if msg.sender not in comm_matrix:
                comm_matrix[msg.sender] = {}
            if msg.recipient not in comm_matrix[msg.sender]:
                comm_matrix[msg.sender][msg.recipient] = 0
            comm_matrix[msg.sender][msg.recipient] += 1
        
        # Find high-frequency communication pairs
        for sender, recipients in comm_matrix.items():
            for recipient, count in recipients.items():
                if count >= self.min_support:
                    pattern = ExtractedPattern(
                        metadata=PatternMetadata(
                            pattern_type=PatternType.COMMUNICATION,
                            _source = PatternSource.MESSAGE_HISTORY,
                            confidence=min(count / 10, 1.0),
                            support_count=count,
                            agents_involved=[sender, recipient],
                        ),
                        pattern_data={
                            "sender": sender,
                            "recipient": recipient,
                            "message_count": count,
                            "communication_frequency": count / len(messages) if messages else 0,
                        },
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _extract_error_recovery_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract patterns from error recovery scenarios."""
        _patterns = []
        
        # Find error and recovery sequences
        _errors = [m for m in messages if m.outcome == "error"]
        
        if len(errors) >= self.min_support:
            pattern = ExtractedPattern(
                metadata=PatternMetadata(
                    pattern_type=PatternType.ERROR_RECOVERY,
                    _source = PatternSource.MESSAGE_HISTORY,
                    confidence=min(len(errors) / 10, 1.0),
                    support_count=len(errors),
                    agents_involved=list(set(m.sender for m in errors)),
                    _tags = ["error", "recovery"],
                ),
                pattern_data={
                    "error_count": len(errors),
                    "error_types": list(set(m.message_type for m in errors)),
                    "affected_agents": list(set(m.sender for m in errors)),
                },
                _preconditions = self._extract_preconditions(errors),
            )
            patterns.append(pattern)
        
        return patterns
    
    async def _extract_emergent_patterns(self, messages: List[MessageAnalysis]) -> List[ExtractedPattern]:
        """Extract emergent behavior patterns."""
        _patterns = []
        
        # Look for patterns that span multiple agents
        _multi_agent_sequences = self._find_multi_agent_sequences(messages)
        
        for sequence in multi_agent_sequences:
            if len(sequence["agents"]) >= 3:  # At least 3 agents involved
                pattern = ExtractedPattern(
                    metadata=PatternMetadata(
                        pattern_type=PatternType.EMERGENT,
                        _source = PatternSource.MESSAGE_HISTORY,
                        confidence=min(len(sequence["occurrences"]) / 3, 1.0),
                        support_count=len(sequence["occurrences"]),
                        agents_involved=sequence["agents"],
                        _tags = ["emergent", "multi-agent"],
                    ),
                    pattern_data={
                        "agent_sequence": sequence["agents"],
                        "occurrence_count": len(sequence["occurrences"]),
                        "avg_sequence_length": sequence.get("avg_length", 0),
                    },
                    _applicability_conditions = [
                        "complex_task_requires_coordination",
                        "multiple_specialists_needed",
                    ],
                )
                patterns.append(pattern)
        
        return patterns
    
    def _find_multi_agent_sequences(self, messages: List[MessageAnalysis]) -> List[Dict[str, Any]]:
        """Find message sequences involving multiple agents."""
        _sequences = []
        
        # Sort messages by timestamp
        _sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        
        # Find sequences where messages chain through multiple agents
        _current_sequence = []
        _current_agents = set()
        
        for msg in sorted_messages:
            if not current_sequence:
                _current_sequence = [msg]
                _current_agents = {msg.sender, msg.recipient}
            elif msg.sender in current_agents:
                current_sequence.append(msg)
                current_agents.add(msg.recipient)
            else:
                # Sequence ended
                if len(current_agents) >= 3:
                    sequences.append({
                        "agents": list(current_agents),
                        "occurrences": [current_sequence.copy()],
                        "avg_length": len(current_sequence),
                    })
                _current_sequence = [msg]
                _current_agents = {msg.sender, msg.recipient}
        
        return sequences
    
    def _extract_preconditions(self, messages: List[MessageAnalysis]) -> List[str]:
        """Extract common preconditions from a group of messages."""
        _preconditions = []
        
        # Find common characteristics
        if messages:
            # Check for common message types
            type_counts: Dict[str, int] = {}
            for msg in messages:
                type_counts[msg.message_type] = type_counts.get(msg.message_type, 0) + 1
            
            _dominant_type = max(type_counts, key=type_counts.get)
            if type_counts[dominant_type] > len(messages) * 0.5:
                preconditions.append(f"message_type={dominant_type}")
            
            # Check for common topics
            _topics = [m.topic for m in messages if m.topic]
            if topics:
                topic_counts: Dict[str, int] = {}
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
                _dominant_topic = max(topic_counts, key=topic_counts.get)
                if topic_counts[dominant_topic] > len(topics) * 0.3:
                    preconditions.append(f"topic={dominant_topic}")
        
        return preconditions
    
    def _find_common_characteristics(self, messages: List[MessageAnalysis]) -> List[str]:
        """Find common characteristics in a group of messages."""
        _characteristics = []
        
        if messages:
            # Analyze complexity distribution
            _avg_complexity = sum(m.complexity_score for m in messages) / len(messages)
            if avg_complexity > 0.7:
                characteristics.append("high_complexity")
            elif avg_complexity < 0.3:
                characteristics.append("low_complexity")
            
            # Analyze sentiment distribution
            _avg_sentiment = sum(m.sentiment_score for m in messages) / len(messages)
            if avg_sentiment < -0.3:
                characteristics.append("negative_sentiment")
        
        return characteristics
    
    def _calculate_avg_handoff_time(self, handoffs: List[MessageAnalysis]) -> float:
        """Calculate average time between handoffs."""
        if len(handoffs) < 2:
            return 0.0
        
        _sorted_handoffs = sorted(handoffs, key=lambda m: m.timestamp)
        _deltas = []
        
        for i in range(1, len(sorted_handoffs)):
            _t1 = datetime.fromisoformat(sorted_handoffs[i - 1].timestamp)
            _t2 = datetime.fromisoformat(sorted_handoffs[i].timestamp)
            deltas.append((t2 - t1).total_seconds())
        
        return sum(deltas) / len(deltas) if deltas else 0.0
    
    def _calculate_avg_decision_time(self, _decisions: List[MessageAnalysis]) -> float:
        """Calculate average decision time."""
        # Placeholder - would need correlation with decision outcomes
        return 0.0
    
    async def _validate_pattern(self, pattern: ExtractedPattern) -> bool:
        """
        Validate a pattern before storing.
        
        Zero-trust validation:
        - Pattern ID must be valid UUID
        - Confidence must be in valid range
        - Support count must meet minimum
        - Pattern data must be non-empty
        """
        try:
            # Validate UUID
            uuid.UUID(pattern.metadata.pattern_id)
            
            # Validate confidence range
            if not 0.0 <= pattern.metadata.confidence <= 1.0:
                logger.warning(
                    "pattern_validation_failed",
                    _reason = "invalid_confidence",
                    confidence=pattern.metadata.confidence,
                )
                return False
            
            # Validate support count
            if pattern.metadata.support_count < self.min_support:
                logger.warning(
                    "pattern_validation_failed",
                    _reason = "insufficient_support",
                    _support_count = pattern.metadata.support_count,
                )
                return False
            
            # Validate pattern data non-empty
            if not pattern.pattern_data:
                logger.warning(
                    "pattern_validation_failed",
                    _reason = "empty_pattern_data",
                )
                return False
            
            logger.debug(
                "pattern_validated",
                pattern_id=pattern.metadata.pattern_id,
                pattern_type=pattern.metadata.pattern_type.value,
                confidence=pattern.metadata.confidence,
            )
            
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(
                "pattern_validation_error",
                _error = str(e),
                pattern_id=pattern.metadata.pattern_id,
            )
            return False
    
    def _update_pattern_confidence(self, pattern: ExtractedPattern, outcome: str) -> None:
        """Update pattern confidence based on outcome."""
        # Simple exponential moving average
        alpha = 0.1  # Learning rate
        
        if outcome == "success":
            _new_confidence = (1 - alpha) * pattern.metadata.confidence + alpha * 1.0
        elif outcome == "failure":
            _new_confidence = (1 - alpha) * pattern.metadata.confidence + alpha * 0.0
        else:
            _new_confidence = pattern.metadata.confidence
        
        pattern.metadata.confidence = max(0.0, min(1.0, new_confidence))
        pattern.metadata.last_observed = datetime.now(timezone.utc).isoformat()
    
    def get_validated_patterns(self, pattern_type: Optional[PatternType], min_confidence: float) -> List[ExtractedPattern]:
        """
        Get validated patterns with optional filtering.
        
        Args:
            pattern_type: Filter by pattern type (default: all)
            min_confidence: Minimum confidence threshold (default: 0.0)
            
        Returns:
            List of matching patterns
        """
        _patterns = list(self._validated_patterns.values())
        
        if pattern_type:
            _patterns = [p for p in patterns if p.metadata.pattern_type == pattern_type]
        
        _patterns = [p for p in patterns if p.metadata.confidence >= min_confidence]
        
        return sorted(
            patterns,
            _key = lambda p: p.metadata.confidence,
            _reverse = True,
        )
    
    def generate_learning_signal(self, pattern: ExtractedPattern, outcome: str) -> LearningSignal:
        """
        Generate a learning signal from a pattern outcome.
        
        Args:
            pattern: Source pattern
            outcome: Pattern outcome (success, failure, partial)
            
        Returns:
            LearningSignal for distribution
        """
        _magnitude = pattern.metadata.confidence
        
        if outcome == "failure":
            _magnitude = -magnitude
        elif outcome == "partial":
            _magnitude = magnitude * 0.5
        
        _signal = LearningSignal(
            _signal_type = "pattern_outcome",
            _magnitude = magnitude,
            _source_agent = pattern.metadata.agents_involved[0] if pattern.metadata.agents_involved else None,
            _target_agents = pattern.metadata.agents_involved,
            _context = {
                "pattern_id": pattern.metadata.pattern_id,
                "pattern_type": pattern.metadata.pattern_type.value,
                "outcome": outcome,
            },
        )
        
        self._learning_signals.append(signal)
        
        # Trim signal history
        if len(self._learning_signals) > 10000:
            self._learning_signals = self._learning_signals[-5000:]
        
        return signal


class CollectiveLearning:
    """
    Orchestrates collective learning across the agent swarm.
    
    This class coordinates pattern extraction, knowledge transformation,
    and distributed learning for emergent intelligence.
    
    Attributes:
        extractor: PatternExtractor instance
        patterns: Dictionary of extracted patterns
        learning_signals: List of generated learning signals
    """
    
    def __init__(self, min_support: int, min_confidence: float):
        """
        Initialize collective learning system.
        
        Args:
            min_support: Minimum pattern support (default: 3)
            min_confidence: Minimum pattern confidence (default: 0.6)
        """
        self.extractor = PatternExtractor(
            _min_support = min_support,
            _min_confidence = min_confidence,
        )
        self._patterns: Dict[str, ExtractedPattern] = {}
        self._learning_signals: List[LearningSignal] = []
        
        logger.info(
            "collective_learning_initialized",
            _min_support = min_support,
            _min_confidence = min_confidence,
        )
    
    async def process_message(self, message_id: str, sender: str, recipient: str, message_type: str, content: Dict[str, Any], timestamp: Optional[str]) -> MessageAnalysis:
        """
        Process a message for pattern extraction.
        
        Args:
            message_id: Unique message identifier
            sender: Sending agent ID
            recipient: Receiving agent ID or topic
            message_type: Type of message
            content: Message content
            timestamp: Message timestamp
            
        Returns:
            MessageAnalysis result
        """
        return await self.extractor.analyze_message(
            _message_id = message_id,
            _sender = sender,
            _recipient = recipient,
            _message_type = message_type,
            _content = content,
            _timestamp = timestamp,
        )
    
    async def extract_and_validate(self, time_window_hours: int) -> List[ExtractedPattern]:
        """
        Extract and validate patterns from message history.
        
        Args:
            time_window_hours: Time window for extraction (default: 24)
            
        Returns:
            List of validated patterns
        """
        _patterns = await self.extractor.extract_patterns(
            _time_window_hours = time_window_hours,
        )
        
        for pattern in patterns:
            self._patterns[pattern.metadata.pattern_id] = pattern
        
        return patterns
    
    def get_patterns(self, pattern_type: Optional[PatternType], min_confidence: float) -> List[ExtractedPattern]:
        """
        Get stored patterns with optional filtering.
        
        Args:
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching patterns
        """
        return self.extractor.get_validated_patterns(
            pattern_type=pattern_type,
            _min_confidence = min_confidence,
        )
    
    async def record_outcome(self, pattern_id: str, outcome: str, outcome_data: Dict[str, Any]) -> Optional[LearningSignal]:
        """
        Record outcome for a pattern and generate learning signal.
        
        Args:
            pattern_id: Pattern identifier
            outcome: Outcome type (success, failure, partial)
            outcome_data: Additional outcome data
            
        Returns:
            Generated learning signal or None if pattern not found
        """
        if pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]
            await self.extractor.track_outcome(pattern_id, outcome, outcome_data)
            _signal = self.extractor.generate_learning_signal(pattern, outcome)
            self._learning_signals.append(signal)
            return signal
        return None
    
    def get_learning_status(self) -> Dict[str, Any]:
        """
        Get current learning system status.
        
        Returns:
            Status dictionary with metrics
        """
        _patterns = list(self._patterns.values())
        
        return {
            "total_patterns": len(patterns),
            "patterns_by_type": {
                pt.value: len([p for p in patterns if p.metadata.pattern_type == pt])
                for pt in PatternType
            },
            "avg_confidence": (
                sum(p.metadata.confidence for p in patterns) / len(patterns)
                if patterns else 0.0
            ),
            "total_learning_signals": len(self._learning_signals),
            "message_cache_size": len(self.extractor._message_cache),
            "extraction_hooks": len(self.extractor._extraction_hooks),
        }
