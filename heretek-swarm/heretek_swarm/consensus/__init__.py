"""
Heretek Swarm Consensus Package

This package provides comprehensive consensus mechanisms for multi-agent decision making:
- MAKER (Multi-Agent Knowledge Extraction & Reasoning) consensus
- Enhanced MAKER with reasoning chains and rollback
- Swarm Deliberation Engine with multi-round voting
- Agent Expertise Profiling for confidence weighting
- Decision Audit Trail for complete追溯 ability
- Raft-based leader election
- Immune Response Building for pattern learning (CONS-02)
- Behavioral Baseline with quorum updates (CONS-03)

Core Features:
- First-to-ahead-by-k voting
- Reputation-weighted voting
- Red-flagging for anomalous outputs
- Multi-round deliberation with argument exchange
- Confidence-weighted voting based on expertise
- Dissent tracking and minority report preservation
- Complete decision provenance tracking
- Immune system for learning from anomaly responses
- Quorum-based baseline updates to prevent corruption
"""

from heretek_swarm.consensus.audit import (
    ArgumentRecord,
    ConsensusAuditTrail,
    DecisionOutcome,
    DecisionRecord,
    QueryResult,
    VoteRecord,
)
from heretek_swarm.consensus.expertise import (
    AgentExpertiseProfile,
    AgentExpertiseProfiler,
    DomainExpertise,
    ExpertiseLevel,
)
from heretek_swarm.consensus.immune import (
    ImmunePattern,
    ImmuneQuorum,
    ImmuneResponse,
    ImmuneResponseBuilding,
    NovelPatternPreservation,
    PatternClassification,
    ResponseOutcome,
)
from heretek_swarm.consensus.maker import (
    ConsensusResult,
    ConsensusState,
    MAKERConsensus,
    Vote,
)
from heretek_swarm.consensus.maker_enhanced import (
    DecisionProvenance,
    EnhancedMAKERConsensus,
    EnhancedVote,
    ReasoningChain,
    ReasoningChainStatus,
    ReasoningStep,
    RollbackResult,
)
from heretek_swarm.consensus.raft_election import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    LeaderState,
    LogEntry,
    MAKERConsensusWithRaft,
    RaftElection,
    RaftState,
    RequestVoteRequest,
    RequestVoteResponse,
)
from heretek_swarm.consensus.swarm_deliberation import (
    AgentPosition,
    Argument,
    DeliberationResult,
    DeliberationRound,
    DeliberationState,
    Position,
    SwarmDeliberationEngine,
)
from heretek_swarm.consensus.tribunal import (
    CaseStatus,
    EvidenceType,
    RulingType,
    Tribunal,
    TribunalCase,
    TribunalEvidence,
    TribunalRuling,
)

__all__ = [
    "AgentExpertiseProfile",
    # Expertise Profiling
    "AgentExpertiseProfiler",
    "AgentPosition",
    "AppendEntriesRequest",
    "AppendEntriesResponse",
    "Argument",
    "ArgumentRecord",
    # Audit Trail
    "ConsensusAuditTrail",
    "ConsensusResult",
    "ConsensusState",
    "DecisionOutcome",
    "DecisionProvenance",
    "DecisionRecord",
    "DeliberationResult",
    "DeliberationRound",
    "DeliberationState",
    "DomainExpertise",
    # Enhanced MAKER
    "EnhancedMAKERConsensus",
    "EnhancedVote",
    "ExpertiseLevel",
    # Immune Response Building (CONS-02)
    "ImmunePattern",
    "ImmuneQuorum",
    "ImmuneResponse",
    "ImmuneResponseBuilding",
    "LeaderState",
    "LogEntry",
    # Base MAKER
    "MAKERConsensus",
    "MAKERConsensusWithRaft",
    "NovelPatternPreservation",
    "PatternClassification",
    "Position",
    "QueryResult",
    # Raft Election
    "RaftElection",
    "RaftState",
    "ReasoningChain",
    "ReasoningChainStatus",
    "ReasoningStep",
    "RequestVoteRequest",
    "RequestVoteResponse",
    "ResponseOutcome",
    "RollbackResult",
    # Swarm Deliberation
    "SwarmDeliberationEngine",
    # Tribunal
    "CaseStatus",
    "EvidenceType",
    "RulingType",
    "Tribunal",
    "TribunalCase",
    "TribunalEvidence",
    "TribunalRuling",
    "Vote",
    "VoteRecord",
]
