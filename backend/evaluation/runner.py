import logging
from typing import Dict, List, Optional

from evaluation.dataset import EVALUATION_DATASET, EvaluationQuestion
from evaluation.metrics import (
    chunk_id_from_metadata,
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from rag.models import RAGResult
from rag.pipeline_registry import PIPELINE_REGISTRY, get_pipeline_service

logger = logging.getLogger(__name__)

DEFAULT_PIPELINES = ["naive", "hybrid", "agentic", "graph"]
K_VALUES = [1, 3, 5]


class EvaluationRunner:
    def __init__(self, pipelines: Optional[List[str]] = None):
        self.pipelines = pipelines or DEFAULT_PIPELINES
        self.service = get_pipeline_service()

    async def run(self, dataset: Optional[List[EvaluationQuestion]] = None) -> Dict:
        questions = dataset or EVALUATION_DATASET
        pipeline_results = {name: self._empty_pipeline_result(name) for name in self.pipelines}

        for question in questions:
            relevant_ids = set(question.relevant_chunk_ids)
            for pipeline_name in self.pipelines:
                summary = pipeline_results[pipeline_name]
                try:
                    pipeline = self.service.get_pipeline(pipeline_name)
                    result: RAGResult = await pipeline.run(
                        question.question,
                        source_ids=question.source_ids,
                    )
                    retrieved_ids = [
                        chunk_id_from_metadata(chunk.metadata)
                        for chunk in result.retrieved_chunks
                        if chunk_id_from_metadata(chunk.metadata)
                    ]

                    if relevant_ids:
                        for k in K_VALUES:
                            summary["retrieval_metrics"][f"hit_rate@{k}"].append(
                                hit_rate_at_k(retrieved_ids, relevant_ids, k)
                            )
                            summary["retrieval_metrics"][f"precision@{k}"].append(
                                precision_at_k(retrieved_ids, relevant_ids, k)
                            )
                            summary["retrieval_metrics"][f"recall@{k}"].append(
                                recall_at_k(retrieved_ids, relevant_ids, k)
                            )
                            summary["retrieval_metrics"][f"ndcg@{k}"].append(
                                ndcg_at_k(retrieved_ids, relevant_ids, k)
                            )
                        summary["retrieval_metrics"]["mrr"].append(
                            mean_reciprocal_rank(retrieved_ids, relevant_ids)
                        )

                    summary["latency_ms"].append(result.total_time_ms)
                    if result.token_usage and result.token_usage.total_tokens:
                        summary["token_usage"].append(result.token_usage.total_tokens)

                    summary["question_results"].append({
                        "question_id": question.id,
                        "question": question.question,
                        "answer": result.answer,
                        "retrieved_chunk_ids": retrieved_ids,
                        "relevant_chunk_ids": list(relevant_ids),
                        "retrieval_time_ms": result.retrieval_time_ms,
                        "generation_time_ms": result.generation_time_ms,
                        "total_time_ms": result.total_time_ms,
                        "token_usage": result.token_usage.model_dump() if result.token_usage else None,
                        "mode": result.mode,
                    })
                except Exception as error:
                    logger.error("Evaluation failed for %s on %s: %s", pipeline_name, question.id, error)
                    summary["errors"].append({
                        "question_id": question.id,
                        "error": str(error),
                    })

        for name, summary in pipeline_results.items():
            summary["averages"] = self._compute_averages(summary)

        return {
            "dataset_size": len(questions),
            "pipelines": pipeline_results,
            "notes": [
                "Retrieval metrics are only computed where ground-truth relevant chunk IDs exist.",
                "Generation quality metrics are not included because they require model-judged evaluation.",
            ],
        }

    def _empty_pipeline_result(self, pipeline_name: str) -> Dict:
        retrieval_metrics = {"mrr": []}
        for k in K_VALUES:
            retrieval_metrics[f"hit_rate@{k}"] = []
            retrieval_metrics[f"precision@{k}"] = []
            retrieval_metrics[f"recall@{k}"] = []
            retrieval_metrics[f"ndcg@{k}"] = []

        return {
            "pipeline": pipeline_name,
            "pipeline_label": PIPELINE_REGISTRY.get(pipeline_name, pipeline_name),
            "retrieval_metrics": retrieval_metrics,
            "latency_ms": [],
            "token_usage": [],
            "question_results": [],
            "errors": [],
            "averages": {},
        }

    def _compute_averages(self, summary: Dict) -> Dict:
        averages = {}
        for metric_name, values in summary["retrieval_metrics"].items():
            averages[metric_name] = round(sum(values) / len(values), 4) if values else None

        averages["avg_latency_ms"] = (
            round(sum(summary["latency_ms"]) / len(summary["latency_ms"]), 2)
            if summary["latency_ms"] else None
        )
        averages["avg_token_usage"] = (
            round(sum(summary["token_usage"]) / len(summary["token_usage"]), 2)
            if summary["token_usage"] else None
        )
        return averages
