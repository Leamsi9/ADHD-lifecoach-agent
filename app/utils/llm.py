"""
LLM utility functions for the Bahai Life Coach agent.
"""

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
    
    # Import required dependencies based on provider
    if provider == "openai":
        from openai import OpenAI
        from app.config.settings import OPENAI_API_KEY
        
        # Initialize client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Set default model if not provided
        model = model or "gpt-4.5-preview"
        
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
        from app.config.settings import OLLAMA_URL
        
        # Set default model if not provided
        model = model or "llama2"
        
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
        from app.config.settings import HUGGINGFACE_API_KEY
        
        # Set default model if not provided
        model = model or "mistralai/Mistral-7B-Instruct-v0.1"
        
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