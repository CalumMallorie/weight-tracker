import os
import sqlite3
import logging
from flask import Flask
from src.models import db
from src.migration import check_and_migrate_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_migrate():
    """Test the migration process on our test database"""
    # Get absolute path to the test database
    db_path = os.path.abspath('test_data/old_database.db')
    logger.info(f"Using database at: {db_path}")
    
    # Set up app with the test database
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the app
    db.init_app(app)
    
    with app.app_context():
        # Check initial schema
        logger.info("Initial database schema:")
        check_db_schema(db_path)
        
        # Run migration
        logger.info("Running migration...")
        check_and_migrate_database()
        
        # Check final schema
        logger.info("Final database schema after migration:")
        check_db_schema(db_path)
        
        # Verify data is preserved
        logger.info("Verifying data was preserved:")
        check_data(db_path)

def check_db_schema(db_path):
    """Check the schema of the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    logger.info(f"Tables in database: {', '.join(t[0] for t in tables)}")
    
    # Get schema for each table
    for table in tables:
        table_name = table[0]
        if table_name.startswith('sqlite_'):
            continue
            
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        logger.info(f"Columns in {table_name}: {', '.join(col[1] for col in columns)}")
    
    conn.close()

def check_data(db_path):
    """Check that data was preserved in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check categories
    cursor.execute("SELECT id, name, is_body_mass FROM weight_category")
    categories = cursor.fetchall()
    logger.info(f"Categories: {categories}")
    
    # Check entries
    cursor.execute("SELECT id, weight, unit, category_id, reps FROM weight_entry")
    entries = cursor.fetchall()
    logger.info(f"Entries: {entries}")
    
    conn.close()

if __name__ == "__main__":
    test_migrate() 