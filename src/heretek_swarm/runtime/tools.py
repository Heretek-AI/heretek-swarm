"""
Tool Registry - Built-in Agent Tools

5+ core tools for agent operations.
Reference: MiniMax Audit + OpenClaw tool patterns
"""

import os
import asyncio
import aiohttp
import shlex
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

# =============================================================================
# Security: Command Whitelist
# =============================================================================
# Only these commands are allowed to be executed by agents
# This prevents command injection and unauthorized system access
ALLOWED_COMMANDS: Set[str] = {
    # File operations (safe)
    "ls", "pwd", "cd", "cat", "head", "tail", "wc",
    "grep", "find", "sort", "uniq", "diff",
    
    # Text processing
    "echo", "printf", "sed", "awk", "cut",
    
    # System information (read-only)
    "df", "du", "free", "top", "ps", "uptime",
    "date", "whoami", "id", "uname",
    
    # Development tools
    "git", "python", "pip", "pytest",
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
    
    def __init__(self):
        self._tools: Dict[str, Dict] = {}
    
    def register(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: Optional[Dict] = None,
    ) -> None:
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
            "registered_at": datetime.utcnow(),
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
    
    async def execute(self, name: str, **params) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            **params: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        
        logger.info("tool_executing", tool=name, params=params)
        
        try:
            result = await tool["handler"](**params)
            logger.info("tool_executed", tool=name, success=True)
            return result
        except Exception as e:
            logger.error("tool_execution_failed", tool=name, error=str(e))
            raise


# =============================================================================
# Built-in Tool Implementations
# =============================================================================

async def search_memory(query: str, agent_id: str, limit: int = 5, memory_backend=None):
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


async def call_agent(
    agent_id: str,
    message: str,
    target_agent: str,
    a2a_server=None,
):
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
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    
    return {
        "sent": success,
        "to": target_agent,
        "message": message[:100],
    }


async def read_file(path: str) -> Dict:
    """
    Read contents of a file.
    
    Args:
        path: File path
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "path": path,
            "content": content,
            "size": len(content),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def write_file(path: str, content: str) -> Dict:
    """
    Write content to a file.
    
    Args:
        path: File path
        content: Content to write
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "path": path,
            "bytes_written": len(content),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def run_command(command: str, timeout: int = 30) -> Dict:
    """
    Execute shell command with security validation.
    
    SECURITY: Only whitelisted commands are allowed. Command injection
    is prevented through strict validation and argument sanitization.
    
    Args:
        command: Shell command
        timeout: Timeout in seconds
        
    Returns:
        Dict with success status, output, or error message
        
    Raises:
        ValueError: If command is not allowed
    """
    # Validate command is not empty
    if not command or not command.strip():
        return {
            "success": False,
            "error": "Empty command not allowed"
        }
    
    # Parse command to extract base command
    parts = command.strip().split()
    if not parts:
        return {
            "success": False,
            "error": "Invalid command format"
        }
    
    base_cmd = parts[0]
    
    # Check if command is blocked (security critical)
    if base_cmd in BLOCKED_COMMANDS:
        logger.warning(
            "command_blocked",
            command=base_cmd,
            reason="Command in blocked list"
        )
        return {
            "success": False,
            "error": f"Command '{base_cmd}' is not allowed for security reasons"
        }
    
    # Check if command is allowed
    if base_cmd not in ALLOWED_COMMANDS:
        logger.warning(
            "command_not_allowed",
            command=base_cmd,
            reason="Command not in whitelist"
        )
        return {
            "success": False,
            "error": f"Command '{base_cmd}' is not in the allowed command list"
        }
    
    # Sanitize arguments to prevent injection
    try:
        sanitized_args = [shlex.quote(arg) for arg in parts[1:]]
        safe_command = f"{base_cmd} {' '.join(sanitized_args)}"
    except Exception as e:
        logger.error("command_sanitization_failed", error=str(e))
        return {
            "success": False,
            "error": f"Failed to sanitize command arguments: {str(e)}"
        }
    
    # Execute command with subprocess (no shell=True for security)
    try:
        proc = await asyncio.create_subprocess_exec(
            base_cmd,
            *parts[1:],  # Pass arguments as separate parameters
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
        
        # Log command execution
        logger.info(
            "command_executed",
            command=base_cmd,
            args_count=len(parts) - 1,
            returncode=proc.returncode,
        )
        
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout.decode()[:10000],  # Limit output
            "stderr": stderr.decode()[:10000],
            "command": safe_command,  # Return sanitized command
        }
    except asyncio.TimeoutError:
        logger.warning("command_timeout", command=base_cmd, timeout=timeout)
        return {
            "success": False,
            "error": f"Command timed out after {timeout}s"
        }
    except FileNotFoundError:
        logger.error("command_not_found", command=base_cmd)
        return {
            "success": False,
            "error": f"Command '{base_cmd}' not found"
        }
    except PermissionError:
        logger.error("command_permission_denied", command=base_cmd)
        return {
            "success": False,
            "error": f"Permission denied for command '{base_cmd}'"
        }
    except Exception as e:
        logger.error("command_execution_failed", command=base_cmd, error=str(e))
        return {
            "success": False,
            "error": f"Command execution failed: {str(e)}"
        }


async def http_request(
    method: str,
    url: str,
    headers: Optional[Dict] = None,
    body: Optional[Dict] = None,
    timeout: int = 30,
) -> Dict:
    """
    Make HTTP request.
    
    Args:
        method: HTTP method
        url: URL
        headers: Request headers
        body: Request body
        timeout: Timeout in seconds
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                content = await response.text()
                
                return {
                    "success": response.status < 400,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": content[:10000],  # Limit
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# Tool Registration
# =============================================================================

def register_builtin_tools(
    registry: ToolRegistry,
    memory_backend=None,
    a2a_server=None,
) -> None:
    """
    Register all built-in tools.
    
    Args:
        registry: Tool registry
        memory_backend: Optional memory backend
        a2a_server: Optional A2A server
    """
    # Memory search (requires backend)
    async def memory_search_wrapper(query: str, agent_id: str, limit: int = 5):
        return await search_memory(query, agent_id, limit, memory_backend)
    
    registry.register(
        name="search_memory",
        handler=memory_search_wrapper,
        description="Search agent memory for relevant information",
        parameters={
            "query": "string (required): Search query",
            "agent_id": "string (required): Agent ID",
            "limit": "integer (optional): Max results (default: 5)",
        },
    )
    
    # Agent calling (requires A2A server)
    async def agent_call_wrapper(agent_id: str, message: str, target: str):
        return await call_agent(agent_id, message, target, a2a_server)
    
    registry.register(
        name="call_agent",
        handler=agent_call_wrapper,
        description="Send message to another agent via A2A protocol",
        parameters={
            "agent_id": "string (required): Your agent ID",
            "message": "string (required): Message content",
            "target": "string (required): Target agent ID",
        },
    )
    
    # File operations
    registry.register(
        name="read_file",
        handler=read_file,
        description="Read contents of a file",
        parameters={"path": "string (required): File path"},
    )
    
    registry.register(
        name="write_file",
        handler=write_file,
        description="Write content to a file",
        parameters={
            "path": "string (required): File path",
            "content": "string (required): Content to write",
        },
    )
    
    # Command execution (with security validation)
    registry.register(
        name="run_command",
        handler=run_command,
        description="Execute shell command (whitelisted commands only, with argument sanitization)",
        parameters={
            "command": "string (required): Shell command from whitelist",
            "timeout": "integer (optional): Timeout in seconds (default: 30)",
        },
    )
    
    # HTTP requests
    registry.register(
        name="http_request",
        handler=http_request,
        description="Make HTTP request",
        parameters={
            "method": "string (required): HTTP method (GET, POST, etc)",
            "url": "string (required): URL",
            "headers": "object (optional): Request headers",
            "body": "object (optional): Request body",
            "timeout": "integer (optional): Timeout in seconds (default: 30)",
        },
    )
    
    logger.info(
        "builtin_tools_registered",
        count=len(registry.list_tools()),
        tools=[t["name"] for t in registry.list_tools()],
    )
