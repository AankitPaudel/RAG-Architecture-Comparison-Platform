# File: backend/audio/text_to_speech.py
import requests
from pathlib import Path
import uuid
import logging
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key and Voice ID from environment variables
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

class TextToSpeech:
    def __init__(self):
        """Initialize TextToSpeech with proper directory structure"""
        self.audio_dir = Path("data/audio")
        self.responses_dir = self.audio_dir / "responses"
        self.temp_dir = self.audio_dir / "temp"
        
        # Create necessary directories
        for directory in [self.audio_dir, self.responses_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.info("TextToSpeech initialized with directories setup")

    def _generate_unique_filename(self) -> str:
        """Generate a unique filename for the audio response"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"response_{timestamp}_{unique_id}.mp3"

    async def convert(self, text: str) -> Path:
        """Convert text to speech using ElevenLabs API"""
        logger.info("Converting text to speech using ElevenLabs API...")

        if not ELEVENLABS_API_KEY or not VOICE_ID:
            logger.error("ElevenLabs API key or Voice ID is missing.")
            raise ValueError("ElevenLabs API key or Voice ID is missing.")

        # Generate unique filename
        filename = self._generate_unique_filename()
        file_path = self.responses_dir / filename

        # ElevenLabs API endpoint
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

        # Request payload with optimized settings
        payload = {
            "text": text,
            "voice_settings": {
                "stability": 0.4,         # Lower for faster output
                "similarity_boost": 0.7,  # Balance quality and speed
                "style": 0.5
            }
        }

        # Request headers
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }

        # API request with faster streaming
        try:
            with requests.post(url, json=payload, headers=headers, stream=True) as response:
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=4096):
                            if chunk:
                                f.write(chunk)

                    logger.info(f"Successfully created audio file: {filename}")
                    return file_path

                else:
                    logger.error(f"Failed to generate speech. Status: {response.status_code}, Error: {response.text}")
                    raise Exception(f"Failed to generate speech: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")

    async def cleanup_old_files(self, max_age_hours: int = 1):
        """Clean up old audio files from temp and responses directories"""
        try:
            current_time = time.time()
            max_age = max_age_hours * 3600
            
            # Clean temp directory
            for file in self.temp_dir.glob("*.mp3"):
                if (current_time - file.stat().st_mtime) > max_age:
                    file.unlink()
                    logger.info(f"Cleaned up temp file: {file}")
            
            # Clean responses directory
            for file in self.responses_dir.glob("*.mp3"):
                if (current_time - file.stat().st_mtime) > max_age:
                    file.unlink()
                    logger.info(f"Cleaned up response file: {file}")
                        
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    async def remove_file(self, file_path: Path):
        """Remove a specific file"""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Removed file: {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")
