from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC
from typing import Dict, Any, Optional

db = SQLAlchemy()

def format_date(dt: datetime) -> str:
    """Format a datetime object consistently across the app"""
    if isinstance(dt, str):
        # Handle case where dt is already a string (shouldn't happen, but defensive)
        return dt.split(' ')[0] if ' ' in dt else dt
    return dt.strftime('%Y-%m-%d')

class WeightCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    is_body_mass = db.Column(db.Boolean, default=False)  # Special case for body mass (just weight, no reps)
    is_body_weight_exercise = db.Column(db.Boolean, default=False)  # For body weight exercises (just reps, no weight)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    last_used_at = db.Column(db.DateTime, nullable=True)  # Track when the category was last used
    entries = db.relationship('WeightEntry', backref='category', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"WeightCategory(id={self.id}, name={self.name}, is_body_mass={self.is_body_mass}, is_body_weight_exercise={self.is_body_weight_exercise})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert category to dictionary for JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'is_body_mass': self.is_body_mass,
            'is_body_weight_exercise': self.is_body_weight_exercise,
            'created_at': format_date(self.created_at),
            'last_used_at': format_date(self.last_used_at) if self.last_used_at else None
        }

class WeightEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)  # 'kg' or 'lb'
    reps = db.Column(db.Integer, nullable=True)  # Number of repetitions (null for body mass)
    category_id = db.Column(db.Integer, db.ForeignKey('weight_category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        rep_str = f", reps={self.reps}" if self.reps is not None else ""
        cat_str = f", category={self.category.name}" if self.category else ""
        return f"WeightEntry(id={self.id}, weight={self.weight}{self.unit}{rep_str}{cat_str}, created_at={format_date(self.created_at)})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON response"""
        result = {
            'id': self.id,
            'weight': self.weight,
            'unit': self.unit,
            'reps': self.reps,
            'created_at': format_date(self.created_at)
        }
        
        if self.category:
            result.update({
                'category_id': self.category_id,
                'category_name': self.category.name,
                'is_body_mass': self.category.is_body_mass
            })
        
        return result
    
    def calculate_volume(self) -> Optional[float]:
        """Calculate volume (weight × reps)"""
        if self.reps is None:
            return None
        return self.weight * self.reps
    
    def calculate_estimated_1rm(self) -> Optional[float]:
        """Calculate estimated 1RM using weight × (1 + reps / 30)"""
        if self.reps is None:
            return None
        return self.weight * (1 + self.reps / 30) 