from evaluation.metrics import (
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_hit_rate_at_k():
    retrieved = ["1:0", "1:1", "2:0"]
    relevant = {"1:0", "1:2"}
    assert hit_rate_at_k(retrieved, relevant, 1) == 1.0
    assert hit_rate_at_k(["2:0"], relevant, 1) == 0.0


def test_precision_at_k():
    retrieved = ["1:0", "2:0", "1:1"]
    relevant = {"1:0", "1:1"}
    assert abs(precision_at_k(retrieved, relevant, 3) - (2 / 3)) < 0.001


def test_recall_at_k():
    retrieved = ["1:0", "2:0"]
    relevant = {"1:0", "1:1"}
    assert recall_at_k(retrieved, relevant, 2) == 0.5


def test_mean_reciprocal_rank():
    retrieved = ["2:0", "1:0", "1:1"]
    relevant = {"1:0"}
    assert mean_reciprocal_rank(retrieved, relevant) == 0.5


def test_ndcg_at_k():
    retrieved = ["1:0", "2:0", "1:1"]
    relevant = {"1:0", "1:1"}
    score = ndcg_at_k(retrieved, relevant, 3)
    assert 0 < score <= 1.0


def test_metrics_return_zero_without_relevant_ids():
    assert hit_rate_at_k(["1:0"], set(), 1) == 0.0
    assert precision_at_k(["1:0"], set(), 1) == 0.0
    assert recall_at_k(["1:0"], set(), 1) == 0.0
    assert mean_reciprocal_rank(["1:0"], set()) == 0.0
    assert ndcg_at_k(["1:0"], set(), 3) == 0.0
