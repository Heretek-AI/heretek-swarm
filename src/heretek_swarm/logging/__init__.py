"""
Logging package for Heretek Swarm.
"""

from .config import (
    setup_logging,
    get_logger,
    logger,
    get_request_id,
    get_agent_id,
    get_trace_id,
    set_request_id,
    set_agent_id,
    set_trace_id,
    clear_context,
    log_api_request,
    log_agent_event,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_CRITICAL,
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
