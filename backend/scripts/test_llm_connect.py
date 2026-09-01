"""Test configured LLM and embedding providers."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from rag.providers import get_embedding_function, get_llm_client, validate_provider_config


async def main():
    provider = validate_provider_config()
    embedding_provider = settings.get_embedding_provider()

    print("RAG Provider Configuration")
    print("--------------------------")
    print(f"LLM provider:        {provider}")
    print(f"Embedding provider:  {embedding_provider}")
    print(f"Chat model:          {settings.get_chat_model(provider)}")
    print(f"Embedding model:     {settings.get_embedding_model(embedding_provider)}")
    print(f"API key env:         {settings.get_provider_key_env_name(provider)}")

    print("\n1. Testing chat completion...")
    client = get_llm_client()
    answer, usage = await client.chat_complete(
        [{"role": "user", "content": "Reply with exactly: provider test ok"}],
        max_tokens=256,
    )
    print(f"   Response: {answer}")
    if usage:
        print(f"   Tokens: {usage.total_tokens}")

    print("\n2. Testing embeddings...")
    embedding_function = get_embedding_function()
    vectors = embedding_function(["hello world"])
    print(f"   Embedding dimensions: {len(vectors[0])}")

    print("\nAll provider checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
