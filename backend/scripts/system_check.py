# File: backend/scripts/system_check.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)


def check_system():
    print("Checking RAG Platform System Setup...")

    backend_dir = Path(__file__).parent.parent
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", llm_provider)

    print(f"\n1. LLM Provider: {llm_provider}")
    print(f"   Embedding Provider: {embedding_provider}")

    key_names = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "grok": "GROK_API_KEY",
        "ollama": "LLM_API_KEY",
        "openai_compatible": "LLM_API_KEY",
    }
    llm_key_name = key_names.get(llm_provider, "LLM_API_KEY")
    embed_key_name = key_names.get(embedding_provider, "LLM_API_KEY")
    llm_key = os.getenv(llm_key_name) or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    embed_key = os.getenv(embed_key_name) or llm_key

    print(f"   {llm_key_name}: {'set' if llm_key and not llm_key.startswith('put_') else 'missing'}")
    if embedding_provider != llm_provider:
        print(f"   {embed_key_name}: {'set' if embed_key and not embed_key.startswith('put_') else 'missing'}")

    dirs_to_check = [
        "data/lectures",
        "data/audio",
        "data/vector_store",
    ]

    print("\n2. Directory Structure:")
    for dir_path in dirs_to_check:
        path = backend_dir / dir_path
        exists = path.exists()
        print(f"   {dir_path}: {'exists' if exists else 'missing'}")
        if not exists:
            path.mkdir(parents=True, exist_ok=True)
            print(f"   Created directory: {dir_path}")

    lecture_dir = backend_dir / "data/lectures"
    lecture_files = list(lecture_dir.glob("*.txt"))
    print(f"\n3. Lecture Files Found: {len(lecture_files)}")
    for file in lecture_files:
        print(f"   - {file.name}")

    print("\n4. Database:")
    db_file = backend_dir / "rag_platform.db"
    legacy_db = backend_dir / "virtual_teacher.db"
    print(f"   rag_platform.db: {'exists' if db_file.exists() else 'missing'}")
    print(f"   virtual_teacher.db: {'exists' if legacy_db.exists() else 'missing'}")

    print("\n5. Next steps:")
    print("   python scripts/test_llm_connect.py")
    print("   python scripts/reindex_all_sources.py")


if __name__ == "__main__":
    check_system()
