# Create a file: backend/scripts/check_data.py
from rag.processor import RAGProcessor

processor = RAGProcessor()
count = processor.vector_store._collection.count()
print(f"Number of documents in vector store: {count}")