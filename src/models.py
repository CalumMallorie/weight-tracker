from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC
from typing import Dict, Any, Optional

db = SQLAlchemy()

class WeightCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    is_body_mass = db.Column(db.Boolean, default=False)  # Special case for body mass
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    entries = db.relationship('WeightEntry', backref='category', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"WeightCategory(id={self.id}, name={self.name}, is_body_mass={self.is_body_mass})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert category to dictionary for JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'is_body_mass': self.is_body_mass,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
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
        return f"WeightEntry(id={self.id}, weight={self.weight}{self.unit}{rep_str}, category={self.category.name})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON response"""
        return {
            'id': self.id,
            'weight': self.weight,
            'unit': self.unit,
            'reps': self.reps,
            'category_id': self.category_id,
            'category_name': self.category.name,
            'is_body_mass': self.category.is_body_mass,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
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