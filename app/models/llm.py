"""
LLM model wrapper for the Bahai Life Coach agent.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_community.llms import HuggingFaceEndpoint
from app.config.settings import (
    OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, 
    USE_OLLAMA, OLLAMA_BASE_URL, OLLAMA_MODEL,
    USE_HUGGINGFACE, HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL, HUGGINGFACE_API_URL
)

def get_llm_model():
    """
    Get the LLM model instance with configuration from settings.
    
    Returns:
        Language model instance based on configuration
    """
    if USE_OLLAMA:
        print(f"Initializing LLM with Ollama model: {OLLAMA_MODEL}")
        print(f"  - Ollama base URL: {OLLAMA_BASE_URL}")
        # Initialize Ollama with minimal parameters to avoid compatibility issues
        return Ollama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=TEMPERATURE,
        )
    elif USE_HUGGINGFACE:
        print(f"Initializing LLM with Hugging Face model: {HUGGINGFACE_MODEL}")
        # Initialize HuggingFaceEndpoint with the Inference API
        return HuggingFaceEndpoint(
            endpoint_url=f"{HUGGINGFACE_API_URL}{HUGGINGFACE_MODEL}",
            huggingfacehub_api_token=HUGGINGFACE_API_KEY,
            task="text-generation",
            model_kwargs={
                "temperature": TEMPERATURE,
                "max_new_tokens": 512,
                "do_sample": True,
                "return_full_text": False
            }
        )
    else:
        print(f"Initializing LLM with OpenAI model: {MODEL_NAME}")
        # Initialize ChatOpenAI with minimal parameters
        return ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
        ) 