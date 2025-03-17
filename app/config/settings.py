"""
Configuration settings for the Bahai Life Coach agent.

This module contains all configuration settings with reasonable defaults.
Only sensitive information (API keys, secrets) should be loaded from environment variables.
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file with more explicit handling
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    print(f"Loading environment from: {dotenv_path}")
    load_dotenv(dotenv_path, override=True)
else:
    print("WARNING: No .env file found!")

# ------------------------------
# LLM Model Configuration
# ------------------------------
# The specific model to use (environment variable overrides default, and enable run-flask.py flag to override default too)
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

# Model behavior settings (hard-coded defaults)
TEMPERATURE = 0.7
MAX_TOKENS = 2000

# ------------------------------
# API Keys (SENSITIVE)
# ------------------------------
# These should always come from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# ------------------------------
# Provider-specific Settings
# ------------------------------
# Gemini settings
GEMINI_LOCATION = "us-central1"
GEMINI_TIMEOUT = 300  # Timeout in seconds

# OLLAMA settings
OLLAMA_BASE_URL = "http://localhost:11434"

# ------------------------------
# Web Server Configuration
# ------------------------------
# Secret key should come from environment (sensitive)
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "bahai-life-coach-secret-key")
# Other web server settings can have reasonable defaults
FLASK_PORT = 5555
FLASK_HOST = "0.0.0.0"  # Allow connections from any IP
FLASK_DEBUG = False

# ------------------------------
# Database Configuration
# ------------------------------
USE_DATABASE = False
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///conversations.db")

# ------------------------------
# Google Integration Configuration
# ------------------------------
ENABLE_GOOGLE_INTEGRATION = False
GOOGLE_CREDENTIALS_PATH = "credentials.json"
GOOGLE_API_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks"
]
GOOGLE_TIMEZONE = "America/Los_Angeles"

# ------------------------------
# Speech Configuration
# ------------------------------
ENABLE_SPEECH = True
SPEECH_VOICE = 1  # Default voice (empty = browser default)
SPEECH_RATE = 1.0  # 1.0 = normal speed
SPEECH_PITCH = 1.0  # 1.0 = normal pitch
SPEECH_PAUSE_THRESHOLD = 2.0  # Seconds of silence before auto-sending

# ------------------------------
# Memory Configuration
# ------------------------------
ENABLE_MEMORY_TRACKING = True
MEMORY_STORAGE_PATH = "memory_storage"

def validate_configuration():
    """Validate configuration and log relevant information."""
    try:
        # Read and validate model settings
        model_config = get_model_info(LLM_MODEL)
        model_provider = model_config['provider']
        api_key = get_model_api_key(LLM_MODEL)
        
        if not api_key:
            raise ValueError(f"API key for model {LLM_MODEL} is required (set {model_config['api_key_env']} environment variable)")
        
        # If Google integration is enabled, check if credentials file exists
        if ENABLE_GOOGLE_INTEGRATION:
            if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
                print(f"WARNING: Google integration is enabled but credentials file not found at {GOOGLE_CREDENTIALS_PATH}")
        
        # Log which LLM model is being used
        print(f"Using LLM model: {model_config['name']} ({LLM_MODEL})")
        print(f"Model provider: {model_provider}")
        
        # Log provider-specific information
        if model_provider == "gemini":
            print(f"  - Gemini location: {GEMINI_LOCATION}")
        elif model_provider == "deepseek":
            print(f"  - Using Deepseek API")
        elif model_provider == "openai":
            print(f"  - Using OpenAI API")
        
        # Log Google integration status
        if ENABLE_GOOGLE_INTEGRATION:
            print(f"Google integration: ENABLED")
            if os.path.exists(GOOGLE_CREDENTIALS_PATH):
                print(f"  Credentials: {GOOGLE_CREDENTIALS_PATH}")
            else:
                print(f"  Credentials: NOT FOUND (expected at {GOOGLE_CREDENTIALS_PATH})")
        else:
            print(f"Google integration: DISABLED")
        
        # Log speech settings
        if ENABLE_SPEECH:
            print(f"Speech functionality: ENABLED")
            print(f"  Pause threshold: {SPEECH_PAUSE_THRESHOLD} seconds")
        else:
            print(f"Speech functionality: DISABLED")
        
        # Web server settings
        print(f"Web server: {FLASK_HOST}:{FLASK_PORT}")
    except ImportError:
        print("WARNING: Configuration validation deferred (llm_models module not yet available)")
    except Exception as e:
        print(f"WARNING: Configuration validation failed: {str(e)}")

# Initialize configuration validation
validate_configuration()