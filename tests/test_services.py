"""
Tests for business logic and data services.

Tests the core data processing, entry saving, and calculation logic.
Includes specific tests for issues like body weight entries saving incorrectly.
"""

import pytest
from datetime import datetime, timedelta, UTC
from src.models import db, WeightEntry
from src import services


# Mark all tests in this file as unit tests (fast)
pytestmark = pytest.mark.unit


class TestWeightEntrySaving:
    """Test weight entry creation and saving logic"""
    
    def test_save_body_weight_exercise_uses_body_mass(self, app, sample_categories):
        """Body weight exercises should use current body mass, not zero"""
        with app.app_context():
            # Add a body mass entry first
            body_mass_entry = services.save_weight_entry(
                75.5, 'kg', sample_categories['body_mass'].id, None
            )
            
            # Save a body weight exercise (push-ups)
            pushup_entry = services.save_weight_entry(
                0, 'kg', sample_categories['pushups'].id, 10
            )
            
            # Should use body mass weight, not zero
            assert pushup_entry.weight == 75.5
            assert pushup_entry.unit == 'kg'
            assert pushup_entry.reps == 10
            assert pushup_entry.category_id == sample_categories['pushups'].id
    
    def test_save_body_weight_exercise_without_body_mass_uses_fallback(self, app, sample_categories):
        """Body weight exercises without body mass should use fallback weight"""
        with app.app_context():
            # No body mass entries exist
            pushup_entry = services.save_weight_entry(
                0, 'kg', sample_categories['pushups'].id, 15
            )
            
            # Should use fallback weight (70.0), not zero
            assert pushup_entry.weight == 70.0
            assert pushup_entry.unit == 'kg'
            assert pushup_entry.reps == 15
    
    def test_save_body_mass_entry_saves_exact_weight(self, app, sample_categories):
        """Body mass entries should save exactly what's entered"""
        with app.app_context():
            entry = services.save_weight_entry(
                82.3, 'kg', sample_categories['body_mass'].id, None
            )
            
            assert entry.weight == 82.3
            assert entry.unit == 'kg'
            assert entry.reps is None
    
    def test_save_regular_exercise_entry(self, app, sample_categories):
        """Regular exercises should save weight and reps normally"""
        with app.app_context():
            entry = services.save_weight_entry(
                100.0, 'kg', sample_categories['benchpress'].id, 8
            )
            
            assert entry.weight == 100.0
            assert entry.unit == 'kg'
            assert entry.reps == 8
    
    def test_save_entry_with_invalid_category_raises_error(self, app):
        """Saving with non-existent category should raise error"""
        with app.app_context():
            with pytest.raises(ValueError, match="Category with ID 999 not found"):
                services.save_weight_entry(100.0, 'kg', 999, 10)


class TestDataRetrievalAndOrdering:
    """Test data retrieval and ordering logic"""
    
    def test_entries_ordered_by_most_recent_first(self, app, sample_categories):
        """Entries should be ordered by most recent first (DESC)"""
        with app.app_context():
            # Create entries with specific timestamps
            old_date = datetime.now(UTC) - timedelta(days=10)
            recent_date = datetime.now(UTC) - timedelta(days=1)
            
            # Add in non-chronological order
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
            
            # Retrieve entries
            entries = services.get_entries_by_time_window(
                'all', sample_categories['benchpress'].id
            )
            
            # Should be ordered with most recent first
            assert len(entries) == 2
            assert entries[0].weight == 110.0  # Recent entry first
            assert entries[1].weight == 100.0  # Older entry second
            assert entries[0].created_at > entries[1].created_at
    
    def test_get_most_recent_body_mass_returns_latest(self, app, sample_categories):
        """Should return the most recent body mass entry"""
        with app.app_context():
            # Add multiple body mass entries
            old_date = datetime.now(UTC) - timedelta(days=5)
            recent_date = datetime.now(UTC) - timedelta(days=1)
            
            old_entry = WeightEntry(
                weight=70.0,
                unit='kg',
                category_id=sample_categories['body_mass'].id,
                created_at=old_date
            )
            recent_entry = WeightEntry(
                weight=75.0,
                unit='kg',
                category_id=sample_categories['body_mass'].id,
                created_at=recent_date
            )
            
            db.session.add(old_entry)
            db.session.add(recent_entry)
            db.session.commit()
            
            # Should return most recent
            most_recent = services.get_most_recent_body_mass()
            assert most_recent.weight == 75.0
    
    def test_get_most_recent_body_mass_returns_none_when_empty(self, app):
        """Should return None when no body mass entries exist"""
        with app.app_context():
            most_recent = services.get_most_recent_body_mass()
            assert most_recent is None


class TestEntryUpdate:
    """Test entry update logic"""
    
    def test_update_body_weight_exercise_uses_current_body_mass(self, app, sample_categories):
        """Updating body weight exercise should use current body mass"""
        with app.app_context():
            # Create initial body mass
            services.save_weight_entry(70.0, 'kg', sample_categories['body_mass'].id, None)
            
            # Create body weight exercise
            pushup_entry = services.save_weight_entry(
                0, 'kg', sample_categories['pushups'].id, 10
            )
            assert pushup_entry.weight == 70.0
            
            # Update body mass
            services.save_weight_entry(75.0, 'kg', sample_categories['body_mass'].id, None)
            
            # Update the body weight exercise
            updated_entry = services.update_entry(
                pushup_entry.id, 0, 'kg', sample_categories['pushups'].id, 12
            )
            
            # Should use new body mass weight
            assert updated_entry.weight == 75.0
            assert updated_entry.reps == 12
    
    def test_update_regular_exercise_preserves_weight(self, app, sample_categories):
        """Updating regular exercise should preserve the weight value"""
        with app.app_context():
            entry = services.save_weight_entry(
                100.0, 'kg', sample_categories['benchpress'].id, 8
            )
            
            updated_entry = services.update_entry(
                entry.id, 105.0, 'kg', sample_categories['benchpress'].id, 10
            )
            
            assert updated_entry.weight == 105.0
            assert updated_entry.reps == 10


class TestPlotDataGeneration:
    """Test plot data generation and processing"""
    
    def test_create_weight_plot_with_data(self, app, sample_categories):
        """Plot creation should work with valid data"""
        with app.app_context():
            # Add some entries
            services.save_weight_entry(100.0, 'kg', sample_categories['benchpress'].id, 8)
            services.save_weight_entry(105.0, 'kg', sample_categories['benchpress'].id, 10)
            
            entries = services.get_entries_by_time_window(
                'month', sample_categories['benchpress'].id
            )
            
            plot_json = services.create_weight_plot(entries, 'month', 'none')
            
            # Should return valid JSON string
            assert plot_json is not None
            assert isinstance(plot_json, str)
            assert len(plot_json) > 0
    
    def test_create_weight_plot_with_no_data(self, app, sample_categories):
        """Plot creation should handle empty data gracefully"""
        with app.app_context():
            entries = services.get_entries_by_time_window(
                'month', sample_categories['benchpress'].id
            )
            
            plot_json = services.create_weight_plot(entries, 'month', 'none')
            
            # Should handle empty data without crashing
            assert plot_json is not None 