"""
Knowledge Access Layer for Heretek Swarm

Provides unified interface for querying memory and RAG systems
with intelligent result merging and MMR reranking.
"""

from heretek_swarm.knowledge.unified_access import (
    UnifiedKnowledgeAccess,
    KnowledgeEntry,
    KnowledgeQueryResult,
    KnowledgeQueryBuilder,
)

__all__ = [
    "UnifiedKnowledgeAccess",
    "KnowledgeEntry",
    "KnowledgeQueryResult",
    "KnowledgeQueryBuilder",
]
