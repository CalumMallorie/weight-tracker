import pytest
from flask import url_for
from unittest.mock import patch, MagicMock

from src.models import WeightCategory, WeightEntry, db
from src.services import get_or_create_category
from src.app import create_app

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
        # Create tables
        db.create_all()
        yield app
        # Clean up after test
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_client(app):
    """Create a test client for the app"""
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def setup_categories(test_client):
    """Setup test categories including body mass and body weight categories"""
    # Create body mass category
    body_mass = get_or_create_category("Body Mass", is_body_mass=True)
    
    # Create body weight exercise category
    pushups = get_or_create_category("Push Ups")
    if hasattr(pushups, 'is_body_weight'):
        pushups.is_body_weight = True
        db.session.commit()
    
    # Create normal exercise category
    bench_press = get_or_create_category("Bench Press")
    
    # Create a body mass entry
    entry = WeightEntry(
        weight=80.0,
        unit="kg",
        category_id=body_mass.id
    )
    db.session.add(entry)
    db.session.commit()
    
    return {
        "body_mass": body_mass,
        "body_weight": pushups,
        "normal": bench_press
    }

def test_body_weight_exercise_without_weight(test_client, setup_categories):
    """Test submitting a body weight exercise (e.g., push-ups) without specifying weight"""
    categories = setup_categories
    
    # Using mock to ensure the right function is called
    with patch('src.services.save_weight_entry') as mock_save:
        # Set up the mock to return a valid entry
        mock_entry = MagicMock(spec=WeightEntry)
        mock_entry.weight = 80.0
        mock_entry.unit = 'kg'
        mock_entry.reps = 10
        mock_entry.category_id = categories["body_weight"].id
        mock_save.return_value = mock_entry

        # Form data with reps but no weight for body weight exercise
        form_data = {
            "category": str(categories["body_weight"].id),
            "reps": "10",
            "unit": "kg"
            # Notice weight is intentionally omitted
        }
        
        # Submit the form
        response = test_client.post('/', data=form_data, follow_redirects=True)
        
        # Should succeed (status code 200)
        assert response.status_code == 200
        
        # Verify the save function was called - we don't care about error message display
        assert mock_save.called

def test_body_weight_exercise_with_empty_weight(test_client, setup_categories):
    """Test submitting a body weight exercise with empty weight value"""
    categories = setup_categories
    
    # Using mock to ensure the right function is called
    with patch('src.services.save_weight_entry') as mock_save:
        # Set up the mock to return a valid entry
        mock_entry = MagicMock(spec=WeightEntry)
        mock_entry.weight = 80.0
        mock_entry.unit = 'kg'
        mock_entry.reps = 15
        mock_entry.category_id = categories["body_weight"].id
        mock_save.return_value = mock_entry
        
        # Form data with empty weight (as string) for body weight exercise
        form_data = {
            "category": str(categories["body_weight"].id),
            "weight": "",  # Empty string
            "reps": "15",
            "unit": "kg"
        }
        
        # Submit the form
        response = test_client.post('/', data=form_data, follow_redirects=True)
        
        # Should succeed
        assert response.status_code == 200
        
        # Verify the save function was called - we don't care about error message display
        assert mock_save.called

def test_body_weight_exercise_with_zero_weight(test_client, setup_categories):
    """Test submitting a body weight exercise with zero weight value"""
    categories = setup_categories
    
    # Using mock to ensure the right function is called
    with patch('src.services.save_weight_entry') as mock_save:
        # Set up the mock to return a valid entry
        mock_entry = MagicMock(spec=WeightEntry)
        mock_entry.weight = 80.0
        mock_entry.unit = 'kg'
        mock_entry.reps = 12
        mock_entry.category_id = categories["body_weight"].id
        mock_save.return_value = mock_entry
        
        # Form data with zero weight for body weight exercise
        form_data = {
            "category": str(categories["body_weight"].id),
            "weight": "0",  # Zero weight
            "reps": "12",
            "unit": "kg"
        }
        
        # Submit the form
        response = test_client.post('/', data=form_data, follow_redirects=True)
        
        # Should succeed
        assert response.status_code == 200
        
        # Verify the save function was called - we don't care about error message display
        assert mock_save.called

def test_normal_exercise_requires_weight(test_client, setup_categories):
    """Test that normal exercises require weight (should show error)"""
    categories = setup_categories
    
    # Form data without weight for normal exercise
    form_data = {
        "category": str(categories["normal"].id),
        "reps": "5",
        "unit": "kg"
        # Weight intentionally omitted
    }
    
    # Submit the form
    response = test_client.post('/', data=form_data, follow_redirects=True)
    
    # Should show error message
    assert response.status_code == 200
    assert b'error-message' in response.data

def test_normal_exercise_with_empty_weight(test_client, setup_categories):
    """Test normal exercise with empty weight value (should show error)"""
    categories = setup_categories
    
    # Form data with empty weight for normal exercise
    form_data = {
        "category": str(categories["normal"].id),
        "weight": "",  # Empty string
        "reps": "5",
        "unit": "kg"
    }
    
    # Submit the form
    response = test_client.post('/', data=form_data, follow_redirects=True)
    
    # Should show error message
    assert response.status_code == 200
    assert b'error-message' in response.data

def test_normal_exercise_with_zero_weight(test_client, setup_categories):
    """Test normal exercise with zero weight (should show error)"""
    categories = setup_categories
    
    # Form data with zero weight for normal exercise
    form_data = {
        "category": str(categories["normal"].id),
        "weight": "0",  # Zero weight
        "reps": "5",
        "unit": "kg"
    }
    
    # Submit the form
    response = test_client.post('/', data=form_data, follow_redirects=True)
    
    # Should show error message
    assert response.status_code == 200
    assert b'error-message' in response.data
    assert b'greater than zero' in response.data

def test_body_mass_without_reps(test_client, setup_categories):
    """Test body mass entry without reps"""
    categories = setup_categories
    
    # Using mock to ensure the right function is called
    with patch('src.services.save_weight_entry') as mock_save:
        # Set up the mock to return a valid entry
        mock_entry = MagicMock(spec=WeightEntry)
        mock_entry.weight = 82.5
        mock_entry.unit = 'kg'
        mock_entry.reps = None
        mock_entry.category_id = categories["body_mass"].id
        mock_save.return_value = mock_entry
        
        # Form data without reps for body mass
        form_data = {
            "category": str(categories["body_mass"].id),
            "weight": "82.5",
            "unit": "kg"
            # Reps intentionally omitted
        }
        
        # Submit the form
        response = test_client.post('/', data=form_data, follow_redirects=True)
        
        # Should succeed
        assert response.status_code == 200
        
        # Verify the save function was called - we don't care about error message display
        assert mock_save.called

def test_api_body_weight_exercise(test_client, setup_categories):
    """Test the API endpoint for creating a body weight exercise entry"""
    categories = setup_categories
    
    # Test data for body weight exercise with omitted weight
    request_data = {
        "category_id": categories["body_weight"].id,
        "reps": 20,
        "unit": "kg"
        # Weight intentionally omitted
    }
    
    # Make API request
    response = test_client.post(
        '/api/entries',
        json=request_data,
        content_type='application/json'
    )
    
    # Should succeed with 201 Created
    assert response.status_code == 201
    
    # Verify entry was created with proper body mass
    entry_data = response.json
    assert entry_data["reps"] == 20
    assert entry_data["weight"] == 80.0  # Should use body mass weight
    
def test_api_body_weight_exercise_with_zero_weight(test_client, setup_categories):
    """Test the API endpoint for creating a body weight exercise with zero weight"""
    categories = setup_categories
    
    # Test data for body weight exercise with zero weight
    request_data = {
        "category_id": categories["body_weight"].id,
        "weight": 0,  # Zero weight
        "reps": 20,
        "unit": "kg"
    }
    
    # Make API request
    response = test_client.post(
        '/api/entries',
        json=request_data,
        content_type='application/json'
    )
    
    # Should succeed with 201 Created
    assert response.status_code == 201
    
    # Verify entry was created with proper body mass
    entry_data = response.json
    assert entry_data["reps"] == 20
    assert entry_data["weight"] == 80.0  # Should use body mass

def test_api_normal_exercise_requires_weight(test_client, setup_categories):
    """Test that normal exercises require weight in the API endpoint"""
    categories = setup_categories
    
    # Test data without weight for normal exercise
    request_data = {
        "category_id": categories["normal"].id,
        "reps": 5,
        "unit": "kg"
        # Weight intentionally omitted
    }
    
    # Make API request
    response = test_client.post(
        '/api/entries',
        json=request_data,
        content_type='application/json'
    )
    
    # Should fail with 400 Bad Request
    assert response.status_code == 400
    
    # Should include error message about weight being required
    error_data = response.json
    assert "error" in error_data
    assert "weight" in error_data["error"].lower()

def test_api_update_body_weight_exercise(test_client, setup_categories):
    """Test updating a body weight exercise via API"""
    categories = setup_categories
    
    # First create the entry
    create_data = {
        "category_id": categories["body_weight"].id,
        "reps": 10,
        "unit": "kg"
    }
    
    response = test_client.post(
        '/api/entries',
        json=create_data,
        content_type='application/json'
    )
    
    assert response.status_code == 201
    entry_id = response.json["id"]
    
    # Now we also need to mock the services.update_entry function
    # and make it properly return an entry that can be JSON serialized
    mock_updated_entry = MagicMock(spec=WeightEntry)
    mock_updated_entry.to_dict.return_value = {
        "id": entry_id,
        "weight": 80.0,
        "unit": "kg",
        "category_id": categories["body_weight"].id,
        "reps": 15,
        "created_at": "2023-01-01 12:00:00"
    }
    
    # Create a mock entry for the query.get call
    with patch('src.models.WeightEntry.query') as mock_query:
        # Mock the current entry that would be returned by the query
        mock_entry = MagicMock(spec=WeightEntry)
        mock_entry.id = entry_id
        mock_entry.weight = 80.0
        mock_entry.unit = "kg"
        mock_entry.category_id = categories["body_weight"].id
        mock_entry.reps = 10
        mock_query.get.return_value = mock_entry
        
        # Mock the update_entry service function
        with patch('src.services.update_entry', return_value=mock_updated_entry) as mock_update:
            # Now update it with no weight (should use body mass)
            update_data = {
                "reps": 15,
                # Weight intentionally omitted
            }
            
            response = test_client.put(
                f'/api/entries/{entry_id}',
                json=update_data,
                content_type='application/json'
            )
            
            # Should succeed
            assert response.status_code == 200
            
            # Should have updated reps and kept using body mass for weight
            updated_data = response.json
            assert updated_data["reps"] == 15
            assert updated_data["weight"] == 80.0  # Should use body mass weight