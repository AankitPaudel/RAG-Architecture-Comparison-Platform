# File: backend/app/config.py
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from pathlib import Path

# .env values override any existing shell environment variables.
load_dotenv(override=True)


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent

    # Provider selection: openai | gemini | grok | ollama | openai_compatible
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "")

    # Provider API keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    # Optional model overrides
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "")

    # OpenAI-compatible endpoints (Grok, Ollama, Together, etc.)
    GROK_BASE_URL: str = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OPENAI_COMPATIBLE_BASE_URL: str = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rag_platform.db")
    VECTOR_STORE_PATH: str = str(BASE_DIR / "data/vector_store")
    AUDIO_TEMP_DIR: str = str(BASE_DIR / "data/audio/temp")
    AUDIO_RESPONSE_DIR: str = str(BASE_DIR / "data/audio/responses")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    @staticmethod
    def resolve_embedding_provider(embedding_provider: str, llm_provider: str) -> str:
        return (embedding_provider or llm_provider).lower().strip()

    def get_embedding_provider(self) -> str:
        return self.resolve_embedding_provider(self.EMBEDDING_PROVIDER, self.LLM_PROVIDER)

    def get_provider_key_env_name(self, provider: str) -> str:
        mapping = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "grok": "GROK_API_KEY",
            "ollama": "LLM_API_KEY",
            "openai_compatible": "LLM_API_KEY",
        }
        return mapping.get(provider, "LLM_API_KEY")

    def get_provider_api_key(self, provider: str) -> str:
        provider = provider.lower().strip()
        provider_keys = {
            "openai": self.OPENAI_API_KEY,
            "gemini": self.GEMINI_API_KEY,
            "grok": self.GROK_API_KEY,
            "ollama": self.LLM_API_KEY,
            "openai_compatible": self.LLM_API_KEY,
        }
        key = provider_keys.get(provider, "")
        if key and not key.startswith("put_"):
            return key

        # Convenience fallback: allow a single key in OPENAI_API_KEY for any provider.
        if self.OPENAI_API_KEY and not self.OPENAI_API_KEY.startswith("put_"):
            return self.OPENAI_API_KEY
        if self.GEMINI_API_KEY and not self.GEMINI_API_KEY.startswith("put_"):
            return self.GEMINI_API_KEY
        if self.GROK_API_KEY and not self.GROK_API_KEY.startswith("put_"):
            return self.GROK_API_KEY
        return self.LLM_API_KEY

    def get_provider_base_url(self, provider: str) -> Optional[str]:
        provider = provider.lower().strip()
        if provider == "grok":
            return self.GROK_BASE_URL
        if provider == "ollama":
            return self.OLLAMA_BASE_URL
        if provider == "openai_compatible":
            return self.OPENAI_COMPATIBLE_BASE_URL or None
        return None

    def get_chat_model(self, provider: str) -> str:
        if self.LLM_MODEL:
            return self.LLM_MODEL

        defaults = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-3.6-flash",
            "grok": "grok-2-latest",
            "ollama": "llama3.2",
            "openai_compatible": "gpt-4o-mini",
        }
        return defaults.get(provider.lower().strip(), "gpt-4o-mini")

    def get_embedding_model(self, provider: str) -> str:
        if self.EMBEDDING_MODEL:
            return self.EMBEDDING_MODEL

        defaults = {
            "openai": "text-embedding-3-small",
            "gemini": "models/gemini-embedding-001",
            "grok": "text-embedding-3-small",
            "ollama": "nomic-embed-text",
            "openai_compatible": "text-embedding-3-small",
        }
        return defaults.get(provider.lower().strip(), "text-embedding-3-small")


settings = Settings()
