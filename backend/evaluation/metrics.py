import math
from typing import List, Set


def hit_rate_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return 1.0 if top_k.intersection(relevant_ids) else 0.0


def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    if not relevant_ids or k == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    return len(set(top_k).intersection(relevant_ids)) / len(top_k)


def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return len(top_k.intersection(relevant_ids)) / len(relevant_ids)


def mean_reciprocal_rank(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    if not relevant_ids:
        return 0.0
    for index, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1.0 / index
    return 0.0


def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    if not relevant_ids or k == 0:
        return 0.0

    def dcg(ids: List[str]) -> float:
        score = 0.0
        for index, chunk_id in enumerate(ids[:k], start=1):
            relevance = 1.0 if chunk_id in relevant_ids else 0.0
            score += relevance / math.log2(index + 1)
        return score

    ideal = dcg(list(relevant_ids))
    if ideal == 0:
        return 0.0
    return dcg(retrieved_ids) / ideal


def chunk_id_from_metadata(metadata: dict) -> str:
    lecture_id = metadata.get("lecture_id")
    chunk_id = metadata.get("chunk_id")
    if lecture_id is None or chunk_id is None:
        return ""
    return f"{lecture_id}:{chunk_id}"
