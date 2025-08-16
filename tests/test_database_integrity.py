"""
Database Integrity and Production Parity Tests

These tests are designed to catch issues that only manifest in production
environments, particularly database corruption or schema inconsistencies.
"""

import pytest
from src import services
from src.models import WeightCategory, WeightEntry
from src.migration import check_and_migrate_database


pytestmark = pytest.mark.integration


class TestDatabaseIntegrity:
    """Test database integrity and schema consistency"""
    
    def test_category_flags_are_mutually_exclusive(self, app, default_user):
        """Test that category flags is_body_mass and is_body_weight_exercise are mutually exclusive"""
        with app.app_context():
            categories = services.get_all_categories(user_id=default_user.id)
            
            for category in categories:
                # A category cannot be both body mass AND body weight exercise
                assert not (category.is_body_mass and category.is_body_weight_exercise), \
                    f"Category '{category.name}' (ID: {category.id}) has both is_body_mass=True AND is_body_weight_exercise=True"
    
    def test_body_mass_category_configuration(self, app, default_user):
        """Test that Body Mass category is properly configured"""
        with app.app_context():
            body_mass_categories = [cat for cat in services.get_all_categories(user_id=default_user.id) if cat.is_body_mass]
            
            # Should have at least one body mass category
            assert len(body_mass_categories) >= 1, "No body mass categories found"
            
            for category in body_mass_categories:
                # Body mass categories should have is_body_mass=True and is_body_weight_exercise=False
                assert category.is_body_mass is True, f"Body mass category '{category.name}' has is_body_mass=False"
                assert category.is_body_weight_exercise is False, f"Body mass category '{category.name}' has is_body_weight_exercise=True"
    
    def test_body_weight_exercise_category_configuration(self, app, default_user):
        """Test that body weight exercise categories are properly configured"""
        with app.app_context():
            body_weight_categories = [cat for cat in services.get_all_categories(user_id=default_user.id) if hasattr(cat, 'is_body_weight_exercise') and cat.is_body_weight_exercise]
            
            for category in body_weight_categories:
                # Body weight exercise categories should have is_body_weight_exercise=True and is_body_mass=False
                assert category.is_body_weight_exercise is True, f"Body weight exercise category '{category.name}' has is_body_weight_exercise=False"
                assert category.is_body_mass is False, f"Body weight exercise category '{category.name}' has is_body_mass=True"
    
    def test_database_schema_completeness(self, app, default_user):
        """Test that database schema has all required columns"""
        with app.app_context():
            # Test that critical columns exist
            categories = services.get_all_categories(user_id=default_user.id)
            assert len(categories) > 0, "No categories found for user"
            sample_category = categories[0]
            
            # Check for required attributes
            required_attributes = ['id', 'name', 'is_body_mass', 'is_body_weight_exercise', 'created_at', 'user_id']
            for attr in required_attributes:
                assert hasattr(sample_category, attr), f"WeightCategory missing required attribute: {attr}"
            
            # If there are entries, check entry schema
            entries = services.get_all_entries(user_id=default_user.id)
            if entries:
                sample_entry = entries[0]
                entry_attributes = ['id', 'weight', 'unit', 'category_id', 'user_id', 'created_at']
                for attr in entry_attributes:
                    assert hasattr(sample_entry, attr), f"WeightEntry missing required attribute: {attr}"


class TestProductionParityValidation:
    """Tests that ensure test environment matches production scenarios"""
    
    def test_body_mass_entry_saves_actual_weight_not_zero(self, app, sample_categories, default_user):
        """REGRESSION TEST: Ensure body mass entries save actual weight, not zero (production bug)"""
        with app.app_context():
            # Test with various weight values that were problematic in production
            test_weights = [87.0, 75.5, 90.2, 65.8, 100.0]
            
            for weight in test_weights:
                # Save a body mass entry
                entry = services.save_weight_entry(weight, 'kg', sample_categories['body_mass'].id, None, user_id=default_user.id)
                
                # Critical assertion: weight should match what was submitted, not be 0
                assert entry.weight == weight, \
                    f"CRITICAL: Body mass entry saved weight={entry.weight} instead of submitted weight={weight}"
                assert entry.weight != 0.0, \
                    f"CRITICAL: Body mass entry saved zero weight instead of {weight}kg"
                
                # Clean up
                services.delete_entry(entry.id, user_id=default_user.id)
    
    def test_form_submission_simulation_body_mass(self, app, client, sample_categories, default_user):
        """REGRESSION TEST: Simulate the exact form submission that failed in production"""
        with app.app_context():
            # Simulate the production form submission that was saving 0kg
            form_data = {
                'weight': '87',      # String as received from form
                'unit': 'kg',
                'category': sample_categories['body_mass'].id,
                # No reps for body mass
            }
            
            # Count entries before
            entries_before = len(services.get_all_entries(user_id=default_user.id))
            
            # Submit form
            response = client.post('/', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Check that entry was created
            entries_after = services.get_all_entries(user_id=default_user.id)
            assert len(entries_after) == entries_before + 1
            
            # Find the new entry
            new_entry = entries_after[0]  # Most recent first
            
            # Critical assertions
            assert new_entry.weight == 87.0, \
                f"PRODUCTION BUG REPRODUCED: Form submission saved weight={new_entry.weight} instead of 87.0"
            assert new_entry.unit == 'kg'
            assert new_entry.category_id == sample_categories['body_mass'].id
    
    def test_category_identification_logic(self, app, sample_categories, default_user):
        """Test the category identification logic that was causing the bug"""
        with app.app_context():
            body_mass_category = sample_categories['body_mass']
            
            # Test the exact logic from routes.py that was problematic
            is_body_mass_entry = body_mass_category and body_mass_category.is_body_mass
            is_body_weight_exercise_entry = body_mass_category and getattr(body_mass_category, 'is_body_weight_exercise', False)
            
            # These should be mutually exclusive for body mass category
            assert is_body_mass_entry is True, "Body mass category not identified as body mass"
            assert is_body_weight_exercise_entry is False, "Body mass category incorrectly identified as body weight exercise"
            
            # Test body weight exercise category if available
            body_weight_categories = [cat for cat in services.get_all_categories() 
                                    if hasattr(cat, 'is_body_weight_exercise') and cat.is_body_weight_exercise]
            if body_weight_categories:
                body_weight_category = body_weight_categories[0]
                is_body_mass_entry = body_weight_category and body_weight_category.is_body_mass
                is_body_weight_exercise_entry = body_weight_category and body_weight_category.is_body_weight_exercise
                
                assert is_body_mass_entry is False, "Body weight exercise category incorrectly identified as body mass"
                assert is_body_weight_exercise_entry is True, "Body weight exercise category not identified as body weight exercise"


class TestMigrationRobustness:
    """Test that migrations work correctly on production-like data"""
    
    def test_migration_preserves_data_integrity(self, app, default_user):
        """Test that database migrations preserve existing data"""
        with app.app_context():
            # Get current categories and entries for the default user
            categories_before = services.get_all_categories(user_id=default_user.id)
            entries_before = services.get_all_entries(user_id=default_user.id)
            
            # Verify data exists (note: tests create fresh databases, which is expected)
            assert len(categories_before) > 0, "No categories found in database"
            # Note: entries may be empty in test environment, which is normal
            
            # Run migration (should be safe to run multiple times)
            try:
                check_and_migrate_database()
            except Exception as e:
                pytest.fail(f"Migration failed on production-like data: {e}")
            
            # Verify data is preserved
            categories_after = services.get_all_categories(user_id=default_user.id)
            entries_after = services.get_all_entries(user_id=default_user.id)
            
            assert len(categories_after) == len(categories_before), "Migration changed number of categories"
            assert len(entries_after) == len(entries_before), "Migration changed number of entries"
    
    def test_production_data_characteristics(self, app, default_user):
        """Verify database structure matches production requirements"""
        with app.app_context():
            categories = services.get_all_categories(user_id=default_user.id)
            entries = services.get_all_entries(user_id=default_user.id)
            
            # Should have at least the default Body Mass category
            assert len(categories) >= 1, f"Only {len(categories)} categories found"
            
            # Should have real category names (not just test names)
            category_names = [cat.name for cat in categories]
            assert "Body Mass" in category_names, "Missing Body Mass category"
            
            # Verify the Body Mass category is properly configured
            body_mass_cat = next((cat for cat in categories if cat.name == "Body Mass"), None)
            assert body_mass_cat is not None, "Body Mass category not found"
            assert body_mass_cat.is_body_mass is True, "Body Mass category not configured as body mass"
            assert body_mass_cat.is_body_weight_exercise is False, "Body Mass category incorrectly configured as body weight exercise"


class TestWeightValidationEdgeCases:
    """Test edge cases for weight validation that could cause zero weight bugs"""
    
    def test_weight_parsing_edge_cases(self, app, sample_categories):
        """Test various weight input formats that might cause parsing issues"""
        with app.app_context():
            # Test cases that might cause issues
            test_cases = [
                ('87', 87.0),       # String number
                ('87.0', 87.0),     # String float
                ('87.5', 87.5),     # String decimal
                ('100', 100.0),     # Large number
                ('65.8', 65.8),     # Decimal
            ]
            
            for weight_str, expected_weight in test_cases:
                # Simulate form submission with string weight
                form_data = {
                    'weight': weight_str,
                    'unit': 'kg',
                    'category': sample_categories['body_mass'].id,
                }
                
                # This simulates the form parsing logic
                try:
                    weight = float(weight_str.replace(',', '.'))
                    assert weight == expected_weight, f"Weight parsing failed: '{weight_str}' -> {weight} != {expected_weight}"
                    assert weight != 0.0, f"Weight parsing returned zero for input '{weight_str}'"
                except ValueError:
                    pytest.fail(f"Weight parsing failed for input '{weight_str}'")
    
    def test_form_data_simulation(self, app, client, sample_categories):
        """Test form data that closely matches production scenarios"""
        with app.app_context():
            # Test the exact scenario from production logs
            test_scenarios = [
                {'weight': '87', 'unit': 'kg', 'expected_weight': 87.0},
                {'weight': '75.5', 'unit': 'kg', 'expected_weight': 75.5},
                {'weight': '90', 'unit': 'lb', 'expected_weight': 90.0},
            ]
            
            for scenario in test_scenarios:
                form_data = {
                    'weight': scenario['weight'],
                    'unit': scenario['unit'],
                    'category': sample_categories['body_mass'].id,
                }
                
                response = client.post('/', data=form_data, follow_redirects=True)
                assert response.status_code == 200
                
                # Get the most recent entry
                entries = services.get_all_entries()
                latest_entry = entries[0]  # Should be most recent
                
                assert latest_entry.weight == scenario['expected_weight'], \
                    f"Form submission {scenario} saved weight={latest_entry.weight} instead of {scenario['expected_weight']}"
                
                # Clean up
                services.delete_entry(latest_entry.id) 