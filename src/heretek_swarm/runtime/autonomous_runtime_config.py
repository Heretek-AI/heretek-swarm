"""
Autonomous Runtime Configuration

Configuration for 24/7 autonomous operation of Heretek Swarm.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


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
        default_factory=lambda: Path(__file__).parent.parent.parent.parent / "workflows"
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
        default_factory=lambda: Path(__file__).parent.parent.parent.parent / "documents"
    )

    # Platform Integration Configuration
    discord_bot_enabled: bool = False
    telegram_bot_enabled: bool = False
    slack_bot_enabled: bool = False

    # API Configuration
    api_host: str = "0.0.0.0"
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
        default_factory=lambda: Path(__file__).parent.parent.parent.parent / "logs"
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


def load_config_from_env() -> AutonomousRuntimeConfig:
    """
    Load runtime configuration from environment variables.

    Returns:
        AutonomousRuntimeConfig instance
    """
    import os

    return AutonomousRuntimeConfig(
        monitoring_enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
        auto_restart_enabled=os.getenv("AUTO_RESTART_ENABLED", "true").lower() == "true",
        consciousness_plugin_enabled=os.getenv("CONSCIOUSNESS_ENABLED", "true").lower() == "true",
        rag_enabled=os.getenv("RAG_ENABLED", "true").lower() == "true",
        discord_bot_enabled=os.getenv("DISCORD_BOT_ENABLED", "false").lower() == "true",
        telegram_bot_enabled=os.getenv("TELEGRAM_BOT_ENABLED", "false").lower() == "true",
        slack_bot_enabled=os.getenv("SLACK_BOT_ENABLED", "false").lower() == "true",
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        database_url=os.getenv("DATABASE_URL"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
