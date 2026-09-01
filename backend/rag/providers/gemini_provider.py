import asyncio
from typing import List, Optional

import google.generativeai as genai

from rag.models import TokenUsage
from rag.providers.base import BaseLLMClient


def _split_messages(messages: List[dict]) -> tuple[Optional[str], str]:
    system_parts = []
    conversation_parts = []

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            conversation_parts.append(f"Assistant: {content}")
        else:
            conversation_parts.append(f"User: {content}")

    system_instruction = "\n\n".join(system_parts).strip() or None
    user_content = "\n\n".join(conversation_parts).strip()
    return system_instruction, user_content


class GeminiLLMClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.api_key = api_key

    async def chat_complete(
        self,
        messages: List[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 350,
    ) -> tuple[str, Optional[TokenUsage]]:
        system_instruction, user_content = _split_messages(messages)

        def _generate() -> tuple[str, Optional[TokenUsage]]:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
            )
            response = model.generate_content(
                user_content,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            answer = ""
            if response.candidates:
                parts = response.candidates[0].content.parts if response.candidates[0].content else []
                answer = "".join(getattr(part, "text", "") or "" for part in parts).strip()

            token_usage = None
            usage = getattr(response, "usage_metadata", None)
            if usage:
                prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
                total_tokens = getattr(usage, "total_token_count", None)
                if total_tokens is None:
                    total_tokens = prompt_tokens + completion_tokens
                token_usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )
            return answer, token_usage

        return await asyncio.to_thread(_generate)
