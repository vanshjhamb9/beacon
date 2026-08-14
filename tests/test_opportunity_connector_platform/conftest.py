"""Tests for opportunity_connector_platform — conftest fixtures."""
import sys
from pathlib import Path

# Ensure packages/ is on sys.path for all test collection
_PACKAGES_DIR = str(Path(__file__).resolve().parent.parent / "packages")
if _PACKAGES_DIR not in sys.path:
    sys.path.insert(0, _PACKAGES_DIR)
