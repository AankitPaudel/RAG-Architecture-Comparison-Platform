import pytest
from unittest.mock import AsyncMock, MagicMock

from rag.graph_pipeline import GraphRAGPipeline
from rag.models import RAGResult


@pytest.fixture
def mock_graph_store():
    store = MagicMock()
    store.find_matching_nodes.return_value = [
        {
            "id": "recursion",
            "name": "Recursion",
            "entity_type": "concept",
            "matched_entity": "recursion",
            "chunk_ids": ["1:0"],
        }
    ]
    store.traverse.return_value = (
        [{"id": "recursion", "name": "Recursion", "entity_type": "concept", "hop": 0, "chunk_ids": ["1:0"]}],
        [{"source": "Recursion", "relation": "REQUIRES", "target": "Base Case", "chunk_ids": ["1:1"], "hop": 1}],
        [["recursion", "base case"]],
        1,
    )
    store.get_chunk_ids_for_subgraph.return_value = ["1:0", "1:1"]
    return store


@pytest.fixture
def mock_graph_processor():
    processor = MagicMock()
    processor.get_all_chunks.return_value = [
        {
            "content": "Recursion is when a function calls itself.",
            "metadata": {"lecture_id": 1, "chunk_id": 0, "title": "Algorithms"},
        },
        {
            "content": "A base case stops recursive calls.",
            "metadata": {"lecture_id": 1, "chunk_id": 1, "title": "Algorithms"},
        },
    ]
    return processor


@pytest.mark.asyncio
async def test_graph_pipeline_returns_graph_metadata(
    mock_settings,
    mock_graph_store,
    mock_graph_processor,
    mock_openai_client,
):
    pipeline = GraphRAGPipeline(
        rag_processor=mock_graph_processor,
        graph_store=mock_graph_store,
        openai_client=mock_openai_client,
    )

    result = await pipeline.run("Explain recursion")

    assert isinstance(result, RAGResult)
    assert result.pipeline_name == "graph_rag"
    assert result.matched_entities
    assert len(result.graph_nodes) >= 1
    assert len(result.relationships) >= 1
    assert result.hop_count == 1
    assert result.chunks_sent_to_llm > 0


@pytest.mark.asyncio
async def test_graph_pipeline_no_graph_match(
    mock_settings,
    mock_graph_processor,
    mock_openai_client,
):
    store = MagicMock()
    store.find_matching_nodes.return_value = []
    store.traverse.return_value = ([], [], [], 0)
    store.get_chunk_ids_for_subgraph.return_value = []

    pipeline = GraphRAGPipeline(
        rag_processor=mock_graph_processor,
        graph_store=store,
        openai_client=mock_openai_client,
    )

    result = await pipeline.run("Unknown topic", allow_fallback=False)
    assert result.mode == "strict_no_match"
