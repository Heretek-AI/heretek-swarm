"""
Autonomous Runtime Configuration

Configuration for 24/7 autonomous operation of Heretek Swarm.
Supports loading from database via ConfigurationService with environment fallback.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import os


@dataclass
class AutonomousRuntimeConfig:
    """
    Configuration for autonomous runtime.

    Attributes:
        agent_configs: Agent character configurations
        workflow_configs: Workflow definitions
        monitoring_config: Monitoring and alerting settings
        recovery_config: Failure recovery settings
        scaling_config: Auto-scaling settings
    """

    # Agent Configuration
    agent_configs: Dict[str, Path] = field(default_factory=lambda: {
        "alpha": Path(__file__).parent / "characters" / "alpha.json",
        "beta": Path(__file__).parent / "characters" / "beta.json",
        "coordinator": Path(__file__).parent / "characters" / "coordinator.json",
        "historian": Path(__file__).parent / "characters" / "historian.json",
    })

    # Workflow Configuration
    default_workflows: List[str] = field(default_factory=list)
    workflow_directory: Path = field(
        _default_factory = lambda: Path(__file__).parent.parent.parent.parent / "workflows"
    )

    # Monitoring Configuration
    monitoring_enabled: bool = True
    health_check_interval: int = 30  # seconds
    metrics_collection_interval: int = 60  # seconds
    log_retention_days: int = 30

    # Recovery Configuration
    auto_restart_enabled: bool = True
    max_restart_attempts: int = 3
    restart_delay_seconds: int = 60
    state_persistence_enabled: bool = True
    state_backup_interval: int = 300  # seconds

    # Scaling Configuration
    auto_scaling_enabled: bool = False
    min_agents: int = 3
    max_agents: int = 20
    scale_up_threshold: float = 0.8  # CPU/memory usage
    scale_down_threshold: float = 0.3

    # Consciousness Plugin Configuration
    consciousness_plugin_enabled: bool = True
    consciousness_metrics_interval: int = 120  # seconds

    # RAG Configuration
    rag_enabled: bool = True
    rag_document_directory: Path = field(
        _default_factory = lambda: Path(__file__).parent.parent.parent.parent / "documents"
    )

    # Platform Integration Configuration
    discord_bot_enabled: bool = False
    telegram_bot_enabled: bool = False
    slack_bot_enabled: bool = False

    # API Configuration
    # SECURITY: Default to 127.0.0.1 for local-only access. Set API_HOST env var to "0.0.0.0" only if external binding is explicitly required.
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_workers: int = 4

    # Database Configuration
    database_url: Optional[str] = None
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"

    # Memory Configuration
    mem0_enabled: bool = True
    memory_retention_days: int = 90

    # Security Configuration
    auth_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_directory: Path = field(
        _default_factory = lambda: Path(__file__).parent.parent.parent.parent / "logs"
    )


@dataclass
class AlertConfig:
    """
    Alert configuration for monitoring.

    Attributes:
        enabled: Whether alerts are enabled
        channels: Alert channels (email, slack, discord)
        thresholds: Alert thresholds
    """

    enabled: bool = True
    email_enabled: bool = False
    email_recipients: List[str] = field(default_factory=list)
    slack_channel: Optional[str] = None
    discord_channel: Optional[str] = None

    # Alert Thresholds
    agent_failure_threshold: int = 3  # failures within window
    high_latency_threshold_ms: int = 5000
    memory_usage_threshold: float = 0.9
    consciousness_drop_threshold: float = 0.3

    # Alert Cooldown
    alert_cooldown_seconds: int = 300  # Don't spam alerts


@dataclass
class ScalingPolicy:
    """
    Auto-scaling policy configuration.

    Attributes:
        policy_type: Type of scaling policy
        triggers: Conditions that trigger scaling
        limits: Scaling limits
    """

    policy_type: str = "manual"  # manual, automatic, scheduled
    scale_up_cpu_threshold: float = 0.8
    scale_up_memory_threshold: float = 0.8
    scale_down_cpu_threshold: float = 0.3
    scale_down_memory_threshold: float = 0.3
    scale_up_cooldown_minutes: int = 10
    scale_down_cooldown_minutes: int = 30
    min_uptime_before_scale_down: int = 60  # minutes


async def load_config_from_env() -> AutonomousRuntimeConfig:
    """
    Load runtime configuration from environment variables or database.
    
    Uses environment variables as the primary source for runtime configuration.
    For database-backed configuration, use the ConfigLoader class instead.

    Returns:
        AutonomousRuntimeConfig instance
    """
    # Try to load from ConfigLoader if available (database-backed)
    try:
        from heretek_swarm.config.loader import get_config_loader
        _loader = get_config_loader()
        
        if loader._initialized:
            # Load from database with environment fallback
            _monitoring_enabled = await loader.get_async("runtime.monitoring_enabled", default=os.getenv("MONITORING_ENABLED", "true"))
            _auto_restart_enabled = await loader.get_async("runtime.auto_restart_enabled", default=os.getenv("AUTO_RESTART_ENABLED", "true"))
            _consciousness_enabled = await loader.get_async("consciousness.enabled", default=os.getenv("CONSCIOUSNESS_ENABLED", "true"))
            _rag_enabled = await loader.get_async("rag.enabled", default=os.getenv("RAG_ENABLED", "true"))
            _discord_enabled = await loader.get_async("integrations.discord_enabled", default=os.getenv("DISCORD_BOT_ENABLED", "false"))
            _telegram_enabled = await loader.get_async("integrations.telegram_enabled", default=os.getenv("TELEGRAM_BOT_ENABLED", "false"))
            _slack_enabled = await loader.get_async("integrations.slack_enabled", default=os.getenv("SLACK_BOT_ENABLED", "false"))
            _api_host = await loader.get_async("api.host", default=os.getenv("API_HOST", "127.0.0.1"))
            _api_port = await loader.get_async("api.port", default=int(os.getenv("API_PORT", "8000")))
            _database_url = await loader.get_async("database.url", default=os.getenv("DATABASE_URL"))
            _redis_url = await loader.get_async("redis.url", default=os.getenv("REDIS_URL", "redis://localhost:6379"))
            _qdrant_url = await loader.get_async("qdrant.url", default=os.getenv("QDRANT_URL", "http://localhost:6333"))
            _log_level = await loader.get_async("logging.level", default=os.getenv("LOG_LEVEL", "INFO"))
            
            # Convert string values to bool if needed
            if isinstance(monitoring_enabled, str):
                _monitoring_enabled = monitoring_enabled.lower() == "true"
            if isinstance(auto_restart_enabled, str):
                _auto_restart_enabled = auto_restart_enabled.lower() == "true"
            if isinstance(consciousness_enabled, str):
                _consciousness_enabled = consciousness_enabled.lower() == "true"
            if isinstance(rag_enabled, str):
                _rag_enabled = rag_enabled.lower() == "true"
            if isinstance(discord_enabled, str):
                _discord_enabled = discord_enabled.lower() == "true"
            if isinstance(telegram_enabled, str):
                _telegram_enabled = telegram_enabled.lower() == "true"
            if isinstance(slack_enabled, str):
                _slack_enabled = slack_enabled.lower() == "true"
            
            return AutonomousRuntimeConfig(
                _monitoring_enabled = monitoring_enabled,
                _auto_restart_enabled = auto_restart_enabled,
                _consciousness_plugin_enabled = consciousness_enabled,
                _rag_enabled = rag_enabled,
                _discord_bot_enabled = discord_enabled,
                _telegram_bot_enabled = telegram_enabled,
                _slack_bot_enabled = slack_enabled,
                _api_host = str(api_host),
                _api_port = int(api_port),
                _database_url = database_url,
                _redis_url = str(redis_url),
                _qdrant_url = str(qdrant_url),
                _log_level = str(log_level),
            )
    except Exception as e:
        import structlog
        _logger = structlog.get_logger("config.runtime")
        logger.warning("Failed to load config from database, using environment fallback", error=str(e))
    
    # Fallback to direct environment variable loading
    return AutonomousRuntimeConfig(
        _monitoring_enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true",
        _auto_restart_enabled = os.getenv("AUTO_RESTART_ENABLED", "true").lower() == "true",
        _consciousness_plugin_enabled = os.getenv("CONSCIOUSNESS_ENABLED", "true").lower() == "true",
        _rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true",
        _discord_bot_enabled = os.getenv("DISCORD_BOT_ENABLED", "false").lower() == "true",
        _telegram_bot_enabled = os.getenv("TELEGRAM_BOT_ENABLED", "false").lower() == "true",
        _slack_bot_enabled = os.getenv("SLACK_BOT_ENABLED", "false").lower() == "true",
        _api_host = os.getenv("API_HOST", "127.0.0.1"),
        _api_port = int(os.getenv("API_PORT", "8000")),
        _database_url = os.getenv("DATABASE_URL"),
        _redis_url = os.getenv("REDIS_URL", "redis://localhost:6379"),
        _qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333"),
        _log_level = os.getenv("LOG_LEVEL", "INFO"),
    )


def load_config_from_env_sync() -> AutonomousRuntimeConfig:
    """
    Synchronous version of load_config_from_env for non-async contexts.
    
    Returns:
        AutonomousRuntimeConfig instance
    """
    import asyncio
    
    try:
        _loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we can't use run_until_complete
            # Return environment-only config
            return _load_config_from_env_sync_fallback()
        return loop.run_until_complete(load_config_from_env())
    except RuntimeError:
        # No event loop exists
        return _load_config_from_env_sync_fallback()


def _load_config_from_env_sync_fallback() -> AutonomousRuntimeConfig:
    """
    Synchronous fallback that only reads from environment variables.
    
    Returns:
        AutonomousRuntimeConfig instance
    """
    return AutonomousRuntimeConfig(
        _monitoring_enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true",
        _auto_restart_enabled = os.getenv("AUTO_RESTART_ENABLED", "true").lower() == "true",
        _consciousness_plugin_enabled = os.getenv("CONSCIOUSNESS_ENABLED", "true").lower() == "true",
        _rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true",
        _discord_bot_enabled = os.getenv("DISCORD_BOT_ENABLED", "false").lower() == "true",
        _telegram_bot_enabled = os.getenv("TELEGRAM_BOT_ENABLED", "false").lower() == "true",
        _slack_bot_enabled = os.getenv("SLACK_BOT_ENABLED", "false").lower() == "true",
        _api_host = os.getenv("API_HOST", "127.0.0.1"),
        _api_port = int(os.getenv("API_PORT", "8000")),
        _database_url = os.getenv("DATABASE_URL"),
        _redis_url = os.getenv("REDIS_URL", "redis://localhost:6379"),
        _qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333"),
        _log_level = os.getenv("LOG_LEVEL", "INFO"),
    )
