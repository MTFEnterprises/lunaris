
"""LUNARIS M3 - hazard.py
Feature F15: Preliminary Landing Safety Assessment.

Uses the existing F14 slope.get_slope function to evaluate candidate
landing-zone centres around a lunar site.

Classes:
    PASS     Complete terrain data, verified DEM, both limits satisfied.
    FAIL     Complete terrain data, verified DEM, at least one limit exceeded.
    UNKNOWN  Missing, partial, incomplete, or unverified information.

Missing information is NEVER replaced with zero.
No universal safety thresholds are built in.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import numbers
import re
import sys
from pathlib import Path
from typing import Any, Optional, Union


__all__ = [
    "evaluate_site",
    "evaluate",
    "get_hazard",
    "write_suitability_png",
    "classify_cell",
    "SAFETY_STATEMENT",
    "PASS",
    "FAIL",
    "UNKNOWN",
]

SAFETY_STATEMENT = (
    "Preliminary decision support, not a certified landing safety assessment."
)

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"

R_MOON_M = 1737400.0
MAX_CELLS = 2500
DEFAULT_HALF_EXTENT_CELLS = 5
_POLE_TOL_DEG = 1e-6

# All these warnings prevent a normal PASS or FAIL classification.
_DEM_BLOCKING_CODES = {
    "DEM_UNVERIFIED",
    "DEM_META_MISSING",
    "DEM_META_INCOMPLETE",
}

_COLOURS = {
    PASS: "#2e9e4f",
    FAIL: "#d64541",
    UNKNOWN: "#9aa0a6",
}


# ---------------------------------------------------------------------
# Import existing F14 slope module
# ---------------------------------------------------------------------

def _import_slope():
    try:
        from . import slope as mod
        return mod
    except ImportError:
        pass

    name = "lunaris_m3_slope"

    if name in sys.modules:
        return sys.modules[name]

    slope_path = Path(__file__).resolve().parent / "slope.py"

    spec = importlib.util.spec_from_file_location(name, slope_path)

    if spec is None or spec.loader is None:
        raise ImportError("Could not load backend/terrain/slope.py")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)

    return mod


_slope = _import_slope()

# Tests can replace this function with a mock.
get_slope = _slope.get_slope


# ---------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------

def _num(
    name: str,
    value: Any,
    lo: Optional[float] = None,
    hi: Optional[float] = None,
    lo_open: bool = False,
) -> float:
    """Validate a finite numeric value."""

    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"{name} must be a number, got {value!r}")

    v = float(value)

    if not math.isfinite(v):
        raise ValueError(f"{name} must be finite")

    if lo is not None and (v <= lo if lo_open else v < lo):
        operator = ">" if lo_open else ">="
        raise ValueError(f"{name} must be {operator} {lo}, got {v}")

    if hi is not None and v > hi:
        raise ValueError(f"{name} must be <= {hi}, got {v}")

    return v


def _is_number(value) -> bool:
    return (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


# ---------------------------------------------------------------------
# Local east/north offset to lunar latitude/longitude
# ---------------------------------------------------------------------

def _offset_to_latlon(lat, lon, east_m, north_m):
    """Move from a site centre using a great-circle calculation."""

    distance = math.hypot(east_m, north_m)

    if distance == 0.0:
        return lat, lon

    bearing = math.atan2(east_m, north_m)
    delta = distance / R_MOON_M

    phi1 = math.radians(lat)
    lam1 = math.radians(lon)

    sin_phi2 = (
        math.sin(phi1) * math.cos(delta)
        + math.cos(phi1) * math.sin(delta) * math.cos(bearing)
    )

    sin_phi2 = max(-1.0, min(1.0, sin_phi2))

    phi2 = math.asin(sin_phi2)

    lam2 = lam1 + math.atan2(
        math.sin(bearing) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * sin_phi2,
    )

    new_lat = math.degrees(phi2)

    new_lon = (math.degrees(lam2) + 180.0) % 360.0 - 180.0

    return new_lat, new_lon


# ---------------------------------------------------------------------
# Warning and reason helpers
# ---------------------------------------------------------------------

def _codes(warnings) -> list:
    """Extract warning codes from F14 warning messages."""

    return [
        str(w).split(":", 1)[0].strip()
        for w in (warnings or [])
    ]


def _reason(code: str, message: str) -> dict:
    return {
        "code": code,
        "message": message,
    }


# ---------------------------------------------------------------------
# Classification of one candidate cell
# ---------------------------------------------------------------------

def classify_cell(
    result,
    max_slope_deg: float,
    max_roughness_m: float,
    min_radius_m: float,
    allow_unverified_dem: bool = False,
) -> tuple:
    """
    Classify one F14 SlopeResult.

    Returns:
        (PASS, [])
        (FAIL, [reasons])
        (UNKNOWN, [reasons])
    """

    unknown = []

    status = getattr(result, "status", None)

    codes = _codes(
        getattr(result, "warnings", [])
    )

    # 1. Check terrain status.

    if status == "UNAVAILABLE":
        unknown.append(
            _reason(
                "TERRAIN_UNAVAILABLE",
                "No terrain data is available for this cell.",
            )
        )

    elif status == "PARTIAL":
        unknown.append(
            _reason(
                "TERRAIN_PARTIAL",
                "Terrain data is incomplete for this cell.",
            )
        )

    elif status != "OK":
        unknown.append(
            _reason(
                "TERRAIN_STATUS_UNRECOGNISED",
                f"Unexpected terrain status {status!r}.",
            )
        )

    elif getattr(result, "approx", True):
        unknown.append(
            _reason(
                "TERRAIN_APPROXIMATE",
                "Terrain result is flagged approximate.",
            )
        )

    # 2. Check landing-zone radius.

    got_radius = getattr(result, "radius_m", None)

    if (
        not _is_number(got_radius)
        or abs(float(got_radius) - min_radius_m) > 1e-6
    ):
        unknown.append(
            _reason(
                "RADIUS_MISMATCH",
                f"Terrain radius {got_radius!r} does not match "
                f"requested radius {min_radius_m:g} m.",
            )
        )

    window = getattr(result, "window", None) or {}

    if not isinstance(window, dict):
        window = {}

    valid_fraction = window.get("valid_fraction")

    if (
        window.get("clipped_by_tile")
        or (
            valid_fraction is not None
            and (
                not _is_number(valid_fraction)
                or float(valid_fraction) < 1.0
            )
        )
    ):
        unknown.append(
            _reason(
                "RADIUS_NOT_FULLY_EVALUATED",
                "The complete landing-zone radius is not covered "
                "by valid DEM data.",
            )
        )

    # 3. Check DEM verification.

    if (
        not allow_unverified_dem
        and any(code in _DEM_BLOCKING_CODES for code in codes)
    ):
        unknown.append(
            _reason(
                "DEM_UNVERIFIED",
                "DEM metadata or vertical units are not verified "
                "or are incomplete.",
            )
        )

    # 4. Check required measurements.

    slope_value = getattr(result, "slope_max_deg", None)

    roughness_value = getattr(
        result,
        "roughness_rms_m",
        None,
    )

    if slope_value is None:
        unknown.append(
            _reason(
                "SLOPE_MISSING",
                "Maximum slope is not available.",
            )
        )

    elif not _is_number(slope_value) or float(slope_value) < 0:
        unknown.append(
            _reason(
                "SLOPE_INVALID",
                "Maximum slope is not a valid number.",
            )
        )

    if roughness_value is None:
        unknown.append(
            _reason(
                "ROUGHNESS_MISSING",
                "Surface roughness is not available.",
            )
        )

    elif (
        not _is_number(roughness_value)
        or float(roughness_value) < 0
    ):
        unknown.append(
            _reason(
                "ROUGHNESS_INVALID",
                "Surface roughness is not a valid number.",
            )
        )

    # Uncertain information always produces UNKNOWN.

    if unknown:
        return UNKNOWN, unknown

    # 5. Compare complete measurements with supplied limits.

    failures = []

    if float(slope_value) > max_slope_deg:
        failures.append(
            _reason(
                "SLOPE_EXCEEDS_LIMIT",
                f"Maximum slope {float(slope_value):g} deg "
                f"exceeds limit {max_slope_deg:g} deg.",
            )
        )

    if float(roughness_value) > max_roughness_m:
        failures.append(
            _reason(
                "ROUGHNESS_EXCEEDS_LIMIT",
                f"Roughness {float(roughness_value):g} m "
                f"exceeds limit {max_roughness_m:g} m.",
            )
        )

    if failures:
        return FAIL, failures

    return PASS, []


# ---------------------------------------------------------------------
# Build class matrix
# ---------------------------------------------------------------------

def _class_matrix_from_cells(cells: list, n: int) -> list:
    """Build a north-up class grid from the cell results."""

    grid = [
        [UNKNOWN] * n
        for _ in range(n)
    ]

    for cell in cells:
        grid[cell["j"]][cell["i"]] = cell["class"]

    return grid


# ---------------------------------------------------------------------
# Main site assessment
# ---------------------------------------------------------------------

def evaluate_site(
    lat: float,
    lon: float,
    *,
    max_slope_deg: float,
    max_roughness_m: float,
    min_radius_m: float,
    cell_size_m: Optional[float] = None,
    half_extent_m: Optional[float] = None,
    allow_unverified_dem: bool = False,
    data_dir: Optional[Union[str, Path]] = None,
    png_path: Optional[Union[str, Path]] = None,
    site_label: Optional[str] = None,
) -> dict:
    """
    Evaluate a grid of candidate landing-zone centres.

    All three safety limits must be supplied by the caller.
    """

    lat = _num("lat", lat, -90.0, 90.0)
    lon = _num("lon", lon, -180.0, 180.0)

    if abs(lat) >= 90.0 - _POLE_TOL_DEG:
        raise ValueError(
            "Site is too close to a pole for this local east/north grid."
        )

    max_slope_deg = _num(
        "max_slope_deg",
        max_slope_deg,
        0.0,
        90.0,
        lo_open=True,
    )

    max_roughness_m = _num(
        "max_roughness_m",
        max_roughness_m,
        0.0,
    )

    min_radius_m = _num(
        "min_radius_m",
        min_radius_m,
        0.0,
        float(_slope.MAX_RADIUS_M),
        lo_open=True,
    )

    cell = (
        2.0 * min_radius_m
        if cell_size_m is None
        else _num("cell_size_m", cell_size_m, 0.0, lo_open=True)
    )

    half = (
        DEFAULT_HALF_EXTENT_CELLS * cell
        if half_extent_m is None
        else _num("half_extent_m", half_extent_m, 0.0)
    )

    if not isinstance(allow_unverified_dem, bool):
        raise ValueError(
            "allow_unverified_dem must be True or False."
        )

    m = int(math.floor(half / cell + 1e-9))

    n = 2 * m + 1

    if n * n > MAX_CELLS:
        raise ValueError(
            f"Grid of {n} x {n} exceeds maximum "
            f"of {MAX_CELLS} cells."
        )

    cells = []

    first_dem = {}
    first_inputs = []

    seen_warnings = {}

    # IMPORTANT:
    # Verification starts as unestablished, not True.
    dem_verification_seen = False
    dem_verification_blocked = False

    # Visit every candidate centre.

    for j in range(n):

        for i in range(n):

            east = (i - m) * cell
            north = (m - j) * cell

            cell_lat, cell_lon = _offset_to_latlon(
                lat,
                lon,
                east,
                north,
            )

            try:
                result = get_slope(
                    cell_lat,
                    cell_lon,
                    min_radius_m,
                    data_dir=data_dir,
                )

            except ValueError as exc:

                cells.append({
                    "i": i,
                    "j": j,
                    "east_m": round(east, 3),
                    "north_m": round(north, 3),
                    "lat": round(cell_lat, 6),
                    "lon": round(cell_lon, 6),
                    "class": UNKNOWN,
                    "reasons": [
                        _reason("TERRAIN_ERROR", str(exc))
                    ],
                    "slope_max_deg": None,
                    "roughness_rms_m": None,
                    "terrain_status": "UNAVAILABLE",
                })

                continue

            warnings = getattr(result, "warnings", []) or []

            codes = _codes(warnings)

            # Record that a terrain result was received.
            dem_verification_seen = True

            # Incomplete or unverified metadata blocks verification.
            if any(
                code in _DEM_BLOCKING_CODES
                for code in codes
            ):
                dem_verification_blocked = True

            for warning in warnings:
                code = str(warning).split(":", 1)[0].strip()

                seen_warnings.setdefault(
                    code,
                    str(warning),
                )

            if (
                not first_dem
                and getattr(result, "dem", None)
            ):
                first_dem = dict(result.dem)

            if not first_inputs:
                provenance = (
                    getattr(result, "provenance", None) or {}
                )

                first_inputs = list(
                    provenance.get("inputs", [])
                )

            cell_class, reasons = classify_cell(
                result,
                max_slope_deg,
                max_roughness_m,
                min_radius_m,
                allow_unverified_dem,
            )

            cells.append({
                "i": i,
                "j": j,
                "east_m": round(east, 3),
                "north_m": round(north, 3),
                "lat": round(cell_lat, 6),
                "lon": round(cell_lon, 6),
                "class": cell_class,
                "reasons": reasons,
                "slope_max_deg": getattr(
                    result,
                    "slope_max_deg",
                    None,
                ),
                "roughness_rms_m": getattr(
                    result,
                    "roughness_rms_m",
                    None,
                ),
                "terrain_status": getattr(
                    result,
                    "status",
                    "UNKNOWN",
                ),
            })

    # -----------------------------------------------------------------
    # DEM verification summary
    # -----------------------------------------------------------------

    dem_verified = (
        dem_verification_seen
        and not dem_verification_blocked
    )

    # -----------------------------------------------------------------
    # Summary counts
    # -----------------------------------------------------------------

    counts = {
        PASS: 0,
        FAIL: 0,
        UNKNOWN: 0,
    }

    for cell_result in cells:
        counts[cell_result["class"]] += 1

    if counts[PASS] > 0:
        site_class = PASS

    elif counts[UNKNOWN] > 0:
        site_class = UNKNOWN

    else:
        site_class = FAIL

    centre = next(
        c for c in cells
        if c["i"] == m and c["j"] == m
    )

    # Group failure and unknown reasons.

    reasons_summary = {}

    for cell_result in cells:

        for reason in cell_result["reasons"]:

            key = (
                cell_result["class"],
                reason["code"],
            )

            entry = reasons_summary.setdefault(
                key,
                {
                    "class": cell_result["class"],
                    "code": reason["code"],
                    "message": reason["message"],
                    "cells": 0,
                    "example_cells": [],
                },
            )

            entry["cells"] += 1

            if len(entry["example_cells"]) < 3:
                entry["example_cells"].append([
                    cell_result["i"],
                    cell_result["j"],
                ])

    computed = any(
        c["slope_max_deg"] is not None
        and c["roughness_rms_m"] is not None
        for c in cells
    )

    warnings = list(seen_warnings.values())

    provisional = (
        not dem_verified
        and allow_unverified_dem
    )

    if provisional:
        warnings.append(
            "UNVERIFIED_DEM_ACCEPTED: allow_unverified_dem=True; "
            "results are provisional because DEM verification "
            "has not been established."
        )

    # -----------------------------------------------------------------
    # Final assessment dictionary
    # -----------------------------------------------------------------

    assessment = {
        "site": {
            "label": site_label,
            "lat": lat,
            "lon": lon,
        },

        "limits": {
            "max_slope_deg": max_slope_deg,
            "max_roughness_m": max_roughness_m,
            "min_radius_m": min_radius_m,
            "comparison": "value <= limit passes",
        },

        "grid": {
            "cell_size_m": cell,
            "half_extent_m": m * cell,
            "n_east": n,
            "n_north": n,
            "orientation": (
                "local tangent plane, north up, east right"
            ),
            "classes": _class_matrix_from_cells(cells, n),
        },

        "cells": cells,

        "summary": {
            "total": len(cells),
            "pass": counts[PASS],
            "fail": counts[FAIL],
            "unknown": counts[UNKNOWN],
            "centre_class": centre["class"],
            "site_class": site_class,
            "has_passing_zone": counts[PASS] > 0,
        },

        "reasons": sorted(
            reasons_summary.values(),
            key=lambda r: (
                r["class"],
                -r["cells"],
            ),
        ),

        "dem": first_dem,

        "dem_verified": dem_verified,

        "results_provisional": provisional,

        "warnings": warnings,

        "provenance": {
            "class": (
                "CALCULATED"
                if computed
                else "UNAVAILABLE"
            ),

            "inputs": first_inputs,

            "assumptions": [
                "All three limits are supplied by the caller.",
                "Slope uses F14 slope_max_deg.",
                "Roughness uses F14 roughness_rms_m.",
                "The complete landing-zone radius must be covered.",
                "A value equal to its limit passes.",
                "Missing, partial, or unverified data gives UNKNOWN.",
                "The DEM cannot represent terrain smaller than "
                "its resolution or every possible landing hazard.",
            ],
        },

        "statement": SAFETY_STATEMENT,

        "map_png": None,
    }

    if png_path is not None:
        assessment["map_png"] = str(
            write_suitability_png(
                assessment,
                png_path,
            )
        )

    return assessment


# ---------------------------------------------------------------------
# Convenience evaluation function
# ---------------------------------------------------------------------

def evaluate(lat: float, lon: float, limits: dict, **kwargs) -> dict:
    """Evaluate using a dictionary containing the three limits."""

    if not isinstance(limits, dict):
        raise ValueError("limits must be a dictionary.")

    required = (
        "max_slope_deg",
        "max_roughness_m",
        "min_radius_m",
    )

    missing = [
        key for key in required
        if key not in limits
    ]

    if missing:
        raise ValueError(
            f"Missing required limits: {', '.join(missing)}"
        )

    return evaluate_site(
        lat,
        lon,
        max_slope_deg=limits["max_slope_deg"],
        max_roughness_m=limits["max_roughness_m"],
        min_radius_m=limits["min_radius_m"],
        **kwargs,
    )


# ---------------------------------------------------------------------
# M1 integration function
# ---------------------------------------------------------------------

def get_hazard(
    lat: float,
    lon: float,
    limits: Optional[dict] = None,
    **kwargs,
) -> dict:
    """
    M1 contract: get_hazard(lat, lon).

    Without supplied limits, the result remains UNKNOWN.
    """

    lat = _num("lat", lat, -90.0, 90.0)
    lon = _num("lon", lon, -180.0, 180.0)

    if limits is not None:
        return evaluate(
            lat,
            lon,
            limits,
            **kwargs,
        )

    return {
        "site": {
            "label": None,
            "lat": lat,
            "lon": lon,
        },

        "limits": None,
        "grid": None,
        "cells": [],

        "summary": {
            "total": 0,
            "pass": 0,
            "fail": 0,
            "unknown": 0,
            "centre_class": UNKNOWN,
            "site_class": UNKNOWN,
            "has_passing_zone": False,
        },

        "reasons": [
            {
                "class": UNKNOWN,
                "code": "NO_LIMITS",
                "cells": 0,
                "example_cells": [],
                "message": (
                    "No safety limits were supplied, "
                    "so nothing can be judged."
                ),
            }
        ],

        "dem": {},
        "dem_verified": False,
        "results_provisional": False,
        "warnings": [],

        "provenance": {
            "class": "UNAVAILABLE",
            "inputs": [],
            "assumptions": [
                "No limits supplied; no assessment performed."
            ],
        },

        "statement": SAFETY_STATEMENT,
        "map_png": None,
    }


# ---------------------------------------------------------------------
# Suitability PNG generation
# ---------------------------------------------------------------------

def write_suitability_png(
    assessment: dict,
    path: Union[str, Path],
) -> Path:
    """Generate a PNG map of PASS, FAIL and UNKNOWN cells."""

    try:
        from matplotlib.colors import ListedColormap
        from matplotlib.figure import Figure
        from matplotlib.patches import Patch

    except ImportError as exc:
        raise ImportError(
            "Matplotlib is required to generate the suitability PNG."
        ) from exc

    order = [
        PASS,
        FAIL,
        UNKNOWN,
    ]

    classes = assessment["grid"]["classes"]

    n = len(classes)

    data = [
        [order.index(value) for value in row]
        for row in classes
    ]

    cell = assessment["grid"]["cell_size_m"]

    half = (n // 2 + 0.5) * cell

    site = assessment["site"]
    limits = assessment["limits"]
    summary = assessment["summary"]

    fig = Figure(
        figsize=(7.5, 8.4),
        dpi=120,
    )

    ax = fig.add_subplot(111)

    ax.imshow(
        data,
        cmap=ListedColormap([
            _COLOURS[c]
            for c in order
        ]),
        vmin=0,
        vmax=2,
        extent=(-half, half, -half, half),
        origin="upper",
        interpolation="nearest",
    )

    centres = [
        (k - n // 2) * cell
        for k in range(n)
    ]

    step = max(1, math.ceil(n / 11))

    ax.set_xticks(centres[::step])
    ax.set_yticks(centres[::step])

    edges = [
        (k - n / 2) * cell
        for k in range(n + 1)
    ]

    ax.set_xticks(edges, minor=True)
    ax.set_yticks(edges, minor=True)

    ax.grid(
        which="minor",
        color="white",
        linewidth=0.6,
    )

    ax.tick_params(
        which="minor",
        length=0,
    )

    ax.plot(
        [0],
        [0],
        marker="+",
        color="black",
        markersize=12,
    )

    ax.set_xlabel(
        "East offset from site centre (m)"
    )

    ax.set_ylabel(
        "North offset from site centre (m)"
    )

    label = site.get("label") or "site"

    ax.set_title(
        f"Landing suitability (preliminary) - {label}\n"
        f"Centre lat {site['lat']:.4f}, "
        f"lon {site['lon']:.4f}\n"
        f"Slope <= {limits['max_slope_deg']:g} deg, "
        f"roughness <= {limits['max_roughness_m']:g} m, "
        f"radius {limits['min_radius_m']:g} m",
        fontsize=9,
    )

    handles = [
        Patch(
            facecolor=_COLOURS[c],
            label=f"{c} ({summary[c.lower()]})",
        )
        for c in order
    ]

    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.11),
        ncol=3,
        frameon=False,
    )

    note = assessment["statement"]

    if not assessment["dem_verified"]:
        note += "\nDEM metadata / vertical units NOT verified."

        if assessment["results_provisional"]:
            note += " Classes are provisional."

    fig.text(
        0.5,
        0.012,
        note,
        ha="center",
        va="bottom",
        fontsize=8,
    )

    fig.subplots_adjust(
        left=0.12,
        right=0.95,
        top=0.9,
        bottom=0.2,
    )

    output = Path(path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        output,
        format="png",
    )

    return output


# ---------------------------------------------------------------------
# Command-line helpers
# ---------------------------------------------------------------------

def _site_from_json(path: Path, site_id: str) -> tuple:
    """Find a site by ID in data/sites.json."""

    raw = json.loads(
        path.read_text(encoding="utf-8")
    )

    items = (
        raw.get("sites", raw)
        if isinstance(raw, dict)
        else raw
    )

    for item in items:

        if item.get("id") == site_id:

            if (
                item.get("lat") is None
                or item.get("lon") is None
            ):
                raise SystemExit(
                    f"{site_id}: coordinates are unavailable."
                )

            return (
                float(item["lat"]),
                float(item["lon"]),
                item.get("name") or site_id,
            )

    raise SystemExit(
        f"Site ID {site_id!r} not found in {path}"
    )


# ---------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------

def main(argv: Optional[list] = None) -> int:

    parser = argparse.ArgumentParser(
        description=(
            "LUNARIS F15 preliminary landing suitability"
        )
    )

    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)

    parser.add_argument("--site-id")

    parser.add_argument(
        "--sites-json",
        type=Path,
    )

    parser.add_argument(
        "--max-slope-deg",
        type=float,
        required=True,
    )

    parser.add_argument(
        "--max-roughness-m",
        type=float,
        required=True,
    )

    parser.add_argument(
        "--min-radius-m",
        type=float,
        required=True,
    )

    parser.add_argument(
        "--cell-size-m",
        type=float,
    )

    parser.add_argument(
        "--half-extent-m",
        type=float,
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
    )

    parser.add_argument(
        "--png",
        type=Path,
    )

    parser.add_argument(
        "--allow-unverified-dem",
        action="store_true",
    )

    parser.add_argument(
        "--full",
        action="store_true",
    )

    args = parser.parse_args(argv)

    label = None

    if args.site_id:

        if not args.sites_json:
            parser.error(
                "--site-id requires --sites-json"
            )

        lat, lon, label = _site_from_json(
            args.sites_json,
            args.site_id,
        )

    elif args.lat is not None and args.lon is not None:

        lat = args.lat
        lon = args.lon

    else:
        parser.error(
            "Provide --lat and --lon, or --site-id with --sites-json."
        )

    png = args.png

    if png is None:

        stem = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "_",
            args.site_id or f"{lat}_{lon}",
        )

        png = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "layers"
            / f"landing_suitability_{stem}.png"
        )

    try:

        result = evaluate_site(
            lat,
            lon,
            max_slope_deg=args.max_slope_deg,
            max_roughness_m=args.max_roughness_m,
            min_radius_m=args.min_radius_m,
            cell_size_m=args.cell_size_m,
            half_extent_m=args.half_extent_m,
            allow_unverified_dem=args.allow_unverified_dem,
            data_dir=args.data_dir,
            png_path=png,
            site_label=label,
        )

    except ValueError as exc:

        print(
            f"Invalid input: {exc}",
            file=sys.stderr,
        )

        return 2

    if args.full:
        output = result

    else:
        keys = (
            "site",
            "limits",
            "summary",
            "reasons",
            "dem_verified",
            "results_provisional",
            "warnings",
            "statement",
            "map_png",
        )

        output = {
            key: result[key]
            for key in keys
        }

    print(
        json.dumps(
            output,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
