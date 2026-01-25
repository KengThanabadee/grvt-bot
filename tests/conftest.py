import pytest
import sys
import os

# Add parent dir to path so we can import execution and config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution import GRVTExecutor
import config

@pytest.fixture(scope="module")
def executor():
    """Initializes the GRVTExecutor with config values."""
    print(f"\nInitializing Executor with Env: {config.GRVT_ENV}")
    ex = GRVTExecutor()
    return ex

