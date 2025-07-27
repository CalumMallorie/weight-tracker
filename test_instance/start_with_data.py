#!/usr/bin/env python3
"""
Test instance launcher with dummy data initialization
"""

import os
import sys
from pathlib import Path

# Add repository root to path - handle being in subdirectories
script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent

# If we're in a subdirectory like test_server, go up one more level
if repo_root.name == 'test_server':
    repo_root = repo_root.parent

sys.path.insert(0, str(repo_root))
print(f"Repository root: {repo_root}")

def initialize_test_data():
    """Initialize dummy data for test instance"""
    print("🗃️  Checking for existing data...")
    
    # Set up the app to initialize dummy data
    from src.app import create_app
    
    app = create_app()
    
    with app.app_context():
        from src.models import WeightCategory, WeightEntry, db
        
        # Check if we already have data
        if WeightCategory.query.count() > 0:
            print(f"✅ Found existing data: {WeightCategory.query.count()} categories, {WeightEntry.query.count()} entries")
            return
        
        print("📝 Creating dummy data...")
        
        # Import dummy data creation functions
        from test_instance.dummy_data import create_dummy_categories, create_dummy_entries
        
        # Create categories and entries
        categories = create_dummy_categories(db, WeightCategory)
        create_dummy_entries(categories, db, WeightEntry)
        
        print(f"✅ Dummy data created: {WeightCategory.query.count()} categories, {WeightEntry.query.count()} entries")

def main():
    """Start test instance with dummy data"""
    
    # Test instance configuration
    test_instance_dir = Path(__file__).parent
    instance_dir = test_instance_dir / "instance"
    logs_dir = test_instance_dir / "logs"
    
    # Ensure directories exist
    instance_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    
    # Set environment variables for test instance
    os.environ['PORT'] = '8081'
    os.environ['FLASK_DEBUG'] = 'true'
    os.environ['DATABASE_PATH'] = str(instance_dir / "weight_tracker_test.db")
    os.environ['INSTANCE_PATH'] = str(instance_dir)
    os.environ['LOG_DIR'] = str(logs_dir)
    os.environ['ENV_NAME'] = 'TEST_INSTANCE'
    
    print("🧪 Starting Weight Tracker Test Instance with Dummy Data")
    print("=" * 60)
    
    # Initialize dummy data
    try:
        initialize_test_data()
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize dummy data: {e}")
        print("Continuing with empty database...")
    
    print()
    print(f"📍 URL: http://127.0.0.1:8081")
    print(f"🗄️  Database: {os.environ['DATABASE_PATH']}")
    print(f"📋 Logs: {logs_dir}")
    print(f"🔧 Debug mode: True")
    print(f"🏷️  Instance: TEST_INSTANCE")
    print(f"🎭 Dummy data: Enabled")
    print()
    print("This is a SEPARATED test instance:")
    print("- Different port (8081 vs 8080)")
    print("- Separate database with realistic test data")
    print("- Separate log files")
    print("- 3 months of exercise data for testing")
    print()
    print("Press Ctrl+C to stop the test instance")
    print("-" * 60)
    
    # Import and run the main app
    try:
        from src.app import run_app
        run_app()
    except KeyboardInterrupt:
        print("\n🛑 Test instance stopped by user")
    except Exception as e:
        print(f"❌ Error starting test instance: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()