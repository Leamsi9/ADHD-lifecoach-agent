"""
Gemini Adapter for the Bahai Life Coach agent.

This module provides an adapter to use Google's Gemini API as an LLM model.
It integrates with the LangChain library and provides a uniform interface
for the Bahai Life Coach agent to interact with Gemini models.
"""

import os
import logging
import importlib.util
from typing import List, Dict, Any, Optional, Union

# Check if google-generativeai is installed
if importlib.util.find_spec("google.generativeai") is None:
    HAS_GEMINI = False
    logging.warning("⚠️ Google Generative AI package not installed.")
    logging.info("To use Google Gemini, install the library with:")
    logging.info("    pip install google-generativeai")
else:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    HAS_GEMINI = True

from app.config.settings import (
    GEMINI_API_KEY, 
    GEMINI_MODEL,
    GEMINI_LOCATION,
    GEMINI_TIMEOUT,
    TEMPERATURE,
    MAX_TOKENS
)

logger = logging.getLogger(__name__)

class GeminiAdapter:
    """
    An adapter for integrating Google's Gemini AI models with the Bahai Life Coach.
    
    This adapter wraps the Gemini API in a way that allows it to be used
    interchangeably with other LLM models in the Bahai Life Coach system.
    """
    
    def __init__(self):
        """Initialize the Gemini adapter."""
        if not HAS_GEMINI:
            raise ImportError(
                "Google Generative AI package is required to use Gemini. "
                "Install it with: pip install google-generativeai"
            )
        
        # Initialize the Gemini API
        self.api_key = GEMINI_API_KEY
        self.model_name = GEMINI_MODEL
        self.location = GEMINI_LOCATION
        self.timeout = GEMINI_TIMEOUT
        
        # Configure the Gemini client
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=GenerationConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_TOKENS
            )
        )
        
        logger.info(f"Initialized Gemini adapter with model {self.model_name}")
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response from Google Gemini.
        
        Args:
            messages: List of message dictionaries with role and content.
            
        Returns:
            The generated response text.
        """
        try:
            # Convert the message format to Gemini's expected format
            formatted_messages = self._format_messages(messages)
            
            # Generate the response
            chat_session = self.model.start_chat()
            for message in formatted_messages:
                if message.role == "user":
                    chat_session.send_message(message.parts[0].text)
                # Note: Gemini doesn't need the assistant messages as it maintains context
            
            # Get the final response (from the most recent message)
            response = chat_session.last
            
            # Extract and return the text content
            return response.text
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Any]:
        """
        Convert messages to the format expected by Gemini.
        
        Args:
            messages: List of message dictionaries with role and content.
            
        Returns:
            List of Gemini content parts.
        """
        # For Gemini's chat model, we need to convert the messages to Content objects
        from google.generativeai.types import Content
        
        # Map OpenAI role names to Gemini roles
        role_map = {
            "system": "user",  # Gemini doesn't have system messages, use as user
            "user": "user",
            "assistant": "model"
        }
        
        # Format the messages
        formatted_messages = []
        for message in messages:
            role = role_map.get(message.get("role", "user"), "user")
            content = message.get("content", "")
            
            # Create a Content object for this message
            formatted_messages.append(Content(
                role=role,
                parts=[{"text": content}]
            ))
        
        return formatted_messages 