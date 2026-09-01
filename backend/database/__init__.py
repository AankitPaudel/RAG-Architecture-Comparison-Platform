# File: backend/database/__init__.py
from .session import SessionLocal, engine, get_db, init_db, test_db_connection
from .models.lecture import Base, Lecture

# Export these for easy access from other modules
__all__ = [
    'SessionLocal',
    'engine',
    'get_db',
    'init_db',
    'test_db_connection',
    'Base',
    'Lecture'
]