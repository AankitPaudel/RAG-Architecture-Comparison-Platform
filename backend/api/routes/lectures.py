# File: backend/api/routes/lectures.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import re
from app.dependencies import get_db
from database.models.lecture import Lecture
from api.schemas.responses import LectureCreate, Lecture as LectureSchema
from rag.pipeline_registry import get_pipeline_service

router = APIRouter()


class YouTubeIngestRequest(BaseModel):
    url: str
    title: str = None


def extract_youtube_video_id(url: str) -> str:
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:shorts/)([A-Za-z0-9_-]{11})",
        r"(?:embed/)([A-Za-z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    raise HTTPException(status_code=400, detail="Invalid YouTube video URL or ID")


@router.post("/", response_model=LectureSchema)
async def create_lecture(
    lecture: LectureCreate,
    db: Session = Depends(get_db)
):
    """Create new lecture"""
    db_lecture = Lecture(**lecture.model_dump())
    db.add(db_lecture)
    db.commit()
    db.refresh(db_lecture)

    get_pipeline_service().index_lecture(
        db_lecture.id,
        db_lecture.content,
        title=db_lecture.title,
    )

    return db_lecture


@router.post("/youtube", response_model=LectureSchema)
async def ingest_youtube_video(
    request: YouTubeIngestRequest,
    db: Session = Depends(get_db)
):
    """Extract a YouTube transcript and store it as a RAG knowledge source."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="YouTube transcript support is not installed. Run pip install -r requirements.txt."
        )

    video_id = extract_youtube_video_id(request.url)

    try:
        transcript_items = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join(item.get("text", "").strip() for item in transcript_items)
        transcript = re.sub(r"\s+", " ", transcript).strip()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not load transcript for this YouTube video: {str(e)}"
        )

    if not transcript:
        raise HTTPException(status_code=400, detail="No transcript text was found for this video")

    title = request.title or f"YouTube transcript {video_id}"
    db_lecture = Lecture(title=title, content=transcript)
    db.add(db_lecture)
    db.commit()
    db.refresh(db_lecture)

    get_pipeline_service().index_lecture(db_lecture.id, db_lecture.content, title=db_lecture.title)
    return db_lecture


@router.get("/", response_model=List[LectureSchema])
async def get_lectures(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all lectures"""
    lectures = db.query(Lecture).offset(skip).limit(limit).all()
    return lectures


@router.get("/{lecture_id}", response_model=LectureSchema)
async def get_lecture(
    lecture_id: int,
    db: Session = Depends(get_db)
):
    """Get specific lecture"""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return lecture


@router.delete("/{lecture_id}")
async def delete_lecture(
    lecture_id: int,
    db: Session = Depends(get_db)
):
    """Delete a lecture/source from database, ChromaDB, BM25 corpus, and graph."""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")

    get_pipeline_service().delete_lecture(lecture_id)
    db.delete(lecture)
    db.commit()
    return {"status": "deleted", "lecture_id": lecture_id}
