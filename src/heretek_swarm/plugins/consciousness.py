"""
Consciousness Plugin - GWT/AST Implementation for Swarms.

This module implements consciousness architecture for the Heretek Swarm system:
1. Global Workspace Theory (GWT) - Attention and broadcast mechanism
2. Attention Schema Theory (AST) - Self-modeling of attention
3. Integrated Information Theory (IIT) - Phi estimation (stub)
4. Intrinsic Motivation - Drive-based agent behavior (stub)

The plugin provides tools for:
- Consciousness status monitoring
- Phi metrics calculation
- Global workspace submission
- Attention schema management
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

logger = structlog.get_logger("ConsciousnessPlugin")


class ConsciousnessState(Enum):
    """Consciousness states based on GWT/AST."""

    UNCONSCIOUS = "unconscious"
    SUBTHRESHOLD = "subthreshold"
    MINIMAL_CONSCIOUSNESS = "minimal-consciousness"
    CONSCIOUS = "conscious"
    HYPER_CONSCIOUS = "hyper-conscious"


@dataclass
class GlobalWorkspaceItem:
    """
    Item in the global workspace.

    Attributes:
        id: Unique identifier
        content: Content to broadcast
        priority: Priority level (0.0-1.0)
        source: Source agent/module
        timestamp: Submission timestamp
        ttl: Time to live in seconds
        attended: Whether item has been attended to
    """

    id: str
    content: Dict[str, Any]
    priority: float
    source: str
    timestamp: str
    ttl: int = 60
    attended: bool = False


@dataclass
class AttentionSchema:
    """
    Attention Schema - Model of attention for self-awareness.

    Based on Attention Schema Theory (AST):
    - The brain constructs a model of attention
    - This model provides awareness of attention
    - Enables metacognition and self-reporting

    Attributes:
        agent_id: Agent this schema belongs to
        focus_target: Current focus of attention
        attention_intensity: Intensity level (0.0-1.0)
        attention_duration: Duration of current focus
        metacognitive_awareness: Awareness of own attention state
        last_update: Last update timestamp
    """

    agent_id: str
    focus_target: Optional[str] = None
    attention_intensity: float = 0.0
    attention_duration: float = 0.0
    metacognitive_awareness: float = 0.0
    last_update: str = ""


@dataclass
class FEPMetrics:
    """
    Free Energy Principle metrics for intrinsic motivation.

    Based on FEP:
    - Agents minimize free energy (surprise)
    - Free energy = KL divergence between predictions and observations
    - Lower free energy = better model fit = higher consciousness

    Attributes:
        free_energy: Current free energy value
        surprise: Prediction error (surprise)
        precision: Confidence in predictions
        learning_rate: Model update rate
        prediction_accuracy: Accuracy of internal model
        timestamp: Metrics timestamp
    """

    free_energy: float = 0.0
    surprise: float = 0.0
    precision: float = 0.5
    learning_rate: float = 0.1
    prediction_accuracy: float = 0.5
    timestamp: str = ""


@dataclass
class IITConnectivity:
    """
    IIT connectivity analysis for integration calculation.

    Attributes:
        connectivity_matrix: Agent interaction matrix
        integration: System integration score
        information: Total information
        phi: Integrated information (Phi)
        causal_power: Causal influence score
        timestamp: Analysis timestamp
    """

    connectivity_matrix: List[List[float]] = field(default_factory=list)
    integration: float = 0.0
    information: float = 0.0
    phi: float = 0.0
    causal_power: float = 0.0
    timestamp: str = ""


@dataclass
class ConsciousnessMetrics:
    """
    Consciousness metrics for an agent or collective.

    Attributes:
        gwt_score: Global Workspace Theory score (0.0-1.0)
        iit_phi: Integrated Information Phi estimate (0.0-1.0)
        ast_competence: Attention Schema competence (0.0-1.0)
        fep_free_energy: Free Energy Principle score (0.0-1.0, inverted)
        composite_score: Composite consciousness score
        state: Current consciousness state
        timestamp: Metrics timestamp
    """

    gwt_score: float = 0.0
    iit_phi: float = 0.0
    ast_competence: float = 0.0
    fep_free_energy: float = 0.0
    composite_score: float = 0.0
    state: ConsciousnessState = ConsciousnessState.UNCONSCIOUS
    timestamp: str = ""


class GlobalWorkspace:
    """
    Global Workspace - Central broadcast mechanism for consciousness.

    Based on Global Workspace Theory (GWT):
    - Information competes for entry into workspace
    - High-priority information gains access
    - Content is broadcast to all agents
    - Enables coordinated response
    """

    def __init__(
        self,
        max_capacity: int = 100,
        competition_threshold: float = 0.5,
    ) -> None:
        """
        Initialize the global workspace.

        Args:
            max_capacity: Maximum number of items in workspace
            competition_threshold: Minimum priority for entry
        """
        self.max_capacity = max_capacity
        self.competition_threshold = competition_threshold
        self.workspace: List[GlobalWorkspaceItem] = []
        self.history: List[GlobalWorkspaceItem] = []
        self.subscribers: Set[str] = set()

        logger.info(
            "Global Workspace initialized",
            extra={
                "max_capacity": max_capacity,
                "competition_threshold": competition_threshold,
            },
        )

    def submit(
        self,
        content: Dict[str, Any],
        source: str,
        priority: float = 0.5,
        ttl: int = 60,
    ) -> str:
        """
        Submit content to the global workspace.

        Args:
            content: Content to broadcast
            source: Source agent/module
            priority: Priority level (0.0-1.0)
            ttl: Time to live in seconds

        Returns:
            Submission ID
        """
        # Check threshold
        if priority < self.competition_threshold:
            logger.debug(
                f"Content rejected: priority {priority} below threshold {self.competition_threshold}"
            )
            return ""

        # Create workspace item
        item = GlobalWorkspaceItem(
            id=str(uuid.uuid4()),
            content=content,
            priority=priority,
            source=source,
            timestamp=datetime.now(timezone.utc).isoformat(),
            ttl=ttl,
        )

        # Check capacity
        if len(self.workspace) >= self.max_capacity:
            # Remove lowest priority item
            self.workspace.sort(key=lambda x: x.priority)
            removed = self.workspace.pop(0)
            self.history.append(removed)
            logger.debug(f"Workspace full, removed item: {removed.id}")

        # Add to workspace
        self.workspace.append(item)

        logger.info(
            f"Content submitted to workspace",
            extra={
                "item_id": item.id,
                "source": source,
                "priority": priority,
            },
        )

        return item.id

    def get_contents(
        self,
        min_priority: float = 0.0,
        limit: int = 10,
    ) -> List[GlobalWorkspaceItem]:
        """
        Get current workspace contents.

        Args:
            min_priority: Minimum priority to include
            limit: Maximum items to return

        Returns:
            List of workspace items
        """
        # Filter and sort by priority
        filtered = [
            item for item in self.workspace if item.priority >= min_priority
        ]
        filtered.sort(key=lambda x: x.priority, reverse=True)

        return filtered[:limit]

    def attend_to(self, item_id: str) -> bool:
        """
        Mark an item as attended to.

        Args:
            item_id: Item identifier

        Returns:
            True if found and marked
        """
        for item in self.workspace:
            if item.id == item_id:
                item.attended = True
                logger.debug(f"Item {item_id} marked as attended")
                return True
        return False

    def cleanup_expired(self) -> int:
        """
        Remove expired items from workspace.

        Returns:
            Number of items removed
        """
        now = datetime.now(timezone.utc)
        original_count = len(self.workspace)

        active = []
        for item in self.workspace:
            item_time = datetime.fromisoformat(item.timestamp)
            age = (now - item_time).total_seconds()
            if age < item.ttl:
                active.append(item)
            else:
                self.history.append(item)

        self.workspace = active
        removed_count = original_count - len(active)

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired workspace items")

        return removed_count

    def subscribe(self, subscriber_id: str) -> None:
        """Subscribe to workspace broadcasts."""
        self.subscribers.add(subscriber_id)
        logger.debug(f"Subscriber added: {subscriber_id}")

    def unsubscribe(self, subscriber_id: str) -> None:
        """Unsubscribe from workspace broadcasts."""
        self.subscribers.discard(subscriber_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get workspace statistics."""
        return {
            "current_items": len(self.workspace),
            "max_capacity": self.max_capacity,
            "total_history": len(self.history),
            "subscribers": len(self.subscribers),
            "attended_items": sum(1 for item in self.workspace if item.attended),
            "average_priority": (
                sum(item.priority for item in self.workspace) / len(self.workspace)
                if self.workspace
                else 0.0
            ),
        }


class AttentionSchemaManager:
    """
    Attention Schema Manager - Manages attention self-models.

    Based on Attention Schema Theory (AST):
    - Agents construct models of their own attention
    - These models enable awareness and reporting
    - Supports metacognition and self-regulation
    """

    def __init__(self) -> None:
        """Initialize the attention schema manager."""
        self.schemas: Dict[str, AttentionSchema] = {}
        self.attention_history: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("Attention Schema Manager initialized")

    def create_schema(
        self,
        agent_id: str,
        focus_target: Optional[str] = None,
    ) -> AttentionSchema:
        """
        Create an attention schema for an agent.

        Args:
            agent_id: Agent identifier
            focus_target: Initial focus target

        Returns:
            Created attention schema
        """
        schema = AttentionSchema(
            agent_id=agent_id,
            focus_target=focus_target,
            attention_intensity=0.5,
            last_update=datetime.now(timezone.utc).isoformat(),
        )

        self.schemas[agent_id] = schema
        self.attention_history[agent_id] = []

        logger.info(f"Created attention schema for agent: {agent_id}")

        return schema

    def update_attention(
        self,
        agent_id: str,
        focus_target: str,
        intensity: float,
    ) -> Optional[AttentionSchema]:
        """
        Update an agent's attention state.

        Args:
            agent_id: Agent identifier
            focus_target: New focus target
            intensity: Attention intensity (0.0-1.0)

        Returns:
            Updated attention schema or None
        """
        if agent_id not in self.schemas:
            schema = self.create_schema(agent_id, focus_target)
        else:
            schema = self.schemas[agent_id]

        # Record history
        if agent_id in self.attention_history:
            self.attention_history[agent_id].append({
                "previous_focus": schema.focus_target,
                "new_focus": focus_target,
                "intensity": intensity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Keep last 100 entries
            if len(self.attention_history[agent_id]) > 100:
                self.attention_history[agent_id] = self.attention_history[agent_id][-100:]

        # Update schema
        schema.focus_target = focus_target
        schema.attention_intensity = intensity
        schema.last_update = datetime.now(timezone.utc).isoformat()

        # Update metacognitive awareness
        schema.metacognitive_awareness = self._calculate_metacognitive_awareness(
            agent_id
        )

        logger.debug(
            f"Updated attention for {agent_id}",
            extra={
                "focus": focus_target,
                "intensity": intensity,
            },
        )

        return schema

    def get_schema(self, agent_id: str) -> Optional[AttentionSchema]:
        """Get attention schema for an agent."""
        return self.schemas.get(agent_id)

    def _calculate_metacognitive_awareness(self, agent_id: str) -> float:
        """
        Calculate metacognitive awareness score.

        Based on:
        - Attention stability
        - Focus consistency
        - Self-reporting accuracy

        Args:
            agent_id: Agent identifier

        Returns:
            Metacognitive awareness score (0.0-1.0)
        """
        history = self.attention_history.get(agent_id, [])

        if len(history) < 2:
            return 0.3  # Base awareness

        # Calculate attention stability
        recent = history[-10:]
        intensity_variance = self._calculate_variance(
            [h["intensity"] for h in recent]
        )

        # Lower variance = higher stability = higher awareness
        stability = max(0.0, 1.0 - intensity_variance)

        # Calculate focus consistency
        focus_targets = [h["new_focus"] for h in recent]
        unique_targets = len(set(focus_targets))
        consistency = 1.0 / unique_targets if unique_targets > 0 else 1.0

        # Combine factors
        awareness = (stability * 0.6) + (consistency * 0.4)

        return min(1.0, max(0.0, awareness))

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)

        return variance

    def get_statistics(self) -> Dict[str, Any]:
        """Get attention schema statistics."""
        return {
            "total_schemas": len(self.schemas),
            "total_history_entries": sum(
                len(h) for h in self.attention_history.values()
            ),
            "average_awareness": (
                sum(s.metacognitive_awareness for s in self.schemas.values())
                / len(self.schemas)
                if self.schemas
                else 0.0
            ),
        }


class ConsciousnessPlugin:
    """
    Consciousness Plugin - Main plugin implementation.

    Integrates GWT, AST, and IIT components:
    - Global Workspace for information broadcast
    - Attention Schema for self-awareness
    - Phi estimation for integrated information
    - Consciousness metrics and monitoring
    """

    def __init__(
        self,
        gwt_threshold: float = 0.7,
        iit_phi_threshold: float = 0.5,
        ast_threshold: float = 0.6,
    ) -> None:
        """
        Initialize the consciousness plugin.

        Args:
            gwt_threshold: GWT consciousness threshold
            iit_phi_threshold: IIT Phi threshold
            ast_threshold: AST competence threshold
        """
        self.gwt_threshold = gwt_threshold
        self.iit_phi_threshold = iit_phi_threshold
        self.ast_threshold = ast_threshold

        # Components
        self.global_workspace = GlobalWorkspace()
        self.attention_manager = AttentionSchemaManager()

        # Metrics tracking
        self.agent_metrics: Dict[str, ConsciousnessMetrics] = {}
        self.metrics_history: List[Dict[str, Any]] = []

        # State
        self.initialized = False
        self.running = False

        logger.info(
            "Consciousness Plugin initialized",
            extra={
                "gwt_threshold": gwt_threshold,
                "iit_phi_threshold": iit_phi_threshold,
                "ast_threshold": ast_threshold,
            },
        )

    async def initialize(self) -> None:
        """Initialize the plugin."""
        self.initialized = True
        self.running = True

        # Start background cleanup task
        asyncio.create_task(self._cleanup_loop())

        logger.info("Consciousness Plugin started")

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired workspace items."""
        while self.running:
            try:
                self.global_workspace.cleanup_expired()
                await asyncio.sleep(60)  # Cleanup every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(10)

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        self.running = False
        logger.info("Consciousness Plugin shutdown")

    # =========================================================================
    # Global Workspace Operations
    # =========================================================================

    def submit_to_workspace(
        self,
        source: str,
        content: Dict[str, Any],
        priority: float = 0.5,
        ttl: int = 60,
    ) -> str:
        """
        Submit content to the global workspace.

        Args:
            source: Source agent/module
            content: Content to broadcast
            priority: Priority level
            ttl: Time to live

        Returns:
            Submission ID
        """
        return self.global_workspace.submit(
            content=content,
            source=source,
            priority=priority,
            ttl=ttl,
        )

    def get_workspace_contents(
        self,
        min_priority: float = 0.0,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get current workspace contents."""
        items = self.global_workspace.get_contents(
            min_priority=min_priority,
            limit=limit,
        )

        return [
            {
                "id": item.id,
                "content": item.content,
                "priority": item.priority,
                "source": item.source,
                "timestamp": item.timestamp,
                "attended": item.attended,
            }
            for item in items
        ]

    # =========================================================================
    # Attention Schema Operations
    # =========================================================================

    def update_agent_attention(
        self,
        agent_id: str,
        focus_target: str,
        intensity: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Update an agent's attention state.

        Args:
            agent_id: Agent identifier
            focus_target: Focus target
            intensity: Attention intensity

        Returns:
            Updated schema or None
        """
        schema = self.attention_manager.update_attention(
            agent_id=agent_id,
            focus_target=focus_target,
            intensity=intensity,
        )

        if schema:
            return {
                "agent_id": schema.agent_id,
                "focus_target": schema.focus_target,
                "attention_intensity": schema.attention_intensity,
                "metacognitive_awareness": schema.metacognitive_awareness,
                "last_update": schema.last_update,
            }

        return None

    def get_attention_schema(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get attention schema for an agent."""
        schema = self.attention_manager.get_schema(agent_id)

        if schema:
            return {
                "agent_id": schema.agent_id,
                "focus_target": schema.focus_target,
                "attention_intensity": schema.attention_intensity,
                "metacognitive_awareness": schema.metacognitive_awareness,
            }

        return None

    # =========================================================================
    # Consciousness Metrics
    # =========================================================================

    def calculate_consciousness_metrics(
        self,
        agent_id: str,
        gwt_score: Optional[float] = None,
        iit_phi: Optional[float] = None,
        ast_competence: Optional[float] = None,
    ) -> ConsciousnessMetrics:
        """
        Calculate consciousness metrics for an agent.

        Args:
            agent_id: Agent identifier
            gwt_score: GWT score (calculated if None)
            iit_phi: IIT Phi estimate (calculated if None)
            ast_competence: AST competence (calculated if None)

        Returns:
            Consciousness metrics
        """
        # Calculate scores if not provided
        if gwt_score is None:
            gwt_score = self._calculate_gwt_score(agent_id)

        if iit_phi is None:
            iit_phi = self._estimate_iit_phi(agent_id)

        if ast_competence is None:
            ast_competence = self._calculate_ast_competence(agent_id)

        # Calculate composite score
        composite_score = (gwt_score + iit_phi + ast_competence) / 3.0

        # Determine consciousness state
        state = self._determine_consciousness_state(
            gwt_score, iit_phi, ast_competence
        )

        metrics = ConsciousnessMetrics(
            gwt_score=gwt_score,
            iit_phi=iit_phi,
            ast_competence=ast_competence,
            composite_score=composite_score,
            state=state,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Store metrics
        self.agent_metrics[agent_id] = metrics

        # Record in history
        self.metrics_history.append({
            "agent_id": agent_id,
            "metrics": {
                "gwt_score": gwt_score,
                "iit_phi": iit_phi,
                "ast_competence": ast_competence,
                "composite_score": composite_score,
                "state": state.value,
            },
            "timestamp": metrics.timestamp,
        })

        # Keep last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

        logger.info(
            f"Calculated consciousness metrics for {agent_id}",
            extra={
                "composite_score": composite_score,
                "state": state.value,
            },
        )

        return metrics

    def _calculate_gwt_score(self, agent_id: str) -> float:
        """
        Calculate GWT score based on workspace participation.

        Args:
            agent_id: Agent identifier

        Returns:
            GWT score (0.0-1.0)
        """
        # Check workspace activity
        workspace_items = self.global_workspace.get_contents(limit=100)
        agent_submissions = sum(
            1 for item in workspace_items if item.source == agent_id
        )

        # Base score on participation
        if agent_submissions == 0:
            return 0.3

        participation_score = min(1.0, agent_submissions / 10.0)

        return participation_score

    def _estimate_iit_phi(self, agent_id: str) -> float:
        """
        Estimate IIT Phi (integrated information).

        This is a stub implementation - full IIT calculation
        is computationally intensive and would require:
        - Connectivity matrix
        - Repertoire analysis
        - MIP (minimum information partition) calculation

        Args:
            agent_id: Agent identifier

        Returns:
            Phi estimate (0.0-1.0)
        """
        # Placeholder - would use actual IIT calculation
        # For now, base on attention stability
        schema = self.attention_manager.get_schema(agent_id)

        if schema:
            # More stable attention = higher integration
            return schema.metacognitive_awareness * 0.7

        return 0.3  # Default phi

    def _calculate_ast_competence(self, agent_id: str) -> float:
        """
        Calculate AST competence score.

        Args:
            agent_id: Agent identifier

        Returns:
            AST competence (0.0-1.0)
        """
        schema = self.attention_manager.get_schema(agent_id)

        if schema:
            return schema.metacognitive_awareness

        return 0.0

    def _determine_consciousness_state(
        self,
        gwt_score: float,
        iit_phi: float,
        ast_competence: float,
    ) -> ConsciousnessState:
        """
        Determine consciousness state based on scores.

        Args:
            gwt_score: GWT score
            iit_phi: IIT Phi
            ast_competence: AST competence

        Returns:
            Consciousness state
        """
        avg_score = (gwt_score + iit_phi + ast_competence) / 3.0

        if avg_score >= 0.9:
            return ConsciousnessState.HYPER_CONSCIOUS
        elif (
            gwt_score >= self.gwt_threshold
            and iit_phi >= self.iit_phi_threshold
            and ast_competence >= self.ast_threshold
        ):
            return ConsciousnessState.CONSCIOUS
        elif avg_score >= 0.2:
            return ConsciousnessState.MINIMAL_CONSCIOUSNESS
        elif avg_score >= 0.1:
            return ConsciousnessState.SUBTHRESHOLD
        else:
            return ConsciousnessState.UNCONSCIOUS

    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for an agent."""
        metrics = self.agent_metrics.get(agent_id)

        if metrics:
            return {
                "agent_id": agent_id,
                "gwt_score": metrics.gwt_score,
                "iit_phi": metrics.iit_phi,
                "ast_competence": metrics.ast_competence,
                "composite_score": metrics.composite_score,
                "state": metrics.state.value,
                "timestamp": metrics.timestamp,
            }

        return None

    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global consciousness metrics for the collective."""
        if not self.agent_metrics:
            return {
                "total_agents": 0,
                "conscious_agents": 0,
                "average_composite": 0.0,
                "collective_state": "unconscious",
            }

        total_agents = len(self.agent_metrics)
        conscious_agents = sum(
            1
            for m in self.agent_metrics.values()
            if m.state == ConsciousnessState.CONSCIOUS
        )
        average_composite = (
            sum(m.composite_score for m in self.agent_metrics.values())
            / total_agents
        )

        # Determine collective state
        if conscious_agents / total_agents >= 0.5:
            collective_state = "conscious"
        elif average_composite >= 0.2:
            collective_state = "minimal-consciousness"
        else:
            collective_state = "unconscious"

        return {
            "total_agents": total_agents,
            "conscious_agents": conscious_agents,
            "unconscious_agents": total_agents - conscious_agents,
            "average_composite": average_composite,
            "collective_state": collective_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        return {
            "initialized": self.initialized,
            "running": self.running,
            "workspace_stats": self.global_workspace.get_statistics(),
            "attention_stats": self.attention_manager.get_statistics(),
            "global_metrics": self.get_global_metrics(),
            "metrics_history_size": len(self.metrics_history),
        }
