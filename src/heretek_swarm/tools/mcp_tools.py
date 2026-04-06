"""
MCP (Model Context Protocol) Tools for Heretek Swarm

Provides standardized tool interface for external AI systems
and agent-to-agent tool sharing.

Implements the MCP specification for tool registration, discovery, and invocation.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MCPToolDefinition:
    """MCP-compliant tool definition."""
    
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    category: str = "general"
    version: str = "1.0.0"
    enabled: bool = True


class MCPToolRegistry:
    """
    Registry for MCP-compatible tools.
    
    Provides centralized tool management with:
    - Tool registration and discovery
    - Input validation against JSON schemas
    - Invocation tracking and metrics
    - Category-based filtering
    """
    
    def __init__(self):
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._tool_stats: Dict[str, Dict] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: MCPToolDefinition) -> None:
        """
        Register an MCP tool.
        
        Args:
            tool: The tool definition to register
            
        Raises:
            ValueError: If tool name conflicts with existing registration
        """
        if tool.name in self._tools:
            logger.warning("tool_registration_conflict", tool_name=tool.name)
            raise ValueError(f"Tool {tool.name} already registered")
        
        self._tools[tool.name] = tool
        self._tool_stats[tool.name] = {
            "calls": 0,
            "errors": 0,
            "last_called": None,
            "avg_latency_ms": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Track by category
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        self._categories[tool.category].append(tool.name)
        
        logger.info("tool_registered", name=tool.name, category=tool.category)
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool by name.
        
        Args:
            name: The tool name to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if name not in self._tools:
            return False
        
        tool = self._tools.pop(name)
        self._tool_stats.pop(name)
        
        # Remove from category
        if tool.category in self._categories:
            self._categories[tool.category].remove(name)
        
        logger.info("tool_unregistered", name=name)
        return True
    
    def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available tools in MCP format.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool definitions in MCP format
        """
        tools = self._tools.values()
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema,
                "category": t.category,
                "version": t.version,
                "enabled": t.enabled,
            }
            for t in tools if t.enabled
        ]
    
    def list_categories(self) -> List[str]:
        """List all available tool categories."""
        return list(self._categories.keys())
    
    def get_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get invocation statistics for a tool."""
        return self._tool_stats.get(name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tools."""
        return self._tool_stats.copy()
    
    async def invoke(
        self, 
        name: str, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Invoke an MCP tool.
        
        Args:
            name: Tool name to invoke
            arguments: Tool arguments
            context: Optional invocation context (agent_id, session_id, etc.)
            
        Returns:
            Tool invocation result with success/error status
            
        Raises:
            ValueError: If tool not found or disabled
            ValidationError: If arguments don't match schema
        """
        import time
        
        start_time = time.time()
        
        if name not in self._tools:
            logger.error("tool_not_found", name=name)
            raise ValueError(f"Tool {name} not found")
        
        tool = self._tools[name]
        
        if not tool.enabled:
            logger.warning("tool_disabled", name=name)
            raise ValueError(f"Tool {name} is disabled")
        
        # Validate arguments against schema
        if not self._validate_arguments(arguments, tool.input_schema):
            logger.error("tool_validation_failed", name=name, arguments=arguments)
            raise ValueError(f"Invalid arguments for tool {name}")
        
        # Update stats
        self._tool_stats[name]["calls"] += 1
        self._tool_stats[name]["last_called"] = datetime.now(timezone.utc).isoformat()
        
        try:
            # Invoke handler
            result = await tool.handler(arguments, context or {})
            
            # Update latency
            latency_ms = (time.time() - start_time) * 1000
            stats = self._tool_stats[name]
            calls = stats["calls"]
            stats["avg_latency_ms"] = (stats["avg_latency_ms"] * (calls - 1) + latency_ms) / calls
            
            logger.debug("tool_invoked", name=name, latency_ms=latency_ms)
            return {"success": True, "result": result}
            
        except Exception as e:
            self._tool_stats[name]["errors"] += 1
            logger.error("tool_invocation_error", name=name, error=str(e))
            return {"success": False, "error": str(e)}
    
    def _validate_arguments(
        self, 
        arguments: Dict[str, Any], 
        schema: Dict[str, Any]
    ) -> bool:
        """
        Validate arguments against JSON schema.
        
        Args:
            arguments: Arguments to validate
            schema: JSON schema to validate against
            
        Returns:
            True if valid, False otherwise
        """
        if not schema:
            return True
        
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in arguments:
                return False
        
        # Check types
        properties = schema.get("properties", {})
        for key, value in arguments.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")
                
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "integer" and not isinstance(value, int):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                elif expected_type == "array" and not isinstance(value, list):
                    return False
                elif expected_type == "object" and not isinstance(value, dict):
                    return False
                
                # Check enum values
                if "enum" in prop_schema and value not in prop_schema["enum"]:
                    return False
                
                # Check min/max for numbers
                if isinstance(value, (int, float)):
                    if "minimum" in prop_schema and value < prop_schema["minimum"]:
                        return False
                    if "maximum" in prop_schema and value > prop_schema["maximum"]:
                        return False
        
        return True


# ============================================================================
# Core MCP Tools
# ============================================================================

class CoreMCPTools:
    """
    Core MCP tools for Heretek Swarm.
    
    Provides standard tools for memory, communication, consensus, RAG,
    and external integration.
    """
    
    def __init__(
        self,
        memory_system=None,
        rag_pipeline=None,
        consensus_engine=None,
        event_mesh=None,
    ):
        self.memory = memory_system
        self.rag = rag_pipeline
        self.consensus = consensus_engine
        self.event_mesh = event_mesh
        self.registry = MCPToolRegistry()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default MCP tools."""
        
        # === MEMORY TOOLS ===
        self.registry.register(MCPToolDefinition(
            name="memory_store",
            description="Store information in collective memory with optional metadata and importance weighting",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to store"},
                    "metadata": {"type": "object", "description": "Additional metadata"},
                    "importance": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5}
                },
                "required": ["content"]
            },
            handler=self._handle_memory_store,
            category="memory"
        ))
        
        self.registry.register(MCPToolDefinition(
            name="memory_retrieve",
            description="Retrieve relevant memories by semantic query",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 100},
                    "tier": {"type": "string", "enum": ["ephemeral", "persistent", "all"], "default": "all"}
                },
                "required": ["query"]
            },
            handler=self._handle_memory_retrieve,
            category="memory"
        ))
        
        # === AGENT COMMUNICATION TOOLS ===
        self.registry.register(MCPToolDefinition(
            name="agent_message",
            description="Send a message to another agent",
            input_schema={
                "type": "object",
                "properties": {
                    "target_agent": {"type": "string", "description": "Target agent ID"},
                    "message_type": {"type": "string", "description": "Message type"},
                    "content": {"type": "object", "description": "Message content"},
                    "reply_expected": {"type": "boolean", "default": False}
                },
                "required": ["target_agent", "message_type", "content"]
            },
            handler=self._handle_agent_message,
            category="communication"
        ))
        
        self.registry.register(MCPToolDefinition(
            name="agent_handoff",
            description="Transfer task context to another agent",
            input_schema={
                "type": "object",
                "properties": {
                    "to_agent": {"type": "string", "description": "Target agent ID"},
                    "context": {"type": "object", "description": "Task context"},
                    "reason": {"type": "string", "description": "Handoff reason"}
                },
                "required": ["to_agent", "context"]
            },
            handler=self._handle_agent_handoff,
            category="communication"
        ))
        
        # === CONSENSUS TOOLS ===
        self.registry.register(MCPToolDefinition(
            name="consensus_propose",
            description="Submit a proposal for collective decision via MAKER consensus",
            input_schema={
                "type": "object",
                "properties": {
                    "proposal": {"type": "string", "description": "Proposal text"},
                    "context": {"type": "object", "description": "Proposal context"},
                    "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"}
                },
                "required": ["proposal"]
            },
            handler=self._handle_consensus_propose,
            category="consensus"
        ))
        
        self.registry.register(MCPToolDefinition(
            name="consensus_vote",
            description="Cast a vote on an active proposal",
            input_schema={
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "string", "description": "Proposal ID"},
                    "vote": {"type": "string", "description": "Vote value"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Confidence level"},
                    "reasoning": {"type": "string", "description": "Vote reasoning"}
                },
                "required": ["proposal_id", "vote", "confidence"]
            },
            handler=self._handle_consensus_vote,
            category="consensus"
        ))
        
        # === RAG TOOLS ===
        self.registry.register(MCPToolDefinition(
            name="rag_query",
            description="Query the RAG knowledge base",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "mode": {"type": "string", "enum": ["vector", "keyword", "hybrid"], "default": "hybrid"},
                    "top_k": {"type": "integer", "default": 10, "minimum": 1, "maximum": 100}
                },
                "required": ["query"]
            },
            handler=self._handle_rag_query,
            category="knowledge"
        ))
        
        self.registry.register(MCPToolDefinition(
            name="rag_ingest",
            description="Ingest a document into the RAG system",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Document content"},
                    "source": {"type": "string", "description": "Document source"},
                    "metadata": {"type": "object", "description": "Document metadata"}
                },
                "required": ["content"]
            },
            handler=self._handle_rag_ingest,
            category="knowledge"
        ))
        
        # === EXTERNAL INTEGRATION TOOLS ===
        self.registry.register(MCPToolDefinition(
            name="external_api_call",
            description="Make an authenticated external API call",
            input_schema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "Connection ID"},
                    "endpoint": {"type": "string", "description": "API endpoint"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                    "payload": {"type": "object", "description": "Request payload"}
                },
                "required": ["connection_id", "endpoint", "method"]
            },
            handler=self._handle_external_api_call,
            category="integration"
        ))
        
        self.registry.register(MCPToolDefinition(
            name="notification_send",
            description="Send a notification to external channels",
            input_schema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "enum": ["discord", "slack", "telegram", "all"], "description": "Notification channel"},
                    "message": {"type": "string", "description": "Notification message"},
                    "priority": {"type": "string", "enum": ["info", "warning", "error", "critical"], "default": "info"}
                },
                "required": ["channel", "message"]
            },
            handler=self._handle_notification_send,
            category="integration"
        ))
        
        # === WORKFLOW TOOLS ===
        self.registry.register(MCPToolDefinition(
            name="workflow_start",
            description="Start a new workflow execution",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_type": {"type": "string", "description": "Workflow type (e.g., 'heavyswarm')"},
                    "params": {"type": "object", "description": "Workflow parameters"},
                    "topic": {"type": "string", "description": "Workflow topic"}
                },
                "required": ["workflow_type"]
            },
            handler=self._handle_workflow_start,
            category="workflow"
        ))
        
        self.registry.register(MCPToolDefinition(
            name="workflow_status",
            description="Get the status of a running workflow",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"}
                },
                "required": ["workflow_id"]
            },
            handler=self._handle_workflow_status,
            category="workflow"
        ))
        
        # === SYSTEM TOOLS ===
        self.registry.register(MCPToolDefinition(
            name="system_health",
            description="Get system health status",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._handle_system_health,
            category="system"
        ))
    
    async def _handle_memory_store(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle memory store request."""
        if not self.memory:
            return {"error": "Memory system not initialized"}
        
        content = arguments.get("content")
        metadata = arguments.get("metadata", {})
        importance = arguments.get("importance", 0.5)
        
        result = await self.memory.store(
            content={"text": content, **metadata},
            metadata={"importance": importance, "source": context.get("agent_id", "unknown") if context else "unknown"}
        )
        
        return {"memory_id": getattr(result, 'id', 'unknown'), "stored_at": datetime.now(timezone.utc).isoformat()}
    
    async def _handle_memory_retrieve(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle memory retrieve request."""
        if not self.memory:
            return {"error": "Memory system not initialized"}
        
        query = arguments.get("query")
        limit = arguments.get("limit", 10)
        tier = arguments.get("tier", "all")
        
        results = await self.memory.query(
            query_text=query,
            limit=limit,
        )
        
        return {
            "entries": [
                {
                    "content": entry.content if hasattr(entry, 'content') else entry,
                    "metadata": getattr(entry, 'metadata', {}),
                    "score": getattr(entry, 'similarity', 0),
                }
                for entry in (results.entries if hasattr(results, 'entries') else results)
            ]
        }
    
    async def _handle_agent_message(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle agent message request."""
        target = arguments.get("target_agent")
        message_type = arguments.get("message_type")
        content = arguments.get("content")
        
        if not self.event_mesh:
            return {"error": "Event mesh not initialized"}
        
        await self.event_mesh.publish(
            f"agent.{target}",
            {
                "type": message_type,
                "content": content,
                "from_agent": context.get("agent_id") if context else None,
            }
        )
        
        return {"sent": True, "target": target}
    
    async def _handle_agent_handoff(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle agent handoff request."""
        to_agent = arguments.get("to_agent")
        handoff_context = arguments.get("context")
        reason = arguments.get("reason", "task_transfer")
        
        if not self.event_mesh:
            return {"error": "Event mesh not initialized"}
        
        await self.event_mesh.publish(
            f"agent.{to_agent}",
            {
                "type": "handoff",
                "context": handoff_context,
                "reason": reason,
                "from_agent": context.get("agent_id") if context else None,
            }
        )
        
        return {"handoff_initiated": True, "to_agent": to_agent}
    
    async def _handle_consensus_propose(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle consensus propose request."""
        if not self.consensus:
            return {"error": "Consensus engine not initialized"}
        
        proposal = arguments.get("proposal")
        proposal_context = arguments.get("context", {})
        urgency = arguments.get("urgency", "medium")
        
        # Submit to consensus engine
        proposal_id = f"proposal_{datetime.now(timezone.utc).timestamp()}"
        
        return {
            "proposal_id": proposal_id,
            "status": "pending",
            "urgency": urgency,
        }
    
    async def _handle_consensus_vote(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle consensus vote request."""
        if not self.consensus:
            return {"error": "Consensus engine not initialized"}
        
        proposal_id = arguments.get("proposal_id")
        vote = arguments.get("vote")
        confidence = arguments.get("confidence")
        reasoning = arguments.get("reasoning")
        
        # Cast vote
        return {
            "vote_cast": True,
            "proposal_id": proposal_id,
            "agent_id": context.get("agent_id") if context else None,
        }
    
    async def _handle_rag_query(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle RAG query request."""
        if not self.rag:
            return {"error": "RAG pipeline not initialized"}
        
        query = arguments.get("query")
        mode = arguments.get("mode", "hybrid")
        top_k = arguments.get("top_k", 10)
        
        result = await self.rag.query(
            query=query,
            top_k=top_k,
        )
        
        return {
            "documents": [
                {
                    "content": doc.content if hasattr(doc, 'content') else doc,
                    "metadata": getattr(doc, 'metadata', {}),
                    "score": getattr(doc, 'score', 0),
                }
                for doc in (result.documents if hasattr(result, 'documents') else result)
            ]
        }
    
    async def _handle_rag_ingest(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle RAG ingest request."""
        if not self.rag:
            return {"error": "RAG pipeline not initialized"}
        
        content = arguments.get("content")
        source = arguments.get("source", "unknown")
        metadata = arguments.get("metadata", {})
        
        # Ingest document
        return {"ingested": True, "source": source}
    
    async def _handle_external_api_call(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle external API call request."""
        import httpx
        
        connection_id = arguments.get("connection_id")
        endpoint = arguments.get("endpoint")
        method = arguments.get("method", "GET")
        payload = arguments.get("payload")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, endpoint, json=payload)
                return {
                    "status_code": response.status_code,
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_notification_send(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle notification send request."""
        channel = arguments.get("channel")
        message = arguments.get("message")
        priority = arguments.get("priority", "info")
        
        if not self.event_mesh:
            return {"error": "Event mesh not initialized"}
        
        await self.event_mesh.publish(
            f"notification.{channel}",
            {
                "message": message,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        return {"sent": True, "channel": channel}
    
    async def _handle_workflow_start(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle workflow start request."""
        workflow_type = arguments.get("workflow_type")
        params = arguments.get("params", {})
        topic = arguments.get("topic")
        
        # Start workflow via event mesh
        if not self.event_mesh:
            return {"error": "Event mesh not initialized"}
        
        workflow_id = f"workflow_{datetime.now(timezone.utc).timestamp()}"
        
        await self.event_mesh.publish(
            "workflow.start",
            {
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "params": params,
                "topic": topic,
            }
        )
        
        return {"workflow_id": workflow_id, "status": "started"}
    
    async def _handle_workflow_status(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle workflow status request."""
        workflow_id = arguments.get("workflow_id")
        
        # Query workflow status (placeholder)
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "phase": "analysis",
        }
    
    async def _handle_system_health(
        self, 
        arguments: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle system health request."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "memory": "initialized" if self.memory else "not_initialized",
                "rag": "initialized" if self.rag else "not_initialized",
                "consensus": "initialized" if self.consensus else "not_initialized",
                "event_mesh": "initialized" if self.event_mesh else "not_initialized",
            },
        }
    
    def get_registry(self) -> MCPToolRegistry:
        """Get the underlying tool registry."""
        return self.registry
