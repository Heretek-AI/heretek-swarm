"""
Configuration Service Module

Provides database-backed configuration management with:
- CRUD operations for configurations
- In-memory caching with TTL
- API key encryption
- Import/export functionality
- Migration from environment variables

Usage:
    from heretek_swarm.config import (
        ConfigurationService,
        ConfigLoader,
        get_config,
        initialize_config_service,
        shutdown_config_service,
    )
"""

from .loader import (
    ConfigLoader,
    get_config,
    get_config_loader,
    get_config_with_source,
    initialize_config_loader,
    reload_config,
)
from .service import (
    ConfigurationService,
    get_config_service,
    initialize_config_service,
    shutdown_config_service,
)

__all__ = [
    # Service
    "ConfigurationService",
    "get_config_service",
    "initialize_config_service",
    "shutdown_config_service",

    # Loader
    "ConfigLoader",
    "get_config_loader",
    "get_config",
    "get_config_with_source",
    "reload_config",
    "initialize_config_loader",
]
