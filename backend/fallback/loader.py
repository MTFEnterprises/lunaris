"""Labelled fallback scenarios (F32). Owner: M1.

If a LIVE computation fails (503) for a curated site, and a stored scenario with the
same site_id / start_utc / hours exists here, we return it, clearly labelled.

Rules (M1 PDF): fallback files must come from REAL precomputed output (or be marked
ILLUSTRATIVE). Never hand-made numbers presented as real. Every file must carry
provenance.class and provenance.generated_utc (retrieval time).

File format, backend/fallback/scenarios/<anything>.json:
{
  "match": {"site_id": "...", "start_utc": "2027-03-14T06:00:00Z", "hours": 708},
  "envelope": { "data": {...ScenarioData...}, "provenance": {...}, "warnings": [], "cached": false }
}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from schemas import Envelope, ScenarioData

logger = logging.getLogger("lunaris")
FALLBACK_DIR = Path(__file__).resolve().parent / "scenarios"


def find_scenario(site_id: str | None, start_utc: str, hours: int) -> Envelope[ScenarioData] | None:
    if site_id is None or not FALLBACK_DIR.is_dir():
        return None
    for path in sorted(FALLBACK_DIR.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            m = doc["match"]
            if (m.get("site_id"), m.get("start_utc"), m.get("hours")) != (site_id, start_utc, hours):
                continue
            env = Envelope[ScenarioData].model_validate(doc["envelope"])
        except (OSError, KeyError, ValueError, ValidationError) as exc:
            logger.warning("Skipping bad fallback file %s: %s", path.name, exc)
            continue
        if not env.provenance.generated_utc:
            logger.warning("Fallback %s has no generated_utc; refusing to use it.", path.name)
            continue
        env.warnings = [
            f"Live computation failed. Showing a stored fallback result "
            f"(class {env.provenance.cls.value}, generated {env.provenance.generated_utc}).",
            *env.warnings,
        ]
        env.cached = True
        return env
    return None
