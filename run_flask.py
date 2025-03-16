#!/usr/bin/env python3
"""
Flask runner script for the Bahai Life Coach web application.
This script makes it easier to run the Flask web server without needing to set FLASK_APP.
"""

import os
import sys

# Ensure we're running from the project root
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the app module first to ensure environment variables are loaded
import app

# Create the Flask app
from flask import Flask
from app.web.routes import main as main_blueprint
from app.config.settings import FLASK_SECRET_KEY, FLASK_PORT

app = Flask(__name__, 
            static_folder='app/web/static',
            template_folder='app/web/templates')

# Register blueprints
app.register_blueprint(main_blueprint)

# Enable session
app.secret_key = FLASK_SECRET_KEY

if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=FLASK_PORT) 