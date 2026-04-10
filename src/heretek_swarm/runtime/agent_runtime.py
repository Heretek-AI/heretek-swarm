"""
Agent Runtime - ElizaOS Pattern Implementation

Runtime environment for single agent with state management, memory, and tools.
Reference: MiniMax Audit Lines 153-242 (elizaOS runtime patterns)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
import structlog

_logger = structlog.get_logger(__name__)


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentContext:
    """Runtime context for an agent."""
    agent_id: str
    state: AgentState = AgentState.IDLE
    working_memory: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict] = field(default_factory=list)
    active_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRuntime:
    """
    Runtime environment for a single agent.
    
    Manages state, memory, and tool execution.
    Pattern stolen from elizaOS/packages/core/runtime/
    """
    
    def __init__(self, agent_id: str, model_provider: str, model_name: str, character: Optional[Dict]):
        self.agent_id = agent_id
        self.model_provider = model_provider
        self.model_name = model_name
        self.character = character or {}
        self.context = AgentContext(agent_id=agent_id)
        self._memory = None  # Injected
        self._tools: Dict[str, Callable] = {}
        self._initialized = False
    
    async def initialize(self, memory_backend) -> None:
        """Initialize runtime with memory backend."""
        self._memory = memory_backend
        self._initialized = True
        logger.info("agent_runtime_initialized", agent_id=self.agent_id)
    
    def register_tool(self, name: str, handler: Callable) -> None:
        """Register a tool with the runtime."""
        self._tools[name] = handler
        logger.debug("tool_registered", agent_id=self.agent_id, tool=name)
    
    def get_tools(self) -> List[str]:
        """Get list of registered tools."""
        return list(self._tools.keys())
    
    async def think(self, prompt: str) -> str:
        """
        Process input and generate response.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response
        """
        self.context.state = AgentState.THINKING
        self.context.last_activity = datetime.now(timezone.utc)
        
        try:
            # Get relevant memories
            _memories = []
            if self._memory:
                try:
                    from memory.base import MemoryQuery
                    _query = MemoryQuery(
                        _query_text = prompt,
                        _agent_ids = [self.agent_id],
                        _limit = 5,
                    )
                    _result = await self._memory.search(query)
                    _memories = result.entries[:5]
                except Exception as e:
                    logger.warning("memory_search_failed", error=str(e))
            
            # Build context with memories
            context = self._build_context(memories, prompt)
            
            # Generate response via LiteLLM
            _response = await self._call_llm(context)
            
            # Store in conversation history
            self.context.conversation_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.context.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error("think_failed", agent_id=self.agent_id, error=str(e))
            self.context.state = AgentState.ERROR
            raise
        finally:
            self.context.state = AgentState.IDLE
    
    async def act(self, action: str, params: Dict) -> Any:
        """
        Execute an action using registered tools.
        
        Args:
            action: Tool name
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        self.context.state = AgentState.ACTING
        self.context.last_activity = datetime.now(timezone.utc)
        
        try:
            if action not in self._tools:
                raise ValueError(f"Unknown action: {action}")
            
            _result = await self._tools[action](**params)
            
            # Store action in memory
            if self._memory:
                try:
                    from memory.base import MemoryEntry, MemoryType, MemoryTier
                    _entry = MemoryEntry(
                        agent_id=self.agent_id,
                        content=f"Executed {action} with {params}",
                        _memory_type = MemoryType.EPISODIC,
                        _tier = MemoryTier.PERSISTENT,
                        _metadata = {"type": "action", "action": action, "result": str(result)},
                    )
                    await self._memory.store(entry)
                except Exception as e:
                    logger.warning("memory_store_failed", error=str(e))
            
            return result
            
        except Exception as e:
            logger.error("act_failed", agent_id=self.agent_id, action=action, error=str(e))
            self.context.state = AgentState.ERROR
            raise
        finally:
            self.context.state = AgentState.IDLE
    
    def _build_context(self, memories: List, prompt: str) -> str:
        """
        Build LLM context with memories and character.
        
        Args:
            memories: Retrieved memories
            prompt: User prompt
            
        Returns:
            Formatted context string
        """
        _context_parts = []
        
        # Character system prompt
        if self.character:
            _bio = self.character.get("bio", "")
            if bio:
                context_parts.append(f"System: {bio}")
            
            _style = self.character.get("style", {}).get("all", [])
            if style:
                context_parts.append(f"Style: {', '.join(style)}")
        
        # Memories
        if memories:
            _memory_texts = [m.content for m in memories[:5]]
            context_parts.append(f"Memories:\n" + "\n".join(f"- {m}" for m in memory_texts))
        
        # Conversation history (last 10)
        _recent_history = self.context.conversation_history[-10:]
        if recent_history:
            _history_text = "\n".join(f"{h['role']}: {h['content']}" for h in recent_history)
            context_parts.append(f"History:\n{history_text}")
        
        # Current prompt
        context_parts.append(f"User: {prompt}")
        
        return "\n\n".join(context_parts)
    
    async def _call_llm(self, context: str) -> str:
        """
        Call LLM for response generation.
        
        Args:
            context: Formatted context
            
        Returns:
            LLM response
        """
        try:
            import litellm
            litellm.api_key = __import__('os').getenv("OPENAI_API_KEY")
            
            _response = await litellm.acompletion(
                model=f"{self.model_provider}/{self.model_name}",
                _messages = [{"role": "user", "content": context}],
                _max_tokens = 1000,
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.warning("litellm_not_installed")
            return f"[Simulated response for: {context[:50]}...]"
        except Exception as e:
            logger.error("llm_call_failed", error=str(e))
            return f"[Error generating response: {str(e)}]"
    
    def get_status(self) -> Dict:
        """Get runtime status."""
        return {
            "agent_id": self.agent_id,
            "state": self.context.state.value,
            "model": f"{self.model_provider}/{self.model_name}",
            "tools": list(self._tools.keys()),
            "conversation_length": len(self.context.conversation_history),
            "last_activity": self.context.last_activity.isoformat(),
            "uptime": (datetime.now(timezone.utc) - self.context.created_at).total_seconds(),
        }
