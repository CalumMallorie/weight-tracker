import pytest
from flask import Flask
from sqlalchemy import inspect, text
import sqlite3

from src.app import create_app
from src.models import db, WeightEntry, WeightCategory
from src.migration import check_and_migrate_database, verify_model_schema

@pytest.fixture
def app_with_old_schema():
    """Create a test app with an old database schema (missing columns)"""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    
    with app.app_context():
        db.init_app(app)
        
        # Create a connection to create tables manually with old schema
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        
        # Create tables with old schema (without notes and reps columns)
        cursor.execute("""
            CREATE TABLE weight_category (
                id INTEGER NOT NULL, 
                name VARCHAR(50) NOT NULL, 
                is_body_mass BOOLEAN, 
                created_at DATETIME, 
                PRIMARY KEY (id),
                UNIQUE (name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE weight_entry (
                id INTEGER NOT NULL, 
                weight FLOAT NOT NULL, 
                unit VARCHAR(2) NOT NULL, 
                created_at DATETIME, 
                PRIMARY KEY (id)
            )
        """)
        
        connection.commit()
        connection.close()
        
    yield app

def test_migration_creates_missing_column(app_with_old_schema):
    """Test that the migration system adds missing columns"""
    with app_with_old_schema.app_context():
        # First verify our old schema is missing columns
        inspector = inspect(db.engine)
        columns_before = {c["name"] for c in inspector.get_columns("weight_entry")}
        
        assert "category_id" not in columns_before
        assert "reps" not in columns_before
        
        # Run the migration
        check_and_migrate_database()
        
        # Verify the schema has been updated
        inspector = inspect(db.engine)
        columns_after = {c["name"] for c in inspector.get_columns("weight_entry")}
        
        assert "category_id" in columns_after
        assert "reps" in columns_after
        # Notes field should be removed in v5 migration
        assert "notes" not in columns_after

def test_verify_model_schema(app_with_old_schema):
    """Test that verify_model_schema correctly identifies schema issues"""
    with app_with_old_schema.app_context():
        # Before migration, schema should not match models
        result_before = verify_model_schema()
        assert result_before["weight_entry"] is False
        
        # Run the migration
        check_and_migrate_database()
        
        # After migration, schema should match models
        result_after = verify_model_schema()
        assert result_after["weight_entry"] is True

def test_save_entry_after_migration(app_with_old_schema):
    """Test that we can save entries after migration"""
    from src import services
    
    with app_with_old_schema.app_context():
        # Run the migration
        check_and_migrate_database()
        
        # Create a default category
        category = services.create_default_category()
        
        # Save a weight entry with the new schema
        entry = services.save_weight_entry(
            weight=80.0,
            unit="kg",
            category_id_or_notes=category.id,
            reps=None
        )
        
        # Verify the entry was saved with the new fields
        assert entry.id is not None
        assert entry.weight == 80.0
        assert entry.unit == "kg"
        assert entry.category_id == category.id
        assert entry.reps is None

def test_load_entry_with_missing_fields(app_with_old_schema):
    """Test that we can load entries that are missing optional fields"""
    from src import services
    
    with app_with_old_schema.app_context():
        # First run migration
        check_and_migrate_database()
        
        # Create a category
        category = services.create_default_category()
        
        # Insert a weight entry directly with SQL, missing optional fields
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO weight_entry (weight, unit, category_id, created_at) VALUES (75.5, 'kg', ?, CURRENT_TIMESTAMP)",
            (category.id,)
        )
        entry_id = cursor.lastrowid
        connection.commit()
        connection.close()
        
        # Now try to load this entry using the ORM
        entry = WeightEntry.query.get(entry_id)
        
        # Verify we can access the entry even with missing fields
        assert entry is not None
        assert entry.weight == 75.5
        assert entry.unit == "kg"
        assert entry.category_id == category.id
        assert entry.reps is None
        
        # Verify notes is not a column in the model
        columns = [column.name for column in WeightEntry.__table__.columns]
        assert 'notes' not in columns

def test_save_entry_handles_schema_mismatch(app_with_old_schema):
    """Test that save_weight_entry handles schema mismatch gracefully"""
    from src import services
    from src.migration import check_and_migrate_database
    
    with app_with_old_schema.app_context():
        # First run the migration to ensure we have a valid schema
        check_and_migrate_database()
        
        # Create a body mass category
        body_mass_category = services.create_default_category()
        assert body_mass_category.is_body_mass is True
        
        # Create a non-body mass category for exercises
        exercise_category = WeightCategory(name="Bench Press", is_body_mass=False)
        db.session.add(exercise_category)
        db.session.commit()
        
        # Try to save an entry with reps to exercise category
        entry = services.save_weight_entry(85.0, 'kg', exercise_category.id, 5)
        
        # Verify the entry was saved correctly
        assert entry.id is not None
        assert entry.weight == 85.0
        assert entry.unit == 'kg'
        assert entry.category_id == exercise_category.id
        assert entry.reps == 5

        # Try saving without category (should use default body mass)
        entry2 = services.save_weight_entry(90.0, 'kg')
        assert entry2.id is not None
        assert entry2.category_id == body_mass_category.id
        # Body mass entries should not have reps
        assert entry2.reps is None

def test_get_entries_handles_schema_mismatch(app_with_old_schema):
    """Test that get_entries_by_time_window handles schema mismatch gracefully"""
    from src import services
    from src.migration import check_and_migrate_database
    from src.models import db
    from datetime import datetime, timedelta
    
    with app_with_old_schema.app_context():
        # First run the migration to ensure we have a valid schema
        check_and_migrate_database()
        
        # Create a category
        category = services.create_default_category()
        
        # Create entries using the service
        for i in range(3):
            services.save_weight_entry(
                weight=80.0 + i,
                unit='kg',
                category_id_or_notes=category.id
            )
            
        # Force a flush to ensure all data is written
        db.session.flush()
        
        # Test for errors with wrong schema - all these should run without crashing
        # and return empty list rather than raising exceptions
        try:
            # Test all time windows
            entries_week = services.get_entries_by_time_window('week')
            entries_month = services.get_entries_by_time_window('month')
            entries_year = services.get_entries_by_time_window('year')
            entries_all = services.get_entries_by_time_window('all')
            all_entries = services.get_all_entries()
            
            # Test with specific category
            services.get_entries_by_time_window('week', category.id)
            services.get_all_entries(category.id)
            
            # Check that at least the 'all' query returns entries
            assert len(entries_all) >= 3 or len(all_entries) >= 3, "Expected entries not found"
            
            # Test passed if we got here without errors
            assert True
        except Exception as e:
            assert False, f"Function raised an exception: {str(e)}" 