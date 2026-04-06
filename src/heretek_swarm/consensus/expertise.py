"""
Agent Expertise Profiling - Dynamic expertise scoring for consensus weighting.

This module provides comprehensive agent expertise tracking and calibration:
- Dynamic expertise scoring per domain
- Historical accuracy tracking
- Confidence calibration
- Expertise-based vote weighting

The expertise system enables more informed consensus decisions by weighting
agent votes based on their demonstrated expertise in relevant domains.

Example:
    ```python
    from heretek_swarm.consensus.expertise import AgentExpertiseProfiler

    # Initialize profiler
    profiler = AgentExpertiseProfiler()

    # Register agent with initial expertise
    profiler.register_agent("agent-1", domains=["code_review", "security"])

    # Record decision outcome
    profiler.record_outcome(
        agent_id="agent-1",
        domain="code_review",
        was_correct=True,
        confidence=0.9
    )

    # Get expertise-weighted confidence
    weighted_confidence = profiler.get_weighted_confidence(
        agent_id="agent-1",
        domain="code_review",
        base_confidence=0.85
    )
    ```
"""

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger("AgentExpertiseProfiler")


class ExpertiseLevel(Enum):
    """Expertise level classifications."""

    NOVICE = "novice"  # 0.0 - 0.3
    INTERMEDIATE = "intermediate"  # 0.3 - 0.6
    EXPERT = "expert"  # 0.6 - 0.85
    MASTER = "master"  # 0.85 - 1.0


@dataclass
class DomainExpertise:
    """
    Expertise tracking for a specific domain.

    Attributes:
        domain: Domain name
        expertise_score: Current expertise score (0.0 to 1.0)
        total_decisions: Total decisions made in this domain
        correct_decisions: Number of correct decisions
        avg_confidence: Average confidence in this domain
        confidence_calibration: How well confidence matches accuracy
        last_updated: Last update timestamp
        recent_outcomes: Recent outcome history for trend analysis
    """

    domain: str
    expertise_score: float = 0.5
    total_decisions: int = 0
    correct_decisions: int = 0
    avg_confidence: float = 0.5
    confidence_calibration: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    recent_outcomes: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate expertise score range."""
        self.expertise_score = max(0.0, min(1.0, self.expertise_score))
        self.avg_confidence = max(0.0, min(1.0, self.avg_confidence))
        self.confidence_calibration = max(-1.0, min(1.0, self.confidence_calibration))

    @property
    def accuracy(self) -> float:
        """Calculate accuracy rate."""
        if self.total_decisions == 0:
            return 0.5
        return self.correct_decisions / self.total_decisions

    @property
    def expertise_level(self) -> ExpertiseLevel:
        """Determine expertise level from score."""
        if self.expertise_score >= 0.85:
            return ExpertiseLevel.MASTER
        elif self.expertise_score >= 0.6:
            return ExpertiseLevel.EXPERT
        elif self.expertise_score >= 0.3:
            return ExpertiseLevel.INTERMEDIATE
        else:
            return ExpertiseLevel.NOVICE

    def get_expertise_multiplier(self) -> float:
        """
        Get expertise multiplier for vote weighting.

        Returns:
            Multiplier value (0.5 to 1.5)
        """
        # Map expertise score to multiplier range [0.5, 1.5]
        return 0.5 + (self.expertise_score * 1.0)


@dataclass
class AgentExpertiseProfile:
    """
    Complete expertise profile for an agent.

    Attributes:
        agent_id: Agent identifier
        domains: Dictionary of domain expertise
        overall_reputation: Overall reputation score
        total_decisions: Total decisions across all domains
        created_at: Profile creation timestamp
        last_active: Last activity timestamp
    """

    agent_id: str
    domains: Dict[str, DomainExpertise] = field(default_factory=dict)
    overall_reputation: float = 0.5
    total_decisions: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_active: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def get_expertise_for_domain(self, domain: str) -> DomainExpertise:
        """Get expertise for a specific domain, creating if needed."""
        if domain not in self.domains:
            self.domains[domain] = DomainExpertise(domain=domain)
        return self.domains[domain]

    def get_domains(self) -> List[str]:
        """Get list of domains with expertise."""
        return list(self.domains.keys())

    def get_primary_domain(self) -> Optional[str]:
        """Get agent's primary (highest expertise) domain."""
        if not self.domains:
            return None
        return max(self.domains.items(), key=lambda x: x[1].expertise_score)[0]


class AgentExpertiseProfiler:
    """
    Agent Expertise Profiler for consensus weighting.

    Provides comprehensive expertise tracking and calibration:
    - Dynamic expertise scoring per domain
    - Historical accuracy tracking
    - Confidence calibration
    - Expertise-based vote weighting

    The profiler tracks agent performance across multiple domains,
    adjusting expertise scores based on decision outcomes and
    confidence calibration.

    Attributes:
        profiles: Dictionary of agent profiles
        domain_statistics: Global statistics per domain
        calibration_window: Number of recent outcomes for calibration
    """

    def __init__(self, calibration_window: int = 20) -> None:
        """
        Initialize the expertise profiler.

        Args:
            calibration_window: Number of recent outcomes for calibration
        """
        self.profiles: Dict[str, AgentExpertiseProfile] = {}
        self.domain_statistics: Dict[str, Dict[str, Any]] = {}
        self.calibration_window = calibration_window

        logger.info(
            f"AgentExpertiseProfiler initialized with calibration_window={calibration_window}"
        )

    def register_agent(
        self,
        agent_id: str,
        domains: Optional[List[str]] = None,
        initial_expertise: float = 0.5,
    ) -> AgentExpertiseProfile:
        """
        Register a new agent with optional initial domains.

        Args:
            agent_id: Unique agent identifier
            domains: List of domains the agent specializes in
            initial_expertise: Initial expertise score (0.0 to 1.0)

        Returns:
            Created agent profile
        """
        if agent_id in self.profiles:
            logger.warning(f"Agent {agent_id} already registered, updating domains")
            profile = self.profiles[agent_id]
            if domains:
                for domain in domains:
                    if domain not in profile.domains:
                        profile.domains[domain] = DomainExpertise(
                            domain=domain, expertise_score=initial_expertise
                        )
            return profile

        profile = AgentExpertiseProfile(agent_id=agent_id)
        if domains:
            for domain in domains:
                profile.domains[domain] = DomainExpertise(
                    domain=domain, expertise_score=initial_expertise
                )

        self.profiles[agent_id] = profile
        logger.info(
            f"Registered agent {agent_id} with domains: {domains or 'none'}"
        )
        return profile

    def record_outcome(
        self,
        agent_id: str,
        domain: str,
        was_correct: bool,
        confidence: float,
        decision_outcome: Optional[Any] = None,
    ) -> None:
        """
        Record a decision outcome for expertise tracking.

        Args:
            agent_id: Agent identifier
            domain: Domain of the decision
            was_correct: Whether the decision was correct
            confidence: Agent's confidence in the decision
            decision_outcome: Optional actual outcome data
        """
        if agent_id not in self.profiles:
            self.register_agent(agent_id, [domain])

        profile = self.profiles[agent_id]
        domain_expertise = profile.get_expertise_for_domain(domain)

        # Update domain statistics
        domain_expertise.total_decisions += 1
        if was_correct:
            domain_expertise.correct_decisions += 1

        # Update average confidence
        n = domain_expertise.total_decisions
        domain_expertise.avg_confidence = (
            (domain_expertise.avg_confidence * (n - 1) + confidence) / n
        )

        # Record recent outcome for trend analysis
        outcome_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "was_correct": was_correct,
            "confidence": confidence,
            "outcome": decision_outcome,
        }
        domain_expertise.recent_outcomes.append(outcome_record)

        # Keep only recent outcomes within calibration window
        if len(domain_expertise.recent_outcomes) > self.calibration_window:
            domain_expertise.recent_outcomes = domain_expertise.recent_outcomes[
                -self.calibration_window :
            ]

        # Update expertise score
        domain_expertise.expertise_score = self._calculate_expertise_score(
            domain_expertise
        )

        # Update confidence calibration
        domain_expertise.confidence_calibration = (
            self._calculate_confidence_calibration(domain_expertise)
        )

        # Update overall reputation
        profile.overall_reputation = self._calculate_overall_reputation(profile)
        profile.total_decisions += 1
        profile.last_active = datetime.now(timezone.utc).isoformat()

        # Update global domain statistics
        self._update_domain_statistics(domain, was_correct, confidence)

        logger.debug(
            f"Recorded outcome for {agent_id} in {domain}: "
            f"correct={was_correct}, confidence={confidence:.2f}, "
            f"new_expertise={domain_expertise.expertise_score:.2f}"
        )

    def _calculate_expertise_score(
        self, domain_expertise: DomainExpertise
    ) -> float:
        """
        Calculate expertise score based on accuracy and recency.

        Args:
            domain_expertise: Domain expertise data

        Returns:
            Calculated expertise score (0.0 to 1.0)
        """
        if domain_expertise.total_decisions == 0:
            return 0.5

        # Base accuracy
        accuracy = domain_expertise.accuracy

        # Recency weight - recent outcomes matter more
        recent_outcomes = domain_expertise.recent_outcomes
        if recent_outcomes:
            recent_accuracy = sum(
                1 for o in recent_outcomes if o["was_correct"]
            ) / len(recent_outcomes)
            # Weight recent performance 60%, historical 40%
            accuracy = 0.4 * accuracy + 0.6 * recent_accuracy

        # Experience bonus - more decisions increase confidence in score
        experience_factor = min(
            1.0, domain_expertise.total_decisions / self.calibration_window
        )

        # Final score with experience factor
        score = 0.5 + (accuracy - 0.5) * experience_factor

        return max(0.0, min(1.0, score))

    def _calculate_confidence_calibration(
        self, domain_expertise: DomainExpertise
    ) -> float:
        """
        Calculate how well agent's confidence matches actual accuracy.

        Positive values indicate good calibration (confidence matches accuracy).
        Negative values indicate overconfidence or underconfidence.

        Args:
            domain_expertise: Domain expertise data

        Returns:
            Calibration score (-1.0 to 1.0)
        """
        recent_outcomes = domain_expertise.recent_outcomes
        if len(recent_outcomes) < 3:
            return 0.0  # Not enough data

        # Calculate average confidence and accuracy for recent outcomes
        avg_confidence = statistics.mean(o["confidence"] for o in recent_outcomes)
        recent_accuracy = sum(
            1 for o in recent_outcomes if o["was_correct"]
        ) / len(recent_outcomes)

        # Calibration = 1 - |confidence - accuracy|
        # Perfect calibration when confidence equals accuracy
        calibration = 1.0 - abs(avg_confidence - recent_accuracy)

        # Scale to -1.0 to 1.0 range
        # Positive when well-calibrated, negative when poorly calibrated
        if calibration > 0.5:
            return calibration * 2 - 1.0
        else:
            return calibration * 2

    def _calculate_overall_reputation(
        self, profile: AgentExpertiseProfile
    ) -> float:
        """
        Calculate overall reputation from domain expertise.

        Args:
            profile: Agent expertise profile

        Returns:
            Overall reputation score (0.0 to 1.0)
        """
        if not profile.domains:
            return 0.5

        # Weighted average of domain expertise
        total_weight = 0
        weighted_sum = 0.0

        for domain_expertise in profile.domains.values():
            # Weight by number of decisions (more experience = more weight)
            weight = max(1, domain_expertise.total_decisions)
            weighted_sum += domain_expertise.expertise_score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _update_domain_statistics(
        self, domain: str, was_correct: bool, confidence: float
    ) -> None:
        """
        Update global domain statistics.

        Args:
            domain: Domain name
            was_correct: Whether decision was correct
            confidence: Decision confidence
        """
        if domain not in self.domain_statistics:
            self.domain_statistics[domain] = {
                "total_decisions": 0,
                "correct_decisions": 0,
                "avg_confidence": 0.0,
                "participating_agents": set(),
            }

        stats = self.domain_statistics[domain]
        stats["total_decisions"] += 1
        if was_correct:
            stats["correct_decisions"] += 1

        # Update average confidence
        n = stats["total_decisions"]
        stats["avg_confidence"] = (stats["avg_confidence"] * (n - 1) + confidence) / n

    def get_weighted_confidence(
        self,
        agent_id: str,
        domain: str,
        base_confidence: float,
    ) -> float:
        """
        Get expertise-weighted confidence for an agent's vote.

        Args:
            agent_id: Agent identifier
            domain: Domain of the decision
            base_confidence: Agent's stated confidence

        Returns:
            Weighted confidence (0.0 to 1.0)
        """
        if agent_id not in self.profiles:
            return base_confidence  # No profile, use base confidence

        profile = self.profiles[agent_id]
        domain_expertise = profile.get_expertise_for_domain(domain)

        # Get expertise multiplier
        multiplier = domain_expertise.get_expertise_multiplier()

        # Apply multiplier to base confidence
        weighted_confidence = base_confidence * multiplier

        # Adjust based on confidence calibration
        calibration_factor = 1.0 + (domain_expertise.confidence_calibration * 0.2)
        weighted_confidence *= calibration_factor

        # Ensure valid range
        return max(0.0, min(1.0, weighted_confidence))

    def get_expertise_score(
        self,
        agent_id: str,
        domain: Optional[str] = None,
    ) -> float:
        """
        Get expertise score for an agent.

        Args:
            agent_id: Agent identifier
            domain: Optional specific domain (uses overall if None)

        Returns:
            Expertise score (0.0 to 1.0)
        """
        if agent_id not in self.profiles:
            return 0.5  # Default for unknown agents

        profile = self.profiles[agent_id]

        if domain:
            domain_expertise = profile.get_expertise_for_domain(domain)
            return domain_expertise.expertise_score
        else:
            return profile.overall_reputation

    def get_expertise_level(
        self,
        agent_id: str,
        domain: str,
    ) -> ExpertiseLevel:
        """
        Get expertise level classification for an agent in a domain.

        Args:
            agent_id: Agent identifier
            domain: Domain name

        Returns:
            Expertise level enum value
        """
        if agent_id not in self.profiles:
            return ExpertiseLevel.NOVICE

        profile = self.profiles[agent_id]
        domain_expertise = profile.get_expertise_for_domain(domain)
        return domain_expertise.expertise_level

    def get_agent_domains(self, agent_id: str) -> List[str]:
        """
        Get list of domains where agent has expertise.

        Args:
            agent_id: Agent identifier

        Returns:
            List of domain names
        """
        if agent_id not in self.profiles:
            return []

        return self.profiles[agent_id].get_domains()

    def get_domain_experts(
        self,
        domain: str,
        min_expertise: float = 0.6,
    ) -> List[Tuple[str, float]]:
        """
        Get list of experts in a specific domain.

        Args:
            domain: Domain name
            min_expertise: Minimum expertise score threshold

        Returns:
            List of (agent_id, expertise_score) tuples sorted by expertise
        """
        experts = []

        for agent_id, profile in self.profiles.items():
            if domain in profile.domains:
                expertise = profile.domains[domain].expertise_score
                if expertise >= min_expertise:
                    experts.append((agent_id, expertise))

        # Sort by expertise descending
        return sorted(experts, key=lambda x: x[1], reverse=True)

    def get_reputation_weight(self, agent_id: str) -> float:
        """
        Get reputation weight for consensus voting.

        Args:
            agent_id: Agent identifier

        Returns:
            Reputation weight (0.0 to 1.0)
        """
        if agent_id not in self.profiles:
            return 0.5  # Default weight for unknown agents

        return self.profiles[agent_id].overall_reputation

    def get_profile(self, agent_id: str) -> Optional[AgentExpertiseProfile]:
        """
        Get complete expertise profile for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent expertise profile or None
        """
        return self.profiles.get(agent_id)

    def get_domain_statistics(self, domain: str) -> Dict[str, Any]:
        """
        Get statistics for a specific domain.

        Args:
            domain: Domain name

        Returns:
            Domain statistics dictionary
        """
        if domain not in self.domain_statistics:
            return {
                "total_decisions": 0,
                "correct_decisions": 0,
                "accuracy": 0.5,
                "avg_confidence": 0.0,
                "participating_agents": 0,
            }

        stats = self.domain_statistics[domain]
        return {
            "total_decisions": stats["total_decisions"],
            "correct_decisions": stats["correct_decisions"],
            "accuracy": (
                stats["correct_decisions"] / stats["total_decisions"]
                if stats["total_decisions"] > 0
                else 0.5
            ),
            "avg_confidence": stats["avg_confidence"],
            "participating_agents": len(stats["participating_agents"]),
        }

    def get_all_profiles(self) -> Dict[str, AgentExpertiseProfile]:
        """
        Get all agent profiles.

        Returns:
            Dictionary of all agent profiles
        """
        return self.profiles.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get profiler statistics.

        Returns:
            Statistics dictionary
        """
        total_agents = len(self.profiles)
        total_domains = len(self.domain_statistics)

        # Calculate average expertise across all agents
        all_expertise = []
        for profile in self.profiles.values():
            all_expertise.append(profile.overall_reputation)

        avg_expertise = (
            statistics.mean(all_expertise) if all_expertise else 0.5
        )

        return {
            "total_agents": total_agents,
            "total_domains": total_domains,
            "avg_expertise": avg_expertise,
            "calibration_window": self.calibration_window,
        }

    def export_profile(self, agent_id: str) -> Dict[str, Any]:
        """
        Export agent profile for serialization.

        Args:
            agent_id: Agent identifier

        Returns:
            Serializable profile dictionary
        """
        if agent_id not in self.profiles:
            return {}

        profile = self.profiles[agent_id]
        return {
            "agent_id": profile.agent_id,
            "overall_reputation": profile.overall_reputation,
            "total_decisions": profile.total_decisions,
            "created_at": profile.created_at,
            "last_active": profile.last_active,
            "domains": {
                domain: {
                    "expertise_score": de.expertise_score,
                    "expertise_level": de.expertise_level.value,
                    "total_decisions": de.total_decisions,
                    "correct_decisions": de.correct_decisions,
                    "accuracy": de.accuracy,
                    "avg_confidence": de.avg_confidence,
                    "confidence_calibration": de.confidence_calibration,
                }
                for domain, de in profile.domains.items()
            },
        }

    def reset_agent_expertise(
        self,
        agent_id: str,
        domain: Optional[str] = None,
        reset_value: float = 0.5,
    ) -> None:
        """
        Reset agent expertise scores.

        Args:
            agent_id: Agent identifier
            domain: Optional specific domain (resets all if None)
            reset_value: Value to reset to
        """
        if agent_id not in self.profiles:
            return

        profile = self.profiles[agent_id]

        if domain:
            if domain in profile.domains:
                profile.domains[domain].expertise_score = reset_value
                profile.domains[domain].recent_outcomes = []
                logger.info(f"Reset expertise for {agent_id} in {domain}")
        else:
            for domain_expertise in profile.domains.values():
                domain_expertise.expertise_score = reset_value
                domain_expertise.recent_outcomes = []
            profile.overall_reputation = reset_value
            logger.info(f"Reset all expertise for {agent_id}")
