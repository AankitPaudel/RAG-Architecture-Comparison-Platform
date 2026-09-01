# File: backend/api/routes/qa.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.dependencies import get_db
from database.models.lecture import Lecture
from qa.pipeline import QAPipeline
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
qa_pipeline = None


def get_qa_pipeline():
    global qa_pipeline
    if qa_pipeline is None:
        qa_pipeline = QAPipeline()
    return qa_pipeline

class QuestionRequest(BaseModel):
    question: str
    allow_fallback: bool = False

class QuestionResponse(BaseModel):
    question: str
    answer: str
    confidence_score: float = 0.0
    sources: Optional[List[str]] = None
    audio_url: Optional[str] = None  # Added audio_url field
    mode: Optional[str] = None

class SearchChunk(BaseModel):
    content: str
    source: str
    title: Optional[str] = None
    score: Optional[float] = None
    matched_terms: Optional[List[str]] = None

class SearchComparisonResponse(BaseModel):
    question: str
    vector_results: List[SearchChunk]
    vectorless_results: List[SearchChunk]
    summary: str

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """Process a question and return an answer with audio"""
    logger.info(f"Received question: {request.question}")

    try:
        # Get response from QA pipeline
        pipeline = get_qa_pipeline()
        response = await pipeline.get_answer(
            request.question,
            allow_fallback=request.allow_fallback
        )
        
        # Return response with audio URL
        return {
            "question": request.question,
            "answer": response["answer"],
            "confidence_score": response.get("confidence_score", 0.0),
            "sources": response.get("sources", []),
            "audio_url": response.get("audio_url"),
            "mode": response.get("mode")
        }
        
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Check if the QA system is operational"""
    try:
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"System unhealthy: {str(e)}"
        )

@router.post("/compare", response_model=SearchComparisonResponse)
async def compare_search_methods(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """Compare semantic vector retrieval with keyword-only vectorless retrieval."""
    try:
        pipeline = get_qa_pipeline()
        vector_docs = await pipeline.rag_processor.find_relevant_context(
            request.question,
            num_chunks=3
        )
        lectures = db.query(Lecture).all()
        keyword_docs = pipeline.rag_processor.keyword_search(
            request.question,
            lectures,
            num_chunks=3
        )

        vector_results = [
            SearchChunk(
                content=doc["content"],
                source=doc["metadata"].get("source", "unknown"),
                title=doc["metadata"].get("title"),
                score=doc.get("score"),
                matched_terms=None
            )
            for doc in vector_docs
        ]

        vectorless_results = [
            SearchChunk(
                content=doc["content"],
                source=doc["metadata"].get("source", "unknown"),
                title=doc["metadata"].get("title"),
                score=doc.get("score"),
                matched_terms=doc["metadata"].get("matched_terms", [])
            )
            for doc in keyword_docs
        ]

        return {
            "question": request.question,
            "vector_results": vector_results,
            "vectorless_results": vectorless_results,
            "summary": (
                "Vector RAG searches by meaning using embeddings. Vectorless search "
                "uses direct keyword overlap, so it is simpler but can miss relevant "
                "content when the wording is different."
            )
        }
    except Exception as e:
        logger.error(f"Error comparing search methods: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing search methods: {str(e)}"
        )
