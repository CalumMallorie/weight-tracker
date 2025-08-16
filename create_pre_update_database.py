#!/usr/bin/env python3
"""
Script to create a comprehensive pre-update database with sample data.

This simulates the old database schema before multi-user migration,
allowing us to test the migration process thoroughly.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_pre_update_database(db_path: str = "pre_update_test.db"):
    """Create a database with the old schema and sample data"""
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creating pre-update database at: {db_path}")
    
    # Create old schema tables (without user_id columns)
    print("Creating old schema tables...")
    
    # Weight category table (old schema - no user_id)
    cursor.execute('''
        CREATE TABLE weight_category (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            is_body_mass BOOLEAN DEFAULT 0,
            is_body_weight_exercise BOOLEAN DEFAULT 0,
            created_at DATETIME,
            last_used_at DATETIME
        )
    ''')
    
    # Weight entry table (old schema - no user_id)
    cursor.execute('''
        CREATE TABLE weight_entry (
            id INTEGER PRIMARY KEY,
            weight REAL NOT NULL,
            unit VARCHAR(10) NOT NULL,
            reps INTEGER,
            category_id INTEGER REFERENCES weight_category(id),
            created_at DATETIME
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_weight_entry_category_id ON weight_entry(category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_weight_entry_created_at ON weight_entry(created_at)')
    
    print("Inserting sample categories...")
    
    # Insert sample categories
    categories = [
        ("Body Mass", 1, 0),  # Body mass category
        ("Bench Press", 0, 0),  # Regular exercise
        ("Push-ups", 0, 1),  # Body weight exercise
        ("Squats", 0, 0),  # Regular exercise
        ("Pull-ups", 0, 1),  # Body weight exercise
        ("Deadlift", 0, 0),  # Regular exercise
        ("Running", 0, 0),  # Could be time-based
        ("Plank", 0, 1),  # Body weight exercise
    ]
    
    base_time = datetime.now()
    
    for i, (name, is_body_mass, is_body_weight_exercise) in enumerate(categories):
        created_at = base_time - timedelta(days=30-i)
        last_used_at = base_time - timedelta(days=random.randint(1, 10))
        
        cursor.execute('''
            INSERT INTO weight_category (name, is_body_mass, is_body_weight_exercise, created_at, last_used_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, is_body_mass, is_body_weight_exercise, created_at, last_used_at))
    
    print("Inserting sample weight entries...")
    
    # Get category IDs
    cursor.execute('SELECT id, name, is_body_mass, is_body_weight_exercise FROM weight_category')
    category_data = cursor.fetchall()
    
    # Generate sample entries for each category
    entry_count = 0
    for category_id, category_name, is_body_mass, is_body_weight_exercise in category_data:
        entries_for_category = random.randint(5, 20)  # 5-20 entries per category
        
        for i in range(entries_for_category):
            entry_date = base_time - timedelta(days=random.randint(1, 90))
            
            if is_body_mass:
                # Body mass entries: weight only, no reps
                weight = random.uniform(70, 90)  # kg
                unit = 'kg'
                reps = None
            elif is_body_weight_exercise:
                # Body weight exercises: reps only, weight from body mass
                weight = random.uniform(70, 90)  # Use body weight
                unit = 'kg'
                reps = random.randint(5, 30)
            else:
                # Regular exercises: both weight and reps
                if category_name == "Bench Press":
                    weight = random.uniform(60, 120)
                elif category_name == "Squats":
                    weight = random.uniform(80, 150)
                elif category_name == "Deadlift":
                    weight = random.uniform(100, 180)
                elif category_name == "Running":
                    weight = 0  # Time-based exercise
                else:
                    weight = random.uniform(20, 100)
                
                unit = 'kg'
                reps = random.randint(1, 15) if weight > 0 else 1
            
            cursor.execute('''
                INSERT INTO weight_entry (weight, unit, reps, category_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (weight, unit, reps, category_id, entry_date))
            
            entry_count += 1
    
    print(f"Inserted {entry_count} sample weight entries")
    
    # Add some entries without category_id to test migration
    print("Adding entries without category_id for migration testing...")
    
    for i in range(5):
        entry_date = base_time - timedelta(days=random.randint(1, 30))
        weight = random.uniform(70, 90)
        
        cursor.execute('''
            INSERT INTO weight_entry (weight, unit, reps, category_id, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (weight, 'kg', None, None, entry_date))
    
    # Add some problematic data to test edge cases
    print("Adding edge case data...")
    
    # Entry with zero weight (should be caught by validation)
    cursor.execute('''
        INSERT INTO weight_entry (weight, unit, reps, category_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (0.0, 'kg', 1, 1, base_time - timedelta(days=1)))
    
    # Entry with very high reps
    cursor.execute('''
        INSERT INTO weight_entry (weight, unit, reps, category_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (50.0, 'kg', 100, 2, base_time - timedelta(days=2)))
    
    # Commit changes
    conn.commit()
    
    # Print summary
    cursor.execute('SELECT COUNT(*) FROM weight_category')
    category_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM weight_entry')
    entry_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM weight_entry WHERE category_id IS NULL')
    null_category_count = cursor.fetchone()[0]
    
    print(f"\nDatabase created successfully!")
    print(f"Categories: {category_count}")
    print(f"Total entries: {entry_count}")
    print(f"Entries without category: {null_category_count}")
    
    # Verify data integrity
    print("\nData integrity check:")
    cursor.execute('''
        SELECT wc.name, COUNT(we.id) as entry_count
        FROM weight_category wc
        LEFT JOIN weight_entry we ON wc.id = we.category_id
        GROUP BY wc.id, wc.name
        ORDER BY entry_count DESC
    ''')
    
    for category_name, count in cursor.fetchall():
        print(f"  {category_name}: {count} entries")
    
    conn.close()
    print(f"\nPre-update database saved as: {db_path}")
    return db_path

if __name__ == "__main__":
    create_pre_update_database()