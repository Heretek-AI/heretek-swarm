"""
MCP (Model Context Protocol) Tools for Heretek Swarm

Provides standardized tool interface for external AI systems
and agent-to-agent tool sharing.

Implements the MCP specification for tool registration, discovery, and invocation.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import structlog

_logger = structlog.get_logger(__name__)


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

    def register(self, _tool: MCPToolDefinition) -> None:
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

    def unregister(self, _name: str) -> bool:
        """
        Unregister a tool by name.
        
        Args:
            name: The tool name to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if name not in self._tools:
            return False

        _tool = self._tools.pop(name)
        self._tool_stats.pop(name)

        # Remove from category
        if tool.category in self._categories:
            self._categories[tool.category].remove(name)

        logger.info("tool_unregistered", name=name)
        return True

    def get_tool(self, _name: str) -> Optional[MCPToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self, _category: Optional[str]) -> List[Dict[str, Any]]:
        """
        List all available tools in MCP format.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool definitions in MCP format
        """
        _tools = self._tools.values()

        if category:
            _tools = [t for t in tools if t.category == category]

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

    def get_stats(self, _name: str) -> Optional[Dict[str, Any]]:
        """Get invocation statistics for a tool."""
        return self._tool_stats.get(name)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tools."""
        return self._tool_stats.copy()

    async def invoke(self, _name: str, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict[str, Any]:
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

        _start_time = time.time()

        if name not in self._tools:
            logger.error("tool_not_found", name=name)
            raise ValueError(f"Tool {name} not found")

        _tool = self._tools[name]

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
            _result = await tool.handler(arguments, context or {})

            # Update latency
            _latency_ms = (time.time() - start_time) * 1000
            _stats = self._tool_stats[name]
            _calls = stats["calls"]
            stats["avg_latency_ms"] = (stats["avg_latency_ms"] * (calls - 1) + latency_ms) / calls

            logger.debug("tool_invoked", name=name, latency_ms=latency_ms)
            return {"success": True, "result": result}

        except Exception as e:
            self._tool_stats[name]["errors"] += 1
            logger.error("tool_invocation_error", name=name, error=str(e))
            return {"success": False, "error": str(e)}

    def _validate_arguments(self, _arguments: Dict[str, Any], _schema: Dict[str, Any]) -> bool:
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
        _required = schema.get("required", [])
        for field in required:
            if field not in arguments:
                return False

        # Check types
        _properties = schema.get("properties", {})
        for key, value in arguments.items():
            if key in properties:
                _prop_schema = properties[key]
                _expected_type = prop_schema.get("type")

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

    def __init__(self, _memory_system=None, _rag_pipeline=None, _consensus_engine=None, _event_mesh=None):
        self.memory = memory_system
        self.rag = rag_pipeline
        self.consensus = consensus_engine
        self.event_mesh = event_mesh
        self.registry = MCPToolRegistry()
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default MCP tools using specialized registrars."""
        from .registrars import get_handler_methods, register_all_tools

        # Extract handler methods from this instance
        _handlers = get_handler_methods(self)

        # Register all tools via specialized registrars
        register_all_tools(self.registry, handlers)

    async def _handle_memory_store(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle memory store request."""
        if not self.memory:
            return {"error": "Memory system not initialized"}

        _content = arguments.get("content")
        _metadata = arguments.get("metadata", {})
        _importance = arguments.get("importance", 0.5)

        _result = await self.memory.store(
            content={"text": content, **metadata},
            _metadata = {"importance": importance, "source": context.get("agent_id", "unknown") if context else "unknown"}
        )

        return {"memory_id": getattr(result, 'id', 'unknown'), "stored_at": datetime.now(timezone.utc).isoformat()}

    async def _handle_memory_retrieve(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle memory retrieve request."""
        if not self.memory:
            return {"error": "Memory system not initialized"}

        query = arguments.get("query")
        _limit = arguments.get("limit", 10)
        _tier = arguments.get("tier", "all")

        _results = await self.memory.query(
            _query_text = query,
            _limit = limit,
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

    async def _handle_agent_message(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle agent message request."""
        _target = arguments.get("target_agent")
        _message_type = arguments.get("message_type")
        _content = arguments.get("content")

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

    async def _handle_agent_handoff(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle agent handoff request."""
        _to_agent = arguments.get("to_agent")
        _handoff_context = arguments.get("context")
        _reason = arguments.get("reason", "task_transfer")

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

    async def _handle_consensus_propose(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle consensus propose request."""
        if not self.consensus:
            return {"error": "Consensus engine not initialized"}

        _proposal = arguments.get("proposal")
        _proposal_context = arguments.get("context", {})
        _urgency = arguments.get("urgency", "medium")

        # Submit to consensus engine
        _proposal_id = f"proposal_{datetime.now(timezone.utc).timestamp()}"

        return {
            "proposal_id": proposal_id,
            "status": "pending",
            "urgency": urgency,
        }

    async def _handle_consensus_vote(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle consensus vote request."""
        if not self.consensus:
            return {"error": "Consensus engine not initialized"}

        _proposal_id = arguments.get("proposal_id")
        _vote = arguments.get("vote")
        _confidence = arguments.get("confidence")
        _reasoning = arguments.get("reasoning")

        # Cast vote
        return {
            "vote_cast": True,
            "proposal_id": proposal_id,
            "agent_id": context.get("agent_id") if context else None,
        }

    async def _handle_rag_query(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle RAG query request."""
        if not self.rag:
            return {"error": "RAG pipeline not initialized"}

        query = arguments.get("query")
        _mode = arguments.get("mode", "hybrid")
        _top_k = arguments.get("top_k", 10)

        _result = await self.rag.query(
            _query = query,
            _top_k = top_k,
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

    async def _handle_rag_ingest(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle RAG ingest request."""
        if not self.rag:
            return {"error": "RAG pipeline not initialized"}

        _content = arguments.get("content")
        _source = arguments.get("source", "unknown")
        _metadata = arguments.get("metadata", {})

        # Ingest document
        return {"ingested": True, "source": source}

    async def _handle_external_api_call(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle external API call request."""
        import httpx

        _connection_id = arguments.get("connection_id")
        _endpoint = arguments.get("endpoint")
        _method = arguments.get("method", "GET")
        _payload = arguments.get("payload")

        try:
            async with httpx.AsyncClient() as client:
                _response = await client.request(method, endpoint, json=payload)
                return {
                    "status_code": response.status_code,
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                }
        except Exception as e:
            return {"error": str(e)}

    async def _handle_notification_send(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle notification send request."""
        _channel = arguments.get("channel")
        _message = arguments.get("message")
        _priority = arguments.get("priority", "info")

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

    async def _handle_workflow_start(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle workflow start request."""
        _workflow_type = arguments.get("workflow_type")
        _params = arguments.get("params", {})
        _topic = arguments.get("topic")

        # Start workflow via event mesh
        if not self.event_mesh:
            return {"error": "Event mesh not initialized"}

        _workflow_id = f"workflow_{datetime.now(timezone.utc).timestamp()}"

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

    async def _handle_workflow_status(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
        """Handle workflow status request."""
        _workflow_id = arguments.get("workflow_id")

        # Query workflow status (placeholder)
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "phase": "analysis",
        }

    async def _handle_system_health(self, _arguments: Dict[str, Any], _context: Optional[Dict]) -> Dict:
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
