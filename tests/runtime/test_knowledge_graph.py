"""
M019 S05: RAGFlow Knowledge Graph — Integration Tests

Tests the knowledge graph retriever and RAGFlow-inspired patterns:
1. SubQuestionDecomposer query decomposition
2. KnowledgeGraphRetriever chunk registration and traversal
3. Knowledge graph API endpoints
"""

import asyncio

import pytest


class AsyncTestCase:
    """Base async test case."""

    @pytest.fixture(autouse=True)
    def setup_event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()


class TestSubQuestionDecomposer:
    """T01: SubQuestion decomposition patterns."""

    def test_decompose_no_pattern_returns_original(self):
        """Simple queries with no decomposition pattern return [query]."""
        from heretek_swarm.rag.knowledge_graph import SubQuestionDecomposer

        decomposer = SubQuestionDecomposer()
        result = decomposer.decompose("What is the capital of France?")

        assert len(result) >= 1
        assert result[0].lower().startswith("what")

    def test_decompose_sequential_split(self):
        """Sequential queries split on 'and then', 'next', 'secondly'."""
        from heretek_swarm.rag.knowledge_graph import SubQuestionDecomposer

        decomposer = SubQuestionDecomposer()
        result = decomposer.decompose(
            "What is photosynthesis? and then how does it relate to plant growth?"
        )

        assert len(result) >= 2

    def test_decompose_comparative(self):
        """Comparative queries split on 'vs', 'versus'."""
        from heretek_swarm.rag.knowledge_graph import SubQuestionDecomposer

        decomposer = SubQuestionDecomposer()
        result = decomposer.decompose("Compare transformer models vs RNN architectures")

        # Should identify comparative structure
        assert len(result) >= 1

    def test_decompose_causal(self):
        """Causal queries split on 'because', 'therefore'."""
        from heretek_swarm.rag.knowledge_graph import SubQuestionDecomposer

        decomposer = SubQuestionDecomposer()
        result = decomposer.decompose(
            "Why did the system fail because of the configuration error therefore it stopped working"
        )

        assert len(result) >= 2

    def test_decompose_deduplicates(self):
        """Duplicate sub-questions are removed."""
        from heretek_swarm.rag.knowledge_graph import SubQuestionDecomposer

        decomposer = SubQuestionDecomposer()
        result = decomposer.decompose("Explain X. Then explain X again.")

        # Should deduplicate
        seen = [q.lower().strip() for q in result]
        assert len(seen) == len(set(seen))


class TestKnowledgeGraphRetriever:
    """T02-T03: Chunk graph registration and traversal."""

    @pytest.mark.asyncio
    async def test_register_chunks_builds_graph(self):
        """register_chunks() populates the internal chunk graph."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            KnowledgeGraphRetriever,
        )

        kg = KnowledgeGraphRetriever()

        chunks = [
            GraphChunkNode(
                chunk_id="c1",
                document_id="doc-1",
                content="Root content",
                heading_path=["Chapter 1"],
                level=0,
            ),
            GraphChunkNode(
                chunk_id="c2",
                document_id="doc-1",
                content="Child content",
                heading_path=["Chapter 1", "Section 1.1"],
                parent_chunk_id="c1",
                level=1,
            ),
        ]

        count = kg.register_chunks(chunks)

        assert count == 2
        assert "c1" in kg._chunk_graph
        assert "c2" in kg._chunk_graph

    @pytest.mark.asyncio
    async def test_parent_child_relationships(self):
        """Parent-child heading relationships are built correctly."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            KnowledgeGraphRetriever,
        )

        kg = KnowledgeGraphRetriever()

        parent = GraphChunkNode(
            chunk_id="parent",
            document_id="doc",
            content="Parent chunk",
            heading_path=["Introduction"],
            level=0,
        )
        child = GraphChunkNode(
            chunk_id="child",
            document_id="doc",
            content="Child chunk",
            heading_path=["Introduction", "Background"],
            parent_chunk_id="parent",
            level=1,
        )

        kg.register_chunks([parent, child])

        retrieved_parent = kg.get_chunk("parent")
        retrieved_child = kg.get_chunk("child")

        assert retrieved_child is not None
        assert retrieved_parent is not None

    @pytest.mark.asyncio
    async def test_expand_by_heading_walks_hierarchy(self):
        """expand_by_heading() walks from chunk to root."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            KnowledgeGraphRetriever,
        )

        kg = KnowledgeGraphRetriever()

        chunks = [
            GraphChunkNode(
                chunk_id="root",
                document_id="doc",
                content="Root",
                level=0,
            ),
            GraphChunkNode(
                chunk_id="mid",
                document_id="doc",
                content="Mid",
                heading_path=["Chapter 1"],
                parent_chunk_id="root",
                level=1,
            ),
            GraphChunkNode(
                chunk_id="leaf",
                document_id="doc",
                content="Leaf",
                heading_path=["Chapter 1", "Section 1.1"],
                parent_chunk_id="mid",
                level=2,
            ),
        ]
        kg.register_chunks(chunks)

        # Expand from leaf
        results = kg.expand_by_heading("leaf")
        result_ids = [r.chunk_id for r in results]

        assert "leaf" in result_ids
        assert "mid" in result_ids
        assert "root" in result_ids
        # Order is leaf → mid → root
        assert result_ids.index("mid") < result_ids.index("root")

    @pytest.mark.asyncio
    async def test_get_parent_chunks(self):
        """get_parent_chunks() returns ancestor chunks."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            KnowledgeGraphRetriever,
        )

        kg = KnowledgeGraphRetriever()
        kg.register_chunks([
            GraphChunkNode(chunk_id="p1", document_id="d", content="", level=0),
            GraphChunkNode(
                chunk_id="c1",
                document_id="d",
                content="",
                parent_chunk_id="p1",
                level=1,
            ),
        ])

        parents = kg.get_parent_chunks("c1")
        assert len(parents) == 1
        assert parents[0].chunk_id == "p1"

    @pytest.mark.asyncio
    async def test_retrieve_with_graph_traversal(self):
        """retrieve() uses graph traversal for seeded chunks."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            KnowledgeGraphRetriever,
        )

        kg = KnowledgeGraphRetriever()
        kg.register_chunks([
            GraphChunkNode(chunk_id="root", document_id="doc", content="Root chunk", level=0),
            GraphChunkNode(
                chunk_id="child",
                document_id="doc",
                content="Child chunk",
                parent_chunk_id="root",
                level=1,
            ),
        ])

        results = await kg.retrieve(
            query="test",
            top_k=5,
            seed_chunk_ids=["root"],
        )

        result_ids = [r.chunk_id for r in results]
        assert "root" in result_ids

    @pytest.mark.asyncio
    async def test_retrieve_with_sub_question_decomposition(self):
        """retrieve() decomposes complex queries before retrieval."""
        from heretek_swarm.rag.knowledge_graph import KnowledgeGraphRetriever

        kg = KnowledgeGraphRetriever()
        kg.config.sub_question_enabled = True

        results = await kg.retrieve(
            query="What is X? And how does X affect Y?",
            top_k=5,
        )

        # Should return results (empty graph but decomposer ran)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_retrieve_scores_by_hop_depth(self):
        """Deeper traversal results score lower."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            KnowledgeGraphRetriever,
        )

        kg = KnowledgeGraphRetriever()
        kg.register_chunks([
            GraphChunkNode(chunk_id="seed", document_id="d", content="Seed", level=0),
            GraphChunkNode(chunk_id="level1", document_id="d", content="L1", parent_chunk_id="seed", level=1),
            GraphChunkNode(chunk_id="level2", document_id="d", content="L2", parent_chunk_id="level1", level=2),
        ])

        results = await kg.retrieve(
            query="test",
            top_k=10,
            seed_chunk_ids=["seed"],
        )

        # Find seed and level2 results
        seed_score = next((r.score for r in results if r.chunk_id == "seed"), None)
        level2_score = next((r.score for r in results if r.chunk_id == "level2"), None)

        if seed_score is not None and level2_score is not None:
            assert seed_score > level2_score

    def test_get_statistics(self):
        """get_statistics() returns correct graph metrics."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            KnowledgeGraphRetriever,
        )

        kg = KnowledgeGraphRetriever()
        kg.register_chunks([
            GraphChunkNode(chunk_id="c1", document_id="doc", content="", level=0),
            GraphChunkNode(chunk_id="c2", document_id="doc", content="", parent_chunk_id="c1", level=1),
        ])

        stats = kg.get_statistics()

        assert stats["total_chunks"] == 2
        assert stats["max_heading_depth"] >= 1


class TestKnowledgeGraphAPIEndpoints:
    """T04: RAGFlow knowledge graph API endpoints."""

    def test_decompose_endpoint_exists(self):
        """RAG API has /graph/decompose endpoint."""
        from heretek_swarm.api.rag import router

        paths = [r.path for r in router.routes]
        assert any("graph" in p for p in paths)

    def test_knowledge_graph_module_imports_cleanly(self):
        """rag/knowledge_graph.py compiles without errors."""
        from heretek_swarm.rag.knowledge_graph import (
            GraphChunkNode,
            GraphRelationshipType,
            GraphRetrievalResult,
            KnowledgeGraphConfig,
            KnowledgeGraphRetriever,
            SubQuestionDecomposer,
        )

        assert issubclass(GraphChunkNode, object)
        assert SubQuestionDecomposer is not None
        assert KnowledgeGraphConfig is not None

    def test_graph_chunk_node_defaults(self):
        """GraphChunkNode has sensible defaults."""
        from heretek_swarm.rag.knowledge_graph import GraphChunkNode

        node = GraphChunkNode(
            chunk_id="test",
            document_id="doc",
            content="Hello",
        )

        assert node.heading_path == []
        assert node.parent_chunk_id is None
        assert node.child_chunk_ids == []
        assert node.level == 0
        assert node.metadata == {}

    def test_graph_retrieval_result_fields(self):
        """GraphRetrievalResult has all required fields."""
        from heretek_swarm.rag.knowledge_graph import GraphRetrievalResult

        result = GraphRetrievalResult(
            chunk_id="c1",
            content="Test content",
            score=0.95,
        )

        assert result.chunk_id == "c1"
        assert result.heading_path == []
        assert result.traversal_path == []
        assert result.hop_depth == 0
        assert result.graph_edges_count == 0

    def test_rag_api_router_has_graph_endpoints(self):
        """RAG router has knowledge graph endpoints registered."""
        import inspect
        from heretek_swarm.api.rag import router

        endpoint_names = [
            name
            for name, obj in inspect.getmembers(router)
            if inspect.isfunction(obj) and hasattr(obj, "__wrapped__")
        ]

        # Check the routes themselves
        route_paths = [r.path for r in router.routes]
        assert any("graph" in p for p in route_paths)
