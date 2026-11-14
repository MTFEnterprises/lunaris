"""Unit tests for Stage 4 Direct-to-Earth (DTE) Communication & RF Link Engine."""

import numpy as np
import pytest

from backend.science.illumination import HorizonProfile
from backend.science.link import (
    LinkError,
    MEAN_EARTH_MOON_DISTANCE_KM,
    RFLinkConfig,
    evaluate_dte_link,
    free_space_path_loss_db,
    summarize_comm_windows,
)


def test_rf_link_config_validation():
    with pytest.raises(LinkError):
        RFLinkConfig(frequency_ghz=0.0)
    with pytest.raises(LinkError):
        RFLinkConfig(tx_power_w=-5.0)
    with pytest.raises(LinkError):
        RFLinkConfig(target_data_rate_kbps=0.0)
    with pytest.raises(LinkError, match="Both antenna boresight"):
        RFLinkConfig(antenna_boresight_az_deg=90.0)
    with pytest.raises(LinkError, match="az_deg"):
        RFLinkConfig(antenna_boresight_az_deg=360.0, antenna_boresight_el_deg=0.0)
    with pytest.raises(LinkError, match="el_deg"):
        RFLinkConfig(antenna_boresight_az_deg=90.0, antenna_boresight_el_deg=91.0)


def test_xband_free_space_path_loss_bounds():
    # At ~384,400 km and 8.4 GHz, X-band FSPL is ~222.6 dB
    fspl = free_space_path_loss_db(MEAN_EARTH_MOON_DISTANCE_KM, 8.4)
    assert 222.0 < fspl < 223.2


def test_terrain_occlusion_blocks_earth_link():
    # Crater wall of 4.0 deg elevation at azimuth 0 deg (North)
    az = np.arange(0.0, 360.0, 10.0)
    el = np.where(np.isclose(az, 0.0), 4.0, 0.0)
    profile = HorizonProfile(azimuth_deg=az, horizon_el_deg=el)

    # Earth at +2.5 deg elevation is geometrically above 0 deg, but blocked by 4.0 deg ridge
    res = evaluate_dte_link(earth_az_deg=0.0, earth_el_deg=2.5, horizon_profile=profile)
    assert res["geometric_los"] is True
    assert res["terrain_los"] is False
    assert res["link_active"] is False
    assert res["achievable_data_rate_kbps"] == 0.0
    assert res["provenance"] == "ESTIMATED"
    assert res["geometric_provenance"] == "CALCULATED"
    assert res["terrain_available"] is True


def test_missing_horizon_uses_geometric_los_without_terrain_values():
    res = evaluate_dte_link(earth_az_deg=10.0, earth_el_deg=5.0, horizon_profile=None)

    assert res["geometric_los"] is True
    assert res["terrain_los"] is None
    assert res["horizon_el_deg"] is None
    assert res["clearance_deg"] is None
    assert res["link_active"] is True
    assert res["geometric_provenance"] == "CALCULATED"
    assert res["provenance"] == "ESTIMATED"
    assert res["terrain_available"] is False
    assert res["pointing_error_deg"] is None


def test_optional_boresight_reports_pointing_error_without_assumed_limit():
    config = RFLinkConfig(
        antenna_boresight_az_deg=359.0,
        antenna_boresight_el_deg=0.0,
    )
    res = evaluate_dte_link(
        earth_az_deg=1.0,
        earth_el_deg=0.0,
        horizon_profile=None,
        config=config,
    )

    assert res["pointing_error_deg"] == pytest.approx(2.0, abs=1e-4)
    assert res["link_active"] is False


def test_boresight_error_does_not_gate_link_without_a_declared_limit():
    config = RFLinkConfig(
        antenna_boresight_az_deg=180.0,
        antenna_boresight_el_deg=-90.0,
    )
    res = evaluate_dte_link(
        earth_az_deg=10.0,
        earth_el_deg=5.0,
        horizon_profile=None,
        config=config,
    )

    assert res["pointing_error_deg"] > 90.0
    assert res["link_active"] is True


def test_clear_dte_link_positive_margin_and_data_rate():
    profile = HorizonProfile.flat(step_deg=10.0)
    res = evaluate_dte_link(earth_az_deg=10.0, earth_el_deg=5.0, horizon_profile=profile)
    assert res["terrain_los"] is True
    assert res["link_active"] is True
    assert res["link_margin_db"] > 0.0
    assert res["achievable_data_rate_kbps"] >= 256.0


def test_comm_windows_aos_and_los_events():
    profile = HorizonProfile.flat(step_deg=10.0)
    times = [
        "2027-03-14T00:00:00Z",
        "2027-03-14T01:00:00Z",
        "2027-03-14T02:00:00Z",
        "2027-03-14T03:00:00Z",
    ]
    # Earth elevation rises above 1.0 deg clearance margin at 01:00 (AOS) and drops at 03:00 (LOS)
    earth_el = [-0.5, 2.5, 3.0, 0.2]

    summary = summarize_comm_windows(
        times_utc=times,
        earth_az_deg=[0.0, 0.5, 1.0, 1.5],
        earth_el_deg=earth_el,
        horizon_profile=profile,
    )
    assert summary["sample_count"] == 4
    assert summary["comm_availability_fraction"] == 0.5
    assert len(summary["events"]) == 2
    assert summary["events"][0]["event"] == "AOS"
    assert summary["events"][0]["time_utc"] == "2027-03-14T01:00:00Z"
    assert summary["events"][1]["event"] == "LOS"
    assert summary["events"][1]["time_utc"] == "2027-03-14T03:00:00Z"