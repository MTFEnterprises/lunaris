"""LUNARIS settings in one place. Owner: M1."""
from pathlib import Path

APP_VERSION = "1.0.0"

# backend/config.py -> repo root is two levels up. Never rely on the working directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

# Calls into M2 / M3 modules (master spec: 10 s timeout, 2 retries with backoff).
CALL_TIMEOUT_S = 10.0
CALL_RETRIES = 2
RETRY_BACKOFF_S = 0.2

CACHE_MAX_ENTRIES = 256
