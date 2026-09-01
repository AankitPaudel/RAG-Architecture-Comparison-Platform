# File: backend/scripts/load_and_verify.py
import sys
from pathlib import Path
import logging

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from database import SessionLocal, Lecture
from rag.processor import RAGProcessor
from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_lectures():
    """Load sample lectures into the system"""
    computer_science_lecture = """
    Introduction to Computer Science

    Computer Science is the study of computers and computational systems. It is a broad field that encompasses both theoretical and practical aspects of computing. Here are the key areas:

    1. Theoretical Computer Science:
    - Algorithms and Data Structures: The fundamental building blocks of software
    - Computation Theory: Understanding what can and cannot be computed
    - Programming Language Theory: How to design and implement programming languages

    2. Practical Applications:
    - Software Development: Creating applications and systems
    - Database Systems: Storing and retrieving information efficiently
    - Artificial Intelligence: Making computers simulate intelligent behavior
    - Computer Networks: Connecting systems and enabling communication

    3. Core Concepts:
    - Programming: Writing instructions for computers to follow
    - Data Structures: Organizing and storing data efficiently
    - Algorithms: Step-by-step procedures for solving problems
    - Software Engineering: Designing and building reliable software systems

    4. Impact on Society:
    - Automation: Replacing manual tasks with computerized systems
    - Digital Communication: Enabling instant global communication
    - Scientific Research: Processing complex calculations and simulations
    - Business Operations: Streamlining processes and improving efficiency

    Computer Science has become fundamental to modern society, driving innovation in fields from medicine to space exploration. It continues to evolve with new technologies and challenges.
    """

    try:
        # Initialize database session
        db = SessionLocal()
        
        # Clear existing lectures
        db.query(Lecture).delete()
        db.commit()
        
        # Create new lecture
        lecture = Lecture(
            title="Introduction to Computer Science",
            content=computer_science_lecture
        )
        db.add(lecture)
        db.commit()
        db.refresh(lecture)
        logger.info("✓ Lecture added to database")

        # Initialize RAG processor
        processor = RAGProcessor()
        
        # Process lecture
        processor.process_lecture(lecture.id, computer_science_lecture)
        logger.info("✓ Lecture processed for RAG system")

        # Verify data is in vector store
        results = processor.vector_store.similarity_search(
            "What is computer science?",
            k=1
        )
        logger.info(f"✓ Vector store test successful - found {len(results)} results")
        
        logger.info("Setup complete! You can now start asking questions.")
        
    except Exception as e:
        logger.error(f"Error in setup: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    load_lectures()