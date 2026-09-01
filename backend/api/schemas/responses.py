# File: backend/api/schemas/responses.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LectureBase(BaseModel):
    title: str
    content: str

class LectureCreate(LectureBase):
    pass

class Lecture(LectureBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class QuestionResponse(BaseModel):
    question: str
    answer: str
    audio_url: Optional[str] = None     # Added this field with default None
    sources: Optional[List[str]] = None
    confidence_score: Optional[float] = None