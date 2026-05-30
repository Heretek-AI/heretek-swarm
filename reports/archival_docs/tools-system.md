# Tools System Documentation

## Overview

The Tools System provides a flexible, type-safe architecture for creating and managing Python-native tools within the Heretek Swarm framework. It supports automatic validation, structured error handling, performance monitoring, and dynamic tool registration with hot reloading.

## Core Architecture

### Tool Base Classes

**Location**: [`src/tools/base.py`](../src/tools/base.py)

The tools system is built on three main components:

1. **BaseTool**: Abstract base for all tools with full lifecycle management
2. **SimpleTool**: Simplified interface for quick tool creation
3. **ToolRegistry**: Dynamic tool discovery and management

```
┌─────────────────────────────────────────────────┐
│              Tool Registry                    │
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │  BaseTool    │  │ SimpleTool   │        │
│  │              │  │              │        │
│  │ - validate   │  │ - execute    │        │
│  │ - execute    │  │              │        │
│  │ - monitor    │  │              │        │
│  └──────────────┘  └──────────────┘        │
│                                             │
│  ┌──────────────────────────────────────────┐   │
│  │        Tool Discovery                 │   │
│  │  - Auto-discover                    │   │
│  │  - Lazy loading                    │   │
│  │  - Hot reload                      │   │
│  └──────────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────────┐   │
│  │        Tool Management               │   │
│  │  - Health monitoring               │   │
│  │  - Performance tracking            │   │
│  │  - Category filtering              │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Data Structures

### ToolStatus

```python
class ToolStatus(str, Enum):
    """Tool execution status"""
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
```

### ToolMetadata

```python
class ToolMetadata(BaseModel):
    """Metadata for tool registration and discovery"""
    
    # Identity
    tool_id: UUID              # Unique tool identifier
    name: str                 # Unique tool name
    version: str              # Tool version (default: "1.0.0")
    
    # Description
    description: str           # Tool description
    category: str            # Tool category (default: "general")
    tags: List[str]          # Search tags
    
    # Authorship
    author: Optional[str]     # Tool author
    source: Optional[str]     # Source repository
    
    # Capabilities
    input_schema: Optional[Dict[str, Any]]   # JSON schema for inputs
    output_schema: Optional[Dict[str, Any]]  # JSON schema for outputs
    
    # Requirements
    requires_memory: bool      # Requires memory access
    requires_state: bool      # Requires state management
    external_dependencies: List[str]  # External dependencies
    
    # Performance
    timeout_seconds: float     # Timeout (default: 30.0)
    max_concurrent: int       # Max concurrent executions (default: 10)
    
    # Status
    status: ToolStatus        # Current status
    enabled: bool            # Whether tool is enabled
    
    # Timestamps
    created_at: datetime      # Creation timestamp
    updated_at: datetime      # Last update timestamp
    last_used_at: Optional[datetime]  # Last usage timestamp
    
    # Metrics
    total_executions: int    # Total executions
    successful_executions: int  # Successful executions
    failed_executions: int    # Failed executions
    avg_execution_time_ms: float  # Average execution time
```

### ToolExecutionResult

```python
class ToolExecutionResult(BaseModel, Generic[TOutput]):
    """Result from tool execution"""
    
    # Execution info
    execution_id: UUID        # Unique execution ID
    tool_id: UUID           # Tool identifier
    tool_name: str          # Tool name
    
    # Status
    status: ToolStatus       # Execution status
    error: Optional[str]    # Error message if failed
    error_details: Optional[Dict[str, Any]]  # Detailed error info
    
    # Output
    output: Optional[TOutput]  # Typed output
    raw_output: Optional[Any]   # Raw output
    
    # Performance
    started_at: datetime     # Start timestamp
    completed_at: datetime  # Completion timestamp
    duration_ms: float     # Duration in milliseconds
    
    # Metadata
    metadata: Dict[str, Any]  # Additional metadata
```

### ToolContext

```python
class ToolContext(BaseModel):
    """Context provided to tools during execution"""
    
    # Agent info
    agent_id: str           # Agent executing the tool
    agent_name: str         # Agent name
    
    # Execution info
    execution_id: UUID      # Execution identifier
    request_id: Optional[UUID]  # Request identifier
    
    # Resources
    memory: Optional[Any]    # Memory system access
    state: Optional[Any]     # State system access
    
    # Configuration
    config: Dict[str, Any]  # Tool configuration
    
    # Metadata
    metadata: Dict[str, Any]  # Additional metadata
```

## Core Components

### BaseTool

**Location**: [`src/tools/base.py`](../src/tools/base.py)

Abstract base class for all tools with full lifecycle management.

**Features**:
- Type-safe input/output validation via Pydantic
- Automatic validation and error handling
- Performance monitoring
- Observability hooks
- Resource access (memory, state)

**Key Methods**:

#### Definition

```python
from typing import TypeVar, Generic
from pydantic import BaseModel
from src.tools.base import BaseTool, ToolContext, ToolExecutionResult

# Define input/output types
TInput = TypeVar('TInput', bound=BaseModel)
TOutput = TypeVar('TOutput', bound=BaseModel)

# Define input schema
class MyToolInput(BaseModel):
    """Input for MyTool"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100)

# Define output schema
class MyToolOutput(BaseModel):
    """Output from MyTool"""
    results: List[str]
    count: int

# Define the tool
class MyTool(BaseTool[TInput, TOutput]):
    """Example tool implementation"""
    
    async def validate_input(self, input_data: TInput) -> None:
        """Validate input before execution"""
        # Custom validation logic
        if len(input_data.query) < 3:
            raise ValueError("Query too short")
    
    async def execute(
        self,
        input_data: TInput,
        context: ToolContext
    ) -> TOutput:
        """Execute the tool"""
        # Tool logic here
        results = await self.search(input_data.query, input_data.limit)
        return MyToolOutput(results=results, count=len(results))
    
    async def search(self, query: str, limit: int) -> List[str]:
        """Internal search method"""
        # Implementation
        return ["result1", "result2"]
```

#### Usage

```python
# Create tool instance
tool = MyTool()

# Get metadata
metadata = await tool.get_metadata()
print(f"Tool: {metadata.name}")
print(f"Description: {metadata.description}")

# Execute tool
context = ToolContext(
    agent_id="alpha",
    agent_name="Alpha Agent",
    execution_id=uuid4()
)

input_data = MyToolInput(query="search term", limit=5)
result = await tool.execute(input_data, context)

# Check result
if result.status == ToolStatus.COMPLETED:
    print(f"Results: {result.output.results}")
else:
    print(f"Error: {result.error}")
```

### SimpleTool

**Location**: [`src/tools/base.py`](../src/tools/base.py)

Simplified interface for quick tool creation without full lifecycle management.

**Features**:
- Simple execute-only interface
- Automatic validation
- Minimal boilerplate
- Perfect for simple tools

**Example**:

```python
from src.tools.base import SimpleTool, ToolContext

class SimpleCalculator(SimpleTool):
    """Simple calculator tool"""
    
    async def execute(
        self,
        a: int,
        b: int,
        operation: str = "add",
        context: ToolContext = None
    ) -> int:
        """Execute calculation"""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            raise ValueError(f"Unknown operation: {operation}")

# Usage
tool = SimpleCalculator()
result = await tool.execute(5, 3, operation="multiply")
print(f"Result: {result}")  # Output: 15
```

### ToolRegistry

**Location**: [`src/tools/registry.py`](../src/tools/registry.py)

Dynamic tool registry with runtime discovery and management.

**Features**:
- Automatic tool discovery from modules
- Lazy loading for performance
- Category-based filtering
- Health monitoring
- Hot reloading
- Performance tracking

**Configuration**:

```python
from src.tools.registry import ToolRegistry, ToolRegistryConfig

# Create registry
config = ToolRegistryConfig(
    auto_discover=True,
    discovery_paths=["heretek_swarm.tools"],
    lazy_loading=True,
    max_tools=1000,
    cache_enabled=True,
    health_check_interval_seconds=300,
    auto_disable_failures=10
)

registry = ToolRegistry(config)
await registry.initialize()
```

**Key Methods**:

#### Tool Registration

```python
# Register a tool
await registry.register_tool(MyTool)

# Register multiple tools
await registry.register_tools([Tool1, Tool2, Tool3])

# Get tool
tool = registry.get_tool("my_tool")

# Check if tool exists
exists = registry.has_tool("my_tool")
```

#### Tool Discovery

```python
# Discover tools from module
await registry.discover_tools("my_module.tools")

# Auto-discover from configured paths
await registry.auto_discover()

# List all tools
tools = registry.list_tools()

# List tools by category
analysis_tools = registry.list_tools(category="analysis")
```

#### Tool Execution

```python
# Execute tool by name
result = await registry.execute_tool(
    tool_name="my_tool",
    input_data={"query": "search", "limit": 10},
    context=context
)

# Execute with typed input
input_data = MyToolInput(query="search", limit=10)
result = await registry.execute_tool("my_tool", input_data, context)

# Check result
if result.status == ToolStatus.COMPLETED:
    print(f"Output: {result.output}")
```

#### Tool Management

```python
# Enable/disable tool
await registry.enable_tool("my_tool")
await registry.disable_tool("my_tool")

# Reload tool
await registry.reload_tool("my_tool")

# Remove tool
await registry.unregister_tool("my_tool")

# Get tool health
health = await registry.check_tool_health("my_tool")
print(f"Health: {health.status}")
```

#### Performance Monitoring

```python
# Get tool metrics
metrics = registry.get_tool_metrics("my_tool")
print(f"Executions: {metrics.total_executions}")
print(f"Success rate: {metrics.success_rate:.2%}")
print(f"Avg time: {metrics.avg_execution_time_ms:.2f}ms")

# Get registry statistics
stats = registry.get_statistics()
print(f"Total tools: {stats.total_tools}")
print(f"Active tools: {stats.active_tools}")
print(f"Total executions: {stats.total_executions}")
```

## Tool Examples

### Example 1: Data Analysis Tool

```python
from typing import List
from pydantic import BaseModel, Field
from src.tools.base import BaseTool, ToolContext, ToolExecutionResult

class AnalysisInput(BaseModel):
    """Input for data analysis"""
    data: List[float] = Field(..., description="Data to analyze")
    operation: str = Field(default="mean", description="Operation to perform")

class AnalysisOutput(BaseModel):
    """Output from data analysis"""
    result: float
    operation: str
    count: int

class DataAnalysisTool(BaseTool[AnalysisInput, AnalysisOutput]):
    """Data analysis tool"""
    
    name = "data_analysis"
    description = "Perform statistical analysis on data"
    category = "analysis"
    
    async def execute(
        self,
        input_data: AnalysisInput,
        context: ToolContext
    ) -> AnalysisOutput:
        """Execute analysis"""
        data = input_data.data
        operation = input_data.operation
        
        if operation == "mean":
            result = sum(data) / len(data)
        elif operation == "sum":
            result = sum(data)
        elif operation == "max":
            result = max(data)
        elif operation == "min":
            result = min(data)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return AnalysisOutput(
            result=result,
            operation=operation,
            count=len(data)
        )
```

### Example 2: API Client Tool

```python
import httpx
from pydantic import BaseModel, Field
from src.tools.base import BaseTool, ToolContext

class APIRequestInput(BaseModel):
    """Input for API request"""
    url: str = Field(..., description="API endpoint URL")
    method: str = Field(default="GET", description="HTTP method")
    headers: dict = Field(default_factory=dict, description="Request headers")

class APIRequestOutput(BaseModel):
    """Output from API request"""
    status_code: int
    data: dict
    headers: dict

class APIClientTool(BaseTool[APIRequestInput, APIRequestOutput]):
    """API client tool"""
    
    name = "api_client"
    description = "Make HTTP requests to APIs"
    category = "network"
    
    async def execute(
        self,
        input_data: APIRequestInput,
        context: ToolContext
    ) -> APIRequestOutput:
        """Execute API request"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=input_data.method,
                url=input_data.url,
                headers=input_data.headers
            )
            
            return APIRequestOutput(
                status_code=response.status_code,
                data=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                headers=dict(response.headers)
            )
```

### Example 3: Memory Access Tool

```python
from pydantic import BaseModel, Field
from src.tools.base import BaseTool, ToolContext

class MemoryQueryInput(BaseModel):
    """Input for memory query"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100)

class MemoryQueryOutput(BaseModel):
    """Output from memory query"""
    results: list
    count: int

class MemoryQueryTool(BaseTool[MemoryQueryInput, MemoryQueryOutput]):
    """Memory query tool"""
    
    name = "memory_query"
    description = "Query the memory system"
    category = "memory"
    requires_memory = True
    
    async def execute(
        self,
        input_data: MemoryQueryInput,
        context: ToolContext
    ) -> MemoryQueryOutput:
        """Execute memory query"""
        if not context.memory:
            raise RuntimeError("Memory system not available")
        
        results = await context.memory.query(
            query_text=input_data.query,
            limit=input_data.limit
        )
        
        return MemoryQueryOutput(
            results=results,
            count=len(results)
        )
```

## Best Practices

### 1. Tool Design

- Keep tools focused on single responsibility
- Use descriptive names and descriptions
- Define clear input/output schemas
- Include comprehensive documentation

### 2. Input Validation

- Use Pydantic for type safety
- Add custom validation in [`validate_input()`](../src/tools/base.py)
- Provide helpful error messages
- Validate all required fields

### 3. Error Handling

- Catch and handle expected errors
- Provide meaningful error messages
- Use appropriate error types
- Log errors with context

### 4. Performance

- Optimize critical paths
- Use async/await properly
- Avoid blocking operations
- Monitor execution time

### 5. Resource Management

- Clean up resources properly
- Use context managers
- Respect timeout limits
- Handle resource exhaustion

### 6. Testing

- Write comprehensive tests
- Test edge cases
- Mock external dependencies
- Verify error handling

## Performance Considerations

### Tool Execution

- Average execution time: 10-100ms
- Timeout default: 30 seconds
- Max concurrent: 10 executions
- Cache TTL: 1 hour

### Registry Operations

- Tool discovery: 100-500ms
- Tool lookup: <1ms
- Tool execution: 10-100ms
- Health check: 50-200ms

### Memory Usage

- Tool instance: ~1KB
- Registry entry: ~5KB
- Execution result: ~1-10KB
- Total overhead: ~10-100KB per tool

## Troubleshooting

### Common Issues

1. **Tool Not Found**
   - Check if tool is registered
   - Verify tool name
   - Ensure discovery paths are correct
   - Check if tool is enabled

2. **Validation Errors**
   - Review input schema
   - Check field types
   - Verify required fields
   - Add custom validation

3. **Execution Timeout**
   - Increase timeout
   - Optimize tool logic
   - Check external dependencies
   - Review performance metrics

4. **Tool Disabled**
   - Check health status
   - Review failure count
   - Check error logs
   - Re-enable if needed

## API Reference

### BaseTool

See [`src/tools/base.py`](../src/tools/base.py) for complete API documentation.

### SimpleTool

See [`src/tools/base.py`](../src/tools/base.py) for complete API documentation.

### ToolRegistry

See [`src/tools/registry.py`](../src/tools/registry.py) for complete API documentation.

## See Also

- [Actors System](./actors-system.md)
- [Memory System](./memory-system.md)
- [State Management](./state-management.md)
- [Observability](./observability.md)
