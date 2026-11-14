
"""LUNARIS M3 - horizon.py

360-degree terrain horizon mask ("skyline") for an observer on the Moon,
computed by ray casting over a LOLA DEM GeoTIFF.

Method (one ray per whole-degree azimuth, 0 = North, 90 = East, clockwise):
  1. For each distance d = step, 2*step, ... up to max_km,
     find the great-circle destination point on a sphere of radius R_MOON.
  2. Project that point into the DEM's own CRS and sample the containing pixel.
  3. Calculate elevation angle with lunar curvature correction.
  4. The horizon at each azimuth is the maximum angle along the ray.

LUNARIS is an independent student prototype, not an official NASA product,
and results are not flight-certified.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

# Optional geospatial dependencies.
# The module can be imported when only NumPy is installed.
try:
    import rasterio
    from pyproj import CRS, Transformer
    from rasterio.errors import RasterioError
    from rasterio.windows import Window

    GEOSPATIAL_AVAILABLE = True

except ImportError:
    rasterio = None
    CRS = None
    Transformer = None
    RasterioError = Exception
    Window = None

    GEOSPATIAL_AVAILABLE = False


__all__ = ["horizon_at", "R_MOON_M"]

R_MOON_M = 1737400.0
DEFAULT_MAX_KM = 150.0
N_AZ = 360
MAX_WINDOW_PIXELS = 100_000_000
_CHUNK_ELEMENTS = 2_000_000
_POLE_TOL_DEG = 1e-6
_METRE_NAMES = {"m", "meter", "metre", "meters", "metres"}

DEM_PATH_ENV = "LUNARIS_DEM_PATH"
DEM_META_ENV = "LUNARIS_DEM_META"


# --------------------------------------------------------------------------- #
# Result helpers
# --------------------------------------------------------------------------- #

def _dem_info(
    name: str = "",
    resolution_m=None,
    coverage: str = "",
    retrieved_utc: str = ""
) -> dict:
    return {
        "name": name,
        "resolution_m": resolution_m,
        "coverage": coverage,
        "retrieved_utc": retrieved_utc,
    }


def _observer(lat, lon, height_m, source) -> dict:
    return {
        "lat": lat,
        "lon": lon,
        "height_m": height_m,
        "height_source": source,
    }


def _unavailable(
    status: str,
    dem: dict,
    lat: float,
    lon: float,
    height_m=None
) -> dict:
    return {
        "deg": None,
        "dem": dem,
        "approx": True,
        "class": "UNAVAILABLE",
        "status": status,
        "observer": _observer(lat, lon, height_m, None),
    }


def _validate_inputs(
    lat,
    lon,
    height_m,
    max_km
) -> tuple[float, float, Optional[float], float]:
    """Return cleaned floats or raise ValueError."""

    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        raise ValueError(
            f"lat/lon must be numbers, got lat={lat!r}, lon={lon!r}"
        )

    if not (math.isfinite(lat_f) and math.isfinite(lon_f)):
        raise ValueError("lat/lon must be finite numbers")

    if not -90.0 <= lat_f <= 90.0:
        raise ValueError(f"lat {lat_f} outside -90..90")

    if not -180.0 <= lon_f <= 180.0:
        raise ValueError(
            f"lon {lon_f} outside -180..180 (East-positive)"
        )

    h = None

    if height_m is not None:
        try:
            h = float(height_m)
        except (TypeError, ValueError):
            raise ValueError(
                f"height_m must be a number or None, got {height_m!r}"
            )

        if not math.isfinite(h):
            raise ValueError("height_m must be finite")

    try:
        km = float(max_km)
    except (TypeError, ValueError):
        raise ValueError(f"max_km must be a number, got {max_km!r}")

    if not (math.isfinite(km) and km > 0):
        raise ValueError("max_km must be a positive finite number")

    return lat_f, lon_f, h, km


def _load_meta(meta_path: Optional[Union[str, Path]]) -> dict:
    """Optional data/dem_meta.json. Only used for labels."""

    path = meta_path or os.environ.get(DEM_META_ENV)

    if not path:
        return {}

    try:
        with open(path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)

        return meta if isinstance(meta, dict) else {}

    except (OSError, ValueError):
        return {}


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #

def _resolution_m(src, crs: CRS) -> Optional[float]:
    """Pixel size in metres for a projected DEM, else None."""

    if crs.is_geographic or not crs.axis_info:
        return None

    factor = crs.axis_info[0].unit_conversion_factor or 1.0

    px = abs(src.transform.a) * factor
    py = abs(src.transform.e) * factor

    return float((px + py) / 2.0)


def _destinations(
    lat_deg: float,
    lon_deg: float,
    az_rad: np.ndarray,
    delta_rad: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Great-circle destination points on a sphere."""

    phi1 = math.radians(lat_deg)
    lam1 = math.radians(lon_deg)

    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)

    sin_d = np.sin(delta_rad)
    cos_d = np.cos(delta_rad)

    sin_phi2 = (
        sin_phi1 * cos_d
        + cos_phi1 * sin_d * np.cos(az_rad)
    )

    sin_phi2 = np.clip(sin_phi2, -1.0, 1.0)

    phi2 = np.arcsin(sin_phi2)

    lam2 = lam1 + np.arctan2(
        np.sin(az_rad) * sin_d * cos_phi1,
        cos_d - sin_phi1 * sin_phi2
    )

    lon2 = (np.degrees(lam2) + 180.0) % 360.0 - 180.0

    return np.degrees(phi2), lon2


def _to_rowcol(
    transformer: Transformer,
    inv_affine,
    shape: tuple[int, int],
    lon: np.ndarray,
    lat: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Convert longitude/latitude to containing DEM pixel indices."""

    out_shape = lon.shape

    x, y = transformer.transform(
        np.ascontiguousarray(lon.ravel(), dtype=np.float64),
        np.ascontiguousarray(lat.ravel(), dtype=np.float64)
    )

    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    finite = np.isfinite(x) & np.isfinite(y)

    x = np.where(finite, x, 0.0)
    y = np.where(finite, y, 0.0)

    col_f = (
        inv_affine.a * x
        + inv_affine.b * y
        + inv_affine.c
    )

    row_f = (
        inv_affine.d * x
        + inv_affine.e * y
        + inv_affine.f
    )

    inside = (
        finite
        & (col_f >= 0)
        & (col_f < shape[1])
        & (row_f >= 0)
        & (row_f < shape[0])
    )

    rows = np.where(
        inside,
        np.floor(row_f),
        -1
    ).astype(np.int64)

    cols = np.where(
        inside,
        np.floor(col_f),
        -1
    ).astype(np.int64)

    return rows.reshape(out_shape), cols.reshape(out_shape)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def horizon_at(
    lat: float,
    lon: float,
    height_m: Optional[float] = None,
    dem_path: Optional[Union[str, Path]] = None,
    max_km: float = DEFAULT_MAX_KM,
    dem_meta_path: Optional[Union[str, Path]] = None
) -> dict:
    """Compute the 360-value terrain horizon for an observer."""

    lat, lon, height_m, max_km = _validate_inputs(
        lat, lon, height_m, max_km
    )

    # Return a clear result if optional dependencies are unavailable.
    if not GEOSPATIAL_AVAILABLE:
        return _unavailable(
            "GEOSPATIAL_DEPENDENCIES_MISSING: "
            "rasterio and pyproj are required for horizon calculations",
            _dem_info(),
            lat,
            lon,
            height_m
        )

    path = dem_path or os.environ.get(DEM_PATH_ENV)

    if not path:
        return _unavailable(
            f"DEM_NOT_CONFIGURED: pass dem_path or set {DEM_PATH_ENV}",
            _dem_info(),
            lat,
            lon,
            height_m
        )

    meta = _load_meta(dem_meta_path)

    dem = _dem_info(
        name=str(meta.get("name") or Path(str(path)).name),
        coverage=str(meta.get("coverage") or ""),
        retrieved_utc=str(meta.get("retrieved_utc") or ""),
    )

    if abs(lat) >= 90.0 - _POLE_TOL_DEG:
        return _unavailable(
            "AZIMUTH_UNDEFINED_AT_POLE: use a point slightly off the pole",
            dem,
            lat,
            lon,
            height_m
        )

    try:
        with rasterio.open(path) as src:
            return _compute(
                src, lat, lon, height_m, max_km, dem
            )

    except RasterioError as exc:
        return _unavailable(
            f"DEM_UNREADABLE: {exc}",
            dem,
            lat,
            lon,
            height_m
        )


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #

def _compute(
    src: rasterio.DatasetReader,
    lat: float,
    lon: float,
    height_m: Optional[float],
    max_km: float,
    dem: dict
) -> dict:

    if src.crs is None:
        return _unavailable(
            "NO_CRS: DEM file has no coordinate system",
            dem, lat, lon, height_m
        )

    dem_crs = CRS.from_user_input(src.crs.to_wkt())

    if dem_crs.is_geographic:
        return _unavailable(
            "UNSUPPORTED_CRS: geographic (degree) DEM; "
            "use a projected polar DEM",
            dem, lat, lon, height_m
        )

    res_m = _resolution_m(src, dem_crs)
    dem["resolution_m"] = res_m

    if not res_m or res_m <= 0:
        return _unavailable(
            "NO_RESOLUTION: cannot determine DEM pixel size",
            dem, lat, lon, height_m
        )

    if not dem["coverage"]:
        b = src.bounds

        dem["coverage"] = (
            f"DEM CRS extent: left={b.left:.1f}, "
            f"bottom={b.bottom:.1f}, "
            f"right={b.right:.1f}, "
            f"top={b.top:.1f} "
            "(linear units of the DEM CRS)"
        )

    unit = src.units[0] if src.units else None

    if (
        unit is not None
        and str(unit).strip().lower() not in _METRE_NAMES
    ):
        return _unavailable(
            f"UNITS: band units are '{unit}', expected metres",
            dem, lat, lon, height_m
        )

    max_m = max_km * 1000.0
    step_m = res_m

    n_steps = int(math.floor(max_m / step_m))

    if n_steps < 1:
        return _unavailable(
            "MAX_DISTANCE_TOO_SHORT: shorter than one DEM pixel",
            dem, lat, lon, height_m
        )

    transformer = Transformer.from_crs(
        dem_crs.geodetic_crs,
        dem_crs,
        always_xy=True
    )

    inv = ~src.transform
    shape = (src.height, src.width)

    # Observer pixel.
    o_row, o_col = _to_rowcol(
        transformer,
        inv,
        shape,
        np.array([lon]),
        np.array([lat])
    )

    o_row = int(o_row[0])
    o_col = int(o_col[0])

    if o_row < 0:
        return _unavailable(
            "OUT_OF_BOUNDS: observer is outside DEM coverage",
            dem, lat, lon, height_m
        )

    dist = step_m * np.arange(
        1, n_steps + 1, dtype=np.float64
    )

    delta = dist / R_MOON_M

    az_all = np.radians(
        np.arange(N_AZ, dtype=np.float64)
    )

    # Pass 1: calculate pixel indices for every sample.
    rows = np.empty(
        (N_AZ, n_steps),
        dtype=np.int32
    )

    cols = np.empty(
        (N_AZ, n_steps),
        dtype=np.int32
    )

    chunk_az = max(1, _CHUNK_ELEMENTS // n_steps)

    for a0 in range(0, N_AZ, chunk_az):
        a1 = min(N_AZ, a0 + chunk_az)

        lat2, lon2 = _destinations(
            lat,
            lon,
            az_all[a0:a1, None],
            delta[None, :]
        )

        r, c = _to_rowcol(
            transformer,
            inv,
            shape,
            lon2,
            lat2
        )

        rows[a0:a1] = r
        cols[a0:a1] = c

    valid_idx = rows >= 0

    if valid_idx.any():
        r_min = min(int(rows[valid_idx].min()), o_row)
        r_max = max(int(rows[valid_idx].max()), o_row)
        c_min = min(int(cols[valid_idx].min()), o_col)
        c_max = max(int(cols[valid_idx].max()), o_col)
    else:
        r_min = r_max = o_row
        c_min = c_max = o_col

    win_h = r_max - r_min + 1
    win_w = c_max - c_min + 1

    if win_h * win_w > MAX_WINDOW_PIXELS:
        return _unavailable(
            f"DEM_WINDOW_TOO_LARGE: {win_h}x{win_w} px needed; "
            "use a coarser or cropped DEM",
            dem, lat, lon, height_m
        )

    # Read one window. Masked pixels become NaN.
    data = src.read(
        1,
        window=Window(c_min, r_min, win_w, win_h),
        masked=True
    )

    arr = data.astype(np.float32).filled(np.nan)

    scale = src.scales[0] if src.scales else 1.0
    offset = src.offsets[0] if src.offsets else 0.0

    if scale != 1.0 or offset != 0.0:
        arr = arr * np.float32(scale) + np.float32(offset)

    arr[~np.isfinite(arr)] = np.nan

    # Observer height.
    if height_m is None:
        z0 = float(
            arr[o_row - r_min, o_col - c_min]
        )

        if not math.isfinite(z0):
            return _unavailable(
                "NODATA_AT_OBSERVER: DEM has no data at the observer; "
                "pass height_m explicitly",
                dem, lat, lon, None
            )

        height_source = "DEM"

    else:
        z0 = float(height_m)
        height_source = "USER"

    # Pass 2: heights -> elevation angles -> maximum per azimuth.
    best = np.full(N_AZ, -np.inf)
    n_valid = np.zeros(N_AZ, dtype=np.int64)

    drop = dist * dist / (2.0 * R_MOON_M)

    for a0 in range(0, N_AZ, chunk_az):
        a1 = min(N_AZ, a0 + chunk_az)

        rr = rows[a0:a1]
        cc = cols[a0:a1]

        ok = rr >= 0

        z = np.full(rr.shape, np.nan)

        z[ok] = arr[
            rr[ok] - r_min,
            cc[ok] - c_min
        ]

        ang = np.degrees(
            np.arctan2(
                (z - z0) - drop[None, :],
                dist[None, :]
            )
        )

        good = np.isfinite(ang)

        n_valid[a0:a1] = good.sum(axis=1)

        best[a0:a1] = np.where(
            good,
            ang,
            -np.inf
        ).max(axis=1)

    if not (n_valid > 0).any():
        return _unavailable(
            "NODATA: no valid DEM samples along any azimuth",
            dem, lat, lon, z0
        )

    gaps = int((n_valid < n_steps).sum())
    approx = gaps > 0

    deg: list[Optional[float]] = []

    for k in range(N_AZ):
        if n_valid[k] < n_steps:
            deg.append(None)
        else:
            deg.append(
                float(np.round(best[k], 2)) + 0.0
            )

    return {
        "deg": deg,
        "dem": dem,
        "approx": approx,
        "class": "CALCULATED",
        "status": (
            "OK" if not approx else
            f"PARTIAL_COVERAGE: {gaps} of {N_AZ} azimuths lost samples "
            "(NaN/no-data/outside DEM); those horizons may be underestimated"
        ),
        "observer": _observer(
            lat,
            lon,
            round(z0, 2),
            height_source
        ),
        "method": {
            "sampling": "nearest_pixel (no interpolation)",
            "step_m": step_m,
            "max_distance_m": float(dist[-1]),
            "curvature": "d^2/(2R)",
            "R_moon_m": R_MOON_M,
            "azimuth_step_deg": 1,
            "azimuth_convention": "0=North, 90=East, clockwise",
        },
        "quality": {
            "azimuths_with_gaps": gaps,
            "valid_sample_fraction": round(
                float(n_valid.sum()) / (N_AZ * n_steps),
                4
            ),
        },
    }


# --------------------------------------------------------------------------- #
# Command line
# --------------------------------------------------------------------------- #

def _main() -> None:
    p = argparse.ArgumentParser(
        description="LUNARIS horizon mask for one point"
    )

    p.add_argument("--dem", required=False, help="DEM GeoTIFF path")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument(
        "--height",
        type=float,
        default=None,
        help="observer height (m)"
    )
    p.add_argument(
        "--max-km",
        type=float,
        default=DEFAULT_MAX_KM
    )
    p.add_argument(
        "--meta",
        default=None,
        help="optional dem_meta.json"
    )

    args = p.parse_args()

    res = horizon_at(
        args.lat,
        args.lon,
        args.height,
        dem_path=args.dem,
        max_km=args.max_km,
        dem_meta_path=args.meta
    )

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    _main()
