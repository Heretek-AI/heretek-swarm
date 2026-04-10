"""
Agent Society - Collective Intelligence Model

Implements agent society with hierarchical coordination, emergent behavior detection,
and collective memory. Inspired by CAMEL agent society patterns and swarm intelligence.

Features:
- Hierarchical agent coordination
- Collective decision-making
- Emergent behavior detection
- Shared collective memory
- Swarm optimization algorithms
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import structlog

_logger = structlog.get_logger(__name__)

# Import swarm intelligence patterns for integration
try:
    from .swarm_intelligence import (
        SwarmIntelligenceEngine,
        SwarmPattern,
        SwarmDecision,
        Particle,
        PheromoneTrail,
        BeeAgent,
        FlockingAgent,
        StigmergicTrace,
    )
    SWARM_INTELLIGENCE_AVAILABLE = True
except ImportError:
    SWARM_INTELLIGENCE_AVAILABLE = False
    logger.warning("Swarm intelligence module not available")


class ContributionCache:
    """
    Cache for agent contributions with TTL support.
    
    Prevents duplicate requests and improves performance.
    """
    
    def __init__(self, _ttl_seconds: int):
        """
        Initialize contribution cache.
        
        Args:
            ttl_seconds: Time to live for cached entries (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds
    
    def _generate_key(self, _agent_id: str, _task_id: str) -> str:
        """Generate cache key from agent and task IDs."""
        return f"{agent_id}:{task_id}"
    
    def get(self, _agent_id: str, _task_id: str) -> Optional["AgentContribution"]:
        """
        Get cached contribution if not expired.
        
        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            
        Returns:
            Cached contribution or None if expired/not found
        """
        key = self._generate_key(agent_id, task_id)
        if key in self._cache:
            _entry = self._cache[key]
            if datetime.fromisoformat(entry["expires_at"]) > datetime.now(timezone.utc):
                return entry["contribution"]
            else:
                # Expired, remove from cache
                del self._cache[key]
        return None
    
    def set(self, _agent_id: str, _task_id: str, _contribution: "AgentContribution") -> None:
        """
        Cache a contribution.
        
        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            contribution: Contribution to cache
        """
        key = self._generate_key(agent_id, task_id)
        self._cache[key] = {
            "contribution": contribution,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(seconds=self._ttl_seconds)
            ).isoformat(),
        }
        logger.debug("contribution_cacheded", agent_id=agent_id, task_id=task_id)
    
    def invalidate(self, _agent_id: str, _task_id: str) -> None:
        """Invalidate a cached contribution."""
        key = self._generate_key(agent_id, task_id)
        if key in self._cache:
            del self._cache[key]
            logger.debug("contribution_invalidated", agent_id=agent_id, task_id=task_id)
    
    def clear(self) -> None:
        """Clear all cached contributions."""
        self._cache.clear()
        logger.info("contribution_cache_cleared")


class SocietyRole(str, Enum):
    """Roles within agent society."""
    
    LEADERSHIP = "leadership"
    ANALYSIS = "analysis"
    SUPPORT = "support"
    EXPLORATION = "exploration"
    DEVELOPMENT = "development"
    SAFETY = "safety"
    COORDINATION = "coordination"


class CollectiveTaskType(str, Enum):
    """Types of collective tasks."""
    
    DELIBERATION = "deliberation"
    CONSENSUS = "consensus"
    COORDINATION = "coordination"
    OPTIMIZATION = "optimization"
    LEARNING = "learning"
    MONITORING = "monitoring"


@dataclass
class CollectiveTask:
    """A task requiring collective agent coordination."""
    
    id: str
    type: CollectiveTaskType
    description: str
    input_data: Dict[str, Any]
    priority: float = 0.5
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    deadline: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


@dataclass
class CollectiveResult:
    """Result of collective task execution."""
    
    task_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    consensus_score: float = 0.0
    emergent_behavior: Optional[str] = None


@dataclass
class AgentContribution:
    """Contribution of an agent to collective task."""
    
    agent_id: str
    task_id: str
    contribution: Dict[str, Any]
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EmergentBehavior:
    """Detected emergent behavior in agent society."""
    
    id: str
    behavior_type: str
    description: str
    participants: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 0.0
    impact: str = "unknown"


class CollectiveMemory:
    """
    Shared memory for agent society.
    
    Stores collective knowledge, patterns, and learnings.
    """
    
    def __init__(self):
        self._memory: Dict[str, Any] = {}
        self._patterns: List[Dict[str, Any]] = []
        self._learnings: List[Dict[str, Any]] = []
    
    async def store(self, _key: str, _value: Any, _source: str, _importance: float) -> None:
        """Store knowledge in collective memory."""
        self._memory[key] = {
            "value": value,
            "source": source,
            "importance": importance,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "access_count": 0
        }
        logger.debug("collective_memory_stored", key=key, source=source)
    
    async def retrieve(self, _key: str) -> Optional[Dict[str, Any]]:
        """Retrieve knowledge from collective memory."""
        if key in self._memory:
            self._memory[key]["access_count"] += 1
            self._memory[key]["last_accessed"] = datetime.now(timezone.utc).isoformat()
            return self._memory[key]
        return None
    
    async def add_pattern(self, _pattern_type: str, _pattern_data: Dict[str, Any], _confidence: float) -> None:
        """Add discovered pattern to collective memory."""
        _pattern = {
            "id": str(uuid.uuid4()),
            "type": pattern_type,
            "data": pattern_data,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._patterns.append(pattern)
        logger.info("pattern_discovered", type=pattern_type, confidence=confidence)
    
    async def add_learning(self, _learning_type: str, _learning_data: Dict[str, Any], _participants: List[str]) -> None:
        """Add collective learning to memory."""
        _learning = {
            "id": str(uuid.uuid4()),
            "type": learning_type,
            "data": learning_data,
            "participants": participants,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._learnings.append(learning)
        logger.info("collective_learning", type=learning_type, participants=len(participants))
    
    async def get_patterns(self, _pattern_type: Optional[str], _min_confidence: float) -> List[Dict[str, Any]]:
        """Get patterns from collective memory."""
        _patterns = self._patterns
        if pattern_type:
            _patterns = [p for p in patterns if p["type"] == pattern_type]
        _patterns = [p for p in patterns if p["confidence"] >= min_confidence]
        return patterns
    
    async def get_learnings(self, _learning_type: Optional[str], _limit: int) -> List[Dict[str, Any]]:
        """Get learnings from collective memory."""
        _learnings = self._learnings
        if learning_type:
            _learnings = [l for l in learnings if l["type"] == learning_type]
        return learnings[-limit:]


class AgentSociety:
    """
    Agent Society for collective intelligence.
    
    Manages hierarchical coordination, collective decision-making,
    and emergent behavior detection.
    """
    
    def __init__(self, _supervisor, _contribution_cache_ttl: int, _enable_swarm_intelligence: bool):
        """
        Initialize agent society.
        
        Args:
            supervisor: ActorSupervisor for agent management
            contribution_cache_ttl: TTL for contribution cache in seconds (default: 300)
            enable_swarm_intelligence: Enable swarm intelligence patterns (default: True)
        """
        self.supervisor = supervisor
        self.hierarchy = self._build_hierarchy()
        self.interaction_rules = self._define_rules()
        self.collective_memory = CollectiveMemory()
        self._active_tasks: Dict[str, CollectiveTask] = {}
        self._emergent_behaviors: List[EmergentBehavior] = []
        self._contribution_cache = ContributionCache(ttl_seconds=contribution_cache_ttl)
        
        # Initialize swarm intelligence engine if available
        self.swarm_engine: Optional[SwarmIntelligenceEngine] = None
        if enable_swarm_intelligence and SWARM_INTELLIGENCE_AVAILABLE:
            self.swarm_engine = SwarmIntelligenceEngine()
            logger.info("swarm_intelligence_enabled")
        elif enable_swarm_intelligence and not SWARM_INTELLIGENCE_AVAILABLE:
            logger.warning("swarm_intelligence_requested_but_not_available")
    
    def _build_hierarchy(self) -> Dict[str, List[str]]:
        """
        Build agent hierarchy for coordination.
        
        Returns:
            Dict mapping roles to agent types
        """
        return {
            SocietyRole.LEADERSHIP: ["steward", "alpha", "arbiter"],
            SocietyRole.ANALYSIS: ["alpha", "beta", "charlie", "examiner"],
            SocietyRole.SUPPORT: ["historian", "metis", "empath", "nexus"],
            SocietyRole.EXPLORATION: ["explorer", "perceiver"],
            SocietyRole.DEVELOPMENT: ["coder", "dreamer", "catalyst"],
            SocietyRole.SAFETY: ["sentinel", "sentinel-prime"],
            SocietyRole.COORDINATION: ["coordinator", "chronos"],
        }
    
    def _define_rules(self) -> Dict[str, Any]:
        """
        Define interaction rules for agent society.
        
        Returns:
            Dict of interaction rules
        """
        return {
            "handoff_rules": {
                "analysis_to_support": ["alpha", "beta", "charlie"],
                "support_to_leadership": ["historian", "metis"],
                "exploration_to_analysis": ["explorer", "perceiver"],
                "development_to_safety": ["coder", "dreamer"],
            },
            "consensus_threshold": 0.7,
            "min_participants": 2,
            "max_participants": 10,
            "timeout_seconds": 300,
        }
    
    async def coordinate_task(self, _task: CollectiveTask) -> CollectiveResult:
        """
        Coordinate agents for collective task.
        
        Args:
            task: Collective task to execute
            
        Returns:
            CollectiveResult with outcome
        """
        _task_id = task.id
        logger.info(
            "coordinating_task",
            _task_id = task_id,
            type=task.type,
            description=task.description
        )
        
        _start_time = datetime.now(timezone.utc)
        
        try:
            # Select participants based on task type
            participants = self._select_participants(task)
            task.participants = participants
            
            # Establish communication protocol
            _protocol = self._establish_protocol(participants, task)
            
            # Execute coordinated action
            result = await self._execute_coordination(
                participants,
                protocol,
                task
            )
            
            # Store in collective memory
            await self.collective_memory.add_learning(
                _learning_type = task.type,
                _learning_data = result,
                participants=participants
            )
            
            # Detect emergent behavior
            _emergent = await self._detect_emergent_behavior(
                participants,
                task,
                result
            )
            
            _execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            _collective_result = CollectiveResult(
                _task_id = task_id,
                _success = True,
                _result = result,
                _participants = participants,
                _execution_time = execution_time,
                _consensus_score = result.get("consensus_score", 0.0),
                _emergent_behavior = emergent
            )
            
            task.status = "completed"
            task.result = result
            self._active_tasks[task_id] = task
            
            logger.info(
                "task_completed",
                _task_id = task_id,
                participants=len(participants),
                _execution_time = execution_time
            )
            
            return collective_result
            
        except Exception as e:
            logger.error("task_failed", task_id=task_id, error=str(e))
            return CollectiveResult(
                _task_id = task_id,
                _success = False,
                _error = str(e)
            )
    
    def _select_participants(self, _task: CollectiveTask) -> List[str]:
        """
        Select participants based on task type and hierarchy.
        
        Args:
            task: Collective task
            
        Returns:
            List of agent IDs
        """
        # Map task types to roles
        _task_role_map = {
            CollectiveTaskType.DELIBERATION: [
                SocietyRole.LEADERSHIP,
                SocietyRole.ANALYSIS,
                SocietyRole.SUPPORT
            ],
            CollectiveTaskType.CONSENSUS: [
                SocietyRole.LEADERSHIP,
                SocietyRole.ANALYSIS
            ],
            CollectiveTaskType.COORDINATION: [
                SocietyRole.COORDINATION,
                SocietyRole.LEADERSHIP
            ],
            CollectiveTaskType.OPTIMIZATION: [
                SocietyRole.DEVELOPMENT,
                SocietyRole.ANALYSIS
            ],
            CollectiveTaskType.LEARNING: [
                SocietyRole.SUPPORT,
                SocietyRole.EXPLORATION
            ],
            CollectiveTaskType.MONITORING: [
                SocietyRole.SAFETY,
                SocietyRole.COORDINATION
            ],
        }
        
        _roles = task_role_map.get(task.type, [SocietyRole.LEADERSHIP])
        participants = []
        
        # Get agents for each role
        for role in roles:
            _agent_types = self.hierarchy.get(role, [])
            for agent_type in agent_types:
                if self.supervisor and agent_type in self.supervisor.actors:
                    participants.append(agent_type)
        
        # Limit participants
        _max_participants = self.interaction_rules.get("max_participants", 10)
        if len(participants) > max_participants:
            participants = participants[:max_participants]
        
        # Ensure minimum participants
        _min_participants = self.interaction_rules.get("min_participants", 2)
        if len(participants) < min_participants:
            logger.warning(
                "insufficient_participants",
                _task_type = task.type,
                _available = len(participants),
                _required = min_participants
            )
        
        return participants
    
    def _establish_protocol(self, _participants: List[str], _task: CollectiveTask) -> Dict[str, Any]:
        """
        Establish communication protocol for coordination.
        
        Args:
            participants: List of participant agents
            task: Collective task
            
        Returns:
            Protocol configuration
        """
        return {
            "task_id": task.id,
            "participants": participants,
            "communication_pattern": "broadcast",
            "consensus_threshold": self.interaction_rules.get("consensus_threshold", 0.7),
            "timeout": self.interaction_rules.get("timeout_seconds", 300),
            "rounds": 3,  # Number of deliberation rounds
        }
    
    async def _execute_coordination(self, _participants: List[str], _protocol: Dict[str, Any], _task: CollectiveTask) -> Dict[str, Any]:
        """
        Execute coordinated action among participants.
        
        Args:
            participants: List of participant agents
            protocol: Communication protocol
            task: Collective task
            
        Returns:
            Coordination result
        """
        _contributions = []
        
        # Collect contributions from all participants
        for participant in participants:
            if self.supervisor and participant in self.supervisor.actors:
                _actor = self.supervisor.actors[participant]
                try:
                    # Simulate agent contribution
                    contribution = await self._get_agent_contribution(
                        actor,
                        task,
                        protocol
                    )
                    contributions.append(contribution)
                except Exception as e:
                    logger.error(
                        "contribution_failed",
                        participant=participant,
                        _error = str(e)
                    )
        
        # Aggregate contributions
        _result = await self._aggregate_contributions(
            contributions,
            task,
            protocol
        )
        
        return result
    
    async def _get_agent_contribution(self, _actor, _task: CollectiveTask, _protocol: Dict[str, Any], _timeout: float) -> AgentContribution:
        """
        Get contribution from an agent by invoking its process method.
        
        This method:
        1. Checks cache for existing contribution
        2. Calls actor's process_contribution method if available
        3. Falls back to run_with_llm if actor has LLM capabilities
        4. Waits for response with timeout
        5. Caches the contribution for future requests
        6. Returns properly formatted AgentContribution
        
        Args:
            actor: Agent actor (must be an AgentActor instance)
            task: Collective task to process
            protocol: Communication protocol
            timeout: Timeout in seconds for contribution request (default: 30s)
            
        Returns:
            AgentContribution with agent's response
            
        Raises:
            asyncio.TimeoutError: If actor doesn't respond within timeout
        """
        # Get actor ID
        agent_id = actor.agent_id if hasattr(actor, 'agent_id') else str(type(actor).__name__)
        
        # Check cache first
        _cached = self._contribution_cache.get(agent_id, task.id)
        if cached is not None:
            logger.debug("contribution_cache_hit", agent_id=agent_id, task_id=task.id)
            return cached
        
        try:
            # Try to get contribution via direct method call
            _contribution_data = await self._request_contribution_from_actor(
                actor, task, protocol, timeout
            )
            
            # Create AgentContribution
            contribution = AgentContribution(
                agent_id=agent_id,
                _task_id = task.id,
                contribution=contribution_data.get("contribution", {}),
                confidence=contribution_data.get("confidence", 0.8)
            )
            
            # Cache the contribution
            self._contribution_cache.set(agent_id, task.id, contribution)
            
            logger.info(
                "contribution_received",
                agent_id=agent_id,
                _task_id = task.id,
                confidence=contribution.get("confidence", 0.8)
            )
            
            return contribution
                
        except asyncio.TimeoutError:
            logger.error(
                "contribution_timeout",
                agent_id=agent_id,
                _task_id = task.id,
                _timeout = timeout
            )
            raise
        except Exception as e:
            logger.error(
                "contribution_error",
                agent_id=agent_id,
                _task_id = task.id,
                _error = str(e)
            )
            # Return fallback contribution on error
            return AgentContribution(
                agent_id=agent_id,
                _task_id = task.id,
                contribution={
                    "analysis": f"Error retrieving contribution from {agent_id}: {str(e)}",
                    "recommendation": "error_fallback",
                    "error": str(e)
                },
                confidence=0.1  # Low confidence for error fallback
            )
    
    async def _request_contribution_from_actor(self, _actor, _task: CollectiveTask, _protocol: Dict[str, Any], _timeout: float) -> Dict[str, Any]:
        """
        Request contribution from an actor using available methods.
        
        This method tries multiple approaches:
        1. Direct process_contribution method if available
        2. run_with_llm if Swarms agent is configured
        3. Default fallback based on actor type
        
        Args:
            actor: Agent actor instance
            task: Collective task
            protocol: Communication protocol
            timeout: Timeout in seconds
            
        Returns:
            Dict with contribution data and confidence
        """
        # Prepare task context for the actor
        _task_context = {
            "task_id": task.id,
            "task_type": task.type.value if hasattr(task.type, 'value') else str(task.type),
            "description": task.description,
            "input_data": task.input_data,
            "priority": task.priority,
            "protocol": protocol,
        }
        
        # Try direct method call if actor has process_contribution
        if hasattr(actor, 'process_contribution') and callable(actor.process_contribution):
            _result = await asyncio.wait_for(
                actor.process_contribution(task, protocol),
                _timeout = timeout
            )
            return result
        
        # Try using LLM if available
        if hasattr(actor, 'run_with_llm') and actor.swarms_agent is not None:
            _prompt = self._build_contribution_prompt(task, protocol)
            _response = await asyncio.wait_for(
                actor.run_with_llm(prompt),
                _timeout = timeout
            )
            return {
                "contribution": {
                    "analysis": response,
                    "recommendation": "llm_generated",
                    "method": "run_with_llm"
                },
                "confidence": 0.75
            }
        
        # Fallback: Generate contribution based on actor type
        _actor_type = type(actor).__name__
        return {
            "contribution": {
                "analysis": f"Analysis from {actor_type} for task: {task.description}",
                "recommendation": f"{actor_type}_recommendation",
                "method": "fallback"
            },
            "confidence": 0.6
        }
    
    def _build_contribution_prompt(self, _task: CollectiveTask, _protocol: Dict[str, Any]) -> str:
        """
        Build a prompt for LLM-based contribution.
        
        Args:
            task: Collective task
            protocol: Communication protocol
            
        Returns:
            Formatted prompt string
        """
        return f"""You are participating in a collective task coordination.

Task Details:
- Task ID: {task.id}
- Task Type: {task.type.value if hasattr(task.type, 'value') else str(task.type)}
- Description: {task.description}
- Priority: {task.priority}
- Input Data: {task.input_data}

Protocol:
- Consensus Threshold: {protocol.get('consensus_threshold', 0.7)}
- Communication Pattern: {protocol.get('communication_pattern', 'broadcast')}
- Rounds: {protocol.get('rounds', 3)}

Please provide your analysis and recommendation for this collective task.
Format your response as:
1. Analysis: Your understanding of the task and key considerations
2. Recommendation: Your suggested approach or solution
"""
    
    async def _aggregate_contributions(self, _contributions: List[AgentContribution], _task: CollectiveTask, _protocol: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate contributions from multiple agents.
        
        Args:
            contributions: List of agent contributions
            task: Collective task
            protocol: Communication protocol
            
        Returns:
            Aggregated result
        """
        if not contributions:
            return {
                "status": "failed",
                "reason": "no_contributions"
            }
        
        # Calculate consensus score
        _consensus_threshold = protocol.get("consensus_threshold", 0.7)
        _avg_confidence = sum(c.confidence for c in contributions) / len(contributions)
        _consensus_score = min(avg_confidence / consensus_threshold, 1.0)
        
        # Aggregate recommendations
        _recommendations = [
            c.contribution.get("recommendation")
            for c in contributions
            if c.contribution.get("recommendation")
        ]
        
        # Simple majority voting
        if recommendations:
            from collections import Counter
            _vote_counts = Counter(recommendations)
            _top_recommendation = vote_counts.most_common(1)[0][0]
        else:
            _top_recommendation = "no_consensus"
        
        return {
            "status": "completed",
            "consensus_score": consensus_score,
            "recommendation": top_recommendation,
            "participant_count": len(contributions),
            "contributions": [
                {
                    "agent_id": c.agent_id,
                    "confidence": c.confidence,
                    "contribution": c.contribution
                }
                for c in contributions
            ]
        }
    
    async def _detect_emergent_behavior(self, _participants: List[str], _task: CollectiveTask, _result: Dict[str, Any]) -> Optional[str]:
        """
        Detect emergent behavior in agent society.
        
        Args:
            participants: List of participant agents
            task: Collective task
            result: Coordination result
            
        Returns:
            Description of emergent behavior or None
        """
        # Check for high consensus
        _consensus_score = result.get("consensus_score", 0.0)
        if consensus_score > 0.9:
            _behavior = EmergentBehavior(
                id=str(uuid.uuid4()),
                _behavior_type = "high_consensus",
                description=f"Agents achieved {consensus_score:.2f} consensus",
                _participants = participants,
                confidence=consensus_score,
                _impact = "positive"
            )
            self._emergent_behaviors.append(behavior)
            await self.collective_memory.add_pattern(
                _pattern_type = "consensus",
                _pattern_data = {
                    "task_type": task.type,
                    "participants": participants,
                    "score": consensus_score
                },
                confidence=consensus_score
            )
            return behavior.description
        
        # Check for diverse opinions
        _participant_count = len(participants)
        _unique_contributions = len(result.get("contributions", []))
        if unique_contributions == participant_count and participant_count > 3:
            _behavior = EmergentBehavior(
                id=str(uuid.uuid4()),
                _behavior_type = "diverse_perspective",
                description=f"All {participant_count} agents provided unique contributions",
                _participants = participants,
                confidence=0.8,
                _impact = "positive"
            )
            self._emergent_behaviors.append(behavior)
            return behavior.description
        
        return None

    async def apply_swarm_pattern(self, _pattern: str, _participants: List[str], _decision_space: Dict[str, float], **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        Apply a swarm intelligence pattern to a decision problem.

        This method delegates to the swarm intelligence engine to apply
        bio-inspired patterns for collective decision-making.

        Args:
            pattern: Swarm pattern to apply ("pso", "ant_colony", "bee_algorithm",
                     "flocking", "stigmergy")
            participants: List of participant agent IDs
            decision_space: Decision space as a dictionary of options and values
            **kwargs: Additional parameters for the specific pattern

        Returns:
            Dictionary with swarm decision results or None if swarm engine unavailable

        Raises:
            ValueError: If invalid pattern specified
        """
        if not self.swarm_engine:
            logger.warning("swarm_pattern_requested_but_engine_unavailable")
            return None

        _pattern_map = {
            "pso": self.swarm_engine.run_pso,
            "ant_colony": self.swarm_engine.run_ant_colony,
            "bee_algorithm": self.swarm_engine.run_bee_algorithm,
            "flocking": self.swarm_engine.run_flocking,
            "stigmergy": self.swarm_engine.run_stigmergy,
        }

        if pattern.lower() not in pattern_map:
            raise ValueError(
                f"Invalid swarm pattern: {pattern}. "
                f"Valid options: {list(pattern_map.keys())}"
            )

        logger.info(
            "applying_swarm_pattern",
            _pattern = pattern,
            participants=len(participants),
        )

        # Execute the swarm pattern
        swarm_decision: SwarmDecision = await pattern_map[pattern.lower()](
            participants=participants,
            _decision_space = decision_space,
            **kwargs,
        )

        # Store result in collective memory
        await self.collective_memory.add_pattern(
            _pattern_type = f"swarm_{pattern}",
            _pattern_data = {
                "decision": swarm_decision.decision,
                "confidence": swarm_decision.confidence,
                "participants": participants,
                "iterations": swarm_decision.iterations,
                "emergence_detected": swarm_decision.emergence_detected,
                "quality_metrics": swarm_decision.quality_metrics,
            },
            confidence=swarm_decision.confidence,
        )

        # Check for emergent behavior
        if swarm_decision.emergence_detected:
            _emergent = EmergentBehavior(
                id=str(uuid.uuid4()),
                _behavior_type = f"swarm_{pattern}_emergence",
                _description = f"Emergent behavior detected in {pattern} pattern",
                _participants = participants,
                confidence=swarm_decision.confidence,
                _impact = "positive" if swarm_decision.quality_metrics.get("convergence_rate", 0) > 0.7 else "neutral",
            )
            self._emergent_behaviors.append(emergent)

        return {
            "decision": swarm_decision.decision,
            "confidence": swarm_decision.confidence,
            "iterations": swarm_decision.iterations,
            "emergence_detected": swarm_decision.emergence_detected,
            "quality_metrics": swarm_decision.quality_metrics,
            "pattern_type": pattern,
        }

    async def run_collective_optimization(self, _task: CollectiveTask, _optimization_type: str, _max_iterations: int) -> CollectiveResult:
        """
        Run collective optimization using swarm intelligence.

        This method integrates swarm patterns into the collective task execution
        flow, enabling bio-inspired optimization for complex decision problems.

        Args:
            task: Collective task to optimize
            optimization_type: Type of optimization ("pso", "ant_colony", "bee_algorithm")
            max_iterations: Maximum optimization iterations

        Returns:
            CollectiveResult with optimization outcome
        """
        _start_time = datetime.now(timezone.utc)

        if not self.swarm_engine:
            return CollectiveResult(
                _task_id = task.id,
                _success = False,
                _error = "Swarm intelligence engine not available",
            )

        logger.info(
            "running_collective_optimization",
            _task_id = task.id,
            _type = optimization_type,
        )

        # Convert task to decision space
        _decision_space = {
            str(k): v if isinstance(v, float) else float(v)
            for k, v in task.input_data.items()
        }

        # Select participants based on task requirements
        _participants = task.participants or self._select_participants(task)

        try:
            # Apply swarm pattern
            _result = await self.apply_swarm_pattern(
                _pattern = optimization_type,
                _participants = participants,
                _decision_space = decision_space,
                _max_iterations = max_iterations,
            )

            if result is None:
                return CollectiveResult(
                    _task_id = task.id,
                    _success = False,
                    _error = "Swarm pattern execution failed",
                )

            _execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return CollectiveResult(
                _task_id = task.id,
                _success = True,
                _result = result,
                _participants = participants,
                _execution_time = execution_time,
                _consensus_score = result.get("confidence", 0.0),
                _emergent_behavior = result.get("emergence_detected", False),
            )

        except Exception as e:
            logger.exception("collective_optimization_failed", task_id=task.id, error=str(e))
            return CollectiveResult(
                _task_id = task.id,
                _success = False,
                _error = str(e),
                _participants = participants,
            )

    def get_swarm_status(self) -> Dict[str, Any]:
        """
        Get status of swarm intelligence engine.

        Returns:
            Dictionary with swarm engine status
        """
        if not self.swarm_engine:
            return {"available": False, "enabled": False}

        return {
            "available": True,
            "enabled": True,
            "patterns_available": [p.value for p in SwarmPattern],
            "active_particles": len(self.swarm_engine.particles),
            "active_pheromones": len(self.swarm_engine.pheromone_trails),
            "active_bees": len(self.swarm_engine.bee_agents),
            "active_flocking_agents": len(self.swarm_engine.flocking_agents),
            "stigmergic_traces": len(self.swarm_engine.stigmergic_traces),
        }

    async def optimize_swarm(self, _metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize swarm based on performance metrics.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Optimization recommendations
        """
        logger.info("optimizing_swarm", metrics=metrics)
        
        _recommendations = []
        
        # Analyze agent performance
        if "agent_performance" in metrics:
            for agent_id, perf in metrics["agent_performance"].items():
                if perf.get("error_rate", 0) > 0.1:
                    recommendations.append({
                        "type": "agent_reconfiguration",
                        "target": agent_id,
                        "reason": "high_error_rate",
                        "suggestion": "review_agent_configuration"
                    })
        
        # Analyze communication patterns
        if "communication_metrics" in metrics:
            _comm_metrics = metrics["communication_metrics"]
            if comm_metrics.get("latency", 0) > 1000:  # 1 second
                recommendations.append({
                    "type": "communication_optimization",
                    "reason": "high_latency",
                    "suggestion": "optimize_message_routing"
                })
        
        # Analyze resource usage
        if "resource_metrics" in metrics:
            _res_metrics = metrics["resource_metrics"]
            if res_metrics.get("memory_usage", 0) > 0.8:
                recommendations.append({
                    "type": "resource_management",
                    "reason": "high_memory_usage",
                    "suggestion": "implement_memory_cleanup"
                })
        
        return {
            "recommendations": recommendations,
            "optimization_score": self._calculate_optimization_score(metrics),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_optimization_score(self, _metrics: Dict[str, Any]) -> float:
        """
        Calculate overall optimization score.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Optimization score (0-1)
        """
        _scores = []
        
        # Agent performance score
        if "agent_performance" in metrics:
            _avg_success_rate = sum(
                p.get("success_rate", 0.5)
                for p in metrics["agent_performance"].values()
            ) / len(metrics["agent_performance"])
            scores.append(avg_success_rate)
        
        # Communication score
        if "communication_metrics" in metrics:
            _latency = metrics["communication_metrics"].get("latency", 1000)
            _comm_score = max(1.0 - (latency / 5000), 0.0)
            scores.append(comm_score)
        
        # Resource score
        if "resource_metrics" in metrics:
            _memory_usage = metrics["resource_metrics"].get("memory_usage", 0.5)
            _resource_score = 1.0 - memory_usage
            scores.append(resource_score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def get_society_status(self) -> Dict[str, Any]:
        """
        Get current status of agent society.
        
        Returns:
            Society status information including swarm intelligence status
        """
        _status = {
            "hierarchy": self.hierarchy,
            "active_tasks": len(self._active_tasks),
            "emergent_behaviors": len(self._emergent_behaviors),
            "collective_memory_size": len(self.collective_memory._memory),
            "patterns_discovered": len(self.collective_memory._patterns),
            "collective_learnings": len(self.collective_memory._learnings),
            "interaction_rules": self.interaction_rules,
        }

        # Add swarm intelligence status if available
        if self.swarm_engine:
            status["swarm_intelligence"] = self.get_swarm_status()

        return status
