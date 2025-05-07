import os
import sys
import pytest

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a directory for the tests if it doesn't exist
os.makedirs(os.path.dirname(__file__), exist_ok=True)

# Create an empty __init__.py file in the tests directory
with open(os.path.join(os.path.dirname(__file__), '__init__.py'), 'a'):
    pass

@pytest.fixture
def test_client(app):
    """Create a test client for the app"""
    with app.test_client() as client:
        with app.app_context():
            yield client 