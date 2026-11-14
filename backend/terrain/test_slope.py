
"""LUNARIS M3 - F14 slope tests.

Uses small synthetic DEM tiles. Does not require the real LOLA DEM.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest


# Load slope.py directly and register it for dataclass compatibility.
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "lunaris_test_slope", HERE / "slope.py"
)
slope = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = slope
SPEC.loader.exec_module(slope)


@pytest.fixture(autouse=True)
def clear_tile_cache():
    slope.clear_cache()
    yield
    slope.clear_cache()


def make_test_dem(data_dir, gx=0.0, gy=0.0, base=100.0):
    """Create a 101x101 synthetic DEM around latitude -80, longitude 0."""

    tile_dir = data_dir / "dem_tiles"
    tile_dir.mkdir(parents=True, exist_ok=True)

    lat, lon = -80.0, 0.0
    resolution = 100.0
    size = 101
    middle = size // 2

    R = slope.R_MOON_M
    k0 = 1.0
    lon0 = 0.0

    x0, y0 = slope.project_south_polar(lat, lon, R, k0, lon0)
    x0, y0 = float(x0), float(y0)

    # Put the test location at the centre of the middle pixel.
    x_left = x0 - (middle + 0.5) * resolution
    y_top = y0 + (middle + 0.5) * resolution

    cols = np.arange(size)
    rows = np.arange(size)

    xs = x_left + (cols + 0.5) * resolution
    ys = y_top - (rows + 0.5) * resolution

    k = float(slope.scale_factor_south_polar(lat, k0))

    # Create a mathematically flat or inclined surface.
    z = (
        base
        + gx * (xs[None, :] - x0) / k
        + gy * (ys[:, None] - y0) / k
    )

    z = np.asarray(z, dtype=np.float32)

    tile_meta = {
        "grid": {
            "res_m": resolution,
            "x_left_m": x_left,
            "y_top_m": y_top,
            "height": size,
            "width": size,
        },
        "projection": {
            "type": slope.PROJECTION_TYPE,
            "R_m": R,
            "k0": k0,
            "lon0_deg": lon0,
        },
        "dem": {
            "name": "Synthetic test DEM",
            "resolution_m": resolution,
            "coverage": "Synthetic test area",
            "retrieved_utc": "2026-11-14T00:00:00Z",
            "version": "test",
        },
    }

    np.savez_compressed(
        tile_dir / "test_tile.npz",
        z=z,
        meta=np.array(json.dumps(tile_meta)),
    )

    # Verified metadata is used only for these synthetic tests.
    dem_meta = {
        "status": "VERIFIED",
        "vertical_units": "m",
        "name": "Synthetic test DEM",
        "resolution_m": resolution,
        "coverage": "Synthetic test area",
        "retrieved_utc": "2026-11-14T00:00:00Z",
    }

    (data_dir / "dem_meta.json").write_text(
        json.dumps(dem_meta),
        encoding="utf-8",
    )

    return lat, lon


def test_flat_dem_has_zero_slope_and_roughness(tmp_path):
    lat, lon = make_test_dem(tmp_path)

    result = slope.get_slope(
        lat, lon, 500, data_dir=tmp_path
    )

    assert result.status == "OK"
    assert result.approx is False
    assert result.data_class == "CALCULATED"
    assert result.slope_deg == pytest.approx(0.0, abs=0.1)
    assert result.slope_max_deg == pytest.approx(0.0, abs=0.1)
    assert result.slope_mean_deg == pytest.approx(0.0, abs=0.1)
    assert result.roughness_rms_m == pytest.approx(0.0, abs=0.01)
    assert result.elevation_m == pytest.approx(100.0, abs=0.1)


def test_inclined_dem_has_expected_slope(tmp_path):
    gx = 0.20
    gy = 0.10
    lat, lon = make_test_dem(tmp_path, gx=gx, gy=gy)

    result = slope.get_slope(
        lat, lon, 500, data_dir=tmp_path
    )

    expected = math.degrees(
        math.atan(math.hypot(gx, gy))
    )

    assert result.status == "OK"
    assert result.slope_deg == pytest.approx(expected, abs=0.2)
    assert result.roughness_rms_m == pytest.approx(0.0, abs=0.01)


def test_missing_tiles_return_unavailable(tmp_path):
    tmp_path.mkdir(exist_ok=True)

    result = slope.get_slope(
        -80.0, 0.0, 500, data_dir=tmp_path
    )

    assert result.status == "UNAVAILABLE"
    assert result.approx is True
    assert result.data_class == "UNAVAILABLE"
    assert result.slope_deg is None
    assert any("NO_DEM_TILES" in w for w in result.warnings)


@pytest.mark.parametrize(
    "lat, lon, radius",
    [
        (91, 0, 500),
        (-91, 0, 500),
        (-80, 181, 500),
        (-80, -181, 500),
        (-80, 0, 0),
        (-80, 0, -10),
        (-80, 0, 50001),
    ],
)
def test_invalid_inputs_raise_value_error(tmp_path, lat, lon, radius):
    with pytest.raises(ValueError):
        slope.get_slope(
            lat, lon, radius, data_dir=tmp_path
        )


def test_profile_contains_expected_samples(tmp_path):
    lat, lon = make_test_dem(tmp_path)

    result = slope.get_slope(
        lat,
        lon,
        500,
        profile_az_deg=90,
        data_dir=tmp_path,
    )

    assert result.profile is not None
    assert result.profile["az_deg"] == 90.0
    assert result.profile["sampling"] == "nearest_pixel"
    assert len(result.profile["distance_m"]) == 11
    assert len(result.profile["elevation_m"]) == 11
    assert all(
        value is not None
        for value in result.profile["elevation_m"]
    )


def test_profile_azimuth_wraps_at_360_degrees(tmp_path):
    lat, lon = make_test_dem(tmp_path)

    result = slope.get_slope(
        lat,
        lon,
        500,
        profile_az_deg=360,
        data_dir=tmp_path,
    )

    assert result.profile is not None
    assert result.profile["az_deg"] == 0.0
