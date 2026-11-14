"""LUNARIS M3 - unit tests for terrain.py and horizon.py.

Run from anywhere:   pytest backend/terrain/test_m3.py -v

Every test uses small SYNTHETIC GeoTIFFs built on the fly (a lunar polar
stereographic grid), so no real LOLA DEM is needed and every expected answer
is known analytically in advance. Nothing here is real lunar data.

Layout of the synthetic DEMs
  - Projection: south polar stereographic on a sphere of R = 1737.4 km
  - Grid: 400 x 400 pixels, 500 m per pixel (200 km x 200 km)
  - Observer: lat -89.0, lon 30.0 (about 30 km from the pole, inside the grid)

The tests load terrain.py and horizon.py from the folder this file lives in,
so it works with or without an __init__.py.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
pyproj = pytest.importorskip("pyproj")

from pyproj import CRS, Transformer  # noqa: E402
from rasterio.errors import RasterioIOError  # noqa: E402
from rasterio.transform import from_origin  # noqa: E402

pytestmark = pytest.mark.filterwarnings(
    "ignore::rasterio.errors.NotGeoreferencedWarning"
)

HERE = Path(__file__).resolve().parent


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(f"lunaris_m3_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


terrain = _load_module("terrain")
horizon = _load_module("horizon")

# --------------------------------------------------------------------------- #
# Synthetic DEM helpers
# --------------------------------------------------------------------------- #
R_MOON = 1737400.0
MOON_WKT = (
    'PROJCS["Moon south polar stereographic",'
    'GEOGCS["Moon",DATUM["D_Moon",SPHEROID["Moon",1737400,0]],'
    'PRIMEM["Reference_Meridian",0],UNIT["degree",0.0174532925199433]],'
    'PROJECTION["Polar_Stereographic"],'
    'PARAMETER["latitude_of_origin",-90],PARAMETER["central_meridian",0],'
    'PARAMETER["scale_factor",1],PARAMETER["false_easting",0],'
    'PARAMETER["false_northing",0],UNIT["metre",1]]'
)
_CRS = CRS.from_wkt(MOON_WKT)
_FWD = Transformer.from_crs(_CRS.geodetic_crs, _CRS, always_xy=True)
_INV = Transformer.from_crs(_CRS, _CRS.geodetic_crs, always_xy=True)

RES = 500.0
N = 400
HALF = N * RES / 2.0
OBS_LAT, OBS_LON = -89.0, 30.0
MAX_KM = 40.0  # ray length used for the small synthetic DEMs


def write_dem(path, data, *, res=RES, crs=MOON_WKT, nodata=-9999.0,
              scale=None, offset=None, units=None) -> str:
    """Write a single-band float32 GeoTIFF centred on the pole."""
    data = np.asarray(data, dtype="float32")
    rows, cols = data.shape
    profile = {
        "driver": "GTiff", "height": rows, "width": cols, "count": 1,
        "dtype": "float32",
        "transform": from_origin(-cols * res / 2.0, rows * res / 2.0, res, res),
    }
    if crs is not None:
        profile["crs"] = crs
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)
        if scale is not None:
            dst.scales = (scale,)
        if offset is not None:
            dst.offsets = (offset,)
        if units is not None:
            dst.units = (units,)
    return str(path)


def xy_grid(n=N, res=RES):
    """Pixel-centre projected coordinates (X, Y) for the standard grid."""
    half = n * res / 2.0
    xs = -half + res * (np.arange(n) + 0.5)
    ys = half - res * (np.arange(n) + 0.5)
    return np.meshgrid(xs, ys)


def observer_xy():
    return _FWD.transform(OBS_LON, OBS_LAT)


def ring_dem(inner_m, outer_m, height_m, n=N, res=RES):
    """Zero terrain with a raised ring around the observer."""
    X, Y = xy_grid(n, res)
    x0, y0 = observer_xy()
    dist = np.hypot(X - x0, Y - y0)
    arr = np.zeros((n, n))
    arr[(dist >= inner_m) & (dist <= outer_m)] = height_m
    return arr


def disc_dem(azimuth_deg, distance_m, radius_m, height_m):
    """Zero terrain with one raised disc at a given bearing from the observer.

    The disc centre comes from horizon._destinations(), whose azimuth
    convention is verified independently in TestAzimuthConvention.
    """
    lat2, lon2 = horizon._destinations(
        OBS_LAT, OBS_LON,
        np.array([[math.radians(azimuth_deg)]]),
        np.array([[distance_m / R_MOON]]),
    )
    cx, cy = _FWD.transform(float(lon2[0, 0]), float(lat2[0, 0]))
    X, Y = xy_grid()
    arr = np.zeros((N, N))
    arr[np.hypot(X - cx, Y - cy) <= radius_m] = height_m
    return arr


def pixel_centre_lonlat(row, col, dx=0.0, dy=0.0, res=RES, n=N):
    """lon/lat of a pixel centre, optionally shifted by (dx, dy) pixels."""
    half = n * res / 2.0
    x = -half + res * (col + 0.5 + dx)
    y = half - res * (row + 0.5 + dy)
    lon, lat = _INV.transform(x, y)
    return lat, lon


def circular_distance(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


@pytest.fixture(scope="module")
def dem_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("m3_dems")


@pytest.fixture(scope="module")
def flat_dem(dem_dir):
    return write_dem(dem_dir / "flat_1250.tif", np.full((N, N), 1250.0))


@pytest.fixture(scope="module")
def ring_path(dem_dir):
    # Ring 20.0-21.5 km from the observer, 500 m high.
    return write_dem(dem_dir / "ring.tif", ring_dem(20000, 21500, 500.0))


@pytest.fixture(autouse=True)
def _no_ambient_env(monkeypatch):
    """Tests must not depend on the developer's environment variables."""
    monkeypatch.delenv(horizon.DEM_PATH_ENV, raising=False)
    monkeypatch.delenv(horizon.DEM_META_ENV, raising=False)


def assert_json_safe(result):
    """M1 serialises these dicts straight into API responses."""
    json.dumps(result, allow_nan=False)


# =========================================================================== #
# terrain.elevation_at
# =========================================================================== #
BAD_COORDS = [
    (91, 0), (-91, 0), (0, 181), (0, -181),
    (float("nan"), 0), (0, float("nan")),
    (float("inf"), 0), (0, float("-inf")),
    ("abc", 0), (0, "abc"), (None, 0), (0, None),
]


class TestTerrainValidation:
    @pytest.mark.parametrize("lat,lon", BAD_COORDS)
    def test_invalid_coordinates_raise_value_error(self, lat, lon, flat_dem):
        with pytest.raises(ValueError):
            terrain.elevation_at(lat, lon, flat_dem)

    @pytest.mark.parametrize("lat,lon", BAD_COORDS)
    def test_validation_happens_before_the_dem_is_opened(self, lat, lon, tmp_path):
        with pytest.raises(ValueError):
            terrain.elevation_at(lat, lon, tmp_path / "does_not_exist.tif")

    @pytest.mark.parametrize("lat,lon", [(-90, 0), (90, 0), (-45, -180), (45, 180), (0, 0)])
    def test_boundary_coordinates_are_accepted(self, lat, lon, flat_dem):
        result = terrain.elevation_at(lat, lon, flat_dem)
        assert set(result) == {"value_m", "resolution_m", "class", "status"}


class TestTerrainErrorHandling:
    def test_missing_file_is_unavailable(self, tmp_path):
        r = terrain.elevation_at(-89.0, 30.0, tmp_path / "missing.tif")
        assert r["class"] == "UNAVAILABLE"
        assert r["value_m"] is None
        assert r["status"].startswith("DEM_UNREADABLE")

    def test_directory_instead_of_file_is_unavailable(self, tmp_path):
        r = terrain.elevation_at(-89.0, 30.0, tmp_path)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("DEM_UNREADABLE")

    def test_corrupt_file_is_unavailable(self, tmp_path):
        bad = tmp_path / "corrupt.tif"
        bad.write_text("this is not a GeoTIFF")
        r = terrain.elevation_at(-89.0, 30.0, bad)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("DEM_UNREADABLE")

    def test_dem_without_crs_is_unavailable(self, dem_dir):
        path = write_dem(dem_dir / "no_crs.tif", np.zeros((20, 20)), crs=None)
        r = terrain.elevation_at(-89.0, 30.0, path)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("NO_CRS")

    def test_open_failure_is_reported_not_raised(self, monkeypatch):
        def boom(*_a, **_k):
            raise OSError("simulated I/O failure")

        monkeypatch.setattr(terrain.rasterio, "open", boom)
        r = terrain.elevation_at(-89.0, 30.0, "anything.tif")
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("DEM_UNREADABLE")

    def test_point_outside_dem_is_out_of_bounds(self, flat_dem):
        # -80 degrees is ~300 km from the pole; the DEM only reaches 100 km.
        r = terrain.elevation_at(-80.0, 0.0, flat_dem)
        assert r["class"] == "UNAVAILABLE"
        assert r["value_m"] is None
        assert r["status"].startswith("OUT_OF_BOUNDS")
        assert r["resolution_m"] == pytest.approx(RES)

    def test_nodata_pixel_is_unavailable(self, dem_dir):
        data = np.full((N, N), 800.0)
        data[150, 230] = -9999.0  # declared nodata value
        path = write_dem(dem_dir / "nodata.tif", data)
        lat, lon = pixel_centre_lonlat(150, 230)
        r = terrain.elevation_at(lat, lon, path)
        assert r["class"] == "UNAVAILABLE"
        assert r["value_m"] is None
        assert r["status"].startswith("NODATA")

    def test_nan_pixel_is_unavailable(self, dem_dir):
        data = np.full((N, N), 800.0)
        data[150, 230] = np.nan
        path = write_dem(dem_dir / "nan.tif", data)
        lat, lon = pixel_centre_lonlat(150, 230)
        r = terrain.elevation_at(lat, lon, path)
        assert r["class"] == "UNAVAILABLE"
        assert r["value_m"] is None
        assert r["status"].startswith("NODATA")

    def test_neighbouring_valid_pixel_is_not_affected_by_a_hole(self, dem_dir):
        data = np.full((N, N), 800.0)
        data[150, 230] = np.nan
        path = write_dem(dem_dir / "nan_neighbour.tif", data)
        lat, lon = pixel_centre_lonlat(150, 232)
        r = terrain.elevation_at(lat, lon, path)
        assert r["class"] == "PUBLISHED"
        assert r["value_m"] == pytest.approx(800.0)


class TestTerrainSuccess:
    def test_flat_dem_value_resolution_and_labels(self, flat_dem):
        r = terrain.elevation_at(OBS_LAT, OBS_LON, flat_dem)
        assert r == {
            "value_m": pytest.approx(1250.0),
            "resolution_m": pytest.approx(RES),
            "class": "PUBLISHED",
            "status": "OK",
        }
        assert_json_safe(r)

    def test_accepts_path_objects(self, flat_dem):
        r = terrain.elevation_at(OBS_LAT, OBS_LON, Path(flat_dem))
        assert r["status"] == "OK"

    @pytest.mark.parametrize("row,col", [(0, 0), (150, 230), (199, 200), (399, 399), (10, 390)])
    def test_returns_the_pixel_containing_the_point(self, row, col, dem_dir):
        # Each pixel's value encodes its own (row, col), so any off-by-one
        # or row/col swap is caught immediately.
        data = np.fromfunction(lambda r, c: r * 1000.0 + c, (N, N))
        path = write_dem(dem_dir / "index_dem.tif", data)
        lat, lon = pixel_centre_lonlat(row, col)
        r = terrain.elevation_at(lat, lon, path)
        assert r["status"] == "OK"
        assert r["value_m"] == pytest.approx(row * 1000.0 + col)

    def test_no_interpolation_inside_a_pixel(self, dem_dir):
        data = np.fromfunction(lambda r, c: r * 1000.0 + c, (N, N))
        path = write_dem(dem_dir / "index_dem2.tif", data)
        expected = 150 * 1000.0 + 230
        for dx, dy in [(0.4, 0.4), (-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4)]:
            lat, lon = pixel_centre_lonlat(150, 230, dx, dy)
            r = terrain.elevation_at(lat, lon, path)
            assert r["value_m"] == pytest.approx(expected), (dx, dy)

    def test_geotiff_scale_and_offset_are_applied(self, dem_dir):
        path = write_dem(dem_dir / "scaled.tif", np.full((N, N), 100.0),
                         scale=2.0, offset=10.0)
        r = terrain.elevation_at(OBS_LAT, OBS_LON, path)
        assert r["value_m"] == pytest.approx(210.0)

    def test_resolution_follows_the_pixel_size(self, dem_dir):
        path = write_dem(dem_dir / "res_1000.tif", np.zeros((200, 200)), res=1000.0)
        r = terrain.elevation_at(OBS_LAT, OBS_LON, path)
        assert r["resolution_m"] == pytest.approx(1000.0)


# =========================================================================== #
# horizon._destinations  (azimuth convention, independent of any DEM)
# =========================================================================== #
class TestAzimuthConvention:
    """Azimuth: 0 = North, 90 = East, clockwise (docs/conventions.md)."""

    DELTA = 0.1  # radians of arc
    EXPECTED_DEG = math.degrees(0.1)

    def _dest(self, lat, lon, az_deg):
        lat2, lon2 = horizon._destinations(
            lat, lon, np.array([[math.radians(az_deg)]]), np.array([[self.DELTA]])
        )
        return float(lat2[0, 0]), float(lon2[0, 0])

    @pytest.mark.parametrize("az,exp_lat,exp_lon", [
        (0, EXPECTED_DEG, 0.0),      # north: latitude increases
        (90, 0.0, EXPECTED_DEG),     # east: longitude increases
        (180, -EXPECTED_DEG, 0.0),   # south
        (270, 0.0, -EXPECTED_DEG),   # west
    ])
    def test_cardinal_directions_from_the_equator(self, az, exp_lat, exp_lon):
        lat2, lon2 = self._dest(0.0, 0.0, az)
        assert lat2 == pytest.approx(exp_lat, abs=1e-9)
        assert lon2 == pytest.approx(exp_lon, abs=1e-9)

    def test_azimuth_360_equals_azimuth_0(self):
        assert self._dest(-89.0, 30.0, 360) == pytest.approx(self._dest(-89.0, 30.0, 0), abs=1e-9)

    def test_longitude_is_wrapped_into_minus180_180(self):
        _, lon2 = self._dest(0.0, 179.0, 90)
        assert -180.0 <= lon2 <= 180.0
        assert lon2 == pytest.approx(179.0 + self.EXPECTED_DEG - 360.0, abs=1e-9)

    def test_ray_length_matches_great_circle_distance(self):
        lat2, lon2 = self._dest(-89.0, 30.0, 123)
        p1, p2 = math.radians(-89.0), math.radians(lat2)
        dl = math.radians(lon2 - 30.0)
        cos_c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)
        assert math.acos(min(1.0, cos_c)) == pytest.approx(self.DELTA, abs=1e-9)


# =========================================================================== #
# horizon.horizon_at
# =========================================================================== #
class TestHorizonValidation:
    @pytest.mark.parametrize("lat,lon", BAD_COORDS)
    def test_invalid_coordinates_raise_value_error(self, lat, lon):
        with pytest.raises(ValueError):
            horizon.horizon_at(lat, lon, dem_path="unused.tif")

    @pytest.mark.parametrize("max_km", [-1, -150.0, 0, float("nan"), float("inf"), "abc", None])
    def test_invalid_max_km_raises_value_error(self, max_km):
        with pytest.raises(ValueError):
            horizon.horizon_at(OBS_LAT, OBS_LON, dem_path="unused.tif", max_km=max_km)

    @pytest.mark.parametrize("height", [float("nan"), float("inf"), float("-inf"), "abc"])
    def test_invalid_height_raises_value_error(self, height):
        with pytest.raises(ValueError):
            horizon.horizon_at(OBS_LAT, OBS_LON, height_m=height, dem_path="unused.tif")

    def test_validation_precedes_dem_configuration_check(self):
        # No DEM configured AND bad input: the caller must hear about the input.
        with pytest.raises(ValueError):
            horizon.horizon_at(123.0, 0.0)

    def test_valid_extreme_height_values_are_accepted(self, flat_dem):
        for h in (-9000.0, 0.0, 12000.0):
            r = horizon.horizon_at(OBS_LAT, OBS_LON, height_m=h, dem_path=flat_dem, max_km=MAX_KM)
            assert r["class"] == "CALCULATED"


class TestHorizonErrorHandling:
    def test_unconfigured_dem_is_unavailable(self):
        r = horizon.horizon_at(OBS_LAT, OBS_LON)
        assert r["class"] == "UNAVAILABLE"
        assert r["deg"] is None
        assert r["approx"] is True
        assert r["status"].startswith("DEM_NOT_CONFIGURED")
        assert horizon.DEM_PATH_ENV in r["status"]
        assert_json_safe(r)

    def test_empty_dem_path_counts_as_unconfigured(self):
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path="")
        assert r["status"].startswith("DEM_NOT_CONFIGURED")

    def test_env_var_supplies_the_dem_path(self, flat_dem, monkeypatch):
        monkeypatch.setenv(horizon.DEM_PATH_ENV, flat_dem)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, max_km=MAX_KM)
        assert r["class"] == "CALCULATED"

    def test_explicit_dem_path_beats_env_var(self, flat_dem, tmp_path, monkeypatch):
        monkeypatch.setenv(horizon.DEM_PATH_ENV, str(tmp_path / "wrong.tif"))
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=flat_dem, max_km=MAX_KM)
        assert r["class"] == "CALCULATED"

    def test_missing_file_is_unavailable(self, tmp_path):
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=tmp_path / "missing.tif")
        assert r["class"] == "UNAVAILABLE"
        assert r["deg"] is None
        assert r["status"].startswith("DEM_UNREADABLE")
        assert_json_safe(r)

    def test_corrupt_file_is_unavailable(self, tmp_path):
        bad = tmp_path / "corrupt.tif"
        bad.write_text("not a raster")
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=bad)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("DEM_UNREADABLE")

    def test_open_failure_is_reported_not_raised(self, monkeypatch):
        def boom(*_a, **_k):
            raise RasterioIOError("simulated read failure")

        monkeypatch.setattr(horizon.rasterio, "open", boom)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path="anything.tif")
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("DEM_UNREADABLE")

    def test_dem_without_crs_is_unavailable(self, dem_dir):
        path = write_dem(dem_dir / "h_no_crs.tif", np.zeros((20, 20)), crs=None)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=path)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("NO_CRS")

    def test_geographic_dem_is_unsupported(self, dem_dir):
        path = write_dem(dem_dir / "geographic.tif", np.zeros((20, 20)),
                         crs="EPSG:4326", res=0.5)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=path)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("UNSUPPORTED_CRS")

    def test_non_metre_vertical_units_are_rejected(self, dem_dir):
        path = write_dem(dem_dir / "feet.tif", np.zeros((N, N)), units="ft")
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=path, max_km=MAX_KM)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("UNITS")

    @pytest.mark.parametrize("lat", [-90.0, 90.0, -89.9999999, 89.9999999])
    def test_azimuth_is_undefined_exactly_at_a_pole(self, lat, flat_dem):
        r = horizon.horizon_at(lat, 0.0, dem_path=flat_dem, max_km=MAX_KM)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("AZIMUTH_UNDEFINED_AT_POLE")

    def test_observer_outside_dem_is_unavailable(self, flat_dem):
        r = horizon.horizon_at(-80.0, 0.0, dem_path=flat_dem, max_km=MAX_KM)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("OUT_OF_BOUNDS")

    def test_ray_shorter_than_one_pixel_is_unavailable(self, flat_dem):
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=flat_dem, max_km=0.1)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("MAX_DISTANCE_TOO_SHORT")

    def test_oversized_window_is_refused_instead_of_exhausting_memory(self, flat_dem, monkeypatch):
        monkeypatch.setattr(horizon, "MAX_WINDOW_PIXELS", 100)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=flat_dem, max_km=MAX_KM)
        assert r["class"] == "UNAVAILABLE"
        assert r["status"].startswith("DEM_WINDOW_TOO_LARGE")


class TestHorizonMissingData:
    def test_nodata_at_observer_is_unavailable(self, dem_dir):
        data = np.zeros((N, N))
        X, Y = xy_grid()
        x0, y0 = observer_xy()
        data[np.hypot(X - x0, Y - y0) < 1500] = np.nan
        path = write_dem(dem_dir / "hole.tif", data)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=path, max_km=MAX_KM)
        assert r["class"] == "UNAVAILABLE"
        assert r["deg"] is None
        assert r["status"].startswith("NODATA_AT_OBSERVER")

    def test_explicit_height_bypasses_a_hole_but_flags_the_gaps(self, dem_dir):
        data = np.zeros((N, N))
        X, Y = xy_grid()
        x0, y0 = observer_xy()
        data[np.hypot(X - x0, Y - y0) < 1500] = np.nan
        path = write_dem(dem_dir / "hole2.tif", data)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, height_m=0.0, dem_path=path, max_km=MAX_KM)
        assert r["class"] == "CALCULATED"
        assert r["approx"] is True
        assert r["status"].startswith("PARTIAL_COVERAGE")
        assert r["quality"]["azimuths_with_gaps"] == 360
        assert r["quality"]["valid_sample_fraction"] < 1.0
        assert r["observer"]["height_source"] == "USER"
        assert all(v is None for v in r["deg"])

    def test_all_nodata_dem_is_unavailable(self, dem_dir):
        path = write_dem(dem_dir / "all_nan.tif", np.full((N, N), np.nan))
        r = horizon.horizon_at(OBS_LAT, OBS_LON, height_m=0.0, dem_path=path, max_km=MAX_KM)
        assert r["class"] == "UNAVAILABLE"
        assert r["deg"] is None
        assert r["status"].startswith("NODATA")

    def test_rays_leaving_the_dem_set_approx(self, dem_dir):
        # 40 km DEM; rays of 40 km from near the middle must run off the edge.
        path = write_dem(dem_dir / "tiny.tif", np.zeros((80, 80)))
        r = horizon.horizon_at(-89.9, 0.0, dem_path=path, max_km=MAX_KM)
        assert r["class"] == "CALCULATED"
        assert r["approx"] is True
        assert 0.0 < r["quality"]["valid_sample_fraction"] < 1.0
        assert r["status"].startswith("PARTIAL_COVERAGE")


class TestHorizonCalculation:
    def test_flat_dem_horizon_is_curvature_only(self, flat_dem):
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=flat_dem, max_km=MAX_KM)
        # On flat ground the best angle is at the first sample, d = one pixel:
        # atan2(-d^2/(2R), d), a few thousandths of a degree below zero.
        expected = math.degrees(math.atan2(-(RES ** 2) / (2 * R_MOON), RES))
        assert r["class"] == "CALCULATED"
        assert r["status"] == "OK"
        assert r["approx"] is False
        assert len(r["deg"]) == 360
        assert r["deg"] == pytest.approx([expected] * 360, abs=0.011)
        assert r["quality"]["valid_sample_fraction"] == 1.0

    def test_result_structure_matches_the_agreed_schema(self, flat_dem):
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=flat_dem, max_km=MAX_KM)
        assert {"deg", "dem", "approx", "class", "status"} <= set(r)
        assert set(r["dem"]) == {"name", "resolution_m", "coverage", "retrieved_utc"}
        assert r["dem"]["resolution_m"] == pytest.approx(RES)
        assert r["dem"]["name"] == Path(flat_dem).name
        assert r["observer"]["height_source"] == "DEM"
        assert r["observer"]["height_m"] == pytest.approx(1250.0)
        assert r["method"]["sampling"].startswith("nearest_pixel")
        assert r["method"]["R_moon_m"] == R_MOON
        assert_json_safe(r)

    def test_values_are_rounded_floats_without_negative_zero(self, ring_path):
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=ring_path, max_km=MAX_KM)
        for v in r["deg"]:
            assert isinstance(v, float)
            assert v == round(v, 2)
            assert not (v == 0.0 and math.copysign(1.0, v) < 0)

    def test_observer_height_dip_matches_the_curvature_formula(self, flat_dem):
        # A 100 m high observer over a smooth sphere sees its horizon at
        # -sqrt(2h/R) radians (about -0.615 degrees).
        h = 100.0
        # The flat DEM sits at 1250 m, so height_m = 1250 + h is h above ground.
        r = horizon.horizon_at(OBS_LAT, OBS_LON, height_m=1250.0 + h,
                               dem_path=flat_dem, max_km=MAX_KM)
        dip = -math.degrees(math.sqrt(2 * h / R_MOON))
        assert r["observer"]["height_source"] == "USER"
        assert r["deg"] == pytest.approx([dip] * 360, abs=0.03)

    def test_ridge_ring_matches_atan_h_over_d_with_curvature(self, ring_path):
        h = 500.0
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=ring_path, max_km=MAX_KM)
        # Ring starts 20.0 km out; the first sample that lands on it is
        # between 20.0 and 20.5 km (500 m sampling), so compute both bounds.
        hi = math.degrees(math.atan2(h - 20000.0 ** 2 / (2 * R_MOON), 20000.0))
        lo = math.degrees(math.atan2(h - 20500.0 ** 2 / (2 * R_MOON), 20500.0))
        assert r["approx"] is False
        for v in r["deg"]:
            assert lo - 0.03 <= v <= hi + 0.03

    def test_curvature_hides_a_distant_ridge(self, dem_dir):
        # Ridge 100 km away, 3000 m high. Pure geometry gives atan(3000/100000)
        # = 1.72 degrees, but the lunar surface drops ~2.9 km by then, so the
        # real skyline angle is a small fraction of that.
        res, n = 1000.0, 500
        X, Y = xy_grid(n, res)
        x0, y0 = observer_xy()
        dist = np.hypot(X - x0, Y - y0)
        arr = np.zeros((n, n))
        arr[(dist >= 100000) & (dist <= 103000)] = 3000.0
        path = write_dem(dem_dir / "far_ridge.tif", arr, res=res)
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=path, max_km=120.0)
        flat_angle = math.degrees(math.atan2(3000.0, 100000.0))
        assert max(r["deg"]) < 0.3 < flat_angle
        assert min(r["deg"]) > 0.0

    def test_two_resolutions_agree_within_sampling_error(self, dem_dir):
        coarse = write_dem(dem_dir / "ring_1000.tif",
                           ring_dem(20000, 21500, 500.0, n=200, res=1000.0), res=1000.0)
        fine = write_dem(dem_dir / "ring_500.tif", ring_dem(20000, 21500, 500.0))
        a = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=fine, max_km=MAX_KM)
        b = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=coarse, max_km=MAX_KM)
        assert a["dem"]["resolution_m"] == pytest.approx(500.0)
        assert b["dem"]["resolution_m"] == pytest.approx(1000.0)
        diff = np.abs(np.array(a["deg"]) - np.array(b["deg"]))
        assert diff.max() < 0.25  # documented, not hidden: coarse DEMs differ

    def test_seam_between_azimuth_359_and_0_has_no_jump(self, ring_path):
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=ring_path, max_km=MAX_KM)
        deg = np.array(r["deg"])
        cyclic_steps = np.abs(np.diff(np.append(deg, deg[0])))  # includes 359 -> 0
        assert cyclic_steps.max() < 0.1
        assert abs(deg[359] - deg[0]) < 0.1

    @pytest.mark.parametrize("azimuth", [0, 90, 180, 270, 45, 315])
    def test_a_single_hill_appears_at_its_own_azimuth(self, azimuth, dem_dir):
        # A 500 m high disc 20 km away, half-width ~8.5 degrees. The peak must
        # sit at the bearing it was placed on (azimuth 0 exercises the seam).
        path = write_dem(dem_dir / f"disc_{azimuth}.tif",
                         disc_dem(azimuth, 20000.0, 3000.0, 500.0))
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=path, max_km=MAX_KM)
        deg = np.array(r["deg"])
        assert r["approx"] is False
        peak = int(np.argmax(deg))
        assert circular_distance(peak, azimuth) <= 3
        assert deg[azimuth] > 1.0
        assert deg[(azimuth + 180) % 360] < 0.1

    def test_dem_metadata_file_supplies_labels_only(self, flat_dem, tmp_path):
        meta = tmp_path / "dem_meta.json"
        meta.write_text(json.dumps({
            "name": "SYNTHETIC_TEST_DEM",
            "coverage": "synthetic 200 km square",
            "retrieved_utc": "2026-11-14T00:00:00Z",
            "resolution_m": 1.0,  # must be ignored: resolution comes from the file
        }))
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=flat_dem, max_km=MAX_KM,
                               dem_meta_path=meta)
        assert r["dem"]["name"] == "SYNTHETIC_TEST_DEM"
        assert r["dem"]["coverage"] == "synthetic 200 km square"
        assert r["dem"]["retrieved_utc"] == "2026-11-14T00:00:00Z"
        assert r["dem"]["resolution_m"] == pytest.approx(RES)

    def test_broken_metadata_file_is_ignored(self, flat_dem, tmp_path):
        meta = tmp_path / "dem_meta.json"
        meta.write_text("{ not json")
        r = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=flat_dem, max_km=MAX_KM,
                               dem_meta_path=meta)
        assert r["class"] == "CALCULATED"
        assert r["dem"]["name"] == Path(flat_dem).name
        assert r["dem"]["coverage"].startswith("DEM CRS extent")

    def test_repeated_calls_are_deterministic(self, ring_path):
        a = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=ring_path, max_km=MAX_KM)
        b = horizon.horizon_at(OBS_LAT, OBS_LON, dem_path=ring_path, max_km=MAX_KM)
        assert a == b