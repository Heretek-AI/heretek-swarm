"""
Integration Manager Module for Heretek Swarm

This module provides unified integration management for the heretek-swarm collective.
It enables centralized registry, lifecycle management, health monitoring, and configuration
for all external AI platform integrations.

Features:
- Unified integration registry
- Lifecycle management (start/stop/restart)
- Health monitoring
- Configuration management
- Zero-trust validation of all integration operations

Reference: EXPANSION_ROADMAP.md Session 47 - Integration Ecosystem
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog

_logger = structlog.get_logger(__name__)


class IntegrationType(str, Enum):
    """Integration types."""
    LANGGRAPH = "langgraph"
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    OPENAI_ASSISTANTS = "openai_assistants"
    ANTHROPIC = "anthropic"
    DISCORD = "discord"
    SLACK = "slack"
    TELEGRAM = "telegram"
    PRAISON = "praison"
    CUSTOM = "custom"


class IntegrationStatus(str, Enum):
    """Integration status enumeration."""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class IntegrationConfig:
    """
    Configuration for an integration.
    
    Attributes:
        integration_id: Unique integration identifier
        integration_type: Type of integration
        name: Human-readable name
        enabled: Whether integration is enabled
        config: Integration-specific configuration
        metadata: Additional metadata
    """
    integration_id: str
    integration_type: IntegrationType
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "integration_id": self.integration_id,
            "integration_type": self.integration_type.value,
            "name": self.name,
            "enabled": self.enabled,
            "config": self.config,
            "metadata": self.metadata,
        }


@dataclass
class HealthCheckResult:
    """
    Result of a health check.
    
    Attributes:
        integration_id: Integration identifier
        status: Health status
        latency_ms: Health check latency
        details: Health check details
        timestamp: Check timestamp
    """
    integration_id: str
    status: HealthStatus
    latency_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "integration_id": self.integration_id,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class IntegrationState:
    """
    State tracking for an integration.
    
    Attributes:
        integration_id: Integration identifier
        status: Current status
        instance: Integration instance
        started_at: Start timestamp
        stopped_at: Stop timestamp
        last_health_check: Last health check result
        restart_count: Number of restarts
        error_count: Number of errors
        metadata: Additional state metadata
    """
    integration_id: str
    status: IntegrationStatus = IntegrationStatus.UNINITIALIZED
    instance: Optional[Any] = None
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    last_health_check: Optional[HealthCheckResult] = None
    restart_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "integration_id": self.integration_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "restart_count": self.restart_count,
            "error_count": self.error_count,
            "last_health_check": self.last_health_check.to_dict() if self.last_health_check else None,
            "metadata": self.metadata,
        }


@dataclass
class IntegrationEvent:
    """
    Event emitted by integration manager.
    
    Attributes:
        event_id: Unique event identifier
        event_type: Event type
        integration_id: Related integration ID
        data: Event data
        timestamp: Event timestamp
    """
    event_id: str
    event_type: str
    integration_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "integration_id": self.integration_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class IntegrationManager:
    """
    Unified Integration Manager for Heretek Swarm.
    
    This manager provides:
    - Unified integration registry
    - Lifecycle management (start/stop/restart)
    - Health monitoring
    - Configuration management
    - Event emission
    
    Attributes:
        integrations: Registered integrations
        states: Integration states
        configs: Integration configurations
    """
    
    def __init__(self, _health_check_interval: float, _max_restart_attempts: int, _enable_auto_restart: bool) -> None:
        """
        Initialize the Integration Manager.
        
        Args:
            health_check_interval: Interval between health checks in seconds
            max_restart_attempts: Maximum restart attempts before giving up
            enable_auto_restart: Enable automatic restart on failure
        """
        self.integrations: Dict[str, Any] = {}
        self.states: Dict[str, IntegrationState] = {}
        self.configs: Dict[str, IntegrationConfig] = {}
        
        self.health_check_interval = health_check_interval
        self.max_restart_attempts = max_restart_attempts
        self.enable_auto_restart = enable_auto_restart
        
        # Event callbacks
        self._event_callbacks: List[Callable] = []
        
        # Health check task
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Adapter instances
        self._langgraph_adapter = None
        self._autogen_adapter = None
        self._crewai_adapter = None
        self._openai_adapter = None
        self._anthropic_adapter = None
        
        logger.info(
            "integration_manager_initialized",
            health_check_interval=health_check_interval,
            max_restart_attempts=max_restart_attempts,
            _auto_restart = enable_auto_restart,
        )
    
    def register_event_callback(self, _callback: Callable) -> None:
        """Register a callback for integration events."""
        self._event_callbacks.append(callback)
        logger.debug("event_callback_registered", callback=callback.__name__)
    
    async def _emit_event(self, _event_type: str, _integration_id: str, _data: Optional[Dict[str, _Any]]) -> None:
        """Emit an integration event."""
        event = IntegrationEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            _event_type = event_type,
            integration_id=integration_id,
            _data = data or {},
        )
        
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error("event_callback_error", error=str(e))
        
        logger.debug(
            "event_emitted",
            _event_id = event.event_id,
            _event_type = event_type,
            integration_id=integration_id,
        )
    
    async def register_integration(self, _integration_id: str, _integration_type: IntegrationType, _name: str, _config: Optional[Dict[str, _Any]], _metadata: Optional[Dict[str, _Any]], _instance: Optional[Any]) -> IntegrationConfig:
        """
        Register a new integration.
        
        Args:
            integration_id: Unique integration identifier
            integration_type: Type of integration
            name: Human-readable name
            config: Integration configuration
            metadata: Additional metadata
            instance: Optional pre-created instance
            
        Returns:
            IntegrationConfig
        """
        _integration_config = IntegrationConfig(
            integration_id=integration_id,
            integration_type=integration_type,
            _name = name,
            config=config or {},
            _metadata = metadata or {},
        )
        
        state = IntegrationState(
            integration_id=integration_id,
            instance=instance,
        )
        
        self.configs[integration_id] = integration_config
        self.states[integration_id] = state
        
        if instance:
            state.status = IntegrationStatus.INITIALIZED
        
        logger.info(
            "integration_registered",
            integration_id=integration_id,
            _type = integration_type.value,
        )
        
        await self._emit_event(
            "integration_registered",
            integration_id,
            {"type": integration_type.value, "name": name},
        )
        
        return integration_config
    
    async def unregister_integration(self, _integration_id: str) -> bool:
        """
        Unregister an integration.
        
        Args:
            integration_id: Integration identifier
            
        Returns:
            True if unregistered
        """
        if integration_id not in self.configs:
            return False
        
        # Stop if running
        state = self.states.get(integration_id)
        if state and state.status == IntegrationStatus.RUNNING:
            await self.stop_integration(integration_id)
        
        del self.configs[integration_id]
        if integration_id in self.states:
            del self.states[integration_id]
        if integration_id in self.integrations:
            del self.integrations[integration_id]
        
        logger.info("integration_unregistered", integration_id=integration_id)
        
        await self._emit_event(
            "integration_unregistered",
            integration_id,
        )
        
        return True
    
    async def start_integration(self, _integration_id: str) -> bool:
        """
        Start an integration.
        
        Args:
            integration_id: Integration identifier
            
        Returns:
            True if started successfully
        """
        if integration_id not in self.configs:
            logger.error("integration_not_found", integration_id=integration_id)
            return False
        
        config = self.configs[integration_id]
        state = self.states[integration_id]
        
        if not config.enabled:
            logger.warning("integration_disabled", integration_id=integration_id)
            return False
        
        if state.status == IntegrationStatus.RUNNING:
            logger.info("integration_already_running", integration_id=integration_id)
            return True
        
        state.status = IntegrationStatus.STARTING
        
        try:
            # Create adapter instance based on type
            instance = await self._create_adapter_instance(config)
            state.instance = instance
            state.status = IntegrationStatus.RUNNING
            state.started_at = datetime.now(timezone.utc).isoformat()
            
            self.integrations[integration_id] = instance
            
            logger.info("integration_started", integration_id=integration_id)
            
            await self._emit_event(
                "integration_started",
                integration_id,
                {"type": config.integration_type.value},
            )
            
            return True
            
        except Exception as e:
            state.status = IntegrationStatus.FAILED
            state.error_count += 1
            
            logger.error(
                "integration_start_failed",
                integration_id=integration_id,
                error=str(e),
            )
            
            await self._emit_event(
                "integration_failed",
                integration_id,
                {"error": str(e)},
            )
            
            return False
    
    async def stop_integration(self, _integration_id: str) -> bool:
        """
        Stop an integration.
        
        Args:
            integration_id: Integration identifier
            
        Returns:
            True if stopped successfully
        """
        if integration_id not in self.states:
            return False
        
        state = self.states[integration_id]
        config = self.configs.get(integration_id)
        
        if state.status not in [IntegrationStatus.RUNNING, IntegrationStatus.STARTING]:
            logger.info("integration_not_running", integration_id=integration_id)
            return True
        
        state.status = IntegrationStatus.STOPPING
        
        try:
            # Call stop method if available
            instance = state.instance
            if instance:
                if hasattr(instance, 'stop'):
                    if asyncio.iscoroutinefunction(instance.stop):
                        await instance.stop()
                    else:
                        instance.stop()
                elif hasattr(instance, 'clear_all'):
                    instance.clear_all()
            
            state.status = IntegrationStatus.STOPPED
            state.stopped_at = datetime.now(timezone.utc).isoformat()
            
            logger.info("integration_stopped", integration_id=integration_id)
            
            await self._emit_event(
                "integration_stopped",
                integration_id,
                {"type": config.integration_type.value if config else "unknown"},
            )
            
            return True
            
        except Exception as e:
            state.status = IntegrationStatus.FAILED
            state.error_count += 1
            
            logger.error(
                "integration_stop_failed",
                integration_id=integration_id,
                error=str(e),
            )
            
            return False
    
    async def restart_integration(self, _integration_id: str) -> bool:
        """
        Restart an integration.
        
        Args:
            integration_id: Integration identifier
            
        Returns:
            True if restarted successfully
        """
        if integration_id not in self.states:
            return False
        
        state = self.states[integration_id]
        state.status = IntegrationStatus.RESTARTING
        state.restart_count += 1
        
        logger.info("integration_restart", integration_id=integration_id)
        
        await self._emit_event(
            "integration_restarting",
            integration_id,
            {"restart_count": state.restart_count},
        )
        
        # Stop
        await self.stop_integration(integration_id)
        
        # Start
        return await self.start_integration(integration_id)
    
    async def _create_adapter_instance(self, _config: IntegrationConfig) -> Any:
        """Create an adapter instance based on integration type."""
        integration_type = config.integration_type
        
        if integration_type == IntegrationType.LANGGRAPH:
            from .langgraph import get_langgraph_adapter
            _adapter = get_langgraph_adapter()
            if config.config:
                if hasattr(adapter, 'create_graph') and 'graph_id' in config.config:
                    adapter.create_graph(
                        config.config['graph_id'],
                        config.config.get('state_schema'),
                    )
            return adapter
            
        elif integration_type == IntegrationType.AUTOGEN:
            from .autogen import get_autogen_adapter
            _adapter = get_autogen_adapter()
            if config.config.get('llm_config'):
                adapter.llm_config = config.config['llm_config']
            return adapter
            
        elif integration_type == IntegrationType.CREWAI:
            from .crewai import get_crewai_adapter
            _adapter = get_crewai_adapter(
                _verbose = config.config.get('verbose', True),
                _memory_enabled = config.config.get('memory_enabled', False),
                _cache_enabled = config.config.get('cache_enabled', True),
            )
            return adapter
            
        elif integration_type == IntegrationType.OPENAI_ASSISTANTS:
            from .openai_assistants import get_openai_assistants_adapter
            _adapter = get_openai_assistants_adapter(
                _api_key = config.config.get('api_key'),
                _base_url = config.config.get('base_url'),
            )
            return adapter
            
        elif integration_type == IntegrationType.ANTHROPIC:
            from .anthropic import get_anthropic_adapter
            _adapter = get_anthropic_adapter(
                _api_key = config.config.get('api_key'),
                _base_url = config.config.get('base_url'),
            )
            return adapter
        
        else:
            logger.warning("unknown_integration_type", type=integration_type.value)
            return None
    
    async def check_health(self, _integration_id: str) -> HealthCheckResult:
        """
        Check health of an integration.
        
        Args:
            integration_id: Integration identifier
            
        Returns:
            HealthCheckResult
        """
        _start_time = datetime.now(timezone.utc)
        
        if integration_id not in self.states:
            return HealthCheckResult(
                integration_id=integration_id,
                status=HealthStatus.UNKNOWN,
                _latency_ms = 0,
                _details = {"error": "Integration not found"},
            )
        
        state = self.states[integration_id]
        
        if state.status != IntegrationStatus.RUNNING:
            return HealthCheckResult(
                integration_id=integration_id,
                status=HealthStatus.UNHEALTHY,
                _latency_ms = 0,
                _details = {"status": state.status.value},
            )
        
        try:
            # Check adapter statistics method
            instance = state.instance
            _health_details = {}
            
            if instance and hasattr(instance, 'get_statistics'):
                _stats = instance.get_statistics()
                health_details["statistics"] = stats
                
                # Determine health based on statistics
                if stats:
                    _health_status = HealthStatus.HEALTHY
                else:
                    _health_status = HealthStatus.DEGRADED
            else:
                _health_status = HealthStatus.HEALTHY
                health_details["note"] = "No statistics available"
            
            _latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            _result = HealthCheckResult(
                integration_id=integration_id,
                status=health_status,
                _latency_ms = latency_ms,
                _details = health_details,
            )
            
            state.last_health_check = result
            
            return result
            
        except Exception as e:
            _latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                integration_id=integration_id,
                status=HealthStatus.UNHEALTHY,
                _latency_ms = latency_ms,
                _details = {"error": str(e)},
            )
    
    async def _run_health_check_loop(self) -> None:
        """Background health check loop."""
        while self._running:
            try:
                for integration_id in list(self.configs.keys()):
                    _result = await self.check_health(integration_id)
                    
                    # Auto-restart on failure
                    if (
                        result.status == HealthStatus.UNHEALTHY
                        and self.enable_auto_restart
                        and self.configs[integration_id].enabled
                    ):
                        state = self.states[integration_id]
                        if state.restart_count < self.max_restart_attempts:
                            await self.restart_integration(integration_id)
                        else:
                            logger.error(
                                "max_restart_attempts_reached",
                                integration_id=integration_id,
                            )
                
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("health_check_loop_error", error=str(e))
                await asyncio.sleep(self.health_check_interval)
    
    async def start(self) -> None:
        """Start the integration manager."""
        if self._running:
            return
        
        self._running = True
        self._health_check_task = asyncio.create_task(self._run_health_check_loop())
        
        logger.info("integration_manager_started")
        
        await self._emit_event("manager_started", "manager")
    
    async def stop(self) -> None:
        """Stop the integration manager."""
        self._running = False
        
        # Stop all integrations
        for integration_id in list(self.configs.keys()):
            await self.stop_integration(integration_id)
        
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("integration_manager_stopped")
        
        await self._emit_event("manager_stopped", "manager")
    
    def get_integration(self, _integration_id: str) -> Optional[Any]:
        """Get integration instance by ID."""
        state = self.states.get(integration_id)
        return state.instance if state else None
    
    def get_integration_state(self, _integration_id: str) -> Optional[IntegrationState]:
        """Get integration state by ID."""
        return self.states.get(integration_id)
    
    def get_integration_config(self, _integration_id: str) -> Optional[IntegrationConfig]:
        """Get integration configuration by ID."""
        return self.configs.get(integration_id)
    
    def list_integrations(self, _status: Optional[IntegrationStatus], _integration_type: Optional[IntegrationType]) -> List[Dict[str, Any]]:
        """List integrations with optional filtering."""
        _result = []
        
        for integration_id, config in self.configs.items():
            if integration_type and config.integration_type != integration_type:
                continue
            
            state = self.states.get(integration_id)
            if status and (not state or state.status != status):
                continue
            
            result.append({
                "config": config.to_dict(),
                "state": state.to_dict() if state else None,
            })
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        _status_counts = {}
        _type_counts = {}
        _healthy_count = 0
        _unhealthy_count = 0
        
        for state in self.states.values():
            status = state.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            config = self.configs.get(state.integration_id)
            if config:
                _type_name = config.integration_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            if state.last_health_check:
                if state.last_health_check.status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif state.last_health_check.status == HealthStatus.UNHEALTHY:
                    unhealthy_count += 1
        
        return {
            "total_integrations": len(self.configs),
            "running_count": sum(
                1 for s in self.states.values()
                if s.status == IntegrationStatus.RUNNING
            ),
            "status_counts": status_counts,
            "type_counts": type_counts,
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "health_check_interval": self.health_check_interval,
            "auto_restart_enabled": self.enable_auto_restart,
        }
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all integrations."""
        _health_results = {}
        
        for integration_id in self.configs:
            _result = await self.check_health(integration_id)
            health_results[integration_id] = result.to_dict()
        
        _total = len(health_results)
        _healthy = sum(
            1 for r in health_results.values()
            if r["status"] == HealthStatus.HEALTHY.value
        )
        _degraded = sum(
            1 for r in health_results.values()
            if r["status"] == HealthStatus.DEGRADED.value
        )
        _unhealthy = sum(
            1 for r in health_results.values()
            if r["status"] == HealthStatus.UNHEALTHY.value
        )
        
        return {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "overall_status": (
                HealthStatus.HEALTHY.value if unhealthy == 0 and healthy == total
                else HealthStatus.DEGRADED.value if unhealthy < total / 2
                else HealthStatus.UNHEALTHY.value
            ),
            "integrations": health_results,
        }


# Global manager instance
integration_manager: Optional[IntegrationManager] = None


def get_integration_manager() -> IntegrationManager:
    """Get the global Integration Manager instance."""
    global integration_manager
    if integration_manager is None:
        _integration_manager = IntegrationManager()
    return integration_manager


async def initialize_integrations(_configs: List[Dict[str, _Any]], _agent_runtime: Optional[Any]) -> IntegrationManager:
    """
    Initialize multiple integrations from configuration.
    
    Args:
        configs: List of integration configurations
        agent_runtime: Optional agent runtime for bridging
        
    Returns:
        IntegrationManager instance
    """
    _manager = get_integration_manager()
    
    for config in configs:
        await manager.register_integration(
            _integration_id = config["integration_id"],
            _integration_type = IntegrationType(config["integration_type"]),
            _name = config.get("name", config["integration_id"]),
            config=config.get("config", {}),
            _metadata = config.get("metadata", {}),
        )
    
    # Set agent runtime for all adapters
    if agent_runtime:
        for integration_id in list(manager.configs.keys()):
            _instance = manager.get_integration(integration_id)
            if instance and hasattr(instance, 'set_agent_runtime'):
                instance.set_agent_runtime(agent_runtime)
    
    # Start manager
    await manager.start()
    
    # Start all enabled integrations
    for integration_id in list(manager.configs.keys()):
        if manager.configs[integration_id].enabled:
            await manager.start_integration(integration_id)
    
    logger.info("integrations_initialized", count=len(configs))
    return manager
