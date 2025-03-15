"""
Simple test script for testing Hugging Face integration.
"""

import os
from dotenv import load_dotenv
from langchain_community.llms import HuggingFaceEndpoint
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Get Hugging Face API key
huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
huggingface_model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")

def test_huggingface_connection():
    """Test the connection to Hugging Face inference API."""
    
    if not huggingface_api_key:
        print("ERROR: HUGGINGFACE_API_KEY is not set in the .env file.")
        print("Please set this variable and try again.")
        return
    
    print(f"Testing connection to Hugging Face with model: {huggingface_model}")
    
    # Create the model
    llm = HuggingFaceEndpoint(
        endpoint_url=f"https://api-inference.huggingface.co/models/{huggingface_model}",
        huggingfacehub_api_token=huggingface_api_key,
        task="text-generation",
        model_kwargs={
            "temperature": 0.7,
            "max_new_tokens": 512,
            "do_sample": True,
            "return_full_text": False
        }
    )
    
    # Define a simple prompt
    template = """You are a wise Bahai Life Coach. Please respond to the following question:

User question: {question}

Your advice:"""
    
    prompt = PromptTemplate(template=template, input_variables=["question"])
    
    # Create a chain
    chain = prompt | llm
    
    try:
        # Use the chain
        question = "How can I find more balance in my life?"
        print(f"\nSending question: '{question}'")
        print("-" * 50)
        
        response = chain.invoke({"question": question})
        
        print("\nResponse from Hugging Face:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        print("\nTest successful!")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_huggingface_connection() 