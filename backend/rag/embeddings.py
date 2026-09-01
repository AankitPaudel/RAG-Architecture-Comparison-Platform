# File: backend/rag/embeddings.py
from langchain.embeddings.openai import OpenAIEmbeddings
from app.config import settings

def get_embeddings():
    """Get embeddings instance"""
    return OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY
    )