"""
Tests for API endpoints and JSON responses.

Tests REST API functionality, data validation, and error handling.
Includes specific tests for issues like body weight entries saving as zero via API.
"""

import pytest
import json
from datetime import datetime, timedelta, UTC
from src.models import db, WeightEntry
from src import services


# Mark all tests in this file as unit tests (fast)
pytestmark = pytest.mark.unit


class TestEntriesAPI:
    """Test entries API endpoints"""
    
    def test_get_entries_api(self, app, client, sample_categories):
        """GET /api/entries should return entries as JSON"""
        with app.app_context():
            # Add test entries
            services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8)
            services.save_weight_entry(105.0, 'kg', sample_categories['benchpress'].id, 10)
            
            response = client.get('/api/entries')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) >= 2
    
    def test_create_entry_via_api(self, app, client, sample_categories):
        """POST /api/entries should create new entry"""
        with app.app_context():
            entry_data = {
                'weight': 110.0,
                'unit': 'kg',
                'category_id': sample_categories['benchpress'].id,
                'reps': 12
            }
            
            response = client.post('/api/entries', 
                                 json=entry_data,
                                 content_type='application/json')
            assert response.status_code == 201
            
            # Verify entry was created
            data = json.loads(response.data)
            assert data['weight'] == 110.0
            assert data['unit'] == 'kg'
            assert data['reps'] == 12
    
    def test_create_body_weight_entry_via_api_uses_body_mass(self, app, client, sample_categories):
        """API body weight entries should use body mass, not zero"""
        with app.app_context():
            # Add body mass entry first
            services.save_weight_entry(78.0, 'kg', sample_categories['body_mass'].id, None)
            
            # Create body weight exercise via API
            entry_data = {
                'weight': 0,  # API might send 0 for body weight exercises
                'unit': 'kg',
                'category_id': sample_categories['pushups'].id,
                'reps': 15
            }
            
            response = client.post('/api/entries',
                                 json=entry_data,
                                 content_type='application/json')
            assert response.status_code == 201
            
            # Should use body mass weight, not zero
            data = json.loads(response.data)
            assert data['weight'] == 78.0, "API should save body mass weight, not zero"
            assert data['reps'] == 15
    
    def test_create_body_mass_entry_via_api(self, app, client, sample_categories):
        """API body mass entries should save exact weight"""
        with app.app_context():
            entry_data = {
                'weight': 82.5,
                'unit': 'kg',
                'category_id': sample_categories['body_mass'].id,
                'reps': None
            }
            
            response = client.post('/api/entries',
                                 json=entry_data,
                                 content_type='application/json')
            assert response.status_code == 201
            
            data = json.loads(response.data)
            assert data['weight'] == 82.5
            assert data['reps'] is None
    
    def test_create_entry_missing_required_fields(self, app, client):
        """API should validate required fields"""
        with app.app_context():
            # Missing unit and category_id
            entry_data = {
                'weight': 100.0,
                'reps': 8
            }
            
            response = client.post('/api/entries',
                                 json=entry_data,
                                 content_type='application/json')
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_create_entry_invalid_category(self, app, client):
        """API should handle invalid category IDs"""
        with app.app_context():
            entry_data = {
                'weight': 100.0,
                'unit': 'kg',
                'category_id': 999,  # Non-existent category
                'reps': 8
            }
            
            response = client.post('/api/entries',
                                 json=entry_data,
                                 content_type='application/json')
            assert response.status_code == 400
    
    def test_update_entry_via_api(self, app, client, sample_categories):
        """PUT /api/entries/<id> should update entry"""
        with app.app_context():
            # Create initial entry
            entry = services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8)
            
            update_data = {
                'weight': 105.0,
                'unit': 'kg',
                'category_id': sample_categories['benchpress'].id,
                'reps': 10
            }
            
            response = client.put(f'/api/entries/{entry.id}',
                                json=update_data,
                                content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['weight'] == 105.0
            assert data['reps'] == 10
    
    def test_update_body_weight_entry_via_api_uses_current_body_mass(self, app, client, sample_categories):
        """Updating body weight exercise via API should use current body mass"""
        with app.app_context():
            # Create initial body mass
            services.save_weight_entry(70.0, 'kg', sample_categories['body_mass'].id, None)
            
            # Create body weight exercise
            entry = services.save_weight_entry(0, 'kg', sample_categories['pushups'].id, 10)
            assert entry.weight == 70.0
            
            # Update body mass
            services.save_weight_entry(75.0, 'kg', sample_categories['body_mass'].id, None)
            
            # Update the body weight exercise via API
            update_data = {
                'weight': 0,
                'unit': 'kg',
                'category_id': sample_categories['pushups'].id,
                'reps': 12
            }
            
            response = client.put(f'/api/entries/{entry.id}',
                                json=update_data,
                                content_type='application/json')
            assert response.status_code == 200
            
            # Should use new body mass weight
            data = json.loads(response.data)
            assert data['weight'] == 75.0
            assert data['reps'] == 12
    
    def test_update_nonexistent_entry(self, app, client):
        """Updating non-existent entry should return 404"""
        with app.app_context():
            update_data = {
                'weight': 100.0,
                'unit': 'kg',
                'category_id': 1,
                'reps': 8
            }
            
            response = client.put('/api/entries/999',
                                json=update_data,
                                content_type='application/json')
            assert response.status_code == 404
    
    def test_delete_entry_via_api(self, app, client, sample_categories):
        """DELETE /api/entries/<id> should delete entry"""
        with app.app_context():
            # Create entry to delete
            entry = services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8)
            
            response = client.delete(f'/api/entries/{entry.id}')
            assert response.status_code == 200
            
            # Verify entry was deleted
            deleted_entry = WeightEntry.query.get(entry.id)
            assert deleted_entry is None
    
    def test_delete_nonexistent_entry(self, app, client):
        """Deleting non-existent entry should return 404"""
        with app.app_context():
            response = client.delete('/api/entries/999')
            assert response.status_code == 404


class TestCategoriesAPI:
    """Test categories API endpoints"""
    
    def test_get_categories_api(self, app, client, sample_categories):
        """GET /api/categories should return categories as JSON"""
        with app.app_context():
            response = client.get('/api/categories')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) >= 3  # At least the sample categories
    
    def test_create_category_via_api(self, app, client):
        """POST /api/categories should create new category"""
        with app.app_context():
            category_data = {
                'name': 'Test Exercise',
                'is_body_weight_exercise': False
            }
            
            response = client.post('/api/categories',
                                 json=category_data,
                                 content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['name'] == 'Test Exercise'
    
    def test_create_category_missing_name(self, app, client):
        """Creating category without name should return error"""
        with app.app_context():
            category_data = {
                'is_body_weight_exercise': False
            }
            
            response = client.post('/api/categories',
                                 json=category_data,
                                 content_type='application/json')
            assert response.status_code == 400
    
    def test_delete_category_via_api(self, app, client, sample_categories):
        """DELETE /api/categories/<id> should delete category"""
        with app.app_context():
            # Use squats category (should have no entries)
            category_id = sample_categories['squats'].id
            
            response = client.delete(f'/api/categories/{category_id}')
            assert response.status_code == 200


class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_invalid_json_returns_400(self, app, client):
        """Invalid JSON should return 400 error"""
        with app.app_context():
            response = client.post('/api/entries',
                                 data='invalid json',
                                 content_type='application/json')
            assert response.status_code == 400
    
    def test_missing_content_type_header(self, app, client, sample_categories):
        """Missing content-type header should be handled"""
        with app.app_context():
            entry_data = {
                'weight': 100.0,
                'unit': 'kg',
                'category_id': sample_categories['benchpress'].id,
                'reps': 8
            }
            
            # Send JSON without proper content-type header
            response = client.post('/api/entries',
                                 data=json.dumps(entry_data))
            # Should handle gracefully (might return 400 or work depending on Flask version)
            assert response.status_code in [200, 201, 400]


class TestProcessingTypesAPI:
    """Test processing types API endpoint"""
    
    def test_get_processing_types(self, app, client):
        """GET /api/processing-types should return available processing options"""
        with app.app_context():
            response = client.get('/api/processing-types')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
            assert any(item['id'] == 'none' for item in data)  # Should include basic processing types 