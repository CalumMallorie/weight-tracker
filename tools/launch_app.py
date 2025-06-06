#!/usr/bin/env python3
"""
Launch script for Weight Tracker app.
Starts the Flask app locally and opens it in the default browser.
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add the parent directory to the Python path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import create_app


def open_browser(url: str, delay: float = 1.5) -> None:
    """
    Open the default browser to the app URL after a short delay.
    
    Args:
        url: The URL to open
        delay: Seconds to wait before opening browser
    """
    def _open():
        time.sleep(delay)
        print(f"Opening browser to {url}")
        webbrowser.open(url)
    
    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    """Launch the app and open browser."""
    # Set development environment variables
    os.environ['FLASK_DEBUG'] = 'true'
    os.environ.setdefault('PORT', '5000')
    
    port = int(os.environ.get('PORT', 5000))
    url = f"http://localhost:{port}"
    
    print("=" * 50)
    print("🚀 Starting Weight Tracker App")
    print("=" * 50)
    print(f"Port: {port}")
    print(f"URL: {url}")
    print(f"Debug mode: True")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Schedule browser opening
    open_browser(url)
    
    # Create and run the app
    app = create_app()
    
    try:
        app.run(
            debug=True,
            host='127.0.0.1',  # Only localhost for security
            port=port,
            use_reloader=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Weight Tracker App")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 