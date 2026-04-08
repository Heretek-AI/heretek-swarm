# Stub function for integration tests - provides mockable access to event mesh
# This allows tests to patch the NATS event mesh without importing the actual NATS library


def get_nats_event_mesh() -> None:
    """
    Get the NATS event mesh instance.
    
    This is a stub that returns None - actual implementation is in the
    runtime initialization. Tests should patch this to provide mock mesh.
    
    Returns:
        None (stub function for testing)
    """
    return None


def get_llm_provider() -> None:
    """
    Get the LLM provider instance.
    
    This is a stub that returns None - actual implementation is in the
    runtime initialization. Tests should patch this to provide mock LLM.
    
    Returns:
        None (stub function for testing)
    """
    return None


def get_db_pool() -> None:
    """
    Get the database connection pool.
    
    This is a stub that returns None - actual implementation is in the
    runtime initialization. Tests should patch this to provide mock DB.
    
    Returns:
        None (stub function for testing)
    """
    return None