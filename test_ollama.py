#!/usr/bin/env python3
"""Test script for Ollama integration."""

import os
import sys
from langchain_community.llms import Ollama

def test_ollama_connection():
    """Test the connection to Ollama with the specified model."""
    
    # Get model name from command line or use default
    model_name = sys.argv[1] if len(sys.argv) > 1 else "llama3.2:latest"
    
    print(f"Testing connection to Ollama with model: {model_name}")
    
    try:
        # Initialize the Ollama model
        ollama_model = Ollama(
            base_url="http://localhost:11434",
            model=model_name,
            temperature=0.7,
        )
        
        # Generate a simple response
        prompt = "Hello, please tell me who you are in one sentence."
        print(f"Sending prompt: '{prompt}'")
        
        response = ollama_model.invoke(prompt)
        
        print("\nResponse from Ollama:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        print("\nConnection test successful!")
        return True
    
    except Exception as e:
        print(f"\nError connecting to Ollama: {str(e)}")
        print("\nPlease check that:")
        print("1. Ollama is running (check with 'ps aux | grep ollama')")
        print(f"2. The model '{model_name}' is available (check with 'ollama list')")
        print("3. Ollama is accessible at http://localhost:11434 (default port)")
        return False

if __name__ == "__main__":
    test_ollama_connection() 