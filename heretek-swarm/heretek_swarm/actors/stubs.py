# Stub function for integration tests - provides mockable access to event mesh
# This allows tests to patch the NATS event mesh without importing the actual NATS library
from heretek_swarm.gateway import NATSEventMesh

# Global mesh instance
_nats_mesh: NATSEventMesh | None = None


def get_nats_event_mesh() -> NATSEventMesh | None:
    """
    Get the NATS event mesh instance.

    Returns the global NATSEventMesh instance for NATS-based
    actor communication. The mesh is lazily initialized on first access.

    Returns:
        NATSEventMesh instance or None if not initialized
    """
    global _nats_mesh
    if _nats_mesh is None:
        # Try to get from gateway module
        from heretek_swarm.gateway.nats_event_mesh import get_nats_bridge
        bridge = get_nats_bridge()
        if bridge is not None:
            _nats_mesh = bridge.mesh
    return _nats_mesh


def get_llm_provider() -> None:
    """
    Get the LLM provider instance.

    This is a stub that returns None - actual implementation is in the
    runtime initialization. Tests should patch this to provide mock LLM.

    Returns:
        None (stub function for testing)
    """
    return


def get_db_pool() -> None:
    """
    Get the database connection pool.

    This is a stub that returns None - actual implementation is in the
    runtime initialization. Tests should patch this to provide mock DB.

    Returns:
        None (stub function for testing)
    """
    return
