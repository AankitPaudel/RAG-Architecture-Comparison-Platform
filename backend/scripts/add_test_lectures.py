# File: backend/scripts/add_test_lecture.py
from pathlib import Path


def add_test_lecture():
    test_lecture = """
    Introduction to Computer Science

    Computer Science is the study of computation and information.
    Computers are tools that help us solve complex problems.
    
    Key Concepts:
    1. Algorithms
    2. Data Structures
    3. Programming Languages
    
    This introduction covers the basic concepts that all computer scientists should know.
    """
    
    # Create lectures directory if it doesn't exist
    lecture_dir = Path('data/lectures')
    lecture_dir.mkdir(parents=True, exist_ok=True)
    
    # Save test lecture
    with open(lecture_dir / 'test_lecture.txt', 'w') as f:
        f.write(test_lecture)
    
    print("Test lecture added successfully!")

if __name__ == "__main__":
    add_test_lecture()