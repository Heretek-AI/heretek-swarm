"""
Example Python-native tools for Heretek Swarm

Demonstrates migration patterns from legacy shell scripts to
type-safe, Python-native Swarms tools.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .base import BaseTool, SimpleTool, ToolContext


# ============================================================================
# Example 1: Memory Search Tool (migrated from knowledge-retrieval shell script)
# ============================================================================

class MemorySearchInput(BaseModel):
    """Input for memory search tool"""
    query: str = Field(..., description="Search query")
    agent_id: Optional[str] = Field(None, description="Filter by agent")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    include_embeddings: bool = Field(default=False, description="Include embeddings")


class MemorySearchOutput(BaseModel):
    """Output from memory search tool"""
    results: List[Dict] = Field(default_factory=list, description="Search results")
    total_count: int = Field(..., description="Total matching count")
    query_time_ms: float = Field(..., description="Query execution time")


class MemorySearchTool(BaseTool[MemorySearchInput, MemorySearchOutput]):
    """
    Search persistent and ephemeral memory.
    
    Migrated from: knowledge-retrieval shell script
    Improvements:
    - Type-safe inputs/outputs
    - Async execution
    - Performance monitoring
    - Integration with dual-tier memory
    """
    
    def __init__(self):
        super().__init__(
            name="memory_search",
            description="Search across persistent and ephemeral memory with semantic search",
            category="memory",
            tags=["search", "memory", "retrieval"],
            requires_memory=True
        )
    
    async def execute(
        self,
        input_data: MemorySearchInput,
        context: ToolContext
    ) -> MemorySearchOutput:
        """Execute memory search"""
        start_time = datetime.now(timezone.utc)
        
        # Placeholder implementation
        # In production, this would integrate with the DualTierMemorySystem
        results = []
        
        # Simulate search
        await asyncio.sleep(0.01)  # Simulate query time
        
        query_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return MemorySearchOutput(
            results=results,
            total_count=len(results),
            query_time_ms=query_time_ms
        )


# ============================================================================
# Example 2: Health Check Tool (migrated from healthcheck shell script)
# ============================================================================

class HealthCheckInput(BaseModel):
    """Input for health check tool"""
    services: Optional[List[str]] = Field(None, description="Services to check")
    include_details: bool = Field(default=False, description="Include detailed status")


class ServiceStatus(BaseModel):
    """Status of a service"""
    name: str
    healthy: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class HealthCheckOutput(BaseModel):
    """Output from health check tool"""
    overall_healthy: bool = Field(..., description="Overall system health")
    services: List[ServiceStatus] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthCheckTool(BaseTool[HealthCheckInput, HealthCheckOutput]):
    """
    Check system health across multiple services.
    
    Migrated from: healthcheck shell script
    Improvements:
    - Parallel health checks
    - Detailed latency metrics
    - Structured output
    """
    
    def __init__(self):
        super().__init__(
            name="health_check",
            description="Check health of system services (Redis, PostgreSQL, LiteLLM, etc)",
            category="system",
            tags=["health", "monitoring", "diagnostics"]
        )
    
    async def execute(
        self,
        input_data: HealthCheckInput,
        context: ToolContext
    ) -> HealthCheckOutput:
        """Execute health checks"""
        services = input_data.services or ["redis", "postgres", "litellm"]
        
        results = []
        overall_healthy = True
        
        for service in services:
            status = await self._check_service(service)
            results.append(status)
            
            if not status.healthy:
                overall_healthy = False
        
        return HealthCheckOutput(
            overall_healthy=overall_healthy,
            services=results
        )
    
    async def _check_service(self, service: str) -> ServiceStatus:
        """Check individual service health"""
        import asyncio
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Simulate health check
            await asyncio.sleep(0.01)
            
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            return ServiceStatus(
                name=service,
                healthy=True,
                latency_ms=latency_ms
            )
        except Exception as e:
            return ServiceStatus(
                name=service,
                healthy=False,
                error=str(e)
            )


# ============================================================================
# Example 3: Consensus Vote Tool (migrated from failover-vote shell script)
# ============================================================================

class ConsensusVoteInput(BaseModel):
    """Input for consensus vote tool"""
    proposal_id: str = Field(..., description="Proposal identifier")
    vote: str = Field(..., description="Vote value (yes/no/abstain)")
    agent_id: str = Field(..., description="Voting agent ID")
    justification: Optional[str] = Field(None, description="Vote justification")


class ConsensusVoteOutput(BaseModel):
    """Output from consensus vote tool"""
    vote_recorded: bool = Field(..., description="Whether vote was recorded")
    vote_id: str = Field(..., description="Vote record ID")
    quorum_reached: bool = Field(..., description="Whether quorum is reached")
    current_tally: Dict[str, int] = Field(default_factory=dict, description="Vote tally")


class ConsensusVoteTool(BaseTool[ConsensusVoteInput, ConsensusVoteOutput]):
    """
    Record votes in consensus decisions.
    
    Migrated from: failover-vote shell script
    Improvements:
    - Type-safe vote recording
    - Real-time quorum tracking
    - Vote justification storage
    """
    
    def __init__(self):
        super().__init__(
            name="consensus_vote",
            description="Record votes in consensus-based decisions with BFT protocol",
            category="governance",
            tags=["consensus", "voting", "governance", "bft"]
        )
    
    async def execute(
        self,
        input_data: ConsensusVoteInput,
        context: ToolContext
    ) -> ConsensusVoteOutput:
        """Record a consensus vote"""
        import uuid
        
        # Validate vote
        if input_data.vote not in ["yes", "no", "abstain"]:
            raise ValueError(f"Invalid vote: {input_data.vote}")
        
        # Record vote (placeholder)
        vote_id = str(uuid.uuid4())
        
        # Simulate vote tally
        tally = {"yes": 5, "no": 2, "abstain": 1}
        quorum_reached = sum(tally.values()) >= 7
        
        return ConsensusVoteOutput(
            vote_recorded=True,
            vote_id=vote_id,
            quorum_reached=quorum_reached,
            current_tally=tally
        )


# ============================================================================
# Example 4: Legacy Wrapper Tool (for gradual migration)
# ============================================================================

class LegacyWrapperTool(SimpleTool):
    """
    Wrapper for legacy shell scripts during migration.
    
    Allows gradual migration while maintaining compatibility.
    """
    
    def __init__(
        self,
        name: str,
        script_path: str,
        description: str,
        category: str = "legacy"
    ):
        import subprocess
        
        async def execute_shell(**kwargs):
            """Execute shell script with arguments"""
            import asyncio
            
            cmd = [script_path]
            for key, value in kwargs.items():
                cmd.extend([f"--{key}", str(value)])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode(),
                "error": stderr.decode(),
                "returncode": process.returncode
            }
        
        super().__init__(
            name=name,
            description=description,
            func=execute_shell,
            category=category,
            tags=["legacy", "shell", "wrapper"],
            timeout_seconds=60.0
        )


# ============================================================================
# Tool Factory Functions
# ============================================================================

def create_memory_search_tool() -> MemorySearchTool:
    """Factory function for memory search tool"""
    return MemorySearchTool()


def create_health_check_tool() -> HealthCheckTool:
    """Factory function for health check tool"""
    return HealthCheckTool()


def create_consensus_vote_tool() -> ConsensusVoteTool:
    """Factory function for consensus vote tool"""
    return ConsensusVoteTool()


def create_legacy_wrapper(
    name: str,
    script_path: str,
    description: str
) -> LegacyWrapperTool:
    """Factory function for legacy wrapper tools"""
    return LegacyWrapperTool(
        name=name,
        script_path=script_path,
        description=description
    )


# Import asyncio at module level for the examples
import asyncio
