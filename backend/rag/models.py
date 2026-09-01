from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    content: str
    metadata: dict = Field(default_factory=dict)
    score: Optional[float] = None
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    fused_rank: Optional[int] = None
    reranked_rank: Optional[int] = None


class Citation(BaseModel):
    source: str
    title: Optional[str] = None


class TokenUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class AgenticAttempt(BaseModel):
    attempt: int
    query: str
    evidence_confidence: float
    decision: str
    rewritten_query: Optional[str] = None
    chunks_found: int = 0


class GraphNode(BaseModel):
    id: str
    name: str
    entity_type: str = "concept"
    hop: int = 0
    chunk_ids: List[str] = Field(default_factory=list)


class GraphRelationship(BaseModel):
    source: str
    relation: str
    target: str
    chunk_ids: List[str] = Field(default_factory=list)
    hop: int = 0


class GraphPath(BaseModel):
    nodes: List[str] = Field(default_factory=list)


class RAGResult(BaseModel):
    pipeline_name: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    retrieval_time_ms: float = 0.0
    reranking_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    total_time_ms: float = 0.0
    token_usage: Optional[TokenUsage] = None
    num_chunks_retrieved: int = 0
    chunks_considered: int = 0
    chunks_sent_to_llm: int = 0
    mode: str = "strict_rag"
    execution_trace: Optional[List[AgenticAttempt]] = None
    matched_entities: List[str] = Field(default_factory=list)
    graph_nodes: List[GraphNode] = Field(default_factory=list)
    relationships: List[GraphRelationship] = Field(default_factory=list)
    graph_paths: List[GraphPath] = Field(default_factory=list)
    hop_count: int = 0
    error: Optional[str] = None

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_name": self.pipeline_name,
            "answer": self.answer,
            "citations": [citation.model_dump() for citation in self.citations],
            "retrieved_chunks": [chunk.model_dump() for chunk in self.retrieved_chunks],
            "retrieval_time_ms": self.retrieval_time_ms,
            "reranking_time_ms": self.reranking_time_ms,
            "generation_time_ms": self.generation_time_ms,
            "total_time_ms": self.total_time_ms,
            "token_usage": self.token_usage.model_dump() if self.token_usage else None,
            "num_chunks_retrieved": self.num_chunks_retrieved,
            "chunks_considered": self.chunks_considered,
            "chunks_sent_to_llm": self.chunks_sent_to_llm,
            "mode": self.mode,
            "execution_trace": (
                [attempt.model_dump() for attempt in self.execution_trace]
                if self.execution_trace else None
            ),
            "matched_entities": self.matched_entities,
            "graph_nodes": [node.model_dump() for node in self.graph_nodes],
            "relationships": [rel.model_dump() for rel in self.relationships],
            "graph_paths": [path.model_dump() for path in self.graph_paths],
            "hop_count": self.hop_count,
            "error": self.error,
        }
