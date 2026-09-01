# File: backend/app/dependencies.py
from typing import Generator
from database.session import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()