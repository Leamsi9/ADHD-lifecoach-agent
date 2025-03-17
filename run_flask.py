#!/usr/bin/env python3
"""
Run script for the Bahai Life Coach Flask application.
This script initializes and runs the Flask application with the correct settings.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

def main():
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Import models module to get available models
    try:
        from app.models.llm_models import get_available_models
        available_models = get_available_models()
        model_str = ", ".join(available_models)
    except ImportError:
        available_models = []
        model_str = "model names not available - check app/models/llm_models.py"
        print("Warning: Could not import get_available_models from app.models.llm_models")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Bahai Life Coach Flask server')
    parser.add_argument('--port', type=int, default=5555, help='Port to run the server on')
    parser.add_argument('--refresh-llm', action='store_true', help='Force refresh of LLM instance')
    parser.add_argument('--model', type=str, help=f'Specify LLM model to use ({model_str})')
    parser.add_argument('--clean-env', action='store_true', help='Clean environment variables before loading .env')
    args = parser.parse_args()

    # Clean environment variables if requested
    if args.clean_env:
        # Clear any existing LLM-related environment variables
        env_vars_to_clean = [
            'LLM_MODEL', 'LLM_PROVIDER', 
            'OPENAI_API_KEY', 'OPENAI_MODEL',
            'GEMINI_API_KEY', 'GEMINI_MODEL', 
            'HUGGINGFACE_API_KEY', 'HUGGINGFACE_MODEL',
            'OLLAMA_BASE_URL', 'OLLAMA_MODEL'
        ]
        for var in env_vars_to_clean:
            if var in os.environ:
                print(f"Cleaning environment variable: {var}")
                del os.environ[var]

    # Load environment variables from .env file with explicit path
    env_path = find_dotenv(usecwd=True)
    if env_path:
        print(f"Loading environment from: {env_path}")
        # Force reload the environment variables
        load_dotenv(env_path, override=True)
    else:
        print("ERROR: No .env file found! Application may not function correctly.")
        sys.exit(1)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Set model if specified via command line
    if args.model:
        os.environ['LLM_MODEL'] = args.model
        logger.info(f"Setting LLM model to: {args.model}")
        
    # Debug: Print current LLM model from environment
    logger.info(f"Current LLM_MODEL: {os.getenv('LLM_MODEL')}")

    # Handle LLM refresh if requested
    if args.refresh_llm:
        try:
            from app.models.llm import get_llm_model
            get_llm_model(force_refresh=True)
            logger.info("✅ LLM instance refreshed successfully")
        except Exception as e:
            logger.error(f"❌ Error refreshing LLM instance: {str(e)}")
            logger.info("Continuing with server startup...")

    logger.info("Starting Bahai Life Coach Flask application")

    # Import Flask and create app directly
    from flask import Flask
    from app.config.settings import FLASK_SECRET_KEY, FLASK_PORT

    # Use command line port if provided, otherwise use FLASK_PORT from settings
    port = args.port if args.port else FLASK_PORT
    logger.info(f"Using port: {port}")

    # Create app instance - use 'flask_app' instead of 'app' to avoid name conflicts
    flask_app = Flask(__name__, 
                      static_folder='app/web/static',
                      template_folder='app/web/templates')
    flask_app.secret_key = FLASK_SECRET_KEY

    # Ensure memory directory exists
    Path("memory_storage").mkdir(parents=True, exist_ok=True)
    logger.info("📁 Ensured memory directory exists")

    # Import the agent adapter to initialize it
    import app.agents.agent_adapter
    logger.info("🧠 Agent adapter initialized")

    # Import and register the blueprint
    from app.web.routes import web_bp
    flask_app.register_blueprint(web_bp)
    logger.info("🛣️ Routes registered")

    # Set environment variable for Flask development
    os.environ['FLASK_ENV'] = 'development'

    # Run the app
    logger.info(f"🚀 Starting Flask server on port {port}")
    flask_app.run(debug=True, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main() 