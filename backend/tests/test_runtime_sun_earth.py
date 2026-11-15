"""Tests for the single-epoch Sun/Earth runtime adapter."""

from __future__ import annotations

import numpy as np
import pytest

from backend.science.ephemeris import EphemerisError
from backend.science.runtime import compute_timeseries, sun_earth_at


EXPECTED_KEYS = {
    "time_utc",
    "sun_el",
    "sun_az",
    "earth_el",
    "earth_az",
    "sun_lit_geom",
    "earth_vis_geom",
    "sun_lit_terrain",
    "earth_vis_terrain",
    "hours_to_sunset",
    "hours_to_sunrise",
    "hours_to_earthset",
    "hours_to_earthrise",
    "sun_dir_bf",
    "earth_dir_bf",
    "terrain_applied",
    "countdown_resolution_min",
    "warnings",
}


def test_sun_earth_at_keys_and_first_sample_match() -> None:
    lat, lon, time_utc = -89.54, 0.0, "2027-03-14T00:00:00Z"
    result = sun_earth_at(lat, lon, time_utc, search_hours=24)
    ts = compute_timeseries(lat, lon, time_utc, hours=24, step_min=30)["timeseries"]

    assert set(result) == EXPECTED_KEYS
    assert result["time_utc"] == ts["start_utc"]
    for key in (
        "sun_el",
        "sun_az",
        "earth_el",
        "earth_az",
        "sun_lit_geom",
        "earth_vis_geom",
        "sun_lit_terrain",
        "earth_vis_terrain",
    ):
        assert result[key] == (None if ts[key] is None else ts[key][0])
    assert not (result["hours_to_sunset"] is not None and result["hours_to_sunrise"] is not None)
    assert not (
        result["hours_to_earthset"] is not None and result["hours_to_earthrise"] is not None
    )
    assert result["countdown_resolution_min"] == 30
    assert np.isclose(np.linalg.norm(result["sun_dir_bf"]), 1.0)
    assert np.isclose(np.linalg.norm(result["earth_dir_bf"]), 1.0)


def test_sun_earth_at_high_horizon_is_dark_without_countdown() -> None:
    result = sun_earth_at(
        -89.54,
        0.0,
        "2027-03-14T00:00:00Z",
        horizon_deg=[45.0] * 360,
        search_hours=24,
    )

    assert result["sun_lit_terrain"] is False
    assert result["terrain_applied"] is True
    assert result["hours_to_sunset"] is None
    assert result["hours_to_sunrise"] is None


def test_sun_earth_at_outside_ephemeris_coverage_raises() -> None:
    with pytest.raises(EphemerisError):
        sun_earth_at(-89.54, 0.0, "2026-12-31T23:59:59Z")


def test_runtime_angles_match_jpl_horizons_reference() -> None:
    # JPL Horizons API, DE441, AIRLESS observer at 0E/-89.54, 2027-03-14 06:00 UT.
    expected = {
        "sun_az": 103.882226,
        "sun_el": -0.943024,
        "earth_az": 355.515888,
        "earth_el": 6.698473,
    }

    result = sun_earth_at(-89.54, 0.0, "2027-03-14T06:00:00Z", search_hours=0)

    for key, reference_deg in expected.items():
        assert abs(result[key] - reference_deg) < 0.1
