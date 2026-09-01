from typing import List, Optional

from pydantic import BaseModel, Field


class EvaluationQuestion(BaseModel):
    id: str
    question: str
    expected_answer: str
    relevant_chunk_ids: List[str] = Field(default_factory=list)
    source_ids: Optional[List[str]] = None


EVALUATION_DATASET: List[EvaluationQuestion] = [
    EvaluationQuestion(
        id="recursion-1",
        question="What is recursion?",
        expected_answer="Recursion is when a function calls itself to solve smaller subproblems.",
        relevant_chunk_ids=["1:0", "1:1"],
        source_ids=["1"],
    ),
    EvaluationQuestion(
        id="base-case-1",
        question="Why is a base case needed in recursion?",
        expected_answer="A base case stops recursive calls and prevents infinite recursion.",
        relevant_chunk_ids=["1:1"],
        source_ids=["1"],
    ),
    EvaluationQuestion(
        id="fastapi-1",
        question="What is FastAPI built on?",
        expected_answer="FastAPI is built on Starlette.",
        relevant_chunk_ids=["2:0"],
        source_ids=["2"],
    ),
    EvaluationQuestion(
        id="photosynthesis-1",
        question="How does photosynthesis work?",
        expected_answer="Photosynthesis converts light energy into chemical energy using chlorophyll.",
        relevant_chunk_ids=["3:0"],
        source_ids=["3"],
    ),
]
