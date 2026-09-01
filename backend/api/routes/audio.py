# File: backend/api/routes/audio.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import shutil
import os
import time
from audio.text_to_speech import TextToSpeech
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
text_to_speech = TextToSpeech()
speech_to_text = None

# Ensure audio directory exists
AUDIO_DIR = Path("data/audio")
TEMP_DIR = AUDIO_DIR / "temp"
RESPONSE_DIR = AUDIO_DIR / "responses"

# Create necessary directories
for directory in [AUDIO_DIR, TEMP_DIR, RESPONSE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def cleanup_old_files(directory: Path, max_age_hours: int = 1):
    """Clean up old files from directory"""
    try:
        current_time = time.time()
        for file in directory.glob("*.*"):
            if (current_time - file.stat().st_mtime) > (max_age_hours * 3600):
                try:
                    file.unlink()
                    logger.info(f"Cleaned up old file: {file}")
                except Exception as e:
                    logger.error(f"Error deleting file {file}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def remove_file(file_path: Path):
    """Remove a file if it exists"""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Removed file: {file_path}")
    except Exception as e:
        logger.error(f"Error removing file {file_path}: {e}")

@router.post("/speech-to-text")
async def convert_speech_to_text(background_tasks: BackgroundTasks, audio: UploadFile = File(...)):
    """Convert speech to text"""
    logger.info(f"Received audio file for conversion: {audio.filename}")
    
    if not audio.filename.endswith(('.wav', '.mp3', '.ogg', '.m4a')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Please use WAV, MP3, OGG, or M4A files."
        )
    
    temp_file = TEMP_DIR / f"input_{audio.filename}"
    
    try:
        global speech_to_text
        if speech_to_text is None:
            try:
                from audio.speech_to_text import SpeechToText
                speech_to_text = SpeechToText()
            except ModuleNotFoundError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Speech-to-text is not installed in this Python environment: {str(e)}"
                )

        # Save uploaded file
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Convert to text
        text = await speech_to_text.convert(temp_file)
        logger.info(f"Successfully converted audio to text: {text[:50]}...")
        
        # Schedule cleanup
        background_tasks.add_task(remove_file, temp_file)
        
        return JSONResponse(
            content={
                "text": text,
                "status": "success"
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        # Clean up on error
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )

@router.post("/text-to-speech")
async def convert_text_to_speech(text: str, background_tasks: BackgroundTasks):
    """Convert text to speech"""
    logger.info("Received text for speech conversion")
    
    if not text or len(text.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Text content is required"
        )
    
    try:
        # Generate audio file
        audio_file = await text_to_speech.convert(text)
        
        if not audio_file.exists():
            raise HTTPException(
                status_code=500,
                detail="Failed to generate audio file"
            )
        
        # Schedule cleanup for later
        background_tasks.add_task(remove_file, audio_file)
        
        return FileResponse(
            path=audio_file,
            media_type="audio/mpeg",
            filename="response.mp3"
        )
        
    except Exception as e:
        logger.error(f"Error converting text to speech: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error converting text to speech: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_files():
    """Clean up old temporary files"""
    try:
        cleanup_old_files(TEMP_DIR)
        cleanup_old_files(RESPONSE_DIR)
        return {"status": "success", "message": "Cleanup completed"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )
