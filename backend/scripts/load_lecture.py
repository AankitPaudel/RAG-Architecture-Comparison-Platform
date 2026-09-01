# File: backend/scripts/load_lecture.py
from pathlib import Path
import sys
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from database import SessionLocal, Lecture
from rag.processor import RAGProcessor
from app.config import settings

def load_sample_lecture():
    """Load a sample lecture into the system"""
    # Sample lecture content
    computer_science_lecture = """
    Introduction to Computer Science

    Computer Science is the study of computers and computational systems. It is a broad field that encompasses both theoretical and practical aspects of computing. Here are the key areas:

    1. Theoretical Computer Science:
    - Algorithms and Data Structures
    - Computation Theory
    - Programming Language Theory

    2. Practical Applications:
    - Software Development
    - Database Systems
    - Artificial Intelligence
    - Computer Networks

    3. Core Concepts:
    - Programming is the process of creating sets of instructions for computers to follow
    - Data structures are ways of organizing and storing data
    - Algorithms are step-by-step procedures for solving problems
    - Software engineering involves designing and building reliable software systems

    4. Impact on Society:
    - Automation of tasks
    - Digital communication
    - Scientific research
    - Business operations

    Computer Science has become fundamental to modern society, driving innovation in fields from medicine to space exploration.
    """

    try:
        # Initialize database session
        db = SessionLocal()
        
        # Create lecture in database
        lecture = Lecture(
            title="Introduction to Computer Science",
            content=computer_science_lecture
        )
        db.add(lecture)
        db.commit()
        db.refresh(lecture)
        print("✓ Lecture added to database")

        # Initialize RAG processor
        processor = RAGProcessor()
        
        # Process lecture for RAG system
        processor.process_lecture(lecture.id, computer_science_lecture)
        print("✓ Lecture processed for RAG system")
        
        print("\nLecture content loaded successfully!")
        
    except Exception as e:
        print(f"Error loading lecture: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    load_sample_lecture()