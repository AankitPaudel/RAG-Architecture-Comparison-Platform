import logging
from typing import Dict, Optional

from rag.agentic_pipeline import AgenticRAGPipeline
from rag.graph_pipeline import GraphRAGPipeline
from rag.graph_store import GraphStore
from rag.hybrid_pipeline import HybridRAGPipeline
from rag.naive_pipeline import NaiveRAGPipeline
from rag.processor import RAGProcessor

logger = logging.getLogger(__name__)

PIPELINE_REGISTRY: Dict[str, str] = {
    "naive": "naive_rag",
    "hybrid": "hybrid_rag",
    "agentic": "agentic_rag",
    "graph": "graph_rag",
}


class PipelineService:
    def __init__(self):
        self._rag_processor: Optional[RAGProcessor] = None
        self._graph_store: Optional[GraphStore] = None
        self._naive: Optional[NaiveRAGPipeline] = None
        self._hybrid: Optional[HybridRAGPipeline] = None
        self._agentic: Optional[AgenticRAGPipeline] = None
        self._graph: Optional[GraphRAGPipeline] = None

    @property
    def rag_processor(self) -> RAGProcessor:
        if self._rag_processor is None:
            self._rag_processor = RAGProcessor()
        return self._rag_processor

    @property
    def graph_store(self) -> GraphStore:
        if self._graph_store is None:
            self._graph_store = GraphStore()
        return self._graph_store

    @property
    def naive(self) -> NaiveRAGPipeline:
        if self._naive is None:
            self._naive = NaiveRAGPipeline(rag_processor=self.rag_processor)
        return self._naive

    @property
    def hybrid(self) -> HybridRAGPipeline:
        if self._hybrid is None:
            self._hybrid = HybridRAGPipeline(rag_processor=self.rag_processor)
        return self._hybrid

    @property
    def agentic(self) -> AgenticRAGPipeline:
        if self._agentic is None:
            self._agentic = AgenticRAGPipeline(
                rag_processor=self.rag_processor,
                hybrid_pipeline=self.hybrid,
            )
        return self._agentic

    @property
    def graph(self) -> GraphRAGPipeline:
        if self._graph is None:
            self._graph = GraphRAGPipeline(
                rag_processor=self.rag_processor,
                graph_store=self.graph_store,
            )
        return self._graph

    def get_pipeline(self, name: str):
        mapping = {
            "naive": self.naive,
            "hybrid": self.hybrid,
            "agentic": self.agentic,
            "graph": self.graph,
        }
        if name not in mapping:
            raise ValueError(f"Unknown pipeline: {name}")
        return mapping[name]

    def index_lecture(self, lecture_id: int, content: str, title: str = None) -> None:
        self.rag_processor.process_lecture(lecture_id, content, title=title)
        chunks = self.rag_processor.text_splitter.split_text(content)
        self.graph.index_lecture_chunks(lecture_id, chunks)

    def delete_lecture(self, lecture_id: int) -> None:
        self.rag_processor.delete_lecture(lecture_id)
        self.graph.delete_lecture(lecture_id)


_pipeline_service: Optional[PipelineService] = None


def get_pipeline_service() -> PipelineService:
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service
