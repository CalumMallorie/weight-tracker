"""
Test Instance Configuration
Separated configuration for test instance of Weight Tracker
"""

import os
from pathlib import Path

# Test instance paths
TEST_BASE_DIR = Path(__file__).parent
TEST_INSTANCE_DIR = TEST_BASE_DIR / "instance"
TEST_LOGS_DIR = TEST_BASE_DIR / "logs"

# Ensure directories exist
TEST_INSTANCE_DIR.mkdir(exist_ok=True)
TEST_LOGS_DIR.mkdir(exist_ok=True)

class TestInstanceConfig:
    """Configuration for test instance"""
    
    # Server settings - different port from main app
    HOST = '127.0.0.1'
    PORT = 8081  # Different from main app (8080)
    DEBUG = True
    
    # Database - separate test database with dummy data
    DATABASE_PATH = TEST_INSTANCE_DIR / "weight_tracker_test.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Logging - separate log file
    LOG_FILE = TEST_LOGS_DIR / "test_app.log"
    LOG_LEVEL = "DEBUG"
    
    # Flask settings
    SECRET_KEY = "test-instance-secret-key-change-in-production"
    TESTING = True
    
    # Environment identification
    ENV_NAME = "TEST_INSTANCE"
    INSTANCE_NAME = "Weight Tracker Test Instance"
    
    # Test data settings
    USE_DUMMY_DATA = True

def get_test_config():
    """Get test instance configuration"""
    return TestInstanceConfig()