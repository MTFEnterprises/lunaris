"""LUNARIS M2 Ephemeris Engine — Moon body-fixed (MOON_ME) Sun & Earth geometry."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import numpy as np

# Authoritative constants from docs/conventions.md & docs/decisions.md
MOON_RADIUS_KM = 1737.4
LUNAR_FRAME = "MOON_ME"
DEFAULT_KERNELS_DIR = Path(__file__).resolve().parents[2] / "kernels"
REQUIRED_KERNELS = (
    "naif0012.tls",
    "de440s.bsp",
    "moon_pa_de440_200625.bpc",
    "moon_080317.tf",
)


class EphemerisError(Exception):
    """Domain error for invalid coordinates, timestamps, or missing SPICE kernels."""


def parse_utc_iso(time_utc: str) -> datetime:
    """Validate and parse an ISO-8601 UTC timestamp string."""
    if not isinstance(time_utc, str) or not time_utc.strip():
        raise EphemerisError("time_utc must be a non-empty ISO-8601 UTC string.")
    normalized = time_utc.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EphemerisError(f"Invalid UTC timestamp format: {time_utc}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def validate_coordinates(lat_deg: float, lon_deg: float, height_m: float = 0.0) -> None:
    """Enforce project conventions: lat [-90, 90], lon [-180, 180] East-positive."""
    if not (-90.0 <= lat_deg <= 90.0):
        raise EphemerisError(f"Latitude {lat_deg} out of range [-90, 90].")
    if not (-180.0 <= lon_deg <= 180.0):
        raise EphemerisError(f"Longitude {lon_deg} out of range [-180, 180].")
    if not (-20000.0 <= height_m <= 50000.0):
        raise EphemerisError(f"Height {height_m} m is outside plausible lunar surface bounds.")


def site_position_moon_me(lat_deg: float, lon_deg: float, height_m: float = 0.0) -> np.ndarray:
    """Return 3D landing site position vector [km] in the MOON_ME frame."""
    validate_coordinates(lat_deg, lon_deg, height_m)
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    r_km = MOON_RADIUS_KM + (height_m / 1000.0)
    return np.array(
        [
            r_km * np.cos(lat) * np.cos(lon),
            r_km * np.cos(lat) * np.sin(lon),
            r_km * np.sin(lat),
        ],
        dtype=np.float64,
    )


def vector_to_enu_az_el(
    target_vec_km: np.ndarray,
    lat_deg: float,
    lon_deg: float,
) -> tuple[float, float]:
    """Convert a MOON_ME target vector (from site to target) into local (az_deg, el_deg).

    Conventions:
    - Azimuth: 0 = North, 90 = East, clockwise [0, 360)
    - Elevation: degrees above local horizontal [-90, 90]
    """
    validate_coordinates(lat_deg, lon_deg)
    vec = np.asarray(target_vec_km, dtype=np.float64)
    norm = np.linalg.norm(vec)
    if norm == 0.0:
        raise EphemerisError("Target vector cannot be zero-length.")
    u_target = vec / norm

    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)

    east = np.array([-np.sin(lon), np.cos(lon), 0.0], dtype=np.float64)
    north = np.array(
        [
            -np.sin(lat) * np.cos(lon),
            -np.sin(lat) * np.sin(lon),
            np.cos(lat),
        ],
        dtype=np.float64,
    )
    up = np.array(
        [
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat),
        ],
        dtype=np.float64,
    )

    e_comp = float(np.dot(u_target, east))
    n_comp = float(np.dot(u_target, north))
    u_comp = float(np.clip(np.dot(u_target, up), -1.0, 1.0))

    el_deg = float(np.degrees(np.arcsin(u_comp)))
    az_deg = float(np.degrees(np.arctan2(e_comp, n_comp)) % 360.0)
    return az_deg, el_deg


def load_spice_kernels(kernels_dir: Path = DEFAULT_KERNELS_DIR) -> None:
    """Furnish required NASA NAIF SPICE kernels; raise clear error if any are missing."""
    try:
        import spiceypy as spice
    except ImportError as exc:
        raise EphemerisError("spiceypy is not installed in this Python environment.") from exc

    missing = [k for k in REQUIRED_KERNELS if not (kernels_dir / k).exists()]
    if missing:
        raise EphemerisError(
            f"Missing SPICE kernel(s) in {kernels_dir}: {', '.join(missing)}. "
            "Run: python scripts/ephemeris/download_kernels.py"
        )

    spice.kclear()
    for name in ("naif0012.tls", "de440s.bsp", "moon_pa_de440_200625.bpc"):
        spice.furnsh(str(kernels_dir / name))

    # Register DE440 Moon Principal Axis frame (ID 31008, binary PCK class 2)
    spice.pipool("FRAME_MOON_PA_DE440", [31008])
    spice.pipool("FRAME_31008_CENTER", [301])
    spice.pipool("FRAME_31008_CLASS", [2])
    spice.pipool("FRAME_31008_CLASS_ID", [31008])
    spice.pcpool("FRAME_31008_NAME", ["MOON_PA_DE440"])

    # Register MOON_ME frame (ID 31006, fixed rotation from MOON_PA_DE440)
    spice.pipool("FRAME_MOON_ME", [31006])
    spice.pipool("FRAME_31006_CENTER", [301])
    spice.pipool("FRAME_31006_CLASS", [4])
    spice.pipool("FRAME_31006_CLASS_ID", [31006])
    spice.pcpool("FRAME_31006_NAME", ["MOON_ME"])
    spice.pcpool("TKFRAME_31006_SPEC", ["ANGLES"])
    spice.pcpool("TKFRAME_31006_RELATIVE", ["MOON_PA_DE440"])
    spice.pcpool("TKFRAME_31006_UNITS", ["ARCSECONDS"])
    spice.pipool("TKFRAME_31006_AXES", [3, 2, 1])
    spice.pdpool("TKFRAME_31006_ANGLES", [-67.92, -78.56, -0.30])


def moon_center_vectors_spice(
    time_utc: str,
    kernels_dir: Path = DEFAULT_KERNELS_DIR,
    auto_load: bool = True,
) -> dict[str, np.ndarray]:
    """Compute Moon-center -> Sun and Moon-center -> Earth vectors [km] in MOON_ME."""
    dt = parse_utc_iso(time_utc)
    if auto_load:
        load_spice_kernels(kernels_dir)

    import spiceypy as spice

    et = spice.str2et(dt.strftime("%Y-%m-%dT%H:%M:%S.%f"))
    sun_pos, _ = spice.spkpos("SUN", et, LUNAR_FRAME, "LT+S", "MOON")
    earth_pos, _ = spice.spkpos("EARTH", et, LUNAR_FRAME, "LT+S", "MOON")

    return {
        "sun_vec_km": np.asarray(sun_pos, dtype=np.float64),
        "earth_vec_km": np.asarray(earth_pos, dtype=np.float64),
    }


def sun_earth_at(
    lat_deg: float,
    lon_deg: float,
    time_utc: str,
    height_m: float = 0.0,
    sun_vec_km: np.ndarray | None = None,
    earth_vec_km: np.ndarray | None = None,
    kernels_dir: Path = DEFAULT_KERNELS_DIR,
) -> dict:
    """Return local Sun & Earth azimuth/elevation and body-fixed unit vectors.

    If precomputed sun_vec_km / earth_vec_km are passed, executes purely in NumPy
    (fast runtime path). Otherwise queries SPICE directly (offline verification path).
    """
    dt = parse_utc_iso(time_utc)
    site_vec = site_position_moon_me(lat_deg, lon_deg, height_m)

    if sun_vec_km is None or earth_vec_km is None:
        vecs = moon_center_vectors_spice(dt.isoformat(), kernels_dir=kernels_dir)
        sun_vec = vecs["sun_vec_km"]
        earth_vec = vecs["earth_vec_km"]
    else:
        sun_vec = np.asarray(sun_vec_km, dtype=np.float64)
        earth_vec = np.asarray(earth_vec_km, dtype=np.float64)

    # Topocentric parallax correction for Earth (~384,400 km away -> up to ~0.26 deg shift)
    earth_topo_vec = earth_vec - site_vec

    sun_az, sun_el = vector_to_enu_az_el(sun_vec, lat_deg, lon_deg)
    earth_az, earth_el = vector_to_enu_az_el(earth_topo_vec, lat_deg, lon_deg)

    return {
        "time_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frame": LUNAR_FRAME,
        "site": {
            "lat_deg": float(lat_deg),
            "lon_deg": float(lon_deg),
            "height_m": float(height_m),
        },
        "sun_az_deg": round(sun_az, 4),
        "sun_el_deg": round(sun_el, 4),
        "earth_az_deg": round(earth_az, 4),
        "earth_el_deg": round(earth_el, 4),
        "sun_dir_bf": (sun_vec / np.linalg.norm(sun_vec)).tolist(),
        "earth_dir_bf": (earth_topo_vec / np.linalg.norm(earth_topo_vec)).tolist(),
        "provenance": "CALCULATED",
    }