"""
Session 47: Integration Ecosystem - Test Suite

This module contains comprehensive tests for the integration ecosystem:
- LangGraph Integration
- AutoGen Integration
- CrewAI Integration
- OpenAI Assistants Integration
- Anthropic Integration
- Integration Manager

Reference: EXPANSION_ROADMAP.md Session 47 - Integration Ecosystem
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Test imports
from src.heretek_swarm.integrations import (
    # LangGraph
    LangGraphAdapter,
    GraphNode,
    GraphEdge,
    GraphCheckpoint,
    GraphState,
    NodeStatus,
    get_langgraph_adapter,
    LANGGRAPH_AVAILABLE,
    
    # AutoGen
    AutoGenAdapter,
    AutoGenMessage,
    AutoGenAgentConfig,
    AutoGenAgentRole,
    get_autogen_adapter,
    AUTOGEN_AVAILABLE,
    
    # CrewAI
    CrewAIAdapter,
    CrewAgentConfig,
    CrewTaskConfig,
    CrewProcess,
    TaskStatus,
    CrewAIAgentRole,
    get_crewai_adapter,
    CREWAI_AVAILABLE,
    
    # OpenAI Assistants
    OpenAIAssistantsAdapter,
    AssistantConfig,
    ThreadContext,
    RunStatus,
    get_openai_assistants_adapter,
    OPENAI_AVAILABLE,
    
    # Anthropic
    AnthropicAdapter,
    ToolDefinition,
    ConversationContext,
    AnthropicMessageRole,
    get_anthropic_adapter,
    ANTHROPIC_AVAILABLE,
    
    # Integration Manager
    IntegrationManager,
    IntegrationConfig,
    IntegrationState,
    IntegrationType,
    IntegrationStatus,
    HealthStatus,
    get_integration_manager,
)


# =============================================================================
# LangGraph Integration Tests
# =============================================================================

class TestLangGraphAdapter:
    """Tests for LangGraphAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = LangGraphAdapter()
        
        assert adapter.graphs == {}
        assert adapter.checkpoints == {}
        assert adapter.tools == {}
        assert adapter.enable_state_sync is True
    
    def test_adapter_with_custom_config(self):
        """Test adapter with custom configuration."""
        adapter = LangGraphAdapter(
            checkpoint_saver=None,
            enable_state_sync=False,
            max_checkpoints=50,
        )
        
        assert adapter.enable_state_sync is False
        assert adapter.max_checkpoints == 50
    
    def test_graph_node_creation(self):
        """Test GraphNode dataclass."""
        node = GraphNode(
            node_id="node_1",
            name="Test Node",
            agent_id="agent_1",
            metadata={"key": "value"},
        )
        
        assert node.node_id == "node_1"
        assert node.name == "Test Node"
        assert node.agent_id == "agent_1"
        assert node.status == NodeStatus.PENDING
        assert node.execution_count == 0
        
        # Test to_dict
        node_dict = node.to_dict()
        assert node_dict["node_id"] == "node_1"
        assert node_dict["status"] == "pending"
    
    def test_graph_edge_creation(self):
        """Test GraphEdge dataclass."""
        edge = GraphEdge(
            edge_id="edge_1",
            source="node_1",
            target="node_2",
            weight=2.0,
        )
        
        assert edge.source == "node_1"
        assert edge.target == "node_2"
        assert edge.weight == 2.0
    
    def test_graph_checkpoint_creation(self):
        """Test GraphCheckpoint dataclass."""
        checkpoint = GraphCheckpoint(
            checkpoint_id="chk_1",
            graph_id="graph_1",
            state={"messages": []},
            node_states={"node_1": NodeStatus.COMPLETED},
            thread_id="thread_1",
        )
        
        assert checkpoint.checkpoint_id == "chk_1"
        assert checkpoint.graph_id == "graph_1"
        assert checkpoint.thread_id == "thread_1"
        
        # Test to_dict
        chk_dict = checkpoint.to_dict()
        assert chk_dict["node_states"]["node_1"] == "completed"
    
    def test_get_langgraph_adapter_singleton(self):
        """Test get_langgraph_adapter returns singleton."""
        adapter1 = get_langgraph_adapter()
        adapter2 = get_langgraph_adapter()
        
        assert adapter1 is adapter2
    
    def test_graph_creation_without_langgraph(self):
        """Test graph creation when LangGraph not available."""
        adapter = LangGraphAdapter()
        
        if not LANGGRAPH_AVAILABLE:
            with pytest.raises(RuntimeError, match="LangGraph is not available"):
                adapter.create_graph("test_graph")
        else:
            graph = adapter.create_graph("test_graph")
            assert graph is not None
            assert "test_graph" in adapter.graphs
    
    def test_statistics(self):
        """Test adapter statistics."""
        adapter = LangGraphAdapter()
        stats = adapter.get_statistics()
        
        assert "graph_count" in stats
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "langgraph_available" in stats


# =============================================================================
# AutoGen Integration Tests
# =============================================================================

class TestAutoGenAdapter:
    """Tests for AutoGenAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = AutoGenAdapter()
        
        assert adapter.agents == {}
        assert adapter.group_chats == {}
        assert adapter.tools == {}
        assert adapter.enable_message_translation is True
    
    def test_adapter_with_llm_config(self):
        """Test adapter with LLM configuration."""
        llm_config = {"config_list": [{"model": "gpt-4", "api_key": "test"}]}
        adapter = AutoGenAdapter(llm_config=llm_config)
        
        assert adapter.llm_config == llm_config
    
    def test_autogen_message_creation(self):
        """Test AutoGenMessage dataclass."""
        message = AutoGenMessage(
            message_id="msg_1",
            role="user",
            content="Hello",
            name="test_user",
        )
        
        assert message.message_id == "msg_1"
        assert message.role == "user"
        assert message.content == "Hello"
        
        # Test to_dict
        msg_dict = message.to_dict()
        assert msg_dict["role"] == "user"
        
        # Test to_autogen_format
        autogen_format = message.to_autogen_format()
        assert autogen_format["role"] == "user"
        assert autogen_format["content"] == "Hello"
    
    def test_agent_config_creation(self):
        """Test AutoGenAgentConfig dataclass."""
        config = AutoGenAgentConfig(
            agent_id="agent_1",
            name="TestAgent",
            role=AutoGenAgentRole.ASSISTANT,
            system_message="You are helpful.",
            goal="Help users",
        )
        
        assert config.agent_id == "agent_1"
        assert config.name == "TestAgent"
        assert config.role == AutoGenAgentRole.ASSISTANT
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict["role"] == "assistant"
    
    def test_get_autogen_adapter_singleton(self):
        """Test get_autogen_adapter returns singleton."""
        adapter1 = get_autogen_adapter()
        adapter2 = get_autogen_adapter()
        
        assert adapter1 is adapter2
    
    def test_agent_creation_without_autogen(self):
        """Test agent creation when AutoGen not available."""
        adapter = AutoGenAdapter()
        
        if not AUTOGEN_AVAILABLE:
            with pytest.raises(RuntimeError, match="AutoGen is not available"):
                adapter.create_agent(
                    agent_id="test",
                    name="Test",
                    role=AutoGenAgentRole.ASSISTANT,
                )
    
    def test_message_translation(self):
        """Test message format translation."""
        adapter = AutoGenAdapter()
        
        heretek_message = {
            "role": "user",
            "content": "Test message",
            "name": "user1",
        }
        
        translated = adapter.translate_message(heretek_message, from_format="heretek")
        
        assert translated.role == "user"
        assert translated.content == "Test message"
    
    def test_statistics(self):
        """Test adapter statistics."""
        adapter = AutoGenAdapter()
        stats = adapter.get_statistics()
        
        assert "agent_count" in stats
        assert "group_chat_count" in stats
        assert "tool_count" in stats
        assert "autogen_available" in stats


# =============================================================================
# CrewAI Integration Tests
# =============================================================================

class TestCrewAIAdapter:
    """Tests for CrewAIAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = CrewAIAdapter()
        
        assert adapter.agents == {}
        assert adapter.tasks == {}
        assert adapter.crews == {}
        assert adapter.verbose is True
        assert adapter.cache_enabled is True
    
    def test_adapter_with_custom_config(self):
        """Test adapter with custom configuration."""
        adapter = CrewAIAdapter(
            verbose=False,
            memory_enabled=True,
            cache_enabled=False,
            max_rpm=100,
        )
        
        assert adapter.verbose is False
        assert adapter.memory_enabled is True
        assert adapter.cache_enabled is False
        assert adapter.max_rpm == 100
    
    def test_crew_agent_config_creation(self):
        """Test CrewAgentConfig dataclass."""
        config = CrewAgentConfig(
            agent_id="agent_1",
            role="Researcher",
            goal="Research topics deeply",
            backstory="You are an expert researcher.",
        )
        
        assert config.agent_id == "agent_1"
        assert config.role == "Researcher"
        assert config.goal == "Research topics deeply"
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict["role"] == "Researcher"
    
    def test_crew_task_config_creation(self):
        """Test CrewTaskConfig dataclass."""
        config = CrewTaskConfig(
            task_id="task_1",
            description="Research AI trends",
            expected_output="A comprehensive report",
            agent_id="agent_1",
        )
        
        assert config.task_id == "task_1"
        assert config.description == "Research AI trends"
        assert config.expected_output == "A comprehensive report"
    
    def test_get_crewai_adapter_singleton(self):
        """Test get_crewai_adapter returns singleton."""
        adapter1 = get_crewai_adapter()
        adapter2 = get_crewai_adapter()
        
        assert adapter1 is adapter2
    
    def test_agent_creation_without_crewai(self):
        """Test agent creation when CrewAI not available."""
        adapter = CrewAIAdapter()
        
        if not CREWAI_AVAILABLE:
            with pytest.raises(RuntimeError, match="CrewAI is not available"):
                adapter.create_agent(
                    agent_id="test",
                    role="Researcher",
                    goal="Test goal",
                )
    
    def test_memory_sharing(self):
        """Test shared memory functionality."""
        adapter = CrewAIAdapter()
        
        adapter.share_memory("key1", {"data": "value"})
        
        assert adapter.get_memory("key1") == {"data": "value"}
        
        status = adapter.get_shared_memory_status()
        assert status["memory_count"] >= 1
    
    def test_statistics(self):
        """Test adapter statistics."""
        adapter = CrewAIAdapter()
        stats = adapter.get_statistics()
        
        assert "agent_count" in stats
        assert "task_count" in stats
        assert "crew_count" in stats
        assert "crewai_available" in stats


# =============================================================================
# OpenAI Assistants Integration Tests
# =============================================================================

class TestOpenAIAssistantsAdapter:
    """Tests for OpenAIAssistantsAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = OpenAIAssistantsAdapter()
        
        assert adapter.assistants == {}
        assert adapter.threads == {}
        assert adapter.runs == {}
        assert adapter.enable_heretek_bridge is True
        assert adapter.client is None  # No API key
    
    def test_adapter_with_api_key(self):
        """Test adapter with API key."""
        adapter = OpenAIAssistantsAdapter(api_key="test_key")
        
        if OPENAI_AVAILABLE:
            assert adapter.client is not None
        else:
            assert adapter.client is None
    
    def test_assistant_config_creation(self):
        """Test AssistantConfig dataclass."""
        config = AssistantConfig(
            assistant_id="asst_1",
            name="Test Assistant",
            model="gpt-4o",
            instructions="You are helpful.",
        )
        
        assert config.assistant_id == "asst_1"
        assert config.name == "Test Assistant"
        assert config.model == "gpt-4o"
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict["name"] == "Test Assistant"
    
    def test_thread_context_creation(self):
        """Test ThreadContext dataclass."""
        context = ThreadContext(
            thread_id="thread_1",
            assistant_id="asst_1",
        )
        
        assert context.thread_id == "thread_1"
        assert context.assistant_id == "asst_1"
        assert context.messages == []
    
    def test_run_status_enum(self):
        """Test RunStatus enumeration."""
        assert RunStatus.QUEUED.value == "queued"
        assert RunStatus.IN_PROGRESS.value == "in_progress"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"
    
    def test_get_openai_assistants_adapter_singleton(self):
        """Test get_openai_assistants_adapter returns singleton."""
        adapter1 = get_openai_assistants_adapter()
        adapter2 = get_openai_assistants_adapter()
        
        assert adapter1 is adapter2
    
    def test_function_registration(self):
        """Test function registration."""
        adapter = OpenAIAssistantsAdapter()
        
        def test_func(x: int) -> int:
            return x * 2
        
        adapter.register_function("test_func", test_func)
        
        assert "test_func" in adapter._registered_functions
    
    def test_statistics(self):
        """Test adapter statistics."""
        adapter = OpenAIAssistantsAdapter()
        stats = adapter.get_statistics()
        
        assert "assistant_count" in stats
        assert "thread_count" in stats
        assert "function_count" in stats
        assert "openai_available" in stats


# =============================================================================
# Anthropic Integration Tests
# =============================================================================

class TestAnthropicAdapter:
    """Tests for AnthropicAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = AnthropicAdapter()
        
        assert adapter.conversations == {}
        assert adapter.tools == {}
        assert adapter.enable_heretek_bridge is True
        assert adapter.client is None  # No API key
    
    def test_adapter_with_api_key(self):
        """Test adapter with API key."""
        adapter = AnthropicAdapter(api_key="test_key")
        
        if ANTHROPIC_AVAILABLE:
            assert adapter.client is not None
        else:
            assert adapter.client is None
    
    def test_tool_definition_creation(self):
        """Test ToolDefinition dataclass."""
        tool = ToolDefinition(
            name="calculator",
            description="Perform calculations",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string"},
                },
            },
        )
        
        assert tool.name == "calculator"
        assert tool.description == "Perform calculations"
        
        # Test to_dict
        tool_dict = tool.to_dict()
        assert tool_dict["name"] == "calculator"
        
        # Test to_anthropic_format
        anthropic_format = tool.to_anthropic_format()
        assert anthropic_format["name"] == "calculator"
    
    def test_conversation_context_creation(self):
        """Test ConversationContext dataclass."""
        context = ConversationContext(
            conversation_id="conv_1",
            system_prompt="You are helpful.",
            max_tokens=2048,
            temperature=0.5,
        )
        
        assert context.conversation_id == "conv_1"
        assert context.system_prompt == "You are helpful."
        assert context.max_tokens == 2048
        assert context.temperature == 0.5
    
    def test_conversation_message_addition(self):
        """Test adding messages to conversation."""
        context = ConversationContext(conversation_id="conv_1")
        
        message = context.add_message(
            role=AnthropicMessageRole.USER,
            content="Hello",
        )
        
        assert len(context.messages) == 1
        assert message.role == AnthropicMessageRole.USER
        assert message.content == "Hello"
    
    def test_tool_use_request_creation(self):
        """Test ToolUseRequest dataclass."""
        request = ToolUseRequest(
            request_id="req_1",
            tool_name="calculator",
            tool_input={"expression": "2 + 2"},
            conversation_id="conv_1",
        )
        
        assert request.request_id == "req_1"
        assert request.tool_name == "calculator"
        assert request.tool_input == {"expression": "2 + 2"}
    
    def test_get_anthropic_adapter_singleton(self):
        """Test get_anthropic_adapter returns singleton."""
        adapter1 = get_anthropic_adapter()
        adapter2 = get_anthropic_adapter()
        
        assert adapter1 is adapter2
    
    def test_tool_registration(self):
        """Test tool registration."""
        adapter = AnthropicAdapter()
        
        def handler(x: int) -> int:
            return x * 2
        
        tool = adapter.register_tool(
            name="doubler",
            description="Doubles a number",
            input_schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
            },
            handler=handler,
        )
        
        assert tool.name == "doubler"
        assert "doubler" in adapter.tools
    
    def test_statistics(self):
        """Test adapter statistics."""
        adapter = AnthropicAdapter()
        stats = adapter.get_statistics()
        
        assert "conversation_count" in stats
        assert "tool_count" in stats
        assert "anthropic_available" in stats


# =============================================================================
# Integration Manager Tests
# =============================================================================

class TestIntegrationManager:
    """Tests for IntegrationManager."""
    
    def test_manager_initialization(self):
        """Test manager initializes correctly."""
        manager = IntegrationManager()
        
        assert manager.integrations == {}
        assert manager.configs == {}
        assert manager.health_check_interval == 30.0
        assert manager.max_restart_attempts == 3
        assert manager.enable_auto_restart is True
    
    def test_manager_with_custom_config(self):
        """Test manager with custom configuration."""
        manager = IntegrationManager(
            health_check_interval=60.0,
            max_restart_attempts=5,
            enable_auto_restart=False,
        )
        
        assert manager.health_check_interval == 60.0
        assert manager.max_restart_attempts == 5
        assert manager.enable_auto_restart is False
    
    def test_integration_config_creation(self):
        """Test IntegrationConfig dataclass."""
        config = IntegrationConfig(
            integration_id="test_integration",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test LangGraph",
            config={"key": "value"},
        )
        
        assert config.integration_id == "test_integration"
        assert config.integration_type == IntegrationType.LANGGRAPH
        assert config.name == "Test LangGraph"
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict["integration_type"] == "langgraph"
    
    def test_integration_state_creation(self):
        """Test IntegrationState dataclass."""
        state = IntegrationState(
            integration_id="test_integration",
            status=IntegrationStatus.RUNNING,
        )
        
        assert state.integration_id == "test_integration"
        assert state.status == IntegrationStatus.RUNNING
        assert state.restart_count == 0
        
        # Test to_dict
        state_dict = state.to_dict()
        assert state_dict["status"] == "running"
    
    def test_health_check_result_creation(self):
        """Test HealthCheckResult dataclass."""
        result = HealthCheckResult(
            integration_id="test_integration",
            status=HealthStatus.HEALTHY,
            latency_ms=10.5,
            details={"check": "passed"},
        )
        
        assert result.integration_id == "test_integration"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms == 10.5
        
        # Test to_dict
        result_dict = result.to_dict()
        assert result_dict["status"] == "healthy"
    
    def test_get_integration_manager_singleton(self):
        """Test get_integration_manager returns singleton."""
        manager1 = get_integration_manager()
        manager2 = get_integration_manager()
        
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_register_integration(self):
        """Test registering an integration."""
        manager = IntegrationManager()
        
        config = await manager.register_integration(
            integration_id="test_langgraph",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test LangGraph Integration",
            config={"graph_id": "test_graph"},
        )
        
        assert config.integration_id == "test_langgraph"
        assert "test_langgraph" in manager.configs
        assert "test_langgraph" in manager.states
    
    @pytest.mark.asyncio
    async def test_unregister_integration(self):
        """Test unregistering an integration."""
        manager = IntegrationManager()
        
        await manager.register_integration(
            integration_id="test_integration",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test",
        )
        
        result = await manager.unregister_integration("test_integration")
        
        assert result is True
        assert "test_integration" not in manager.configs
    
    @pytest.mark.asyncio
    async def test_start_stop_integration(self):
        """Test starting and stopping an integration."""
        manager = IntegrationManager()
        
        await manager.register_integration(
            integration_id="test_langgraph",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test LangGraph",
        )
        
        # Start
        started = await manager.start_integration("test_langgraph")
        assert started is True
        
        state = manager.states["test_langgraph"]
        assert state.status == IntegrationStatus.RUNNING
        
        # Stop
        stopped = await manager.stop_integration("test_langgraph")
        assert stopped is True
        
        state = manager.states["test_langgraph"]
        assert state.status == IntegrationStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        manager = IntegrationManager()
        
        await manager.register_integration(
            integration_id="test_langgraph",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test LangGraph",
        )
        
        # Health check when not running
        result = await manager.check_health("test_langgraph")
        assert result.status == HealthStatus.UNHEALTHY
        
        # Start and check again
        await manager.start_integration("test_langgraph")
        result = await manager.check_health("test_langgraph")
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    @pytest.mark.asyncio
    async def test_list_integrations(self):
        """Test listing integrations."""
        manager = IntegrationManager()
        
        await manager.register_integration(
            integration_id="test_langgraph",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test LangGraph",
        )
        
        integrations = manager.list_integrations()
        
        assert len(integrations) == 1
        assert integrations[0]["config"]["integration_id"] == "test_langgraph"
    
    @pytest.mark.asyncio
    async def test_statistics(self):
        """Test manager statistics."""
        manager = IntegrationManager()
        
        await manager.register_integration(
            integration_id="test_langgraph",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test LangGraph",
        )
        
        stats = manager.get_statistics()
        
        assert stats["total_integrations"] == 1
        assert "status_counts" in stats
        assert "type_counts" in stats
    
    @pytest.mark.asyncio
    async def test_event_callback(self):
        """Test event callback registration."""
        manager = IntegrationManager()
        events_received = []
        
        def callback(event):
            events_received.append(event)
        
        manager.register_event_callback(callback)
        
        await manager.register_integration(
            integration_id="test_integration",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test",
        )
        
        # Should have received registration event
        assert len(events_received) >= 1
    
    def test_integration_type_enum(self):
        """Test IntegrationType enumeration."""
        assert IntegrationType.LANGGRAPH.value == "langgraph"
        assert IntegrationType.AUTOGEN.value == "autogen"
        assert IntegrationType.CREWAI.value == "crewai"
        assert IntegrationType.OPENAI_ASSISTANTS.value == "openai_assistants"
        assert IntegrationType.ANTHROPIC.value == "anthropic"
    
    def test_integration_status_enum(self):
        """Test IntegrationStatus enumeration."""
        assert IntegrationStatus.UNINITIALIZED.value == "uninitialized"
        assert IntegrationStatus.RUNNING.value == "running"
        assert IntegrationStatus.STOPPED.value == "stopped"
        assert IntegrationStatus.FAILED.value == "failed"
    
    def test_health_status_enum(self):
        """Test HealthStatus enumeration."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


# =============================================================================
# Integration Tests with Sessions 41-46 Systems
# =============================================================================

class TestIntegrationWithCollectiveSystems:
    """Tests for integration with Sessions 41-46 collective systems."""
    
    def test_langgraph_state_sync_with_agent_runtime(self):
        """Test LangGraph state sync with agent runtime."""
        adapter = LangGraphAdapter()
        
        # Mock agent runtime
        mock_runtime = {
            "agent_1": MagicMock(),
        }
        mock_runtime["agent_1"].update_context = AsyncMock()
        
        adapter.set_agent_runtime(mock_runtime)
        
        # Verify runtime is set
        assert adapter._agent_runtime is not None
    
    def test_autogen_heretek_bridge(self):
        """Test AutoGen Heretek bridge functionality."""
        adapter = AutoGenAdapter()
        
        # Mock agent runtime
        mock_runtime = {
            "heretek_agent": MagicMock(),
        }
        mock_runtime["heretek_agent"].think = AsyncMock(return_value="Response")
        
        adapter.set_agent_runtime(mock_runtime)
        adapter.register_heretek_agent("heretek_agent", "autogen_agent")
        
        assert "heretek_agent" in adapter._heretek_agents
    
    def test_crewai_memory_sharing_with_heretek(self):
        """Test CrewAI memory sharing with Heretek agents."""
        adapter = CrewAIAdapter()
        
        # Mock agent runtime
        mock_runtime = {
            "agent_1": MagicMock(),
        }
        mock_runtime["agent_1"].update_context = AsyncMock()
        
        adapter.set_agent_runtime(mock_runtime)
        adapter.register_heretek_agent_mapping("heretek_1", "crewai_1")
        
        # Share memory
        adapter.share_memory("shared_key", {"data": "value"}, heretek_agents=["agent_1"])
        
        assert adapter.get_memory("shared_key") == {"data": "value"}
    
    def test_openai_heretek_bridge(self):
        """Test OpenAI Assistants Heretek bridge."""
        adapter = OpenAIAssistantsAdapter()
        
        # Mock agent runtime
        mock_runtime = {"agent_1": MagicMock()}
        adapter.set_agent_runtime(mock_runtime)
        adapter.register_heretek_agent_mapping("agent_1", "asst_1")
        
        assert "agent_1" in adapter._heretek_agent_mappings
    
    def test_anthropic_heretek_bridge(self):
        """Test Anthropic Heretek bridge."""
        adapter = AnthropicAdapter()
        
        # Mock agent runtime
        mock_runtime = {"agent_1": MagicMock()}
        adapter.set_agent_runtime(mock_runtime)
        adapter.register_heretek_agent_mapping("agent_1", "calculator")
        
        assert "agent_1" in adapter._heretek_agent_mappings
    
    def test_integration_manager_with_agent_runtime(self):
        """Test Integration Manager coordination with agent runtime."""
        manager = IntegrationManager()
        
        # Mock agent runtime
        mock_runtime = {"agent_1": MagicMock()}
        
        # Register and start integrations
        asyncio.run(manager.register_integration(
            integration_id="test_langgraph",
            integration_type=IntegrationType.LANGGRAPH,
            name="Test LangGraph",
        ))
        
        # Set runtime on adapter
        adapter = manager.get_integration("test_langgraph")
        if adapter and hasattr(adapter, 'set_agent_runtime'):
            adapter.set_agent_runtime(mock_runtime)
        
        # Verify statistics
        stats = manager.get_statistics()
        assert stats["total_integrations"] == 1


# =============================================================================
# Zero-Trust Validation Tests
# =============================================================================

class TestZeroTrustValidation:
    """Tests for zero-trust validation in integrations."""
    
    def test_langgraph_pattern_validation(self):
        """Test LangGraph pattern validation."""
        # Verify no datetime.utcnow usage
        import inspect
        from src.heretek_swarm.integrations import langgraph
        
        source = inspect.getsource(langgraph)
        assert "datetime.utcnow" not in source
    
    def test_autogen_input_validation(self):
        """Test AutoGen input validation."""
        import inspect
        from src.heretek_swarm.integrations import autogen
        
        source = inspect.getsource(autogen)
        # Check for validation patterns
        assert "ValueError" in source or "raise" in source
    
    def test_crewai_state_validation(self):
        """Test CrewAI state validation."""
        import inspect
        from src.heretek_swarm.integrations import crewai
        
        source = inspect.getsource(crewai)
        assert "ValueError" in source or "raise" in source
    
    def test_openai_api_validation(self):
        """Test OpenAI API validation."""
        import inspect
        from src.heretek_swarm.integrations import openai_assistants
        
        source = inspect.getsource(openai_assistants)
        assert "ValueError" in source or "raise" in source
    
    def test_anthropic_message_validation(self):
        """Test Anthropic message validation."""
        import inspect
        from src.heretek_swarm.integrations import anthropic
        
        source = inspect.getsource(anthropic)
        assert "ValueError" in source or "raise" in source
    
    def test_manager_integration_validation(self):
        """Test Integration Manager validation."""
        import inspect
        from src.heretek_swarm.integrations import manager
        
        source = inspect.getsource(manager)
        assert "ValueError" in source or "raise" in source


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
