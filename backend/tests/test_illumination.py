"""Unit tests for Stage 2 Illumination Engine (geometric vs terrain-corrected sunlight)."""

import numpy as np
import pytest

from backend.science.illumination import (
    HorizonProfile,
    IlluminationError,
    evaluate_sunlight,
    interpolate_horizon_el,
    summarize_illumination_series,
)


def test_horizon_profile_validation():
    with pytest.raises(IlluminationError):
        HorizonProfile(azimuth_deg=np.array([0.0, 90.0]), horizon_el_deg=np.array([0.0, 0.0]))

    with pytest.raises(IlluminationError):
        HorizonProfile(
            azimuth_deg=np.array([0.0, 180.0, 90.0, 270.0]),
            horizon_el_deg=np.array([1.0, 1.0, 1.0, 1.0]),
        )


def test_periodic_north_wrap_interpolation():
    profile = HorizonProfile(
        azimuth_deg=np.array([10.0, 90.0, 180.0, 350.0]),
        horizon_el_deg=np.array([4.0, 0.0, 0.0, 2.0]),
    )
    # Midway between 350 deg (el=2.0) and 10 deg (el=4.0) is 0 deg -> el=3.0
    assert np.isclose(interpolate_horizon_el(0.0, profile), 3.0)
    assert np.isclose(interpolate_horizon_el(360.0, profile), 3.0)


def test_terrain_shadowing_vs_geometric_sunlight():
    # Ridge of 3.0 deg elevation around azimuth 90 deg
    az = np.arange(0.0, 360.0, 10.0)
    el = np.where(np.isclose(az, 90.0), 3.0, 0.0)
    profile = HorizonProfile(azimuth_deg=az, horizon_el_deg=el)

    # Sun at +1.5 deg elevation is geometrically lit, but blocked by 3.0 deg crater rim
    res = evaluate_sunlight(sun_az_deg=90.0, sun_el_deg=1.5, horizon_profile=profile)
    assert res["geometric_sunlit"] is True
    assert res["terrain_sunlit"] is False
    assert res["solar_disk_fraction"] == 0.0
    assert res["provenance"] == "CALCULATED"


def test_partial_solar_disk_occultation():
    profile = HorizonProfile.flat(step_deg=10.0)
    # Sun center exactly on horizon (0.0 deg) -> half of solar disk visible
    res = evaluate_sunlight(sun_az_deg=45.0, sun_el_deg=0.0, horizon_profile=profile, include_solar_disk=True)
    assert res["terrain_sunlit"] is True
    assert np.isclose(res["solar_disk_fraction"], 0.5, atol=1e-3)
    assert res["provenance"] == "CALCULATED"


def test_missing_horizon_keeps_only_geometric_sunlight():
    res = evaluate_sunlight(sun_az_deg=120.0, sun_el_deg=2.0, horizon_profile=None)
    assert res["geometric_sunlit"] is True
    assert res["terrain_sunlit"] is None
    assert res["horizon_el_deg"] is None
    assert res["clearance_deg"] is None
    assert res["solar_disk_fraction"] == 1.0
    assert res["provenance"] == "CALCULATED"
    assert res["terrain_available"] is False


def test_missing_horizon_summary_does_not_report_terrain_fraction():
    summary = summarize_illumination_series(
        times_utc=["2027-03-14T00:00:00Z", "2027-03-14T01:00:00Z"],
        sun_az_deg=[80.0, 90.0],
        sun_el_deg=[-1.0, 1.0],
    )

    assert summary["terrain_sunlit_fraction"] is None
    assert summary["terrain_available"] is False
    assert summary["provenance"] == "CALCULATED"
    assert all(record["terrain_sunlit"] is None for record in summary["series"])


def test_illumination_series_sunrise_and_sunset_events():
    profile = HorizonProfile.flat(step_deg=10.0)
    times = [
        "2027-03-14T00:00:00Z",
        "2027-03-14T01:00:00Z",
        "2027-03-14T02:00:00Z",
        "2027-03-14T03:00:00Z",
    ]
    sun_az = [80.0, 90.0, 100.0, 110.0]
    sun_el = [-1.0, 0.5, 1.0, -0.5]

    summary = summarize_illumination_series(times, sun_az, sun_el, horizon_profile=profile)
    assert summary["sample_count"] == 4
    assert summary["terrain_sunlit_fraction"] == 0.5
    assert len(summary["events"]) == 2
    assert summary["events"][0]["event"] == "SUNRISE"
    assert summary["events"][0]["time_utc"] == "2027-03-14T01:00:00Z"
    assert summary["events"][1]["event"] == "SUNSET"
    assert summary["events"][1]["time_utc"] == "2027-03-14T03:00:00Z"