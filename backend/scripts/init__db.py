# File: backend/scripts/init_db.py
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = str(Path(__file__).parent.parent.absolute())
sys.path.append(backend_dir)

from database.models.lecture import Base
from database.session import engine, SessionLocal
from database.models.lecture import Lecture

def init_database():
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")

        # Test database by adding a sample lecture
        db = SessionLocal()
        try:
            # Check if we already have lectures
            existing_lecture = db.query(Lecture).first()
            
            if not existing_lecture:
                print("Adding sample lecture...")
                sample_lecture = Lecture(
                    title="Introduction to Programming",
                    content="""
                    Welcome to Programming!
                    
                    This is a sample lecture that introduces basic programming concepts.
                    Key topics include:
                    - Variables and Data Types
                    - Control Structures
                    - Functions
                    - Object-Oriented Programming
                    """
                )
                db.add(sample_lecture)
                db.commit()
                print("✓ Sample lecture added successfully!")
            else:
                print("✓ Database already contains lectures!")

        finally:
            db.close()
            
        print("\nDatabase initialization complete!")
        
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        raise

if __name__ == "__main__":
    init_database()