"""
Habit-Forge Agent - Behavior Architecture & Pattern Optimization.

The Habit-Forge agent provides:
- Habit formation and modification protocols
- Behavioral pattern analysis and optimization
- Routine design and reinforcement strategies
- Counterproductive pattern identification
- Progress tracking for habit establishment

Named for the ability to forge and shape behavioral patterns into productive,
sustainable habits that drive collective excellence.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from pydantic import ValidationError, Field
import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.actors.validation import validate_message, MessageContent

logger = structlog.get_logger("HabitForgeAgent")


class HabitStage(str, Enum):
    """Stages of habit formation."""
    AWARENESS = "awareness"
    INITIATION = "initiation"
    ACQUISITION = "acquisition"
    CONSOLIDATION = "consolidation"
    AUTOMATICITY = "automaticity"
    MAINTENANCE = "maintenance"


class PatternType(str, Enum):
    """Types of behavioral patterns."""
    PRODUCTIVE = "productive"
    COUNTERPRODUCTIVE = "counterproductive"
    NEUTRAL = "neutral"
    COMPOUND = "compound"
    TRIGGERED = "triggered"


class ReinforcementType(str, Enum):
    """Types of reinforcement strategies."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    SOCIAL = "social"
    MATERIAL = "material"
    INTRINSIC = "intrinsic"


class Habit:
    """Represents a tracked habit."""
    
    def __init__(
        self,
        habit_id: str,
        name: str,
        description: str,
        trigger: str,
        routine: str,
        reward: str,
        target_frequency: str = "daily",
        stage: HabitStage = HabitStage.INITIATION,
    ) -> None:
        self.habit_id = habit_id
        self.name = name
        self.description = description
        self.trigger = trigger
        self.routine = routine
        self.reward = reward
        self.target_frequency = target_frequency
        self.stage = stage
        self.created_at = datetime.now(timezone.utc)
        
        # Tracking metrics
        self.completions: List[Dict[str, Any]] = []
        self.adherence_rate: float = 0.0
        self.streak_current: int = 0
        self.streak_longest: int = 0
        self.last_completion: Optional[datetime] = None
    
    def record_completion(self, context: Optional[str] = None) -> None:
        """Record a habit completion."""
        completion_time = datetime.now(timezone.utc)
        self.completions.append({
            "timestamp": completion_time.isoformat(),
            "context": context,
        })
        self.last_completion = completion_time
        
        # Update streak
        if self.streak_current == 0 or (
            self.last_completion and 
            completion_time - self.last_completion < timedelta(days=2)
        ):
            self.streak_current += 1
        else:
            self.streak_current = 1
        
        if self.streak_current > self.streak_longest:
            self.streak_longest = self.streak_current
        
        # Calculate adherence rate
        self._calculate_adherence()
    
    def _calculate_adherence(self) -> None:
        """Calculate adherence rate based on completions."""
        if not self.completions:
            self.adherence_rate = 0.0
            return
        
        # Calculate expected completions based on frequency
        days_active = (datetime.now(timezone.utc) - self.created_at).days
        if days_active == 0:
            days_active = 1
        
        if self.target_frequency == "daily":
            expected = days_active
        elif self.target_frequency == "weekly":
            expected = days_active / 7
        else:
            expected = days_active
        
        self.adherence_rate = min(len(self.completions) / expected, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert habit to dictionary."""
        return {
            "habit_id": self.habit_id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "routine": self.routine,
            "reward": self.reward,
            "target_frequency": self.target_frequency,
            "stage": self.stage.value,
            "adherence_rate": self.adherence_rate,
            "streak_current": self.streak_current,
            "streak_longest": self.streak_longest,
            "completions_count": len(self.completions),
            "created_at": self.created_at.isoformat(),
            "last_completion": self.last_completion.isoformat() if self.last_completion else None,
        }


class BehavioralPattern:
    """Represents a detected behavioral pattern."""
    
    def __init__(
        self,
        pattern_id: str,
        pattern_type: PatternType,
        description: str,
        triggers: List[str],
        behaviors: List[str],
        outcomes: List[str],
        frequency: str = "unknown",
        impact_score: float = 0.0,
    ) -> None:
        self.pattern_id = pattern_id
        self.pattern_type = pattern_type
        self.description = description
        self.triggers = triggers
        self.behaviors = behaviors
        self.outcomes = outcomes
        self.frequency = frequency
        self.impact_score = impact_score
        self.detected_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "triggers": self.triggers,
            "behaviors": self.behaviors,
            "outcomes": self.outcomes,
            "frequency": self.frequency,
            "impact_score": self.impact_score,
            "detected_at": self.detected_at.isoformat(),
        }


class HabitForgeAgent(AgentActor):
    """
    Habit-Forge Agent - Behavior Architecture Specialist.
    
    The Habit-Forge is responsible for:
    - Analyzing collective behavioral patterns for improvement opportunities
    - Designing effective habit formation protocols
    - Tracking and measuring habit establishment progress
    - Identifying and modifying counterproductive patterns
    - Providing reinforcement strategies for sustainable change
    
    Behavior Optimization Workflow:
    1. Observe behavioral patterns and routines
    2. Identify productive and counterproductive patterns
    3. Design habit protocols with triggers and rewards
    4. Track adherence and progress
    5. Adjust protocols based on data
    6. Reinforce successful habits
    """
    
    def __init__(
        self,
        agent_id: str = "habit-forge",
        name: str = "Habit-Forge",
        description: str = "Behavior architecture and habit optimization specialist",
        swarms_agent: Optional[Agent] = None,
        max_habits: int = 50,
        max_patterns: int = 100,
        min_adherence_threshold: float = 0.7,
        **kwargs,
    ) -> None:
        """
        Initialize the Habit-Forge agent.
        
        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            max_habits: Maximum habits to track
            max_patterns: Maximum patterns to store
            min_adherence_threshold: Minimum adherence rate for habit success
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=[
                "habits",
                "behaviors",
                "routines",
                "patterns",
                "reinforcement",
            ],
            capabilities=[
                "habit-formation",
                "pattern-analysis",
                "behavior-optimization",
                "progress-tracking",
                "reinforcement-design",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )
        
        # Habit-Forge specific state
        self.max_habits = max_habits
        self.max_patterns = max_patterns
        self.min_adherence_threshold = min_adherence_threshold
        
        # Habit and pattern tracking
        self.active_habits: Dict[str, Habit] = {}
        self.completed_habits: Dict[str, Habit] = {}
        self.detected_patterns: Dict[str, BehavioralPattern] = {}
        self.reinforcement_strategies: Dict[str, List[Dict[str, Any]]] = {}
        
        # Collective behavior metrics
        self.collective_behavior_score: float = 0.5
        self.pattern_evolution: List[Dict[str, Any]] = []
        
        logger.info(f"[{self.agent_id}] Habit-Forge agent initialized")
    
    async def initialize(self) -> None:
        """Initialize the Habit-Forge agent."""
        # Register message handlers with Zero-Trust validation
        self.register_handler("create_habit", self._handle_create_habit)
        self.register_handler("track_habit", self._handle_track_habit)
        self.register_handler("analyze_patterns", self._handle_analyze_patterns)
        self.register_handler("get_habit_progress", self._handle_get_habit_progress)
        self.register_handler("modify_pattern", self._handle_modify_pattern)
        self.register_handler("get_behavior_report", self._handle_get_behavior_report)
        self.register_handler("design_reinforcement", self._handle_design_reinforcement)
        
        logger.info(f"[{self.agent_id}] Habit-Forge initialization complete")
    
    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming messages with exception handling.
        
        Args:
            message: Actor message to process
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    exc_info=True,
                )
                self.error_count += 1
                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        sender_id=self.agent_id,
                    )
        else:
            logger.warning(f"[{self.agent_id}] Unknown message type: {message.message_type}")
    
    def _validate_habit_request(self, content: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate habit creation/modification request.
        
        Args:
            content: Message content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["name", "trigger", "routine", "reward"]
        for field in required_fields:
            if field not in content:
                return False, f"Missing required field: {field}"
            if not isinstance(content[field], str):
                return False, f"Field '{field}' must be a string"
            if len(content[field]) > 5000:
                return False, f"Field '{field}' exceeds maximum length"
        return True, ""
    
    async def _handle_create_habit(self, message: ActorMessage) -> None:
        """
        Create a new habit formation protocol.
        
        Args:
            message: Actor message with habit details
        """
        try:
            # Validate content
            is_valid, error = self._validate_habit_request(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid habit creation request: {error}")
                return
            
            # Check habit limit
            if len(self.active_habits) >= self.max_habits:
                logger.error(f"[{self.agent_id}] Maximum habit limit reached ({self.max_habits})")
                return
            
            habit_id = message.content.get(
                "habit_id", 
                f"habit_{datetime.now(timezone.utc).timestamp()}"
            )
            
            # Create habit
            habit = Habit(
                habit_id=habit_id,
                name=message.content["name"],
                description=message.content.get("description", ""),
                trigger=message.content["trigger"],
                routine=message.content["routine"],
                reward=message.content["reward"],
                target_frequency=message.content.get("target_frequency", "daily"),
                stage=HabitStage(message.content.get("stage", "initiation")),
            )
            
            # Store habit
            self.active_habits[habit_id] = habit
            
            logger.info(f"[{self.agent_id}] Created habit: {habit.name} ({habit_id})")
            
            # Send response
            response = {
                "message_type": "habit_created",
                "habit_id": habit_id,
                "habit": habit.to_dict(),
                "message": f"Habit '{habit.name}' created successfully",
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error creating habit: {e}", exc_info=True)
    
    async def _handle_track_habit(self, message: ActorMessage) -> None:
        """
        Track a habit completion or progress.
        
        Args:
            message: Actor message with habit tracking data
        """
        try:
            habit_id = message.content.get("habit_id")
            if not habit_id:
                logger.error(f"[{self.agent_id}] No habit_id provided for tracking")
                return
            
            if habit_id not in self.active_habits:
                logger.error(f"[{self.agent_id}] Habit not found: {habit_id}")
                return
            
            habit = self.active_habits[habit_id]
            action = message.content.get("action", "complete")
            
            if action == "complete":
                context = message.content.get("context", "")
                habit.record_completion(context)
                
                logger.info(
                    f"[{self.agent_id}] Recorded completion for habit: {habit.name} "
                    f"(streak: {habit.streak_current}, adherence: {habit.adherence_rate:.1%})"
                )
                
                # Check for stage progression
                await self._check_stage_progression(habit)
            
            response = {
                "message_type": "habit_tracked",
                "habit_id": habit_id,
                "habit_name": habit.name,
                "action": action,
                "current_streak": habit.streak_current,
                "longest_streak": habit.streak_longest,
                "adherence_rate": habit.adherence_rate,
                "stage": habit.stage.value,
                "total_completions": len(habit.completions),
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error tracking habit: {e}", exc_info=True)
    
    async def _check_stage_progression(self, habit: Habit) -> None:
        """
        Check and update habit stage based on adherence.
        
        Args:
            habit: Habit to check for progression
        """
        old_stage = habit.stage
        
        # Stage progression logic based on adherence rate
        if habit.adherence_rate >= 0.9 and habit.streak_current >= 60:
            habit.stage = HabitStage.MAINTENANCE
        elif habit.adherence_rate >= 0.8 and habit.streak_current >= 30:
            habit.stage = HabitStage.AUTOMATICITY
        elif habit.adherence_rate >= 0.7 and habit.streak_current >= 21:
            habit.stage = HabitStage.CONSOLIDATION
        elif habit.adherence_rate >= 0.5 and habit.streak_current >= 7:
            habit.stage = HabitStage.ACQUISITION
        elif habit.adherence_rate >= 0.3:
            habit.stage = HabitStage.INITIATION
        else:
            habit.stage = HabitStage.AWARENESS
        
        # Log stage change
        if habit.stage != old_stage:
            logger.info(
                f"[{self.agent_id}] Habit '{habit.name}' progressed from "
                f"{old_stage.value} to {habit.stage.value}"
            )
            
            # Check for graduation to completed habits
            if habit.stage == HabitStage.MAINTENANCE:
                self.completed_habits[habit.habit_id] = habit
                del self.active_habits[habit.habit_id]
                logger.info(f"[{self.agent_id}] Habit '{habit.name}' graduated to completed habits")
    
    async def _handle_analyze_patterns(self, message: ActorMessage) -> None:
        """
        Analyze behavioral patterns for optimization opportunities.
        
        Args:
            message: Actor message with behavior data
        """
        try:
            behavior_data = message.content.get("behavior_data", [])
            context = message.content.get("context", "")
            
            if not behavior_data:
                logger.warning(f"[{self.agent_id}] No behavior data provided for analysis")
                return
            
            logger.info(f"[{self.agent_id}] Analyzing behavioral patterns")
            
            # Analyze patterns
            patterns = await self._analyze_behavior_patterns(behavior_data, context)
            
            # Store patterns
            for pattern in patterns:
                if len(self.detected_patterns) >= self.max_patterns:
                    # Remove oldest pattern
                    oldest_id = list(self.detected_patterns.keys())[0]
                    del self.detected_patterns[oldest_id]
                self.detected_patterns[pattern.pattern_id] = pattern
            
            # Send response
            response = {
                "message_type": "pattern_analysis_response",
                "patterns_detected": len(patterns),
                "patterns": [p.to_dict() for p in patterns],
                "recommendations": await self._generate_pattern_recommendations(patterns),
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )
            
            logger.info(f"[{self.agent_id}] Detected {len(patterns)} behavioral patterns")
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error analyzing patterns: {e}", exc_info=True)
    
    async def _analyze_behavior_patterns(
        self,
        behavior_data: List[Dict[str, Any]],
        context: str,
    ) -> List[BehavioralPattern]:
        """
        Analyze behavior data to detect patterns.
        
        Args:
            behavior_data: List of behavior observations
            context: Context for the behavior
            
        Returns:
            List of detected behavioral patterns
        """
        patterns = []
        
        # Build prompt for LLM analysis
        prompt = f"""Analyze the following behavioral data for patterns:

CONTEXT: {context[:2000]}

BEHAVIOR DATA:
{str(behavior_data)[:5000]}

Identify behavioral patterns including:
1. Productive patterns (behaviors that lead to positive outcomes)
2. Counterproductive patterns (behaviors that hinder goals)
3. Trigger-behavior-outcome loops
4. Frequency and impact of each pattern

For each pattern, provide:
- Pattern type (productive/counterproductive/neutral)
- Description
- Triggers that initiate the pattern
- Specific behaviors in the pattern
- Outcomes resulting from the pattern
- Frequency (daily/weekly/occasional)
- Impact score (0-1)

Respond in JSON format:
[
    {{
        "pattern_type": "...",
        "description": "...",
        "triggers": ["...", "..."],
        "behaviors": ["...", "..."],
        "outcomes": ["...", "..."],
        "frequency": "...",
        "impact_score": 0.0
    }}
]"""
        
        try:
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )
                
                import json
                try:
                    start_idx = result.find("[")
                    end_idx = result.rfind("]") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        data = json.loads(result[start_idx:end_idx])
                        
                        for i, item in enumerate(data):
                            pattern = BehavioralPattern(
                                pattern_id=f"pattern_{datetime.now(timezone.utc).timestamp()}_{i}",
                                pattern_type=PatternType(item.get("pattern_type", "neutral")),
                                description=item.get("description", ""),
                                triggers=item.get("triggers", []),
                                behaviors=item.get("behaviors", []),
                                outcomes=item.get("outcomes", []),
                                frequency=item.get("frequency", "unknown"),
                                impact_score=float(item.get("impact_score", 0.5)),
                            )
                            patterns.append(pattern)
                except Exception:
                    pass
            
            # Fallback: Heuristic pattern detection
            if not patterns:
                patterns.extend(self._heuristic_pattern_detection(behavior_data))
            
        except Exception as e:
            logger.warning(f"[{self.agent_id}] LLM pattern analysis failed: {e}")
            patterns.extend(self._heuristic_pattern_detection(behavior_data))
        
        return patterns
    
    def _heuristic_pattern_detection(
        self,
        behavior_data: List[Dict[str, Any]],
    ) -> List[BehavioralPattern]:
        """
        Detect patterns using heuristics when LLM unavailable.
        
        Args:
            behavior_data: List of behavior observations
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Simple frequency-based pattern detection
        behavior_counts: Dict[str, int] = {}
        for behavior in behavior_data:
            action = behavior.get("action", "unknown")
            behavior_counts[action] = behavior_counts.get(action, 0) + 1
        
        # Create patterns for frequent behaviors
        for action, count in behavior_counts.items():
            if count >= 3:  # Minimum occurrences for pattern
                pattern_type = PatternType.PRODUCTIVE if "complete" in action.lower() else PatternType.NEUTRAL
                patterns.append(BehavioralPattern(
                    pattern_id=f"pattern_{action}_{datetime.now(timezone.utc).timestamp()}",
                    pattern_type=pattern_type,
                    description=f"Repeated behavior: {action}",
                    triggers=["Context-dependent"],
                    behaviors=[action],
                    outcomes=[f"Performed {count} times"],
                    frequency="recurring",
                    impact_score=min(count / 10, 1.0),
                ))
        
        return patterns
    
    async def _generate_pattern_recommendations(
        self,
        patterns: List[BehavioralPattern],
    ) -> List[str]:
        """
        Generate recommendations based on detected patterns.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            List of recommendations
        """
        counterproductive = [p for p in patterns if p.pattern_type == PatternType.COUNTERPRODUCTIVE]
        productive = [p for p in patterns if p.pattern_type == PatternType.PRODUCTIVE]
        
        recommendations = []
        
        # Recommendations for counterproductive patterns
        for pattern in counterproductive:
            recommendations.append(
                f"Address counterproductive pattern '{pattern.description}': "
                f"Consider modifying trigger '{pattern.triggers[0] if pattern.triggers else 'unknown'}' "
                f"or replacing behavior with alternative."
            )
        
        # Reinforcement for productive patterns
        for pattern in productive:
            recommendations.append(
                f"Reinforce productive pattern '{pattern.description}': "
                f"Ensure consistent rewards and consider adding social accountability."
            )
        
        if not recommendations:
            recommendations.append(
                "Continue monitoring behavioral patterns. No immediate interventions required."
            )
        
        return recommendations
    
    async def _handle_get_habit_progress(self, message: ActorMessage) -> None:
        """
        Get progress report for specific habit or all habits.
        
        Args:
            message: Actor message with habit query
        """
        try:
            habit_id = message.content.get("habit_id", None)
            
            if habit_id:
                # Get specific habit
                if habit_id in self.active_habits:
                    habit = self.active_habits[habit_id]
                elif habit_id in self.completed_habits:
                    habit = self.completed_habits[habit_id]
                else:
                    logger.error(f"[{self.agent_id}] Habit not found: {habit_id}")
                    return
                
                response = {
                    "message_type": "habit_progress_response",
                    "habit_id": habit_id,
                    "habit": habit.to_dict(),
                    "status": "active" if habit_id in self.active_habits else "completed",
                }
            else:
                # Get all habits summary
                active_summary = {
                    h.habit_id: {
                        "name": h.name,
                        "stage": h.stage.value,
                        "adherence": h.adherence_rate,
                        "streak": h.streak_current,
                    }
                    for h in self.active_habits.values()
                }
                
                response = {
                    "message_type": "habit_progress_response",
                    "active_habits_count": len(self.active_habits),
                    "completed_habits_count": len(self.completed_habits),
                    "active_habits": active_summary,
                    "collective_adherence": self._calculate_collective_adherence(),
                }
            
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error getting habit progress: {e}", exc_info=True)
    
    def _calculate_collective_adherence(self) -> float:
        """Calculate collective adherence rate across all active habits."""
        if not self.active_habits:
            return 0.0
        
        total_adherence = sum(h.adherence_rate for h in self.active_habits.values())
        return total_adherence / len(self.active_habits)
    
    async def _handle_modify_pattern(self, message: ActorMessage) -> None:
        """
        Modify a detected behavioral pattern.
        
        Args:
            message: Actor message with pattern modification details
        """
        try:
            pattern_id = message.content.get("pattern_id")
            if not pattern_id:
                logger.error(f"[{self.agent_id}] No pattern_id provided")
                return
            
            if pattern_id not in self.detected_patterns:
                logger.error(f"[{self.agent_id}] Pattern not found: {pattern_id}")
                return
            
            pattern = self.detected_patterns[pattern_id]
            modification_type = message.content.get("modification_type", "replace")
            
            logger.info(f"[{self.agent_id}] Modifying pattern: {pattern.pattern_id}")
            
            # Generate modification plan
            modification_plan = await self._generate_modification_plan(
                pattern, modification_type, message.content
            )
            
            response = {
                "message_type": "pattern_modification_response",
                "pattern_id": pattern_id,
                "original_pattern": pattern.to_dict(),
                "modification_type": modification_type,
                "modification_plan": modification_plan,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error modifying pattern: {e}", exc_info=True)
    
    async def _generate_modification_plan(
        self,
        pattern: BehavioralPattern,
        modification_type: str,
        request_content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a plan for modifying a behavioral pattern.
        
        Args:
            pattern: Pattern to modify
            modification_type: Type of modification
            request_content: Original request content
            
        Returns:
            Modification plan dictionary
        """
        prompt = f"""Generate a behavior modification plan:

CURRENT PATTERN:
- Type: {pattern.pattern_type.value}
- Description: {pattern.description}
- Triggers: {pattern.triggers}
- Behaviors: {pattern.behaviors}
- Outcomes: {pattern.outcomes}

MODIFICATION TYPE: {modification_type}

Generate a step-by-step modification plan including:
1. Identification of trigger points for intervention
2. Replacement behaviors to implement
3. Reinforcement strategies
4. Timeline for change
5. Success metrics

Respond in JSON:
{{
    "trigger_interventions": ["...", "..."],
    "replacement_behaviors": ["...", "..."],
    "reinforcement_strategies": ["...", "..."],
    "timeline_days": 0,
    "success_metrics": ["...", "..."]
}}"""
        
        try:
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )
                
                import json
                try:
                    start_idx = result.find("{")
                    end_idx = result.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        return json.loads(result[start_idx:end_idx])
                except Exception:
                    pass
            
            # Fallback
            return {
                "trigger_interventions": ["Identify and awareness of trigger"],
                "replacement_behaviors": ["Implement alternative response"],
                "reinforcement_strategies": ["Apply positive reinforcement"],
                "timeline_days": 21,
                "success_metrics": ["Consistent execution of replacement behavior"],
                "note": "LLM unavailable - basic plan provided",
            }
            
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Modification plan generation failed: {e}")
            return {
                "error": str(e),
                "note": "Plan generation failed",
            }
    
    async def _handle_get_behavior_report(self, message: ActorMessage) -> None:
        """
        Get comprehensive behavior report.
        
        Args:
            message: Actor message
        """
        try:
            report_type = message.content.get("report_type", "summary")
            
            if report_type == "summary":
                report = {
                    "report_type": "summary",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "active_habits_count": len(self.active_habits),
                    "completed_habits_count": len(self.completed_habits),
                    "detected_patterns_count": len(self.detected_patterns),
                    "collective_adherence": self._calculate_collective_adherence(),
                    "collective_behavior_score": self.collective_behavior_score,
                }
            elif report_type == "detailed":
                report = {
                    "report_type": "detailed",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "active_habits": [h.to_dict() for h in self.active_habits.values()],
                    "completed_habits": [h.to_dict() for h in self.completed_habits.values()],
                    "detected_patterns": [p.to_dict() for p in self.detected_patterns.values()],
                }
            else:
                report = {"error": f"Unknown report type: {report_type}"}
            
            response = {
                "message_type": "behavior_report_response",
                "report": report,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error generating behavior report: {e}", exc_info=True)
    
    async def _handle_design_reinforcement(self, message: ActorMessage) -> None:
        """
        Design reinforcement strategy for a habit or behavior.
        
        Args:
            message: Actor message with reinforcement request
        """
        try:
            habit_id = message.content.get("habit_id")
            behavior = message.content.get("behavior", "")
            
            if not habit_id and not behavior:
                logger.error(f"[{self.agent_id}] No habit_id or behavior provided")
                return
            
            logger.info(f"[{self.agent_id}] Designing reinforcement strategy")
            
            # Design reinforcement
            reinforcement = await self._design_reinforcement_strategy(
                habit_id, behavior
            )
            
            # Store strategy
            strategy_id = habit_id or f"behavior_{datetime.now(timezone.utc).timestamp()}"
            self.reinforcement_strategies[strategy_id] = reinforcement
            
            response = {
                "message_type": "reinforcement_design_response",
                "strategy_id": strategy_id,
                "reinforcement_strategies": reinforcement,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error designing reinforcement: {e}", exc_info=True)
    
    async def _design_reinforcement_strategy(
        self,
        habit_id: Optional[str],
        behavior: str,
    ) -> Dict[str, Any]:
        """
        Design reinforcement strategy for habit or behavior.
        
        Args:
            habit_id: Optional habit identifier
            behavior: Behavior description
            
        Returns:
            Reinforcement strategy dictionary
        """
        habit = self.active_habits.get(habit_id) if habit_id else None
        
        prompt = f"""Design a reinforcement strategy for behavior change:

HABIT: {habit.name if habit else 'N/A'}
TRIGGER: {habit.trigger if habit else 'N/A'}
ROUTINE: {habit.routine if habit else 'N/A'}
REWARD: {habit.reward if habit else 'N/A'}
ADHERENCE: {habit.adherence_rate if habit else 'N/A'}

BEHAVIOR TO REINFORCE: {behavior}

Design a comprehensive reinforcement strategy including:
1. Positive reinforcement techniques
2. Negative reinforcement (removing aversive stimuli)
3. Social reinforcement options
4. Intrinsic motivation enhancers
5. Implementation schedule

Respond in JSON:
{{
    "positive_reinforcement": ["...", "..."],
    "negative_reinforcement": ["...", "..."],
    "social_reinforcement": ["...", "..."],
    "intrinsic_motivation": ["...", "..."],
    "schedule": "..."
}}"""
        
        try:
            if self.swarms_agent:
                result = await self.run_with_llm(
                    prompt=prompt,
                    timeout=60,
                )
                
                import json
                try:
                    start_idx = result.find("{")
                    end_idx = result.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        return json.loads(result[start_idx:end_idx])
                except Exception:
                    pass
            
            # Fallback
            return {
                "positive_reinforcement": ["Celebrate small wins", "Track progress visibly"],
                "negative_reinforcement": ["Remove friction from desired behavior"],
                "social_reinforcement": ["Share progress with accountability partner"],
                "intrinsic_motivation": ["Connect behavior to core values"],
                "schedule": "Daily reinforcement for first 21 days",
                "note": "LLM unavailable - basic strategy provided",
            }
            
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Reinforcement design failed: {e}")
            return {
                "error": str(e),
                "note": "Reinforcement design failed",
            }
