"""Build labelled fallback scenarios (F32) from the REAL backend output. Owner: M1.

Run from the repo root (offline, on a laptop):  python scripts/fallback/make_fallback.py
Each file stores the real /api/timeline envelope for one curated site + start date, with
provenance.generated_utc (retrieval time). Used only when the live computation fails (503).
No number here is hand-made; re-run this script after M2/M3 data changes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

OUT = ROOT / "backend" / "fallback" / "scenarios"
START = "2027-03-14T06:00:00Z"
HOURS = 708  # default 29.5-day window
SITES = ["shackleton_rim", "malapert_massif", "haworth"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    for site in SITES:
        r = client.post("/api/timeline", json={"site_id": site, "start_utc": START, "hours": HOURS})
        r.raise_for_status()
        env = r.json()
        env["cached"] = False
        doc = {"match": {"site_id": site, "start_utc": START, "hours": HOURS}, "envelope": env}
        path = OUT / f"{site}_2027-03-14.json"
        path.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB, class {env['provenance']['class']})")


if __name__ == "__main__":
    main()
