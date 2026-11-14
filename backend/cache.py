"""In-memory response cache (F33). Owner: M1.

Key = hash(endpoint + canonical request JSON). A hit returns the stored envelope
with "cached": true. The ORIGINAL provenance.generated_utc is kept, so a cached
result is never passed off as fresh (honesty rule).

Only successful responses are cached (errors raise before we store anything).
On Vercel each serverless instance has its own memory, so this is a speed-up and
a demo safety net, not a guarantee.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections import OrderedDict
from typing import Any, Callable

from pydantic import BaseModel

import config
from schemas import Envelope

_store: "OrderedDict[str, Envelope]" = OrderedDict()
_lock = threading.Lock()


def make_key(endpoint: str, payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{endpoint}|{canonical}".encode()).hexdigest()


def request_key(endpoint: str, request: BaseModel) -> str:
    return make_key(endpoint, request.model_dump(mode="json"))


def get(key: str) -> Envelope | None:
    with _lock:
        env = _store.get(key)
        if env is not None:
            _store.move_to_end(key)
        return env


def put(key: str, env: Envelope) -> None:
    with _lock:
        _store[key] = env
        _store.move_to_end(key)
        while len(_store) > config.CACHE_MAX_ENTRIES:
            _store.popitem(last=False)  # drop the oldest


def clear() -> None:
    with _lock:
        _store.clear()


def size() -> int:
    with _lock:
        return len(_store)


def cached_envelope(endpoint: str, request: BaseModel, build: Callable[[], Envelope]) -> Envelope:
    """Return the cached envelope for this request, or build, store and return it."""
    key = request_key(endpoint, request)
    hit = get(key)
    if hit is not None:
        return hit.model_copy(update={"cached": True})
    env = build()
    put(key, env)
    return env
