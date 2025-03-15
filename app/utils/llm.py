"""
LLM utility functions for the Bahai Life Coach agent.
"""

import logging
from app.config.settings import (
    OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, 
    OLLAMA_URL, OLLAMA_MODEL, 
    HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL
)

# Configure logging
logger = logging.getLogger(__name__)

def get_completion(messages, provider="openai", model=None, temperature=0.7):
    """
    Get a completion from the LLM based on the messages provided.
    
    Args:
        messages: List of message dictionaries with role and content.
        provider: The LLM provider to use (openai, ollama, huggingface).
        model: The model to use.
        temperature: The temperature to use for the completion.
        
    Returns:
        The generated completion as a string.
    """
    # Process provider name
    provider = provider.lower()
    
    # Log the actual MODEL_NAME from settings
    logger.info(f"MODEL_NAME from settings: {MODEL_NAME}")
    
    # Import required dependencies based on provider
    if provider == "openai":
        from openai import OpenAI
        
        # Initialize client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Set default model if not provided
        model = model or MODEL_NAME
        logger.info(f"Using OpenAI model: {model}")
        
        # Create completion
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        # Return the text
        return response.choices[0].message.content
    
    elif provider == "ollama":
        import requests
        import json
        
        # Set default model if not provided
        model = model or (MODEL_NAME if "llama" in MODEL_NAME else OLLAMA_MODEL)
        logger.info(f"Using Ollama model: {model}")
        
        # Convert to ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Create completion
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "model": model,
                "messages": ollama_messages,
                "temperature": temperature
            })
        )
        
        # Parse response
        if response.status_code == 200:
            result = response.json()
            return result["message"]["content"]
        else:
            raise Exception(f"Error calling Ollama API: {response.text}")
    
    elif provider == "huggingface":
        import requests
        
        # Set default model if not provided
        model = model or (MODEL_NAME if "/" in MODEL_NAME else HUGGINGFACE_MODEL)
        logger.info(f"Using HuggingFace model: {model}")
        
        # Combine messages into a single prompt for HF
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"{role.upper()}: {content}\n\n"
        prompt += "ASSISTANT: "
        
        # Create completion
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json={"inputs": prompt, "parameters": {"temperature": temperature}}
        )
        
        # Parse response
        if response.status_code == 200:
            return response.json()[0]["generated_text"].split("ASSISTANT: ", 1)[1]
        else:
            raise Exception(f"Error calling HuggingFace API: {response.text}")
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}") 