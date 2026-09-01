import pytest
from unittest.mock import AsyncMock, MagicMock

from rag.hybrid_pipeline import HybridRAGPipeline
from rag.models import RAGResult, RetrievedChunk
from rag.reranker import CompositeReranker


@pytest.fixture
def hybrid_chunks():
    return [
        {
            "content": "Recursion is a function calling itself.",
            "metadata": {"lecture_id": 1, "chunk_id": 0, "title": "Algorithms", "dense_rank": 1},
            "score": 0.9,
            "fused_rank": 1,
        },
        {
            "content": "A base case stops recursive calls.",
            "metadata": {"lecture_id": 1, "chunk_id": 1, "title": "Algorithms", "bm25_rank": 1},
            "score": 0.8,
            "fused_rank": 2,
        },
    ]


@pytest.fixture
def mock_hybrid_processor(hybrid_chunks):
    processor = MagicMock()
    processor.find_relevant_context = AsyncMock(return_value=hybrid_chunks)
    processor.get_all_chunks = MagicMock(return_value=[
        {"content": item["content"], "metadata": item["metadata"]}
        for item in hybrid_chunks
    ])
    return processor


@pytest.mark.asyncio
async def test_hybrid_pipeline_runs_full_flow(mock_settings, mock_hybrid_processor, mock_openai_client):
    pipeline = HybridRAGPipeline(
        rag_processor=mock_hybrid_processor,
        openai_client=mock_openai_client,
        retrieval_top_k=5,
        final_top_k=2,
    )

    result = await pipeline.run("Explain recursion")

    assert isinstance(result, RAGResult)
    assert result.pipeline_name == "hybrid_rag"
    assert result.mode == "strict_rag"
    assert result.num_chunks_retrieved <= 2
    assert result.chunks_considered >= 1
    assert result.chunks_sent_to_llm <= 2
    assert result.retrieval_time_ms >= 0
    assert result.reranking_time_ms >= 0
    assert result.generation_time_ms >= 0


@pytest.mark.asyncio
async def test_hybrid_pipeline_chunk_metadata(mock_settings, mock_hybrid_processor, mock_openai_client):
    pipeline = HybridRAGPipeline(
        rag_processor=mock_hybrid_processor,
        openai_client=mock_openai_client,
        final_top_k=2,
    )

    result = await pipeline.run("Explain recursion")

    for chunk in result.retrieved_chunks:
        assert isinstance(chunk, RetrievedChunk)
        assert chunk.reranked_rank is not None


@pytest.mark.asyncio
async def test_hybrid_pipeline_no_results(mock_settings, mock_openai_client):
    processor = MagicMock()
    processor.find_relevant_context = AsyncMock(return_value=[])
    processor.get_all_chunks = MagicMock(return_value=[])

    pipeline = HybridRAGPipeline(
        rag_processor=processor,
        openai_client=mock_openai_client,
    )

    result = await pipeline.run("Unknown?", allow_fallback=False)

    assert result.mode == "strict_no_match"
    assert result.num_chunks_retrieved == 0


@pytest.mark.asyncio
async def test_composite_reranker_orders_chunks():
    reranker = CompositeReranker()
    chunks = [
        RetrievedChunk(content="iteration loops", metadata={}, score=0.4, fused_rank=2),
        RetrievedChunk(content="recursion base case", metadata={}, score=0.3, fused_rank=1),
    ]

    reranked = await reranker.rerank("recursion base case", chunks)

    assert reranked[0].reranked_rank == 1
    assert reranked[0].content == "recursion base case"
