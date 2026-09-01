import math
import re
from collections import Counter
from typing import List, Optional


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "what", "when", "where", "which", "who", "why",
    "with", "you", "your",
}


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
    return [word for word in words if len(word) > 2 and word not in STOP_WORDS]


def chunk_key(metadata: dict, content: str) -> str:
    lecture_id = metadata.get("lecture_id", "unknown")
    chunk_id = metadata.get("chunk_id", "unknown")
    return f"{lecture_id}:{chunk_id}:{hash(content)}"


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._corpus_tokens: List[List[str]] = []
        self._chunks: List[dict] = []
        self._doc_freq: Counter = Counter()
        self._avg_doc_len = 0.0

    def index(self, chunks: List[dict]) -> None:
        self._chunks = chunks
        self._corpus_tokens = [tokenize(chunk["content"]) for chunk in chunks]
        self._doc_freq = Counter()
        for tokens in self._corpus_tokens:
            for token in set(tokens):
                self._doc_freq[token] += 1
        lengths = [len(tokens) for tokens in self._corpus_tokens]
        self._avg_doc_len = sum(lengths) / len(lengths) if lengths else 0.0

    def search(
        self,
        query: str,
        top_k: int = 10,
        source_ids: Optional[List[int]] = None,
    ) -> List[dict]:
        if not self._chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        num_docs = len(self._chunks)
        scores = []

        for index, (chunk, doc_tokens) in enumerate(zip(self._chunks, self._corpus_tokens)):
            metadata = chunk.get("metadata", {})
            lecture_id = metadata.get("lecture_id")
            if source_ids is not None and lecture_id not in source_ids:
                continue

            doc_len = len(doc_tokens) or 1
            term_freq = Counter(doc_tokens)
            score = 0.0

            for token in query_tokens:
                if token not in term_freq:
                    continue
                df = self._doc_freq.get(token, 0)
                idf = math.log(1 + (num_docs - df + 0.5) / (df + 0.5))
                tf = term_freq[token]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self._avg_doc_len))
                score += idf * (numerator / denominator)

            if score > 0:
                scores.append({
                    "content": chunk["content"],
                    "metadata": metadata,
                    "score": round(score, 4),
                    "_index": index,
                })

        scores.sort(key=lambda item: item["score"], reverse=True)
        return scores[:top_k]
