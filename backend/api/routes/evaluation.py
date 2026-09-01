import logging
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from evaluation.runner import EvaluationRunner

logger = logging.getLogger(__name__)
router = APIRouter()


class EvaluationRequest(BaseModel):
    pipelines: List[str] = Field(
        default_factory=lambda: ["naive", "hybrid", "agentic", "graph"]
    )


@router.post("/run")
async def run_evaluation(request: EvaluationRequest):
    runner = EvaluationRunner(pipelines=request.pipelines)
    return await runner.run()


@router.get("/dataset")
async def get_evaluation_dataset():
    from evaluation.dataset import EVALUATION_DATASET
    return {
        "questions": [question.model_dump() for question in EVALUATION_DATASET],
    }
