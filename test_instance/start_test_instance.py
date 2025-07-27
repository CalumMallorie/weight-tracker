#!/usr/bin/env python3
"""
Weight Tracker Test Instance Launcher
Starts a separated test instance of the Weight Tracker webapp
"""

import sys
import os
from pathlib import Path

# Add the repository root to Python path (like tools/launch_app.py)
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import test configuration
from test_config import get_test_config

def create_test_app():
    """Create Weight Tracker app configured for test instance"""
    
    # Import main app components
    from src.app import create_app
    from dummy_data import initialize_dummy_data
    
    # Get test configuration
    config = get_test_config()
    
    # Set environment variables for test instance
    os.environ['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    os.environ['SECRET_KEY'] = config.SECRET_KEY
    os.environ['ENV_NAME'] = config.ENV_NAME
    
    # Create app with test settings
    app = create_app()
    
    # Override configuration
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': config.SQLALCHEMY_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': config.SQLALCHEMY_TRACK_MODIFICATIONS,
        'SECRET_KEY': config.SECRET_KEY,
        'DEBUG': config.DEBUG,
        'TESTING': config.TESTING,
        'ENV_NAME': config.ENV_NAME
    })
    
    # Initialize dummy data if enabled
    if getattr(config, 'USE_DUMMY_DATA', False):
        initialize_dummy_data(app)
    
    return app, config

def main():
    """Start the test instance"""
    
    print("🧪 Starting Weight Tracker Test Instance")
    print("=" * 50)
    
    try:
        # Create test app
        app, config = create_test_app()
        
        print(f"✅ Test instance configured")
        print(f"📍 URL: http://{config.HOST}:{config.PORT}")
        print(f"🗄️  Database: {config.DATABASE_PATH}")
        print(f"📋 Logs: {config.LOG_FILE}")
        print(f"🔧 Debug mode: {config.DEBUG}")
        print(f"🏷️  Instance: {config.INSTANCE_NAME}")
        if getattr(config, 'USE_DUMMY_DATA', False):
            print(f"🎭 Dummy data: Enabled (realistic test data)")
        print()
        print("This is a SEPARATED test instance - different from main app:")
        print("- Different port (8081 vs 8080)")
        print("- Separate database with dummy data")
        print("- Separate log files")
        print("- Test configuration")
        print("- Pre-populated with 3 months of realistic exercise data")
        print()
        print("Press Ctrl+C to stop the test instance")
        print("-" * 50)
        
        # Start the test server
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Test instance stopped by user")
    except Exception as e:
        print(f"❌ Error starting test instance: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()