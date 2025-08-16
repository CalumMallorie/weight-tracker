#!/usr/bin/env python3
"""
Script to test migration compatibility with pre-update database.

This script:
1. Copies the pre-update database
2. Runs the migration process
3. Validates the results
"""

import os
import shutil
import sqlite3
from src.app import create_app
from src.models import db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_migration(source_db: str = "pre_update_test.db", test_db: str = "migration_test.db"):
    """Test migration process with pre-update database"""
    
    # Copy the pre-update database for testing
    if not os.path.exists(source_db):
        logger.error(f"Source database {source_db} not found!")
        logger.error("Please run create_pre_update_database.py first")
        return False
    
    # Remove existing test database
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Copy pre-update database
    shutil.copy2(source_db, test_db)
    logger.info(f"Copied {source_db} to {test_db}")
    
    # Verify pre-migration state
    logger.info("Verifying pre-migration state...")
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Check if user table exists (should not exist in pre-update)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    user_table_exists = cursor.fetchone() is not None
    logger.info(f"User table exists before migration: {user_table_exists}")
    
    # Check category and entry counts
    cursor.execute("SELECT COUNT(*) FROM weight_category")
    category_count_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM weight_entry")
    entry_count_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM weight_entry WHERE category_id IS NULL")
    null_category_count_before = cursor.fetchone()[0]
    
    logger.info(f"Categories before migration: {category_count_before}")
    logger.info(f"Entries before migration: {entry_count_before}")
    logger.info(f"Entries without category before migration: {null_category_count_before}")
    
    # Check if user_id columns exist (should not exist in pre-update)
    cursor.execute("PRAGMA table_info(weight_category)")
    category_columns = [col[1] for col in cursor.fetchall()]
    has_user_id_category = 'user_id' in category_columns
    
    cursor.execute("PRAGMA table_info(weight_entry)")
    entry_columns = [col[1] for col in cursor.fetchall()]
    has_user_id_entry = 'user_id' in entry_columns
    
    logger.info(f"weight_category has user_id column before migration: {has_user_id_category}")
    logger.info(f"weight_entry has user_id column before migration: {has_user_id_entry}")
    
    conn.close()
    
    # Run migration using Flask app
    logger.info("Starting migration process...")
    
    try:
        # Use absolute path for database
        abs_test_db = os.path.abspath(test_db)
        app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{abs_test_db}',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key'
        })
        
        with app.app_context():
            logger.info("Migration completed successfully!")
            
            # Verify post-migration state
            logger.info("Verifying post-migration state...")
            
            # Check if user table exists (should exist after migration)
            from src.models import User
            try:
                default_user = User.query.filter_by(username='default').first()
                logger.info(f"Default user created: {default_user is not None}")
                if default_user:
                    logger.info(f"Default user ID: {default_user.id}")
            except Exception as e:
                logger.error(f"Error checking default user: {e}")
            
            # Check category and entry counts
            from src.models import WeightCategory, WeightEntry
            
            category_count_after = WeightCategory.query.count()
            entry_count_after = WeightEntry.query.count()
            
            logger.info(f"Categories after migration: {category_count_after}")
            logger.info(f"Entries after migration: {entry_count_after}")
            
            # Check if all categories have user_id
            categories_without_user = WeightCategory.query.filter_by(user_id=None).count()
            logger.info(f"Categories without user_id after migration: {categories_without_user}")
            
            # Check if all entries have user_id
            entries_without_user = WeightEntry.query.filter_by(user_id=None).count()
            logger.info(f"Entries without user_id after migration: {entries_without_user}")
            
            # Check if entries without category were migrated
            entries_without_category = WeightEntry.query.filter_by(category_id=None).count()
            logger.info(f"Entries without category after migration: {entries_without_category}")
            
            # Validate data integrity
            logger.info("Validating data integrity...")
            
            # Check Body Mass category exists and is properly configured
            body_mass = WeightCategory.query.filter_by(name='Body Mass').first()
            if body_mass:
                logger.info(f"Body Mass category: is_body_mass={body_mass.is_body_mass}, is_body_weight_exercise={body_mass.is_body_weight_exercise}")
                if body_mass.is_body_mass and not body_mass.is_body_weight_exercise:
                    logger.info("✅ Body Mass category correctly configured")
                else:
                    logger.error("❌ Body Mass category misconfigured!")
            
            # Check if all data was preserved
            if (category_count_after >= category_count_before and 
                entry_count_after >= entry_count_before and
                categories_without_user == 0 and
                entries_without_user == 0):
                logger.info("✅ Migration completed successfully!")
                
                # Test basic functionality
                logger.info("Testing basic functionality...")
                
                try:
                    from src import services
                    
                    # Test creating a new entry
                    test_category = WeightCategory.query.filter_by(name='Bench Press').first()
                    if test_category and default_user:
                        test_entry = services.save_weight_entry(
                            weight=100.0,
                            unit='kg',
                            category_id_or_notes=test_category.id,
                            reps=5,
                            user_id=default_user.id
                        )
                        logger.info(f"✅ Successfully created test entry: {test_entry.id}")
                    
                    # Test retrieving entries
                    user_entries = services.get_all_entries(user_id=default_user.id)
                    logger.info(f"✅ Retrieved {len(user_entries)} entries for default user")
                    
                    # Test retrieving categories
                    user_categories = services.get_all_categories(user_id=default_user.id)
                    logger.info(f"✅ Retrieved {len(user_categories)} categories for default user")
                    
                except Exception as e:
                    logger.error(f"❌ Error testing basic functionality: {e}")
                
                return True
                
            else:
                logger.error("❌ Migration validation failed!")
                logger.error(f"Categories: {category_count_before} -> {category_count_after}")
                logger.error(f"Entries: {entry_count_before} -> {entry_count_after}")
                logger.error(f"Categories without user_id: {categories_without_user}")
                logger.error(f"Entries without user_id: {entries_without_user}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_migration()
    if success:
        print("\n🎉 Migration test PASSED!")
    else:
        print("\n💥 Migration test FAILED!")
        exit(1)