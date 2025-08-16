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
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key-for-sessions'
    })
    
    with app.app_context():
        db.create_all()
        # Create default user for testing
        from src.models import User
        default_user = User.create_default_user()
        db.session.add(default_user)
        db.session.commit()
        
        # Create default categories
        services.create_default_category(user_id=default_user.id)
        
    yield app
    
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client for making HTTP requests"""
    return app.test_client()


@pytest.fixture
def default_user(app):
    """Get the default user for testing"""
    with app.app_context():
        from src.models import User
        return User.query.filter_by(username='default').first()


@pytest.fixture 
def authenticated_client(app, client, default_user):
    """Create authenticated client - authentication is bypassed in test mode"""
    # In test mode, the login_required decorator is bypassed
    # so we just return the regular client
    return client


@pytest.fixture 
def runner(app):
    """Create test runner for CLI commands"""
    return app.test_cli_runner()


@pytest.fixture
def sample_categories(app):
    """Create sample categories for testing"""
    with app.app_context():
        # Get the default user created in app fixture
        from src.models import User
        default_user = User.query.filter_by(username='default').first()
        
        categories = {
            'body_mass': services.get_or_create_category("Body Mass", default_user.id, is_body_mass=True),
            'pushups': services.get_or_create_category("Push-ups", default_user.id),
            'squats': services.get_or_create_category("Squats", default_user.id),
            'benchpress': services.get_or_create_category("Bench Press", default_user.id)
        }
        
        # Set up body weight exercise
        if hasattr(categories['pushups'], 'is_body_weight_exercise'):
            categories['pushups'].is_body_weight_exercise = True
            db.session.commit()
        
        # Refresh to ensure they're properly bound to session
        for key in categories:
            db.session.refresh(categories[key])
            
        return categories 