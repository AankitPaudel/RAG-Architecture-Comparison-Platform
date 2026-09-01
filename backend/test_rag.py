# test_rag.py
import requests

# Your lecture content
lecture_content = """
[Your full lecture text here]
Example:
Introduction to Machine Learning
Machine learning is a subset of artificial intelligence...
Key concepts include:
1. Supervised Learning
2. Unsupervised Learning
3. Reinforcement Learning
...
"""

# Add lecture to the system
response = requests.post(
    "http://localhost:8000/api/lectures/",
    json={
        "title": "Introduction to Machine Learning",
        "content": lecture_content
    }
)

print("Lecture Added:", response.json())

# Test RAG with a question
test_question = "What are the key concepts in machine learning?"
response = requests.post(
    "http://localhost:8000/api/qa/ask",
    json={
        "question": test_question
    }
)

print("\nQuestion:", test_question)
print("Answer:", response.json()["answer"])
print("Sources:", response.json()["sources"])