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
from datetime import datetime, timezone
import structlog

_logger = structlog.get_logger(__name__)

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
    
    def __init__(self, _default_timeout: int):
        """
        Initialize tool registry.
        
        Args:
            default_timeout: Default timeout for tool execution in seconds (default: 30)
        """
        self._tools: Dict[str, Dict] = {}
        self.default_timeout = default_timeout
    
    def register(self, _name: str, _handler: Callable, _description: str, _parameters: Optional[Dict]) -> None:
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
    
    def get(self, _name: str) -> Optional[Dict]:
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
    
    async def execute(self, _name: str, _timeout: Optional[int], _**params) -> Any:
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
        _tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        
        # Use provided timeout, tool-specific timeout, or default
        _execution_timeout = timeout or tool["parameters"].get("timeout", self.default_timeout)
        
        logger.info("tool_executing", tool=name, params=params, timeout=execution_timeout)
        
        try:
            _result = await asyncio.wait_for(
                tool["handler"](**params),
                _timeout = execution_timeout,
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

async def search_memory(_query: str, _agent_id: str, _limit: int, _memory_backend):
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
    
    _search_query = MemoryQuery(
        _query_text = query,
        _agent_ids = [agent_id],
        _limit = limit,
    )
    
    _result = await memory_backend.search(search_query)
    
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


async def call_agent(_agent_id: str, _message: str, _target_agent: str, _a2a_server = None):
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
    _success = await a2a_server.event_mesh.send_to_json(
        target_agent,
        {
            "type": "message",
            "from": agent_id,
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    return {
        "sent": success,
        "to": target_agent,
        "message": message[:100],
    }


async def read_file(_path: str, _allowed_base_paths: Optional[List[str]]) -> Dict:
    """
    Read contents of a file with path traversal protection.
    
    SECURITY: Validates that the resolved path is within allowed base paths
    to prevent reading sensitive files like /etc/passwd.
    
    Args:
        path: File path
        allowed_base_paths: List of allowed base directories (default: current working directory)
    """
    # Default to current working directory if not specified
    if allowed_base_paths is None:
        _allowed_base_paths = [os.getcwd()]
    
    # Resolve to absolute path
    _resolved_path = os.path.realpath(os.path.abspath(path))
    
    # Validate path is within allowed directories
    _path_allowed = False
    for base_path in allowed_base_paths:
        _resolved_base = os.path.realpath(os.path.abspath(base_path))
        if resolved_path.startswith(resolved_base + os.sep) or resolved_path == resolved_base:
            _path_allowed = True
            break
    
    if not path_allowed:
        logger.warning(
            "path_traversal_blocked",
            _requested_path = path,
            _resolved_path = resolved_path,
            _allowed_bases = allowed_base_paths
        )
        return {
            "success": False,
            "error": "Access denied: Path traversal detected. Access is restricted to allowed directories."
        }
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            _content = f.read()
        
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


async def write_file(_path: str, _content: str, _allowed_base_paths: Optional[List[str]]) -> Dict:
    """
    Write content to a file with path traversal protection.
    
    SECURITY: Validates that the resolved path is within allowed base paths
    to prevent writing to sensitive locations like /etc/.
    
    Args:
        path: File path
        content: Content to write
        allowed_base_paths: List of allowed base directories (default: current working directory)
    """
    # Default to current working directory if not specified
    if allowed_base_paths is None:
        _allowed_base_paths = [os.getcwd()]
    
    # Resolve to absolute path
    _resolved_path = os.path.realpath(os.path.abspath(path))
    
    # Validate path is within allowed directories
    _path_allowed = False
    for base_path in allowed_base_paths:
        _resolved_base = os.path.realpath(os.path.abspath(base_path))
        if resolved_path.startswith(resolved_base + os.sep) or resolved_path == resolved_base:
            _path_allowed = True
            break
    
    if not path_allowed:
        logger.warning(
            "path_traversal_blocked",
            _requested_path = path,
            _resolved_path = resolved_path,
            _allowed_bases = allowed_base_paths
        )
        return {
            "success": False,
            "error": "Access denied: Path traversal detected. Access is restricted to allowed directories."
        }
    
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


async def run_command(_command: str, _timeout: int) -> Dict:
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
    _parts = command.strip().split()
    if not parts:
        return {
            "success": False,
            "error": "Invalid command format"
        }
    
    _base_cmd = parts[0]
    
    # Check if command is blocked (security critical)
    if base_cmd in BLOCKED_COMMANDS:
        logger.warning(
            "command_blocked",
            _command = base_cmd,
            _reason = "Command in blocked list"
        )
        return {
            "success": False,
            "error": f"Command '{base_cmd}' is not allowed for security reasons"
        }
    
    # Check if command is allowed
    if base_cmd not in ALLOWED_COMMANDS:
        logger.warning(
            "command_not_allowed",
            _command = base_cmd,
            _reason = "Command not in whitelist"
        )
        return {
            "success": False,
            "error": f"Command '{base_cmd}' is not in the allowed command list"
        }
    
    # Sanitize arguments to prevent injection
    try:
        _sanitized_args = [shlex.quote(arg) for arg in parts[1:]]
        _safe_command = f"{base_cmd} {' '.join(sanitized_args)}"
    except Exception as e:
        logger.error("command_sanitization_failed", error=str(e))
        return {
            "success": False,
            "error": f"Failed to sanitize command arguments: {str(e)}"
        }
    
    # Execute command with subprocess (no shell=True for security)
    try:
        _proc = await asyncio.create_subprocess_exec(
            base_cmd,
            *parts[1:],  # Pass arguments as separate parameters
            _stdout = asyncio.subprocess.PIPE,
            _stderr = asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            _timeout = timeout,
        )
        
        # Log command execution
        logger.info(
            "command_executed",
            _command = base_cmd,
            _args_count = len(parts) - 1,
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


async def http_request(_method: str, _url: str, _headers: Optional[Dict], _body: Optional[Dict], _timeout: int, _max_retries: int) -> Dict:
    """
    Make HTTP request with timeout and retry support.
    
    Args:
        method: HTTP method
        url: URL
        headers: Request headers
        body: Request body
        timeout: Timeout in seconds (default: 30)
        max_retries: Maximum retry attempts (default: 1)
        
    Returns:
        Dict with success status, response data, or error message
    """
    # Validate URL to prevent SSRF attacks
    if not url or not isinstance(url, str):
        return {
            "success": False,
            "error": "Invalid URL provided",
        }
    
    # Block private/internal IP ranges to prevent SSRF
    import re
    _private_ip_pattern = re.compile(
        r'^(127\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|0\.0\.0\.0|localhost)',
        re.IGNORECASE
    )
    if private_ip_pattern.match(url):
        logger.warning("ssrf_attempt_blocked", url=url)
        return {
            "success": False,
            "error": "Access to internal addresses is not allowed",
        }
    
    _attempt = 0
    _last_error = None
    
    while attempt <= max_retries:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    _json = body,
                    _timeout = aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    _content = await response.text()
                    
                    return {
                        "success": response.status < 400,
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": content[:10000],  # Limit output size
                    }
        except asyncio.TimeoutError as e:
            _last_error = f"Request timed out after {timeout}s"
            logger.warning("http_request_timeout", url=url, attempt=attempt + 1)
        except aiohttp.ClientError as e:
            _last_error = f"HTTP client error: {str(e)}"
            logger.error("http_request_client_error", url=url, error=str(e))
            break  # Don't retry client errors
        except Exception as e:
            _last_error = str(e)
            logger.error("http_request_error", url=url, error=str(e))
        
        attempt += 1
        if attempt <= max_retries:
            await asyncio.sleep(1.0 * attempt)  # Exponential backoff
    
    return {
        "success": False,
        "error": last_error or "Unknown error",
        "attempts": attempt,
    }


# =============================================================================
# Tool Registration
# =============================================================================

def register_builtin_tools(_registry: ToolRegistry, _memory_backend = None, _a2a_server = None) -> None:
    """
    Register all built-in tools.
    
    Args:
        registry: Tool registry
        memory_backend: Optional memory backend
        a2a_server: Optional A2A server
    """
    # Memory search (requires backend)
    async def memory_search_wrapper(_query: str, _agent_id: str, _limit: int):
        return await search_memory(query, agent_id, limit, memory_backend)
    
    registry.register(
        _name = "search_memory",
        _handler = memory_search_wrapper,
        _description = "Search agent memory for relevant information",
        _parameters = {
            "query": "string (required): Search query",
            "agent_id": "string (required): Agent ID",
            "limit": "integer (optional): Max results (default: 5)",
        },
    )
    
    # Agent calling (requires A2A server)
    async def agent_call_wrapper(_agent_id: str, _message: str, _target: str):
        return await call_agent(agent_id, message, target, a2a_server)
    
    registry.register(
        _name = "call_agent",
        _handler = agent_call_wrapper,
        _description = "Send message to another agent via A2A protocol",
        _parameters = {
            "agent_id": "string (required): Your agent ID",
            "message": "string (required): Message content",
            "target": "string (required): Target agent ID",
        },
    )
    
    # File operations
    registry.register(
        _name = "read_file",
        _handler = read_file,
        _description = "Read contents of a file",
        _parameters = {"path": "string (required): File path"},
    )
    
    registry.register(
        _name = "write_file",
        _handler = write_file,
        _description = "Write content to a file",
        _parameters = {
            "path": "string (required): File path",
            "content": "string (required): Content to write",
        },
    )
    
    # Command execution (with security validation)
    registry.register(
        _name = "run_command",
        _handler = run_command,
        _description = "Execute shell command (whitelisted commands only, with argument sanitization)",
        _parameters = {
            "command": "string (required): Shell command from whitelist",
            "timeout": "integer (optional): Timeout in seconds (default: 30)",
        },
    )
    
    # HTTP requests
    registry.register(
        _name = "http_request",
        _handler = http_request,
        _description = "Make HTTP request",
        _parameters = {
            "method": "string (required): HTTP method (GET, POST, etc)",
            "url": "string (required): URL",
            "headers": "object (optional): Request headers",
            "body": "object (optional): Request body",
            "timeout": "integer (optional): Timeout in seconds (default: 30)",
        },
    )
    
    logger.info(
        "builtin_tools_registered",
        _count = len(registry.list_tools()),
        _tools = [t["name"] for t in registry.list_tools()],
    )
