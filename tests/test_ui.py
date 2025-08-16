"""
Tests for UI rendering and frontend behavior.

Tests template rendering, form handling, and user interface elements.
Includes specific tests for issues like graph headers and mobile responsiveness.
"""

import pytest
from datetime import datetime, timedelta, UTC
from src.models import db, WeightEntry
from src import services


# Mark all tests in this file as integration tests (medium speed)
pytestmark = pytest.mark.integration


class TestIndexPageRendering:
    """Test main index page rendering and behavior"""
    
    def test_index_page_loads_successfully(self, app, client):
        """Index page should load without errors"""
        with app.app_context():
            response = client.get('/')
            assert response.status_code == 200
    
    def test_index_shows_most_recent_entry_data(self, app, client, sample_categories, default_user):
        """Index page should display most recent entry information"""
        with app.app_context():
            # Create entries with different dates
            old_date = datetime.now(UTC) - timedelta(days=10)
            recent_date = datetime.now(UTC) - timedelta(days=1)
            
            old_entry = WeightEntry(
                weight=100.0,
                unit='kg',
                category_id=sample_categories['benchpress'].id,
                user_id=default_user.id,
                reps=5,
                created_at=old_date
            )
            recent_entry = WeightEntry(
                weight=120.0,
                unit='kg', 
                category_id=sample_categories['benchpress'].id,
                user_id=default_user.id,
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
    
    def test_body_weight_exercise_form_submission(self, app, client, sample_categories, default_user):
        """Body weight exercise form should work correctly"""
        with app.app_context():
            # Add body mass first
            services.save_weight_entry(75.0, 'kg', sample_categories['body_mass'].id, None, user_id=default_user.id)
            
            form_data = {
                'weight': '',  # Empty weight for body weight exercise
                'unit': 'kg',
                'category': sample_categories['pushups'].id,
                'reps': '10'
            }
            
            response = client.post('/', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify entry was created correctly
            entries = services.get_entries_by_time_window('all', sample_categories['pushups'].id, user_id=default_user.id)
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
    
    def test_plot_container_has_explicit_height(self, app, client, sample_categories, default_user):
        """Plot container should have explicit height to prevent mobile cutoff"""
        with app.app_context():
            # Add data to generate a plot
            services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8, user_id=default_user.id)
            services.save_weight_entry(105.0, 'kg', sample_categories['benchpress'].id, 10, user_id=default_user.id)
            
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
    
    def test_plot_mobile_cutoff_prevention(self, app, client, sample_categories, default_user):
        """Plot should have proper mobile configuration to prevent bottom cutoff"""
        with app.app_context():
            # Add data to generate a plot
            services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8, user_id=default_user.id)
            services.save_weight_entry(105.0, 'kg', sample_categories['benchpress'].id, 10, user_id=default_user.id)
            
            response = client.get(f'/?category={sample_categories["benchpress"].id}')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            
            # Check that CSS has proper mobile adjustments
            assert 'overflow: visible' in html_content, "Plot should use visible overflow to prevent cutoff"
            assert 'min-height' in html_content, "Plot should have minimum height"
            
            # Check for mobile media queries that increase plot height
            assert '@media (max-width: 768px)' in html_content, "Should have mobile CSS rules"
            assert '@media (max-width: 480px)' in html_content, "Should have small mobile CSS rules"
            
            # Check that Plotly config includes mobile optimizations
            assert 'scrollZoom: false' in html_content, "Should disable scroll zoom on mobile"
            assert 'responsive: true' in html_content, "Should be responsive"
    
    def test_body_weight_modal_form_saves_correctly(self, app, client, sample_categories):
        """Body weight modal form should save the actual weight value, not zero"""
        with app.app_context():
            # Submit via the body weight modal form (which should save to body mass category)
            form_data = {
                'weight': '75.5',
                'unit': 'kg',
                'category': sample_categories['body_mass'].id,  # This simulates the hidden field
            }
            
            response = client.post('/', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify the entry was saved with the correct weight
            entries = services.get_entries_by_time_window('all', sample_categories['body_mass'].id)
            assert len(entries) == 1
            assert entries[0].weight == 75.5, f"Expected weight 75.5, but got {entries[0].weight}"
            assert entries[0].unit == 'kg'
            assert entries[0].category_id == sample_categories['body_mass'].id
    
    def test_body_weight_modal_multiple_submissions(self, app, client, sample_categories):
        """Multiple body weight submissions should save correctly, reproducing real user behavior"""
        with app.app_context():
            # First body weight submission
            form_data_1 = {
                'weight': '75.0',
                'unit': 'kg', 
                'category': sample_categories['body_mass'].id,
            }
            response_1 = client.post('/', data=form_data_1, follow_redirects=True)
            assert response_1.status_code == 200
            
            # Second body weight submission (like user updating their weight)
            form_data_2 = {
                'weight': '76.2',
                'unit': 'kg',
                'category': sample_categories['body_mass'].id,
            }
            response_2 = client.post('/', data=form_data_2, follow_redirects=True)
            assert response_2.status_code == 200
            
            # Check that both entries were saved correctly
            entries = services.get_entries_by_time_window('all', sample_categories['body_mass'].id)
            assert len(entries) == 2
            
            # Entries should be ordered by creation time (newest first)
            assert entries[0].weight == 76.2, f"Latest entry should be 76.2, got {entries[0].weight}"
            assert entries[1].weight == 75.0, f"First entry should be 75.0, got {entries[1].weight}"
            
            # Both should be body mass entries with no reps
            assert entries[0].reps is None
            assert entries[1].reps is None
    
    def test_body_weight_edge_cases_that_might_cause_zero(self, app, client, sample_categories):
        """Test edge cases that might cause body weight to save as zero"""
        with app.app_context():
            # Test case 1: Empty weight string (should cause validation error, not save as 0)
            form_data_empty = {
                'weight': '',
                'unit': 'kg',
                'category': sample_categories['body_mass'].id,
            }
            response = client.post('/', data=form_data_empty, follow_redirects=True)
            # Should either reject or handle gracefully, but not save as 0
            entries = services.get_entries_by_time_window('all', sample_categories['body_mass'].id)
            # If it saved an entry, it should not be 0
            if len(entries) > 0:
                assert entries[0].weight != 0, "Empty weight should not save as 0"
            
            # Clear any entries created
            for entry in entries:
                services.delete_entry(entry.id)
            
            # Test case 2: Weight as "0" string (explicit zero - should be rejected)
            form_data_zero = {
                'weight': '0',
                'unit': 'kg', 
                'category': sample_categories['body_mass'].id,
            }
            response = client.post('/', data=form_data_zero, follow_redirects=True)
            # Should reject zero weight for body mass entries
            entries = services.get_entries_by_time_window('all', sample_categories['body_mass'].id)
            assert len(entries) == 0, "Zero weight should not be saved for body mass entries"
            
            # Check that the response contains an error message
            html_content = response.get_data(as_text=True)
            assert 'Body weight must be greater than zero' in html_content, "Should show validation error for zero weight"
            
            # Test case 3: Invalid weight format (should cause validation error)
            form_data_invalid = {
                'weight': 'abc',
                'unit': 'kg',
                'category': sample_categories['body_mass'].id,
            }
            response = client.post('/', data=form_data_invalid, follow_redirects=True)
            # Should reject and not save anything
            entries = services.get_entries_by_time_window('all', sample_categories['body_mass'].id)
            assert len(entries) == 0, "Invalid weight should not save any entry"
    
    def test_body_weight_bug_fix_verification(self, app, client, sample_categories):
        """Verify that the original bug 'Body weight always saves as zero' is fixed"""
        with app.app_context():
            # Test the exact scenario described in the bug report:
            # User clicks "Track Body Weight" and enters their weight
            
            # Simulate user entering a normal body weight value
            form_data = {
                'weight': '72.5',  # User's actual body weight
                'unit': 'kg',
                'category': sample_categories['body_mass'].id,  # Hidden field from modal
            }
            
            response = client.post('/', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify that the weight was saved correctly (not as zero)
            entries = services.get_entries_by_time_window('all', sample_categories['body_mass'].id)
            assert len(entries) == 1, "Should save exactly one body weight entry"
            
            saved_entry = entries[0]
            assert saved_entry.weight == 72.5, f"Expected 72.5, but saved {saved_entry.weight} - bug still exists!"
            assert saved_entry.unit == 'kg'
            assert saved_entry.category_id == sample_categories['body_mass'].id
            assert saved_entry.reps is None, "Body mass entries should not have reps"
            
            # Test another submission to ensure it works consistently
            form_data_2 = {
                'weight': '73.1',
                'unit': 'kg', 
                'category': sample_categories['body_mass'].id,
            }
            
            response_2 = client.post('/', data=form_data_2, follow_redirects=True)
            assert response_2.status_code == 200
            
            # Verify second entry also saved correctly
            entries = services.get_entries_by_time_window('all', sample_categories['body_mass'].id)
            assert len(entries) == 2, "Should have two body weight entries"
            
            # Most recent entry should be first
            assert entries[0].weight == 73.1, f"Latest entry should be 73.1, got {entries[0].weight}"
            assert entries[1].weight == 72.5, f"First entry should be 72.5, got {entries[1].weight}"


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
    
    def test_time_filter_links_work(self, app, client, sample_categories, default_user):
        """Time filter links should function correctly"""
        with app.app_context():
            # Add some test data
            services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8, user_id=default_user.id)
            
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
    
    def test_entries_list_shows_recent_first(self, app, client, sample_categories, default_user):
        """Entries list should show most recent entries first"""
        with app.app_context():
            # Create entries with different dates
            old_date = datetime.now(UTC) - timedelta(days=5)
            recent_date = datetime.now(UTC) - timedelta(days=1)
            
            old_entry = WeightEntry(
                weight=100.0,
                unit='kg',
                category_id=sample_categories['benchpress'].id,
                user_id=default_user.id,
                reps=5,
                created_at=old_date
            )
            recent_entry = WeightEntry(
                weight=110.0,
                unit='kg',
                category_id=sample_categories['benchpress'].id,
                user_id=default_user.id,
                reps=8,
                created_at=recent_date
            )
            
            db.session.add(old_entry)
            db.session.add(recent_entry)
            db.session.commit()
            
            response = client.get('/entries')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            
            # Look for the specific weight values in table data context
            recent_pos = html_content.find('110.0 kg')
            old_pos = html_content.find('100.0 kg')
            
            # More recent entry (110kg) should appear before older entry (100kg)
            # If both are found, recent should come first (lower index)
            if recent_pos != -1 and old_pos != -1:
                assert recent_pos < old_pos, "Recent entries should appear first"
            else:
                # If we can't find the specific patterns, the entries might not be displayed
                assert False, f"Could not find weight entries in HTML. recent_pos={recent_pos}, old_pos={old_pos}" 