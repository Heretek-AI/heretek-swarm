"""
Heretek Swarm Consensus API Endpoints

Provides HTTP endpoints for:
- Listing active consensus rounds
- Creating new consensus processes
- Submitting votes
- Retrieving consensus results

Uses MAKER (Multi-Agent Knowledge Extraction & Reasoning) consensus.

SECURITY: All endpoints require authentication. Agent identity verification required for voting.
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from heretek_swarm.consensus import (
    MAKERConsensus,
    ConsensusState,
    ConsensusResult,
    Vote,
)

logger = structlog.get_logger("api.consensus")

# =============================================================================
# Authentication Configuration
# =============================================================================

security = HTTPBearer(auto_error=False)

class ConsensusAuthManager:
    """Manages authentication for consensus operations."""
    
    def __init__(self):
        self._valid_tokens: Dict[str, Dict[str, Any]] = {}
        self._token_expiry = timedelta(hours=24)
        self._agent_permissions: Dict[str, List[str]] = {}  # agent_id -> allowed operations
    
    def generate_token(self, agent_id: str, permissions: Optional[List[str]] = None) -> str:
        """Generate an authentication token for an agent."""
        token = secrets.token_urlsafe(32)
        self._valid_tokens[token] = {
            "agent_id": agent_id,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + self._token_expiry,
        }
        self._agent_permissions[agent_id] = permissions or ["vote", "create", "view"]
        return token
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate an authentication token.
        
        Returns:
            Tuple of (is_valid, agent_id, error_message)
        """
        if not token:
            return False, None, "Token required"
        
        if token not in self._valid_tokens:
            return False, None, "Invalid token"
        
        token_data = self._valid_tokens[token]
        if datetime.now(timezone.utc) > token_data["expires_at"]:
            del self._valid_tokens[token]
            return False, None, "Token expired"
        
        return True, token_data["agent_id"], None
    
    def check_permission(self, agent_id: str, operation: str) -> bool:
        """Check if agent has permission for operation."""
        permissions = self._agent_permissions.get(agent_id, [])
        return operation in permissions
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        if token in self._valid_tokens:
            agent_id = self._valid_tokens[token]["agent_id"]
            del self._valid_tokens[token]
            if agent_id in self._agent_permissions:
                del self._agent_permissions[agent_id]
            return True
        return False


# Global auth manager instance
consensus_auth_manager = ConsensusAuthManager()


async def get_authenticated_agent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_agent_id: Optional[str] = Header(None, description="Agent ID header"),
) -> str:
    """
    Dependency to authenticate agent for consensus operations.
    
    Returns:
        Authenticated agent ID
    
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(401, "Authentication required. Provide Bearer token.")
    
    token = credentials.credentials
    is_valid, agent_id, error = consensus_auth_manager.validate_token(token)
    
    if not is_valid:
        raise HTTPException(401, f"Authentication failed: {error}")
    
    # Verify agent ID matches if provided in header
    if x_agent_id and x_agent_id != agent_id:
        raise HTTPException(403, "Agent ID mismatch. Token does not match provided agent ID.")
    
    return agent_id


# Create router
router = APIRouter(prefix="/api/consensus", tags=["consensus"])

# In-memory storage for consensus processes (use Redis in production)
_consensus_store: Dict[str, MAKERConsensus] = {}
_active_rounds: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# Consensus Round Endpoints
# =============================================================================

@router.get("")
async def get_active_consensus_rounds(
    agent_id: str = Depends(get_authenticated_agent)
):
    """
    Get all active consensus rounds.
    
    SECURITY: Requires authentication.
    
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
async def get_consensus_history(
    limit: int = 50,
    agent_id: str = Depends(get_authenticated_agent)
):
    """
    Get completed consensus rounds history.
    
    SECURITY: Requires authentication.
    
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
async def get_consensus_round(
    consensus_id: str,
    agent_id: str = Depends(get_authenticated_agent)
):
    """
    Get details of a specific consensus round.
    
    SECURITY: Requires authentication.
    
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
async def create_consensus_round(
    topic: str,
    description: str = "",
    agent_id: str = Depends(get_authenticated_agent)
):
    """
    Create a new consensus round.
    
    SECURITY: Requires authentication with 'create' permission.
    
    Args:
        topic: The topic/question to reach consensus on
        description: Optional detailed description
        
    Returns:
        Created consensus round details
    """
    # Check permission
    if not consensus_auth_manager.check_permission(agent_id, "create"):
        raise HTTPException(403, "Permission denied. Agent cannot create consensus rounds.")
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
        "created_at": datetime.now(timezone.utc).isoformat(),
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
    decision: str,
    confidence: float,
    metadata: Optional[Dict[str, Any]] = None,
    authenticated_agent_id: str = Depends(get_authenticated_agent),
    x_agent_id: Optional[str] = Header(None, description="Agent ID header"),
):
    """
    Submit a vote for a consensus round.
    
    SECURITY: Requires authentication. Agent identity verified via token.
    
    Args:
        consensus_id: Unique consensus round identifier
        decision: The agent's decision/answer
        confidence: Confidence level (0.0 to 1.0)
        metadata: Optional additional metadata
        x_agent_id: Agent ID (must match authenticated token)
        
    Returns:
        Vote confirmation with current vote count
    """
    # Use authenticated agent ID
    agent_id = x_agent_id or authenticated_agent_id
    
    # Check permission
    if not consensus_auth_manager.check_permission(authenticated_agent_id, "vote"):
        raise HTTPException(403, "Permission denied. Agent cannot vote.")
    
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
        timestamp=datetime.now(timezone.utc).isoformat(),
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
async def aggregate_consensus(
    consensus_id: str,
    agent_id: str = Depends(get_authenticated_agent)
):
    """
    Aggregate votes and determine consensus decision.
    
    SECURITY: Requires authentication with 'create' permission.
    
    Args:
        consensus_id: Unique consensus round identifier
        
    Returns:
        Aggregated consensus result
    """
    # Check permission
    if not consensus_auth_manager.check_permission(agent_id, "create"):
        raise HTTPException(403, "Permission denied. Agent cannot aggregate consensus.")
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
async def cancel_consensus(
    consensus_id: str,
    agent_id: str = Depends(get_authenticated_agent)
):
    """
    Cancel an active consensus round.
    
    SECURITY: Requires authentication with 'create' permission.
    
    Args:
        consensus_id: Unique consensus round identifier
        
    Returns:
        Cancellation confirmation
    """
    # Check permission
    if not consensus_auth_manager.check_permission(agent_id, "create"):
        raise HTTPException(403, "Permission denied. Agent cannot cancel consensus.")
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
async def get_consensus_config(
    agent_id: str = Depends(get_authenticated_agent)
):
    """
    Get current consensus configuration.
    
    SECURITY: Requires authentication.
    
    Returns:
        Consensus parameters
    """
    return {
        "ahead_by_k": int(os.environ.get("CONSENSUS_AHEAD_BY_K", "2")),
        "min_votes": int(os.environ.get("CONSENSUS_MIN_VOTES", "3")),
        "red_flag_threshold": float(os.environ.get("CONSENSUS_RED_FLAG_THRESHOLD", "0.3")),
        "voting_timeout_seconds": int(os.environ.get("CONSENSUS_VOTING_TIMEOUT", "300")),
    }


# Auth token generation endpoint
@router.post("/auth/token")
async def generate_auth_token(agent_id: str, permissions: Optional[List[str]] = None):
    """
    Generate an authentication token for an agent.
    
    Args:
        agent_id: Agent identifier
        permissions: List of allowed operations (vote, create, view)
        
    Returns:
        Generated token
    """
    token = consensus_auth_manager.generate_token(agent_id, permissions)
    return {
        "token": token,
        "agent_id": agent_id,
        "permissions": permissions or ["vote", "create", "view"],
    }


# Token revocation endpoint
@router.post("/auth/revoke")
async def revoke_auth_token(token: str):
    """
    Revoke an authentication token.
    
    Args:
        token: Token to revoke
        
    Returns:
        Revocation confirmation
    """
    success = consensus_auth_manager.revoke_token(token)
    return {
        "revoked": success,
    }


# Export router
__all__ = ["router"]