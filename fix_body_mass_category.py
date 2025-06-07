#!/usr/bin/env python3
"""
Fix Body Mass category flags in the database.

The issue: Body Mass category has both is_body_mass=True AND is_body_weight=True
This causes the system to treat body mass entries as body weight exercises,
setting weight to 0 instead of using the submitted weight.

Solution: Set is_body_weight=False for Body Mass category.
"""

import sqlite3
import sys
from pathlib import Path

def fix_body_mass_category(db_path: str = "user_instance/instance/weight_tracker.db"):
    """Fix the Body Mass category flags in the database"""
    
    if not Path(db_path).exists():
        print(f"Database file not found: {db_path}")
        print("Please make sure you're running this from the weight-tracker directory")
        sys.exit(1)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current state
        cursor.execute("SELECT id, name, is_body_mass, is_body_weight FROM weight_category WHERE name = 'Body Mass'")
        result = cursor.fetchone()
        
        if not result:
            print("Body Mass category not found in database")
            return
        
        cat_id, name, is_body_mass, is_body_weight = result
        print(f"Current state - ID: {cat_id}, Name: {name}")
        print(f"  is_body_mass: {bool(is_body_mass)}")
        print(f"  is_body_weight: {bool(is_body_weight)}")
        
        if is_body_mass and is_body_weight:
            print("\nFIXING: Body Mass category has both flags set to True!")
            print("Setting is_body_weight = False for Body Mass category...")
            
            # Fix the issue
            cursor.execute(
                "UPDATE weight_category SET is_body_weight = 0 WHERE id = ? AND name = 'Body Mass'",
                (cat_id,)
            )
            conn.commit()
            
            # Verify the fix
            cursor.execute("SELECT id, name, is_body_mass, is_body_weight FROM weight_category WHERE id = ?", (cat_id,))
            result = cursor.fetchone()
            cat_id, name, is_body_mass, is_body_weight = result
            
            print(f"\nAfter fix - ID: {cat_id}, Name: {name}")
            print(f"  is_body_mass: {bool(is_body_mass)}")
            print(f"  is_body_weight: {bool(is_body_weight)}")
            print("\n✅ Body Mass category fixed!")
            
        elif is_body_mass and not is_body_weight:
            print("✅ Body Mass category is already correctly configured")
            
        else:
            print("⚠️  Body Mass category has unexpected configuration")
            print("Expected: is_body_mass=True, is_body_weight=False")
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_body_mass_category() 