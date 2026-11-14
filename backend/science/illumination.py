"""LUNARIS M2 Illumination Engine — Geometric & terrain-corrected solar visibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np

# Solar apparent angular radius / upper limb threshold at ~1 AU [degrees]
SOLAR_ANGULAR_RADIUS_DEG = 0.27


class IlluminationError(Exception):
    """Domain error for invalid horizon profiles, azimuth grids, or illumination inputs."""


@dataclass(frozen=True)
class HorizonProfile:
    """360-degree terrain horizon elevation profile supplied by M3 DEM pipeline.

    Conventions:
    - azimuth_deg: strictly increasing in [0, 360), 0 = North, 90 = East, clockwise.
    - horizon_el_deg: terrain obstruction elevation angle in [-90, 90] degrees.
    """

    azimuth_deg: np.ndarray
    horizon_el_deg: np.ndarray

    def __post_init__(self) -> None:
        az = np.asarray(self.azimuth_deg, dtype=np.float64)
        el = np.asarray(self.horizon_el_deg, dtype=np.float64)

        if az.ndim != 1 or el.ndim != 1 or az.shape != el.shape:
            raise IlluminationError("azimuth_deg and horizon_el_deg must be 1D arrays of equal length.")
        if az.size < 4:
            raise IlluminationError("Horizon profile requires at least 4 azimuth samples.")
        if np.any((az < 0.0) | (az >= 360.0)):
            raise IlluminationError("Horizon azimuth_deg values must be within [0, 360).")
        if np.any(np.diff(az) <= 0.0):
            raise IlluminationError("Horizon azimuth_deg must be strictly increasing.")
        if np.any((el < -90.0) | (el > 90.0)):
            raise IlluminationError("Horizon horizon_el_deg values must be within [-90, 90].")

        object.__setattr__(self, "azimuth_deg", az)
        object.__setattr__(self, "horizon_el_deg", el)

    @classmethod
    def flat(cls, step_deg: float = 1.0) -> HorizonProfile:
        """Return a flat 0-degree horizon profile (fallback when M3 DEM is unavailable)."""
        if step_deg <= 0.0 or step_deg > 90.0:
            raise IlluminationError("step_deg must be in (0, 90].")
        az = np.arange(0.0, 360.0, step_deg, dtype=np.float64)
        el = np.zeros_like(az)
        return cls(azimuth_deg=az, horizon_el_deg=el)

    @classmethod
    def from_m3_dict(cls, payload: dict) -> HorizonProfile:
        """Parse M3 horizon schema payload into a validated HorizonProfile."""
        if not isinstance(payload, dict):
            raise IlluminationError("M3 horizon payload must be a dictionary.")
        if "azimuth_deg" not in payload or "horizon_el_deg" not in payload:
            raise IlluminationError("M3 horizon payload missing 'azimuth_deg' or 'horizon_el_deg'.")
        return cls(
            azimuth_deg=np.asarray(payload["azimuth_deg"], dtype=np.float64),
            horizon_el_deg=np.asarray(payload["horizon_el_deg"], dtype=np.float64),
        )


def interpolate_horizon_el(sun_az_deg: float, profile: HorizonProfile) -> float:
    """Periodic linear interpolation of terrain horizon elevation at sun_az_deg [0, 360)."""
    az_query = float(sun_az_deg) % 360.0
    az_grid = profile.azimuth_deg
    el_grid = profile.horizon_el_deg

    az_wrapped = np.append(az_grid, az_grid[0] + 360.0)
    el_wrapped = np.append(el_grid, el_grid[0])

    if az_query < az_wrapped[0]:
        az_query += 360.0

    return float(np.interp(az_query, az_wrapped, el_wrapped))


def interpolate_horizon_el_batch(
    az_deg: np.ndarray,
    profile: HorizonProfile,
) -> np.ndarray:
    """Vectorized periodic linear interpolation of terrain horizon elevation."""
    az_query = np.asarray(az_deg, dtype=np.float64) % 360.0
    az_grid = profile.azimuth_deg
    el_grid = profile.horizon_el_deg

    az_wrapped = np.append(az_grid, az_grid[0] + 360.0)
    el_wrapped = np.append(el_grid, el_grid[0])

    az_query = np.where(az_query < az_wrapped[0], az_query + 360.0, az_query)
    return np.interp(az_query, az_wrapped, el_wrapped)


def compute_solar_disk_fraction_batch(clearance_deg: np.ndarray) -> np.ndarray:
    """Vectorized visible solar disk fraction [0.0, 1.0] given clearance above horizon [deg]."""
    c = np.asarray(clearance_deg, dtype=np.float64)
    r_sun = SOLAR_ANGULAR_RADIUS_DEG
    frac = np.empty_like(c, dtype=np.float64)

    full_dark = c <= -r_sun
    full_lit = c >= r_sun
    partial = ~(full_dark | full_lit)

    frac[full_dark] = 0.0
    frac[full_lit] = 1.0

    if np.any(partial):
        x = np.clip(-c[partial] / r_sun, -1.0, 1.0)
        occulted = (np.arccos(x) - x * np.sqrt(np.maximum(0.0, 1.0 - x * x))) / np.pi
        frac[partial] = np.clip(1.0 - occulted, 0.0, 1.0)

    return frac


def evaluate_illumination_batch(
    sun_az_deg: np.ndarray,
    sun_el_deg: np.ndarray,
    earth_az_deg: np.ndarray,
    earth_el_deg: np.ndarray,
    horizon_profile: HorizonProfile | None = None,
) -> dict[str, np.ndarray | None]:
    """Vectorized geometric & terrain-corrected visibility for Sun (0.27 deg limb) and Earth.

    When horizon_profile is None, all terrain arrays are strictly returned as None.
    """
    s_az = np.asarray(sun_az_deg, dtype=np.float64)
    s_el = np.asarray(sun_el_deg, dtype=np.float64)
    e_az = np.asarray(earth_az_deg, dtype=np.float64)
    e_el = np.asarray(earth_el_deg, dtype=np.float64)

    # Geometric visibility (upper solar limb at -0.27 deg; Earth center at 0.0 deg)
    sun_lit_geom = s_el > -SOLAR_ANGULAR_RADIUS_DEG
    earth_vis_geom = e_el > 0.0
    geom_disk_fraction = compute_solar_disk_fraction_batch(s_el)

    if horizon_profile is None:
        return {
            "sun_lit_geom": sun_lit_geom,
            "sun_lit_terrain": None,
            "earth_vis_geom": earth_vis_geom,
            "earth_vis_terrain": None,
            "solar_disk_fraction": geom_disk_fraction,
        }

    sun_hor = interpolate_horizon_el_batch(s_az, horizon_profile)
    earth_hor = interpolate_horizon_el_batch(e_az, horizon_profile)

    sun_clearance = s_el - sun_hor
    terrain_disk_fraction = compute_solar_disk_fraction_batch(sun_clearance)
    sun_lit_terrain = terrain_disk_fraction > 0.0
    earth_vis_terrain = e_el > earth_hor

    return {
        "sun_lit_geom": sun_lit_geom,
        "sun_lit_terrain": sun_lit_terrain,
        "earth_vis_geom": earth_vis_geom,
        "earth_vis_terrain": earth_vis_terrain,
        "solar_disk_fraction": terrain_disk_fraction,
    }


def evaluate_sunlight(
    sun_az_deg: float,
    sun_el_deg: float,
    horizon_profile: HorizonProfile | None = None,
    include_solar_disk: bool = True,
) -> dict:
    """Evaluate geometric and terrain-corrected sunlight state at a single epoch."""
    geometric_sunlit = bool(sun_el_deg > -SOLAR_ANGULAR_RADIUS_DEG)

    if horizon_profile is None:
        disk_fraction = (
            float(compute_solar_disk_fraction_batch(np.asarray([sun_el_deg]))[0])
            if include_solar_disk
            else float(sun_el_deg > 0.0)
        )
        return {
            "geometric_sunlit": geometric_sunlit,
            "terrain_sunlit": None,
            "sun_az_deg": round(float(sun_az_deg) % 360.0, 4),
            "sun_el_deg": round(float(sun_el_deg), 4),
            "horizon_el_deg": None,
            "clearance_deg": None,
            "solar_disk_fraction": round(disk_fraction, 4),
            "provenance": "CALCULATED",
            "terrain_available": False,
        }

    horizon_el = interpolate_horizon_el(sun_az_deg, horizon_profile)
    clearance_deg = float(sun_el_deg) - horizon_el

    if include_solar_disk:
        r_sun = SOLAR_ANGULAR_RADIUS_DEG
        if clearance_deg <= -r_sun:
            disk_fraction = 0.0
        elif clearance_deg >= r_sun:
            disk_fraction = 1.0
        else:
            x = np.clip(-clearance_deg / r_sun, -1.0, 1.0)
            occulted = (np.arccos(x) - x * np.sqrt(max(0.0, 1.0 - x * x))) / np.pi
            disk_fraction = float(np.clip(1.0 - occulted, 0.0, 1.0))
        terrain_sunlit = bool(disk_fraction > 0.0)
    else:
        disk_fraction = 1.0 if clearance_deg > 0.0 else 0.0
        terrain_sunlit = bool(clearance_deg > 0.0)

    return {
        "geometric_sunlit": geometric_sunlit,
        "terrain_sunlit": terrain_sunlit,
        "sun_az_deg": round(float(sun_az_deg) % 360.0, 4),
        "sun_el_deg": round(float(sun_el_deg), 4),
        "horizon_el_deg": round(horizon_el, 4),
        "clearance_deg": round(clearance_deg, 4),
        "solar_disk_fraction": round(disk_fraction, 4),
        "provenance": "CALCULATED",
        "terrain_available": True,
    }


def summarize_illumination_series(
    times_utc: Sequence[str],
    sun_az_deg: Sequence[float],
    sun_el_deg: Sequence[float],
    horizon_profile: HorizonProfile | None = None,
    include_solar_disk: bool = True,
) -> dict:
    """Compute time-series sunlight state, duty cycles, and sunrise/sunset transitions."""
    n = len(times_utc)
    if n == 0 or len(sun_az_deg) != n or len(sun_el_deg) != n:
        raise IlluminationError("times_utc, sun_az_deg, and sun_el_deg must have matching non-zero length.")

    records = []
    events = []
    prev_lit: bool | None = None

    for t_str, az, el in zip(times_utc, sun_az_deg, sun_el_deg):
        step_res = evaluate_sunlight(
            sun_az_deg=float(az),
            sun_el_deg=float(el),
            horizon_profile=horizon_profile,
            include_solar_disk=include_solar_disk,
        )
        step_res["time_utc"] = str(t_str)
        records.append(step_res)

        curr_lit = step_res["terrain_sunlit"]
        if prev_lit is not None and curr_lit != prev_lit:
            events.append(
                {
                    "time_utc": str(t_str),
                    "event": "SUNRISE" if curr_lit else "SUNSET",
                    "sun_az_deg": step_res["sun_az_deg"],
                    "sun_el_deg": step_res["sun_el_deg"],
                    "horizon_el_deg": step_res["horizon_el_deg"],
                }
            )
        prev_lit = curr_lit

    geom_fraction = sum(1 for r in records if r["geometric_sunlit"]) / n
    terrain_fraction = (
        sum(1 for r in records if r["terrain_sunlit"]) / n
        if horizon_profile is not None
        else None
    )
    effective_fraction = sum(r["solar_disk_fraction"] for r in records) / n

    return {
        "sample_count": n,
        "geometric_sunlit_fraction": round(geom_fraction, 4),
        "terrain_sunlit_fraction": (
            None if terrain_fraction is None else round(terrain_fraction, 4)
        ),
        "effective_irradiance_fraction": round(effective_fraction, 4),
        "events": events,
        "series": records,
        "provenance": "CALCULATED",
        "terrain_available": horizon_profile is not None,
    }