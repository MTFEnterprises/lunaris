"""LUNARIS M2 Solar Power & Battery Energy Balance Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence
import numpy as np

# Solar irradiance constant at 1 AU [W/m^2]
SOLAR_CONSTANT_W_M2 = 1361.0
SOLAR_UPPER_LIMB_DEG = 0.27

PanelMountMode = Literal["horizontal", "sun_tracking", "vertical_south_pole", "fixed"]


class PowerError(Exception):
    """Domain error for invalid solar array, load, or battery parameters."""


@dataclass(frozen=True)
class SolarArrayConfig:
    """Lunar lander/rover photovoltaic and battery system specification.

    Defaults represent a small polar lunar lander class (~2 m^2, 28% triple-junction GaAs).
    """

    area_m2: float = 2.0
    efficiency: float = 0.28
    losses: float = 0.0
    mount_mode: PanelMountMode = "sun_tracking"
    panel_tilt_deg: float = 0.0
    panel_az_deg: float = 0.0
    battery_capacity_wh: float = 1200.0
    initial_soc: float = 0.80
    min_soc: float = 0.20
    charge_efficiency: float = 0.92
    discharge_efficiency: float = 0.95
    base_load_w: float = 140.0

    def __post_init__(self) -> None:
        if self.area_m2 <= 0.0:
            raise PowerError("area_m2 must be strictly positive.")
        if not (0.0 < self.efficiency <= 1.0):
            raise PowerError("efficiency must be in (0, 1].")
        if not (0.0 <= self.losses < 1.0):
            raise PowerError("losses must be in [0, 1).")
        if self.mount_mode not in ("horizontal", "sun_tracking", "vertical_south_pole", "fixed"):
            raise PowerError(f"Unsupported mount_mode: {self.mount_mode}")
        if not (0.0 <= self.panel_tilt_deg <= 90.0):
            raise PowerError("panel_tilt_deg must be within [0, 90].")
        if self.battery_capacity_wh <= 0.0:
            raise PowerError("battery_capacity_wh must be strictly positive.")
        if not (0.0 <= self.initial_soc <= 1.0) or not (0.0 <= self.min_soc < 1.0):
            raise PowerError("initial_soc and min_soc must be within [0, 1].")
        if not (0.0 < self.charge_efficiency <= 1.0) or not (0.0 < self.discharge_efficiency <= 1.0):
            raise PowerError("Battery charge/discharge efficiencies must be in (0, 1].")
        if self.base_load_w < 0.0:
            raise PowerError("base_load_w cannot be negative.")


def incidence_cos_factor(
    sun_az_deg: float,
    sun_el_deg: float,
    mount_mode: PanelMountMode = "sun_tracking",
    panel_tilt_deg: float = 0.0,
    panel_az_deg: float = 0.0,
) -> float:
    """Compute cosine of solar incidence angle [0.0, 1.0] on the solar panel surface."""
    if sun_el_deg <= -SOLAR_UPPER_LIMB_DEG:
        return 0.0

    el_rad = np.radians(float(sun_el_deg))

    if mount_mode == "sun_tracking":
        # Two-axis gimballing panel points directly at the Sun when above horizon
        return 1.0

    if mount_mode == "horizontal":
        return float(np.clip(np.sin(el_rad), 0.0, 1.0))

    if mount_mode == "vertical_south_pole":
        # Vertical azimuth-tracking mast optimal for low-elevation (~0-3 deg) polar Sun
        return float(np.clip(np.cos(el_rad), 0.0, 1.0))

    # General fixed tilted panel normal vector in local ENU frame
    tilt_rad = np.radians(float(panel_tilt_deg))
    paz_rad = np.radians(float(panel_az_deg))
    saz_rad = np.radians(float(sun_az_deg))

    sun_enu = np.array(
        [
            np.cos(el_rad) * np.sin(saz_rad),
            np.cos(el_rad) * np.cos(saz_rad),
            np.sin(el_rad),
        ],
        dtype=np.float64,
    )
    normal_enu = np.array(
        [
            np.sin(tilt_rad) * np.sin(paz_rad),
            np.sin(tilt_rad) * np.cos(paz_rad),
            np.cos(tilt_rad),
        ],
        dtype=np.float64,
    )
    return float(np.clip(np.dot(sun_enu, normal_enu), 0.0, 1.0))


def instantaneous_solar_power_w(
    sun_az_deg: float,
    sun_el_deg: float,
    solar_disk_fraction: float,
    config: SolarArrayConfig | None = None,
    irradiance_w_m2: float = SOLAR_CONSTANT_W_M2,
) -> dict:
    """Calculate electrical power output [W] at a single time step."""
    cfg = config or SolarArrayConfig()
    disk_frac = float(np.clip(solar_disk_fraction, 0.0, 1.0))

    if disk_frac <= 0.0 or sun_el_deg <= -SOLAR_UPPER_LIMB_DEG:
        cos_theta = 0.0
        power_w = 0.0
    else:
        cos_theta = incidence_cos_factor(
            sun_az_deg=sun_az_deg,
            sun_el_deg=sun_el_deg,
            mount_mode=cfg.mount_mode,
            panel_tilt_deg=cfg.panel_tilt_deg,
            panel_az_deg=cfg.panel_az_deg,
        )
        net_efficiency = cfg.efficiency * (1.0 - cfg.losses)
        power_w = float(irradiance_w_m2) * cfg.area_m2 * net_efficiency * disk_frac * cos_theta

    net_power_w = power_w - cfg.base_load_w

    return {
        "generated_w": round(power_w, 3),
        "load_w": round(cfg.base_load_w, 3),
        "net_w": round(net_power_w, 3),
        "cos_incidence": round(cos_theta, 4),
        "solar_disk_fraction": round(disk_frac, 4),
        "mount_mode": cfg.mount_mode,
        "provenance": "CALCULATED",
    }


def simulate_power_budget(
    times_utc: Sequence[str],
    sun_az_deg: Sequence[float],
    sun_el_deg: Sequence[float],
    solar_disk_fractions: Sequence[float],
    dt_hours: float = 1.0,
    config: SolarArrayConfig | None = None,
    load_profile_w: Sequence[float] | None = None,
) -> dict:
    """Simulate time-stepped solar generation and battery State-of-Charge (SoC) trajectory."""
    n = len(times_utc)
    if n == 0 or len(sun_az_deg) != n or len(sun_el_deg) != n or len(solar_disk_fractions) != n:
        raise PowerError("Input arrays must have matching non-zero length.")
    if dt_hours <= 0.0:
        raise PowerError("dt_hours must be strictly positive.")

    cfg = config or SolarArrayConfig()
    if load_profile_w is not None:
        if len(load_profile_w) != n:
            raise PowerError("load_profile_w must match times_utc length.")
        loads = [float(x) for x in load_profile_w]
    else:
        loads = [cfg.base_load_w] * n

    energy_wh = cfg.initial_soc * cfg.battery_capacity_wh
    min_energy_wh = cfg.min_soc * cfg.battery_capacity_wh

    series = []
    total_generated_wh = 0.0
    total_consumed_wh = 0.0
    brownout_steps = 0

    for t_str, az, el, disk_frac, load_w in zip(
        times_utc, sun_az_deg, sun_el_deg, solar_disk_fractions, loads
    ):
        step = instantaneous_solar_power_w(
            sun_az_deg=float(az),
            sun_el_deg=float(el),
            solar_disk_fraction=float(disk_frac),
            config=cfg,
        )
        gen_w = step["generated_w"]
        net_w = gen_w - load_w

        if net_w >= 0.0:
            # Excess solar energy charges battery up to 100% capacity
            stored_wh = net_w * dt_hours * cfg.charge_efficiency
            energy_wh = min(cfg.battery_capacity_wh, energy_wh + stored_wh)
        else:
            # Deficit draws from battery accounting for discharge efficiency
            drawn_wh = (-net_w * dt_hours) / cfg.discharge_efficiency
            energy_wh = max(0.0, energy_wh - drawn_wh)

        soc = energy_wh / cfg.battery_capacity_wh
        deficit_alert = energy_wh < min_energy_wh
        if deficit_alert:
            brownout_steps += 1

        total_generated_wh += gen_w * dt_hours
        total_consumed_wh += load_w * dt_hours

        series.append(
            {
                "time_utc": str(t_str),
                "generated_w": round(gen_w, 3),
                "load_w": round(load_w, 3),
                "net_w": round(net_w, 3),
                "battery_wh": round(energy_wh, 3),
                "battery_soc": round(soc, 4),
                "low_battery_alert": bool(deficit_alert),
            }
        )

    return {
        "sample_count": n,
        "dt_hours": float(dt_hours),
        "mount_mode": cfg.mount_mode,
        "total_generated_wh": round(total_generated_wh, 2),
        "total_consumed_wh": round(total_consumed_wh, 2),
        "mean_generated_w": round(total_generated_wh / (n * dt_hours), 2),
        "min_battery_soc": round(min(r["battery_soc"] for r in series), 4),
        "final_battery_soc": round(series[-1]["battery_soc"], 4),
        "low_battery_steps": brownout_steps,
        "series": series,
        "provenance": "CALCULATED",
    }