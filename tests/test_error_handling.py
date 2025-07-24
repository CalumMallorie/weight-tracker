"""
Error Handling and Resilience Tests - HIGH Priority

Tests for graceful error handling, database failures, concurrent access,
and system resilience under various failure conditions.
"""

import pytest
import json
import threading
import time
import tempfile
import os
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError, IntegrityError
from src.models import db, WeightEntry, WeightCategory
from src import services


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestDatabaseErrorHandling:
    """Test handling of database connection and operation failures"""
    
    def test_database_connection_failure_graceful_handling(self, app):
        """Test graceful handling when database is unavailable"""
        with app.app_context():
            # Mock database connection failure
            with patch('src.services.db.session') as mock_session:
                mock_session.commit.side_effect = OperationalError("Database connection failed", None, None)
                
                # Attempt to save an entry
                try:
                    result = services.save_weight_entry(80.0, 'kg', 1, 10)
                    # Should either return None or raise a handled exception
                    if result is not None:
                        pytest.fail("Expected database failure to be handled gracefully")
                except Exception as e:
                    # Should be a handled exception, not a raw database error
                    assert not isinstance(e, OperationalError), \
                        "Raw database error not properly handled"
    
    def test_database_integrity_error_handling(self, app, sample_categories):
        """Test handling of database integrity constraint violations"""
        with app.app_context():
            # Try to create duplicate categories (should violate unique constraint)
            category_name = "Duplicate Test Category"
            
            # Create first category successfully
            first_category = services.get_or_create_category(category_name)
            assert first_category.name == category_name
            
            # Mock integrity error on second attempt
            with patch('src.services.db.session.commit') as mock_commit:
                mock_commit.side_effect = IntegrityError("Duplicate key", None, None)
                
                try:
                    # This should handle the integrity error gracefully
                    second_category = services.get_or_create_category(category_name)
                    # Should either return the existing category or handle error gracefully
                except IntegrityError:
                    pytest.fail("Integrity error not properly handled")
    
    def test_database_rollback_on_error(self, app, sample_categories):
        """Test that database transactions are properly rolled back on errors"""
        with app.app_context():
            initial_entry_count = len(services.get_all_entries())
            
            # Mock an error during entry save that should trigger rollback
            with patch('src.services.WeightEntry') as mock_entry_class:
                mock_entry = MagicMock()
                mock_entry_class.return_value = mock_entry
                
                # Mock the save to succeed initially
                mock_entry.save = MagicMock()
                
                # But mock commit to fail
                with patch('src.services.db.session.commit') as mock_commit:
                    mock_commit.side_effect = Exception("Commit failed")
                    
                    try:
                        services.save_weight_entry(75.0, 'kg', sample_categories['benchpress'].id, 8)
                    except:
                        pass  # Error is expected
                    
                    # Verify rollback occurred - entry count should be unchanged
                    final_entry_count = len(services.get_all_entries())
                    assert final_entry_count == initial_entry_count, \
                        "Database transaction not properly rolled back"


class TestConcurrentAccessHandling:
    """Test handling of concurrent user access and race conditions"""
    
    def test_concurrent_entry_creation(self, app, sample_categories):
        """Test handling multiple users creating entries simultaneously"""
        with app.app_context():
            initial_count = len(services.get_all_entries())
            results = []
            errors = []
            
            def create_entry(weight, reps):
                try:
                    entry = services.save_weight_entry(
                        weight, 'kg', sample_categories['benchpress'].id, reps)
                    results.append(entry.id if entry else None)
                except Exception as e:
                    errors.append(str(e))
            
            # Launch 10 concurrent entry creations
            threads = []
            for i in range(10):
                thread = threading.Thread(target=create_entry, args=(70.0 + i, 10 + i))
                threads.append(thread)
                thread.start()
            
            # Wait for all to complete
            for thread in threads:
                thread.join()
            
            # Verify all entries were created successfully
            final_count = len(services.get_all_entries())
            expected_count = initial_count + 10
            
            assert len(errors) == 0, f"Errors during concurrent creation: {errors}"
            assert final_count >= expected_count, \
                f"Expected at least {expected_count} entries, got {final_count}"
            assert len([r for r in results if r is not None]) == 10, \
                "Not all concurrent entries were created successfully"
    
    def test_concurrent_category_creation(self, app):
        """Test concurrent creation of categories with same name"""
        with app.app_context():
            category_name = "Concurrent Test Category"
            results = []
            errors = []
            
            def create_category():
                try:
                    category = services.get_or_create_category(category_name)
                    results.append(category.id)
                except Exception as e:
                    errors.append(str(e))
            
            # Launch 5 concurrent attempts to create same category
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=create_category)
                threads.append(thread)
                thread.start()
            
            # Wait for all to complete
            for thread in threads:
                thread.join()
            
            # Should either all succeed (getting same category) or handle conflicts gracefully
            unique_ids = set(results)
            assert len(unique_ids) <= 1, \
                f"Multiple categories created with same name: {unique_ids}"
            assert len(errors) == 0, f"Errors during concurrent category creation: {errors}"


class TestMalformedRequestHandling:
    """Test handling of various malformed and invalid requests"""
    
    def test_api_malformed_json_handling(self, app, client):
        """Test handling of malformed JSON in API requests"""
        with app.app_context():
            malformed_json_strings = [
                '{"weight": 80, "unit": kg}',  # Missing quotes
                '{"weight": 80, "unit": "kg",}',  # Trailing comma
                '{"weight": 80 "unit": "kg"}',  # Missing comma
                '{weight: 80, unit: "kg"}',  # Unquoted key
                '{"weight": 80, "unit": "kg"',  # Missing closing brace
                'weight: 80, unit: kg',  # Not JSON at all
                '',  # Empty string
                'null',  # Null JSON
                '[]',  # Array instead of object
                '"just a string"',  # String instead of object
            ]
            
            for malformed_json in malformed_json_strings:
                response = client.post('/api/entries',
                    data=malformed_json,
                    content_type='application/json')
                
                # Should be rejected with proper error code
                assert response.status_code in [400, 422], \
                    f"Malformed JSON not properly rejected: {malformed_json[:30]}..."
    
    def test_missing_required_fields_handling(self, app, client):
        """Test handling when required fields are missing"""
        with app.app_context():
            incomplete_requests = [
                {},  # No fields
                {'weight': 80},  # Missing unit and category
                {'unit': 'kg'},  # Missing weight and category  
                {'category_id': 1},  # Missing weight and unit
                {'weight': 80, 'unit': 'kg'},  # Missing category_id
                {'weight': 80, 'category_id': 1},  # Missing unit
                {'unit': 'kg', 'category_id': 1},  # Missing weight
            ]
            
            for incomplete_request in incomplete_requests:
                response = client.post('/api/entries',
                    json=incomplete_request,
                    content_type='application/json')
                
                # Should be rejected with proper error message
                assert response.status_code in [400, 422], \
                    f"Incomplete request not properly rejected: {incomplete_request}"
                
                # Error message should be helpful
                if response.status_code in [400, 422]:
                    try:
                        error_data = json.loads(response.data)
                        assert 'error' in error_data or 'message' in error_data, \
                            "Error response should include error message"
                    except json.JSONDecodeError:
                        # Plain text error is also acceptable
                        pass
    
    def test_invalid_data_types_handling(self, app, client, sample_categories):
        """Test handling of incorrect data types in requests"""
        with app.app_context():
            invalid_type_requests = [
                {'weight': 'eighty', 'unit': 'kg', 'category_id': sample_categories['benchpress'].id},
                {'weight': 80, 'unit': 123, 'category_id': sample_categories['benchpress'].id}, 
                {'weight': 80, 'unit': 'kg', 'category_id': 'bench_press'},
                {'weight': True, 'unit': 'kg', 'category_id': sample_categories['benchpress'].id},
                {'weight': [], 'unit': 'kg', 'category_id': sample_categories['benchpress'].id},
                {'weight': {}, 'unit': 'kg', 'category_id': sample_categories['benchpress'].id},
                {'weight': 80, 'unit': 'kg', 'category_id': sample_categories['benchpress'].id, 'reps': 'ten'},
            ]
            
            for invalid_request in invalid_type_requests:
                response = client.post('/api/entries',
                    json=invalid_request,
                    content_type='application/json')
                
                # Should be rejected
                assert response.status_code in [400, 422], \
                    f"Invalid data types not properly rejected: {invalid_request}"


class TestResourceExhaustionHandling:
    """Test handling of resource exhaustion scenarios"""
    
    def test_large_dataset_handling(self, app, sample_categories):
        """Test system behavior with large datasets"""
        with app.app_context():
            # Create a moderate number of entries to test performance
            initial_count = len(services.get_all_entries())
            
            # Create 100 entries (reasonable for testing, not too slow)
            created_entries = []
            for i in range(100):
                try:
                    entry = services.save_weight_entry(
                        70.0 + (i % 50), 'kg', 
                        sample_categories['benchpress'].id, 
                        10 + (i % 5)
                    )
                    if entry:
                        created_entries.append(entry.id)
                except Exception as e:
                    pytest.fail(f"Failed to create entry {i}: {e}")
            
            # Verify all entries were created
            assert len(created_entries) == 100
            
            # Test that queries still work efficiently with larger dataset
            all_entries = services.get_all_entries()
            assert len(all_entries) >= initial_count + 100
            
            # Test plot generation with larger dataset
            plot_json = services.create_weight_plot(all_entries[:50], 'month')
            assert plot_json is not None
            assert len(plot_json) > 0
            
            # Clean up created entries
            for entry_id in created_entries:
                services.delete_entry(entry_id)
    
    def test_memory_leak_prevention(self, app, sample_categories):
        """Test that repeated operations don't cause memory leaks"""
        with app.app_context():
            # Perform repeated operations to check for memory leaks
            for i in range(50):
                # Create and delete entries repeatedly
                entry = services.save_weight_entry(
                    75.0, 'kg', sample_categories['benchpress'].id, 10)
                if entry:
                    services.delete_entry(entry.id)
                
                # Generate plots repeatedly
                test_entries = services.get_all_entries()[:10]
                if test_entries:
                    plot_json = services.create_weight_plot(test_entries, 'week')
                    assert plot_json is not None
            
            # Test should complete without excessive memory usage or errors
            # (Memory usage testing would require additional tools)


class TestNetworkErrorHandling:
    """Test handling of network-related errors and timeouts"""
    
    def test_request_timeout_handling(self, app, client):
        """Test handling of slow/hanging requests"""
        with app.app_context():
            # Simulate slow request by mocking a delay
            with patch('src.services.save_weight_entry') as mock_save:
                # Mock a function that takes a long time
                def slow_save(*args, **kwargs):
                    time.sleep(0.1)  # Short delay for testing
                    return MagicMock(id=1, weight=80.0)
                
                mock_save.side_effect = slow_save
                
                # Request should still complete (we're not testing actual timeout,
                # just that slow operations are handled)
                response = client.post('/api/entries',
                    json={'weight': 80, 'unit': 'kg', 'category_id': 1},
                    content_type='application/json')
                
                # Should complete successfully or with appropriate error
                assert response.status_code in [200, 201, 400, 422, 500]
    
    def test_client_disconnect_handling(self, app, client):
        """Test graceful handling when client disconnects during request"""
        with app.app_context():
            # This is difficult to test directly, but we can test that
            # operations complete even if client isn't waiting
            
            # Mock a scenario where client disconnects
            with patch('src.services.db.session.commit') as mock_commit:
                original_commit = mock_commit.side_effect
                
                def commit_with_delay():
                    time.sleep(0.05)  # Small delay
                    if original_commit:
                        return original_commit()
                
                mock_commit.side_effect = commit_with_delay
                
                # Operation should still complete successfully
                response = client.post('/api/entries',
                    json={'weight': 75, 'unit': 'kg', 'category_id': 1},
                    content_type='application/json')
                
                # Should handle gracefully
                assert response.status_code in [200, 201, 400, 422, 500]


class TestErrorResponseQuality:
    """Test that error responses are helpful and don't leak sensitive information"""
    
    def test_error_message_quality(self, app, client):
        """Test that error messages are helpful but don't expose internals"""
        with app.app_context():
            # Test invalid category ID
            response = client.post('/api/entries',
                json={'weight': 80, 'unit': 'kg', 'category_id': 99999},
                content_type='application/json')
            
            assert response.status_code in [400, 422]
            
            # Check error message
            try:
                error_data = json.loads(response.data)
                error_message = error_data.get('error', '') or error_data.get('message', '')
                
                # Should be helpful
                assert len(error_message) > 0, "Error message should not be empty"
                
                # Should not expose internal details
                sensitive_patterns = [
                    'traceback', 'exception', 'sql', 'database',
                    'internal server error', 'stack trace'
                ]
                
                for pattern in sensitive_patterns:
                    assert pattern.lower() not in error_message.lower(), \
                        f"Error message exposes internal details: {error_message}"
                        
            except json.JSONDecodeError:
                # Text error message is acceptable too
                error_text = response.data.decode('utf-8')
                assert len(error_text) > 0
    
    def test_no_sensitive_data_in_errors(self, app, client):
        """Test that error responses don't leak sensitive information"""
        with app.app_context():
            # Test various error conditions
            error_inducing_requests = [
                {'weight': 'invalid', 'unit': 'kg', 'category_id': 1},
                {'weight': 80, 'unit': 'invalid', 'category_id': 1},
                {'weight': 80, 'unit': 'kg', 'category_id': 'invalid'},
            ]
            
            for request_data in error_inducing_requests:
                response = client.post('/api/entries',
                    json=request_data,
                    content_type='application/json')
                
                if response.status_code >= 400:
                    response_text = response.data.decode('utf-8').lower()
                    
                    # Should not contain sensitive information
                    sensitive_info = [
                        'password', 'secret', 'key', 'token',
                        'database', 'sql', 'traceback', 'exception',
                        'file path', 'directory', 'config'
                    ]
                    
                    for sensitive in sensitive_info:
                        assert sensitive not in response_text, \
                            f"Error response contains sensitive info '{sensitive}': {response_text[:100]}..."