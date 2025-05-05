from flask import Flask, send_from_directory
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from .models import db
from .routes import main as main_blueprint, api
from . import services
from pathlib import Path
import threading

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
    else:
        # Test configuration
        app.config.update(test_config)
    
    # Set up logging
    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api)
    
    # Create database tables
    with app.app_context():
        services.create_tables()
        
        # Migrate old entries to the new schema
        services.migrate_old_entries_to_body_mass()
    
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