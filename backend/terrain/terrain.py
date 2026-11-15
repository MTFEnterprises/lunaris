
"""LUNARIS M3 - terrain.py

elevation_at(lat, lon, dem_path):
    Returns the elevation of the lunar surface at a coordinate,
    using the pixel containing that coordinate in a LOLA DEM GeoTIFF.

Conventions:
    Latitude: -90 to 90 degrees, south negative.
    Longitude: -180 to 180 degrees, east-positive.
    Height: metres above the Moon reference sphere.

Important:
    The DEM's vertical units and lunar reference frame must be
    verified from the source product metadata before publishing
    its values as PUBLISHED.

    No interpolation is performed.
    Missing or invalid data is returned as UNAVAILABLE.

LUNARIS is an independent student prototype, not an official NASA product.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Union

import numpy as np
from backend.terrain.projection import south_polar_parameters
from backend.terrain.slope import project_south_polar

# Optional geospatial dependencies.
# This module can still be imported when only NumPy is installed.
try:
    import rasterio
    from pyproj import CRS
    from pyproj.exceptions import CRSError
    from rasterio.errors import RasterioError
    from rasterio.transform import rowcol
    from rasterio.windows import Window

    GEOSPATIAL_AVAILABLE = True

except ImportError:
    rasterio = None
    CRS = None
    CRSError = Exception
    RasterioError = Exception
    rowcol = None
    Window = None

    GEOSPATIAL_AVAILABLE = False


PUBLISHED = "PUBLISHED"
UNAVAILABLE = "UNAVAILABLE"


def _result(value_m, resolution_m, data_class, status):
    return {
        "value_m": value_m,
        "resolution_m": resolution_m,
        "class": data_class,
        "status": status,
    }


def _unavailable(status, resolution_m=None):
    return _result(None, resolution_m, UNAVAILABLE, status)


def _validate_coordinate(lat: float, lon: float) -> None:
    """Validate latitude and longitude."""

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        raise ValueError("Latitude and longitude must be numbers.")

    if not math.isfinite(lat) or not math.isfinite(lon):
        raise ValueError("Latitude and longitude must be finite.")

    if not -90.0 <= lat <= 90.0:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180.0 <= lon <= 180.0:
        raise ValueError("Longitude must be between -180 and 180.")


def _resolution_m(src, crs: CRS):
    """Calculate approximate pixel size in metres.

    Returns None if the CRS does not provide a reliable
    projected linear unit.
    """

    if not crs.is_projected or not crs.axis_info:
        return None

    if len(crs.axis_info) < 2:
        return None

    factor_x = crs.axis_info[0].unit_conversion_factor
    factor_y = crs.axis_info[1].unit_conversion_factor

    if factor_x is None or factor_y is None:
        return None

    # Account for rotated as well as north-up rasters.
    pixel_x = math.hypot(
        src.transform.a * factor_x,
        src.transform.d * factor_x
    )

    pixel_y = math.hypot(
        src.transform.b * factor_y,
        src.transform.e * factor_y
    )

    resolution = (pixel_x + pixel_y) / 2.0

    if not math.isfinite(resolution) or resolution <= 0:
        return None

    return float(resolution)


def elevation_at(
    lat: float,
    lon: float,
    dem_path: Union[str, Path]
) -> dict:
    """Return lunar elevation at a latitude/longitude.

    Returns:
        {
            "value_m": float or None,
            "resolution_m": float or None,
            "class": "PUBLISHED" or "UNAVAILABLE",
            "status": "OK" or reason
        }

    Raises:
        ValueError: Invalid latitude or longitude.
    """

    _validate_coordinate(lat, lon)

    # Do not attempt DEM access without geospatial dependencies.
    if not GEOSPATIAL_AVAILABLE:
        return _unavailable(
            "GEOSPATIAL_DEPENDENCIES_MISSING: "
            "rasterio and pyproj are required for DEM access."
        )

    lat = float(lat)
    lon = float(lon)

    try:
        with rasterio.open(dem_path) as src:

            # Check that the DEM has a coordinate system.
            if src.crs is None:
                return _unavailable(
                    "NO_CRS: DEM has no coordinate system."
                )

            try:
                dem_crs = CRS.from_user_input(src.crs)
            except CRSError:
                return _unavailable(
                    "INVALID_CRS: DEM coordinate system is invalid."
                )

            resolution_m = _resolution_m(src, dem_crs)

            try:
                projection = south_polar_parameters(dem_crs)
                x, y = project_south_polar(
                    lat, lon, projection["R_m"], projection["k0"],
                    projection["lon0_deg"]
                )
                x, y = float(x), float(y)
            except ValueError as exc:
                return _unavailable(
                    f"UNSUPPORTED_CRS: {exc}",
                    resolution_m
                )

            if not (math.isfinite(x) and math.isfinite(y)):
                return _unavailable(
                    "OUT_OF_BOUNDS: Invalid projected coordinate.",
                    resolution_m
                )

            # Handle geographic DEMs using 0 to 360 longitude.
            if dem_crs.is_geographic:
                left = src.bounds.left
                right = src.bounds.right

                if not left <= x <= right:
                    for shift in (360.0, -360.0):
                        if left <= x + shift <= right:
                            x += shift
                            break

            # Check DEM coverage.
            bounds = src.bounds

            if not (
                bounds.left <= x <= bounds.right
                and bounds.bottom <= y <= bounds.top
            ):
                return _unavailable(
                    "OUT_OF_BOUNDS: Coordinate outside DEM coverage.",
                    resolution_m
                )

            # Find the pixel containing the coordinate.
            row, col = rowcol(src.transform, x, y)

            row = int(row)
            col = int(col)

            if not (
                0 <= row < src.height
                and 0 <= col < src.width
            ):
                return _unavailable(
                    "OUT_OF_BOUNDS: Pixel outside DEM coverage.",
                    resolution_m
                )

            # Read only one pixel.
            data = src.read(
                1,
                window=Window(col, row, 1, 1),
                masked=True
            )

            if data.size == 0 or np.ma.is_masked(data[0, 0]):
                return _unavailable(
                    "NODATA: No elevation data at this coordinate.",
                    resolution_m
                )

            raw_value = float(data[0, 0])

            if not math.isfinite(raw_value):
                return _unavailable(
                    "NODATA: Elevation is NaN or infinite.",
                    resolution_m
                )

            # Apply GeoTIFF scale and offset.
            scale = src.scales[0] if src.scales else 1.0
            offset = src.offsets[0] if src.offsets else 0.0

            value_m = raw_value * scale + offset

            if not math.isfinite(value_m):
                return _unavailable(
                    "INVALID_VALUE: Scaled elevation is not finite.",
                    resolution_m
                )

            # This assumes source metadata has confirmed that
            # the scaled vertical values are in metres.
            return _result(
                float(value_m),
                resolution_m,
                PUBLISHED,
                "OK"
            )

    except (RasterioError, OSError):
        return _unavailable(
            "DEM_UNREADABLE: Could not open or read the DEM."
        )
