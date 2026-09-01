from abc import ABC, abstractmethod
from typing import List, Optional

from rag.models import TokenUsage


class BaseLLMClient(ABC):
    """Provider-agnostic async chat client used by all RAG pipelines."""

    @abstractmethod
    async def chat_complete(
        self,
        messages: List[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 350,
    ) -> tuple[str, Optional[TokenUsage]]:
        raise NotImplementedError
