import pytest
from unittest.mock import AsyncMock, MagicMock

from rag.agentic_components import EvidenceGrader, QueryRewriter, SUFFICIENT_THRESHOLD
from rag.agentic_pipeline import AgenticRAGPipeline, MAX_RETRIEVAL_ATTEMPTS
from rag.models import RetrievedChunk


@pytest.fixture
def sample_chunks():
    return [
        RetrievedChunk(
            content="Recursion is when a function calls itself with a smaller input.",
            metadata={"lecture_id": 1, "chunk_id": 0, "title": "Algorithms"},
            score=0.82,
            fused_rank=1,
            reranked_rank=1,
        )
    ]


@pytest.fixture
def mock_hybrid_pipeline(sample_chunks):
    hybrid = MagicMock()
    hybrid.retrieve = AsyncMock(return_value=(sample_chunks, 12.0, 3.0, 4))
    return hybrid


@pytest.mark.asyncio
async def test_evidence_grader_returns_high_score_for_relevant_chunks(mock_openai_client, sample_chunks):
    grader = EvidenceGrader(mock_openai_client)
    score = await grader.grade("What is recursion?", sample_chunks)
    assert score >= SUFFICIENT_THRESHOLD


@pytest.mark.asyncio
async def test_evidence_grader_returns_zero_for_empty_chunks(mock_openai_client):
    grader = EvidenceGrader(mock_openai_client)
    score = await grader.grade("What is recursion?", [])
    assert score == 0.0


@pytest.mark.asyncio
async def test_query_rewriter_fallback(mock_llm_client, sample_chunks):
    rewriter = QueryRewriter(mock_llm_client)
    mock_llm_client.chat_complete = AsyncMock(side_effect=RuntimeError("offline"))

    rewritten = await rewriter.rewrite(
        original_question="Explain recursion",
        current_query="Explain recursion",
        chunks=sample_chunks,
        attempt=1,
    )

    assert rewritten
    assert rewritten != ""


@pytest.mark.asyncio
async def test_agentic_pipeline_answers_when_evidence_sufficient(
    mock_settings,
    mock_openai_client,
    mock_hybrid_pipeline,
    sample_chunks,
):
    pipeline = AgenticRAGPipeline(
        rag_processor=MagicMock(),
        openai_client=mock_openai_client,
        hybrid_pipeline=mock_hybrid_pipeline,
    )

    result = await pipeline.run("Explain recursion")

    assert result.pipeline_name == "agentic_rag"
    assert result.mode == "strict_rag"
    assert result.execution_trace is not None
    assert len(result.execution_trace) == 1
    assert result.execution_trace[0].decision == "answer"
    assert result.execution_trace[0].query == "Explain recursion"


@pytest.mark.asyncio
async def test_agentic_pipeline_retries_and_rewrites_query(
    mock_settings,
    mock_openai_client,
    sample_chunks,
):
    hybrid = MagicMock()
    hybrid.retrieve = AsyncMock(return_value=(sample_chunks, 10.0, 2.0, 3))

    grader = MagicMock()
    grader.grade = AsyncMock(side_effect=[0.2, 0.8])

    rewriter = MagicMock()
    rewriter.rewrite = AsyncMock(return_value="recursion base case definition")

    pipeline = AgenticRAGPipeline(
        rag_processor=MagicMock(),
        openai_client=mock_openai_client,
        hybrid_pipeline=hybrid,
    )
    pipeline.evidence_grader = grader
    pipeline.query_rewriter = rewriter

    result = await pipeline.run("Explain recursion")

    assert len(result.execution_trace) == 2
    assert result.execution_trace[0].decision == "rewrite_query"
    assert result.execution_trace[0].rewritten_query == "recursion base case definition"
    assert result.execution_trace[1].decision == "answer"
    assert result.execution_trace[1].query == "recursion base case definition"


@pytest.mark.asyncio
async def test_agentic_pipeline_max_retries_returns_grounded_message(
    mock_settings,
    mock_openai_client,
    sample_chunks,
):
    hybrid = MagicMock()
    hybrid.retrieve = AsyncMock(return_value=(sample_chunks, 8.0, 2.0, 2))

    grader = MagicMock()
    grader.grade = AsyncMock(return_value=0.1)

    rewriter = MagicMock()
    rewriter.rewrite = AsyncMock(side_effect=[
        "recursion definition",
        "recursive function examples",
    ])

    pipeline = AgenticRAGPipeline(
        rag_processor=MagicMock(),
        openai_client=mock_openai_client,
        hybrid_pipeline=hybrid,
    )
    pipeline.evidence_grader = grader
    pipeline.query_rewriter = rewriter

    result = await pipeline.run("Explain quantum chromodynamics in the sources")

    assert len(result.execution_trace) == MAX_RETRIEVAL_ATTEMPTS
    assert result.mode == "strict_no_match"
    assert "not enough information" in result.answer.lower()
    assert result.chunks_sent_to_llm == 0
