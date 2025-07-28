from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
from typing import Dict, Any, Optional
import secrets

from src.models import db, format_date

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Password reset functionality
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    weight_entries = db.relationship('WeightEntry', backref='user', lazy=True, cascade="all, delete-orphan")
    weight_categories = db.relationship('WeightCategory', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, email={self.email}, active={self.is_active})"
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
        self.updated_at = datetime.now(UTC)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self) -> str:
        """Generate a secure reset token for password reset"""
        self.reset_token = secrets.token_urlsafe(32)
        # Token expires in 1 hour
        self.reset_token_expires = datetime.now(UTC).replace(microsecond=0) + datetime.timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token: str) -> bool:
        """Verify if the reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        
        if token != self.reset_token:
            return False
        
        if datetime.now(UTC) > self.reset_token_expires:
            # Token expired, clear it
            self.reset_token = None
            self.reset_token_expires = None
            return False
        
        return True
    
    def clear_reset_token(self) -> None:
        """Clear the reset token after successful password reset"""
        self.reset_token = None
        self.reset_token_expires = None
    
    def update_last_login(self) -> None:
        """Update the last login timestamp"""
        self.last_login = datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for JSON response (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': format_date(self.created_at),
            'updated_at': format_date(self.updated_at),
            'is_active': self.is_active,
            'last_login': format_date(self.last_login) if self.last_login else None
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        from src.models import WeightEntry, WeightCategory
        
        total_entries = WeightEntry.query.filter_by(user_id=self.id).count()
        total_categories = WeightCategory.query.filter_by(user_id=self.id).count()
        
        # Get latest entry date
        latest_entry = WeightEntry.query.filter_by(user_id=self.id).order_by(WeightEntry.created_at.desc()).first()
        latest_entry_date = format_date(latest_entry.created_at) if latest_entry else None
        
        return {
            'total_entries': total_entries,
            'total_categories': total_categories,
            'latest_entry_date': latest_entry_date,
            'member_since': format_date(self.created_at)
        }
    
    @classmethod
    def create_default_user(cls) -> 'User':
        """Create the default user for migration purposes"""
        default_user = cls(
            username='default',
            email='default@example.com',
            is_active=True
        )
        default_user.set_password('changeme123')  # Default password that should be changed
        return default_user
    
    @classmethod
    def find_by_username_or_email(cls, login: str) -> Optional['User']:
        """Find user by username or email"""
        return cls.query.filter(
            (cls.username == login) | (cls.email == login)
        ).first()