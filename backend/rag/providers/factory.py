from typing import Optional

from app.config import settings
from rag.providers.base import BaseLLMClient
from rag.providers.gemini_provider import GeminiLLMClient
from rag.providers.openai_provider import OpenAILLMClient

SUPPORTED_PROVIDERS = ("openai", "gemini", "grok", "ollama", "openai_compatible")


def validate_provider_config(provider: Optional[str] = None) -> str:
    provider = (provider or settings.LLM_PROVIDER).lower().strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. "
            f"Use one of: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    api_key = settings.get_provider_api_key(provider)
    if not api_key or api_key.startswith("put_"):
        raise ValueError(
            f"API key for provider '{provider}' is not set. "
            f"Set {settings.get_provider_key_env_name(provider)} in backend/.env"
        )
    return provider


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMClient:
    provider = validate_provider_config(provider)
    api_key = settings.get_provider_api_key(provider)
    model = model or settings.get_chat_model(provider)

    if provider == "gemini":
        return GeminiLLMClient(api_key=api_key, model=model)

    base_url = settings.get_provider_base_url(provider)
    return OpenAILLMClient(api_key=api_key, model=model, base_url=base_url)
