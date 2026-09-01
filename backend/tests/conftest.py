import pytest
from unittest.mock import AsyncMock, MagicMock

from rag.models import TokenUsage


@pytest.fixture
def sample_context_docs():
    return [
        {
            "content": "Photosynthesis converts light energy into chemical energy.",
            "metadata": {
                "lecture_id": 1,
                "chunk_id": 0,
                "source": "lecture_1",
                "title": "Biology Basics",
            },
            "score": 0.85,
        },
        {
            "content": "Chlorophyll absorbs red and blue light wavelengths.",
            "metadata": {
                "lecture_id": 1,
                "chunk_id": 1,
                "source": "lecture_1",
                "title": "Biology Basics",
            },
            "score": 0.72,
        },
    ]


@pytest.fixture
def mock_rag_processor(sample_context_docs):
    processor = MagicMock()
    processor.find_relevant_context = AsyncMock(return_value=sample_context_docs)
    return processor


@pytest.fixture
def mock_token_usage():
    return TokenUsage(prompt_tokens=120, completion_tokens=30, total_tokens=150)


@pytest.fixture
def mock_llm_client(mock_token_usage):
    client = MagicMock()
    client.chat_complete = AsyncMock(
        return_value=(
            "Photosynthesis converts light into chemical energy using chlorophyll.",
            mock_token_usage,
        )
    )
    return client


@pytest.fixture
def mock_openai_client(mock_llm_client):
    return mock_llm_client


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr("rag.naive_pipeline.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("rag.naive_pipeline.settings.OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setattr("rag.hybrid_pipeline.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("rag.hybrid_pipeline.settings.OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setattr("rag.agentic_pipeline.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("rag.agentic_pipeline.settings.OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setattr("rag.graph_pipeline.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("rag.graph_pipeline.settings.OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setattr("rag.providers.factory.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("rag.providers.factory.settings.OPENAI_API_KEY", "test-key-12345")

    def _get_provider_api_key(provider):
        return "test-key-12345"

    monkeypatch.setattr("rag.providers.factory.settings.get_provider_api_key", _get_provider_api_key)
    monkeypatch.setattr("rag.processor.settings.get_provider_api_key", _get_provider_api_key)
    monkeypatch.setattr("rag.processor.settings.get_embedding_provider", lambda: "openai")
    monkeypatch.setattr(
        "rag.processor.validate_provider_config",
        lambda provider=None: provider or "openai",
    )
