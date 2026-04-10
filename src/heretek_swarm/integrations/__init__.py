"""
Integration Modules for Heretek Swarm

This package provides comprehensive integration capabilities for the heretek-swarm collective,
enabling seamless integration with external AI platforms, communication channels, and
orchestration frameworks.

Available Integrations:
- LangGraph: Graph-based workflow orchestration
- AutoGen: Microsoft AutoGen agent compatibility
- CrewAI: Crew task delegation and role mapping
- OpenAI Assistants: OpenAI Assistants API integration
- Anthropic Claude: Anthropic Messages API integration
- Discord/Slack/Telegram: Communication platform bots
- Praison: PraisonAI handoff patterns

Example Usage:
    ```python
    from heretek_swarm.integrations import (
        get_langgraph_adapter,
        get_autogen_adapter,
        get_crewai_adapter,
        get_openai_assistants_adapter,
        get_anthropic_adapter,
        get_integration_manager,
        IntegrationManager,
        IntegrationType,
    )
    
    # Get adapters
    langgraph = get_langgraph_adapter()
    autogen = get_autogen_adapter()
    crewai = get_crewai_adapter()
    openai = get_openai_assistants_adapter(api_key="your-key")
    anthropic = get_anthropic_adapter(api_key="your-key")
    
    # Use integration manager
    manager = get_integration_manager()
    await manager.register_integration(
        integration_id="my_langgraph",
        integration_type=IntegrationType.LANGGRAPH,
        name="My LangGraph Workflow",
    )
    await manager.start()
    ```

Reference: EXPANSION_ROADMAP.md Session 47 - Integration Ecosystem
"""

from .langgraph import (
    LangGraphAdapter,
    GraphNode,
    GraphEdge,
    GraphCheckpoint,
    GraphExecutionResult,
    GraphState,
    NodeStatus,
    get_langgraph_adapter,
    create_workflow_graph,
    LANGGRAPH_AVAILABLE,
)

from .autogen import (
    AutoGenAdapter,
    AutoGenMessage,
    AutoGenAgentConfig,
    GroupChatConfig,
    ToolRegistration,
    AgentRole as AutoGenAgentRole,
    MessageRole as AutoGenMessageRole,
    get_autogen_adapter,
    create_assistant_agent,
    AUTOGEN_AVAILABLE,
)

from .crewai import (
    CrewAIAdapter,
    CrewAgentConfig,
    CrewTaskConfig,
    TaskExecutionResult,
    CrewExecutionResult,
    CrewProcess,
    TaskStatus,
    AgentRole as CrewAIAgentRole,
    get_crewai_adapter,
    create_sequential_crew,
    CREWAI_AVAILABLE,
)

from .openai_assistants import (
    OpenAIAssistantsAdapter,
    AssistantConfig,
    ThreadContext,
    RunContext,
    FunctionCallRequest,
    RunStatus,
    MessageRole as OpenAIMessageRole,
    get_openai_assistants_adapter,
    create_assistant,
    OPENAI_AVAILABLE,
)

from .anthropic import (
    AnthropicAdapter,
    ToolDefinition,
    ConversationMessage,
    ConversationContext,
    ToolUseRequest,
    AnthropicMessageRole,
    StopReason,
    get_anthropic_adapter,
    create_conversation,
    ANTHROPIC_AVAILABLE,
)

from .openai_assistants import (
    MessageRole as OpenAIMessageRole,
)

from .autogen import (
    MessageRole as AutoGenMessageRole,
)

from .manager import (
    IntegrationManager,
    IntegrationConfig,
    IntegrationState,
    IntegrationEvent,
    HealthCheckResult,
    IntegrationType,
    IntegrationStatus,
    HealthStatus,
    get_integration_manager,
    initialize_integrations,
)

# Re-export existing integrations if available
try:
    from .discord_bot import DiscordBot, get_discord_bot, start_discord_bot, stop_discord_bot
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

try:
    from .slack_bot import SlackBot, get_slack_bot, start_slack_bot, stop_slack_bot
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

try:
    from .telegram_bot import TelegramBot, get_telegram_bot, start_telegram_bot, stop_telegram_bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

try:
    from .praison_handoffs import (
        AgentHandoff,
        HandoffContext,
        HandoffStatus,
        handoff_manager,
        create_handoff_sync,
    )
    PRAISON_AVAILABLE = True
except ImportError:
    PRAISON_AVAILABLE = False


__all__ = [
    # LangGraph
    "LangGraphAdapter",
    "GraphNode",
    "GraphEdge",
    "GraphCheckpoint",
    "GraphExecutionResult",
    "GraphState",
    "NodeStatus",
    "get_langgraph_adapter",
    "create_workflow_graph",
    "LANGGRAPH_AVAILABLE",
    
    # AutoGen
    "AutoGenAdapter",
    "AutoGenMessage",
    "AutoGenAgentConfig",
    "GroupChatConfig",
    "ToolRegistration",
    "AutoGenAgentRole",
    "AutoGenMessageRole",
    "get_autogen_adapter",
    "create_assistant_agent",
    "AUTOGEN_AVAILABLE",
    
    # CrewAI
    "CrewAIAdapter",
    "CrewAgentConfig",
    "CrewTaskConfig",
    "TaskExecutionResult",
    "CrewExecutionResult",
    "CrewProcess",
    "TaskStatus",
    "CrewAIAgentRole",
    "get_crewai_adapter",
    "create_sequential_crew",
    "CREWAI_AVAILABLE",
    
    # OpenAI Assistants
    "OpenAIAssistantsAdapter",
    "AssistantConfig",
    "ThreadContext",
    "RunContext",
    "FunctionCallRequest",
    "RunStatus",
    "OpenAIMessageRole",
    "get_openai_assistants_adapter",
    "create_assistant",
    "OPENAI_AVAILABLE",
    
    # Anthropic
    "AnthropicAdapter",
    "ToolDefinition",
    "ConversationMessage",
    "ConversationContext",
    "ToolUseRequest",
    "AnthropicMessageRole",
    "StopReason",
    "get_anthropic_adapter",
    "create_conversation",
    "ANTHROPIC_AVAILABLE",
    
    # Integration Manager
    "IntegrationManager",
    "IntegrationConfig",
    "IntegrationState",
    "IntegrationEvent",
    "HealthCheckResult",
    "IntegrationType",
    "IntegrationStatus",
    "HealthStatus",
    "get_integration_manager",
    "initialize_integrations",
    
    # Legacy integrations
    "DISCORD_AVAILABLE",
    "SLACK_AVAILABLE",
    "TELEGRAM_AVAILABLE",
    "PRAISON_AVAILABLE",
]

# Package version
__version__ = "0.1.0"

# Integration ecosystem version
INTEGRATION_ECOSYSTEM_VERSION = "47.0.0"
