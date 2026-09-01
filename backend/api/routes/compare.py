import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag.models import RAGResult
from rag.pipeline_registry import PIPELINE_REGISTRY, get_pipeline_service

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    source_ids: Optional[List[str]] = None
    pipeline: str = "naive"
    allow_fallback: bool = False


class CompareRequest(BaseModel):
    question: str
    source_ids: Optional[List[str]] = None
    pipelines: List[str] = Field(default_factory=lambda: ["naive", "hybrid", "agentic", "graph"])


class PipelineResultResponse(BaseModel):
    pipeline: str
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None


class CompareResponse(BaseModel):
    question: str
    source_ids: Optional[List[str]] = None
    results: List[PipelineResultResponse]


class QueryResponse(BaseModel):
    question: str
    pipeline: str
    result: dict


async def _run_pipeline_safe(pipeline_name: str, question: str, source_ids: Optional[List[str]], allow_fallback: bool = False):
    service = get_pipeline_service()
    try:
        pipeline = service.get_pipeline(pipeline_name)
        result: RAGResult = await pipeline.run(
            question=question,
            allow_fallback=allow_fallback,
            source_ids=source_ids,
        )
        return PipelineResultResponse(
            pipeline=pipeline_name,
            success=result.mode != "error",
            result=result.to_api_dict(),
            error=result.error,
        )
    except Exception as error:
        logger.error("Pipeline %s failed: %s", pipeline_name, error, exc_info=True)
        return PipelineResultResponse(
            pipeline=pipeline_name,
            success=False,
            result=None,
            error=str(error),
        )


@router.post("/query", response_model=QueryResponse)
async def query_with_pipeline(request: QueryRequest):
    if request.pipeline not in PIPELINE_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown pipeline: {request.pipeline}")

    pipeline_result = await _run_pipeline_safe(
        request.pipeline,
        request.question,
        request.source_ids,
        allow_fallback=request.allow_fallback,
    )
    if not pipeline_result.success or not pipeline_result.result:
        raise HTTPException(
            status_code=500,
            detail=pipeline_result.error or f"Pipeline {request.pipeline} failed",
        )

    return QueryResponse(
        question=request.question,
        pipeline=request.pipeline,
        result=pipeline_result.result,
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_pipelines(request: CompareRequest):
    invalid = [name for name in request.pipelines if name not in PIPELINE_REGISTRY]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown pipelines: {', '.join(invalid)}")

    tasks = [
        _run_pipeline_safe(pipeline_name, request.question, request.source_ids)
        for pipeline_name in request.pipelines
    ]
    results = await asyncio.gather(*tasks)

    return CompareResponse(
        question=request.question,
        source_ids=request.source_ids,
        results=results,
    )
