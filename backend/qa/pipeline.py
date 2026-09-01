from typing import Dict
import logging

from audio.text_to_speech import TextToSpeech
from rag.pipeline_registry import get_pipeline_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QAPipeline:
    def __init__(self):
        logger.info("Initializing QA Pipeline...")
        self.pipeline_service = get_pipeline_service()
        self.text_to_speech = TextToSpeech()
        logger.info("QA Pipeline initialized successfully")

    @property
    def rag_processor(self):
        return self.pipeline_service.rag_processor

    async def get_answer(self, question: str, allow_fallback: bool = False) -> Dict:
        rag_result = await self.pipeline_service.naive.run(question, allow_fallback=allow_fallback)
        audio_url = await self._make_audio(rag_result.answer)

        return {
            "question": question,
            "answer": rag_result.answer,
            "sources": [citation.source for citation in rag_result.citations],
            "confidence_score": self._calculate_confidence(rag_result),
            "audio_url": audio_url,
            "mode": rag_result.mode,
            "rag_result": rag_result,
        }

    async def _make_audio(self, text: str):
        try:
            audio_file = await self.text_to_speech.convert(text)
            return f"/api/audio/responses/{audio_file.name}"
        except Exception as audio_error:
            logger.error(f"Error generating audio: {audio_error}")
            return None

    def _calculate_confidence(self, rag_result) -> float:
        if not rag_result.retrieved_chunks:
            if rag_result.mode == "hybrid_fallback":
                return 0.25
            return 0.0

        context_docs = [
            {"score": chunk.score}
            for chunk in rag_result.retrieved_chunks
        ]
        context_score = min(len(context_docs) / 3, 1.0)
        answer_length_score = min(len(rag_result.answer) / 500, 1.0)
        scores = [doc.get("score") for doc in context_docs if isinstance(doc.get("score"), float)]
        score_bonus = min(sum(scores) / len(scores), 1.0) * 0.2 if scores else 0.0
        return round(min((context_score * 0.6 + answer_length_score * 0.2 + score_bonus), 1.0), 3)
