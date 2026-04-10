"""
Dynamic Tool Registry for Heretek Swarm

Provides runtime tool discovery, registration, and management with:
- Dynamic tool loading from modules
- Category-based filtering
- Performance-based ranking
- Health monitoring
- Hot reloading support
"""

import importlib
import inspect
import pkgutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Type
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

from .base import BaseTool, ToolContext, ToolExecutionResult, ToolMetadata, ToolStatus

_logger = structlog.get_logger()


class ToolRegistryConfig(BaseModel):
    """Configuration for tool registry"""
    
    # Discovery
    auto_discover: bool = Field(default=True, description="Auto-discover tools on startup")
    discovery_paths: List[str] = Field(
        default_factory = lambda: ["src.tools", "heretek_swarm.tools", "heretek_swarm.tools.examples"],
        description="Python paths to search for tools"
    )
    
    # Loading
    lazy_loading: bool = Field(default=True, description="Load tools on-demand")
    preload_tools: List[str] = Field(default_factory=list, description="Tools to preload")
    
    # Performance
    max_tools: int = Field(default=1000, ge=1, description="Maximum registered tools")
    cache_enabled: bool = Field(default=True, description="Cache tool instances")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL")
    
    # Health
    health_check_interval_seconds: int = Field(default=300, description="Health check interval")
    auto_disable_failures: int = Field(default=10, description="Auto-disable after N failures")
    
    # Security
    allow_external_tools: bool = Field(default=False, description="Allow external tool loading")
    allowed_modules: Set[str] = Field(default_factory=set, description="Allowed module patterns")


class ToolRegistryEntry(BaseModel):
    """Registry entry for a tool"""
    
    # Tool reference
    tool_id: UUID = Field(...)
    name: str = Field(...)
    metadata: ToolMetadata = Field(...)
    
    # Class info
    module_path: Optional[str] = Field(None, description="Module where tool is defined")
    class_name: Optional[str] = Field(None, description="Class name")
    
    # Instance - use Any to avoid pydantic schema issues with BaseTool
    instance: Optional[Any] = Field(None, description="Cached tool instance")
    
    # Loading
    loaded: bool = Field(default=False, description="Whether tool is loaded")
    load_time: Optional[datetime] = Field(None)
    
    # Health
    health_status: str = Field(default="healthy")
    last_health_check: Optional[datetime] = Field(None)
    consecutive_failures: int = Field(default=0, ge=0)
    
    # Usage
    usage_count: int = Field(default=0, ge=0)
    last_used_at: Optional[datetime] = Field(None)
    
    class Config:
        arbitrary_types_allowed = True


class ToolRegistry:
    """
    Dynamic tool registry with runtime discovery and management.
    
    Features:
    - Automatic tool discovery from modules
    - Lazy loading for performance
    - Category-based filtering
    - Health monitoring
    - Hot reloading
    - Performance tracking
    
    Usage:
        _registry = ToolRegistry()
        await registry.initialize()
        
        # Get tool by name
        tool = await registry.get_tool("memory_search")
        
        # Execute tool
        _result = await registry.execute_tool(
            "memory_search",
            {"query": "find documents"},
            context
        )
        
        # List tools by category
        _tools = registry.list_tools(category="memory")
    """
    
    def __init__(self, _config: Optional[ToolRegistryConfig]):
        self.config = config or ToolRegistryConfig()
        
        # Tool storage
        self._tools: Dict[str, ToolRegistryEntry] = {}
        self._tools_by_category: Dict[str, Set[str]] = {}
        self._tools_by_tag: Dict[str, Set[str]] = {}
        
        # Cache
        self._cache: Dict[UUID, BaseTool] = {}
        self._cache_timestamps: Dict[UUID, datetime] = {}
        
        # Health monitoring
        self._health_check_task = None
        self._running = False
        
        # Metrics
        self._total_executions = 0
        self._cache_hits = 0
        self._cache_misses = 0
    
    async def initialize(self) -> None:
        """Initialize the tool registry"""
        logger.info("tool_registry_initializing")
        
        # Auto-discover tools
        if self.config.auto_discover:
            await self._discover_tools()
        
        # Preload specified tools
        for tool_name in self.config.preload_tools:
            try:
                await self._load_tool(tool_name)
            except Exception as e:
                logger.error(
                    "tool_preload_failed",
                    _tool_name = tool_name,
                    _error = str(e)
                )
        
        # Start health monitoring
        self._running = True
        # Note: Health check task would be started here in production
        
        logger.info(
            "tool_registry_initialized",
            _total_tools = len(self._tools)
        )
    
    async def shutdown(self) -> None:
        """Shutdown the registry"""
        self._running = False
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except Exception:
                pass
        
        # Clear cache
        self._cache.clear()
        self._cache_timestamps.clear()
        
        logger.info("tool_registry_shutdown")
    
    async def _discover_tools(self) -> None:
        """Discover tools from configured paths"""
        for path in self.config.discovery_paths:
            try:
                await self._discover_tools_in_path(path)
            except Exception as e:
                logger.error(
                    "tool_discovery_failed",
                    _path = path,
                    _error = str(e)
                )
    
    async def _discover_tools_in_path(self, _path: str) -> None:
        """Discover tools in a specific Python path"""
        try:
            module = importlib.import_module(path)
            
            # Iterate through submodules
            if hasattr(module, '__path__'):
                for _, name, is_pkg in pkgutil.iter_modules(module.__path__, path + '.'):
                    if is_pkg:
                        # Recursively discover in packages
                        await self._discover_tools_in_path(name)
                    else:
                        # Discover tools in module
                        await self._discover_tools_in_module(name)
        except Exception as e:
            logger.warning(
                "path_discovery_failed",
                _path = path,
                _error = str(e)
            )
    
    async def _discover_tools_in_module(self, _module_path: str) -> None:
        """Discover tools in a specific module"""
        try:
            module = importlib.import_module(module_path)
            
            # Find all tool classes
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    # Check if it's a tool class
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        await self._register_tool_class(obj, module_path)
        except Exception as e:
            logger.warning(
                "module_discovery_failed",
                module=module_path,
                _error = str(e)
            )
    
    async def _register_tool_class(self, _tool_class: Type[BaseTool], _module_path: str) -> None:
        """Register a tool class"""
        try:
            # Create instance to get metadata
            # Note: This assumes tool can be instantiated without args
            # In production, you'd need a more sophisticated approach
            instance = tool_class()
            metadata = instance.get_metadata()
            
            # Create registry entry
            _entry = ToolRegistryEntry(
                tool_id=metadata.tool_id,
                name=metadata.name,
                metadata=metadata,
                module_path=module_path,
                class_name=tool_class.__name__,
                instance=instance if not self.config.lazy_loading else None,
                loaded=not self.config.lazy_loading
            )
            
            # Register
            self._tools[metadata.name] = entry
            
            # Index by category
            if metadata.category not in self._tools_by_category:
                self._tools_by_category[metadata.category] = set()
            self._tools_by_category[metadata.category].add(metadata.name)
            
            # Index by tags
            for tag in metadata.tags:
                if tag not in self._tools_by_tag:
                    self._tools_by_tag[tag] = set()
                self._tools_by_tag[tag].add(metadata.name)
            
            logger.debug(
                "tool_registered",
                _tool_name = metadata.name,
                category=metadata.category
            )
        
        except Exception as e:
            logger.error(
                "tool_registration_failed",
                module=module_path,
                class_name=tool_class.__name__,
                _error = str(e)
            )
    
    def register_tool(self, _tool: BaseTool) -> None:
        """Manually register a tool instance"""
        metadata = tool.get_metadata()
        
        _entry = ToolRegistryEntry(
            tool_id=metadata.tool_id,
            name=metadata.name,
            metadata=metadata,
            instance=tool,
            loaded=True
        )
        
        self._tools[metadata.name] = entry
        
        # Index
        if metadata.category not in self._tools_by_category:
            self._tools_by_category[metadata.category] = set()
        self._tools_by_category[metadata.category].add(metadata.name)
        
        for tag in metadata.tags:
            if tag not in self._tools_by_tag:
                self._tools_by_tag[tag] = set()
            self._tools_by_tag[tag].add(metadata.name)
        
        logger.info(
            "tool_manually_registered",
            _tool_name = metadata.name
        )
    
    async def _load_tool(self, _tool_name: str) -> Optional[BaseTool]:
        """Load a tool instance"""
        _entry = self._tools.get(tool_name)
        
        if not entry:
            logger.warning("tool_not_found", tool_name=tool_name)
            return None
        
        if entry.loaded and entry.instance:
            return entry.instance
        
        try:
            # Import module
            if not entry.module_path or not entry.class_name:
                raise ValueError("Missing module or class info")
            
            module = importlib.import_module(entry.module_path)
            tool_class = getattr(module, entry.class_name)
            
            # Create instance
            instance = tool_class()
            
            # Update entry
            entry.instance = instance
            entry.loaded = True
            entry.load_time = datetime.now(timezone.utc)
            
            # Cache
            if self.config.cache_enabled:
                self._cache[entry.tool_id] = instance
                self._cache_timestamps[entry.tool_id] = datetime.now(timezone.utc)
            
            logger.info(
                "tool_loaded",
                _tool_name = tool_name,
                module=entry.module_path
            )
            
            return instance
        
        except Exception as e:
            logger.error(
                "tool_load_failed",
                _tool_name = tool_name,
                _error = str(e)
            )
            entry.consecutive_failures += 1
            
            # Auto-disable if too many failures
            if entry.consecutive_failures >= self.config.auto_disable_failures:
                entry.metadata.enabled = False
                entry.metadata.status = ToolStatus.DISABLED
                logger.warning(
                    "tool_auto_disabled",
                    _tool_name = tool_name,
                    _failures = entry.consecutive_failures
                )
            
            return None
    
    def _get_cached_tool(self, _tool_id: UUID) -> Optional[BaseTool]:
        """Get tool from cache"""
        if not self.config.cache_enabled:
            return None
        
        if tool_id not in self._cache:
            self._cache_misses += 1
            return None
        
        # Check TTL
        _timestamp = self._cache_timestamps.get(tool_id)
        if timestamp:
            _age = (datetime.now(timezone.utc) - timestamp).total_seconds()
            if age > self.config.cache_ttl_seconds:
                # Expired
                del self._cache[tool_id]
                del self._cache_timestamps[tool_id]
                self._cache_misses += 1
                return None
        
        self._cache_hits += 1
        return self._cache[tool_id]
    
    async def get_tool(self, _tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        _entry = self._tools.get(tool_name)
        
        if not entry:
            return None
        
        # Check cache first
        _cached = self._get_cached_tool(entry.tool_id)
        if cached:
            return cached
        
        # Load if needed
        if not entry.loaded:
            return await self._load_tool(tool_name)
        
        return entry.instance
    
    async def execute_tool(self, _tool_name: str, _input_data: Dict[str, _Any], _context: Optional[ToolContext]) -> ToolExecutionResult:
        """Execute a tool by name"""
        _start_time = datetime.now(timezone.utc)
        
        # Get tool
        tool = await self.get_tool(tool_name)
        
        if not tool:
            return ToolExecutionResult(
                _execution_id = uuid4(),
                tool_id=uuid4(),
                _tool_name = tool_name,
                status=ToolStatus.FAILED,
                error=f"Tool not found: {tool_name}",
                _execution_time_ms = 0,
                _started_at = start_time,
                _completed_at = datetime.now(timezone.utc)
            )
        
        # Execute
        _result = await tool.run(input_data, context)
        
        # Update metrics
        self._total_executions += 1
        
        # Update entry
        _entry = self._tools.get(tool_name)
        if entry:
            entry.usage_count += 1
            entry.last_used_at = datetime.now(timezone.utc)
            entry.consecutive_failures = 0 if result.status == ToolStatus.COMPLETED else entry.consecutive_failures + 1
        
        return result
    
    def list_tools(self, _category: Optional[str], _tags: Optional[List[str]], _enabled_only: bool) -> List[ToolMetadata]:
        """List tools with optional filtering"""
        _tools = []
        
        for name, entry in self._tools.items():
            # Filter by enabled
            if enabled_only and not entry.metadata.enabled:
                continue
            
            # Filter by category
            if category and entry.metadata.category != category:
                continue
            
            # Filter by tags
            if tags:
                if not all(tag in entry.metadata.tags for tag in tags):
                    continue
            
            tools.append(entry.metadata)
        
        return tools
    
    def get_categories(self) -> List[str]:
        """Get all tool categories"""
        return list(self._tools_by_category.keys())
    
    def get_tags(self) -> List[str]:
        """Get all tool tags"""
        return list(self._tools_by_tag.keys())
    
    def search_tools(self, _query: str, _limit: int) -> List[ToolMetadata]:
        """Search tools by name, description, or tags"""
        _query_lower = query.lower()
        _results = []
        
        for name, entry in self._tools.items():
            if not entry.metadata.enabled:
                continue
            
            # Search in name, description, tags
            _score = 0
            
            if query_lower in name.lower():
                score += 3
            if query_lower in entry.metadata.description.lower():
                score += 2
            if any(query_lower in tag.lower() for tag in entry.metadata.tags):
                score += 1
            
            if score > 0:
                results.append((score, entry.metadata))
        
        # Sort by score
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [metadata for _, metadata in results[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        _total_tools = len(self._tools)
        _loaded_tools = sum(1 for e in self._tools.values() if e.loaded)
        _enabled_tools = sum(1 for e in self._tools.values() if e.metadata.enabled)
        
        return {
            "total_tools": total_tools,
            "loaded_tools": loaded_tools,
            "enabled_tools": enabled_tools,
            "disabled_tools": total_tools - enabled_tools,
            "categories": len(self._tools_by_category),
            "tags": len(self._tools_by_tag),
            "cache_size": len(self._cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": (
                self._cache_hits / (self._cache_hits + self._cache_misses)
                if (self._cache_hits + self._cache_misses) > 0 else 0
            ),
            "total_executions": self._total_executions,
        }
    
    async def reload_tool(self, _tool_name: str) -> bool:
        """Reload a tool (hot reload)"""
        _entry = self._tools.get(tool_name)
        
        if not entry:
            return False
        
        try:
            # Remove from cache
            if entry.tool_id in self._cache:
                del self._cache[entry.tool_id]
            if entry.tool_id in self._cache_timestamps:
                del self._cache_timestamps[entry.tool_id]
            
            # Reload module
            if entry.module_path:
                _module = importlib.import_module(entry.module_path)
                importlib.reload(module)
            
            # Reload tool
            entry.loaded = False
            entry.instance = None
            
            await self._load_tool(tool_name)
            
            logger.info(
                "tool_reloaded",
                _tool_name = tool_name
            )
            
            return True
        
        except Exception as e:
            logger.error(
                "tool_reload_failed",
                _tool_name = tool_name,
                _error = str(e)
            )
            
            return False


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


async def initialize_registry(_config: Optional[ToolRegistryConfig]) -> ToolRegistry:
    """Initialize the global registry"""
    global _registry
    _registry = ToolRegistry(config)
    await _registry.initialize()
    return _registry
