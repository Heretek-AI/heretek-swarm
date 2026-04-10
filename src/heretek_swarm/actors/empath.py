"""
Empath Agent - Emotional Intelligence & Sentiment Analysis.

The Empath agent provides:
- Sentiment analysis on inputs and communications
- Agent mood tracking and emotional state monitoring
- Conflict de-escalation and emotional mediation
- Emotional context for decision-making
- Stress detection and burnout prevention

Named for the ability to understand and share the feelings of others.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import structlog
from pydantic import ValidationError
from swarms import Agent

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


_logger = structlog.get_logger("EmpathAgent")


class EmpathAgent(AgentActor):
    """
    Empath Agent - Emotional Intelligence Specialist.

    The Empath is responsible for:
    - Analyzing sentiment in all inter-agent communications
    - Tracking emotional states of agents (mood, stress, confidence)
    - Detecting conflicts and initiating de-escalation protocols
    - Providing emotional context to Triad deliberations
    - Monitoring collective emotional health of the swarm

    Emotional Intelligence Workflow:
    1. Receive message or communication
    2. Analyze sentiment (positive/negative/neutral + intensity)
    3. Update agent emotional state
    4. Detect conflicts or stress patterns
    5. Trigger interventions if needed
    6. Log emotional metrics for observability
    """

    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], _sentiment_threshold: float, _stress_threshold: float, _max_mood_history: int, _pattern_extractor: Optional[PatternExtractor], _deliberation_engine: Optional[SwarmDeliberationEngine], _access_analyzer: Optional[AccessPatternAnalyzer], _zero_trust_validator: Optional[ZeroTrustValidator], _**kwargs) -> None:
        """
        Initialize the Empath agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            sentiment_threshold: Threshold for flagging strong sentiments (0-1)
            stress_threshold: Threshold for stress alerts (0-1)
            max_mood_history: Maximum mood history entries per agent
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            _name = name,
            _description = description,
            _topics = [
                "sentiment",
                "emotions",
                "conflict-resolution",
                "agent-health",
            ],
            _capabilities = [
                "sentiment-analysis",
                "emotion-detection",
                "conflict-mediation",
                "stress-monitoring",
                "emotional-context",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        # Empath-specific state
        self.sentiment_threshold = sentiment_threshold
        self.stress_threshold = stress_threshold
        self.max_mood_history = max_mood_history

        # Agent emotional states
        self.agent_moods: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_stress_levels: Dict[str, float] = {}
        self.agent_confidence: Dict[str, float] = {}
        self.conflict_log: List[Dict[str, Any]] = []
        self.sentiment_history: List[Dict[str, Any]] = []

        # Aggregate emotional metrics
        self.collective_mood: Dict[str, float] = {
            "positive": 0.5,
            "negative": 0.1,
            "neutral": 0.4,
        }
        self.collective_stress: float = 0.0

        
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


        logger.info(f"[{self.agent_id}] Empath agent initialized")

    async def initialize(self) -> None:
        """Initialize the Empath agent."""
        # Register message handlers with Zero-Trust validation
        self.register_handler("analyze_sentiment", self._handle_analyze_sentiment)
        self.register_handler("track_emotion", self._handle_track_emotion)
        self.register_handler("detect_conflict", self._handle_detect_conflict)
        self.register_handler("get_emotional_state", self._handle_get_emotional_state)
        self.register_handler("mediate_conflict", self._handle_mediate_conflict)
        self.register_handler("get_collective_mood", self._handle_get_collective_mood)

        logger.info(f"[{self.agent_id}] Empath initialization complete")

    async def process_message(self, _message: ActorMessage) -> None:
        """
        Process incoming messages with exception handling.

        Args:
            message: Actor message to process
        """
        _handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    _exc_info = True,
                )
                self.error_count += 1
                # Send error response if reply_to is specified
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        _content = {
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        _correlation_id = message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] No handler for message type: {message.message_type}"
            )

    def _validate_message_content(self, _message_type: str, _content: Dict[str, _Any]) -> Any:
        """
        Validate message content using Pydantic models.

        Args:
            message_type: Type of message
            content: Message content to validate

        Returns:
            Validated content or None if no validator exists
        """
        try:
            return validate_message(message_type, content)
        except ValidationError as e:
            logger.warning(
                f"[{self.agent_id}] Message validation failed for {message_type}: {e}",
                extra={"validation_errors": e.errors()},
            )
            raise ValueError(f"Invalid message format: {e.errors()}")
        except KeyError:
            # Unknown message type - skip validation
            logger.debug(f"[{self.agent_id}] No validator for message type: {message_type}")
            return None

    async def _handle_analyze_sentiment(self, _message: ActorMessage) -> None:
        """
        Analyze sentiment of text content.

        Args:
            message: ActorMessage with content containing:
                - text: Text to analyze
                - source_agent: ID of the source agent
                - context: Optional context (message type, topic, etc.)

        Response:
            - sentiment: positive/negative/neutral
            - confidence: 0-1 confidence score
            - intensity: 0-1 emotional intensity
            - emotions: List of detected emotions
        """
        try:
            # Zero-Trust input validation
            _validated = self._validate_message_content("analyze_sentiment", message.content)
            content = validated.model_dump() if validated else message.content

            _text = content.get("text", "")
            _source_agent = content.get("source_agent", "unknown")
            _context = content.get("context", {})

            if not text:
                logger.warning(f"[{self.agent_id}] Empty text for sentiment analysis")
                await self._send_error_response(message, "Empty text provided")
                return

            # Perform sentiment analysis
            _sentiment_result = await self._analyze_sentiment_llm(text, source_agent, context)

            # Update agent mood history
            self._update_agent_mood(source_agent, sentiment_result)

            # Check for stress indicators
            self._check_stress_indicators(source_agent, sentiment_result)

            # Log sentiment for observability
            self._log_sentiment(source_agent, sentiment_result)

            # Send response
            await self.send(
                _topic = message.content.get("reply_to", f"actor:{source_agent}"),
                _content = {
                    "message_type": "sentiment_result",
                    "text": text[:100],  # Truncate for logging
                    **sentiment_result,
                },
                _correlation_id = message.correlation_id,
            )

            logger.debug(
                f"[{self.agent_id}] Sentiment analyzed for {source_agent}",
                extra={"sentiment": sentiment_result["sentiment"]},
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Sentiment analysis failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Sentiment analysis failed: {e}")

    async def _analyze_sentiment_llm(self, _text: str, _source_agent: str, _context: Dict[str, _Any]) -> Dict[str, Any]:
        """
        Analyze sentiment using LLM if available, otherwise use heuristic analysis.

        Args:
            text: Text to analyze
            source_agent: Source agent ID
            context: Additional context

        Returns:
            Sentiment analysis result dict
        """
        try:
            if self.swarms_agent and self.swarms_agent.llm:
                # Use LLM for sophisticated sentiment analysis
                _prompt = self._build_sentiment_prompt(text, context)
                _response = await asyncio.wait_for(
                    self.swarms_agent.llm(prompt),
                    _timeout = 60,  # P1-2: LLM timeout
                )
                return self._parse_sentiment_response(response)
            else:
                # Fallback to heuristic analysis
                return self._analyze_sentiment_heuristic(text)

        except asyncio.TimeoutError:
            logger.warning(f"[{self.agent_id}] LLM sentiment analysis timed out")
            return self._analyze_sentiment_heuristic(text)
        except Exception as e:
            logger.error(f"[{self.agent_id}] LLM sentiment analysis error: {e}")
            return self._analyze_sentiment_heuristic(text)

    def _build_sentiment_prompt(self, _text: str, _context: Dict[str, _Any]) -> str:
        """Build prompt for LLM sentiment analysis."""
        _context_str = f"Context: {context}\n" if context else ""
        return f"""
Analyze the sentiment of the following text. Consider the emotional tone, 
intensity, and any underlying emotions.

{context_str}
Text: {text}

Provide your analysis in this exact JSON format:
{{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.0-1.0,
    "intensity": 0.0-1.0,
    "emotions": ["emotion1", "emotion2"],
    "stress_indicators": true|false,
    "conflict_potential": true|false
}}
"""

    def _parse_sentiment_response(self, _response: str) -> Dict[str, Any]:
        """Parse LLM response into sentiment result."""
        import json
        import re

        try:
            # Extract JSON from response
            _json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Failed to parse LLM sentiment response: {e}")

        # Fallback to heuristic analysis
        return self._analyze_sentiment_heuristic(response)

    def _analyze_sentiment_heuristic(self, _text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using heuristic rules.

        This is a fallback when LLM is unavailable.
        """
        _text_lower = text.lower()

        # Simple positive/negative word lists
        _positive_words = {
            "good", "great", "excellent", "positive", "success", "happy",
            "confident", "sure", "certain", "agree", "support", "help",
            "thanks", "thank", "appreciate", "wonderful", "amazing",
        }
        _negative_words = {
            "bad", "terrible", "awful", "negative", "fail", "error",
            "wrong", "disagree", "reject", "problem", "issue", "stress",
            "angry", "frustrat", "worried", "concern", "unfortunately",
        }
        _stress_words = {
            "urgent", "asap", "immediately", "stress", "panic", "crisis",
            "emergency", "deadline", "overwhelm", "burnout", "pressure",
        }
        _conflict_words = {
            "disagree", "conflict", "argue", "fight", "oppose", "against",
            "wrong", "reject", "deny", "accuse", "blame",
        }

        # Count matches
        _positive_count = sum(1 for word in positive_words if word in text_lower)
        _negative_count = sum(1 for word in negative_words if word in text_lower)
        _stress_count = sum(1 for word in stress_words if word in text_lower)
        _conflict_count = sum(1 for word in conflict_words if word in text_lower)

        # Calculate sentiment
        total = positive_count + negative_count + 1  # +1 to avoid division by zero
        _positive_score = positive_count / total
        _negative_score = negative_count / total

        if positive_score > negative_score + 0.2:
            sentiment = "positive"
        elif negative_score > positive_score + 0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Detect emotions
        _emotions = []
        if "angry" in text_lower or "frustrat" in text_lower:
            emotions.append("anger")
        if "worried" in text_lower or "concern" in text_lower:
            emotions.append("anxiety")
        if "happy" in text_lower or "great" in text_lower:
            emotions.append("joy")
        if "sad" in text_lower or "disappoint" in text_lower:
            emotions.append("sadness")
        if "sure" in text_lower or "confident" in text_lower:
            emotions.append("confidence")

        return {
            "sentiment": sentiment,
            "confidence": min(0.9, 0.5 + (max(positive_count, negative_count) * 0.1)),
            "intensity": min(1.0, (positive_count + negative_count) * 0.15),
            "emotions": emotions if emotions else ["neutral"],
            "stress_indicators": stress_count > 0,
            "conflict_potential": conflict_count > 0,
        }

    def _update_agent_mood(self, _agent_id: str, _sentiment_result: Dict[str, _Any]) -> None:
        """Update agent's mood history with new sentiment data."""
        if agent_id not in self.agent_moods:
            self.agent_moods[agent_id] = []

        _mood_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sentiment": sentiment_result["sentiment"],
            "intensity": sentiment_result["intensity"],
            "emotions": sentiment_result["emotions"],
        }

        self.agent_moods[agent_id].append(mood_entry)

        # Enforce max history size (P1-3 pattern)
        if len(self.agent_moods[agent_id]) > self.max_mood_history:
            self.agent_moods[agent_id] = self.agent_moods[agent_id][-self.max_mood_history:]

    def _check_stress_indicators(self, _agent_id: str, _sentiment_result: Dict[str, _Any]) -> None:
        """Check for stress indicators and update stress levels."""
        # Update stress level
        if sentiment_result.get("stress_indicators", False):
            self.agent_stress_levels[agent_id] = min(
                1.0, self.agent_stress_levels.get(agent_id, 0.0) + 0.1
            )
        else:
            # Gradually decrease stress over time
            self.agent_stress_levels[agent_id] = max(
                0.0, self.agent_stress_levels.get(agent_id, 0.0) - 0.05
            )

        # Check for high stress alert
        if self.agent_stress_levels.get(agent_id, 0.0) > self.stress_threshold:
            logger.warning(
                f"[{self.agent_id}] High stress detected for agent {agent_id}",
                _extra = {"stress_level": self.agent_stress_levels[agent_id]},
            )
            # Could trigger alert to supervisor or steward

    def _log_sentiment(self, _agent_id: str, _sentiment_result: Dict[str, _Any]) -> None:
        """Log sentiment for observability and analysis."""
        self.sentiment_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            **sentiment_result,
        })

        # Limit history size
        if len(self.sentiment_history) > 1000:
            self.sentiment_history = self.sentiment_history[-1000:]

    async def _handle_track_emotion(self, _message: ActorMessage) -> None:
        """
        Track emotional state for an agent.

        Args:
            message: ActorMessage with content containing:
                - agent_id: Agent to track
                - emotion: Emotion to record
                - intensity: Optional intensity (0-1)
        """
        try:
            content = message.content
            agent_id = content.get("agent_id")
            _emotion = content.get("emotion")
            _intensity = content.get("intensity", 0.5)

            if not agent_id or not emotion:
                await self._send_error_response(
                    message, "Missing required fields: agent_id, emotion"
                )
                return

            self._update_agent_mood(
                agent_id,
                {
                    "sentiment": "neutral",
                    "intensity": intensity,
                    "emotions": [emotion],
                    "stress_indicators": False,
                    "conflict_potential": False,
                },
            )

            logger.debug(f"[{self.agent_id}] Emotion tracked for {agent_id}: {emotion}")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Emotion tracking failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Emotion tracking failed: {e}")

    async def _handle_detect_conflict(self, _message: ActorMessage) -> None:
        """
        Detect potential conflicts between agents.

        Args:
            message: ActorMessage with content containing:
                - agents: List of agent IDs involved
                - context: Description of the situation
        """
        try:
            content = message.content
            _agents = content.get("agents", [])
            _context = content.get("context", "")

            if len(agents) < 2:
                await self._send_error_response(
                    message, "Conflict detection requires at least 2 agents"
                )
                return

            # Analyze recent interactions between agents
            _conflict_detected = self._analyze_conflict_potential(agents)

            if conflict_detected:
                # Log conflict
                self.conflict_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agents": agents,
                    "context": context,
                    "status": "detected",
                })

                # Alert steward for mediation
                await self.send(
                    _topic = "actor:steward",
                    _content = {
                        "message_type": "conflict_alert",
                        "agents": agents,
                        "context": context,
                    },
                )

            # Send response
            await self.send(
                _topic = message.content.get("reply_to", f"actor:{agents[0]}"),
                _content = {
                    "message_type": "conflict_result",
                    "conflict_detected": conflict_detected,
                    "agents": agents,
                },
                _correlation_id = message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Conflict detection failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Conflict detection failed: {e}")

    def _analyze_conflict_potential(self, _agents: List[str]) -> bool:
        """Analyze potential for conflict between agents."""
        # Check for opposing sentiments in recent history
        _recent_sentiments = {}
        for agent_id in agents:
            moods = self.agent_moods.get(agent_id, [])[-10:]  # Last 10 entries
            if moods:
                _avg_sentiment = sum(
                    1 if m["sentiment"] == "positive" else -1 if m["sentiment"] == "negative" else 0
                    for m in moods
                ) / len(moods)
                recent_sentiments[agent_id] = avg_sentiment

        # Check for significant sentiment divergence
        if len(recent_sentiments) >= 2:
            values = list(recent_sentiments.values())
            _max_diff = max(values) - min(values)
            if max_diff > 1.5:  # Significant divergence
                return True

        # Check stress levels
        for agent_id in agents:
            if self.agent_stress_levels.get(agent_id, 0.0) > self.stress_threshold:
                return True

        return False

    async def _handle_get_emotional_state(self, _message: ActorMessage) -> None:
        """
        Get current emotional state for an agent or all agents.

        Args:
            message: ActorMessage with optional agent_id
        """
        try:
            agent_id = message.content.get("agent_id")

            if agent_id:
                # Get specific agent state
                _moods = self.agent_moods.get(agent_id, [])
                _recent_mood = moods[-1] if moods else None
                stress = self.agent_stress_levels.get(agent_id, 0.0)
                confidence = self.agent_confidence.get(agent_id, 0.5)

                _result = {
                    "agent_id": agent_id,
                    "current_mood": recent_mood,
                    "stress_level": stress,
                    "confidence": confidence,
                    "mood_history_size": len(moods),
                }
            else:
                # Get aggregate state
                _result = {
                    "collective_mood": self.collective_mood.copy(),
                    "collective_stress": self.collective_stress,
                    "agent_count": len(self.agent_moods),
                    "high_stress_agents": [
                        aid for aid, stress in self.agent_stress_levels.items()
                        if stress > self.stress_threshold
                    ],
                }

            await self.send(
                _topic = message.content.get("reply_to", "actor:*"),
                _content = {
                    "message_type": "emotional_state_result",
                    **result,
                },
                _correlation_id = message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Emotional state query failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Emotional state query failed: {e}")

    async def _handle_mediate_conflict(self, _message: ActorMessage) -> None:
        """
        Mediate conflict between agents.

        Args:
            message: ActorMessage with content containing:
                - conflict_id: ID of conflict to mediate
                - agents: List of agent IDs
                - proposed_resolution: Optional proposed solution
        """
        try:
            content = message.content
            _agents = content.get("agents", [])
            _proposed_resolution = content.get("proposed_resolution")

            if len(agents) < 2:
                await self._send_error_response(
                    message, "Mediation requires at least 2 agents"
                )
                return

            # Generate mediation suggestions using LLM if available
            _mediation_result = await self._generate_mediation(
                agents, proposed_resolution
            )

            # Send mediation suggestions to all involved agents
            for agent_id in agents:
                await self.send(
                    _topic = f"actor:{agent_id}",
                    _content = {
                        "message_type": "mediation_suggestion",
                        "agents": agents,
                        **mediation_result,
                    },
                )

            # Log mediation attempt
            self.conflict_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agents": agents,
                "status": "mediated",
                "result": mediation_result,
            })

            await self.send(
                _topic = message.content.get("reply_to"),
                _content = {
                    "message_type": "mediation_result",
                    "agents": agents,
                    **mediation_result,
                },
                _correlation_id = message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Conflict mediation failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Mediation failed: {e}")

    async def _generate_mediation(self, _agents: List[str], _proposed_resolution: Optional[str]) -> Dict[str, Any]:
        """Generate mediation suggestions."""
        try:
            if self.swarms_agent and self.swarms_agent.llm:
                _prompt = f"""
Generate a fair mediation suggestion for a conflict between these agents: {agents}.

{"Proposed resolution: " + proposed_resolution if proposed_resolution else ""}

Provide a balanced resolution that considers all perspectives.
Return as JSON: {{"resolution": "...", "reasoning": "..."}}
"""
                _response = await asyncio.wait_for(
                    self.swarms_agent.llm(prompt),
                    _timeout = 60,
                )
                import json
                import re
                _json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"[{self.agent_id}] LLM mediation failed: {e}")

        # Fallback mediation
        return {
            "resolution": "Consider taking a break and revisiting this discussion later.",
            "reasoning": "High stress or conflicting sentiments detected. Cooling-off period recommended.",
        }

    async def _handle_get_collective_mood(self, _message: ActorMessage) -> None:
        """
        Get the collective mood of the swarm.

        Args:
            message: ActorMessage
        """
        try:
            # Calculate collective metrics
            self._update_collective_mood()

            await self.send(
                _topic = message.content.get("reply_to"),
                _content = {
                    "message_type": "collective_mood_result",
                    "collective_mood": self.collective_mood,
                    "collective_stress": self.collective_stress,
                    "total_agents": len(self.agent_moods),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                _correlation_id = message.correlation_id,
            )

        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Collective mood query failed: {e}", exc_info=True
            )
            await self._send_error_response(message, f"Collective mood query failed: {e}")

    def _update_collective_mood(self) -> None:
        """Update aggregate collective mood metrics."""
        if not self.agent_moods:
            return

        # Average sentiment across all agents
        _all_moods = []
        for moods in self.agent_moods.values():
            all_moods.extend(moods[-5:])  # Last 5 entries per agent

        if all_moods:
            _positive = sum(1 for m in all_moods if m["sentiment"] == "positive")
            _negative = sum(1 for m in all_moods if m["sentiment"] == "negative")
            _neutral = sum(1 for m in all_moods if m["sentiment"] == "neutral")
            _total = len(all_moods)

            self.collective_mood = {
                "positive": positive / total,
                "negative": negative / total,
                "neutral": neutral / total,
            }

        # Average stress
        if self.agent_stress_levels:
            self.collective_stress = sum(
                self.agent_stress_levels.values()
            ) / len(self.agent_stress_levels)


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, _item_id: str, _item_type: str, _outcome: str, _content: Dict[str, _Any]) -> None:
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
                message_type=f"{item_type}_completion",
                content=content,
                _timestamp = datetime.now(timezone.utc).isoformat(),
            )
            
            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, _pattern_types: Optional[List[PatternType]]) -> List[Dict[str, Any]]:
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

    async def _initiate_deliberation(self, _item_id: str, _proposal: str, _participating_agents: List[str], _domain: str) -> Optional[str]:
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

    async def _submit_deliberation_position(self, _item_id: str, _agent_id: str, _position: Position, _confidence: float, _argument: str) -> bool:
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

    async def _finalize_deliberation(self, _item_id: str) -> Optional[Any]:
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

    def _track_memory_access(self, _item_id: str, _item_type: str, _access_type: str) -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return
        
        _memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            _memory_id = memory_id,
            _access_type = access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, _item_id: str, _item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD
        
        _memory_id = f"{item_type}_{item_id}"
        _profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, _agent_id: str, _item_type: str) -> List[str]:
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


    async def _send_error_response(self, _message: ActorMessage, _error: str) -> None:
        """Send error response."""
        if message.content.get("reply_to"):
            await self.send(
                _topic = message.content["reply_to"],
                _content = {
                    "message_type": "error_response",
                    "error": error,
                    "original_message_type": message.message_type,
                },
                _correlation_id = message.correlation_id,
            )
