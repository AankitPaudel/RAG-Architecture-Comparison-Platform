from abc import ABC, abstractmethod
from typing import List

from rag.bm25 import tokenize
from rag.models import RetrievedChunk


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(self, query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        raise NotImplementedError


class CompositeReranker(BaseReranker):
    """Lightweight reranker combining fused score with query-term overlap."""

    async def rerank(self, query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        if not chunks:
            return []

        query_terms = set(tokenize(query))
        scored_chunks = []

        for chunk in chunks:
            chunk_terms = set(tokenize(chunk.content))
            overlap = len(query_terms.intersection(chunk_terms))
            overlap_score = overlap / max(len(query_terms), 1)
            base_score = chunk.score or 0.0
            composite_score = (base_score * 0.7) + (overlap_score * 0.3)
            scored_chunks.append((composite_score, chunk))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)

        reranked = []
        for rank, (score, chunk) in enumerate(scored_chunks, start=1):
            reranked.append(chunk.model_copy(update={
                "score": round(score, 4),
                "reranked_rank": rank,
            }))
        return reranked
