"""Vercel serverless entry point. Owner: M1.

Vercel serves the `app` object below. backend/ is put on sys.path so the backend's
flat imports (`from errors import ...`) work exactly as they do locally. The repo
root is added too, so older `from backend.x import ...` imports still resolve
(temporary; remove once everyone uses relative/flat imports).
"""
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(1, str(_ROOT))

from main import app  # noqa: E402,F401  (Vercel looks for `app`)
