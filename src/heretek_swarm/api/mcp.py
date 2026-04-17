"""
MCP (Model Context Protocol) API Endpoints

Provides HTTP endpoints for MCP server management:
- GET /api/mcp/tools - List available tools
- POST /api/mcp/tools/call - Execute a tool
- GET /api/mcp/servers - List configured servers
- POST /api/mcp/servers/connect - Connect to external server
- DELETE /api/mcp/servers/{server_id} - Disconnect server
- GET /api/mcp/servers/{server_id}/health - Server health

Integrates with the main FastAPI application.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from heretek_swarm.mcp.client import MCPClientManager
from heretek_swarm.mcp.server import MCPServer, get_registry

logger = structlog.get_logger("api.mcp")

# Create router
router = APIRouter(prefix="/api/mcp", tags=["mcp"])

# Global MCP server instance
_mcp_server: MCPServer | None = None
_client_manager: MCPClientManager | None = None


def get_mcp_server() -> MCPServer:
    """Get or create the global MCP server."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


def get_client_manager() -> MCPClientManager:
    """Get or create the global client manager."""
    global _client_manager
    if _client_manager is None:
        registry = get_registry()
        _client_manager = MCPClientManager(registry)
    return _client_manager


# =============================================================================
# Tool Endpoints
# =============================================================================


@router.get("/tools")
async def list_mcp_tools(
    category: str | None = None,
) -> dict[str, Any]:
    """
    List all available MCP tools.

    Args:
        category: Optional category filter

    Returns:
        List of tools with metadata
    """
    registry = get_registry()
    tools = registry.list_tools(category=category)

    return {
        "tools": registry.list_tool_summaries(),
        "total": len(tools),
        "categories": list({t.category for t in tools}),
    }


@router.get("/tools/{tool_name}")
async def get_mcp_tool(tool_name: str) -> dict[str, Any]:
    """
    Get details for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Detailed tool information
    """
    registry = get_registry()
    tool = registry.get_tool(tool_name)

    if not tool:
        raise HTTPException(404, f"Tool {tool_name} not found")

    stats = registry.get_stats(tool_name)

    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": tool.input_schema,
        "outputSchema": tool.output_schema,
        "category": tool.category,
        "version": tool.version,
        "provider": tool.provider.value,
        "serverId": tool.server_id,
        "tags": tool.tags,
        "enabled": tool.enabled,
        "stats": stats,
    }


@router.post("/tools/call")
async def call_mcp_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Invoke an MCP tool.

    Args:
        name: Tool name to invoke
        arguments: Tool arguments
        context: Optional invocation context

    Returns:
        Tool invocation result
    """
    registry = get_registry()

    if arguments is None:
        arguments = {}

    return await registry.invoke(
        name=name,
        arguments=arguments,
        context=context,
    )


@router.get("/tools/{tool_name}/stats")
async def get_mcp_tool_stats(tool_name: str) -> dict[str, Any]:
    """
    Get statistics for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool statistics
    """
    registry = get_registry()
    stats = registry.get_stats(tool_name)

    if stats is None:
        raise HTTPException(404, f"Tool {tool_name} not found")

    return stats


# =============================================================================
# Server Management Endpoints
# =============================================================================


@router.get("/servers")
async def list_mcp_servers() -> dict[str, Any]:
    """
    List all configured MCP servers.

    Returns:
        List of server configurations
    """
    manager = get_client_manager()
    servers = manager.list_servers()

    return {
        "servers": servers,
        "total": len(servers),
    }


@router.post("/servers/connect")
async def connect_mcp_server(
    server_id: str,
    name: str,
    base_url: str,
    auth_token: str | None = None,
    proxy_tools: bool = True,
) -> dict[str, Any]:
    """
    Connect to an external MCP server.

    Args:
        server_id: Unique server identifier
        name: Human-readable server name
        base_url: Server base URL
        auth_token: Optional authentication token
        proxy_tools: Whether to proxy server tools

    Returns:
        Connection result
    """
    manager = get_client_manager()

    success = await manager.connect_server(
        server_id=server_id,
        name=name,
        base_url=base_url,
        auth_token=auth_token,
        proxy_tools=proxy_tools,
    )

    if not success:
        raise HTTPException(400, f"Failed to connect to server {server_id}")

    return {
        "status": "connected",
        "server_id": server_id,
        "name": name,
        "proxy_tools": proxy_tools,
    }


@router.delete("/servers/{server_id}")
async def disconnect_mcp_server(server_id: str) -> dict[str, Any]:
    """
    Disconnect from an MCP server.

    Args:
        server_id: Server identifier

    Returns:
        Disconnection result
    """
    manager = get_client_manager()

    success = await manager.disconnect_server(server_id)

    if not success:
        raise HTTPException(404, f"Server {server_id} not found")

    return {
        "status": "disconnected",
        "server_id": server_id,
    }


@router.get("/servers/{server_id}/health")
async def get_mcp_server_health(server_id: str) -> dict[str, Any]:
    """
    Get health status of a server.

    Args:
        server_id: Server identifier

    Returns:
        Health status
    """
    manager = get_client_manager()
    return await manager.get_server_health(server_id)


@router.get("/servers/{server_id}/tools")
async def list_server_tools(server_id: str) -> dict[str, Any]:
    """
    List tools from a specific server.

    Args:
        server_id: Server identifier

    Returns:
        List of tool names from server
    """
    manager = get_client_manager()
    tools = manager.list_proxied_tools(server_id=server_id)

    return {
        "server_id": server_id,
        "tools": tools,
        "total": len(tools),
    }


# =============================================================================
# Server Info Endpoint
# =============================================================================


@router.get("/info")
async def get_mcp_info() -> dict[str, Any]:
    """
    Get MCP server information.

    Returns:
        Server metadata
    """
    return {
        "name": "heretek-swarm-mcp",
        "version": "1.0.0",
        "protocol_version": "2024-11-05",
    }


@router.get("/health")
async def get_mcp_health() -> dict[str, Any]:
    """
    Get MCP server health.

    Returns:
        Server health status
    """
    registry = get_registry()
    all_stats = registry.get_all_stats()

    total_calls = sum(s.get("calls", 0) for s in all_stats.values())
    total_errors = sum(s.get("errors", 0) for s in all_stats.values())

    return {
        "status": "healthy",
        "registry": {
            "total_tools": len(registry.list_tools()),
            "total_calls": total_calls,
            "total_errors": total_errors,
        },
    }


# =============================================================================
# Tool Registration Endpoint (Internal)
# =============================================================================


@router.post("/tools/register")
async def register_mcp_tool(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any] | None = None,
    category: str = "general",
    version: str = "1.0.0",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Register a new MCP tool.

    Args:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for input
        output_schema: JSON schema for output
        category: Tool category
        version: Tool version
        tags: Optional tags

    Returns:
        Registration result
    """
    server = get_mcp_server()

    # Create a placeholder handler that returns an error
    # Actual handler should be set separately
    def placeholder_handler(
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {"error": "Handler not implemented"}

    server.register_tool(
        name=name,
        description=description,
        input_schema=input_schema,
        handler=placeholder_handler,
        output_schema=output_schema,
        category=category,
        version=version,
        tags=tags,
    )

    return {
        "status": "registered",
        "name": name,
        "category": category,
    }
