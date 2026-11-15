"""Precompute 13-month lunar Sun/Earth MOON_ME vectors (Jan 2027 - Jan 2028, 30-min step)
and per-site 29.5-day window metrics from NASA SPICE.

Outputs:
- data/ephemeris_2027_2028.npz
- data/window_metrics_<site_id>.json (for all sites in data/sites.json)
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

DATA_DIR = REPO_ROOT / "data"
DEFAULT_OUTPUT_NPZ = DATA_DIR / "ephemeris_2027_2028.npz"
SITES_JSON_PATH = DATA_DIR / "sites.json"

START_UTC = "2027-01-01T00:00:00Z"
END_UTC = "2028-01-31T23:30:00Z"
STEP_MIN = 30
WINDOW_HOURS = 708  # 29.5 days (one lunar synodic day)


def generate_ephemeris_npz(
    start_utc: str = START_UTC,
    end_utc: str = END_UTC,
    step_min: int = STEP_MIN,
    kernels_dir: Path = DEFAULT_KERNELS_DIR,
    output_path: Path = DEFAULT_OUTPUT_NPZ,
) -> Path:
    """Compute Moon-centered Sun & Earth MOON_ME vectors [km] and save compressed .npz."""
    import spiceypy as spice

    load_spice_kernels(kernels_dir)

    start_dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
    end_dt = datetime.fromisoformat(end_utc.replace("Z", "+00:00")).astimezone(timezone.utc)

    total_minutes = int((end_dt - start_dt).total_seconds() // 60)
    total_steps = (total_minutes // step_min) + 1

    epoch_s = np.empty(total_steps, dtype=np.float64)
    times_utc: list[str] = []
    sun_vec_km = np.empty((total_steps, 3), dtype=np.float64)
    earth_vec_km = np.empty((total_steps, 3), dtype=np.float64)

    for i in range(total_steps):
        dt = start_dt + timedelta(minutes=i * step_min)
        iso_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        et = float(spice.str2et(iso_str))

        sun_pos, _ = spice.spkpos("SUN", et, LUNAR_FRAME, "LT+S", "MOON")
        earth_pos, _ = spice.spkpos("EARTH", et, LUNAR_FRAME, "LT+S", "MOON")

        epoch_s[i] = (dt - start_dt).total_seconds()
        times_utc.append(iso_str)
        sun_vec_km[i] = np.asarray(sun_pos, dtype=np.float64)
        earth_vec_km[i] = np.asarray(earth_pos, dtype=np.float64)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        epoch_s=epoch_s,
        times_utc=np.asarray(times_utc, dtype="U20"),
        sun_vec_km=sun_vec_km,
        earth_vec_km=earth_vec_km,
        step_min=np.int32(step_min),
        frame=np.asarray(LUNAR_FRAME),
        frame_definition=np.asarray(
            "NAIF moon_080317.tf MOON_ME_DE421 rotation applied to MOON_PA_DE440"
        ),
    )
    return output_path


def generate_all_site_window_metrics(
    sites_path: Path = SITES_JSON_PATH,
    step_days: int = 1,
) -> list[Path]:
    """Precompute 29.5-day (708h) metrics for every valid start date (2027-01-01..2027-12-31) per site."""
    from backend.science.runtime import compute_timeseries

    if not sites_path.exists():
        print(f"[WARN] {sites_path} not found; skipping window_metrics_<id>.json generation.")
        return []

    raw = json.loads(sites_path.read_text(encoding="utf-8"))
    sites = raw["sites"] if isinstance(raw, dict) and "sites" in raw else raw

    scan_start = datetime(2027, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    scan_end = datetime(2027, 12, 31, 0, 0, 0, tzinfo=timezone.utc)

    start_dates: list[str] = []
    curr = scan_start
    while curr <= scan_end:
        start_dates.append(curr.strftime("%Y-%m-%dT%H:%M:%SZ"))
        curr += timedelta(days=step_days)

    written: list[Path] = []
    generated_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for site in sites:
        site_id = site.get("id")
        lat = site.get("lat")
        lon = site.get("lon")
        if not site_id or lat is None or lon is None:
            continue

        lat_val = float(lat)
        lon_val = float(lon)
        if lon_val > 180.0:
            lon_val -= 360.0

        # Check if precomputed M3 horizon exists for this site
        horizon_file = DATA_DIR / f"horizon_{site_id}.json"
        horizon_deg = None
        horizon_payload = {}
        if horizon_file.exists():
            h_payload = json.loads(horizon_file.read_text(encoding="utf-8"))
            if isinstance(h_payload, dict):
                horizon_payload = h_payload
                if "horizon" in h_payload and isinstance(h_payload["horizon"], dict):
                    horizon_deg = h_payload["horizon"].get("deg")
                elif "deg" in h_payload:
                    horizon_deg = h_payload.get("deg")
                elif "horizon_el_deg" in h_payload:
                    horizon_deg = h_payload.get("horizon_el_deg")
        if horizon_deg is None or len(horizon_deg) != 360:
            raise ValueError(f"{site_id}: a complete 360-bin M3 horizon is required")
        if any(value is None for value in horizon_deg):
            raise ValueError(f"{site_id}: horizon has unavailable bins; refusing terrain metrics")

        frame_status = horizon_payload.get(
            "coordinate_frame_status", "UNKNOWN"
        )
        anchor_status = site.get("anchor_status", "PENDING")
        warnings = []
        if anchor_status != "CONFIRMED_PROJECT_ANCHOR":
            warnings.append(
                "PRELIMINARY: the selected site coordinates are not confirmed as the intended project anchor."
            )
        if frame_status != "VERIFIED":
            warnings.append(
                "PRELIMINARY: DEM horizon frame is not confirmed compatible with the M2 MOON_ME ephemeris frame."
            )

        windows: dict[str, dict] = {}
        for s_date in start_dates:
            res = compute_timeseries(
                lat=lat_val,
                lon=lon_val,
                start_utc=s_date,
                hours=WINDOW_HOURS,
                step_min=STEP_MIN,
                horizon_deg=horizon_deg,
            )
            windows[s_date] = res["metrics"]

        out_file = DATA_DIR / f"window_metrics_{site_id}.json"
        out_payload = {
            "site_id": site_id,
            "window_hours": WINDOW_HOURS,
            "step_min": STEP_MIN,
            "status": "PRELIMINARY" if warnings else "VERIFIED",
            "coordinate_frame_status": frame_status,
            "ephemeris_frame": LUNAR_FRAME,
            "horizon_frame": horizon_payload.get("dem", {}).get("frame"),
            "site_coordinates": {
                "lat": lat_val,
                "lon": lon_val,
                "class": site.get("coords_class"),
                "anchor_status": anchor_status,
                "source_url": site.get("coords_source_url"),
                "definition": site.get("notes"),
            },
            "generated_utc": generated_utc,
            "warnings": warnings,
            "windows": windows,
        }
        out_file.write_text(json.dumps(out_payload, separators=(",", ":")), encoding="utf-8")
        written.append(out_file)
        print(f"[OK] Wrote {out_file} ({len(windows)} windows)")

    return written


if __name__ == "__main__":
    npz_out = generate_ephemeris_npz()
    size_kb = npz_out.stat().st_size / 1024.0
    print(f"[OK] Wrote {npz_out} ({size_kb:.1f} KB)")
    generate_all_site_window_metrics()