from typing import Dict, List

from rag.bm25 import chunk_key


def reciprocal_rank_fusion(
    ranked_lists: List[List[dict]],
    k: int = 60,
) -> List[dict]:
    fused_scores: Dict[str, float] = {}
    chunk_lookup: Dict[str, dict] = {}
    rank_metadata: Dict[str, dict] = {}

    for list_index, ranked_list in enumerate(ranked_lists):
        for rank, item in enumerate(ranked_list, start=1):
            metadata = item.get("metadata", {})
            key = chunk_key(metadata, item["content"])
            fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (k + rank))
            chunk_lookup[key] = item

            if key not in rank_metadata:
                rank_metadata[key] = {}
            if list_index == 0:
                rank_metadata[key]["dense_rank"] = rank
            elif list_index == 1:
                rank_metadata[key]["bm25_rank"] = rank

    fused_items = []
    for rank, (key, score) in enumerate(
        sorted(fused_scores.items(), key=lambda item: item[1], reverse=True),
        start=1,
    ):
        item = dict(chunk_lookup[key])
        item["score"] = round(score, 6)
        item["metadata"] = dict(item.get("metadata", {}))
        item["metadata"].update(rank_metadata.get(key, {}))
        item["fused_rank"] = rank
        fused_items.append(item)

    return fused_items
