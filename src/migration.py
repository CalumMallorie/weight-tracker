import logging
import sqlite3
from sqlalchemy import inspect, text
from typing import List, Dict, Optional

from .models import db, WeightEntry, WeightCategory

# Set up logger
logger = logging.getLogger(__name__)

def check_and_migrate_database() -> None:
    """Check database schema and perform migrations if needed"""
    try:
        logger.info("Checking database schema for required migrations")
        
        # Get all tables first
        inspector = inspect(db.engine)
        
        # Check if database is completely new or needs complete setup
        needs_full_setup = False
        
        # Check if weight_entry table exists
        if not inspector.has_table("weight_entry"):
            logger.info("weight_entry table doesn't exist yet, performing full setup")
            needs_full_setup = True
        else:
            # Check weight_entry table columns
            columns = inspector.get_columns("weight_entry")
            column_names = set(col["name"] for col in columns)
            
            # Check if category_id is missing
            if "category_id" not in column_names:
                logger.info("weight_entry table exists but is missing the category_id column, will recreate tables")
                needs_full_setup = True
        
        if needs_full_setup:
            # If table doesn't exist or is missing fundamental columns, 
            # drop all tables and recreate
            _recreate_all_tables()
            logger.info("Database schema recreated")
            return
            
        # Check weight_entry table columns for missing newer columns
        columns = inspector.get_columns("weight_entry")
        column_names = set(col["name"] for col in columns)
        
        missing_columns = []
        
        # Check for missing reps column
        if "reps" not in column_names:
            missing_columns.append(("reps", "INTEGER"))
            
        # Check for missing notes column
        if "notes" not in column_names:
            missing_columns.append(("notes", "TEXT"))
        
        # Perform migration if needed
        if missing_columns:
            _migrate_weight_entry_schema(missing_columns)
            logger.info(f"Migration completed for weight_entry table")
        else:
            logger.info("Database schema is up-to-date, no migration needed")
    
    except Exception as e:
        logger.error(f"Error during database schema check/migration: {str(e)}")
        logger.info("Continuing with application startup despite migration error")

def _recreate_all_tables() -> None:
    """Drop all tables and recreate them"""
    logger.info("Recreating all database tables")
    try:
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        logger.info("All tables recreated successfully")
    except Exception as e:
        logger.error(f"Error recreating tables: {str(e)}")
        raise

def _migrate_weight_entry_schema(missing_columns: List[tuple]) -> None:
    """Add missing columns to weight_entry table"""
    logger.info(f"Migrating weight_entry table to add columns: {missing_columns}")
    
    try:
        # Get SQLite connection
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        
        # Add each missing column
        for column_name, column_type in missing_columns:
            logger.info(f"Adding column {column_name} ({column_type}) to weight_entry table")
            try:
                cursor.execute(f"ALTER TABLE weight_entry ADD COLUMN {column_name} {column_type}")
                # For reps column, set default value for non-body mass entries
                if column_name == "reps":
                    try:
                        # First find all non-body mass entries
                        cursor.execute("""
                            SELECT we.id 
                            FROM weight_entry we
                            JOIN weight_category wc ON we.category_id = wc.id
                            WHERE wc.is_body_mass = 0
                        """)
                        non_body_mass_entries = cursor.fetchall()
                        
                        # Set default value of 1 for non-body mass entries
                        if non_body_mass_entries:
                            ids = ','.join(str(entry[0]) for entry in non_body_mass_entries)
                            cursor.execute(f"UPDATE weight_entry SET reps = 1 WHERE id IN ({ids})")
                            logger.info(f"Set default reps=1 for {len(non_body_mass_entries)} non-body mass entries")
                    except sqlite3.OperationalError as e:
                        logger.warning(f"Error updating reps: {str(e)}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.warning(f"Column {column_name} already exists, skipping")
                else:
                    raise
        
        # Commit changes
        connection.commit()
        
        logger.info("Migration completed successfully")
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def verify_model_schema() -> Dict[str, bool]:
    """Verify if database schema matches model schema
    
    Returns a dictionary with table names as keys and boolean status as values
    """
    results = {}
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Check WeightEntry model
        if "weight_entry" in tables:
            model_columns = {c.name for c in WeightEntry.__table__.columns}
            db_columns = {c["name"] for c in inspector.get_columns("weight_entry")}
            results["weight_entry"] = model_columns.issubset(db_columns)
        else:
            results["weight_entry"] = False
            
        # Check WeightCategory model
        if "weight_category" in tables:
            model_columns = {c.name for c in WeightCategory.__table__.columns}
            db_columns = {c["name"] for c in inspector.get_columns("weight_category")}
            results["weight_category"] = model_columns.issubset(db_columns)
        else:
            results["weight_category"] = False
            
        return results
    except Exception as e:
        logger.error(f"Error verifying model schema: {str(e)}")
        return {"error": False}

def migrate_db_v5(db):
    """
    Migration v5: Add last_used_at to WeightCategory and remove notes from WeightEntry
    """
    try:
        # Add last_used_at column to weight_category
        db.session.execute("""
            ALTER TABLE weight_category 
            ADD COLUMN last_used_at TIMESTAMP
        """)
        
        # Remove notes column from weight_entry
        db.session.execute("""
            ALTER TABLE weight_entry 
            DROP COLUMN notes
        """)
        
        # Update schema version
        db.session.execute("""
            UPDATE schema_version 
            SET version = 5 
            WHERE id = 1
        """)
        
        db.session.commit()
        print("Migration v5 completed successfully")
        return True
    except Exception as e:
        print(f"Error in migration v5: {e}")
        db.session.rollback()
        return False

# Update migrations list
MIGRATIONS = [
    migrate_db_v1,
    migrate_db_v2,
    migrate_db_v3,
    migrate_db_v4,
    migrate_db_v5
] 