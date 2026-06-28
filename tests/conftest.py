"""
Pytest configuration shared by all tests.

Adds the project root to sys.path so tests can `import src...` the same way
the pipeline scripts do, regardless of which directory pytest is invoked
from.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
