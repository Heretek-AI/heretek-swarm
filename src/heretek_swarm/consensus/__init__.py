"""
Heretek Swarm Consensus Package

This package provides consensus mechanisms for multi-agent decision making:
- MAKER (Multi-Agent Knowledge Extraction & Reasoning) consensus
- First-to-ahead-by-k voting
- Reputation-weighted voting
- Red-flagging for anomalous outputs
"""

from heretek_swarm.consensus.maker import (
    ConsensusResult,
    ConsensusState,
    MAKERConsensus,
    Vote,
)

__all__ = [
    "MAKERConsensus",
    "ConsensusState",
    "ConsensusResult",
    "Vote",
]
