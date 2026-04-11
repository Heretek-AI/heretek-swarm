"""
Heretek Swarm Consensus Package

This package provides comprehensive consensus mechanisms for multi-agent decision making:
- MAKER (Multi-Agent Knowledge Extraction & Reasoning) consensus
- Enhanced MAKER with reasoning chains and rollback
- Swarm Deliberation Engine with multi-round voting
- Agent Expertise Profiling for confidence weighting
- Decision Audit Trail for complete追溯 ability
- Raft-based leader election

Core Features:
- First-to-ahead-by-k voting
- Reputation-weighted voting
- Red-flagging for anomalous outputs
- Multi-round deliberation with argument exchange
- Confidence-weighted voting based on expertise
- Dissent tracking and minority report preservation
- Complete decision provenance tracking
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

__all__ = [
    # Base MAKER
    "MAKERConsensus",
    "ConsensusState",
    "ConsensusResult",
    "Vote",
    # Enhanced MAKER
    "EnhancedMAKERConsensus",
    "EnhancedVote",
    "ReasoningChain",
    "ReasoningStep",
    "ReasoningChainStatus",
    "DecisionProvenance",
    "RollbackResult",
    # Swarm Deliberation
    "SwarmDeliberationEngine",
    "DeliberationState",
    "DeliberationRound",
    "DeliberationResult",
    "Position",
    "AgentPosition",
    "Argument",
    # Expertise Profiling
    "AgentExpertiseProfiler",
    "AgentExpertiseProfile",
    "DomainExpertise",
    "ExpertiseLevel",
    # Audit Trail
    "ConsensusAuditTrail",
    "DecisionOutcome",
    "DecisionRecord",
    "VoteRecord",
    "ArgumentRecord",
    "QueryResult",
    # Raft Election
    "RaftElection",
    "RaftState",
    "LeaderState",
    "LogEntry",
    "RequestVoteRequest",
    "RequestVoteResponse",
    "AppendEntriesRequest",
    "AppendEntriesResponse",
    "MAKERConsensusWithRaft",
]
