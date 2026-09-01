# File: backend/rag/vector_store.py
from typing import List, Dict, Optional
from langchain.vectorstores import Chroma
from langchain.embeddings.base import Embeddings
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, embeddings: Embeddings):
        """Initialize vector store with embeddings"""
        try:
            self.embeddings = embeddings
            self.store = Chroma(
                persist_directory=settings.VECTOR_STORE_PATH,
                embedding_function=embeddings
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise

    def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """Add texts to vector store"""
        try:
            self.store.add_texts(texts, metadatas)
            self.store.persist()
            logger.info(f"Added {len(texts)} texts to vector store")
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {str(e)}")
            raise

    async def similarity_search(
        self, 
        query: str, 
        k: int = 3
    ) -> List[Dict]:
        """Search for similar texts"""
        try:
            docs = self.store.similarity_search(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise

    def clear(self) -> None:
        """Clear vector store"""
        try:
            self.store.delete_collection()
            self.store = Chroma(
                persist_directory=settings.VECTOR_STORE_PATH,
                embedding_function=self.embeddings
            )
            logger.info("Vector store cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise