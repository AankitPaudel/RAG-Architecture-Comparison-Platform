from typing import Optional

from rag.models import TokenUsage
from rag.providers.base import BaseLLMClient

STRICT_RAG_SYSTEM_PROMPT = (
    "You are a controlled RAG teaching assistant. Answer only from the provided context. "
    "Do not use outside knowledge. If the context does not contain the answer, say: "
    "'No relevant information was found in the provided sources.'"
)
FALLBACK_SYSTEM_PROMPT = (
    "You are a helpful teaching assistant. The indexed knowledge base did not contain "
    "relevant information. Answer from general knowledge and clearly label the answer "
    "as external knowledge, not source-grounded."
)
NO_SOURCE_ANSWER = "No relevant information was found in the provided sources."


class RAGGenerator:
    def __init__(self, client: BaseLLMClient, model: Optional[str] = None):
        self.client = client
        self.model = model

    async def generate_grounded_answer(self, question: str, context: str) -> tuple[str, Optional[TokenUsage]]:
        messages = [
            {"role": "system", "content": STRICT_RAG_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        return await self._chat(messages)

    async def generate_fallback_answer(self, question: str) -> tuple[str, Optional[TokenUsage]]:
        answer, token_usage = await self._chat([
            {"role": "system", "content": FALLBACK_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ])
        if not answer.lower().startswith("external knowledge"):
            answer = f"External knowledge fallback: {answer}"
        return answer, token_usage

    async def chat(self, messages: list) -> tuple[str, Optional[TokenUsage]]:
        return await self._chat(messages)

    async def _chat(self, messages: list) -> tuple[str, Optional[TokenUsage]]:
        return await self.client.chat_complete(
            messages,
            temperature=0.2,
            max_tokens=350,
        )


def format_context(context_docs: list) -> str:
    return "\n\n".join(
        (
            f"Source: {doc['metadata'].get('title') or doc['metadata'].get('source', 'unknown')}\n"
            f"{doc['content']}"
        )
        for doc in context_docs
    )


def build_citations(context_docs: list):
    from rag.models import Citation

    citations = []
    seen = set()
    for doc in context_docs:
        metadata = doc.get("metadata", {})
        source = metadata.get("title") or metadata.get("source", "unknown")
        if source in seen:
            continue
        seen.add(source)
        citations.append(Citation(source=source, title=metadata.get("title")))
    return citations
