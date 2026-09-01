import pytest
from unittest.mock import AsyncMock, MagicMock

from rag.naive_pipeline import NaiveRAGPipeline, NO_SOURCE_ANSWER
from rag.models import RAGResult, TokenUsage


@pytest.mark.asyncio
async def test_strict_rag_with_context(mock_settings, mock_rag_processor, mock_llm_client, sample_context_docs):
    pipeline = NaiveRAGPipeline(
        rag_processor=mock_rag_processor,
        llm_client=mock_llm_client,
    )

    result = await pipeline.run("What is photosynthesis?")

    assert isinstance(result, RAGResult)
    assert result.pipeline_name == "naive_rag"
    assert result.mode == "strict_rag"
    assert result.num_chunks_retrieved == 2
    assert len(result.retrieved_chunks) == 2
    assert result.retrieved_chunks[0].content == sample_context_docs[0]["content"]
    assert result.retrieved_chunks[0].score == 0.85
    assert len(result.citations) == 1
    assert result.citations[0].source == "Biology Basics"
    assert "photosynthesis" in result.answer.lower()
    assert result.retrieval_time_ms >= 0
    assert result.generation_time_ms >= 0
    assert result.total_time_ms >= 0
    assert result.token_usage is not None
    assert result.token_usage.total_tokens == 150

    mock_rag_processor.find_relevant_context.assert_awaited_once_with(
        "What is photosynthesis?",
        num_chunks=3,
        min_score=0.2,
        source_ids=None,
    )
    mock_llm_client.chat_complete.assert_awaited_once()


@pytest.mark.asyncio
async def test_strict_no_match_without_fallback(mock_settings, mock_llm_client):
    processor = MagicMock()
    processor.find_relevant_context = AsyncMock(return_value=[])

    pipeline = NaiveRAGPipeline(
        rag_processor=processor,
        llm_client=mock_llm_client,
    )

    result = await pipeline.run("Unknown topic?", allow_fallback=False)

    assert result.mode == "strict_no_match"
    assert result.answer == NO_SOURCE_ANSWER
    assert result.num_chunks_retrieved == 0
    assert result.retrieved_chunks == []
    assert result.citations == []
    assert result.generation_time_ms == 0.0
    mock_llm_client.chat_complete.assert_not_awaited()


@pytest.mark.asyncio
async def test_hybrid_fallback_when_no_context(mock_settings, mock_llm_client):
    processor = MagicMock()
    processor.find_relevant_context = AsyncMock(return_value=[])

    mock_llm_client.chat_complete = AsyncMock(
        return_value=(
            "The sky is blue due to Rayleigh scattering.",
            TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
        )
    )

    pipeline = NaiveRAGPipeline(
        rag_processor=processor,
        llm_client=mock_llm_client,
    )

    result = await pipeline.run("Why is the sky blue?", allow_fallback=True)

    assert result.mode == "hybrid_fallback"
    assert result.answer.startswith("External knowledge fallback:")
    assert result.num_chunks_retrieved == 0
    assert len(result.citations) == 1
    assert result.citations[0].source == "External GPT fallback"
    assert result.token_usage.total_tokens == 70
    mock_llm_client.chat_complete.assert_awaited_once()


@pytest.mark.asyncio
async def test_error_handling_returns_error_mode(mock_settings, mock_llm_client):
    processor = MagicMock()
    processor.find_relevant_context = AsyncMock(side_effect=RuntimeError("ChromaDB unavailable"))

    pipeline = NaiveRAGPipeline(
        rag_processor=processor,
        llm_client=mock_llm_client,
    )

    result = await pipeline.run("Any question?")

    assert result.mode == "error"
    assert "error" in result.answer.lower()
    assert result.num_chunks_retrieved == 0


@pytest.mark.asyncio
async def test_result_model_fields_complete(mock_settings, mock_rag_processor, mock_llm_client):
    pipeline = NaiveRAGPipeline(
        rag_processor=mock_rag_processor,
        llm_client=mock_llm_client,
    )

    result = await pipeline.run("Tell me about chlorophyll")

    assert hasattr(result, "pipeline_name")
    assert hasattr(result, "answer")
    assert hasattr(result, "citations")
    assert hasattr(result, "retrieved_chunks")
    assert hasattr(result, "retrieval_time_ms")
    assert hasattr(result, "generation_time_ms")
    assert hasattr(result, "total_time_ms")
    assert hasattr(result, "token_usage")
    assert hasattr(result, "num_chunks_retrieved")
    assert hasattr(result, "mode")
    assert result.total_time_ms >= result.retrieval_time_ms


@pytest.mark.asyncio
async def test_citations_deduplicate_same_source(mock_settings, mock_llm_client):
    docs = [
        {
            "content": "Chunk A",
            "metadata": {"source": "lecture_1", "title": "Same Source"},
            "score": 0.9,
        },
        {
            "content": "Chunk B",
            "metadata": {"source": "lecture_1", "title": "Same Source"},
            "score": 0.8,
        },
    ]
    processor = MagicMock()
    processor.find_relevant_context = AsyncMock(return_value=docs)

    pipeline = NaiveRAGPipeline(
        rag_processor=processor,
        llm_client=mock_llm_client,
    )

    result = await pipeline.run("Question?")

    assert len(result.citations) == 1
    assert result.citations[0].source == "Same Source"


@pytest.mark.asyncio
async def test_token_usage_none_when_not_returned(mock_settings, mock_rag_processor):
    client = MagicMock()
    client.chat_complete = AsyncMock(return_value=("An answer.", None))

    pipeline = NaiveRAGPipeline(
        rag_processor=mock_rag_processor,
        llm_client=client,
    )

    result = await pipeline.run("Question?")

    assert result.token_usage is None


def test_init_raises_without_api_key(monkeypatch):
    def _empty_key(_provider):
        return ""

    monkeypatch.setattr("rag.naive_pipeline.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("rag.providers.factory.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("rag.providers.factory.settings.get_provider_api_key", _empty_key)

    with pytest.raises(ValueError, match="API key"):
        NaiveRAGPipeline()
