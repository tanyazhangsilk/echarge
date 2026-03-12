import sys
from pathlib import Path

# Ensure project root on sys.path for consistent imports
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.app import app
