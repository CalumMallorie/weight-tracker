"""
Models package for the Weight Tracker application.

This package contains all database models including User and WeightEntry models.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def format_date(dt: datetime) -> str:
    """Format a datetime object consistently across the app"""
    if isinstance(dt, str):
        # Handle case where dt is already a string (shouldn't happen, but defensive)
        return dt.split(' ')[0] if ' ' in dt else dt
    return dt.strftime('%Y-%m-%d')

# Import models after db is defined to avoid circular imports
from .user import User
from .weight import WeightCategory, WeightEntry

__all__ = ['db', 'format_date', 'User', 'WeightCategory', 'WeightEntry']