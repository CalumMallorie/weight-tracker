"""
Shared test fixtures and configuration for all tests.
"""

import pytest
from src.app import create_app
from src.models import db
from src import services


@pytest.fixture
def app():
    """Create test Flask app with in-memory database"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with app.app_context():
        db.create_all()
        # Create default categories
        services.create_default_category()
        
    yield app
    
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client for making HTTP requests"""
    return app.test_client()


@pytest.fixture 
def runner(app):
    """Create test runner for CLI commands"""
    return app.test_cli_runner()


@pytest.fixture
def sample_categories(app):
    """Create sample categories for testing"""
    with app.app_context():
        categories = {
            'body_mass': services.get_or_create_category("Body Mass", is_body_mass=True),
            'pushups': services.get_or_create_category("Push-ups"),
            'squats': services.get_or_create_category("Squats"),
            'benchpress': services.get_or_create_category("Bench Press")
        }
        
        # Set up body weight exercise
        if hasattr(categories['pushups'], 'is_body_weight_exercise'):
            categories['pushups'].is_body_weight_exercise = True
            db.session.commit()
        
        # Refresh to ensure they're properly bound to session
        for key in categories:
            db.session.refresh(categories[key])
            
        return categories 