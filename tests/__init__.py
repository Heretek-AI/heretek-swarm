"""
Test package initialization.
Sets up module-level mocks before test collection.
"""
import sys
from unittest.mock import MagicMock

# Mock pynats to avoid import errors for NATS dependencies
if "pynats" not in sys.modules:
    mock_pynats = MagicMock()
    sys.modules["pynats"] = mock_pynats
