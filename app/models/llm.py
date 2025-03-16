"""
LLM model wrapper for the Bahai Life Coach agent.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_community.llms import HuggingFaceEndpoint
from langchain.chat_models.base import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import (
    OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE, MAX_TOKENS,
    USE_OLLAMA, OLLAMA_BASE_URL, OLLAMA_MODEL,
    USE_HUGGINGFACE, HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL, HUGGINGFACE_API_URL,
    USE_GEMINI, GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TIMEOUT
)

def get_llm_model() -> BaseChatModel:
    """
    Get the LLM model instance with configuration from settings.
    
    Returns:
        Language model instance based on configuration
    """
    if USE_GEMINI:
        print(f"Initializing Google Gemini model: {GEMINI_MODEL}")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS,
            timeout=GEMINI_TIMEOUT if GEMINI_TIMEOUT else None,
            max_retries=2
        )
    elif USE_OLLAMA:
        print(f"Initializing LLM with Ollama model: {OLLAMA_MODEL}")
        return Ollama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=TEMPERATURE,
        )
    elif USE_HUGGINGFACE:
        print(f"Initializing LLM with Hugging Face model: {HUGGINGFACE_MODEL}")
        return HuggingFaceEndpoint(
            endpoint_url=f"{HUGGINGFACE_API_URL}{HUGGINGFACE_MODEL}",
            huggingfacehub_api_token=HUGGINGFACE_API_KEY,
            task="text-generation",
            temperature=TEMPERATURE,
            max_new_tokens=512,
            do_sample=True,
            return_full_text=False
        )
    else:
        print(f"Initializing LLM with OpenAI model: {OPENAI_MODEL}")
        return ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=TEMPERATURE,
        ) 