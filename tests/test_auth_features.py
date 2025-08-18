"""
Tests for authentication features including username/email changes
"""
import pytest

from src.models import db
from src.models.user import User
from src.forms import ChangeUsernameForm, ChangeEmailForm
from src.app import create_app

pytestmark = pytest.mark.unit


class TestUserAccountUpdates:
    """Test user account update functionality"""
    
    def test_username_change_route_get(self, authenticated_client, default_user):
        """Test GET request to change username route"""
        response = authenticated_client.get('/auth/change-username')
        assert response.status_code == 200
        assert b'Change Username' in response.data
        assert b'new_username' in response.data
        assert b'current_password' in response.data
    
    def test_email_change_route_get(self, authenticated_client, default_user):
        """Test GET request to change email route"""
        response = authenticated_client.get('/auth/change-email')
        assert response.status_code == 200
        assert b'Change Email' in response.data
        assert b'new_email' in response.data
        assert b'current_password' in response.data
    
    def test_username_change_requires_authentication(self, app):
        """Test that username change requires user to be logged in"""
        # Create a non-testing app to test real authentication
        non_test_app = create_app({
            'TESTING': False,  # Disable test mode
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key'
        })
        
        with non_test_app.test_client() as client:
            response = client.get('/auth/change-username')
            # Should redirect to login when not authenticated
            assert response.status_code == 302
            assert '/auth/login' in response.headers['Location']
    
    def test_email_change_requires_authentication(self, app):
        """Test that email change requires user to be logged in"""
        # Create a non-testing app to test real authentication
        non_test_app = create_app({
            'TESTING': False,  # Disable test mode
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key'
        })
        
        with non_test_app.test_client() as client:
            response = client.get('/auth/change-email')
            # Should redirect to login when not authenticated
            assert response.status_code == 302
            assert '/auth/login' in response.headers['Location']
    
    def test_profile_page_shows_change_links(self, authenticated_client, default_user):
        """Test that profile page includes links to change username and email"""
        response = authenticated_client.get('/auth/profile')
        assert response.status_code == 200
        assert b'Change' in response.data  # Should have "Change" links
        assert b'/auth/change-username' in response.data or b'change-username' in response.data
        assert b'/auth/change-email' in response.data or b'change-email' in response.data


class TestFormSecurityFeatures:
    """Test security aspects of the new forms"""
    
    def test_forms_have_csrf_protection(self, app):
        """Test that CSRF protection is properly configured"""
        # Verify app config enables CSRF in production
        # (test mode disables it, but production should have it enabled)
        production_app = create_app()
        assert production_app.config.get('WTF_CSRF_ENABLED', False) == True
        
        # Verify test mode correctly disables CSRF for testing
        assert app.config.get('WTF_CSRF_ENABLED', True) == False
        
        # Verify forms are Flask-WTF forms (which support CSRF automatically)
        with app.app_context():
            username_form = ChangeUsernameForm()
            email_form = ChangeEmailForm()
            
            # Verify they are FlaskForm instances (which have built-in CSRF)
            from flask_wtf import FlaskForm
            assert isinstance(username_form, FlaskForm)
            assert isinstance(email_form, FlaskForm)


class TestFormHTMLAttributes:
    """Test HTML form attributes for better UX"""
    
    def test_username_form_has_correct_attributes(self, authenticated_client, default_user):
        """Test username change form has proper HTML attributes"""
        response = authenticated_client.get('/auth/change-username')
        response_data = response.data.decode('utf-8')
        
        # Check for autocomplete attributes
        assert 'autocomplete="username"' in response_data
        assert 'autocapitalize="none"' in response_data
        
        # Check for password attributes
        assert 'autocomplete="current-password"' in response_data
    
    def test_email_form_has_correct_attributes(self, authenticated_client, default_user):
        """Test email change form has proper HTML attributes"""
        response = authenticated_client.get('/auth/change-email')
        response_data = response.data.decode('utf-8')
        
        # Check for email attributes
        assert 'autocomplete="email"' in response_data
        assert 'inputmode="email"' in response_data
        assert 'type="email"' in response_data
        assert 'autocapitalize="none"' in response_data
        
        # Check for password attributes
        assert 'autocomplete="current-password"' in response_data
    
    def test_login_form_html_attributes(self, client):
        """Test login form has proper HTML5 attributes"""
        response = client.get('/auth/login')
        response_data = response.data.decode('utf-8')
        
        # Check for autocomplete and input attributes
        assert 'autocomplete="username email"' in response_data
        assert 'inputmode="email"' in response_data
        assert 'autocapitalize="none"' in response_data
        assert 'autocomplete="current-password"' in response_data
    
    def test_register_form_html_attributes(self, client):
        """Test registration form has proper HTML5 attributes"""
        response = client.get('/auth/register')
        response_data = response.data.decode('utf-8')
        
        # Check for autocomplete and input attributes
        assert 'autocomplete="username"' in response_data
        assert 'autocomplete="email"' in response_data
        assert 'inputmode="email"' in response_data
        assert 'type="email"' in response_data
        assert 'autocapitalize="none"' in response_data
        assert 'autocomplete="new-password"' in response_data


class TestFormFunctionality:
    """Test that forms work correctly"""
    
    def test_change_forms_exist(self, app):
        """Test that change forms can be instantiated"""
        with app.app_context():
            # Should be able to create forms without error
            username_form = ChangeUsernameForm()
            email_form = ChangeEmailForm()
            
            # Forms should have required fields
            assert hasattr(username_form, 'new_username')
            assert hasattr(username_form, 'current_password')
            assert hasattr(email_form, 'new_email')
            assert hasattr(email_form, 'current_password')
    
    def test_routes_exist(self, authenticated_client):
        """Test that new routes exist and return correct responses"""
        # Username change route
        response = authenticated_client.get('/auth/change-username')
        assert response.status_code == 200
        
        # Email change route
        response = authenticated_client.get('/auth/change-email')
        assert response.status_code == 200
        
        # Profile page should still work
        response = authenticated_client.get('/auth/profile')
        assert response.status_code == 200