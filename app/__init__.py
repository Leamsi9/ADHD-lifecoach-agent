"""
Initialization file for the Bahai Life Coach application.
"""

# Import the agent adapter to apply the patch
import app.agents.agent_adapter

# Initialize logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🚀 Bahai Life Coach application initialized")
logger.info("🧠 Using LifeCoachAgent with system prompt-based approach")
