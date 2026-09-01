import logging
import os
import re
import uuid
from typing import List, Optional

import chromadb

from app.config import settings
from rag.providers import get_embedding_function, validate_provider_config

logger = logging.getLogger(__name__)


class SimpleTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str):
        clean_text = re.sub(r"\s+", " ", text or "").strip()
        if not clean_text:
            return []

        chunks = []
        start = 0
        while start < len(clean_text):
            end = min(start + self.chunk_size, len(clean_text))
            chunks.append(clean_text[start:end])
            if end == len(clean_text):
                break
            start = max(end - self.chunk_overlap, start + 1)
        return chunks


def parse_source_ids(source_ids: Optional[List[str]]) -> Optional[List[int]]:
    if not source_ids:
        return None

    parsed = []
    for source_id in source_ids:
        value = str(source_id).strip()
        if value.startswith("source-"):
            value = value.replace("source-", "", 1)
        if value.startswith("lecture_"):
            value = value.replace("lecture_", "", 1)
        try:
            parsed.append(int(value))
        except ValueError:
            logger.warning("Skipping invalid source id: %s", source_id)
    return parsed or None


class RAGProcessor:
    def __init__(self):
        logger.info("Initializing RAG Processor...")
        validate_provider_config(settings.get_embedding_provider())

        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
        self.text_splitter = SimpleTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.client = chromadb.PersistentClient(path=settings.VECTOR_STORE_PATH)
        self.embedding_function = get_embedding_function()
        collection_name = f"knowledge_sources_{settings.get_embedding_provider()}"
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        logger.info("RAG Processor initialized successfully")

    def process_lecture(self, lecture_id: int, content: str, title: str = None) -> None:
        chunks = self.text_splitter.split_text(content)
        if not chunks:
            return

        ids = [f"lecture_{lecture_id}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
        metadatas = [{
            "lecture_id": lecture_id,
            "chunk_id": i,
            "source": f"lecture_{lecture_id}",
            "title": title or f"Source {lecture_id}"
        } for i in range(len(chunks))]

        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        logger.info(f"Successfully processed source {lecture_id} with {len(chunks)} chunks")

    def get_all_chunks(self, source_ids: Optional[List[int]] = None) -> List[dict]:
        if self.collection.count() == 0:
            return []

        where = None
        if source_ids:
            if len(source_ids) == 1:
                where = {"lecture_id": source_ids[0]}
            else:
                where = {"lecture_id": {"$in": source_ids}}

        results = self.collection.get(
            where=where,
            include=["documents", "metadatas"],
        )

        documents = results.get("documents", []) or []
        metadatas = results.get("metadatas", []) or []
        chunks = []
        for doc, metadata in zip(documents, metadatas):
            chunks.append({
                "content": doc,
                "metadata": metadata or {},
            })
        return chunks

    def keyword_search(self, question: str, lectures: list, num_chunks: int = 3):
        query_terms = self._tokenize(question)
        if not query_terms:
            return []

        scored_chunks = []
        for lecture in lectures:
            chunks = self.text_splitter.split_text(lecture.content)
            for chunk_id, chunk in enumerate(chunks):
                overlap = query_terms.intersection(self._tokenize(chunk))
                if not overlap:
                    continue

                score = len(overlap) / max(len(query_terms), 1)
                scored_chunks.append({
                    "content": chunk,
                    "metadata": {
                        "lecture_id": lecture.id,
                        "chunk_id": chunk_id,
                        "source": f"lecture_{lecture.id}",
                        "title": lecture.title,
                        "matched_terms": sorted(overlap)
                    },
                    "score": round(score, 3)
                })

        scored_chunks.sort(key=lambda item: item["score"], reverse=True)
        return scored_chunks[:num_chunks]

    async def find_relevant_context(
        self,
        question: str,
        num_chunks: int = 3,
        min_score: float = 0.2,
        source_ids: Optional[List[int]] = None,
    ):
        if self.collection.count() == 0:
            logger.warning("Vector store is empty - no sources loaded")
            return []

        where = None
        if source_ids:
            if len(source_ids) == 1:
                where = {"lecture_id": source_ids[0]}
            else:
                where = {"lecture_id": {"$in": source_ids}}

        results = self.collection.query(
            query_texts=[question],
            n_results=num_chunks,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        context_docs = []
        for rank, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances), start=1):
            score = max(0.0, 1.0 - float(distance)) if distance is not None else None
            if score is not None and score < min_score:
                continue
            context_docs.append({
                "content": doc,
                "metadata": metadata or {},
                "score": round(score, 3) if score is not None else None,
                "dense_rank": rank,
            })

        logger.info(f"Found {len(context_docs)} relevant chunks for question")
        return context_docs

    def delete_lecture(self, lecture_id: int) -> None:
        try:
            self.collection.delete(where={"lecture_id": lecture_id})
        except Exception as e:
            logger.warning(f"Could not delete source {lecture_id} from vector store: {e}")

    def _tokenize(self, text: str):
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
            "this", "to", "what", "when", "where", "which", "who", "why",
            "with", "you", "your"
        }
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return {word for word in words if len(word) > 2 and word not in stop_words}
