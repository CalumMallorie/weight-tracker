from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC

db = SQLAlchemy()

class WeightEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)  # 'kg' or 'lb'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"WeightEntry(id={self.id}, weight={self.weight}{self.unit}, created_at={self.created_at})"
    
    def to_dict(self) -> dict:
        """Convert entry to dictionary for JSON response"""
        return {
            'id': self.id,
            'weight': self.weight,
            'unit': self.unit,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } 