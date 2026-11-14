"""Helpers for calling M2 / M3 code safely. Owner: M1.

  load("terrain.horizon", "get_horizon")  -> the function, or 501 if that module is not merged yet
  call_with_retry(fn, *args)              -> 10 s timeout, 2 retries with backoff, then 503
  get(obj, "name")                        -> works for dict, object, dataclass, pydantic model
  plain(x)                                -> numpy -> python, NaN -> None (JSON-safe)
"""

from __future__ import annotations

import dataclasses
import importlib
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

import config
from errors import FeatureNotAvailable, LunarisError, ServiceUnavailable

_pool = ThreadPoolExecutor(max_workers=8)


def load(module: str, attr: str) -> Callable:
    """Import M2/M3 code lazily, so the API still starts before their modules exist."""
    try:
        mod = importlib.import_module(module)
    except ImportError as exc:
        missing = getattr(exc, "name", None) or ""
        if module == missing or module.startswith(missing + "."):
            raise FeatureNotAvailable(
                f"'{module}' is not merged yet, so this feature is not connected.",
                {"module": module},
            ) from exc
        raise ServiceUnavailable(
            f"Module '{module}' failed to import: {exc}", {"module": module}
        ) from exc
    fn = getattr(mod, attr, None)
    if fn is None:
        raise FeatureNotAvailable(
            f"'{module}.{attr}' is not implemented yet.", {"module": module, "function": attr}
        )
    return fn


def call_with_retry(fn: Callable, *args: Any, timeout: float | None = None,
                    retries: int | None = None, **kwargs: Any) -> Any:
    timeout = config.CALL_TIMEOUT_S if timeout is None else timeout
    retries = config.CALL_RETRIES if retries is None else retries
    name = getattr(fn, "__name__", "function")
    last = "unknown failure"
    for attempt in range(retries + 1):
        future = _pool.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except LunarisError:
            raise  # M2/M3 raised a proper error: pass it through unchanged
        except FutureTimeout:
            last = f"timed out after {timeout:g} s"
        except Exception as exc:  # noqa: BLE001 - any failure inside M2/M3 code
            last = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(config.RETRY_BACKOFF_S * (2**attempt))
    raise ServiceUnavailable(
        f"{name} failed after {retries + 1} attempts ({last}).",
        {"function": name, "attempts": retries + 1},
    )


def get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def as_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return dict(vars(obj))


def plain(x: Any) -> Any:
    """numpy arrays/scalars -> python; NaN -> None (JSON cannot hold NaN)."""
    if hasattr(x, "tolist"):
        x = x.tolist()
    if isinstance(x, (list, tuple)):
        return [plain(i) for i in x]
    if isinstance(x, float) and x != x:
        return None
    return x


def build_model(model: type[BaseModel], /, **kwargs: Any) -> Any:
    """Build a schema model from M2/M3 output; bad shape -> 503 with a clear message."""
    try:
        return model(**kwargs)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()[:5]
        )
        raise ServiceUnavailable(
            f"A science/terrain module returned data in an unexpected shape ({model.__name__}): {problems}",
            {"model": model.__name__},
        ) from exc
