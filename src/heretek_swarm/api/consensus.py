"""
Heretek Swarm Consensus API Endpoints

Provides HTTP endpoints for:
- Listing active consensus rounds
- Creating new consensus processes
- Submitting votes
- Retrieving consensus results

Uses MAKER (Multi-Agent Knowledge Extraction & Reasoning) consensus.
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
import structlog

from heretek_swarm.consensus import (
    MAKERConsensus,
    ConsensusState,
    ConsensusResult,
    Vote,
)

logger = structlog.get_logger("api.consensus")

# Create router
router = APIRouter(prefix="/api/consensus", tags=["consensus"])

# In-memory storage for consensus processes (use Redis in production)
_consensus_store: Dict[str, MAKERConsensus] = {}
_active_rounds: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# Consensus Round Endpoints
# =============================================================================

@router.get("")
async def get_active_consensus_rounds():
    """
    Get all active consensus rounds.
    
    Returns:
        List of active consensus rounds with their current state
    """
    active = []
    for round_id, data in _active_rounds.items():
        if data["state"] in [ConsensusState.GATHERING.value, ConsensusState.VOTING.value]:
            active.append({
                "id": round_id,
                "state": data["state"],
                "topic": data["topic"],
                "vote_count": len(data["votes"]),
                "created_at": data["created_at"],
                "deadline": data.get("deadline"),
            })
    
    return {"consensus_rounds": active, "total": len(active)}


@router.get("/history")
async def get_consensus_history(limit: int = 50):
    """
    Get completed consensus rounds history.
    
    Args:
        limit: Maximum number of results to return (default: 50)
        
    Returns:
        List of completed consensus results
    """
    completed = []
    for round_id, data in _active_rounds.items():
        if data["state"] == ConsensusState.COMPLETED.value:
            completed.append({
                "id": round_id,
                "topic": data["topic"],
                "decision": data.get("decision"),
                "confidence": data.get("confidence"),
                "vote_count": len(data["votes"]),
                "completed_at": data.get("completed_at"),
                "red_flags": data.get("red_flags", []),
            })
    
    # Sort by completion time, most recent first
    completed.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    
    return {
        "consensus_history": completed[:limit],
        "total": len(completed),
    }


@router.get("/{consensus_id}")
async def get_consensus_round(consensus_id: str):
    """
    Get details of a specific consensus round.
    
    Args:
        consensus_id: Unique consensus round identifier
        
    Returns:
        Consensus round details including all votes
    """
    if consensus_id not in _active_rounds:
        raise HTTPException(404, f"Consensus round {consensus_id} not found")
    
    data = _active_rounds[consensus_id]
    
    return {
        "id": consensus_id,
        "topic": data["topic"],
        "state": data["state"],
        "votes": data["votes"],
        "decision": data.get("decision"),
        "confidence": data.get("confidence"),
        "red_flags": data.get("red_flags", []),
        "created_at": data["created_at"],
        "completed_at": data.get("completed_at"),
        "metadata": data.get("metadata", {}),
    }


@router.post("")
async def create_consensus_round(topic: str, description: str = ""):
    """
    Create a new consensus round.
    
    Args:
        topic: The topic/question to reach consensus on
        description: Optional detailed description
        
    Returns:
        Created consensus round details
    """
    consensus_id = str(uuid4())
    
    # Create MAKER consensus instance
    ahead_by_k = int(os.environ.get("CONSENSUS_AHEAD_BY_K", "2"))
    min_votes = int(os.environ.get("CONSENSUS_MIN_VOTES", "3"))
    consensus = MAKERConsensus(ahead_by_k=ahead_by_k, min_votes=min_votes)
    
    # Store consensus instance
    _consensus_store[consensus_id] = consensus
    
    # Store round data
    _active_rounds[consensus_id] = {
        "id": consensus_id,
        "topic": topic,
        "description": description,
        "state": ConsensusState.GATHERING.value,
        "votes": [],
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {},
    }
    
    logger.info("Created consensus round", consensus_id=consensus_id, topic=topic)
    
    return {
        "id": consensus_id,
        "topic": topic,
        "description": description,
        "state": ConsensusState.GATHERING.value,
        "created_at": _active_rounds[consensus_id]["created_at"],
    }


@router.post("/{consensus_id}/vote")
async def submit_vote(
    consensus_id: str,
    agent_id: str,
    decision: str,
    confidence: float,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Submit a vote for a consensus round.
    
    Args:
        consensus_id: Unique consensus round identifier
        agent_id: Unique agent identifier submitting the vote
        decision: The agent's decision/answer
        confidence: Confidence level (0.0 to 1.0)
        metadata: Optional additional metadata
        
    Returns:
        Vote confirmation with current vote count
    """
    if consensus_id not in _active_rounds:
        raise HTTPException(404, f"Consensus round {consensus_id} not found")
    
    data = _active_rounds[consensus_id]
    
    # Check if consensus is still accepting votes
    if data["state"] in [ConsensusState.COMPLETED.value, ConsensusState.FAILED.value]:
        raise HTTPException(400, f"Consensus round {consensus_id} is already {data['state']}")
    
    # Validate confidence
    if not 0.0 <= confidence <= 1.0:
        raise HTTPException(400, "Confidence must be between 0.0 and 1.0")
    
    # Check for duplicate votes from same agent
    for vote in data["votes"]:
        if vote["agent_id"] == agent_id:
            raise HTTPException(400, f"Agent {agent_id} has already voted")
    
    # Create vote
    vote = Vote(
        agent_id=agent_id,
        decision=decision,
        confidence=confidence,
        timestamp=datetime.utcnow().isoformat(),
        metadata=metadata or {},
    )
    
    # Add to store
    data["votes"].append({
        "agent_id": vote.agent_id,
        "decision": vote.decision,
        "confidence": vote.confidence,
        "timestamp": vote.timestamp,
        "metadata": vote.metadata,
    })
    
    # Get consensus and process vote
    consensus = _consensus_store.get(consensus_id)
    if consensus:
        consensus.add_vote(consensus_id, agent_id, decision, confidence)
    
    # Transition state if enough votes
    if len(data["votes"]) >= int(os.environ.get("CONSENSUS_MIN_VOTES", "3")):
        data["state"] = ConsensusState.AGGREGATING.value
    
    logger.info(
        "Vote submitted",
        consensus_id=consensus_id,
        agent_id=agent_id,
        decision=decision,
        confidence=confidence,
    )
    
    return {
        "status": "vote_accepted",
        "consensus_id": consensus_id,
        "agent_id": agent_id,
        "vote_count": len(data["votes"]),
        "current_state": data["state"],
    }


@router.post("/{consensus_id}/aggregate")
async def aggregate_consensus(consensus_id: str):
    """
    Aggregate votes and determine consensus decision.
    
    Args:
        consensus_id: Unique consensus round identifier
        
    Returns:
        Aggregated consensus result
    """
    if consensus_id not in _active_rounds:
        raise HTTPException(404, f"Consensus round {consensus_id} not found")
    
    data = _active_rounds[consensus_id]
    
    if len(data["votes"]) == 0:
        raise HTTPException(400, "No votes to aggregate")
    
    # Get consensus instance
    consensus = _consensus_store.get(consensus_id)
    if not consensus:
        raise HTTPException(500, "Consensus instance not found")
    
    # Aggregate
    result = consensus.aggregate_consensus(consensus_id)
    
    # Update store
    data["state"] = result.state.value
    data["decision"] = result.decision
    data["confidence"] = result.confidence
    data["red_flags"] = result.red_flags
    data["completed_at"] = result.timestamp
    
    logger.info(
        "Consensus aggregated",
        consensus_id=consensus_id,
        decision=result.decision,
        confidence=result.confidence,
    )
    
    return {
        "id": consensus_id,
        "decision": result.decision,
        "confidence": result.confidence,
        "state": result.state.value,
        "votes": data["votes"],
        "red_flags": result.red_flags,
        "completed_at": result.timestamp,
    }


@router.get("/{consensus_id}/results")
async def get_consensus_results(consensus_id: str):
    """
    Get results of a completed consensus round.
    
    Args:
        consensus_id: Unique consensus round identifier
        
    Returns:
        Consensus result with decision and all votes
    """
    if consensus_id not in _active_rounds:
        raise HTTPException(404, f"Consensus round {consensus_id} not found")
    
    data = _active_rounds[consensus_id]
    
    if data["state"] != ConsensusState.COMPLETED.value:
        return {
            "id": consensus_id,
            "state": data["state"],
            "decision": None,
            "confidence": None,
            "message": "Consensus not yet completed",
        }
    
    return {
        "id": consensus_id,
        "topic": data["topic"],
        "decision": data.get("decision"),
        "confidence": data.get("confidence"),
        "state": data["state"],
        "votes": data["votes"],
        "red_flags": data.get("red_flags", []),
        "completed_at": data.get("completed_at"),
    }


@router.delete("/{consensus_id}")
async def cancel_consensus(consensus_id: str):
    """
    Cancel an active consensus round.
    
    Args:
        consensus_id: Unique consensus round identifier
        
    Returns:
        Cancellation confirmation
    """
    if consensus_id not in _active_rounds:
        raise HTTPException(404, f"Consensus round {consensus_id} not found")
    
    data = _active_rounds[consensus_id]
    data["state"] = ConsensusState.FAILED.value
    
    # Clean up consensus instance
    if consensus_id in _consensus_store:
        del _consensus_store[consensus_id]
    
    logger.info("Consensus cancelled", consensus_id=consensus_id)
    
    return {
        "status": "cancelled",
        "consensus_id": consensus_id,
    }


# =============================================================================
# Consensus Configuration
# =============================================================================

@router.get("/config")
async def get_consensus_config():
    """
    Get current consensus configuration.
    
    Returns:
        Consensus parameters
    """
    return {
        "ahead_by_k": int(os.environ.get("CONSENSUS_AHEAD_BY_K", "2")),
        "min_votes": int(os.environ.get("CONSENSUS_MIN_VOTES", "3")),
        "red_flag_threshold": float(os.environ.get("CONSENSUS_RED_FLAG_THRESHOLD", "0.3")),
        "voting_timeout_seconds": int(os.environ.get("CONSENSUS_VOTING_TIMEOUT", "300")),
    }


# Export router
__all__ = ["router"]