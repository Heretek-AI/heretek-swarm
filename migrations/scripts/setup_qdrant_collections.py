#!/usr/bin/env python3
"""
Qdrant Collection Setup Script
Initializes vector collections for RAG and memory systems.
"""

import os
import sys
from typing import Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        CollectionConfig,
        OptimizersConfigDiff,
        HnswConfigDiff,
        WalConfigDiff,
        QuantizationConfigDiff,
        ScalarQuantization,
        ScalarType,
    )
except ImportError:
    print("ERROR: qdrant-client not installed. Install with: pip install qdrant-client")
    sys.exit(1)


def get_qdrant_url() -> str:
    """Get Qdrant URL from environment or use default."""
    return os.environ.get("QDRANT_URL", "http://localhost:6333")


def get_api_key() -> Optional[str]:
    """Get Qdrant API key from environment."""
    return os.environ.get("QDRANT_API_KEY")


def create_collection_if_not_exists(_client: QdrantClient, _collection_name: str, _vector_size: int, _distance: str, _description: str) -> bool:
    """Create a collection if it doesn't already exist."""
    try:
        # Check if collection exists
        _collections = client.get_collections().collections
        _existing = [c.name for c in collections]

        if collection_name in existing:
            print(f"✓ Collection '{collection_name}' already exists")
            return False

        # Create collection with optimized settings
        client.create_collection(
            _collection_name = collection_name,
            _vectors_config = VectorParams(
                _size = vector_size,
                _distance = Distance[distance.upper()],
            ),
            _optimizers_config = OptimizersConfigDiff(
                _indexing_threshold = 20000,
                _vacuum_min_vector_number = 1000,
                _default_segment_number = 2,
            ),
            _hnsw_config = HnswConfigDiff(
                _m = 16,
                _ef_construct = 100,
                _full_scan_threshold = 10000,
            ),
            _wal_config = WalConfigDiff(
                _wal_capacity_mb = 32,
                _wal_segments_number = 2,
            ),
            _quantization_config = QuantizationConfigDiff(
                _scalar = ScalarQuantization(
                    _type = ScalarType.INT8,
                    _quantile = 0.99,
                    _always_ram = True,
                )
            ),
        )

        print(f"✓ Created collection '{collection_name}' (size={vector_size}, distance={distance})")
        return True

    except Exception as e:
        print(f"✗ Error creating collection '{collection_name}': {e}")
        return False


def setup_collections() -> dict:
    """Set up all Qdrant collections for Heretek Swarm.
    
    Session 45 additions:
    - heretek_patterns: Collective learning pattern vectors
    - heretek_consensus: Consensus deliberation embeddings
    - heretek_memory_access: Memory access pattern vectors
    """
    # Collection definitions
    _collections = {
        "heretek_rag": {
            "vector_size": 1536,  # OpenAI text-embedding-3-small
            "distance": "Cosine",
            "description": "RAG document embeddings",
        },
        "heretek_memory": {
            "vector_size": 1536,  # OpenAI text-embedding-3-small
            "distance": "Cosine",
            "description": "Agent memory embeddings",
        },
        "heretek_semantic": {
            "vector_size": 1536,
            "distance": "Cosine",
            "description": "Semantic knowledge embeddings",
        },
        "heretek_context": {
            "vector_size": 1536,
            "distance": "Cosine",
            "description": "Context and conversation embeddings",
        },
        # Session 45: Collective Learning Collections
        "heretek_patterns": {
            "vector_size": 1536,
            "distance": "Cosine",
            "description": "Collective learning pattern vectors (Session 45)",
        },
        "heretek_consensus": {
            "vector_size": 1536,
            "distance": "Cosine",
            "description": "Consensus deliberation embeddings (Session 45)",
        },
        "heretek_memory_access": {
            "vector_size": 1536,
            "distance": "Cosine",
            "description": "Memory access pattern vectors (Session 45)",
        },
    }

    # Connect to Qdrant
    _url = get_qdrant_url()
    _api_key = get_api_key()

    print(f"Connecting to Qdrant at {url}...")
    try:
        _client = QdrantClient(url=url, api_key=api_key)
        print("✓ Connected to Qdrant")
    except Exception as e:
        print(f"✗ Failed to connect to Qdrant: {e}")
        return {"success": False, "error": str(e)}

    # Create collections
    _results = {"created": [], "existing": [], "failed": []}

    for name, config in collections.items():
        try:
            _created = create_collection_if_not_exists(
                client,
                _collection_name = name,
                _vector_size = config["vector_size"],
                _distance = config["distance"],
                _description = config["description"],
            )
            if created:
                results["created"].append(name)
            else:
                results["existing"].append(name)
        except Exception as e:
            results["failed"].append({"name": name, "error": str(e)})

    # Create payload indexes for efficient filtering
    print("\nCreating payload indexes...")

    _indexes_to_create = [
        # Original indexes (Session 1-44)
        ("heretek_rag", "source"),
        ("heretek_rag", "document_type"),
        ("heretek_rag", "created_at"),
        ("heretek_memory", "agent_id"),
        ("heretek_memory", "memory_type"),
        ("heretek_memory", "tier"),
        ("heretek_semantic", "category"),
        ("heretek_semantic", "domain"),
        ("heretek_context", "session_id"),
        ("heretek_context", "agent_id"),
        # Session 45: Collective Learning indexes
        ("heretek_patterns", "pattern_type"),
        ("heretek_patterns", "pattern_category"),
        ("heretek_patterns", "state"),
        ("heretek_patterns", "discovered_by"),
        ("heretek_patterns", "confidence_score"),
        # Session 45: Consensus indexes
        ("heretek_consensus", "proposal_type"),
        ("heretek_consensus", "state"),
        ("heretek_consensus", "agent_id"),
        ("heretek_consensus", "round_number"),
        # Session 45: Memory Access indexes
        ("heretek_memory_access", "agent_id"),
        ("heretek_memory_access", "access_type"),
        ("heretek_memory_access", "tier"),
        ("heretek_memory_access", "cache_hit"),
    ]

    for collection, field in indexes_to_create:
        try:
            client.create_payload_index(
                _collection_name = collection,
                _field_name = field,
                _field_schema = "keyword",
            )
            print(f"✓ Created index on {collection}.{field}")
        except Exception as e:
            print(f"✗ Error creating index on {collection}.{field}: {e}")

    return {
        "success": True,
        "created": results["created"],
        "existing": results["existing"],
        "failed": results["failed"],
    }


def main():
    """Main entry point."""
    print("=" * 60)
    print("Heretek Swarm - Qdrant Collection Setup")
    print("=" * 60)
    print()

    _results = setup_collections()

    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Created: {len(results.get('created', []))}")
    print(f"  Existing: {len(results.get('existing', []))}")
    print(f"  Failed: {len(results.get('failed', []))}")
    print()
    print("Collections:")
    for name in collections:
        _status = "✓" if name in results.get("created", []) or name in results.get("existing", []) else "✗"
        print(f"  {status} {name}")
    print("=" * 60)

    if results.get("failed"):
        print("\nFailed collections:")
        for item in results["failed"]:
            print(f"  - {item['name']}: {item['error']}")
        sys.exit(1)

    print("\n✓ Qdrant collection setup complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
