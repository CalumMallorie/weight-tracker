"""
Security Tests - CRITICAL Priority

Tests for SQL injection, XSS prevention, input validation, and other security vulnerabilities.
These tests are essential before any production deployment with user data.
"""

import pytest
import json
from src.models import db, WeightEntry, WeightCategory
from src import services


# Mark all tests in this file as unit tests (should run in CI) and security tests
pytestmark = [pytest.mark.unit, pytest.mark.security]


class TestSQLInjectionPrevention:
    """Test that SQL injection attempts are properly blocked"""
    
    def test_sql_injection_in_entry_creation(self, app, client, sample_categories):
        """Test SQL injection attempts in weight entry creation"""
        with app.app_context():
            malicious_payloads = [
                "'; DROP TABLE weight_entry; --",
                "1' OR '1'='1",
                "UNION SELECT * FROM weight_category--",
                "'; UPDATE weight_entry SET weight=0; --",
                "1; DELETE FROM weight_entry WHERE 1=1; --"
            ]
            
            for payload in malicious_payloads:
                # Test via API
                response = client.post('/api/entries', 
                    json={
                        'weight': payload, 
                        'unit': 'kg', 
                        'category_id': sample_categories['benchpress'].id
                    },
                    content_type='application/json')
                
                # Should be rejected with 400 or 422
                assert response.status_code in [400, 422], \
                    f"SQL injection payload '{payload[:20]}...' was not properly rejected"
                
                # Test via form submission  
                form_response = client.post('/', data={
                    'weight': payload,
                    'unit': 'kg', 
                    'category': sample_categories['benchpress'].id,
                    'reps': '10'
                })
                
                # Should either reject (400) or redirect successfully (but not execute injection)
                assert form_response.status_code in [200, 302, 400, 422]
                
                # Verify no data corruption occurred
                entries = services.get_all_entries()
                # Database should still exist and be intact
                assert isinstance(entries, list)
    
    def test_sql_injection_in_category_creation(self, app, client):
        """Test SQL injection attempts in category creation"""
        with app.app_context():
            malicious_names = [
                "Test'; DROP TABLE weight_category; --",
                "'; INSERT INTO weight_category (name) VALUES ('hacked'); --",
                "Test' UNION SELECT password FROM users--"
            ]
            
            for malicious_name in malicious_names:
                response = client.post('/api/categories',
                    json={'name': malicious_name},
                    content_type='application/json')
                
                # Should be rejected or handled safely
                assert response.status_code in [200, 201, 400, 422]
                
                # Verify database integrity
                categories = services.get_all_categories()
                assert isinstance(categories, list)
                assert len(categories) > 0  # Original categories should still exist


class TestInputValidationSecurity:
    """Test comprehensive input validation and edge cases"""
    
    def test_extreme_numeric_values(self, app, client, sample_categories):
        """Test handling of extreme or invalid numeric inputs"""
        with app.app_context():
            dangerous_values = [
                float('inf'),      # Infinity
                float('-inf'),     # Negative infinity  
                float('nan'),      # Not a number
                1e308,            # Extremely large number
                -1e308,           # Extremely large negative
                0.0000000001,     # Extremely small positive
                -999999999,       # Large negative weight
                999999999,        # Unrealistically large weight
            ]
            
            for value in dangerous_values:
                try:
                    response = client.post('/api/entries',
                        json={
                            'weight': value,
                            'unit': 'kg',
                            'category_id': sample_categories['benchpress'].id,
                            'reps': 10
                        },
                        content_type='application/json')
                    
                    # Should either be rejected or handled gracefully
                    if response.status_code == 201:
                        # If accepted, verify the value was sanitized/validated
                        data = json.loads(response.data)
                        saved_weight = data.get('weight', 0)
                        assert isinstance(saved_weight, (int, float))
                        assert saved_weight > 0  # Should be positive
                        assert saved_weight < 1000  # Should be reasonable
                    else:
                        # Should be rejected with proper error code
                        assert response.status_code in [400, 422]
                        
                except (ValueError, OverflowError):
                    # It's okay if the JSON serialization itself fails
                    pass
    
    def test_malformed_data_structures(self, app, client):
        """Test handling of malformed JSON and data structures"""
        with app.app_context():
            malformed_requests = [
                {},  # Empty object
                {'weight': 'not_a_number'},  # Invalid type
                {'unit': 'invalid_unit'},    # Invalid unit
                {'category_id': 'not_an_id'}, # Invalid category ID
                {'category_id': -1},         # Negative ID
                {'category_id': 999999},     # Non-existent ID
                {'reps': -10},              # Negative reps
                {'reps': 'not_a_number'},   # Invalid reps type
                None,                       # Null request
                [],                         # Array instead of object
                "string_instead_of_object", # String instead of object
            ]
            
            for malformed_data in malformed_requests:
                try:
                    response = client.post('/api/entries',
                        json=malformed_data,
                        content_type='application/json')
                    
                    # Should be rejected
                    assert response.status_code in [400, 422], \
                        f"Malformed request was not properly rejected: {malformed_data}"
                        
                except (TypeError, ValueError):
                    # It's okay if the request fails at the JSON level
                    pass
    
    def test_oversized_input_handling(self, app, client, sample_categories):
        """Test handling of extremely large inputs"""
        with app.app_context():
            # Test very long strings
            very_long_string = "A" * 10000  # 10KB string
            
            response = client.post('/api/categories',
                json={'name': very_long_string},
                content_type='application/json')
            
            # Should be rejected or truncated safely
            assert response.status_code in [200, 201, 400, 422]
            
            if response.status_code in [200, 201]:
                # If accepted, verify it was handled safely
                data = json.loads(response.data)
                saved_name = data.get('name', '')
                assert len(saved_name) <= 1000  # Should be reasonably limited


class TestXSSPrevention:
    """Test prevention of Cross-Site Scripting attacks"""
    
    def test_xss_in_category_names(self, app, client):
        """Test XSS prevention in category names"""
        with app.app_context():
            xss_payloads = [
                "<script>alert('xss')</script>",
                "<img src=x onerror=alert('xss')>",
                "javascript:alert('xss')",
                "<svg onload=alert('xss')>",
                "';alert('xss');//",
                "<iframe src=javascript:alert('xss')></iframe>",
                "<<SCRIPT>alert('xss')</SCRIPT>",
            ]
            
            for payload in xss_payloads:
                response = client.post('/api/categories',
                    json={'name': payload},
                    content_type='application/json')
                
                # Should either be rejected or sanitized
                if response.status_code in [200, 201]:
                    data = json.loads(response.data)
                    saved_name = data.get('name', '')
                    
                    # Should not contain executable JavaScript
                    dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
                    for pattern in dangerous_patterns:
                        assert pattern.lower() not in saved_name.lower(), \
                            f"XSS payload not properly sanitized: {saved_name}"
                else:
                    # Rejection is also acceptable
                    assert response.status_code in [400, 422]
    
    def test_xss_in_form_submissions(self, app, client, sample_categories):
        """Test XSS prevention in form data"""
        with app.app_context():
            # Test XSS in notes field (if it exists) or other text fields
            xss_payload = "<script>alert('xss')</script>"
            
            response = client.post('/', data={
                'weight': '100',
                'unit': 'kg',
                'category': sample_categories['benchpress'].id,
                'reps': '10',
                'notes': xss_payload  # If notes field exists
            })
            
            # Should be handled safely (redirect or rejection)
            assert response.status_code in [200, 302, 400, 422]


class TestCSRFProtection:
    """Test CSRF protection mechanisms"""
    
    def test_form_csrf_protection(self, app, client):
        """Test that forms require CSRF tokens (when implemented)"""
        with app.app_context():
            # This test will need to be updated when CSRF protection is added
            # For now, just verify forms work as expected
            response = client.get('/')
            assert response.status_code == 200
            
            # TODO: When CSRF is implemented, test that:
            # 1. Forms without CSRF tokens are rejected
            # 2. Forms with invalid CSRF tokens are rejected
            # 3. Forms with valid CSRF tokens are accepted


class TestAuthorizationBoundaries:
    """Test that unauthorized access is properly prevented"""
    
    def test_api_access_without_auth(self, app, client):
        """Test API endpoints don't expose sensitive data without auth"""
        with app.app_context():
            # Test that API endpoints are accessible (current single-user app)
            # But document what should happen in multi-user scenario
            
            response = client.get('/api/entries')
            # Currently should work (single-user app)
            assert response.status_code == 200
            
            # TODO: When multi-user auth is added, test that:
            # 1. Unauthenticated requests are rejected
            # 2. Users can only access their own data  
            # 3. Admin endpoints require admin privileges
    
    def test_direct_database_access_prevention(self, app, client):
        """Test that database files aren't directly accessible via web"""
        with app.app_context():
            # Test common database file paths
            database_paths = [
                '/instance/weight_tracker.db',
                '/data/weight_tracker.db', 
                '/weight_tracker.db',
                '/../weight_tracker.db',
                '/../../weight_tracker.db'
            ]
            
            for path in database_paths:
                response = client.get(path)
                # Should be 404 or 403, not 200
                assert response.status_code in [404, 403], \
                    f"Database file may be accessible at {path}"


class TestDataIntegrityUnderAttack:
    """Test that data integrity is maintained under various attack scenarios"""
    
    def test_concurrent_malicious_requests(self, app, client, sample_categories):
        """Test handling of multiple malicious requests simultaneously"""
        import threading
        import time
        
        with app.app_context():
            results = []
            errors = []
            
            def make_malicious_request():
                try:
                    response = client.post('/api/entries',
                        json={
                            'weight': "'; DROP TABLE weight_entry; --",
                            'unit': 'kg',
                            'category_id': sample_categories['benchpress'].id
                        },
                        content_type='application/json')
                    results.append(response.status_code)
                except Exception as e:
                    errors.append(str(e))
            
            # Launch multiple concurrent malicious requests
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=make_malicious_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all to complete
            for thread in threads:
                thread.join()
            
            # Verify all were handled properly
            for status_code in results:
                assert status_code in [400, 422], \
                    f"Concurrent malicious request not properly handled: {status_code}"
            
            # Verify database is still intact
            entries = services.get_all_entries()
            assert isinstance(entries, list)
            categories = services.get_all_categories() 
            assert isinstance(categories, list)
            assert len(categories) > 0


class TestSecurityHeaders:
    """Test security-related HTTP headers"""
    
    def test_security_headers_present(self, app, client):
        """Test that appropriate security headers are set"""
        with app.app_context():
            response = client.get('/')
            
            # Check for basic security headers
            headers = response.headers
            
            # Content-Type should be set correctly
            assert 'text/html' in headers.get('Content-Type', ''), \
                "Content-Type header not properly set"
            
            # TODO: When security headers are implemented, test for:
            # - X-Content-Type-Options: nosniff
            # - X-Frame-Options: DENY or SAMEORIGIN  
            # - X-XSS-Protection: 1; mode=block
            # - Referrer-Policy: strict-origin-when-cross-origin
            # - Content-Security-Policy: appropriate policy
            
            # For now, just verify basic response structure
            assert response.status_code == 200