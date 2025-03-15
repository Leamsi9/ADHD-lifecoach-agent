"""
Simple test script to directly test the Ollama API without LangChain.
"""

import requests
import json

def test_ollama_api():
    """Test the Ollama API directly."""
    
    # Ollama API endpoint
    url = "http://localhost:11434/api/generate"
    
    # Request payload
    payload = {
        "model": "llama3.2",
        "prompt": "Hello, please introduce yourself in one sentence.",
        "stream": False
    }
    
    print("Testing direct connection to Ollama API...")
    print(f"Sending request to {url}")
    print(f"Using model: {payload['model']}")
    print(f"Prompt: {payload['prompt']}")
    print("-" * 50)
    
    try:
        # Send the request with a timeout
        response = requests.post(url, json=payload, timeout=30)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("Response from Ollama:")
            print("=" * 50)
            print(result.get("response", "No response found"))
            print("=" * 50)
            print("\nTest successful!")
        else:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)
    
    except requests.exceptions.Timeout:
        print("Error: Request timed out after 30 seconds")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_ollama_api() 