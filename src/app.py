from flask import Flask, send_from_directory
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from .models import db
from .routes import main as main_blueprint, api
from .auth_routes import auth_bp
from .auth import init_login
from . import services
from . import migration
from pathlib import Path
import threading
import secrets

def create_app(test_config=None):
    """Application factory function"""
    # Set custom instance path to a directory we can write to
    instance_path = os.environ.get('INSTANCE_PATH', os.path.join(os.getcwd(), 'instance'))
    os.makedirs(instance_path, exist_ok=True)
    
    app = Flask(__name__, instance_path=instance_path)
    
    # Configure the app
    if test_config is None:
        # Default configuration
        # Use DATABASE_PATH environment variable if set, otherwise use default
        db_path = os.environ.get('DATABASE_PATH', 'weight_tracker.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Authentication configuration
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
        
        # Session configuration for security
        app.config['SESSION_COOKIE_SECURE'] = os.environ.get('HTTPS', 'false').lower() == 'true'
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
        
        # Development mode flag for password reset tokens
        app.config['DEVELOPMENT'] = os.environ.get('FLASK_ENV') == 'development'
    else:
        # Test configuration
        app.config.update(test_config)
        # Ensure test config has required auth settings
        if 'SECRET_KEY' not in app.config:
            app.config['SECRET_KEY'] = 'test-secret-key'
        if 'WTF_CSRF_ENABLED' not in app.config:
            app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests
    
    # Set up logging
    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    init_login(app)
    
    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api)
    app.register_blueprint(auth_bp)
    
    # Create database tables and migrate if needed (skip in test mode)
    if not app.config.get('SKIP_MIGRATION', False):
        with app.app_context():
            app.logger.info("Checking database and performing migrations if needed")
            
            # First verify if this is a mounted DB from a previous version that needs migration
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                app.logger.info(f"Found existing database at {db_path}")
                
                # First run migration checks (handles older database versions)
                app.logger.info("Running migration checks for existing database")
                migration.check_and_migrate_database()
                
                # Then create any additional tables if needed
                app.logger.info("Creating any missing tables")
                services.create_tables()
            else:
                # If database doesn't exist, create it from scratch
                app.logger.info("No existing database found, creating tables from scratch")
                # For new databases, the migration system handles both table creation and setup
                migration.check_and_migrate_database()
        
        # Migrate old entries to the new schema (only needed for existing databases)
        # For new databases, this is handled by the migration system
        if db_path != ":memory:" and os.path.exists(db_path):
            services.migrate_old_entries_to_body_mass()
        
        # Verify schema is consistent
        schema_verification = migration.verify_model_schema()
        for table, is_valid in schema_verification.items():
            if not is_valid:
                app.logger.warning(f"Schema mismatch detected for table {table}")
    
    # Add service worker route - needed for PWA
    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)
        
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory('static', 'manifest.json')
    
    return app

def configure_logging(app):
    """Configure logging for the application"""
    # Set log level based on environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create a file handler if not in debug mode
    if not app.debug:
        log_dir = os.environ.get('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'weight_tracker.log'), 
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        app.logger.addHandler(file_handler)
    
    # Log application startup
    app.logger.info('Weight Tracker application starting up')

def run_app():
    """Main function to run the application"""
    app = create_app()
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.logger.info(f'Starting application on port {port} with debug={debug_mode}')
    app.run(debug=debug_mode,
            host='0.0.0.0', 
            port=port)

if __name__ == '__main__':
    run_app() 