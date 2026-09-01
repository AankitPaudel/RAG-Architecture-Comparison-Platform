"""Seed the database and all RAG indexes with example long-text sources."""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.session import SessionLocal, init_db
from database.models.lecture import Lecture
from rag.pipeline_registry import get_pipeline_service

SAMPLE_SOURCES = [
    {
        "title": "Algorithms and Recursion",
        "file": "recursion_algorithms.txt",
    },
    {
        "title": "FastAPI Web Development",
        "file": "fastapi_development.txt",
    },
    {
        "title": "Data Structures Fundamentals",
        "file": "data_structures.txt",
    },
]


def seed_sources():
    init_db()
    db = SessionLocal()
    service = get_pipeline_service()
    lectures_dir = backend_dir / "data" / "lectures"

    created = 0
    skipped = 0

    for source in SAMPLE_SOURCES:
        existing = db.query(Lecture).filter(Lecture.title == source["title"]).first()
        if existing:
            print(f"SKIP  {source['title']} (already exists, id={existing.id})")
            skipped += 1
            continue

        file_path = lectures_dir / source["file"]
        if not file_path.exists():
            print(f"WARN  Missing file: {file_path}")
            continue

        content = file_path.read_text(encoding="utf-8")
        lecture = Lecture(title=source["title"], content=content)
        db.add(lecture)
        db.commit()
        db.refresh(lecture)

        print(f"INDEX {source['title']} (id={lecture.id}, {len(content)} chars)")
        try:
            service.index_lecture(lecture.id, lecture.content, title=lecture.title)
        except Exception as error:
            print(f"WARN  Vector indexing failed for {source['title']}: {error}")
            chunks = service.rag_processor.text_splitter.split_text(lecture.content)
            service.graph.index_lecture_chunks(lecture.id, chunks)
            print(f"      Graph indexed with {len(chunks)} chunks")
        created += 1

    total = db.query(Lecture).count()
    db.close()

    print(f"\nDone: {created} created, {skipped} skipped, {total} total sources in database.")
    print("You can now use the Compare page with questions like:")
    print('  - "Explain recursion and base cases"')
    print('  - "What is FastAPI built on?"')
    print('  - "Compare merge sort and quick sort"')


if __name__ == "__main__":
    seed_sources()
