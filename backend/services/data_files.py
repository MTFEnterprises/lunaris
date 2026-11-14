"""Read M3's precomputed data files straight from data/. Owner: M1.

Why: M3's terrain modules import rasterio/pyproj (not installed on Vercel). The
runtime only needs the SMALL precomputed outputs, so we read them here:

  data/sites.json              -> {"sites": [...]}  (or a plain list)
  data/horizon_<site_id>.json  -> {"deg": [360], "dem": {...}, "approx": bool, "status": "OK", ...}

Missing file -> None (the caller turns that into an honest UNAVAILABLE).
Broken file  -> ServiceUnavailable with the file name.
Files may be UTF-8 (with or without BOM) or UTF-16 (Windows PowerShell often writes UTF-16).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import config
from errors import ServiceUnavailable

_SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def read_json(path: Path) -> Any:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
        return json.loads(text)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ServiceUnavailable(
            f"Data file '{path.name}' could not be read: {exc}", {"file": path.name}
        ) from exc


def load_sites_raw() -> list[dict[str, Any]] | None:
    path = config.DATA_DIR / "sites.json"
    if not path.is_file():
        return None
    doc = read_json(path)
    sites = doc.get("sites") if isinstance(doc, dict) else doc
    if not isinstance(sites, list):
        raise ServiceUnavailable(
            "data/sites.json must be a list of sites or an object with a 'sites' list.",
            {"file": "sites.json"},
        )
    return sites


def load_horizon_raw(site_id: str) -> dict[str, Any] | None:
    if not _SAFE_ID.fullmatch(site_id):  # never build a path from unchecked input
        return None
    path = config.DATA_DIR / f"horizon_{site_id}.json"
    if not path.is_file():
        return None
    doc = read_json(path)
    if not isinstance(doc, dict):
        raise ServiceUnavailable(f"{path.name} must be a JSON object.", {"file": path.name})
    return doc
