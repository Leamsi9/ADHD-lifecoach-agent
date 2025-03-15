"""
Simple test script for the Bahai Life Coach agent.
"""

import os
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Define a simple prompt
template = """You are a wise Bahai Life Coach. Please respond to the following question:

User question: {question}

Your advice:"""

prompt = PromptTemplate(template=template, input_variables=["question"])

# Initialize Ollama
llm = Ollama(
    base_url="http://localhost:11434",
    model="llama3.2",
    temperature=0.7,
)

# Create a chain using the newer LCEL style
chain = prompt | llm

# Test the chain
def test_chain():
    question = "How can I find more balance in my life?"
    try:
        # Use the newer invoke method
        response = chain.invoke({"question": question})
        print("\nQuestion:", question)
        print("\nResponse from Ollama:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        print("\nTest successful!")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_chain() 