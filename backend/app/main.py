# File: backend/app/main.py
import sys
from pathlib import Path
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import audio, compare, evaluation, qa, lectures

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="RAG Architecture Comparison API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up audio directories
AUDIO_DIR = Path("data/audio")
RESPONSES_DIR = AUDIO_DIR / "responses"
TEMP_DIR = AUDIO_DIR / "temp"

# Create necessary directories
for directory in [AUDIO_DIR, RESPONSES_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Mount static directory for serving audio files
app.mount(
    "/api/audio/responses", 
    StaticFiles(directory=str(RESPONSES_DIR), check_dir=True), 
    name="audio_responses"
)

# Include routers
app.include_router(qa.router, prefix="/api/qa", tags=["qa"])
app.include_router(compare.router, prefix="/api", tags=["compare"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(lectures.router, prefix="/api/lectures", tags=["lectures"])

@app.get("/")
async def root():
    return {
        "message": "RAG Architecture Comparison API is running",
        "status": "ok"
    }

@app.on_event("startup")
async def startup_event():
    # Log application startup and directory setup
    logger.info("Creating required directories...")
    logger.info(f"Audio responses directory: {RESPONSES_DIR}")
    logger.info(f"Temporary audio directory: {TEMP_DIR}")
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup on shutdown
    logger.info("Application shutting down...")
    try:
        # Cleanup temporary files
        for file in TEMP_DIR.glob("*.*"):
            try:
                file.unlink()
            except Exception as e:
                logger.error(f"Error deleting temp file {file}: {e}")
        
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}")
