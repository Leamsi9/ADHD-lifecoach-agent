#!/usr/bin/env python
"""
Test script for the DirectCoachAgent.
Run this script to verify that the DirectCoachAgent works correctly via the adapter.
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("🧪 Starting DirectCoachAgent test")

# Import the adapter to apply the patch
import app.agents.agent_adapter

# Import the patched LifeCoachAgent
from app.agents.life_coach_agent import LifeCoachAgent

# Test the agent
def test_agent():
    # Create the agent
    agent = LifeCoachAgent()
    logger.info(f"Created agent with conversation ID: {agent.conversation_id}")
    
    # Test start_new_conversation
    result = agent.start_new_conversation()
    logger.info(f"New conversation greeting: {result['response']}")
    
    # Test provide_coaching
    test_inputs = [
        "Hi, I'm feeling overwhelmed with my work and spiritual practice balance.",
        "I'd like to develop a better daily prayer routine.",
        "I sometimes struggle with motivation to maintain consistency.",
        "Can you help me create a plan for morning prayers?",
        "Thank you for your guidance today."
    ]
    
    for i, user_input in enumerate(test_inputs):
        logger.info(f"\n--- Test input {i+1}: {user_input}")
        result = agent.provide_coaching(user_input)
        logger.info(f"Agent response: {result['response']}")
        
        if 'insights' in result:
            logger.info(f"Insights: {result['insights']}")
    
    # Test memory features
    logger.info("\n--- Testing memory features")
    agent.add_explicit_memory("I want to remember to be more patient with my children.")
    
    memories = agent.get_memories("patient")
    logger.info(f"Retrieved memories about patience: {memories}")
    
    logger.info("✅ Test completed successfully")

if __name__ == "__main__":
    test_agent() 