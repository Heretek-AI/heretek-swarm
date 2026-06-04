"""
Composable initializers for AutonomousSwarm.

Implements Phase 2.6 of PLAN.md (§1.4 god-class
extraction; the audit's exit criterion is
"runtime/main_loop.py into composable initializers; replace
_rewire_orchestrator_refs post-hoc patching with
constructor injection").

Each module in this package owns one initialization
concern. The free functions take the swarm instance and
configure it; the main_loop method delegates to the
function. The full constructor-injection refactor
(touching every orchestrator) is queued behind a
follow-up; this commit ships the structural decomposition.

The available initializers are:

* :mod:`.channel_registry` — channel + group registries
* :mod:`.memory` — cognee reader + writer
* :mod:`.rag` — RAG retriever
* :mod:`.consensus` — MAKERConsensus engine
"""

from __future__ import annotations

from heretek_swarm.runtime.initializers import (  # noqa: F401
    channel_registry,
    consensus,
    memory,
    rag,
)
from heretek_swarm.runtime.initializers.channel_registry import (  # noqa: F401
    initialize_channel_registry,
)
from heretek_swarm.runtime.initializers.consensus import (  # noqa: F401
    initialize_consensus,
)
from heretek_swarm.runtime.initializers.memory import (  # noqa: F401
    initialize_memory,
)
from heretek_swarm.runtime.initializers.rag import (  # noqa: F401
    initialize_rag,
)

__all__ = [
    "channel_registry",
    "consensus",
    "memory",
    "rag",
    "initialize_channel_registry",
    "initialize_consensus",
    "initialize_memory",
    "initialize_rag",
]
