#!/usr/bin/env python3
"""
Basic test that just tries to start Flask without migrations
"""

import os
import sys
from pathlib import Path

def main():
    print("🧪 Basic Flask Test")
    print("=" * 30)
    
    try:
        # Handle path issues
        script_path = Path(__file__).resolve()
        repo_root = script_path.parent.parent
        
        if repo_root.name == 'test_server':
            repo_root = repo_root.parent
            
        sys.path.insert(0, str(repo_root))
        print(f"✅ Repository root: {repo_root}")
        
        # Test instance configuration
        test_instance_dir = script_path.parent
        instance_dir = test_instance_dir / "instance"
        logs_dir = test_instance_dir / "logs"
        
        # Ensure directories exist
        instance_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
        print(f"✅ Directories created: {instance_dir}, {logs_dir}")
        
        # Set minimal environment variables
        os.environ['PORT'] = '8081'
        os.environ['FLASK_DEBUG'] = 'true'
        os.environ['DATABASE_PATH'] = str(instance_dir / "test.db")
        os.environ['INSTANCE_PATH'] = str(instance_dir)
        print("✅ Environment variables set")
        
        # Try importing Flask app
        from src.app import create_app
        print("✅ Flask app imported")
        
        # Try creating app
        app = create_app()
        print("✅ Flask app created")
        
        print(f"📍 Ready to start on http://127.0.0.1:8081")
        print("Starting Flask development server...")
        
        # Start with minimal configuration
        app.run(
            host='127.0.0.1',
            port=8081,
            debug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()