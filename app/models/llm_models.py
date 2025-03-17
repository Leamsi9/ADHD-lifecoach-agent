"""
LLM Provider Configuration Module.

This module defines the available LLM providers and their configurations,
separating provider definitions from secrets (API keys).
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default provider to use if not specified
DEFAULT_MODEL = 'gemini'

# Available LLM provider definitions
LLM_MODELS = {
    'openai': {
        'name': 'OpenAI',
        'description': 'OpenAI ChatGPT and GPT-4 models',
        'models': ['gpt-3.5-turbo', 'gpt-4o', 'gpt-4-turbo', 'gpt-4.5-preview'],
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
    # Add new providers here following the same structure
}

def get_available_providers() -> List[str]:
    """
    Get a list of available provider names.
    
    Returns:
        List of provider names
    """
    return list(LLM_MODELS.keys())

def get_available_models() -> List[str]:
    """
    Get a list of all available models across all providers.
    
    Returns:
        List of model names
    """
    all_models = []
    for provider_info in LLM_MODELS.values():
        all_models.extend(provider_info['models'])
    return all_models

def get_model_info(model_name: str) -> Dict[str, Any]:
    """
    Get provider information for a specific model.
    
    Args:
        model_name: The name of the model
        
    Returns:
        Provider configuration dictionary including provider name
    """
    for provider_name, provider_info in LLM_MODELS.items():
        if model_name in provider_info['models']:
            result = provider_info.copy()
            result['provider'] = provider_name
            return result
    
    # If model not found, raise error
    available_models = get_available_models()
    raise ValueError(f"Model '{model_name}' not found. Available models: {', '.join(available_models)}")

def get_model_api_key(model_name: str) -> Optional[str]:
    """
    Get the API key for a model's provider.
    
    Args:
        model_name: The name of the model
        
    Returns:
        The API key if found, None otherwise
    """
    model_info = get_model_info(model_name)
    api_key_env = model_info['api_key_env']
    return os.getenv(api_key_env)

def get_provider_info(provider_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the configuration for a specific provider.
    
    Args:
        provider_name: The name of the provider, or None to use default
        
    Returns:
        Provider configuration dictionary
    """
    if provider_name is None:
        provider_name = os.getenv('LLM_MODEL', DEFAULT_MODEL).lower()
    
    if provider_name not in LLM_MODELS:
        logger.warning(f"Provider '{provider_name}' not found in configuration. Using default provider '{DEFAULT_MODEL}'")
        provider_name = DEFAULT_MODEL
    
    return LLM_MODELS[provider_name]

def get_provider_model(provider_name: Optional[str] = None) -> str:
    """
    Get the configured model for a provider.
    
    Args:
        provider_name: The name of the provider, or None to use current
        
    Returns:
        The model name
    """
    provider = get_provider_info(provider_name)
    model_env = provider['model_env']
    default_model = provider['default_model']
    
    return os.getenv(model_env, default_model)

def get_provider_api_key(provider_name: Optional[str] = None) -> Optional[str]:
    """
    Get the API key for a provider.
    
    Args:
        provider_name: The name of the provider, or None to use current
        
    Returns:
        The API key if found, None otherwise
    """
    provider = get_provider_info(provider_name)
    api_key_env = provider['api_key_env']
    
    return os.getenv(api_key_env) 