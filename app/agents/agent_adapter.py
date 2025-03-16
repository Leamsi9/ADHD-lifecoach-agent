"""
Agent Adapter Module for the Bahai Life Coach.

This module provides a simplified interface for accessing the LifeCoachAgent.
"""

from typing import Dict, List, Any, Optional
import logging
from app.agents.life_coach_agent import LifeCoachAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_agent(conversation_id: Optional[str] = None) -> LifeCoachAgent:
    """Return a new instance of LifeCoachAgent."""
    agent = LifeCoachAgent(conversation_id=conversation_id)
    logger.info(f"Created LifeCoachAgent with conversation ID: {agent.conversation_id}")
    return agent 