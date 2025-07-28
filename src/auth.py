from flask import current_app
from flask_login import LoginManager, current_user
from functools import wraps
from typing import Optional

from src.models.user import User

# Initialize Flask-Login
login_manager = LoginManager()

def init_login(app):
    """Initialize Flask-Login with the Flask app"""
    login_manager.init_app(app)
    
    # Set login view and message
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Set session protection
    login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Load user by ID for Flask-Login"""
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

def login_required(func):
    """Custom login required decorator with better error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request, redirect, url_for, flash
        from flask_login import login_required as flask_login_required
        
        # Use Flask-Login's built-in decorator
        return flask_login_required(func)(*args, **kwargs)
    
    return wrapper

def anonymous_required(func):
    """Decorator to ensure user is NOT logged in (for login/register pages)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import redirect, url_for
        from flask_login import current_user
        
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        
        return func(*args, **kwargs)
    
    return wrapper

def get_current_user() -> Optional[User]:
    """Get the current authenticated user"""
    from flask_login import current_user
    
    if current_user.is_authenticated:
        return current_user
    return None

def is_authenticated() -> bool:
    """Check if the current user is authenticated"""
    from flask_login import current_user
    return current_user.is_authenticated

def require_user_ownership(user_id: int) -> bool:
    """Check if the current user owns the specified user_id"""
    if not is_authenticated():
        return False
    
    return current_user.id == user_id

def get_user_id() -> Optional[int]:
    """Get the current user's ID or None if not authenticated"""
    if is_authenticated():
        return current_user.id
    return None