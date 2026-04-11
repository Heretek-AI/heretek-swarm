"""
Tool Registry - Built-in Agent Tools

5+ core tools for agent operations.
Reference: MiniMax Audit + OpenClaw tool patterns
"""

import asyncio
import os
import shlex
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

import aiohttp
import structlog

logger = structlog.get_logger(__name__)

# =============================================================================
# Security: Command Whitelist
# =============================================================================
# Only these commands are allowed to be executed by agents
# This prevents command injection and unauthorized system access
# SECURITY NOTE: 'python' and 'git' removed due to arbitrary code execution risk
ALLOWED_COMMANDS: Set[str] = {
    # File operations (safe)
    "ls", "pwd", "cd", "cat", "head", "tail", "wc",
    "grep", "find", "sort", "uniq", "diff",

    # Text processing
    "echo", "printf", "sed", "awk", "cut",

    # System information (read-only)
    "df", "du", "free", "top", "ps", "uptime",
    "date", "whoami", "id", "uname",

    # Package management (controlled)
    "pip",
}

# Commands that are NEVER allowed (security critical)
BLOCKED_COMMANDS: Set[str] = {
    "rm", "rmdir", "mv", "cp", "chmod", "chown",
    "sudo", "su", "passwd", "useradd", "userdel",
    "systemctl", "service", "iptables", "netstat",
    "curl", "wget", "ssh", "scp", "rsync",
    "kill", "killall", "pkill", "reboot", "shutdown",
    "dd", "mkfs", "fdisk", "mount", "umount",
}


class ToolRegistry:
    """
    Central registry for agent tools.
    
    Manages tool registration, discovery, and execution.
    """

    def __init__(self, default_timeout: int):
        """
        Initialize tool registry.
        
        Args:
            default_timeout: Default timeout for tool execution in seconds (default: 30)
        """
        self._tools: Dict[str, Dict] = {}
        self.default_timeout = default_timeout

    def register(self, name: str, handler: Callable, description: str, parameters: Optional[Dict]) -> None:
        """
        Register a tool.
        
        Args:
            name: Tool name
            handler: Async function to execute tool
            description: Tool description
            parameters: Parameter schema
        """
        self._tools[name] = {
            "handler": handler,
            "description": description,
            "parameters": parameters or {},
            "registered_at": datetime.now(timezone.utc),
        }
        logger.debug("tool_registered", tool=name)

    def get(self, name: str) -> Optional[Dict]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict]:
        """List all available tools."""
        return [
            {
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
            for name, tool in self._tools.items()
        ]

    async def execute(self, name: str, timeout: Optional[int], **params) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            timeout: Optional timeout override in seconds
            **params: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
            asyncio.TimeoutError: If tool execution times out
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")

        # Use provided timeout, tool-specific timeout, or default
        execution_timeout = timeout or tool["parameters"].get("timeout", self.default_timeout)

        logger.info("tool_executing", tool=name, params=params, timeout=execution_timeout)

        try:
            result = await asyncio.wait_for(
                tool["handler"](**params),
                timeout=execution_timeout,
            )
            logger.info("tool_executed", tool=name, success=True)
            return result
        except asyncio.TimeoutError:
            logger.error("tool_execution_timeout", tool=name, timeout=execution_timeout)
            raise
        except Exception as e:
            logger.error("tool_execution_failed", tool=name, error=str(e))
            raise


# =============================================================================
# Built-in Tool Implementations
# =============================================================================

async def search_memory(query: str, agent_id: str, limit: int, memory_backend):
    """
    Search agent memory for relevant information.
    
    Args:
        query: Search query
        agent_id: Agent ID
        limit: Max results
        memory_backend: Memory backend instance
    """
    if not memory_backend:
        return {"error": "Memory backend not available"}

    from memory.base import MemoryQuery

    search_query = MemoryQuery(
        query_text=query,
        agent_ids=[agent_id],
        limit=limit,
    )

    result = await memory_backend.search(search_query)

    return {
        "query": query,
        "results": [
            {
                "content": entry.content,
                "memory_type": entry.memory_type.value,
                "importance": entry.importance_score,
            }
            for entry in result.entries
        ],
        "total": result.total_count,
    }


async def call_agent(agent_id: str, message: str, target_agent: str, a2a_server=None):
    """
    Send message to another agent via A2A protocol.
    
    Args:
        agent_id: Sending agent ID
        message: Message content
        target_agent: Target agent ID
        a2a_server: A2A server instance
    """
    if not a2a_server:
        return {"error": "A2A server not available"}

    # Send via event mesh
    success = await a2a_server.event_mesh.send_to_json(
        target_agent,
        {
            "type": "message",
            "from": agent_id,
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {"success": success, "target": target_agent}


async def execute_bash(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a safe bash command.
    
    Args:
        command: Command to execute
        timeout: Execution timeout in seconds
        
    Returns:
        Command output and status
    """
    try:
        # Parse command safely
        parts = shlex.split(command)
        if not parts:
            return {"error": "Empty command", "stdout": "", "stderr": "", "returncode": 1}

        base_cmd = parts[0]

        # Security check
        if base_cmd in BLOCKED_COMMANDS:
            return {
                "error": f"Command '{base_cmd}' is blocked for security",
                "stdout": "",
                "stderr": "",
                "returncode": 1,
            }

        if base_cmd not in ALLOWED_COMMANDS:
            return {
                "error": f"Command '{base_cmd}' not in whitelist",
                "stdout": "",
                "stderr": "",
                "returncode": 1,
            }

        # Execute command
        process = await asyncio.create_subprocess_exec(
            *parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": process.returncode,
            }
        except asyncio.TimeoutError:
            process.kill()
            return {
                "error": f"Command timed out after {timeout}s",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }

    except Exception as e:
        return {
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "returncode": 1,
        }


async def fetch_url(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch content from a URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Response content and metadata
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                content = await response.text()
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "content": content[:10000],  # Limit content size
                    "url": str(response.url),
                }
    except asyncio.TimeoutError:
        return {"error": f"Request timed out after {timeout}s", "status": 0}
    except Exception as e:
        return {"error": str(e), "status": 0}


def register_builtin_tools(registry: ToolRegistry) -> None:
    """
    Register all built-in tools with the registry.
    
    Args:
        registry: ToolRegistry instance
    """
    registry.register(
        "search_memory",
        search_memory,
        "Search agent memory for relevant information",
        {"type": "object", "properties": {}},
    )

    registry.register(
        "call_agent",
        call_agent,
        "Send message to another agent via A2A protocol",
        {"type": "object", "properties": {}},
    )

    registry.register(
        "execute_bash",
        execute_bash,
        "Execute a safe bash command from the whitelist",
        {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"},
            },
            "required": ["command"],
        },
    )

    registry.register(
        "fetch_url",
        fetch_url,
        "Fetch content from a URL",
        {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"},
            },
            "required": ["url"],
        },
    )
