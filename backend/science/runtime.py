"""LUNARIS M2 Runtime Science Adapter — Pure NumPy execution for Vercel/FastAPI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Sequence
import numpy as np

from .ephemeris import (
    EphemerisError,
    parse_utc_iso,
    site_position_moon_me,
    vectors_to_enu_az_el_batch,
)
from .illumination import (
    HorizonProfile,
    evaluate_illumination_batch,
)
from .power import (
    SolarArrayConfig,
    simulate_power_budget,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

EPOCH_REF = datetime(2027, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _to_epoch_seconds(dt: datetime) -> float:
    return (dt.astimezone(timezone.utc) - EPOCH_REF).total_seconds()


def _format_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@lru_cache(maxsize=1)
def _load_ephemeris_npz() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load precomputed Moon-center -> Sun and Moon-center -> Earth vectors [km] from data/."""
    npz_files = sorted(DATA_DIR.glob("ephemeris_*.npz"))
    if not npz_files:
        raise FileNotFoundError(
            f"No precomputed ephemeris_*.npz file found in {DATA_DIR}. "
            "Run: python scripts/ephemeris/precompute_ephemeris.py"
        )
    # Use the latest / primary ephemeris file in data/
    target_file = npz_files[-1]
    with np.load(target_file) as data:
        if "epoch_s" in data:
            epoch_s = np.asarray(data["epoch_s"], dtype=np.float64)
        elif "times_utc" in data:
            times = [parse_utc_iso(str(t)) for t in data["times_utc"]]
            epoch_s = np.array([_to_epoch_seconds(t) for t in times], dtype=np.float64)
        else:
            raise KeyError(f"{target_file.name} must contain 'epoch_s' or 'times_utc'.")

        sun_vecs = np.asarray(data["sun_vec_km"], dtype=np.float64)
        earth_vecs = np.asarray(data["earth_vec_km"], dtype=np.float64)

    return epoch_s, sun_vecs, earth_vecs


def _interpolate_vectors(query_epochs_s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Linearly interpolate 3D Sun & Earth MOON_ME vectors [km] at query_epochs_s."""
    epoch_s, sun_vecs, earth_vecs = _load_ephemeris_npz()
    if query_epochs_s[0] < epoch_s[0] or query_epochs_s[-1] > epoch_s[-1]:
        raise EphemerisError(
            "Requested time window falls outside precomputed ephemeris coverage."
        )

    sun_interp = np.column_stack(
        [np.interp(query_epochs_s, epoch_s, sun_vecs[:, axis]) for axis in range(3)]
    )
    earth_interp = np.column_stack(
        [np.interp(query_epochs_s, epoch_s, earth_vecs[:, axis]) for axis in range(3)]
    )
    return sun_interp, earth_interp


def _longest_false_run_hours(mask: np.ndarray, step_min: int) -> float:
    """Return longest contiguous False streak in hours."""
    if mask.size == 0:
        return 0.0
    dark = ~np.asarray(mask, dtype=bool)
    if not np.any(dark):
        return 0.0
    padded = np.concatenate(([False], dark, [False]))
    diffs = np.diff(padded.astype(np.int8))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    max_steps = int(np.max(ends - starts))
    return round((max_steps * step_min) / 60.0, 2)


def compute_timeseries(
    lat: float,
    lon: float,
    start_utc: str,
    hours: int = 708,
    step_min: int = 30,
    horizon_deg: Sequence[float | None] | None = None,
) -> dict[str, Any]:
    """Compute Sun & Earth ephemeris, geometric & terrain-corrected visibility, and metrics.

    - Uses upper solar limb (+0.27 deg) for Sun illumination.
    - Applies topocentric parallax correction (earth_vec - site_vec) for Earth visibility.
    - When horizon_deg is None, all terrain fields are strictly returned as None.
    """
    start_dt = parse_utc_iso(start_utc)
    total_minutes = int(hours * 60)
    n_steps = (total_minutes // int(step_min)) + 1

    start_sec = _to_epoch_seconds(start_dt)
    step_sec = float(step_min * 60)
    query_epochs_s = start_sec + np.arange(n_steps, dtype=np.float64) * step_sec

    sun_vecs_km, earth_vecs_km = _interpolate_vectors(query_epochs_s)

    # Topocentric parallax correction for Earth (~up to 0.26 deg shift)
    site_vec_km = site_position_moon_me(lat, lon, height_m=0.0)
    earth_topo_vecs_km = earth_vecs_km - site_vec_km[None, :]

    sun_az, sun_el = vectors_to_enu_az_el_batch(sun_vecs_km, lat, lon)
    earth_az, earth_el = vectors_to_enu_az_el_batch(earth_topo_vecs_km, lat, lon)

    warnings: list[str] = []
    profile: HorizonProfile | None = None

    if horizon_deg is not None:
        arr = np.asarray(
            [np.nan if v is None else float(v) for v in horizon_deg],
            dtype=np.float64,
        )
        if arr.shape != (360,) or np.isnan(arr).any():
            warnings.append("Invalid or incomplete 360-deg horizon profile; terrain fields unavailable.")
        else:
            profile = HorizonProfile(
                azimuth_deg=np.arange(360.0, dtype=np.float64),
                horizon_el_deg=arr,
            )

    illum = evaluate_illumination_batch(
        sun_az_deg=sun_az,
        sun_el_deg=sun_el,
        earth_az_deg=earth_az,
        earth_el_deg=earth_el,
        horizon_profile=profile,
    )

    sun_lit_geom = illum["sun_lit_geom"]
    sun_lit_terrain = illum["sun_lit_terrain"]
    earth_vis_geom = illum["earth_vis_geom"]
    earth_vis_terrain = illum["earth_vis_terrain"]
    assert sun_lit_geom is not None and earth_vis_geom is not None

    sunlit_geom_pct = round(float(np.mean(sun_lit_geom) * 100.0), 2)
    earth_geom_pct = round(float(np.mean(earth_vis_geom) * 100.0), 2)
    max_sun_el_deg = round(float(np.max(sun_el)), 4)

    if sun_lit_terrain is not None and earth_vis_terrain is not None:
        sunlit_terrain_pct: float | None = round(float(np.mean(sun_lit_terrain) * 100.0), 2)
        earth_terrain_pct: float | None = round(float(np.mean(earth_vis_terrain) * 100.0), 2)
        longest_dark_h = _longest_false_run_hours(sun_lit_terrain, step_min)
        longest_comms_gap_h = _longest_false_run_hours(earth_vis_terrain, step_min)
        sun_lit_terrain_list: list[bool | None] | None = [bool(x) for x in sun_lit_terrain]
        earth_vis_terrain_list: list[bool | None] | None = [bool(x) for x in earth_vis_terrain]
    else:
        sunlit_terrain_pct = None
        earth_terrain_pct = None
        longest_dark_h = _longest_false_run_hours(sun_lit_geom, step_min)
        longest_comms_gap_h = _longest_false_run_hours(earth_vis_geom, step_min)
        sun_lit_terrain_list = None
        earth_vis_terrain_list = None

    return {
        "timeseries": {
            "start_utc": _format_utc(start_dt),
            "step_min": int(step_min),
            "sun_el": [round(float(x), 4) for x in sun_el],
            "sun_az": [round(float(x), 4) for x in sun_az],
            "earth_el": [round(float(x), 4) for x in earth_el],
            "earth_az": [round(float(x), 4) for x in earth_az],
            "sun_lit_geom": [bool(x) for x in sun_lit_geom],
            "sun_lit_terrain": sun_lit_terrain_list,
            "earth_vis_geom": [bool(x) for x in earth_vis_geom],
            "earth_vis_terrain": earth_vis_terrain_list,
        },
        "metrics": {
            "sunlit_geom_pct": sunlit_geom_pct,
            "sunlit_terrain_pct": sunlit_terrain_pct,
            "earth_geom_pct": earth_geom_pct,
            "earth_terrain_pct": earth_terrain_pct,
            "longest_dark_h": longest_dark_h,
            "longest_comms_gap_h": longest_comms_gap_h,
            "max_sun_el_deg": max_sun_el_deg,
        },
        "warnings": warnings,
    }


def window_metrics(site_id: str, start_dates: Sequence[str]) -> list[dict[str, Any]]:
    """Return precomputed 29.5-day metrics per start_date from data/window_metrics_<id>.json."""
    metrics_path = DATA_DIR / f"window_metrics_{site_id}.json"
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Precomputed window metrics file not found: {metrics_path}"
        )

    with metrics_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    # Support either {"windows": {"2027-01-01T00:00:00Z": {...}}} or flat dict / list
    if isinstance(payload, dict) and "windows" in payload:
        lookup = payload["windows"]
    elif isinstance(payload, dict):
        lookup = payload
    elif isinstance(payload, list):
        lookup = {item["start_utc"]: item.get("metrics", item) for item in payload if "start_utc" in item}
    else:
        raise ValueError(f"Unexpected format in {metrics_path.name}")

    results: list[dict[str, Any]] = []
    for raw_date in start_dates:
        norm_date = _format_utc(parse_utc_iso(raw_date))
        entry = lookup.get(norm_date) or lookup.get(raw_date)
        if isinstance(entry, dict) and "metrics" in entry and "start_utc" in entry:
            metrics_obj = entry["metrics"]
        else:
            metrics_obj = entry
        results.append({"start_utc": norm_date, "metrics": metrics_obj})

    return results


def estimate_power(timeseries: dict[str, Any], panel: Any) -> dict[str, Any]:
    """Estimate solar array power output [W] and total energy [Wh] over a timeseries.

    Uses terrain-corrected solar disk fractions when terrain illumination is present
    so shadowed intervals produce 0 W.
    """
    ts = timeseries["timeseries"] if "timeseries" in timeseries else timeseries
    start_dt = parse_utc_iso(ts["start_utc"])
    step_min = int(ts.get("step_min", 30))
    dt_hours = step_min / 60.0

    sun_az = np.asarray(ts["sun_az"], dtype=np.float64)
    sun_el = np.asarray(ts["sun_el"], dtype=np.float64)
    n = len(sun_el)

    times_utc = [_format_utc(start_dt + timedelta(minutes=i * step_min)) for i in range(n)]

    # Extract panel parameters from dict or Pydantic PanelSpec
    def _get(field: str, default: float) -> float:
        if isinstance(panel, dict):
            return float(panel.get(field, default))
        return float(getattr(panel, field, default))

    area_m2 = _get("area_m2", 2.0)
    efficiency = _get("efficiency", 0.28)
    losses = _get("losses", 0.0)
    tilt_deg = _get("tilt_deg", 0.0)
    azimuth_deg = _get("azimuth_deg", 0.0)

    # Compute solar disk fractions: zero out any step blocked by terrain shadow
    from .illumination import compute_solar_disk_fraction_batch

    sun_lit_terrain = ts.get("sun_lit_terrain")
    sun_lit_geom = ts.get("sun_lit_geom")

    if sun_lit_terrain is not None:
        # Terrain-corrected visibility available: blocked intervals get disk fraction = 0.0
        terrain_mask = np.array([bool(v) for v in sun_lit_terrain], dtype=bool)
        base_fractions = compute_solar_disk_fraction_batch(sun_el)
        disk_fractions = np.where(terrain_mask, base_fractions, 0.0)
    elif sun_lit_geom is not None:
        geom_mask = np.array([bool(v) for v in sun_lit_geom], dtype=bool)
        base_fractions = compute_solar_disk_fraction_batch(sun_el)
        disk_fractions = np.where(geom_mask, base_fractions, 0.0)
    else:
        disk_fractions = compute_solar_disk_fraction_batch(sun_el)

    cfg = SolarArrayConfig(
        area_m2=area_m2,
        efficiency=efficiency,
        losses=losses,
        mount_mode="fixed",
        panel_tilt_deg=min(tilt_deg, 90.0),
        panel_az_deg=azimuth_deg,
    )

    budget = simulate_power_budget(
        times_utc=times_utc,
        sun_az_deg=sun_az.tolist(),
        sun_el_deg=sun_el.tolist(),
        solar_disk_fractions=disk_fractions.tolist(),
        dt_hours=dt_hours,
        config=cfg,
    )

    power_w = [round(float(step["generated_w"]), 3) for step in budget["series"]]
    peak_w = round(max(power_w), 3) if power_w else 0.0
    energy_wh = round(float(budget["total_generated_wh"]), 2)

    return {
        "power_w": power_w,
        "peak_w": peak_w,
        "energy_wh": energy_wh,
    }