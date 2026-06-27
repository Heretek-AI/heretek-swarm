"""heretek_swarm_core — Phase 4 of PLAN.md.

The sovereign service library for the Heretek Swarm. Phase 4
of the audit (§1.13 'Sovereign multi-package monorepo')
carves the core sub-packages out of the single heretek-swarm
package.

This package is the future home for:
  * actors/, mixins/, base/
  * consensus/, gateway/, runtime/
  * memory/, llm/, embeddings/
  * models/, schemas/, swarm_logging/
  * config/ (lib portion), utils/, validation/, channels/

Today (2026-06-03), the canonical code still lives under
``backend/heretek_swarm/``. This ``__init__.py`` re-exports
the public surface from there so the new package is a
drop-in namespace for new code; activating the actual
build (which would require this package to own the source
files) is a multi-PR effort.

The migration plan is captured in the audit:
  1. Move the sub-packages from ``backend/heretek_swarm/``
     into this directory (``packages/core/src/heretek_swarm_core/``).
  2. Update internal imports to use the new namespace.
  3. Add heretek-swarm-core to heretek-swarm-api's deps.
  4. Activate the workspace member in the root
     ``pyproject.toml``.

Until then, this ``__init__.py`` is the bridge: new code
can write ``from heretek_swarm_core import …`` and the
import resolves through the re-exports below.
"""

from __future__ import annotations

# Re-export the canonical public surface from the legacy
# monolith. New code that imports from heretek_swarm_core
# gets the same names as if it imported from heretek_swarm.
# When the actual move happens, the re-exports below are
# removed and the source files live in this package.
from heretek_swarm.actors import (  # noqa: F401
    AgentActor,
    ActorMessage,
    ActorSupervisor,
    ActorFactory,
)
from heretek_swarm.consensus import (  # noqa: F401
    MAKERConsensus,
    EnhancedMAKERConsensus,
    SwarmDeliberationEngine,
)
from heretek_swarm.consensus.deliberation import (  # noqa: F401
    DeliberationEngine,
)
from heretek_swarm.consensus.protocol import (  # noqa: F401
    ConsensusEngine,
    compute_consensus_for,
    is_consensus_engine,
)
from heretek_swarm.gateway.auth import (  # noqa: F401
    TokenStore,
    default_token_store,
    verify_auth,
    verify_jwt,
)
from heretek_swarm.memory import (  # noqa: F401
    MemoryStore,
    MemoryType,
    MemoryEntry,
    get_default_store,
)
from heretek_swarm.llm.headroom_compat import (  # noqa: F401
    HEADROOM_AVAILABLE,
    wrap as headroom_wrap,
    unwrap as headroom_unwrap,
)
from heretek_swarm.llm.hindsight_compat import (  # noqa: F401
    HindsightClient,
    HINDSIGHT_ENABLED as HINDSIGHT_AVAILABLE,
    HINDSIGHT_URL,
    get_hindsight_client,
)
from heretek_swarm.orchestration import (  # noqa: F401
    LangGraphHeavySwarmWorkflow,
    WorkflowPhase,
    WorkflowResult,
)
from heretek_swarm.runtime.main_loop import (  # noqa: F401
    AutonomousSwarm,
)
from heretek_swarm.runtime.wiring import (  # noqa: F401
    wire_orchestrators,
    thread_event_mesh_to_supervisor,
)
from heretek_swarm.security.immune import (  # noqa: F401
    ImmuneResponseBuilding,
    ResponseOutcome,
)
from heretek_swarm.security.rate_limiter import (  # noqa: F401
    limiter,
    install_rate_limiter,
)
from heretek_swarm.services import (  # noqa: F401
    ConsensusServiceStub,
    MemoryServiceStub,
    ObservabilityServiceStub,
    RealtimeServiceStub,
)
from heretek_swarm_core.embeddings import *  # noqa: F401,F403

__all__ = [
    "AgentActor",
    "ActorMessage",
    "ActorSupervisor",
    "ActorFactory",
    "ActorOrchestrator",
    "AutonomousSwarm",
    "ConsensusEngine",
    "MAKERConsensus",
    "EnhancedMAKERConsensus",
    "SwarmDeliberationEngine",
    "DeliberationEngine",
    "compute_consensus_for",
    "is_consensus_engine",
    "TokenStore",
    "default_token_store",
    "verify_auth",
    "verify_jwt",
    "MemoryStore",
    "MemoryType",
    "MemoryEntry",
    "get_default_store",
    "HEADROOM_AVAILABLE",
    "headroom_wrap",
    "headroom_unwrap",
    "HindsightClient",
    "HINDSIGHT_AVAILABLE",
    "HINDSIGHT_URL",
    "get_hindsight_client",
    "LangGraphHeavySwarmWorkflow",
    "WorkflowPhase",
    "WorkflowResult",
    "wire_orchestrators",
    "thread_event_mesh_to_supervisor",
    "ImmuneResponseBuilding",
    "ResponseOutcome",
    "limiter",
    "install_rate_limiter",
    "ConsensusServiceStub",
    "MemoryServiceStub",
    "ObservabilityServiceStub",
    "RealtimeServiceStub",
]
