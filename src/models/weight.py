from datetime import datetime, UTC
from typing import Dict, Any, Optional

from . import db, format_date


class WeightCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    is_body_mass = db.Column(db.Boolean, default=False)  # Special case for body mass (just weight, no reps)
    is_body_weight_exercise = db.Column(db.Boolean, default=False)  # For body weight exercises (just reps, no weight)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    last_used_at = db.Column(db.DateTime, nullable=True)  # Track when the category was last used
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    entries = db.relationship('WeightEntry', backref='category', lazy=True, cascade="all, delete-orphan")
    
    # Ensure category names are unique per user, not globally
    __table_args__ = (db.UniqueConstraint('name', 'user_id', name='_category_name_user_uc'),)
    
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    notes = db.Column(db.Text, nullable=True)  # Optional notes field

    def __repr__(self) -> str:
        return f"WeightEntry(id={self.id}, weight={self.weight}{self.unit}, reps={self.reps}, category_id={self.category_id})"
    
    def calculate_volume(self) -> Optional[float]:
        """Calculate training volume (weight * reps)"""
        if self.reps is None or self.weight is None:
            return None
        return self.weight * self.reps
    
    def calculate_estimated_1rm(self) -> Optional[float]:
        """
        Calculate estimated 1 rep max using Epley formula: weight * (1 + reps/30)
        Only applicable for exercises with both weight and reps
        """
        if self.reps is None or self.weight is None or self.reps <= 0:
            return None
        
        # Don't calculate 1RM for body mass entries or very high rep counts
        if self.reps > 30 or self.category.is_body_mass:
            return None
            
        return self.weight * (1 + self.reps / 30)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON response"""
        return {
            'id': self.id,
            'weight': self.weight,
            'unit': self.unit,
            'reps': self.reps,
            'category_id': self.category_id,
            'user_id': self.user_id,
            'created_at': format_date(self.created_at),
            'notes': self.notes,
            'volume': self.calculate_volume(),
            'estimated_1rm': self.calculate_estimated_1rm()
        }