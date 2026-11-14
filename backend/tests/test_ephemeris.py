"""Unit tests for Stage 1 Ephemeris Engine (NumPy geometry + SPICE integration)."""

from pathlib import Path
import numpy as np
import pytest

from backend.science.ephemeris import (
    DEFAULT_KERNELS_DIR,
    EphemerisError,
    LUNAR_FRAME,
    MOON_RADIUS_KM,
    REQUIRED_KERNELS,
    parse_utc_iso,
    site_position_moon_me,
    sun_earth_at,
    vector_to_enu_az_el,
)


def test_parse_utc_iso_valid_and_invalid():
    dt = parse_utc_iso("2027-03-14T06:00:00Z")
    assert dt.year == 2027 and dt.month == 3 and dt.day == 14 and dt.hour == 6

    with pytest.raises(EphemerisError):
        parse_utc_iso("not-a-date")

    with pytest.raises(EphemerisError):
        parse_utc_iso("")


def test_coordinate_validation():
    with pytest.raises(EphemerisError):
        site_position_moon_me(-95.0, 0.0)
    with pytest.raises(EphemerisError):
        site_position_moon_me(0.0, 185.0)


def test_site_position_conventions():
    p0 = site_position_moon_me(0.0, 0.0, 0.0)
    assert np.allclose(p0, [MOON_RADIUS_KM, 0.0, 0.0])

    pe = site_position_moon_me(0.0, 90.0, 0.0)
    assert np.allclose(pe, [0.0, MOON_RADIUS_KM, 0.0], atol=1e-9)

    ps = site_position_moon_me(-90.0, 0.0, 0.0)
    assert np.allclose(ps, [0.0, 0.0, -MOON_RADIUS_KM], atol=1e-9)


def test_enu_azimuth_and_elevation_directions():
    az_n, el_n = vector_to_enu_az_el(np.array([0.0, 0.0, 1.0]), 0.0, 0.0)
    assert np.isclose(az_n, 0.0) and np.isclose(el_n, 0.0)

    az_e, el_e = vector_to_enu_az_el(np.array([0.0, 1.0, 0.0]), 0.0, 0.0)
    assert np.isclose(az_e, 90.0) and np.isclose(el_e, 0.0)

    _, el_up = vector_to_enu_az_el(np.array([1.0, 0.0, 0.0]), 0.0, 0.0)
    assert np.isclose(el_up, 90.0)


def test_earth_parallax_shift_at_south_pole():
    sun_vec = np.array([1.496e8, 0.0, 0.0])
    earth_vec = np.array([384400.0, 0.0, 0.0])
    res = sun_earth_at(-90.0, 0.0, "2027-03-14T06:00:00Z", sun_vec_km=sun_vec, earth_vec_km=earth_vec)
    assert res["frame"] == LUNAR_FRAME
    assert np.isclose(res["sun_el_deg"], 0.0, atol=1e-4)
    assert -0.27 < res["earth_el_deg"] < -0.25


def test_missing_kernels_raises_helpful_error(tmp_path: Path):
    pytest.importorskip("spiceypy")
    with pytest.raises(EphemerisError, match="Missing SPICE kernel"):
        sun_earth_at(-89.5, 0.0, "2027-03-14T06:00:00Z", kernels_dir=tmp_path)


@pytest.mark.skipif(
    not all((DEFAULT_KERNELS_DIR / k).exists() for k in REQUIRED_KERNELS),
    reason="SPICE kernels not downloaded yet; run scripts/ephemeris/download_kernels.py",
)
def test_live_spice_south_pole_bounds():
    res = sun_earth_at(-89.54, 0.0, "2027-03-14T06:00:00Z")
    assert -3.0 <= res["sun_el_deg"] <= 3.0
    assert -9.0 <= res["earth_el_deg"] <= 9.0
    assert 0.0 <= res["sun_az_deg"] < 360.0
    assert 0.0 <= res["earth_az_deg"] < 360.0

