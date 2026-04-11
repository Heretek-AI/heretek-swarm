"""
Logging package for Heretek Swarm.
"""

from .config import (
    LOG_LEVEL_CRITICAL,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    clear_context,
    get_agent_id,
    get_logger,
    get_request_id,
    get_trace_id,
    log_agent_event,
    log_api_request,
    logger,
    set_agent_id,
    set_request_id,
    set_trace_id,
    setup_logging,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "logger",
    "get_request_id",
    "get_agent_id",
    "get_trace_id",
    "set_request_id",
    "set_agent_id",
    "set_trace_id",
    "clear_context",
    "log_api_request",
    "log_agent_event",
    "LOG_LEVEL_DEBUG",
    "LOG_LEVEL_INFO",
    "LOG_LEVEL_WARNING",
    "LOG_LEVEL_ERROR",
    "LOG_LEVEL_CRITICAL",
]
