#!/usr/bin/env python3
"""
Minimal test to isolate import issues
"""

print("Starting minimal test...")

try:
    import sys
    from pathlib import Path
    print("✅ Basic imports work")
    
    # Add repository root to path
    REPO_ROOT = Path(__file__).parent.parent
    sys.path.insert(0, str(REPO_ROOT))
    print(f"✅ Added repo root to path: {REPO_ROOT}")
    
    # Test main app import
    from src.app import create_app
    print("✅ Main app import successful")
    
    # Test app creation
    app = create_app()
    print("✅ App creation successful")
    
    print("🎉 All basic tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()