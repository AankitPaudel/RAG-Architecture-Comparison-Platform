"""Re-index all SQLite sources into ChromaDB and the knowledge graph."""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.session import SessionLocal
from database.models.lecture import Lecture
from rag.pipeline_registry import get_pipeline_service


def main():
    db = SessionLocal()
    lectures = db.query(Lecture).all()
    service = get_pipeline_service()

    print(f"Re-indexing {len(lectures)} sources...\n")

    for lecture in lectures:
        print(f"  [{lecture.id}] {lecture.title}")
        try:
            service.delete_lecture(lecture.id)
        except Exception:
            pass
        try:
            service.index_lecture(lecture.id, lecture.content, title=lecture.title)
            print(f"       OK - indexed")
        except Exception as error:
            print(f"       FAILED: {error}")

    count = service.rag_processor.collection.count()
    print(f"\nDone. ChromaDB now has {count} chunks.")
    db.close()


if __name__ == "__main__":
    main()
