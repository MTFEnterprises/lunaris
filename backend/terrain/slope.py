"""LUNARIS M3 - slope.py  (Feature F14: slope, roughness, elevation profile)

Contract for M1's routers (signature must not change):

    get_slope(lat: float, lon: float, radius_m: float) -> SlopeResult

RUNTIME vs OFFLINE (master guide, section 4.1)
----------------------------------------------
This module is RUNTIME code. It imports only the standard library and NumPy,
so it can run on the Vercel server. It does NOT open the big DEM GeoTIFF and
does not need rasterio or pyproj.

The DEM is turned into small tiles OFFLINE by scripts/terrain/make_dem_tiles.py
(which reuses terrain.py's DEM reading and coordinate logic and cross-checks the
tiles against terrain.elevation_at). The tiles live in data/dem_tiles/*.npz and
are committed (small). A point that no tile covers is UNAVAILABLE: we never
estimate terrain we do not have.

What is calculated (all class CALCULATED, all PRELIMINARY)
----------------------------------------------------------
slope_deg        Horn 3x3 slope at the DEM pixel that contains the point, at the
                 DEM's own resolution (no interpolation).
slope_max_deg /  Maximum / mean Horn slope over the pixels within radius_m.
slope_mean_deg
roughness_rms_m  RMS of the height residuals after removing the least-squares
                 plane, over the pixel centres within radius_m of the point.
elevation_m      Height of the pixel that contains the point.
profile          Heights along a great-circle line through the point, from
                 -radius_m to +radius_m, one sample per DEM pixel, nearest pixel.

Honesty rules
-------------
No data -> None fields + warnings (never an exception, never an estimate).
Slope of terrain smaller than the DEM pixel, lander-footprint-scale slope, and
rocks/boulders are NOT available from this DEM. Results are preliminary decision
support, not a certified landing safety assessment. LUNARIS is an independent
student prototype, not an official NASA product.

Conventions (docs/conventions.md): lat -90..90 (south negative), lon East-positive
-180..180, heights in metres from the Moon reference sphere (R = 1737.4 km),
azimuth 0 = North, 90 = East, clockwise.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

__all__ = ["get_slope", "SlopeResult", "Tile", "load_tiles", "clear_cache",
           "MAX_RADIUS_M"]

R_MOON_M = 1737400.0
MAX_RADIUS_M = 50_000.0           # performance guard on the analysis radius
MIN_FIT_PIXELS = 6                # numerical minimum for a plane fit + residual RMS
MAX_WINDOW_PIXELS = 4_000_000     # memory guard for the analysis window
_POLE_TOL_DEG = 1e-6              # azimuth is undefined this close to a pole
_METRE_NAMES = {"m", "meter", "metre", "meters", "metres"}

DATA_DIR_ENV = "LUNARIS_DATA_DIR"
TILE_SUBDIR = "dem_tiles"
DEM_META_FILE = "dem_meta.json"
PROJECTION_TYPE = "polar_stereographic_south"


# --------------------------------------------------------------------------- #
# Result type
# --------------------------------------------------------------------------- #
@dataclass
class SlopeResult:
    """Result of get_slope(). Use .to_dict() for JSON/API output.

    status:  "OK" | "PARTIAL" | "UNAVAILABLE"
    approx:  True whenever status is not "OK" (some value is missing or the
             analysis window was clipped / had gaps).
    """
    lat: float
    lon: float
    radius_m: float
    status: str
    approx: bool
    data_class: str                       # "CALCULATED" | "UNAVAILABLE"
    slope_deg: Optional[float] = None
    slope_max_deg: Optional[float] = None
    slope_mean_deg: Optional[float] = None
    roughness_rms_m: Optional[float] = None
    elevation_m: Optional[float] = None
    profile: Optional[dict] = None
    window: dict = field(default_factory=dict)
    dem: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["class"] = d.pop("data_class")
        return d


# --------------------------------------------------------------------------- #
# Projection (pure NumPy). Verified against pyproj OFFLINE by make_dem_tiles.py
# --------------------------------------------------------------------------- #
def project_south_polar(lat_deg, lon_deg, R: float, k0: float, lon0_deg: float):
    """lat/lon (degrees) -> projected (x, y) metres, south polar stereographic
    on a sphere of radius R with scale factor k0 at the pole."""
    phi = np.radians(np.asarray(lat_deg, dtype=np.float64))
    lam = np.radians(np.asarray(lon_deg, dtype=np.float64) - lon0_deg)
    rho = 2.0 * R * k0 * np.tan(np.pi / 4.0 + phi / 2.0)
    return rho * np.sin(lam), rho * np.cos(lam)


def unproject_south_polar(x_m, y_m, R: float, k0: float, lon0_deg: float):
    """Projected south-polar stereographic coordinates -> lat/lon degrees."""
    x = np.asarray(x_m, dtype=np.float64)
    y = np.asarray(y_m, dtype=np.float64)
    rho = np.hypot(x, y)
    phi = 2.0 * np.arctan2(rho, 2.0 * R * k0) - np.pi / 2.0
    lam = np.radians(lon0_deg) + np.arctan2(x, y)
    lat = np.degrees(phi)
    lon = (np.degrees(lam) + 180.0) % 360.0 - 180.0
    return lat, lon


def scale_factor_south_polar(lat_deg, k0: float):
    """Local map scale k (projected distance / ground distance)."""
    phi = np.radians(np.asarray(lat_deg, dtype=np.float64))
    return 2.0 * k0 / (1.0 - np.sin(phi))


def _destinations(lat_deg: float, lon_deg: float,
                  az_rad: np.ndarray, delta_rad: np.ndarray):
    """Great-circle destinations on a sphere (same maths as horizon.py).
    az_rad and delta_rad (= distance / R) are arrays of the same shape."""
    phi1, lam1 = math.radians(lat_deg), math.radians(lon_deg)
    sin_phi1, cos_phi1 = math.sin(phi1), math.cos(phi1)
    sin_d, cos_d = np.sin(delta_rad), np.cos(delta_rad)
    sin_phi2 = np.clip(sin_phi1 * cos_d + cos_phi1 * sin_d * np.cos(az_rad), -1.0, 1.0)
    phi2 = np.arcsin(sin_phi2)
    lam2 = lam1 + np.arctan2(np.sin(az_rad) * sin_d * cos_phi1,
                             cos_d - sin_phi1 * sin_phi2)
    return np.degrees(phi2), (np.degrees(lam2) + 180.0) % 360.0 - 180.0


# --------------------------------------------------------------------------- #
# DEM tiles (written offline, read here with NumPy only)
# --------------------------------------------------------------------------- #
class Tile:
    """One precomputed DEM crop: heights (NaN = no data) + grid + projection."""

    def __init__(self, path: Path, meta: dict):
        grid, proj = meta["grid"], meta["projection"]
        if proj.get("type") != PROJECTION_TYPE:
            raise ValueError(f"unsupported projection {proj.get('type')!r}")
        self.path = Path(path)
        self.meta = meta
        self.res_m = float(grid["res_m"])
        self.x_left = float(grid["x_left_m"])
        self.y_top = float(grid["y_top_m"])
        self.height = int(grid["height"])
        self.width = int(grid["width"])
        self.R = float(proj["R_m"])
        self.k0 = float(proj["k0"])
        self.lon0 = float(proj["lon0_deg"])
        self.dem = dict(meta.get("dem") or {})
        if not (math.isfinite(self.res_m) and self.res_m > 0):
            raise ValueError("tile resolution must be positive")
        self._z: Optional[np.ndarray] = None

    @property
    def z(self) -> np.ndarray:
        """Height grid (float32, NaN = no data); loaded on first use."""
        if self._z is None:
            with np.load(self.path) as f:
                z = np.asarray(f["z"], dtype=np.float32)
            if z.shape != (self.height, self.width):
                raise ValueError(f"tile array {z.shape} != grid "
                                 f"{(self.height, self.width)}")
            self._z = z
        return self._z

    def project(self, lat, lon):
        return project_south_polar(lat, lon, self.R, self.k0, self.lon0)

    def locate(self, lat: float, lon: float):
        """(row, col, x, y) of the pixel containing lat/lon; row/col may be
        outside the tile."""
        x, y = self.project(lat, lon)
        x, y = float(x), float(y)
        if not (math.isfinite(x) and math.isfinite(y)):
            return -1, -1, x, y
        col = math.floor((x - self.x_left) / self.res_m)
        row = math.floor((self.y_top - y) / self.res_m)
        return row, col, x, y

    def contains(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def elevation_at(self, lat: float, lon: float) -> Optional[float]:
        """Height of the pixel containing lat/lon, or None (outside / no data)."""
        row, col, _, _ = self.locate(lat, lon)
        if not self.contains(row, col):
            return None
        v = float(self.z[row, col])
        return v if math.isfinite(v) else None


_TILE_CACHE: dict[Path, tuple[list, list]] = {}


def clear_cache() -> None:
    _TILE_CACHE.clear()


def load_tiles(tile_dir: Union[str, Path]) -> tuple[list, list]:
    """Read the metadata of every *.npz tile in tile_dir (arrays load lazily).

    Returns (tiles, errors). A bad tile is skipped and reported in errors."""
    tile_dir = Path(tile_dir)
    key = tile_dir.resolve()
    if key in _TILE_CACHE:
        return _TILE_CACHE[key]
    tiles, errors = [], []
    if tile_dir.is_dir():
        for p in sorted(tile_dir.glob("*.npz")):
            try:
                with np.load(p) as f:
                    meta = json.loads(str(f["meta"]))
                tiles.append(Tile(p, meta))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(f"TILE_SKIPPED: {p.name}: {exc}")
    _TILE_CACHE[key] = (tiles, errors)
    return tiles, errors


def _select_tile(tiles: list, lat: float, lon: float):
    """Tile containing the point, preferring the one with the most margin."""
    best, best_margin = None, -1
    for t in tiles:
        row, col, _, _ = t.locate(lat, lon)
        if t.contains(row, col):
            margin = min(row, col, t.height - 1 - row, t.width - 1 - col)
            if margin > best_margin:
                best, best_margin = (t, row, col), margin
    return best if best else (None, -1, -1)


# --------------------------------------------------------------------------- #
# Maths on arrays
# --------------------------------------------------------------------------- #
def horn_slope_deg(ze: np.ndarray, ground_res_m: float) -> np.ndarray:
    """Horn (1981) 3x3 slope in degrees for the interior cells of ze.

    ze has shape (h+2, w+2); the result has shape (h, w). NaN wherever the cell
    or any of its 8 neighbours is NaN."""
    a, b, c = ze[:-2, :-2], ze[:-2, 1:-1], ze[:-2, 2:]
    d, e, f = ze[1:-1, :-2], ze[1:-1, 1:-1], ze[1:-1, 2:]
    g, h, i = ze[2:, :-2], ze[2:, 1:-1], ze[2:, 2:]
    dzdx = ((c + 2.0 * f + i) - (a + 2.0 * d + g)) / (8.0 * ground_res_m)
    dzdy = ((g + 2.0 * h + i) - (a + 2.0 * b + c)) / (8.0 * ground_res_m)
    out = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    out[~np.isfinite(e)] = np.nan
    return out


def plane_fit_rms(xs: np.ndarray, ys: np.ndarray, zs: np.ndarray) -> Optional[float]:
    """RMS of residuals of z after a least-squares plane fit; None if the fit
    is numerically impossible (too few or collinear points)."""
    if zs.size < MIN_FIT_PIXELS:
        return None
    A = np.column_stack([np.ones_like(xs), xs, ys])
    coef, _, rank, _ = np.linalg.lstsq(A, zs, rcond=None)
    if rank < 3:
        return None
    resid = zs - A @ coef
    return float(math.sqrt(float(np.mean(resid * resid))))


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _default_data_dir() -> Path:
    env = os.environ.get(DATA_DIR_ENV)
    return Path(env) if env else Path(__file__).resolve().parents[2] / "data"


def _validate(lat, lon, radius_m, az) -> tuple[float, float, float, float]:
    """Return clean floats or raise ValueError (M1 maps it to a 400 error)."""
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        raise ValueError(f"lat/lon must be numbers, got lat={lat!r}, lon={lon!r}")
    if not (math.isfinite(lat_f) and math.isfinite(lon_f)):
        raise ValueError("lat/lon must be finite numbers")
    if not -90.0 <= lat_f <= 90.0:
        raise ValueError(f"lat {lat_f} outside -90..90")
    if not -180.0 <= lon_f <= 180.0:
        raise ValueError(f"lon {lon_f} outside -180..180 (East-positive)")
    try:
        r = float(radius_m)
    except (TypeError, ValueError):
        raise ValueError(f"radius_m must be a number, got {radius_m!r}")
    if not (math.isfinite(r) and r > 0):
        raise ValueError("radius_m must be a positive finite number")
    if r > MAX_RADIUS_M:
        raise ValueError(f"radius_m {r} exceeds the maximum of {MAX_RADIUS_M:.0f} m")
    try:
        a = float(az)
    except (TypeError, ValueError):
        raise ValueError(f"profile_az_deg must be a number, got {az!r}")
    if not math.isfinite(a):
        raise ValueError("profile_az_deg must be finite")
    return lat_f, lon_f, r, a % 360.0


def _read_dem_meta(data_dir: Path, warnings: list) -> dict:
    path = data_dir / DEM_META_FILE
    try:
        with open(path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        if isinstance(meta, dict):
            return meta
    except (OSError, ValueError):
        pass
    warnings.append(f"DEM_META_MISSING: could not read {DEM_META_FILE}; "
                    "provenance falls back to the tile's own copy")
    return {}


def _dem_unverified_reasons(meta: dict) -> list:
    reasons = []
    status = meta.get("status")
    if status != "VERIFIED":
        reasons.append(f"status is {status!r}")
    units = str(meta.get("vertical_units") or "").strip().lower()
    if units not in _METRE_NAMES:
        reasons.append(f"vertical units are {meta.get('vertical_units')!r}")
    return reasons


def _dem_block(meta: dict, tile: Optional[Tile]) -> dict:
    td = tile.dem if tile else {}
    return {
        "name": str(meta.get("name") or td.get("name") or ""),
        "resolution_m": tile.res_m if tile else meta.get("resolution_m"),
        "coverage": str(meta.get("coverage") or td.get("coverage") or ""),
        "retrieved_utc": str(meta.get("retrieved_utc") or td.get("retrieved_utc") or ""),
    }


def _assumptions(tile: Optional[Tile], unverified: list) -> list:
    res = f"{tile.res_m:g} m" if tile else "the DEM resolution"
    items = [
        f"Slope: Horn 3x3 gradient at the DEM pixel containing the point, at the DEM "
        f"resolution ({res}); no interpolation. Ground pixel size = projected pixel "
        f"size divided by the local polar-stereographic scale factor.",
        "Slope statistics and roughness use one scale factor (the point's) for the "
        "whole analysis window.",
        "Roughness: RMS of height residuals after removing a least-squares plane, "
        "over pixel centres within radius_m of the point (window size and DEM "
        "resolution are reported).",
        "Profile: nearest-pixel heights along a great circle through the point, "
        "azimuth 0 = North, 90 = East, one sample per DEM pixel.",
        "Terrain smaller than one DEM pixel, lander-footprint-scale slope and "
        "rocks/boulders are not represented in this data.",
        "Preliminary decision support, not a certified landing safety assessment.",
    ]
    if unverified:
        items.append("DEM heights are assumed to be metres above the Moon reference "
                     "sphere; dem_meta.json is not yet verified (" + "; ".join(unverified) + ").")
    return items


def _provenance(cls: str, meta: dict, tile: Optional[Tile], unverified: list) -> dict:
    dem = _dem_block(meta, tile)
    td = tile.dem if tile else {}
    return {
        "class": cls,
        "inputs": [{
            "name": dem["name"],
            "version": str(meta.get("version") or td.get("version") or ""),
            "retrieved_utc": dem["retrieved_utc"],
        }],
        "assumptions": _assumptions(tile, unverified),
    }


def _r(value, ndigits: int):
    """Round for presentation (not more decimals than the DEM supports)."""
    if value is None:
        return None
    v = float(value)
    return round(v, ndigits) + 0.0 if math.isfinite(v) else None


def _unavailable(base: dict, meta: dict, tile: Optional[Tile],
                 warnings: list, unverified: list) -> SlopeResult:
    return SlopeResult(
        **base, status="UNAVAILABLE", approx=True, data_class="UNAVAILABLE",
        dem=_dem_block(meta, tile), warnings=warnings,
        provenance=_provenance("UNAVAILABLE", meta, tile, unverified),
    )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_slope(lat: float, lon: float, radius_m: float, *,
              profile_az_deg: float = 0.0,
              data_dir: Optional[Union[str, Path]] = None) -> SlopeResult:
    """Slope, roughness and an elevation profile around (lat, lon).

    Parameters
    ----------
    lat, lon         Point (degrees; south negative, East-positive).
    radius_m         Analysis radius for roughness / slope statistics, and half
                     the length of the profile. 0 < radius_m <= 50 000.
    profile_az_deg   (optional) profile azimuth, 0 = North, clockwise.
    data_dir         (optional) override for the data/ folder
                     (env LUNARIS_DATA_DIR also works).

    Returns a SlopeResult. Missing data gives None fields, status
    "UNAVAILABLE"/"PARTIAL", approx=True and explanatory warnings; nothing is
    estimated. Raises ValueError only for invalid input arguments.
    """
    lat, lon, radius_m, az_deg = _validate(lat, lon, radius_m, profile_az_deg)
    base = {"lat": lat, "lon": lon, "radius_m": radius_m}
    ddir = Path(data_dir) if data_dir is not None else _default_data_dir()

    warnings: list = []
    meta = _read_dem_meta(ddir, warnings)
    unverified = _dem_unverified_reasons(meta) if meta else []
    if not meta:
        warnings.append(
            "DEM_META_MISSING: terrain values are unavailable until "
            "dem_meta.json is present and verified."
        )
    if unverified:
        warnings.append("DEM_UNVERIFIED: dem_meta.json is not verified ("
                        + "; ".join(unverified) + "); results assume DEM heights "
                        "are metres.")
    if meta and not meta.get("retrieved_utc"):
        warnings.append("DEM_META_INCOMPLETE: retrieved_utc is missing in dem_meta.json.")

    tiles, errors = load_tiles(ddir / TILE_SUBDIR)
    warnings.extend(errors)
    if not tiles:
        warnings.append(f"NO_DEM_TILES: no usable tiles in {TILE_SUBDIR}/; run "
                        "scripts/terrain/make_dem_tiles.py offline.")
        return _unavailable(base, meta, None, warnings, unverified)

    if not meta or unverified:
        return _unavailable(base, meta, None, warnings, unverified)

    tile, row, col = _select_tile(tiles, lat, lon)
    if tile is None:
        warnings.append("OUTSIDE_TILES: no precomputed DEM tile covers this point; "
                        "slope and roughness are only available near curated sites.")
        return _unavailable(base, meta, None, warnings, unverified)

    try:
        z = tile.z
    except (OSError, ValueError, KeyError) as exc:
        warnings.append(f"TILE_UNREADABLE: {tile.path.name}: {exc}")
        return _unavailable(base, meta, tile, warnings, unverified)

    res = tile.res_m
    k = float(scale_factor_south_polar(lat, tile.k0))
    ground_res = res / k
    rp = int(math.ceil(radius_m * k / res))
    if (2 * rp + 3) ** 2 > MAX_WINDOW_PIXELS:
        warnings.append("WINDOW_TOO_LARGE: radius_m is too large for this DEM "
                        "resolution; use a smaller radius.")
        return _unavailable(base, meta, tile, warnings, unverified)

    # ---- analysis window: extended by one pixel for the Horn neighbours -----
    rows = np.arange(row - rp - 1, row + rp + 2)
    cols = np.arange(col - rp - 1, col + rp + 2)
    r_ok = (rows >= 0) & (rows < tile.height)
    c_ok = (cols >= 0) & (cols < tile.width)
    ze = np.full((rows.size, cols.size), np.nan)
    ze[np.ix_(np.flatnonzero(r_ok), np.flatnonzero(c_ok))] = \
        z[np.ix_(rows[r_ok], cols[c_ok])]

    _, _, xp, yp = tile.locate(lat, lon)
    xc = tile.x_left + (cols[1:-1] + 0.5) * res          # pixel-centre x (inner)
    yc = tile.y_top - (rows[1:-1] + 0.5) * res           # pixel-centre y (inner)
    dx, dy = np.broadcast_arrays(xc[None, :] - xp, yc[:, None] - yp)
    disc = np.hypot(dx, dy) <= radius_m * k

    inner = ze[1:-1, 1:-1]
    inside_tile = np.outer(r_ok[1:-1], c_ok[1:-1])
    n_total = int(disc.sum())
    n_in_tile = int((disc & inside_tile).sum())
    valid = disc & np.isfinite(inner)
    n_valid = int(valid.sum())
    clipped = n_in_tile < n_total
    window = {
        "radius_m": radius_m,
        "pixels_in_window": n_total,
        "pixels_valid": n_valid,
        "valid_fraction": _r(n_valid / n_total, 3) if n_total else None,
        "clipped_by_tile": bool(clipped),
        "dem_resolution_m": res,
    }

    # ---- slope ----------------------------------------------------------------
    sgrid = horn_slope_deg(ze, ground_res)
    slope_pt = float(sgrid[rp, rp])
    slope_pt = slope_pt if math.isfinite(slope_pt) else None
    s_win = sgrid[disc & np.isfinite(sgrid)]
    slope_max = float(s_win.max()) if s_win.size else None
    slope_mean = float(s_win.mean()) if s_win.size else None
    if slope_pt is None:
        warnings.append("SLOPE_UNAVAILABLE: the point's 3x3 neighbourhood has "
                        "no data or leaves the tile.")

    # ---- elevation + roughness ---------------------------------------------
    elev = float(inner[rp, rp])
    elev = elev if math.isfinite(elev) else None

    rough = plane_fit_rms(dx[valid] / k, dy[valid] / k, inner[valid]) \
        if n_valid >= MIN_FIT_PIXELS else None
    if rough is None:
        warnings.append(f"ROUGHNESS_UNAVAILABLE: fewer than {MIN_FIT_PIXELS} valid "
                        "pixels in the window (radius too small for the DEM "
                        "resolution, or no data).")
    if clipped:
        warnings.append("WINDOW_CLIPPED: the analysis radius extends beyond the "
                        "DEM tile; statistics use only the pixels inside it.")
    if n_total and n_valid < n_in_tile:
        warnings.append("WINDOW_GAPS: some pixels in the window have no data and "
                        "were left out.")

    # ---- profile ------------------------------------------------------------
    profile = None
    if abs(lat) >= 90.0 - _POLE_TOL_DEG:
        warnings.append("PROFILE_UNAVAILABLE: azimuth is undefined at a pole.")
    else:
        n = int(math.floor(radius_m / ground_res))
        if n < 1:
            warnings.append("PROFILE_UNAVAILABLE: radius_m is shorter than one "
                            "DEM pixel.")
        else:
            d = ground_res * np.arange(-n, n + 1, dtype=np.float64)
            az = np.where(d >= 0, az_deg, az_deg + 180.0)
            lat2, lon2 = _destinations(lat, lon, np.radians(az),
                                       np.abs(d) / R_MOON_M)
            px, py = tile.project(lat2, lon2)
            cf = np.floor((px - tile.x_left) / res)
            rf = np.floor((tile.y_top - py) / res)
            ok = (np.isfinite(cf) & np.isfinite(rf) & (cf >= 0) & (cf < tile.width)
                  & (rf >= 0) & (rf < tile.height))
            heights = np.full(d.shape, np.nan)
            heights[ok] = z[rf[ok].astype(int), cf[ok].astype(int)]
            if np.isfinite(heights).any():
                profile = {
                    "az_deg": _r(az_deg, 1),
                    "step_m": _r(ground_res, 1),
                    "sampling": "nearest_pixel",
                    "distance_m": [_r(v, 1) for v in d],
                    "elevation_m": [_r(v, 1) for v in heights],
                }
                if not np.isfinite(heights).all():
                    warnings.append("PROFILE_GAPS: parts of the profile are "
                                    "outside the tile or have no data (null).")
            else:
                warnings.append("PROFILE_UNAVAILABLE: no DEM data along the profile.")

    # ---- assemble -----------------------------------------------------------
    computed = [slope_pt, slope_max, rough, elev]
    any_value = any(v is not None for v in computed) or profile is not None
    complete = (slope_pt is not None and rough is not None and elev is not None
                and profile is not None and not clipped
                and n_valid == n_total
                and all(v is not None for v in profile["elevation_m"]))
    if not any_value:
        return _unavailable(base, meta, tile, warnings, unverified)
    status = "OK" if complete else "PARTIAL"
    return SlopeResult(
        **base,
        status=status,
        approx=status != "OK",
        data_class="CALCULATED",
        slope_deg=_r(slope_pt, 1),
        slope_max_deg=_r(slope_max, 1),
        slope_mean_deg=_r(slope_mean, 1),
        roughness_rms_m=_r(rough, 2),
        elevation_m=_r(elev, 1),
        profile=profile,
        window=window,
        dem=_dem_block(meta, tile),
        warnings=warnings,
        provenance=_provenance("CALCULATED", meta, tile, unverified),
    )