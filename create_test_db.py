import sqlite3
import os
from datetime import datetime

def create_test_database():
    """Create a test database with the old schema (missing last_used_at column)"""
    # Ensure the directory exists
    os.makedirs('test_data', exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists('test_data/old_database.db'):
        os.remove('test_data/old_database.db')
    
    # Create and connect to the database
    conn = sqlite3.connect('test_data/old_database.db')
    cursor = conn.cursor()
    
    # Create weight_category table (old schema, missing last_used_at)
    cursor.execute('''
    CREATE TABLE weight_category (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        is_body_mass BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create weight_entry table
    cursor.execute('''
    CREATE TABLE weight_entry (
        id INTEGER PRIMARY KEY,
        weight FLOAT NOT NULL,
        unit TEXT NOT NULL,
        category_id INTEGER REFERENCES weight_category(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reps INTEGER
    )
    ''')
    
    # Add some test data
    current_time = datetime.utcnow().isoformat()
    
    # Insert categories
    cursor.execute("INSERT INTO weight_category (name, is_body_mass, created_at) VALUES (?, ?, ?)", 
                  ('Body Mass', 1, current_time))
    cursor.execute("INSERT INTO weight_category (name, is_body_mass, created_at) VALUES (?, ?, ?)", 
                  ('Bench Press', 0, current_time))
    
    # Insert entries
    cursor.execute("INSERT INTO weight_entry (weight, unit, category_id, reps, created_at) VALUES (?, ?, ?, ?, ?)", 
                  (80.5, 'kg', 1, None, current_time))
    cursor.execute("INSERT INTO weight_entry (weight, unit, category_id, reps, created_at) VALUES (?, ?, ?, ?, ?)", 
                  (100, 'kg', 2, 5, current_time))
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("Test database created at test_data/old_database.db")

if __name__ == "__main__":
    create_test_database() 