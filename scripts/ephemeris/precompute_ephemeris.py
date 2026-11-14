"""Precompute 30-day lunar South Pole Sun/Earth MOON_ME vectors from NASA SPICE.

Generates a lightweight JSON bundle in backend/fallback/ephemeris_precomputed.json
so serverless deployments (e.g., Vercel) can run exact SPICE ephemeris interpolation
without shipping multi-megabyte binary BSP/BPC kernels.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.science.ephemeris import DEFAULT_KERNELS_DIR, LUNAR_FRAME, load_spice_kernels

DEFAULT_OUTPUT_PATH = REPO_ROOT / "backend" / "fallback" / "ephemeris_precomputed.json"


def generate_ephemeris_bundle(
    start_utc: str = "2027-03-01T00:00:00Z",
    days: int = 30,
    step_hours: int = 1,
    kernels_dir: Path = DEFAULT_KERNELS_DIR,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    """Compute Moon-centered Sun & Earth MOON_ME vectors and write JSON bundle."""
    import spiceypy as spice

    load_spice_kernels(kernels_dir)

    start_dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
    total_steps = int((days * 24) / step_hours) + 1

    epochs_utc: list[str] = []
    sun_vectors_km: list[list[float]] = []
    earth_vectors_km: list[list[float]] = []

    for i in range(total_steps):
        dt = start_dt + timedelta(hours=i * step_hours)
        iso_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        et = float(spice.str2et(iso_str))

        sun_pos, _ = spice.spkpos("SUN", et, LUNAR_FRAME, "LT+S", "MOON")
        earth_pos, _ = spice.spkpos("EARTH", et, LUNAR_FRAME, "LT+S", "MOON")

        epochs_utc.append(iso_str)
        sun_vectors_km.append([round(float(x), 3) for x in np.asarray(sun_pos)])
        earth_vectors_km.append([round(float(x), 3) for x in np.asarray(earth_pos)])

    payload = {
        "schema_version": "1.0",
        "provenance": "PRECOMPUTED_SPICE",
        "frame": LUNAR_FRAME,
        "kernels": ["naif0012.tls", "de440s.bsp", "moon_pa_de440_200625.bpc"],
        "start_utc": epochs_utc[0],
        "end_utc": epochs_utc[-1],
        "step_hours": step_hours,
        "sample_count": len(epochs_utc),
        "epochs_utc": epochs_utc,
        "sun_vectors_km": sun_vectors_km,
        "earth_vectors_km": earth_vectors_km,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    out = generate_ephemeris_bundle()
    size_kb = out.stat().st_size / 1024.0
    print(f"[OK] Wrote {out} ({size_kb:.1f} KB)")