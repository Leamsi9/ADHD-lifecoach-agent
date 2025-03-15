"""
Web module for the Bahai Life Coach agent.
"""

from flask import Flask

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configure the app
    app.config['SECRET_KEY'] = 'bahai-life-coach-secret-key'
    
    # Register blueprints
    from app.web.routes import main
    app.register_blueprint(main)
    
    return app 