"""
Tool Registry for ElizaOS-style agents.

This module provides the tool registry with built-in tools for the swarm,
including memory search, agent communication, and file operations.
"""

import asyncio
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger("ToolRegistry")

# Type alias for tool functions
ToolFunction = Callable[..., Any]


# Rate limiter
@dataclass
class RateLimit:
    """Rate limiting configuration for a tool."""

    max_calls: int = 10
    window_seconds: int = 60
    _calls: list[float] = field(default_factory=list)

    def is_allowed(self) -> bool:
        """Check if a call is allowed under rate limits."""
        now = time.time()
        # Remove calls outside the window
        self._calls = [t for t in self._calls if now - t < self.window_seconds]
        return len(self._calls) < self.max_calls

    def record_call(self) -> None:
        """Record a call for rate limiting."""
        self._calls.append(time.time())

    def reset(self) -> None:
        """Reset the rate limiter."""
        self._calls.clear()


# Tool definition
@dataclass
class ToolDefinition:
    """Definition of a tool."""

    name: str
    description: str
    function: ToolFunction
    parameters: dict[str, Any] = field(default_factory=dict)
    rate_limit: Optional[RateLimit] = None
    requires_approval: bool = False
    restricted: bool = False


# Dangerous commands that require Sentinel approval
DANGEROUS_COMMANDS = {
    "rm -rf",
    "rm -rf /",
    "chmod 777",
    "chmod -R 777",
    "dd if=",
    ":(){:|:&};:",
    "mkfs",
    "dd bs=",
    "> /dev/sd",
    "wget | sh",
    "curl | sh",
    "chown -R",
    "shutdown",
    "reboot",
    "init 0",
    "init 6",
}

# Blocked file paths
BLOCKED_PATHS = {
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "~/.ssh",
    "~/.bashrc",
    "/etc",
    "/sys",
    "/proc",
}


class ToolRegistry:
    """
    Registry for managing tools.

    Provides tool registration, validation, and execution with
    built-in tools for memory, file system, and agent operations.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: dict[str, ToolDefinition] = {}
        self._execution_history: list[dict[str, Any]] = []
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """Register all built-in tools."""
        self.register(
            "search_memory",
            "Search memory for relevant context",
            self._search_memory,
            parameters={
                "query": {"type": "string", "required": True},
                "limit": {"type": "integer", "default": 5},
            },
            rate_limit=RateLimit(max_calls=30, window_seconds=60),
        )

        self.register(
            "call_agent",
            "Send a message to another agent via A2A",
            self._call_agent,
            parameters={
                "agent_name": {"type": "string", "required": True},
                "message": {"type": "string", "required": True},
            },
            rate_limit=RateLimit(max_calls=20, window_seconds=60),
            requires_approval=True,
        )

        self.register(
            "read_file",
            "Read content from a file",
            self._read_file,
            parameters={
                "path": {"type": "string", "required": True},
                "offset": {"type": "integer", "default": 0},
                "limit": {"type": "integer", "default": 1000},
            },
            rate_limit=RateLimit(max_calls=50, window_seconds=60),
        )

        self.register(
            "write_file",
            "Write content to a file",
            self._write_file,
            parameters={
                "path": {"type": "string", "required": True},
                "content": {"type": "string", "required": True},
            },
            rate_limit=RateLimit(max_calls=20, window_seconds=60),
            requires_approval=True,
        )

        self.register(
            "run_command",
            "Execute a shell command",
            self._run_command,
            parameters={
                "command": {"type": "string", "required": True},
                "timeout": {"type": "integer", "default": 30},
            },
            rate_limit=RateLimit(max_calls=10, window_seconds=60),
            requires_approval=True,
            restricted=True,
        )

        self.register(
            "list_directory",
            "List contents of a directory",
            self._list_directory,
            parameters={
                "path": {"type": "string", "default": "."},
            },
            rate_limit=RateLimit(max_calls=30, window_seconds=60),
        )

        logger.info("Built-in tools registered")

    def register(
        self,
        name: str,
        description: str,
        function: ToolFunction,
        parameters: Optional[dict[str, Any]] = None,
        rate_limit: Optional[RateLimit] = None,
        requires_approval: bool = False,
        restricted: bool = False,
    ) -> None:
        """
        Register a tool.

        Args:
            name: Tool name
            description: Tool description
            function: Tool function
            parameters: Parameter schema
            rate_limit: Rate limiting configuration
            requires_approval: Whether tool requires approval
            restricted: Whether tool is restricted
        """
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            function=function,
            parameters=parameters or {},
            rate_limit=rate_limit,
            requires_approval=requires_approval,
            restricted=restricted,
        )
        logger.debug(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            ToolDefinition or None
        """
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """
        List all available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "requires_approval": tool.requires_approval,
                "restricted": tool.restricted,
            }
            for tool in self._tools.values()
        ]

    def validate_parameters(
        self, tool_name: str, params: dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate parameters for a tool.

        Args:
            tool_name: Tool name
            params: Parameters to validate

        Returns:
            Tuple of (valid, error_message)
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False, f"Tool not found: {tool_name}"

        # Check required parameters
        for param_name, schema in tool.parameters.items():
            if schema.get("required", False) and param_name not in params:
                return False, f"Missing required parameter: {param_name}"

        return True, None

    def check_rate_limit(self, tool_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if a tool call is allowed under rate limits.

        Args:
            tool_name: Tool name

        Returns:
            Tuple of (allowed, error_message)
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False, f"Tool not found: {tool_name}"

        if tool.rate_limit and not tool.rate_limit.is_allowed():
            return False, f"Rate limit exceeded for tool: {tool_name}"

        if tool.rate_limit:
            tool.rate_limit.record_call()

        return True, None

    async def execute(
        self,
        tool_name: str,
        params: dict[str, Any],
        approved: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a tool.

        Args:
            tool_name: Tool name
            params: Tool parameters
            approved: Whether the tool has been approved (for restricted tools)

        Returns:
            Execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}

        # Check rate limits
        allowed, error = self.check_rate_limit(tool_name)
        if not allowed:
            return {"success": False, "error": error}

        # Check approval for restricted tools
        if tool.restricted and not approved:
            return {
                "success": False,
                "error": f"Tool {tool_name} requires approval",
                "requires_approval": True,
            }

        # Validate parameters
        valid, error = self.validate_parameters(tool_name, params)
        if not valid:
            return {"success": False, "error": error}

        # Execute tool
        start_time = time.time()
        try:
            result = await tool.function(**params)
            execution_time = time.time() - start_time

            self._execution_history.append(
                {
                    "tool": tool_name,
                    "params": params,
                    "result": result,
                    "time": execution_time,
                }
            )

            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {"success": False, "error": str(e)}

    # Built-in tool implementations

    async def _search_memory(
        self, query: str, limit: int = 5
    ) -> dict[str, Any]:
        """Search memory for relevant context."""
        # This is a placeholder - in a full implementation, this would
        # query the actual memory system
        return {
            "query": query,
            "results": [],
            "count": 0,
            "message": "Memory search not configured - configure memory system for full functionality",
        }

    async def _call_agent(
        self, agent_name: str, message: str
    ) -> dict[str, Any]:
        """Send a message to another agent."""
        # This is a placeholder - in a full implementation, this would
        # use the A2A protocol to send messages
        return {
            "agent": agent_name,
            "message": message,
            "status": "not_delivered",
            "message": "A2A not configured - configure gateway for full functionality",
        }

    async def _read_file(
        self, path: str, offset: int = 0, limit: int = 1000
    ) -> dict[str, Any]:
        """Read content from a file."""
        file_path = Path(path).resolve()

        # Security check - prevent access to blocked paths
        for blocked in BLOCKED_PATHS:
            if str(file_path).startswith(blocked):
                return {"success": False, "error": f"Access blocked: {path}"}

        try:
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {path}"}

            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Apply offset and limit
            selected_lines = lines[offset : offset + limit]

            return {
                "success": True,
                "path": str(file_path),
                "content": "\n".join(selected_lines),
                "total_lines": len(lines),
                "returned_lines": len(selected_lines),
                "offset": offset,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _write_file(
        self, path: str, content: str
    ) -> dict[str, Any]:
        """Write content to a file."""
        file_path = Path(path).resolve()

        # Security check - prevent access to blocked paths
        for blocked in BLOCKED_PATHS:
            if str(file_path).startswith(blocked):
                return {"success": False, "error": f"Access blocked: {path}"}

        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            file_path.write_text(content, encoding="utf-8")

            logger.info(f"File written: {file_path}")

            return {
                "success": True,
                "path": str(file_path),
                "bytes_written": len(content),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_command(
        self, command: str, timeout: int = 30
    ) -> dict[str, Any]:
        """Execute a shell command with safety limits."""
        # Security check - check for dangerous commands
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command:
                logger.warning(f"Blocked dangerous command: {command}")
                return {
                    "success": False,
                    "error": "Command blocked for safety",
                    "requires_approval": True,
                }

        # Security check - prevent certain path access
        words = command.split()
        for word in words:
            if word.startswith("/"):
                for blocked in BLOCKED_PATHS:
                    if word.startswith(blocked):
                        return {
                            "success": False,
                            "error": f"Access to blocked path: {word}",
                        }

        try:
            # Execute command with timeout
            result = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=timeout,
            )

            stdout, stderr = await result.communicate()

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }

        except asyncio.TimeoutError:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _list_directory(
        self, path: str = "."
    ) -> dict[str, Any]:
        """List contents of a directory."""
        dir_path = Path(path).resolve()

        # Security check
        for blocked in BLOCKED_PATHS:
            if str(dir_path).startswith(blocked):
                return {"success": False, "error": f"Access blocked: {path}"}

        try:
            if not dir_path.exists():
                return {"success": False, "error": f"Directory not found: {path}"}

            entries = []
            for entry in dir_path.iterdir():
                entries.append(
                    {
                        "name": entry.name,
                        "type": "dir" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else 0,
                    }
                )

            return {
                "success": True,
                "path": str(dir_path),
                "entries": entries,
                "count": len(entries),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Get the execution history."""
        return self._execution_history

    def reset_rate_limits(self) -> None:
        """Reset all rate limits."""
        for tool in self._tools.values():
            if tool.rate_limit:
                tool.rate_limit.reset()


# Global registry instance
_default_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry.

    Returns:
        ToolRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def list_tools() -> list[dict[str, Any]]:
    """
    List all available tools.

    Returns:
        List of tool definitions
    """
    return get_tool_registry().list_tools()


async def execute_tool(
    tool_name: str,
    params: dict[str, Any],
    approved: bool = False,
) -> dict[str, Any]:
    """
    Execute a tool from the global registry.

    Args:
        tool_name: Tool name
        params: Tool parameters
        approved: Whether the tool has been approved

    Returns:
        Execution result
    """
    return await get_tool_registry().execute(tool_name, params, approved)