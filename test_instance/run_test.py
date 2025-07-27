#!/usr/bin/env python3
"""
Simple test runner for debugging the test instance
"""

import sys
import os
from pathlib import Path

# Get the repository root and add it to path (like tools/launch_app.py)
REPO_ROOT = Path(__file__).parent.parent
test_path = REPO_ROOT / "test_instance"

print(f"Repository root: {REPO_ROOT}")
print(f"Test path: {test_path}")

# Add paths to Python path
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(test_path))

try:
    print("Importing test config...")
    from test_config import get_test_config
    config = get_test_config()
    print(f"✅ Test config loaded: {config.INSTANCE_NAME}")
    
    print("Importing Flask app...")
    from src.app import create_app
    print("✅ Flask app imported")
    
    print("Creating app instance...")
    app = create_app()
    print("✅ App instance created")
    
    # Update config
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': config.SQLALCHEMY_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': config.SQLALCHEMY_TRACK_MODIFICATIONS,
        'SECRET_KEY': config.SECRET_KEY,
        'DEBUG': config.DEBUG,
        'TESTING': config.TESTING,
        'ENV_NAME': config.ENV_NAME
    })
    print("✅ App config updated")
    
    # Initialize dummy data
    if getattr(config, 'USE_DUMMY_DATA', False):
        print("Importing dummy data...")
        from dummy_data import initialize_dummy_data
        initialize_dummy_data(app)
    
    print(f"\n🚀 Starting test instance on http://{config.HOST}:{config.PORT}")
    print("Press Ctrl+C to stop")
    
    # Start the server
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed and paths are correct")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()