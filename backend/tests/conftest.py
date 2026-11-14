"""Make `import errors`, `import schemas`... work when pytest runs from backend/.

This matches the path setup in backend.main for local flat imports.
Run tests with:  cd backend && python -m pytest
"""
import pathlib
import sys

_BACKEND = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(1, str(_BACKEND.parent))  # also lets `backend.science...` imports work (M2 stopgap)
