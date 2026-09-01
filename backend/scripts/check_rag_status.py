"""Diagnose RAG indexing and retrieval status."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.session import SessionLocal
from database.models.lecture import Lecture
from rag.processor import RAGProcessor
from rag.pipeline_registry import get_pipeline_service


async def main():
    db = SessionLocal()
    lectures = db.query(Lecture).all()
    print(f"SQLite sources: {len(lectures)}")
    for lecture in lectures:
        print(f"  [{lecture.id}] {lecture.title} ({len(lecture.content)} chars)")
    db.close()

    try:
        processor = RAGProcessor()
    except Exception as error:
        print(f"\nRAGProcessor init FAILED: {error}")
        print("Check LLM_PROVIDER and the matching API key in backend/.env")
        return

    count = processor.collection.count()
    print(f"\nChromaDB chunks: {count}")

    if count == 0:
        print("\nPROBLEM: Vector store is empty. Sources exist in SQLite but were never embedded.")
        print("Fix: run  python scripts/reindex_all_sources.py")
        return

    all_chunks = processor.get_all_chunks()
    lecture_ids_in_chroma = sorted({c["metadata"].get("lecture_id") for c in all_chunks})
    print(f"Lecture IDs in Chroma: {lecture_ids_in_chroma}")

    for question in ["Explain recursion", "What is FastAPI built on?", "urban transportation"]:
        results = await processor.find_relevant_context(question, num_chunks=3, min_score=0.2)
        print(f"\nQuery: {question!r}")
        print(f"  Results (min_score=0.2): {len(results)}")
        for item in results:
            print(f"    score={item.get('score')} source={item['metadata'].get('title')}")

    # Test full pipeline
    print("\n--- Naive RAG pipeline test ---")
    service = get_pipeline_service()
    result = await service.naive.run("Explain recursion and base cases", allow_fallback=False)
    print(f"Mode: {result.mode}")
    print(f"Answer: {result.answer[:200]}...")
    print(f"Chunks: {result.num_chunks_retrieved}")


if __name__ == "__main__":
    asyncio.run(main())
