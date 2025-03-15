#!/usr/bin/env python3
"""
Simple runner script for the Bahai Life Coach agent.
This script makes it easier to run the application without needing to set PYTHONPATH.
"""

import os
import sys

# Ensure we're running from the project root
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Run the main application
from app.main import console_interface

if __name__ == "__main__":
    sys.exit(console_interface()) 