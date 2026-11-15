"""Projection parameters for the project's MOON_ME south-polar DEM."""

import math


def south_polar_parameters(crs) -> dict:
    """Read projection numbers from a projected CRS without using its datum."""
    if crs.is_bound:
        crs = crs.source_crs

    if not crs.is_projected:
        raise ValueError("DEM CRS is not projected.")

    ellipsoid = crs.ellipsoid
    radius = float(ellipsoid.semi_major_metre)
    if (
        not math.isfinite(radius)
        or radius <= 0
        or abs(radius - float(ellipsoid.semi_minor_metre)) > 1e-6
    ):
        raise ValueError("DEM CRS must use a spherical lunar reference surface.")

    operation = crs.coordinate_operation
    method_name = operation.method_name if operation else ""
    if "polar stereographic" not in method_name.lower():
        raise ValueError("DEM CRS must use a polar stereographic projection.")

    if not crs.axis_info or any(
        axis.unit_conversion_factor is None
        or abs(float(axis.unit_conversion_factor) - 1.0) > 1e-12
        for axis in crs.axis_info[:2]
    ):
        raise ValueError("DEM projected axes must be in metres.")

    params = {
        param.name.strip().lower(): float(param.value)
        for param in operation.params
    }

    def parameter(*names):
        for name in names:
            if name in params:
                return params[name]
        return None

    latitude_origin = parameter(
        "latitude of natural origin",
        "latitude of origin",
    )
    standard_parallel = parameter(
        "latitude of standard parallel",
        "latitude of standard parallel (lat_ts)",
    )
    scale_factor = parameter(
        "scale factor at natural origin",
        "scale factor",
    )
    longitude_origin = parameter(
        "longitude of natural origin",
        "longitude of origin",
        "longitude of natural origin (longitude of origin)",
    )
    false_easting = parameter("false easting")
    false_northing = parameter("false northing")
    false_easting = 0.0 if false_easting is None else false_easting
    false_northing = 0.0 if false_northing is None else false_northing

    if (
        not math.isfinite(false_easting)
        or not math.isfinite(false_northing)
        or abs(false_easting) > 1e-9
        or abs(false_northing) > 1e-9
    ):
        raise ValueError("DEM CRS false easting/northing must be zero.")

    if longitude_origin is None or not math.isfinite(longitude_origin):
        raise ValueError("DEM CRS has no central meridian.")

    if standard_parallel is not None:
        if (
            not math.isfinite(standard_parallel)
            or standard_parallel > 0
            or standard_parallel < -90
        ):
            raise ValueError("DEM CRS standard parallel is not south-polar.")
        k0 = (1.0 - math.sin(math.radians(standard_parallel))) / 2.0
    elif scale_factor is not None and latitude_origin is not None:
        if (
            not math.isfinite(latitude_origin)
            or not math.isfinite(scale_factor)
            or abs(latitude_origin + 90.0) > 1e-9
        ):
            raise ValueError("DEM CRS latitude of origin must be the south pole.")
        k0 = scale_factor
    else:
        raise ValueError("DEM CRS has no supported south-polar scale parameter.")

    if not math.isfinite(k0) or k0 <= 0:
        raise ValueError("DEM CRS scale factor must be positive and finite.")
    if scale_factor is not None and abs(scale_factor - k0) > 1e-9:
        raise ValueError("DEM CRS scale parameters are inconsistent.")

    return {
        "type": "polar_stereographic_south",
        "R_m": radius,
        "k0": k0,
        "lon0_deg": longitude_origin,
    }
