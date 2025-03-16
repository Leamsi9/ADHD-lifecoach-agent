#!/usr/bin/env python3
"""
Test script for the Google Gemini integration.
"""

import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Run the test for Google Gemini integration."""
    try:
        # Set the LLM_PROVIDER environment variable to gemini for this test
        os.environ["LLM_PROVIDER"] = "gemini"
        
        # Import the agent adapter and create a new conversation
        from app.agents.agent_adapter import get_agent
        
        # Create a new agent
        agent = get_agent()
        logger.info(f"Created agent with conversation ID: {agent.conversation_id}")
        
        # Test with a simple prompt
        response = agent.provide_coaching("Hello, I'm interested in learning more about the Bahá'í Faith.")
        
        # Print the response
        print("\nResponse from Gemini:")
        print("-" * 50)
        print(response.get("response", "No response generated"))
        print("-" * 50)
        
        print("\nConversation ID:", agent.conversation_id)
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("Make sure you have installed the required packages:")
        logger.info("    pip install google-generativeai")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main() 