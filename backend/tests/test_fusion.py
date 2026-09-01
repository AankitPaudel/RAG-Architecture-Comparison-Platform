from rag.fusion import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_combines_lists():
    dense = [
        {
            "content": "Recursion calls itself.",
            "metadata": {"lecture_id": 1, "chunk_id": 0},
            "score": 0.9,
        },
        {
            "content": "Iteration uses loops.",
            "metadata": {"lecture_id": 1, "chunk_id": 1},
            "score": 0.7,
        },
    ]
    bm25 = [
        {
            "content": "Recursion calls itself.",
            "metadata": {"lecture_id": 1, "chunk_id": 0},
            "score": 4.2,
        },
        {
            "content": "Base cases stop recursion.",
            "metadata": {"lecture_id": 1, "chunk_id": 2},
            "score": 3.1,
        },
    ]

    fused = reciprocal_rank_fusion([dense, bm25])

    assert len(fused) == 3
    assert fused[0]["content"] == "Recursion calls itself."
    assert fused[0]["fused_rank"] == 1
    assert fused[0]["metadata"]["dense_rank"] == 1
    assert fused[0]["metadata"]["bm25_rank"] == 1


def test_reciprocal_rank_fusion_assigns_ranks():
    dense = [
        {"content": "A", "metadata": {"lecture_id": 1, "chunk_id": 0}, "score": 0.8},
    ]
    bm25 = [
        {"content": "B", "metadata": {"lecture_id": 1, "chunk_id": 1}, "score": 2.0},
    ]

    fused = reciprocal_rank_fusion([dense, bm25])

    assert fused[0]["fused_rank"] == 1
    assert fused[1]["fused_rank"] == 2
