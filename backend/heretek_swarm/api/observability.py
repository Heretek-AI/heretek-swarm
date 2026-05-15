"""Observability API - re-export stub.

All endpoints, helpers, and shared state now live under
`heretek_swarm.api.observability` (the subpackage).  This module is kept as a
thin compat shim so that existing imports of `from heretek_swarm.api.observability
import router` continue to work without changes.
"""

# Re-export everything from the subpackage
from heretek_swarm.api.observability import (  # noqa: F401, E402
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    ConnectionManager,
    ReplayJobCreate,
    ReplayJobListResponse,
    ReplayJobResponse,
    TimeTravelRequestCreate,
    TimeTravelResponse,
    TraceEvent,
    _get_external_call_log_session_factory,
    _rate_limit_state,
    _traces,
    check_rate_limit,
    connection_manager,
    get_metrics_collector,
    get_metrics_stream,
    get_replay_manager,
    get_zero_trust,
    router,
    validate_input,
)
