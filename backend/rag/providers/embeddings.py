import time
from typing import List, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.config import settings


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)

    def name(self) -> str:
        return f"gemini-{self.model_name}"

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []

        embeddings: List[List[float]] = []
        batch_size = 16

        for start in range(0, len(input), batch_size):
            batch = list(input[start:start + batch_size])
            embeddings.extend(self._embed_batch(batch))
            if start + batch_size < len(input):
                time.sleep(1.0)

        return embeddings

    def _embed_batch(self, batch: List[str], retries: int = 4) -> List[List[float]]:
        for attempt in range(retries):
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=batch,
                    task_type="retrieval_document",
                )
                batch_embeddings = result.get("embedding", [])
                if batch_embeddings and isinstance(batch_embeddings[0], (int, float)):
                    return [batch_embeddings]
                return batch_embeddings
            except google_exceptions.ResourceExhausted:
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return []


class OpenAICompatibleEmbeddingFunction(EmbeddingFunction):
    """Embeddings via any OpenAI-compatible endpoint (OpenAI, Grok host, Ollama, etc.)."""

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        kwargs = {"api_key": api_key, "model_name": model_name}
        if base_url:
            kwargs["api_base"] = base_url
        self._embedding_function = OpenAIEmbeddingFunction(**kwargs)
        self.model_name = model_name
        self.base_url = base_url or "openai"

    def name(self) -> str:
        return f"openai-compatible-{self.model_name}-{self.base_url}"

    def __call__(self, input: Documents) -> Embeddings:
        return self._embedding_function(input)


def get_embedding_function() -> EmbeddingFunction:
    provider = settings.get_embedding_provider()
    api_key = settings.get_provider_api_key(provider)
    model = settings.get_embedding_model(provider)

    if provider == "gemini":
        return GeminiEmbeddingFunction(api_key=api_key, model_name=model)

    base_url = settings.get_provider_base_url(provider)
    return OpenAICompatibleEmbeddingFunction(
        api_key=api_key,
        model_name=model,
        base_url=base_url,
    )
