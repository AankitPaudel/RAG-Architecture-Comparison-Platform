import logging
import time
from typing import List, Optional

from app.config import settings
from rag.generation import (
    NO_SOURCE_ANSWER,
    RAGGenerator,
    build_citations,
    format_context,
)
from rag.models import Citation, RAGResult, RetrievedChunk
from rag.processor import RAGProcessor, parse_source_ids
from rag.providers import get_llm_client, validate_provider_config
from rag.providers.base import BaseLLMClient

logger = logging.getLogger(__name__)

PIPELINE_NAME = "naive_rag"


class NaiveRAGPipeline:
    def __init__(
        self,
        rag_processor: Optional[RAGProcessor] = None,
        llm_client: Optional[BaseLLMClient] = None,
        openai_client: Optional[BaseLLMClient] = None,
        model: Optional[str] = None,
        num_chunks: int = 3,
        min_score: float = 0.2,
    ):
        validate_provider_config()
        self.rag_processor = rag_processor or RAGProcessor()
        self.client = llm_client or openai_client or get_llm_client(model=model)
        self.model = model or settings.get_chat_model(settings.LLM_PROVIDER)
        self.generator = RAGGenerator(self.client, model=self.model)
        self.num_chunks = num_chunks
        self.min_score = min_score

    async def run(
        self,
        question: str,
        allow_fallback: bool = False,
        source_ids: Optional[List[str]] = None,
    ) -> RAGResult:
        total_start = time.perf_counter()
        parsed_source_ids = parse_source_ids(source_ids)

        try:
            retrieval_start = time.perf_counter()
            context_docs = await self.rag_processor.find_relevant_context(
                question,
                num_chunks=self.num_chunks,
                min_score=self.min_score,
                source_ids=parsed_source_ids,
            )
            retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

            retrieved_chunks = [
                RetrievedChunk(
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    score=doc.get("score"),
                    dense_rank=doc.get("dense_rank"),
                )
                for doc in context_docs
            ]

            if not context_docs:
                if not allow_fallback:
                    return self._build_result(
                        answer=NO_SOURCE_ANSWER,
                        retrieved_chunks=[],
                        retrieval_time_ms=retrieval_time_ms,
                        generation_time_ms=0.0,
                        total_start=total_start,
                        mode="strict_no_match",
                    )
                return await self._run_fallback(
                    question=question,
                    retrieval_time_ms=retrieval_time_ms,
                    total_start=total_start,
                )

            generation_start = time.perf_counter()
            context = format_context(context_docs)
            answer, token_usage = await self.generator.generate_grounded_answer(question, context)
            generation_time_ms = (time.perf_counter() - generation_start) * 1000

            citations = build_citations(context_docs)

            return self._build_result(
                answer=answer,
                retrieved_chunks=retrieved_chunks,
                citations=citations,
                retrieval_time_ms=retrieval_time_ms,
                generation_time_ms=generation_time_ms,
                total_start=total_start,
                token_usage=token_usage,
                mode="strict_rag",
                chunks_considered=len(context_docs),
                chunks_sent_to_llm=len(context_docs),
            )
        except Exception as error:
            logger.error("Error in NaiveRAGPipeline.run: %s", error, exc_info=True)
            return self._build_result(
                answer="I encountered an error while processing your question. Please try again.",
                retrieved_chunks=[],
                retrieval_time_ms=0.0,
                generation_time_ms=0.0,
                total_start=total_start,
                mode="error",
                error=str(error),
            )

    async def _run_fallback(
        self,
        question: str,
        retrieval_time_ms: float,
        total_start: float,
    ) -> RAGResult:
        generation_start = time.perf_counter()
        answer, token_usage = await self.generator.generate_fallback_answer(question)
        generation_time_ms = (time.perf_counter() - generation_start) * 1000

        return self._build_result(
            answer=answer,
            retrieved_chunks=[],
            citations=[Citation(source="External GPT fallback", title="External GPT fallback")],
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            total_start=total_start,
            token_usage=token_usage,
            mode="hybrid_fallback",
        )

    def _build_result(
        self,
        answer: str,
        retrieved_chunks: list[RetrievedChunk],
        retrieval_time_ms: float,
        generation_time_ms: float,
        total_start: float,
        mode: str,
        citations=None,
        token_usage=None,
        chunks_considered: int = 0,
        chunks_sent_to_llm: int = 0,
        error: Optional[str] = None,
    ) -> RAGResult:
        return RAGResult(
            pipeline_name=PIPELINE_NAME,
            answer=answer,
            citations=citations or build_citations(
                [{"metadata": chunk.metadata} for chunk in retrieved_chunks]
            ),
            retrieved_chunks=retrieved_chunks,
            retrieval_time_ms=round(retrieval_time_ms, 2),
            generation_time_ms=round(generation_time_ms, 2),
            total_time_ms=round((time.perf_counter() - total_start) * 1000, 2),
            token_usage=token_usage,
            num_chunks_retrieved=len(retrieved_chunks),
            chunks_considered=chunks_considered or len(retrieved_chunks),
            chunks_sent_to_llm=chunks_sent_to_llm or len(retrieved_chunks),
            mode=mode,
            error=error,
        )
