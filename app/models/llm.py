"""
LLM Module for the Bahai Life Coach Agent.

This module provides a centralized interface for accessing various LLM providers
through a singleton pattern for efficiency.
"""

import os
import logging
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global LLM instance (singleton pattern)
_llm_instance = None

# Import LLM providers
try:
    from langchain_openai import ChatOpenAI as OpenAI
except ImportError:
    logger.warning("OpenAI not available. Install with: pip install langchain-openai")
    OpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI as Gemini
except ImportError:
    logger.warning("Gemini not available. Install with: pip install langchain-google-genai")
    Gemini = None

try:
    from langchain_deepseek import ChatDeepseek as Deepseek
except ImportError:
    logger.warning("Deepseek not available. Install with: pip install langchain-deepseek")
    Deepseek = None

# Import model information
from app.models.llm_models import get_model_info, get_model_api_key
from app.config.settings import LLM_MODEL

# Map of provider names to classes
MODEL_CLASSES = {
    'openai': OpenAI,
    'gemini': Gemini,
    'deepseek': Deepseek
    # Add other providers here
}

def get_llm_model(force_refresh: bool = False) -> Any:
    """
    Get the LLM instance using singleton pattern with refresh capability.
    
    Args:
        force_refresh: If True, creates a new instance even if one exists
        
    Returns:
        The LLM instance
    """
    global _llm_instance
    
    if force_refresh or _llm_instance is None:
        model_name = os.getenv('LLM_MODEL', LLM_MODEL)
        logger.info(f"Using LLM model: {model_name}")
        
        try:
            # Get model configuration
            model_info = get_model_info(model_name)
            provider_name = model_info['provider']
            api_key = get_model_api_key(model_name)
            
            # Get the provider class
            ProviderClass = MODEL_CLASSES.get(provider_name)
            
            if ProviderClass is None:
                logger.error(f"Provider {provider_name} implementation not available. Please install the required package.")
                # Attempt to find an available provider
                for p_name, p_class in MODEL_CLASSES.items():
                    if p_class is not None:
                        logger.warning(f"Falling back to available provider: {p_name}")
                        # Get default model for the available provider
                        provider_name = p_name
                        ProviderClass = p_class
                        alt_model_info = get_model_info(model_info['models'][0])
                        model_name = alt_model_info['default_model']
                        api_key = get_model_api_key(model_name)
                        break
            
            # If still None, we can't proceed
            if ProviderClass is None:
                logger.error("No LLM providers available. Please install at least one provider package.")
                raise ImportError("No LLM providers available")
            
            # Check for API key
            if not api_key:
                logger.error(f"API key for model {model_name} not found (expected in {model_info['api_key_env']} environment variable)")
                raise ValueError(f"API key for model {model_name} not found. Set {model_info['api_key_env']} environment variable.")
            
            # Initialize the LLM
            api_param_name = model_info.get('api_param', 'api_key')
            
            # Create kwargs with the appropriate api_key parameter name
            kwargs = {
                'model': model_name,
                api_param_name: api_key
            }
            
            # Initialize the provider with the correct parameters
            _llm_instance = ProviderClass(**kwargs)
            logger.info(f"Successfully initialized LLM with model: {model_name} (provider: {provider_name})")
            
        except Exception as e:
            logger.error(f"Error initializing LLM with model {model_name}: {str(e)}")
            raise
    
    return _llm_instance

def get_llm(provider: str = 'gemini') -> Any:
    """
    Legacy function for backward compatibility only.
    
    This function maintains backward compatibility with code that still uses
    the provider-centric approach. New code should use get_llm_model() directly
    and specify the model via LLM_MODEL in settings or environment variables.
    
    Args:
        provider: The LLM provider to use (e.g., 'gemini', 'openai')
        
    Returns:
        The LLM instance
    """
    # Get default model for this provider from llm_models.py
    from app.models.llm_models import get_provider_info
    provider_info = get_provider_info(provider)
    
    # Set the environment variable to the default model for this provider
    os.environ['LLM_MODEL'] = provider_info['default_model']
    return get_llm_model(force_refresh=True)

# Clear the LLM cache (useful for testing or when settings change)
def reset_llm():
    """
    Reset the LLM singleton by clearing the cache.
    This forces re-initialization on the next call to get_llm_model().
    """
    global _llm_instance
    _llm_instance = None
    logger.info("LLM singleton has been reset")

class MockLLM:
    """A mock LLM that returns predefined responses for testing"""
    
    def __init__(self):
        self.temperature = 0.0
        logger.warning("Using MockLLM - this should only be used for testing")
    
    def generate(self, messages):
        """Mock generate method"""
        return {"text": "This is a mock response from the LLM. Please configure a valid LLM provider."}
        
    def invoke(self, prompt, *args, **kwargs):
        """Mock invoke method compatible with langchain"""
        from langchain_core.messages import AIMessage
        return AIMessage(content="This is a mock response. Please configure a valid LLM provider.")
        
    def generate_response(self, messages):
        """Generate a response based on messages"""
        return "This is a mock response. Please configure a valid LLM provider." 