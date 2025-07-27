"""
Dummy Data Generator for Weight Tracker Test Instance
Creates realistic test data for development and testing
"""

from datetime import datetime, timedelta
import random
import sys
import os
from pathlib import Path

# Add the repository root to Python path (like tools/launch_app.py)
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


def create_dummy_categories(db, WeightCategory):
    """Create realistic weight categories"""
    categories = [
        # Body weight tracking
        {
            'name': 'Body Weight',
            'is_body_mass': True,
            'is_body_weight_exercise': False
        },
        
        # Regular weight exercises
        {
            'name': 'Bench Press',
            'is_body_mass': False,
            'is_body_weight_exercise': False
        },
        {
            'name': 'Squat',
            'is_body_mass': False,
            'is_body_weight_exercise': False
        },
        {
            'name': 'Deadlift',
            'is_body_mass': False,
            'is_body_weight_exercise': False
        },
        {
            'name': 'Overhead Press',
            'is_body_mass': False,
            'is_body_weight_exercise': False
        },
        {
            'name': 'Bicep Curls',
            'is_body_mass': False,
            'is_body_weight_exercise': False
        },
        
        # Bodyweight exercises
        {
            'name': 'Push-ups',
            'is_body_mass': False,
            'is_body_weight_exercise': True
        },
        {
            'name': 'Pull-ups',
            'is_body_mass': False,
            'is_body_weight_exercise': True
        },
        {
            'name': 'Plank Hold',
            'is_body_mass': False,
            'is_body_weight_exercise': True
        }
    ]
    
    created_categories = []
    for cat_data in categories:
        category = WeightCategory(**cat_data)
        db.session.add(category)
        created_categories.append(category)
    
    db.session.commit()
    return created_categories


def create_dummy_entries(categories, db, WeightEntry):
    """Create realistic weight entries for the past 3 months"""
    
    # Define exercise progressions and starting points
    exercise_data = {
        'Body Weight': {
            'start_weight': 175.0,
            'trend': -0.5,  # Losing weight
            'variation': 2.0
        },
        'Bench Press': {
            'start_weight': 135.0,
            'trend': 2.5,  # Progressive overload
            'variation': 5.0,
            'start_reps': 8,
            'rep_variation': 2
        },
        'Squat': {
            'start_weight': 185.0,
            'trend': 3.0,
            'variation': 7.5,
            'start_reps': 5,
            'rep_variation': 1
        },
        'Deadlift': {
            'start_weight': 225.0,
            'trend': 2.5,
            'variation': 10.0,
            'start_reps': 3,
            'rep_variation': 1
        },
        'Overhead Press': {
            'start_weight': 95.0,
            'trend': 1.5,
            'variation': 2.5,
            'start_reps': 6,
            'rep_variation': 2
        },
        'Bicep Curls': {
            'start_weight': 25.0,
            'trend': 0.5,
            'variation': 2.5,
            'start_reps': 12,
            'rep_variation': 3
        },
        'Push-ups': {
            'start_reps': 20,
            'trend_reps': 1.0,
            'rep_variation': 5
        },
        'Pull-ups': {
            'start_reps': 8,
            'trend_reps': 0.5,
            'rep_variation': 3
        },
        'Plank Hold': {
            'start_reps': 45,  # seconds
            'trend_reps': 2.0,
            'rep_variation': 10
        }
    }
    
    # Create entries for the past 90 days
    start_date = datetime.now() - timedelta(days=90)
    
    for category in categories:
        if category.name not in exercise_data:
            continue
            
        data = exercise_data[category.name]
        
        # Create entries with realistic frequency
        current_date = start_date
        entry_count = 0
        
        while current_date <= datetime.now():
            # Skip some days randomly (not every day)
            if random.random() < 0.7:  # 70% chance of workout
                days_elapsed = (current_date - start_date).days
                
                if category.is_body_mass:
                    # Body weight - just weight, no reps
                    weight = (data['start_weight'] + 
                             (days_elapsed * data['trend'] / 30) +
                             random.uniform(-data['variation'], data['variation']))
                    weight = max(100.0, round(weight, 1))  # Keep realistic
                    
                    entry = WeightEntry(
                        weight=weight,
                        unit='kg',
                        reps=None,
                        created_at=current_date,
                        category_id=category.id
                    )
                    
                elif category.is_body_weight_exercise:
                    # Bodyweight exercise - just reps, no weight
                    reps = (data['start_reps'] + 
                           (days_elapsed * data['trend_reps'] / 30) +
                           random.uniform(-data['rep_variation'], data['rep_variation']))
                    reps = max(1, round(reps))
                    
                    entry = WeightEntry(
                        weight=0.0,
                        unit='kg',
                        reps=reps,
                        created_at=current_date,
                        category_id=category.id
                    )
                    
                else:
                    # Regular exercise - both weight and reps
                    weight = (data['start_weight'] + 
                             (days_elapsed * data['trend'] / 30) +
                             random.uniform(-data['variation'], data['variation']))
                    weight = max(5.0, round(weight, 1))
                    
                    reps = (data['start_reps'] + 
                           random.randint(-data['rep_variation'], data['rep_variation']))
                    reps = max(1, reps)
                    
                    entry = WeightEntry(
                        weight=weight,
                        unit='kg',
                        reps=reps,
                        created_at=current_date,
                        category_id=category.id
                    )
                
                db.session.add(entry)
                entry_count += 1
            
            # Move to next day (or skip 1-3 days for exercises)
            if category.is_body_mass:
                current_date += timedelta(days=1)  # Daily weigh-ins
            else:
                current_date += timedelta(days=random.randint(1, 4))  # 1-4 days between workouts
        
        print(f"Created {entry_count} entries for {category.name}")
    
    db.session.commit()


def initialize_dummy_data(app):
    """Initialize the test database with dummy data"""
    
    print("🗃️  Initializing dummy data for test instance...")
    
    with app.app_context():
        # Import models within app context
        from src.models import WeightCategory, WeightEntry, db
        
        # Clear existing data
        WeightEntry.query.delete()
        WeightCategory.query.delete()
        db.session.commit()
        
        # Create categories
        print("📝 Creating weight categories...")
        categories = create_dummy_categories(db, WeightCategory)
        
        # Create entries
        print("📊 Creating weight entries...")
        create_dummy_entries(categories, db, WeightEntry)
        
        # Summary
        category_count = WeightCategory.query.count()
        entry_count = WeightEntry.query.count()
        
        print(f"✅ Dummy data created successfully!")
        print(f"   - {category_count} categories")
        print(f"   - {entry_count} entries")
        print(f"   - Data spans last 90 days")
        print()


if __name__ == '__main__':
    # For standalone testing
    from test_config import get_test_config
    from src.app import create_app
    
    config = get_test_config()
    app = create_app()
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': config.SQLALCHEMY_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': config.SQLALCHEMY_TRACK_MODIFICATIONS,
    })
    
    initialize_dummy_data(app)