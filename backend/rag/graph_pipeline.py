import logging
import time
from typing import List, Optional

from app.config import settings
from rag.generation import NO_SOURCE_ANSWER, RAGGenerator, build_citations, format_context
from rag.graph_extractor import extract_entities_from_question
from rag.graph_store import GraphStore
from rag.models import GraphNode, GraphPath, GraphRelationship, RAGResult, RetrievedChunk
from rag.processor import RAGProcessor, parse_source_ids
from rag.providers import get_llm_client, validate_provider_config
from rag.providers.base import BaseLLMClient

logger = logging.getLogger(__name__)

PIPELINE_NAME = "graph_rag"


class GraphRAGPipeline:
    def __init__(
        self,
        rag_processor: Optional[RAGProcessor] = None,
        graph_store: Optional[GraphStore] = None,
        llm_client: Optional[BaseLLMClient] = None,
        openai_client: Optional[BaseLLMClient] = None,
        model: Optional[str] = None,
        max_hops: int = 2,
        final_top_k: int = 3,
    ):
        validate_provider_config()
        self.rag_processor = rag_processor or RAGProcessor()
        self.graph_store = graph_store or GraphStore()
        self.client = llm_client or openai_client or get_llm_client(model=model)
        self.model = model or settings.get_chat_model(settings.LLM_PROVIDER)
        self.generator = RAGGenerator(self.client, model=self.model)
        self.max_hops = max_hops
        self.final_top_k = final_top_k

    def index_lecture_chunks(self, lecture_id: int, chunks: List[str]) -> None:
        from rag.graph_extractor import extract_from_chunk

        for chunk_id, content in enumerate(chunks):
            entities, relationships = extract_from_chunk(content, lecture_id, chunk_id)
            for entity in entities:
                self.graph_store.add_entity(
                    entity["name"],
                    entity["entity_type"],
                    lecture_id,
                    chunk_id,
                )
            for relationship in relationships:
                self.graph_store.add_relationship(
                    relationship["source"],
                    relationship["relation"],
                    relationship["target"],
                    lecture_id,
                    chunk_id,
                )
        self.graph_store.save()

    def delete_lecture(self, lecture_id: int) -> None:
        self.graph_store.delete_lecture(lecture_id)

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
            matched_entities = extract_entities_from_question(question)
            matched_nodes = self.graph_store.find_matching_nodes(
                matched_entities,
                source_ids=parsed_source_ids,
            )
            node_ids = [node["id"] for node in matched_nodes]
            graph_nodes, relationships, graph_paths, hop_count = self.graph_store.traverse(
                node_ids,
                max_hops=self.max_hops,
                source_ids=parsed_source_ids,
            )

            chunk_keys = self.graph_store.get_chunk_ids_for_subgraph(graph_nodes, relationships)
            all_chunks = self.rag_processor.get_all_chunks(source_ids=parsed_source_ids)
            chunk_lookup = {
                f"{chunk['metadata'].get('lecture_id')}:{chunk['metadata'].get('chunk_id')}": chunk
                for chunk in all_chunks
            }

            retrieved_docs = []
            for chunk_key in chunk_keys:
                chunk = chunk_lookup.get(chunk_key)
                if chunk:
                    retrieved_docs.append(chunk)

            if not retrieved_docs and matched_nodes:
                for node in matched_nodes:
                    for chunk_key in node.get("chunk_ids", []):
                        chunk = chunk_lookup.get(chunk_key)
                        if chunk:
                            retrieved_docs.append(chunk)

            retrieved_docs = retrieved_docs[:self.final_top_k]
            retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

            retrieved_chunks = [
                RetrievedChunk(
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                )
                for doc in retrieved_docs
            ]

            if not retrieved_docs:
                if not allow_fallback:
                    return self._build_result(
                        answer=NO_SOURCE_ANSWER,
                        retrieved_chunks=[],
                        retrieval_time_ms=retrieval_time_ms,
                        generation_time_ms=0.0,
                        total_start=total_start,
                        mode="strict_no_match",
                        matched_entities=matched_entities,
                        graph_nodes=graph_nodes,
                        relationships=relationships,
                        graph_paths=graph_paths,
                        hop_count=hop_count,
                    )
                generation_start = time.perf_counter()
                answer, token_usage = await self.generator.generate_fallback_answer(question)
                generation_time_ms = (time.perf_counter() - generation_start) * 1000
                return self._build_result(
                    answer=answer,
                    retrieved_chunks=[],
                    retrieval_time_ms=retrieval_time_ms,
                    generation_time_ms=generation_time_ms,
                    total_start=total_start,
                    mode="hybrid_fallback",
                    token_usage=token_usage,
                    matched_entities=matched_entities,
                    graph_nodes=graph_nodes,
                    relationships=relationships,
                    graph_paths=graph_paths,
                    hop_count=hop_count,
                )

            generation_start = time.perf_counter()
            answer, token_usage = await self.generator.generate_grounded_answer(
                question,
                format_context(retrieved_docs),
            )
            generation_time_ms = (time.perf_counter() - generation_start) * 1000

            return self._build_result(
                answer=answer,
                retrieved_chunks=retrieved_chunks,
                citations=build_citations(retrieved_docs),
                retrieval_time_ms=retrieval_time_ms,
                generation_time_ms=generation_time_ms,
                total_start=total_start,
                token_usage=token_usage,
                mode="strict_rag",
                matched_entities=matched_entities,
                graph_nodes=graph_nodes,
                relationships=relationships,
                graph_paths=graph_paths,
                hop_count=hop_count,
                chunks_considered=len(chunk_keys),
                chunks_sent_to_llm=len(retrieved_docs),
            )
        except Exception as error:
            logger.error("Error in GraphRAGPipeline.run: %s", error, exc_info=True)
            return self._build_result(
                answer="I encountered an error while processing your question. Please try again.",
                retrieved_chunks=[],
                retrieval_time_ms=0.0,
                generation_time_ms=0.0,
                total_start=total_start,
                mode="error",
                error=str(error),
            )

    def _build_result(
        self,
        answer: str,
        retrieved_chunks: list,
        retrieval_time_ms: float,
        generation_time_ms: float,
        total_start: float,
        mode: str,
        citations=None,
        token_usage=None,
        matched_entities=None,
        graph_nodes=None,
        relationships=None,
        graph_paths=None,
        hop_count: int = 0,
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
            matched_entities=matched_entities or [],
            graph_nodes=[GraphNode(**node) for node in (graph_nodes or [])],
            relationships=[GraphRelationship(**rel) for rel in (relationships or [])],
            graph_paths=[GraphPath(nodes=path) for path in (graph_paths or [])],
            hop_count=hop_count,
            error=error,
        )
