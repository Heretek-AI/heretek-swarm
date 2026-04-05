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
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


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
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
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
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class EmergentBehavior:
    """Detected emergent behavior in agent society."""
    
    id: str
    behavior_type: str
    description: str
    participants: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
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
    
    async def store(
        self,
        key: str,
        value: Any,
        source: str = "collective",
        importance: float = 0.5
    ) -> None:
        """Store knowledge in collective memory."""
        self._memory[key] = {
            "value": value,
            "source": source,
            "importance": importance,
            "timestamp": datetime.utcnow().isoformat(),
            "access_count": 0
        }
        logger.debug("collective_memory_stored", key=key, source=source)
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve knowledge from collective memory."""
        if key in self._memory:
            self._memory[key]["access_count"] += 1
            self._memory[key]["last_accessed"] = datetime.utcnow().isoformat()
            return self._memory[key]
        return None
    
    async def add_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        confidence: float = 0.5
    ) -> None:
        """Add discovered pattern to collective memory."""
        pattern = {
            "id": str(uuid.uuid4()),
            "type": pattern_type,
            "data": pattern_data,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._patterns.append(pattern)
        logger.info("pattern_discovered", type=pattern_type, confidence=confidence)
    
    async def add_learning(
        self,
        learning_type: str,
        learning_data: Dict[str, Any],
        participants: List[str]
    ) -> None:
        """Add collective learning to memory."""
        learning = {
            "id": str(uuid.uuid4()),
            "type": learning_type,
            "data": learning_data,
            "participants": participants,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._learnings.append(learning)
        logger.info("collective_learning", type=learning_type, participants=len(participants))
    
    async def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Get patterns from collective memory."""
        patterns = self._patterns
        if pattern_type:
            patterns = [p for p in patterns if p["type"] == pattern_type]
        patterns = [p for p in patterns if p["confidence"] >= min_confidence]
        return patterns
    
    async def get_learnings(
        self,
        learning_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get learnings from collective memory."""
        learnings = self._learnings
        if learning_type:
            learnings = [l for l in learnings if l["type"] == learning_type]
        return learnings[-limit:]


class AgentSociety:
    """
    Agent Society for collective intelligence.
    
    Manages hierarchical coordination, collective decision-making,
    and emergent behavior detection.
    """
    
    def __init__(self, supervisor=None):
        """
        Initialize agent society.
        
        Args:
            supervisor: ActorSupervisor for agent management
        """
        self.supervisor = supervisor
        self.hierarchy = self._build_hierarchy()
        self.interaction_rules = self._define_rules()
        self.collective_memory = CollectiveMemory()
        self._active_tasks: Dict[str, CollectiveTask] = {}
        self._emergent_behaviors: List[EmergentBehavior] = []
    
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
    
    async def coordinate_task(
        self,
        task: CollectiveTask
    ) -> CollectiveResult:
        """
        Coordinate agents for collective task.
        
        Args:
            task: Collective task to execute
            
        Returns:
            CollectiveResult with outcome
        """
        task_id = task.id
        logger.info(
            "coordinating_task",
            task_id=task_id,
            type=task.type,
            description=task.description
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Select participants based on task type
            participants = self._select_participants(task)
            task.participants = participants
            
            # Establish communication protocol
            protocol = self._establish_protocol(participants, task)
            
            # Execute coordinated action
            result = await self._execute_coordination(
                participants,
                protocol,
                task
            )
            
            # Store in collective memory
            await self.collective_memory.add_learning(
                learning_type=task.type,
                learning_data=result,
                participants=participants
            )
            
            # Detect emergent behavior
            emergent = await self._detect_emergent_behavior(
                participants,
                task,
                result
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            collective_result = CollectiveResult(
                task_id=task_id,
                success=True,
                result=result,
                participants=participants,
                execution_time=execution_time,
                consensus_score=result.get("consensus_score", 0.0),
                emergent_behavior=emergent
            )
            
            task.status = "completed"
            task.result = result
            self._active_tasks[task_id] = task
            
            logger.info(
                "task_completed",
                task_id=task_id,
                participants=len(participants),
                execution_time=execution_time
            )
            
            return collective_result
            
        except Exception as e:
            logger.error("task_failed", task_id=task_id, error=str(e))
            return CollectiveResult(
                task_id=task_id,
                success=False,
                error=str(e)
            )
    
    def _select_participants(self, task: CollectiveTask) -> List[str]:
        """
        Select participants based on task type and hierarchy.
        
        Args:
            task: Collective task
            
        Returns:
            List of agent IDs
        """
        # Map task types to roles
        task_role_map = {
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
        
        roles = task_role_map.get(task.type, [SocietyRole.LEADERSHIP])
        participants = []
        
        # Get agents for each role
        for role in roles:
            agent_types = self.hierarchy.get(role, [])
            for agent_type in agent_types:
                if self.supervisor and agent_type in self.supervisor.actors:
                    participants.append(agent_type)
        
        # Limit participants
        max_participants = self.interaction_rules.get("max_participants", 10)
        if len(participants) > max_participants:
            participants = participants[:max_participants]
        
        # Ensure minimum participants
        min_participants = self.interaction_rules.get("min_participants", 2)
        if len(participants) < min_participants:
            logger.warning(
                "insufficient_participants",
                task_type=task.type,
                available=len(participants),
                required=min_participants
            )
        
        return participants
    
    def _establish_protocol(
        self,
        participants: List[str],
        task: CollectiveTask
    ) -> Dict[str, Any]:
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
    
    async def _execute_coordination(
        self,
        participants: List[str],
        protocol: Dict[str, Any],
        task: CollectiveTask
    ) -> Dict[str, Any]:
        """
        Execute coordinated action among participants.
        
        Args:
            participants: List of participant agents
            protocol: Communication protocol
            task: Collective task
            
        Returns:
            Coordination result
        """
        contributions = []
        
        # Collect contributions from all participants
        for participant in participants:
            if self.supervisor and participant in self.supervisor.actors:
                actor = self.supervisor.actors[participant]
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
                        error=str(e)
                    )
        
        # Aggregate contributions
        result = await self._aggregate_contributions(
            contributions,
            task,
            protocol
        )
        
        return result
    
    async def _get_agent_contribution(
        self,
        actor,
        task: CollectiveTask,
        protocol: Dict[str, Any]
    ) -> AgentContribution:
        """
        Get contribution from an agent.
        
        Args:
            actor: Agent actor
            task: Collective task
            protocol: Communication protocol
            
        Returns:
            Agent contribution
        """
        # This would typically call the agent's process method
        # For now, return a placeholder
        return AgentContribution(
            agent_id=actor.agent_id if hasattr(actor, 'agent_id') else str(type(actor).__name__),
            task_id=task.id,
            contribution={
                "analysis": f"Analysis from {type(actor).__name__}",
                "recommendation": "pending",
            },
            confidence=0.8
        )
    
    async def _aggregate_contributions(
        self,
        contributions: List[AgentContribution],
        task: CollectiveTask,
        protocol: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        consensus_threshold = protocol.get("consensus_threshold", 0.7)
        avg_confidence = sum(c.confidence for c in contributions) / len(contributions)
        consensus_score = min(avg_confidence / consensus_threshold, 1.0)
        
        # Aggregate recommendations
        recommendations = [
            c.contribution.get("recommendation")
            for c in contributions
            if c.contribution.get("recommendation")
        ]
        
        # Simple majority voting
        if recommendations:
            from collections import Counter
            vote_counts = Counter(recommendations)
            top_recommendation = vote_counts.most_common(1)[0][0]
        else:
            top_recommendation = "no_consensus"
        
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
    
    async def _detect_emergent_behavior(
        self,
        participants: List[str],
        task: CollectiveTask,
        result: Dict[str, Any]
    ) -> Optional[str]:
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
        consensus_score = result.get("consensus_score", 0.0)
        if consensus_score > 0.9:
            behavior = EmergentBehavior(
                id=str(uuid.uuid4()),
                behavior_type="high_consensus",
                description=f"Agents achieved {consensus_score:.2f} consensus",
                participants=participants,
                confidence=consensus_score,
                impact="positive"
            )
            self._emergent_behaviors.append(behavior)
            await self.collective_memory.add_pattern(
                pattern_type="consensus",
                pattern_data={
                    "task_type": task.type,
                    "participants": participants,
                    "score": consensus_score
                },
                confidence=consensus_score
            )
            return behavior.description
        
        # Check for diverse opinions
        participant_count = len(participants)
        unique_contributions = len(result.get("contributions", []))
        if unique_contributions == participant_count and participant_count > 3:
            behavior = EmergentBehavior(
                id=str(uuid.uuid4()),
                behavior_type="diverse_perspective",
                description=f"All {participant_count} agents provided unique contributions",
                participants=participants,
                confidence=0.8,
                impact="positive"
            )
            self._emergent_behaviors.append(behavior)
            return behavior.description
        
        return None
    
    async def optimize_swarm(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize swarm based on performance metrics.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Optimization recommendations
        """
        logger.info("optimizing_swarm", metrics=metrics)
        
        recommendations = []
        
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
            comm_metrics = metrics["communication_metrics"]
            if comm_metrics.get("latency", 0) > 1000:  # 1 second
                recommendations.append({
                    "type": "communication_optimization",
                    "reason": "high_latency",
                    "suggestion": "optimize_message_routing"
                })
        
        # Analyze resource usage
        if "resource_metrics" in metrics:
            res_metrics = metrics["resource_metrics"]
            if res_metrics.get("memory_usage", 0) > 0.8:
                recommendations.append({
                    "type": "resource_management",
                    "reason": "high_memory_usage",
                    "suggestion": "implement_memory_cleanup"
                })
        
        return {
            "recommendations": recommendations,
            "optimization_score": self._calculate_optimization_score(metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_optimization_score(
        self,
        metrics: Dict[str, Any]
    ) -> float:
        """
        Calculate overall optimization score.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Optimization score (0-1)
        """
        scores = []
        
        # Agent performance score
        if "agent_performance" in metrics:
            avg_success_rate = sum(
                p.get("success_rate", 0.5)
                for p in metrics["agent_performance"].values()
            ) / len(metrics["agent_performance"])
            scores.append(avg_success_rate)
        
        # Communication score
        if "communication_metrics" in metrics:
            latency = metrics["communication_metrics"].get("latency", 1000)
            comm_score = max(1.0 - (latency / 5000), 0.0)
            scores.append(comm_score)
        
        # Resource score
        if "resource_metrics" in metrics:
            memory_usage = metrics["resource_metrics"].get("memory_usage", 0.5)
            resource_score = 1.0 - memory_usage
            scores.append(resource_score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def get_society_status(self) -> Dict[str, Any]:
        """
        Get current status of agent society.
        
        Returns:
            Society status information
        """
        return {
            "hierarchy": self.hierarchy,
            "active_tasks": len(self._active_tasks),
            "emergent_behaviors": len(self._emergent_behaviors),
            "collective_memory_size": len(self.collective_memory._memory),
            "patterns_discovered": len(self.collective_memory._patterns),
            "collective_learnings": len(self.collective_memory._learnings),
            "interaction_rules": self.interaction_rules
        }
