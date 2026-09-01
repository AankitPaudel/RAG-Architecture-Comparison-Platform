import json
import logging
import re
from typing import List

from rag.bm25 import tokenize
from rag.models import RetrievedChunk
from rag.providers.base import BaseLLMClient

logger = logging.getLogger(__name__)

SUFFICIENT_THRESHOLD = 0.55


class EvidenceGrader:
    def __init__(self, client: BaseLLMClient, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model

    async def grade(self, question: str, chunks: List[RetrievedChunk]) -> float:
        if not chunks:
            return 0.0

        heuristic_score = self._heuristic_grade(question, chunks)
        if heuristic_score >= SUFFICIENT_THRESHOLD:
            return heuristic_score
        if heuristic_score <= 0.2:
            return heuristic_score

        try:
            context = "\n\n".join(
                f"Chunk {index + 1}: {chunk.content}"
                for index, chunk in enumerate(chunks)
            )
            content, _ = await self.client.chat_complete(
                [
                    {
                        "role": "system",
                        "content": (
                            "You grade whether retrieved evidence is sufficient to answer a question. "
                            "Return only JSON: {\"confidence\": <number between 0 and 1>}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nEvidence:\n{context}",
                    },
                ],
                temperature=0.0,
                max_tokens=50,
            )
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                payload = json.loads(match.group())
                llm_score = float(payload.get("confidence", heuristic_score))
                return round(max(0.0, min(llm_score, 1.0)), 3)
        except Exception as error:
            logger.warning("Evidence grader LLM fallback: %s", error)

        return heuristic_score

    def _heuristic_grade(self, question: str, chunks: List[RetrievedChunk]) -> float:
        query_terms = set(tokenize(question))
        if not query_terms:
            return 0.0

        overlap_scores = []
        retrieval_scores = []
        for chunk in chunks:
            chunk_terms = set(tokenize(chunk.content))
            overlap = len(query_terms.intersection(chunk_terms))
            overlap_scores.append(overlap / max(len(query_terms), 1))
            if chunk.score is not None:
                retrieval_scores.append(min(float(chunk.score), 1.0))

        overlap_avg = sum(overlap_scores) / len(overlap_scores)
        retrieval_avg = sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0.0
        coverage_bonus = min(len(chunks) / 3, 1.0) * 0.1
        return round(min((overlap_avg * 0.55) + (retrieval_avg * 0.35) + coverage_bonus, 1.0), 3)


class QueryRewriter:
    def __init__(self, client: BaseLLMClient, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model

    async def rewrite(
        self,
        original_question: str,
        current_query: str,
        chunks: List[RetrievedChunk],
        attempt: int,
    ) -> str:
        try:
            evidence_preview = "\n".join(
                f"- {chunk.content[:180]}"
                for chunk in chunks[:3]
            ) or "No useful evidence retrieved."
            rewritten, _ = await self.client.chat_complete(
                [
                    {
                        "role": "system",
                        "content": (
                            "Rewrite only the retrieval query to improve source retrieval. "
                            "Do not answer the question. Return only the rewritten query text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Original user question (must not change): {original_question}\n"
                            f"Current retrieval query: {current_query}\n"
                            f"Attempt: {attempt}\n"
                            f"Evidence preview:\n{evidence_preview}\n\n"
                            "Provide a better retrieval query."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=80,
            )
            rewritten = rewritten.strip().strip('"')
            if rewritten and rewritten.lower() != current_query.lower():
                return rewritten
        except Exception as error:
            logger.warning("Query rewriter fallback: %s", error)

        return self._fallback_rewrite(original_question, current_query, attempt)

    def _fallback_rewrite(self, original_question: str, current_query: str, attempt: int) -> str:
        keywords = tokenize(original_question)
        if attempt == 1:
            return " ".join(keywords[:8]) or current_query
        if attempt == 2:
            return f"{original_question} key concepts definitions examples"
        return original_question
