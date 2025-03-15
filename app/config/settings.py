"""
Configuration settings for the Bahai Life Coach agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Key and Model Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # Options: openai, ollama, huggingface
USE_OPENAI = LLM_PROVIDER == "openai"
USE_OLLAMA = LLM_PROVIDER == "ollama"
USE_HUGGINGFACE = LLM_PROVIDER == "huggingface"

# Model Settings
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo" if USE_OPENAI else "llama2")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))

# Additional LangChain-specific settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")
HUGGINGFACE_API_URL = os.getenv("HUGGINGFACE_API_URL", "https://api-inference.huggingface.co/models/")

# Flask App Configuration
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "bahai-life-coach-secret-key")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5555"))

# Database Configuration (optional)
USE_DATABASE = os.getenv("USE_DATABASE", "False").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///conversations.db")

# Google Integration Configuration
ENABLE_GOOGLE_INTEGRATION = os.getenv("ENABLE_GOOGLE_INTEGRATION", "False").lower() == "true"
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_API_SCOPES = os.getenv("GOOGLE_API_SCOPES", "https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/tasks").split(",")
GOOGLE_TIMEZONE = os.getenv("GOOGLE_TIMEZONE", "America/Los_Angeles")

# Speech Configuration
ENABLE_SPEECH = os.getenv("ENABLE_SPEECH", "True").lower() == "true"
SPEECH_VOICE = os.getenv("SPEECH_VOICE", "")  # Default voice (empty = browser default)
SPEECH_RATE = float(os.getenv("SPEECH_RATE", "1.0"))  # 1.0 = normal speed
SPEECH_PITCH = float(os.getenv("SPEECH_PITCH", "1.0"))  # 1.0 = normal pitch
SPEECH_PAUSE_THRESHOLD = float(os.getenv("SPEECH_PAUSE_THRESHOLD", "5.0"))  # Seconds of silence before auto-sending

def validate_config():
    """
    Validate required configuration settings.
    
    Raises:
        ValueError: If a required configuration setting is missing.
    """
    if USE_OPENAI and not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is required when using OpenAI as the LLM provider")
    
    if USE_HUGGINGFACE and not HUGGINGFACE_API_KEY:
        raise ValueError("HuggingFace API key is required when using HuggingFace as the LLM provider")
    
    # If Google integration is enabled, check if credentials file exists
    if ENABLE_GOOGLE_INTEGRATION:
        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            print(f"WARNING: Google integration is enabled but credentials file not found at {GOOGLE_CREDENTIALS_PATH}")
    
    # Log which LLM provider is being used
    print(f"Using LLM provider: {LLM_PROVIDER.upper()}")
    print(f"Model: {MODEL_NAME}")
    
    if USE_OPENAI:
        print(f"  - Using OpenAI API")
    elif USE_OLLAMA:
        print(f"  - Using Ollama: {OLLAMA_MODEL}")
        print(f"  - Ollama base URL: {OLLAMA_BASE_URL}")
    elif USE_HUGGINGFACE:
        print(f"  - Using HuggingFace: {HUGGINGFACE_MODEL}")
    
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

# Initialize configuration validation
validate_config() 