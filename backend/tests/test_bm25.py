import pytest

from rag.bm25 import BM25Retriever, tokenize
from rag.processor import parse_source_ids


def test_tokenize_removes_stop_words():
    tokens = tokenize("What is the algorithm for sorting data?")
    assert "what" not in tokens
    assert "the" not in tokens
    assert "algorithm" in tokens
    assert "sorting" in tokens


def test_bm25_search_returns_ranked_results():
    retriever = BM25Retriever()
    chunks = [
        {
            "content": "Recursion is when a function calls itself to solve smaller subproblems.",
            "metadata": {"lecture_id": 1, "chunk_id": 0, "title": "Algorithms"},
        },
        {
            "content": "Binary search divides a sorted array in half repeatedly.",
            "metadata": {"lecture_id": 1, "chunk_id": 1, "title": "Algorithms"},
        },
        {
            "content": "Recursion needs a base case to stop infinite calls.",
            "metadata": {"lecture_id": 2, "chunk_id": 0, "title": "CS Basics"},
        },
    ]
    retriever.index(chunks)

    results = retriever.search("Explain recursion", top_k=2)

    assert len(results) == 2
    assert "recursion" in results[0]["content"].lower()
    assert results[0]["score"] >= results[1]["score"]


def test_bm25_source_filtering():
    retriever = BM25Retriever()
    chunks = [
        {
            "content": "Recursion solves problems by calling itself.",
            "metadata": {"lecture_id": 1, "chunk_id": 0},
        },
        {
            "content": "Photosynthesis converts sunlight into energy.",
            "metadata": {"lecture_id": 2, "chunk_id": 0},
        },
    ]
    retriever.index(chunks)

    results = retriever.search("recursion", top_k=5, source_ids=[2])
    assert results == []


def test_parse_source_ids_supports_multiple_formats():
    assert parse_source_ids(["1", "source-2", "lecture_3"]) == [1, 2, 3]
    assert parse_source_ids([]) is None
