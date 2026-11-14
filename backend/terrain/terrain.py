"""LUNARIS M3 - terrain.py

elevation_at(lat, lon, dem_path): height of the Moon's surface at a point,
read from a LOLA DEM GeoTIFF.

Conventions (docs/conventions.md):
  - lat: -90..90 degrees, south negative
  - lon: East-positive, -180..180 degrees
  - height: metres above the Moon reference sphere (R = 1737.4 km)

Rules followed here:
  - No guessing. No-data, NaN, out-of-bounds, missing CRS -> class UNAVAILABLE.
  - The DEM's own CRS is used (never an Earth ellipsoid assumed).
  - The value is the pixel that contains the point (no interpolation).

LUNARIS is an independent student prototype, not an official NASA product.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Union

import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.errors import RasterioError
from rasterio.transform import rowcol
from rasterio.windows import Window

PUBLISHED = "PUBLISHED"
UNAVAILABLE = "UNAVAILABLE"


def _result(value_m, resolution_m, cls, status) -> dict:
    return {
        "value_m": value_m,
        "resolution_m": resolution_m,
        "class": cls,
        "status": status,
    }


def _unavailable(status: str, resolution_m=None) -> dict:
    return _result(None, resolution_m, UNAVAILABLE, status)


def _validate_coordinate(lat: float, lon: float) -> None:
    """Raise ValueError for invalid input (M1 maps this to INVALID_COORDINATE)."""
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


def _resolution_m(src: rasterio.DatasetReader, crs: CRS) -> float | None:
    """Pixel size in metres, or None if it cannot be stated honestly.

    Projected CRS: pixel size * the CRS linear unit factor.
    Geographic CRS (degrees): None, because metres per degree is not constant
    and we do not want to publish an approximation as if it were a fact.
    """
    if crs.is_geographic or not crs.axis_info:
        return None
    factor = crs.axis_info[0].unit_conversion_factor or 1.0
    px = abs(src.transform.a) * factor
    py = abs(src.transform.e) * factor
    # LOLA grids are square; report the mean if tiny float differences exist.
    return float((px + py) / 2.0)


def elevation_at(lat: float, lon: float, dem_path: Union[str, Path]) -> dict:
    """Return the DEM height at (lat, lon).

    Returns
    -------
    dict with keys
      value_m       float | None   height in metres (None if UNAVAILABLE)
      resolution_m  float | None   DEM pixel size in metres
      class         "PUBLISHED" | "UNAVAILABLE"
      status        "OK" or the reason the value is unavailable
                    (OUT_OF_BOUNDS, NODATA, NO_CRS, DEM_UNREADABLE, ...)

    Raises
    ------
    ValueError  if lat/lon are not valid numbers or are out of range.
    """
    _validate_coordinate(lat, lon)
    lat, lon = float(lat), float(lon)

    try:
        with rasterio.open(dem_path) as src:
            if src.crs is None:
                return _unavailable("NO_CRS: DEM file has no coordinate system")

            dem_crs = CRS.from_user_input(src.crs.to_wkt())
            res_m = _resolution_m(src, dem_crs)

            # lat/lon -> DEM projection. Use the DEM CRS's own (lunar)
            # geodetic CRS so we never fall back to an Earth ellipsoid.
            transformer = Transformer.from_crs(
                dem_crs.geodetic_crs, dem_crs, always_xy=True
            )
            x, y = transformer.transform(lon, lat)
            if not (math.isfinite(x) and math.isfinite(y)):
                return _unavailable(
                    "OUT_OF_BOUNDS: point cannot be projected into DEM CRS", res_m
                )

            # Geographic DEMs may use 0..360 longitude instead of -180..180.
            if dem_crs.is_geographic:
                left, right = src.bounds.left, src.bounds.right
                if not left <= x <= right:
                    for shift in (360.0, -360.0):
                        if left <= x + shift <= right:
                            x += shift
                            break

            # Quick bounds test before indexing.
            b = src.bounds
            if not (b.left <= x <= b.right and b.bottom <= y <= b.top):
                return _unavailable("OUT_OF_BOUNDS: outside DEM coverage", res_m)

            row, col = rowcol(src.transform, x, y)
            row = int(np.asarray(row).reshape(-1)[0])
            col = int(np.asarray(col).reshape(-1)[0])

            if not (0 <= row < src.height and 0 <= col < src.width):
                return _unavailable("OUT_OF_BOUNDS: outside DEM coverage", res_m)

            # Read only the single pixel. masked=True honours the file's
            # nodata value and any internal mask.
            data = src.read(1, window=Window(col, row, 1, 1), masked=True)
            if data.size == 0 or np.ma.is_masked(data[0, 0]):
                return _unavailable("NODATA: DEM has no data at this point", res_m)

            raw = float(data[0, 0])
            if not math.isfinite(raw):
                return _unavailable("NODATA: DEM value is NaN/inf here", res_m)

            # Apply GeoTIFF scale/offset if the file defines them
            # (some LOLA products store scaled integers).
            scale = src.scales[0] if src.scales else 1.0
            offset = src.offsets[0] if src.offsets else 0.0
            value_m = raw * scale + offset

            return _result(value_m, res_m, PUBLISHED, "OK")

    except RasterioError as exc:
        return _unavailable(f"DEM_UNREADABLE: {exc}")