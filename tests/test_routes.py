import pytest
from flask import url_for
from unittest.mock import patch, MagicMock
import json

from src.app import create_app
from src.models import WeightEntry

@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    
    # Create test context
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app"""
    return app.test_cli_runner()

def test_index_get(client):
    """Test GET request to index page"""
    with patch('src.services.get_entries_by_time_window', return_value=[]) as mock_get:
        with patch('src.services.create_weight_plot', return_value=None) as mock_plot:
            response = client.get('/')
            
            assert response.status_code == 200
            assert b'Weight Tracker' in response.data
            assert mock_get.called
            assert mock_plot.called

def test_index_post_valid(client):
    """Test POST request to index page with valid data"""
    with patch('src.services.save_weight_entry') as mock_save:
        response = client.post('/', data={
            'weight': '75.5',
            'unit': 'kg',
            'notes': 'Test notes'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert mock_save.called
        mock_save.assert_called_with(75.5, 'kg', 'Test notes')

def test_index_post_invalid(client):
    """Test POST request to index page with invalid data"""
    with patch('src.services.get_entries_by_time_window', return_value=[]) as mock_get:
        with patch('src.services.create_weight_plot', return_value=None) as mock_plot:
            response = client.post('/', data={
                'weight': 'invalid',
                'unit': 'kg',
                'notes': 'Test notes'
            })
            
            assert response.status_code == 200
            assert b'Please enter a valid weight number' in response.data
            assert mock_get.called
            assert mock_plot.called

def test_entries_page(client):
    """Test the entries management page"""
    with patch('src.services.get_all_entries', return_value=[]) as mock_get:
        response = client.get('/entries')
        
        assert response.status_code == 200
        assert b'Manage Weight Entries' in response.data
        assert mock_get.called

def test_api_entries_get(client):
    """Test the API endpoint for getting entries"""
    mock_entry = MagicMock(spec=WeightEntry)
    mock_entry.to_dict.return_value = {
        'id': 1,
        'weight': 75.5,
        'unit': 'kg',
        'notes': 'Test notes',
        'created_at': '2023-01-01 12:00:00'
    }
    
    with patch('src.services.get_all_entries', return_value=[mock_entry]) as mock_get:
        response = client.get('/api/entries')
        
        assert response.status_code == 200
        assert mock_get.called
        assert len(response.json) == 1
        assert response.json[0]['id'] == 1
        assert response.json[0]['weight'] == 75.5
        assert response.json[0]['unit'] == 'kg'

def test_api_delete_entry(client):
    """Test the API endpoint for deleting an entry"""
    with patch('src.services.delete_entry', return_value=True) as mock_delete:
        response = client.delete('/api/entries/1')
        
        assert response.status_code == 200
        assert mock_delete.called
        assert response.json['success'] is True 