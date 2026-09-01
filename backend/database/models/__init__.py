# File: backend/database/models/__init__.py
from .lecture import Lecture, Base

# Export these for easy access
__all__ = [
    'Lecture',
    'Base'
]