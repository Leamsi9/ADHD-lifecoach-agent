"""
LLM model Configuration Module.

This module defines the available LLM models and their configurations,
separating model definitions from secrets (API keys).
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default model to use if not specified
DEFAULT_MODEL = 'gemini'

# Available LLM model definitions
LLM_MODELS = {
    'openai': {
        'name': 'OpenAI',
        'description': 'OpenAI ChatGPT and GPT-4 models',
        'models': ['gpt-3.5-turbo', 'gpt-4o', 'gpt-4-turbo'],
        'default_model': 'gpt-4o',
        'api_key_env': 'OPENAI_API_KEY',
        'model_env': 'OPENAI_MODEL',
        'module': 'langchain_openai',
        'class': 'ChatOpenAI',
        'api_param': 'openai_api_key'
    },
    'gemini': {
        'name': 'Google Gemini',
        'description': 'Google Gemini AI models',
        'models': ['gemini-pro', 'gemini-1.5-pro', 'gemini-2.0-flash'],
        'default_model': 'gemini-2.0-flash',
        'api_key_env': 'GEMINI_API_KEY',
        'model_env': 'GEMINI_MODEL',
        'module': 'langchain_google_genai',
        'class': 'ChatGoogleGenerativeAI',
        'api_param': 'google_api_key',
        'extra_settings': {
            'GEMINI_LOCATION': 'us-central1',
            'GEMINI_TIMEOUT': 300
        }
    },
    'deepseek': {
        'name': 'Deepseek',
        'description': 'Deepseek AI models',
        'models': ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
        'default_model': 'deepseek-chat',
        'api_key_env': 'DEEPSEEK_API_KEY',
        'model_env': 'DEEPSEEK_MODEL',
        'module': 'langchain_deepseek',
        'class': 'ChatDeepseek',
        'api_param': 'api_key',
        'extra_settings': {
            'DEEPSEEK_TIMEOUT': 300
        }
    }
    # Add new models here following the same structure
}

def get_available_models() -> List[str]:
    """
    Get a list of available model names.
    
    Returns:
        List of model names
    """
    return list(LLM_MODELS.keys())

def get_model_info(model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the configuration for a specific model.
    
    Args:
        model_name: The name of the model, or None to use default
        
    Returns:
        model configuration dictionary
    """
    if model_name is None:
        model_name = os.getenv('LLM_MODEL', DEFAULT_MODEL).lower()
    
    if model_name not in LLM_MODELS:
        logger.warning(f"model '{model_name}' not found in configuration. Using default model '{DEFAULT_MODEL}'")
        model_name = DEFAULT_MODEL
    
    return LLM_MODELS[model_name]

def get_model_model(model_name: Optional[str] = None) -> str:
    """
    Get the configured model for a model.
    
    Args:
        model_name: The name of the model, or None to use current
        
    Returns:
        The model name
    """
    model = get_model_info(model_name)
    model_env = model['model_env']
    default_model = model['default_model']
    
    return os.getenv(model_env, default_model)

def get_model_api_key(model_name: Optional[str] = None) -> Optional[str]:
    """
    Get the API key for a model.
    
    Args:
        model_name: The name of the model, or None to use current
        
    Returns:
        The API key if found, None otherwise
    """
    model = get_model_info(model_name)
    api_key_env = model['api_key_env']
    
    return os.getenv(api_key_env) 