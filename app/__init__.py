"""
Initialization file for the Bahai Life Coach application.

This file is intentionally empty and serves as a package marker.
All Flask app initialization is done directly in run_flask.py to avoid
circular import issues.
"""

# Initialize logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
