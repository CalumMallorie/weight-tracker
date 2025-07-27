#!/usr/bin/env python3
"""
Simple test instance launcher - sets environment variables and uses main app
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

def main():
    """Start test instance by setting environment variables and using main app"""
    
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
    
    print("🧪 Starting Weight Tracker Test Instance")
    print("=" * 50)
    print(f"📍 URL: http://127.0.0.1:8081")
    print(f"🗄️  Database: {os.environ['DATABASE_PATH']}")
    print(f"📋 Logs: {logs_dir}")
    print(f"🔧 Debug mode: True")
    print(f"🏷️  Instance: TEST_INSTANCE")
    print()
    print("This is a SEPARATED test instance:")
    print("- Different port (8081 vs 8080)")
    print("- Separate database file")
    print("- Separate log files")
    print("- Test configuration")
    print()
    print("Press Ctrl+C to stop the test instance")
    print("-" * 50)
    
    # Import and run the main app (it will use our environment variables)
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