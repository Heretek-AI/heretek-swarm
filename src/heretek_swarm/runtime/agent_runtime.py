"""
ElizaOS-Style Agent Runtime.

This module provides the core agent runtime that powers the Heretek Swarm,
inspired by the elizaOS runtime patterns.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger("AgentRuntime")


class AgentState(Enum):
    """Agent lifecycle states."""

    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentContext:
    """Agent execution context."""

    agent_id: str
    state: AgentState = AgentState.IDLE
    working_memory: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    active_tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ThoughtResult:
    """Result from a think operation."""

    response: str
    reasoning: str
    confidence: float = 1.0
    next_actions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ActionResult:
    """Result from an act operation."""

    success: bool
    result: Any
    error: Optional[str] = None


# Type alias for tool handlers
ToolHandler = Callable[..., Any]


class AgentRuntime:
    """
    ElizaOS-style agent runtime.

    Provides think/act cycle with memory integration and tool execution
    for autonomous agent behavior.
    """

    def __init__(
        self,
        agent_id: str,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
    ) -> None:
        """
        Initialize the agent runtime.

        Args:
            agent_id: Unique identifier for this agent
            model_provider: LLM provider (openai, anthropic, etc.)
            model_name: Model name to use
        """
        self.agent_id = agent_id
        self.model_provider = model_provider
        self.model_name = model_name
        self.context = AgentContext(agent_id=agent_id)
        self._memory: Optional[Any] = None  # Injected memory system
        self._tools: dict[str, ToolHandler] = {}
        self._character: Optional[dict[str, Any]] = None  # Injected character
        self._model_client: Optional[Any] = None  # Injected LLM client

    def set_memory(self, memory_system: Any) -> None:
        """Set the memory system for this agent."""
        self._memory = memory_system
        logger.debug(f"[{self.agent_id}] Memory system attached")

    def set_character(self, character: dict[str, Any]) -> None:
        """Set the character definition for this agent."""
        self._character = character
        logger.debug(f"[{self.agent_id}] Character set: {character.get('name', 'Unknown')}")

    def set_model_client(self, client: Any) -> None:
        """Set the LLM client for this agent."""
        self._model_client = client
        logger.debug(f"[{self.agent_id}] Model client attached")

    def register_tool(self, name: str, handler: ToolHandler) -> None:
        """
        Register a tool with the agent.

        Args:
            name: Tool name
            handler: Tool handler function
        """
        self._tools[name] = handler
        self.context.active_tools.append(name)
        logger.debug(f"[{self.agent_id}] Registered tool: {name}")

    def register_tools(self, tools: dict[str, ToolHandler]) -> None:
        """
        Register multiple tools at once.

        Args:
            tools: Dictionary of tool name -> handler mappings
        """
        for name, handler in tools.items():
            self.register_tool(name, handler)

    async def think(self, prompt: str) -> ThoughtResult:
        """
        Process a prompt through the think cycle.

        This method:
        1. Searches memory for relevant context
        2. Builds a context prompt
        3. Calls the LLM to generate a response

        Args:
            prompt: User input or system prompt

        Returns:
            ThoughtResult with response, reasoning, and potential actions
        """
        self.context.state = AgentState.THINKING
        logger.debug(f"[{self.agent_id}] Thinking: {prompt[:50]}...")

        try:
            # Search memory for relevant context
            memories = await self._search_memory(prompt)

            # Build context from character and memories
            context_prompt = self._build_context(prompt, memories)

            # Generate response using LLM
            response_text, reasoning = await self._generate_response(context_prompt)

            # Store the interaction in memory
            await self._store_interaction(prompt, response_text)

            # Parse next actions if any
            next_actions = self._parse_actions(response_text)

            result = ThoughtResult(
                response=response_text,
                reasoning=reasoning,
                next_actions=next_actions,
            )

            self.context.state = AgentState.IDLE
            logger.debug(f"[{self.agent_id}] Thought complete")

            return result

        except Exception as e:
            logger.error(f"[{self.agent_id}] Think error: {e}")
            self.context.state = AgentState.ERROR
            return ThoughtResult(
                response="I encountered an error while processing your request.",
                reasoning=f"Error: {str(e)}",
                confidence=0.0,
            )

    async def act(self, action: str, params: dict[str, Any]) -> ActionResult:
        """
        Execute an action.

        Args:
            action: Action name (must be registered tool)
            params: Action parameters

        Returns:
            ActionResult with success status and result
        """
        self.context.state = AgentState.ACTING
        logger.debug(f"[{self.agent_id}] Acting: {action}")

        try:
            if action not in self._tools:
                raise ValueError(f"Unknown action: {action}")

            # Execute the tool
            handler = self._tools[action]
            result = await handler(**params)

            # Store action in memory
            await self._store_action(action, params, result)

            self.context.state = AgentState.IDLE
            logger.debug(f"[{self.agent_id}] Action complete: {action}")

            return ActionResult(success=True, result=result)

        except Exception as e:
            logger.error(f"[{self.agent_id}] Act error: {e}")
            self.context.state = AgentState.ERROR
            return ActionResult(success=False, result=None, error=str(e))

    async def _search_memory(self, query: str) -> list[dict[str, Any]]:
        """
        Search memory for relevant context.

        Args:
            query: Search query

        Returns:
            List of relevant memory entries
        """
        if not self._memory:
            return []

        try:
            from heretek_swarm.memory.base import MemoryQuery

            memory_query = MemoryQuery(
                query_text=query,
                limit=5,
                similarity_threshold=0.5,
            )
            results = await self._memory.query(memory_query)
            return [
                {"content": str(entry.content), "metadata": entry.metadata}
                for entry in results
            ]
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Memory search failed: {e}")
            return []

    def _build_context(self, prompt: str, memories: list[dict[str, Any]]) -> str:
        """
        Build context prompt from character and memories.

        Args:
            prompt: User prompt
            memories: Retrieved memory entries

        Returns:
            Formatted context prompt
        """
        parts = []

        # Add character context if available
        if self._character:
            bio = self._character.get("bio", "")
            lore = self._character.get("lore", "")
            topics = self._character.get("topics", [])
            knowledge = self._character.get("knowledge", [])

            if bio:
                parts.append(f"Role: {bio}")
            if lore:
                parts.append(f"Background: {lore}")
            if topics:
                parts.append(f"Topics: {', '.join(topics)}")
            if knowledge:
                parts.append(f"Knowledge: {', '.join(knowledge)}")

        # Add relevant memories
        if memories:
            parts.append("Relevant context:")
            for mem in memories:
                content = mem.get("content", "")
                if content:
                    parts.append(f"- {content}")

        # Add conversation history
        if self.context.conversation_history:
            parts.append("Conversation history:")
            for msg in self.context.conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"{role}: {content[:100]}")

        # Add current prompt
        parts.append(f"User: {prompt}")

        # Add system instruction
        parts.append("Please respond helpfully and accurately.")

        return "\n\n".join(parts)

    async def _generate_response(
        self, context_prompt: str
    ) -> tuple[str, str]:
        """
        Generate response using the LLM.

        Args:
            context_prompt: Formatted context prompt

        Returns:
            Tuple of (response_text, reasoning)
        """
        if self._model_client:
            try:
                response = await self._model_client.generate(
                    model=self.model_name,
                    prompt=context_prompt,
                )
                return response.get("text", ""), response.get("reasoning", "")
            except Exception as e:
                logger.warning(f"[{self.agent_id}] Model client error: {e}")

        # Fallback: simple response without LLM
        # This allows basic functionality without an API key
        return f"I processed your request: {context_prompt[:100]}...", "Using fallback response"

    async def _store_interaction(
        self, prompt: str, response: str
    ) -> None:
        """
        Store the interaction in memory.

        Args:
            prompt: User prompt
            response: Agent response
        """
        if not self._memory:
            return

        try:
            await self._memory.store(
                content={"prompt": prompt, "response": response},
                metadata={
                    "type": "interaction",
                    "agent_id": self.agent_id,
                },
            )
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Failed to store interaction: {e}")

    async def _store_action(
        self, action: str, params: dict[str, Any], result: Any
    ) -> None:
        """
        Store an action in memory.

        Args:
            action: Action name
            params: Action parameters
            result: Action result
        """
        if not self._memory:
            return

        try:
            await self._memory.store(
                content={"action": action, "params": params, "result": str(result)},
                metadata={
                    "type": "action",
                    "agent_id": self.agent_id,
                    "action": action,
                },
            )
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Failed to store action: {e}")

    def _parse_actions(self, response: str) -> list[dict[str, Any]]:
        """
        Parse potential actions from response.

        Args:
            response: Agent response

        Returns:
            List of potential actions
        """
        # Simple parsing - in a full implementation, this would use
        # structured output or a more sophisticated approach
        actions = []

        # Check for common action patterns
        response_lower = response.lower()

        if "search" in response_lower:
            actions.append({"type": "search_memory", "query": response})
        if "call" in response_lower or "route" in response_lower:
            actions.append({"type": "call_agent", "message": response})
        if "write" in response_lower or "create" in response_lower:
            actions.append({"type": "write_file", "content": response})

        return actions

    def get_state(self) -> dict[str, Any]:
        """
        Get the current agent state.

        Returns:
            Dictionary with agent state information
        """
        return {
            "agent_id": self.agent_id,
            "state": self.context.state.value,
            "provider": self.model_provider,
            "model": self.model_name,
            "character": self._character.get("name") if self._character else None,
            "tools": list(self._tools.keys()),
            "memory_configured": self._memory is not None,
        }

    def reset(self) -> None:
        """Reset the agent context."""
        self.context = AgentContext(agent_id=self.agent_id)
        logger.debug(f"[{self.agent_id}] Context reset")