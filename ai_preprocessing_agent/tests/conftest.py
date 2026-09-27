"""Pytest configuration to ensure app package is on sys.path."""

import sys
from pathlib import Path

# Add ai_preprocessing_agent root to sys.path
agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))
