"""
Pytest configuration and shared fixtures
"""
import sys
from pathlib import Path

# Backend path'i Python path'e ekle
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
