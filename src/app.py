from flask import Flask
import os
from models import db
from routes import main as main_blueprint, api
import services

def create_app(test_config=None):
    """Application factory function"""
    app = Flask(__name__)
    
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
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api)
    
    # Create database tables
    with app.app_context():
        services.create_tables()
    
    return app

def run_app():
    """Main function to run the application"""
    app = create_app()
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
            host='0.0.0.0', 
            port=port)

if __name__ == '__main__':
    run_app() 