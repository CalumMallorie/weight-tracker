"""
Tests for UI rendering and frontend behavior.

Tests template rendering, form handling, and user interface elements.
Includes specific tests for issues like graph headers and mobile responsiveness.
"""

import pytest
from datetime import datetime, timedelta, UTC
from src.models import db, WeightEntry
from src import services


class TestIndexPageRendering:
    """Test main index page rendering and behavior"""
    
    def test_index_page_loads_successfully(self, app, client):
        """Index page should load without errors"""
        with app.app_context():
            response = client.get('/')
            assert response.status_code == 200
    
    def test_index_shows_most_recent_entry_data(self, app, client, sample_categories):
        """Index page should display most recent entry information"""
        with app.app_context():
            # Create entries with different dates
            old_date = datetime.now(UTC) - timedelta(days=10)
            recent_date = datetime.now(UTC) - timedelta(days=1)
            
            old_entry = WeightEntry(
                weight=100.0,
                unit='kg',
                category_id=sample_categories['benchpress'].id,
                reps=5,
                created_at=old_date
            )
            recent_entry = WeightEntry(
                weight=120.0,
                unit='kg', 
                category_id=sample_categories['benchpress'].id,
                reps=8,
                created_at=recent_date
            )
            
            db.session.add(old_entry)
            db.session.add(recent_entry)
            db.session.commit()
            
            response = client.get(f'/?category={sample_categories["benchpress"].id}')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            
            # Most recent entry (120kg) should be displayed, not the older one (100kg)
            assert '120' in html_content, "Most recent weight should be displayed"
    
    def test_index_handles_empty_category_gracefully(self, app, client, sample_categories):
        """Index page should handle categories with no entries"""
        with app.app_context():
            response = client.get(f'/?category={sample_categories["squats"].id}')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            # Should handle empty state without crashing
            assert response.status_code == 200
    
    def test_category_selection_persists_in_form(self, app, client, sample_categories):
        """Selected category should be maintained in the form"""
        with app.app_context():
            response = client.get(f'/?category={sample_categories["benchpress"].id}')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            # Form should have the selected category
            assert 'selected' in html_content or 'value=' in html_content


class TestFormSubmission:
    """Test form submission and validation"""
    
    def test_valid_form_submission_redirects(self, app, client, sample_categories):
        """Valid form submission should redirect successfully"""
        with app.app_context():
            form_data = {
                'weight': '100.5',
                'unit': 'kg',
                'category': sample_categories['benchpress'].id,
                'reps': '8'
            }
            
            response = client.post('/', data=form_data, follow_redirects=False)
            assert response.status_code == 302  # Redirect after successful submission
    
    def test_body_weight_exercise_form_submission(self, app, client, sample_categories):
        """Body weight exercise form should work correctly"""
        with app.app_context():
            # Add body mass first
            services.save_weight_entry(75.0, 'kg', sample_categories['body_mass'].id, None)
            
            form_data = {
                'weight': '',  # Empty weight for body weight exercise
                'unit': 'kg',
                'category': sample_categories['pushups'].id,
                'reps': '10'
            }
            
            response = client.post('/', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify entry was created correctly
            entries = services.get_entries_by_time_window('all', sample_categories['pushups'].id)
            assert len(entries) == 1
            assert entries[0].weight == 75.0  # Should use body mass
    
    def test_invalid_form_submission_shows_error(self, app, client, sample_categories):
        """Invalid form data should show error message"""
        with app.app_context():
            form_data = {
                'weight': 'invalid',  # Invalid weight
                'unit': 'kg',
                'category': sample_categories['benchpress'].id,
                'reps': '8'
            }
            
            response = client.post('/', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            # Should show error message
            assert 'error' in html_content.lower() or 'invalid' in html_content.lower()


class TestMobileResponsiveness:
    """Test mobile UI and responsiveness"""
    
    def test_viewport_meta_tag_present(self, app, client):
        """Page should have proper mobile viewport meta tag"""
        with app.app_context():
            response = client.get('/')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            assert 'viewport' in html_content, "Should have viewport meta tag"
            assert 'width=device-width' in html_content, "Should set device width"
    
    def test_plot_container_has_explicit_height(self, app, client, sample_categories):
        """Plot container should have explicit height to prevent mobile cutoff"""
        with app.app_context():
            # Add data to generate a plot
            services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8)
            services.save_weight_entry(105.0, 'kg', sample_categories['benchpress'].id, 10)
            
            response = client.get(f'/?category={sample_categories["benchpress"].id}')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            
            # Check for plot container styling
            assert 'plot-container' in html_content, "Should have plot container class"
            
            # Should have explicit height set
            assert 'height:' in html_content or 'height=' in html_content, "Plot should have explicit height"
    
    def test_responsive_css_classes_present(self, app, client):
        """Page should have responsive CSS classes"""
        with app.app_context():
            response = client.get('/')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            # Should have responsive design elements
            assert 'max-width' in html_content or 'container' in html_content


class TestNavigationAndLinks:
    """Test navigation elements and links"""
    
    def test_navigation_links_present(self, app, client):
        """Page should have navigation links"""
        with app.app_context():
            response = client.get('/')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            # Should have links to other pages
            assert 'entries' in html_content or 'categories' in html_content
    
    def test_time_filter_links_work(self, app, client, sample_categories):
        """Time filter links should function correctly"""
        with app.app_context():
            # Add some test data
            services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8)
            
            # Test different time windows
            for window in ['week', 'month', 'year', 'all']:
                response = client.get(f'/?window={window}&category={sample_categories["benchpress"].id}')
                assert response.status_code == 200


class TestCategoryManagement:
    """Test category management UI"""
    
    def test_categories_page_loads(self, app, client):
        """Categories management page should load"""
        with app.app_context():
            response = client.get('/categories')
            assert response.status_code == 200
    
    def test_category_creation_form_present(self, app, client):
        """Categories page should have creation form"""
        with app.app_context():
            response = client.get('/categories')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            # Should have form elements for creating categories
            assert 'name' in html_content and 'form' in html_content
    
    def test_existing_categories_displayed(self, app, client, sample_categories):
        """Categories page should display existing categories"""
        with app.app_context():
            response = client.get('/categories')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            # Should show existing categories
            assert 'Body Mass' in html_content
            assert 'Push-ups' in html_content


class TestEntriesManagement:
    """Test entries management UI"""
    
    def test_entries_page_loads(self, app, client):
        """Entries management page should load"""
        with app.app_context():
            response = client.get('/entries')
            assert response.status_code == 200
    
    def test_entries_list_shows_recent_first(self, app, client, sample_categories):
        """Entries list should show most recent entries first"""
        with app.app_context():
            # Create entries with different dates
            old_date = datetime.now(UTC) - timedelta(days=5)
            recent_date = datetime.now(UTC) - timedelta(days=1)
            
            old_entry = WeightEntry(
                weight=100.0,
                unit='kg',
                category_id=sample_categories['benchpress'].id,
                reps=5,
                created_at=old_date
            )
            recent_entry = WeightEntry(
                weight=110.0,
                unit='kg',
                category_id=sample_categories['benchpress'].id,
                reps=8,
                created_at=recent_date
            )
            
            db.session.add(old_entry)
            db.session.add(recent_entry)
            db.session.commit()
            
            response = client.get('/entries')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            
            # More recent entry (110kg) should appear before older entry (100kg)
            recent_pos = html_content.find('110')
            old_pos = html_content.find('100')
            
            # If both are found, recent should come first (lower index)
            if recent_pos != -1 and old_pos != -1:
                assert recent_pos < old_pos, "Recent entries should appear first" 