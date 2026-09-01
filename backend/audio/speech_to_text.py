# File: backend/audio/speech_to_text.py
from faster_whisper import WhisperModel
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self):
        try:
            # Optimized model for speed and accuracy
            self.model = WhisperModel(
                "base.en",          # Switch to base.en for better balance
                device="cpu",       # Ensure it runs efficiently on CPU
                compute_type="int8" # Optimize for CPU with int8 precision
            )
            logger.info("Speech to text model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing speech to text model: {str(e)}")
            raise

    async def convert(self, audio_file: Path) -> str:
        """Convert speech to text"""
        try:
            logger.info(f"Processing audio file: {audio_file}")

            # Transcribe audio with faster parameters
            segments, _ = self.model.transcribe(
                str(audio_file),
                language="en",
                word_timestamps=False,
                vad_filter=True  # Use voice activity detection for cleaner results
            )

            # Join segments into a single text output
            text = " ".join([segment.text.strip() for segment in segments])

            logger.info(f"Successfully transcribed audio to: {text[:50]}...")
            return text

        except Exception as e:
            logger.error(f"Error in speech to text conversion: {str(e)}")
            raise
