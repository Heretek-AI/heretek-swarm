"""
LangroidAdapter - Langroid Conversational AI Adapter for Heretek Swarm

This module provides Langroid integration:
- Agent wrapper for Langroid agents
- Conversation state management
- Multi-turn conversation support
- Integration with Swarms Agent via adapter pattern
- Conversation handler mixin

Reference: https://github.com/langroid/langroid
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

_logger = structlog.get_logger("LangroidAdapter")

# Try to import Langroid, but make it optional
try:
    from langroid.agent import Agent as LangroidAgentBase
    from langroid.embedding import EmbeddingConfig
    from langroid.language import LanguageModelConfig
    from langroid.vector_store import VectorStoreConfig
    LANGROID_AVAILABLE = True
except ImportError:
    LANGROID_AVAILABLE = False
    _LangroidAgentBase = object


class ConversationState(Enum):
    """Conversation states."""
    IDLE = "idle"
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentConversation:
    """
    Conversation state dataclass.
    
    Attributes:
        conversation_id: Unique conversation ID
        agent_id: Agent ID
        messages: List of (role, content) tuples
        state: Current conversation state
        created_at: Conversation start time
        updated_at: Last update time
        metadata: Additional metadata
    """
    conversation_id: str
    agent_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    state: ConversationState = ConversationState.IDLE
    created_at: str = field(default_factory=datetime.now(timezone.utc).isoformat)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, _role: str, _content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages."""
        return self.messages

    def get_last_message(self) -> Optional[Dict[str, str]]:
        """Get last message."""
        return self.messages[-1] if self.messages else None


@dataclass
class LangroidConfig:
    """
    Configuration for Langroid agent.
    
    Attributes:
        agent_name: Agent name
        llm_config: Language model configuration
        embedding_config: Embedding configuration
        vector_store_config: Vector store configuration
        use_tools: Enable tool use
        debug: Enable debug mode
    """
    agent_name: str = "heretek-agent"
    llm_config: Optional[Dict[str, Any]] = None
    embedding_config: Optional[Dict[str, Any]] = None
    vector_store_config: Optional[Dict[str, Any]] = None
    use_tools: bool = False
    debug: bool = False


class LangroidAgent:
    """
    Langroid agent wrapper.
    
    Wraps Langroid agents for use in Heretek Swarm:
    - Conversation state management
    - Async message handling
    - Tool integration
    - Integration with Swarms Agent
    
    Example:
        ```python
        # Initialize agent
        agent = LangroidAgent(
            agent_id="agent-1",
            name="Assistant",
            config=LangroidConfig(
                agent_name="assistant",
                llm_config={"provider": "openai", "model": "gpt-4"}
            )
        )
        
        # Start conversation
        _conv_id = await agent.start_conversation("user-1")
        
        # Send message
        _response = await agent.send_message("Hello!")
        
        # Receive response
        _response = await agent.receive_message()
        ```
    """

    def __init__(self, _agent_id: Optional[str], _name: Optional[str], _config: Optional[LangroidConfig], _swarms_agent: Optional[Any], _max_conversations: int, _conversation_timeout: float) -> None:
        """
        Initialize LangroidAgent.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            config: Langroid configuration
            swarms_agent: Optional Swarms Agent for LLM
            max_conversations: Max concurrent conversations
            conversation_timeout: Conversation timeout in seconds
        """
        self.agent_id = agent_id or f"langroid_{uuid.uuid4().hex[:8]}"
        self.name = name or "LangroidAgent"
        self.config = config or LangroidConfig(agent_name=self.name)
        self.swarms_agent = swarms_agent

        self.max_conversations = max_conversations
        self.conversation_timeout = conversation_timeout

        # Langroid agent (if available)
        self._langroid_agent = None
        if LANGROID_AVAILABLE and self.config:
            try:
                self._langroid_agent = self._create_langroid_agent()
            except Exception as e:
                logger.warning(f"Failed to create Langroid agent: {e}")

        # Conversations
        self._conversations: Dict[str, AgentConversation] = {}
        self._active_conversations: Set[str] = set()

        # Message queues
        self._message_queues: Dict[str, asyncio.Queue] = {}

        # Callbacks
        self._on_message: Optional[callable] = None
        self._on_error: Optional[callable] = None

        logger.info(
            f"LangroidAgent initialized",
            _extra = {
                "agent_id": self.agent_id,
                "name": self.name,
                "langroid_available": LANGROID_AVAILABLE,
            },
        )

    def _create_langroid_agent(self) -> Any:
        """Create Langroid agent instance."""
        llm_config = LanguageModelConfig(
            **{} if self.config.llm_config is None else self.config.llm_config
        )
        return LangroidAgentBase(
            name=self.config.agent_name,
            _llm = llm_config,
        )

    @property
    def is_available(self) -> bool:
        """Check if Langroid is available."""
        return LANGROID_AVAILABLE and self._langroid_agent is not None

    @property
    def active_conversation_count(self) -> int:
        """Get number of active conversations."""
        return len(self._active_conversations)

    async def start_conversation(self, _user_id: str, _initial_message: Optional[str], _metadata: Optional[Dict[str, Any]]) -> str:
        """
        Start a new conversation.
        
        Args:
            user_id: User ID
            initial_message: Optional initial message
            metadata: Optional conversation metadata
            
        Returns:
            Conversation ID
        """
        if len(self._conversations) >= self.max_conversations:
            raise RuntimeError("Max conversations reached")

        _conversation_id = f"conv_{uuid.uuid4().hex[:8]}"

        _conversation = AgentConversation(
            _conversation_id = conversation_id,
            agent_id=self.agent_id,
            _metadata = metadata or {},
        )

        if initial_message:
            conversation.add_message("user", initial_message)
            conversation.state = ConversationState.ACTIVE

        self._conversations[conversation_id] = conversation
        self._active_conversations.add(conversation_id)
        self._message_queues[conversation_id] = asyncio.Queue()

        logger.info(
            f"Started conversation",
            _extra = {
                "conversation_id": conversation_id,
                "user_id": user_id,
            },
        )

        return conversation_id

    async def end_conversation(self, _conversation_id: str) -> None:
        """
        End a conversation.
        
        Args:
            conversation_id: Conversation ID
        """
        if conversation_id not in self._conversations:
            return

        _conversation = self._conversations[conversation_id]
        conversation.state = ConversationState.COMPLETED

        if conversation_id in self._active_conversations:
            self._active_conversations.remove(conversation_id)

        if conversation_id in self._message_queues:
            del self._message_queues[conversation_id]

        logger.info(f"Ended conversation {conversation_id}")

    async def send_message(self, _content: str, _conversation_id: Optional[str], _role: str) -> str:
        """
        Send a message in a conversation.
        
        Args:
            content: Message content
            conversation_id: Conversation ID (creates new if None)
            role: Message role (user/assistant/system)
            
        Returns:
            Response content
        """
        # Create new conversation if needed
        if conversation_id is None:
            _conversation_id = await self.start_conversation("default", content)
        elif conversation_id not in self._conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        _conversation = self._conversations[conversation_id]

        # Add message to conversation
        conversation.add_message(role, content)
        conversation.state = ConversationState.ACTIVE

        # Generate response
        try:
            _response = await self._generate_response(conversation)
            conversation.add_message("assistant", response)

            logger.debug(
                f"Sent message",
                _extra = {"conversation_id": conversation_id, "response": response[:50]},
            )

            return response

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            conversation.state = ConversationState.ERROR
            raise

    async def receive_message(self, _conversation_id: str, _timeout: Optional[float]) -> Optional[str]:
        """
        Receive a message from conversation queue.
        
        Args:
            conversation_id: Conversation ID
            timeout: Optional timeout
            
        Returns:
            Message content or None
        """
        if conversation_id not in self._message_queues:
            return None

        _queue = self._message_queues[conversation_id]

        try:
            if timeout:
                _message = await asyncio.wait_for(
                    queue.get(),
                    _timeout = timeout,
                )
            else:
                _message = await queue.get()

            return message

        except asyncio.TimeoutError:
            return None

    async def _generate_response(self, _conversation: AgentConversation) -> str:
        """Generate response using LLM."""
        # Use Langroid if available
        if self.is_available and self._langroid_agent:
            _messages = self._format_messages(conversation)
            return await self._langroid_agent.chat(messages)

        # Fallback to Swarms Agent
        if self.swarms_agent:
            return await self._use_swarms_agent(conversation)

        # Simple echo fallback
        return await self._echo_response(conversation)

    def _format_messages(self, _conversation: AgentConversation) -> List[Dict[str, str]]:
        """Format messages for Langroid."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation.get_messages()
        ]

    async def _use_swarms_agent(self, _conversation: AgentConversation) -> str:
        """Use Swarms agent for response."""
        _messages = conversation.get_messages()

        if not messages:
            return "No messages in conversation"

        # Get last user message
        _last_user = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                _last_user = msg["content"]
                break

        if last_user is None:
            return "No user message found"

        # Run through Swarms agent
        try:
            _response = await asyncio.to_thread(
                self.swarms_agent.run,
                last_user,
            )
            return str(response)
        except Exception as e:
            logger.error(f"Swarms agent error: {e}")
            return f"Error generating response: {e}"

    async def _echo_response(self, _conversation: AgentConversation) -> str:
        """Simple echo response."""
        _messages = conversation.get_messages()

        if not messages:
            return "Hello! How can I help you?"

        _last = messages[-1]

        if last["role"] == "user":
            return f"I received your message: {last['content'][:50]}..."

        return "Understood."

    def get_conversation(self, _conversation_id: str) -> Optional[AgentConversation]:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)

    def get_conversations(self) -> List[AgentConversation]:
        """Get all conversations."""
        return list(self._conversations.values())

    def get_active_conversations(self) -> List[AgentConversation]:
        """Get active conversations."""
        return [
            conv for conv in self._conversations.values()
            if conv.state == ConversationState.ACTIVE
        ]

    def set_message_callback(self, _callback: callable) -> None:
        """Set callback for incoming messages."""
        self._on_message = callback

    def set_error_callback(self, _callback: callable) -> None:
        """Set callback for errors."""
        self._on_error = callback

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "is_available": self.is_available,
            "active_conversations": len(self._active_conversations),
            "total_conversations": len(self._conversations),
        }


class ConversationHandlerMixin:
    """
    Mixin to add conversation handling to AgentActor.
    
    Provides multi-turn conversation support:
    - Conversation state management
    - Message history
    - Conversation persistence
    
    Example:
        ```python
        class ConversationalAgent(ConversationHandlerMixin, AgentActor):
            pass
        
        agent = ConversationalAgent(agent_id="agent-1")
        await agent.start_conversation("user-1")
        await agent.send_message("Hello!")
        ```
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize mixin."""
        self._conversations: Dict[str, AgentConversation] = {}
        self._active_conversation: Optional[str] = None
        self._conversation_config: Dict[str, Any] = kwargs.copy()

    async def start_conversation(self, _user_id: str, _initial_message: Optional[str]) -> str:
        """
        Start a new conversation.
        
        Args:
            user_id: User ID
            initial_message: Optional initial message
            
        Returns:
            Conversation ID
        """
        _conversation_id = f"conv_{uuid.uuid4().hex[:8]}"

        _conversation = AgentConversation(
            _conversation_id = conversation_id,
            agent_id=self.agent_id,
        )

        if initial_message:
            conversation.add_message("user", initial_message)
            conversation.state = ConversationState.ACTIVE

        self._conversations[conversation_id] = conversation
        self._active_conversation = conversation_id

        logger.debug(
            f"[{self.agent_id}] Started conversation",
            _extra = {"conversation_id": conversation_id},
        )

        return conversation_id

    async def end_conversation(self, _conversation_id: str) -> None:
        """
        End a conversation.
        
        Args:
            conversation_id: Conversation ID
        """
        if conversation_id not in self._conversations:
            return

        _conversation = self._conversations[conversation_id]
        conversation.state = ConversationState.COMPLETED

        if self._active_conversation == conversation_id:
            self._active_conversation = None

        logger.debug(f"[{self.agent_id}] Ended conversation {conversation_id}")

    async def send_message(self, _content: str, _conversation_id: Optional[str], _role: str) -> str:
        """
        Send a message in conversation.
        
        Args:
            content: Message content
            conversation_id: Conversation ID (uses active if None)
            role: Message role
            
        Returns:
            Response content
        """
        _conv_id = conversation_id or self._active_conversation

        if conv_id is None:
            _conv_id = await self.start_conversation("default", content)
        elif conv_id not in self._conversations:
            raise ValueError(f"Conversation {conv_id} not found")

        _conversation = self._conversations[conv_id]
        conversation.add_message(role, content)

        # Generate response
        _response = await self._generate_response(conversation)
        conversation.add_message("assistant", response)

        return response

    async def _generate_response(self, _conversation: AgentConversation) -> str:
        """Generate response (override in subclass)."""
        _last_msg = conversation.get_last_message()

        if last_msg and last_msg["role"] == "user":
            return f"I received: {last_msg['content'][:50]}..."

        return "How can I help?"

    def get_conversation(self, _conversation_id: str) -> Optional[AgentConversation]:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)

    def get_active_conversation(self) -> Optional[AgentConversation]:
        """Get active conversation."""
        if self._active_conversation:
            return self._conversations.get(self._active_conversation)
        return None

    @property
    def has_active_conversation(self) -> bool:
        """Check if has active conversation."""
        return self._active_conversation is not None