"""
Heretek Swarm API Module

Provides FastAPI-based HTTP and WebSocket endpoints:
- Health checks for all services
- Agent management and monitoring
- Memory statistics
- A2A protocol WebSocket
- Consensus voting endpoints
- Plugin management

Example:
    ```python
    import uvicorn
    from heretek_swarm.api.main import app

    # Start the API server
    uvicorn.run(app, host="0.0.0.0", port=8000)
    ```
"""

from heretek_swarm.api.main import app
from heretek_swarm.api import websockets, consensus, plugins, observability
from heretek_swarm.api import consciousness, emergent_intelligence, collective_evolution

__all__ = [
    "app",
    "websockets",
    "consensus",
    "plugins",
    "observability",
    "consciousness",
    "emergent_intelligence",
    "collective_evolution",
]
