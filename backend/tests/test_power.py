"""Unit tests for Stage 3 Solar Power & Battery Energy Balance Engine."""

import numpy as np
import pytest

from backend.science.power import (
    PowerError,
    SOLAR_CONSTANT_W_M2,
    SolarArrayConfig,
    incidence_cos_factor,
    instantaneous_solar_power_w,
    simulate_power_budget,
)


def test_solar_array_config_validation():
    with pytest.raises(PowerError):
        SolarArrayConfig(area_m2=-1.0)
    with pytest.raises(PowerError):
        SolarArrayConfig(efficiency=1.5)
    with pytest.raises(PowerError):
        SolarArrayConfig(battery_capacity_wh=0.0)


def test_polar_panel_mount_physics():
    # At 1.5 deg polar sun elevation: horizontal panel gets sin(1.5 deg) ~ 0.026,
    # whereas vertical_south_pole gets cos(1.5 deg) ~ 0.9997, and sun_tracking gets 1.0
    c_horiz = incidence_cos_factor(90.0, 1.5, mount_mode="horizontal")
    c_vert = incidence_cos_factor(90.0, 1.5, mount_mode="vertical_south_pole")
    c_track = incidence_cos_factor(90.0, 1.5, mount_mode="sun_tracking")

    assert np.isclose(c_horiz, np.sin(np.radians(1.5)), atol=1e-4)
    assert c_vert > 0.999
    assert c_track == 1.0


def test_instantaneous_power_sunlit_and_eclipse():
    cfg = SolarArrayConfig(area_m2=2.0, efficiency=0.28, mount_mode="sun_tracking", base_load_w=140.0)

    lit = instantaneous_solar_power_w(90.0, 2.0, solar_disk_fraction=1.0, config=cfg)
    expected_w = SOLAR_CONSTANT_W_M2 * 2.0 * 0.28
    assert np.isclose(lit["generated_w"], expected_w, atol=0.1)
    assert lit["net_w"] > 0.0
    assert lit["provenance"] == "ESTIMATED"

    dark = instantaneous_solar_power_w(90.0, 2.0, solar_disk_fraction=0.0, config=cfg)
    assert dark["generated_w"] == 0.0
    assert dark["net_w"] == -140.0


def test_battery_charge_and_discharge_trajectory():
    cfg = SolarArrayConfig(
        area_m2=2.0,
        efficiency=0.28,
        mount_mode="sun_tracking",
        battery_capacity_wh=1000.0,
        initial_soc=0.50,
        min_soc=0.20,
        base_load_w=200.0,
    )
    times = [
        "2027-03-14T00:00:00Z",
        "2027-03-14T01:00:00Z",
        "2027-03-14T02:00:00Z",
        "2027-03-14T03:00:00Z",
    ]
    # First 2 hours sunlit (charges battery), next 2 hours shadowed (discharges battery)
    disk_fracs = [1.0, 1.0, 0.0, 0.0]

    sim = simulate_power_budget(
        times_utc=times,
        sun_az_deg=[90.0, 95.0, 100.0, 105.0],
        sun_el_deg=[1.5, 1.5, 1.5, 1.5],
        solar_disk_fractions=disk_fracs,
        dt_hours=1.0,
        config=cfg,
    )
    assert sim["sample_count"] == 4
    assert sim["series"][1]["battery_soc"] > 0.50
    assert sim["series"][3]["battery_soc"] < sim["series"][1]["battery_soc"]
    assert sim["provenance"] == "ESTIMATED"


def test_simulate_power_budget_uses_supplied_irradiance():
    cfg = SolarArrayConfig(
        area_m2=2.0,
        efficiency=0.28,
        mount_mode="horizontal",
        base_load_w=0.0,
    )
    sim = simulate_power_budget(
        times_utc=["2027-03-14T00:00:00Z"],
        sun_az_deg=[90.0],
        sun_el_deg=[30.0],
        solar_disk_fractions=[1.0],
        dt_hours=0.5,
        config=cfg,
        irradiance_w_m2=[SOLAR_CONSTANT_W_M2],
    )

    assert sim["series"][0]["generated_w"] == pytest.approx(
        cfg.area_m2 * cfg.efficiency * SOLAR_CONSTANT_W_M2 * 0.5,
        abs=0.001,
    )


def test_simulate_power_budget_requires_irradiance_per_step():
    with pytest.raises(PowerError, match="irradiance_w_m2 must match"):
        simulate_power_budget(
            times_utc=["2027-03-14T00:00:00Z"],
            sun_az_deg=[90.0],
            sun_el_deg=[30.0],
            solar_disk_fractions=[1.0],
            irradiance_w_m2=[],
        )


def test_low_battery_alert_triggered_during_long_shadow():
    cfg = SolarArrayConfig(
        battery_capacity_wh=500.0,
        initial_soc=0.30,
        min_soc=0.20,
        base_load_w=100.0,
    )
    times = ["2027-03-14T00:00:00Z", "2027-03-14T01:00:00Z"]
    sim = simulate_power_budget(
        times_utc=times,
        sun_az_deg=[90.0, 95.0],
        sun_el_deg=[-1.0, -1.0],
        solar_disk_fractions=[0.0, 0.0],
        dt_hours=1.0,
        config=cfg,
    )
    assert sim["low_battery_steps"] >= 1
    assert sim["series"][-1]["low_battery_alert"] is True