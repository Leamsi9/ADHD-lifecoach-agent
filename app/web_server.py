"""
Web server script for the Bahai Life Coach agent.
"""

import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.settings import validate_config, FLASK_PORT, ENABLE_GOOGLE_INTEGRATION
from app.web import create_app

def run_web_server():
    """
    Run the web server.
    
    Returns:
        int: Exit code
    """
    try:
        # Validate configuration
        validate_config()
        
        # Create the Flask app
        app = create_app()
        
        # Print server information
        print(f"Starting Bahai Life Coach web server on port {FLASK_PORT}")
        print(f"Google integration: {'Enabled' if ENABLE_GOOGLE_INTEGRATION else 'Disabled'}")
        print(f"Open your browser and navigate to: http://localhost:{FLASK_PORT}")
        
        # Run the app
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=True)
        
        return 0
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
        print("Please check your .env file and ensure all required variables are set.")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(run_web_server()) 