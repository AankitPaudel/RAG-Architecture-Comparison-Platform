import logging
import time
from typing import List, Optional

from app.config import settings
from rag.agentic_components import EvidenceGrader, QueryRewriter, SUFFICIENT_THRESHOLD
from rag.generation import NO_SOURCE_ANSWER, RAGGenerator, build_citations, format_context
from rag.hybrid_pipeline import HybridRAGPipeline
from rag.models import AgenticAttempt, RAGResult
from rag.processor import RAGProcessor
from rag.providers import get_llm_client, validate_provider_config
from rag.providers.base import BaseLLMClient

logger = logging.getLogger(__name__)

PIPELINE_NAME = "agentic_rag"
MAX_RETRIEVAL_ATTEMPTS = 3


class AgenticRAGPipeline:
    def __init__(
        self,
        rag_processor: Optional[RAGProcessor] = None,
        llm_client: Optional[BaseLLMClient] = None,
        openai_client: Optional[BaseLLMClient] = None,
        hybrid_pipeline: Optional[HybridRAGPipeline] = None,
        model: Optional[str] = None,
        max_attempts: int = MAX_RETRIEVAL_ATTEMPTS,
    ):
        validate_provider_config()
        self.rag_processor = rag_processor or RAGProcessor()
        self.client = llm_client or openai_client or get_llm_client(model=model)
        self.model = model or settings.get_chat_model(settings.LLM_PROVIDER)
        self.hybrid_pipeline = hybrid_pipeline or HybridRAGPipeline(
            rag_processor=self.rag_processor,
            llm_client=self.client,
            model=self.model,
        )
        self.generator = RAGGenerator(self.client, model=self.model)
        self.evidence_grader = EvidenceGrader(self.client, model=self.model)
        self.query_rewriter = QueryRewriter(self.client, model=self.model)
        self.max_attempts = max_attempts

    async def run(
        self,
        question: str,
        allow_fallback: bool = False,
        source_ids: Optional[List[str]] = None,
    ) -> RAGResult:
        total_start = time.perf_counter()
        execution_trace: List[AgenticAttempt] = []
        retrieval_time_ms = 0.0
        reranking_time_ms = 0.0
        chunks_considered = 0
        current_query = question
        best_chunks = []

        try:
            for attempt in range(1, self.max_attempts + 1):
                chunks, attempt_retrieval_ms, attempt_rerank_ms, considered = await self.hybrid_pipeline.retrieve(
                    current_query,
                    source_ids=source_ids,
                )
                retrieval_time_ms += attempt_retrieval_ms
                reranking_time_ms += attempt_rerank_ms
                chunks_considered = max(chunks_considered, considered)

                confidence = await self.evidence_grader.grade(question, chunks)
                decision = "answer" if confidence >= SUFFICIENT_THRESHOLD else "rewrite_query"
                rewritten_query = None

                trace_entry = AgenticAttempt(
                    attempt=attempt,
                    query=current_query,
                    evidence_confidence=confidence,
                    decision=decision,
                    chunks_found=len(chunks),
                )

                if decision == "answer":
                    best_chunks = chunks
                    execution_trace.append(trace_entry)
                    break

                if attempt < self.max_attempts:
                    rewritten_query = await self.query_rewriter.rewrite(
                        original_question=question,
                        current_query=current_query,
                        chunks=chunks,
                        attempt=attempt,
                    )
                    trace_entry.rewritten_query = rewritten_query
                    current_query = rewritten_query

                execution_trace.append(trace_entry)
                best_chunks = chunks

            if not best_chunks or execution_trace[-1].decision != "answer":
                answer = (
                    "There is not enough information in the selected sources to answer this question."
                )
                return RAGResult(
                    pipeline_name=PIPELINE_NAME,
                    answer=answer,
                    citations=[],
                    retrieved_chunks=best_chunks,
                    retrieval_time_ms=round(retrieval_time_ms, 2),
                    reranking_time_ms=round(reranking_time_ms, 2),
                    generation_time_ms=0.0,
                    total_time_ms=round((time.perf_counter() - total_start) * 1000, 2),
                    num_chunks_retrieved=len(best_chunks),
                    chunks_considered=chunks_considered,
                    chunks_sent_to_llm=0,
                    mode="strict_no_match",
                    execution_trace=execution_trace,
                )

            context_docs = [
                {"content": chunk.content, "metadata": chunk.metadata}
                for chunk in best_chunks
            ]
            generation_start = time.perf_counter()
            answer, token_usage = await self.generator.generate_grounded_answer(
                question,
                format_context(context_docs),
            )
            generation_time_ms = (time.perf_counter() - generation_start) * 1000

            return RAGResult(
                pipeline_name=PIPELINE_NAME,
                answer=answer,
                citations=build_citations(context_docs),
                retrieved_chunks=best_chunks,
                retrieval_time_ms=round(retrieval_time_ms, 2),
                reranking_time_ms=round(reranking_time_ms, 2),
                generation_time_ms=round(generation_time_ms, 2),
                total_time_ms=round((time.perf_counter() - total_start) * 1000, 2),
                token_usage=token_usage,
                num_chunks_retrieved=len(best_chunks),
                chunks_considered=chunks_considered,
                chunks_sent_to_llm=len(best_chunks),
                mode="strict_rag",
                execution_trace=execution_trace,
            )
        except Exception as error:
            logger.error("Error in AgenticRAGPipeline.run: %s", error, exc_info=True)
            return RAGResult(
                pipeline_name=PIPELINE_NAME,
                answer="I encountered an error while processing your question. Please try again.",
                retrieved_chunks=[],
                retrieval_time_ms=round(retrieval_time_ms, 2),
                reranking_time_ms=round(reranking_time_ms, 2),
                generation_time_ms=0.0,
                total_time_ms=round((time.perf_counter() - total_start) * 1000, 2),
                mode="error",
                execution_trace=execution_trace or None,
                error=str(error),
            )
