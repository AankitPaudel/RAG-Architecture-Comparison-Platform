import logging
import time
from typing import List, Optional

from app.config import settings
from rag.bm25 import BM25Retriever
from rag.fusion import reciprocal_rank_fusion
from rag.generation import NO_SOURCE_ANSWER, RAGGenerator, build_citations, format_context
from rag.models import RAGResult, RetrievedChunk
from rag.processor import RAGProcessor, parse_source_ids
from rag.providers import get_llm_client, validate_provider_config
from rag.providers.base import BaseLLMClient
from rag.reranker import BaseReranker, CompositeReranker

logger = logging.getLogger(__name__)

PIPELINE_NAME = "hybrid_rag"


class HybridRAGPipeline:
    def __init__(
        self,
        rag_processor: Optional[RAGProcessor] = None,
        llm_client: Optional[BaseLLMClient] = None,
        openai_client: Optional[BaseLLMClient] = None,
        reranker: Optional[BaseReranker] = None,
        model: Optional[str] = None,
        retrieval_top_k: int = 10,
        final_top_k: int = 3,
        min_score: float = 0.2,
    ):
        validate_provider_config()
        self.rag_processor = rag_processor or RAGProcessor()
        self.client = llm_client or openai_client or get_llm_client(model=model)
        self.model = model or settings.get_chat_model(settings.LLM_PROVIDER)
        self.generator = RAGGenerator(self.client, model=self.model)
        self.reranker = reranker or CompositeReranker()
        self.bm25 = BM25Retriever()
        self.retrieval_top_k = retrieval_top_k
        self.final_top_k = final_top_k
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
            dense_results = await self.rag_processor.find_relevant_context(
                question,
                num_chunks=self.retrieval_top_k,
                min_score=self.min_score,
                source_ids=parsed_source_ids,
            )

            all_chunks = self.rag_processor.get_all_chunks(source_ids=parsed_source_ids)
            self.bm25.index(all_chunks)
            bm25_results = self.bm25.search(
                question,
                top_k=self.retrieval_top_k,
                source_ids=parsed_source_ids,
            )

            for rank, item in enumerate(bm25_results, start=1):
                item["bm25_rank"] = rank

            fused_results = reciprocal_rank_fusion([dense_results, bm25_results])
            chunks_considered = len(fused_results)
            retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

            fused_chunks = [
                RetrievedChunk(
                    content=item["content"],
                    metadata=item.get("metadata", {}),
                    score=item.get("score"),
                    dense_rank=item.get("metadata", {}).get("dense_rank"),
                    bm25_rank=item.get("metadata", {}).get("bm25_rank"),
                    fused_rank=item.get("fused_rank"),
                )
                for item in fused_results
            ]

            if not fused_chunks:
                if not allow_fallback:
                    return self._build_result(
                        answer=NO_SOURCE_ANSWER,
                        retrieved_chunks=[],
                        retrieval_time_ms=retrieval_time_ms,
                        reranking_time_ms=0.0,
                        generation_time_ms=0.0,
                        total_start=total_start,
                        mode="strict_no_match",
                        chunks_considered=0,
                        chunks_sent_to_llm=0,
                    )
                return await self._run_fallback(
                    question=question,
                    retrieval_time_ms=retrieval_time_ms,
                    total_start=total_start,
                )

            rerank_start = time.perf_counter()
            reranked_chunks = await self.reranker.rerank(question, fused_chunks)
            final_chunks = reranked_chunks[:self.final_top_k]
            reranking_time_ms = (time.perf_counter() - rerank_start) * 1000

            context_docs = [
                {
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                }
                for chunk in final_chunks
            ]

            generation_start = time.perf_counter()
            context = format_context(context_docs)
            answer, token_usage = await self.generator.generate_grounded_answer(question, context)
            generation_time_ms = (time.perf_counter() - generation_start) * 1000

            return self._build_result(
                answer=answer,
                retrieved_chunks=final_chunks,
                citations=build_citations(context_docs),
                retrieval_time_ms=retrieval_time_ms,
                reranking_time_ms=reranking_time_ms,
                generation_time_ms=generation_time_ms,
                total_start=total_start,
                token_usage=token_usage,
                mode="strict_rag",
                chunks_considered=chunks_considered,
                chunks_sent_to_llm=len(final_chunks),
            )
        except Exception as error:
            logger.error("Error in HybridRAGPipeline.run: %s", error, exc_info=True)
            return self._build_result(
                answer="I encountered an error while processing your question. Please try again.",
                retrieved_chunks=[],
                retrieval_time_ms=0.0,
                reranking_time_ms=0.0,
                generation_time_ms=0.0,
                total_start=total_start,
                mode="error",
                error=str(error),
            )

    async def retrieve(
        self,
        question: str,
        source_ids: Optional[List[str]] = None,
    ) -> tuple[list[RetrievedChunk], float, float, int]:
        parsed_source_ids = parse_source_ids(source_ids)
        retrieval_start = time.perf_counter()

        dense_results = await self.rag_processor.find_relevant_context(
            question,
            num_chunks=self.retrieval_top_k,
            min_score=self.min_score,
            source_ids=parsed_source_ids,
        )
        all_chunks = self.rag_processor.get_all_chunks(source_ids=parsed_source_ids)
        self.bm25.index(all_chunks)
        bm25_results = self.bm25.search(
            question,
            top_k=self.retrieval_top_k,
            source_ids=parsed_source_ids,
        )
        for rank, item in enumerate(bm25_results, start=1):
            item["bm25_rank"] = rank

        fused_results = reciprocal_rank_fusion([dense_results, bm25_results])
        retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

        fused_chunks = [
            RetrievedChunk(
                content=item["content"],
                metadata=item.get("metadata", {}),
                score=item.get("score"),
                dense_rank=item.get("metadata", {}).get("dense_rank"),
                bm25_rank=item.get("metadata", {}).get("bm25_rank"),
                fused_rank=item.get("fused_rank"),
            )
            for item in fused_results
        ]

        rerank_start = time.perf_counter()
        reranked_chunks = await self.reranker.rerank(question, fused_chunks)
        reranking_time_ms = (time.perf_counter() - rerank_start) * 1000
        return reranked_chunks[:self.final_top_k], retrieval_time_ms, reranking_time_ms, len(fused_results)

    async def _run_fallback(self, question: str, retrieval_time_ms: float, total_start: float) -> RAGResult:
        generation_start = time.perf_counter()
        answer, token_usage = await self.generator.generate_fallback_answer(question)
        generation_time_ms = (time.perf_counter() - generation_start) * 1000
        return self._build_result(
            answer=answer,
            retrieved_chunks=[],
            citations=[],
            retrieval_time_ms=retrieval_time_ms,
            reranking_time_ms=0.0,
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
        reranking_time_ms: float,
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
            reranking_time_ms=round(reranking_time_ms, 2),
            generation_time_ms=round(generation_time_ms, 2),
            total_time_ms=round((time.perf_counter() - total_start) * 1000, 2),
            token_usage=token_usage,
            num_chunks_retrieved=len(retrieved_chunks),
            chunks_considered=chunks_considered,
            chunks_sent_to_llm=chunks_sent_to_llm,
            mode=mode,
            error=error,
        )
