from typing import List, Optional

from openai import AsyncOpenAI

from rag.models import TokenUsage
from rag.providers.base import BaseLLMClient


class OpenAILLMClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = model

    async def chat_complete(
        self,
        messages: List[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 350,
    ) -> tuple[str, Optional[TokenUsage]]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        answer = (response.choices[0].message.content or "").strip()
        token_usage = None
        if response.usage:
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return answer, token_usage
